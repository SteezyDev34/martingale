import os
import sys
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


def GetCouponInfo(driver):
    """
    Récupère les informations du pari validé depuis la modal de confirmation.
    Cherche les données dans le DOM selon le site_type et retourne un dictionnaire.

    Args:
        driver: Instance du WebDriver Selenium

    Returns:
        dict: Dictionnaire contenant les informations du pari validé, ou None en cas d'erreur
    """
    info = {
        'montant': config.mise,
        'cote': None,
        'match': None,
        'equipe_1': None,
        'equipe_2': None,
        'type_de_pari': None,
        'bet': None,
        'coupon': None,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    site = config.site_type

    if site == 'new_site':
        info = _parse_new_site(driver, info)
    elif site == 'mobile_site':
        print(site)
        info = _parse_mobile_site(driver, info)
    else:
        info = _parse_old_site(driver, info)

    config.log(f"GetCouponInfo: {info}")
    return info


def _extract_text(driver, css_selector, timeout=3):
    """Extrait le texte d'un élément via CSS selector avec un timeout."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        txt = el.text or driver.execute_script(
            "return (arguments[0].innerText || arguments[0].textContent || '').trim();", el)
        print('extract txt : ', txt.strip())
        return txt.strip() if txt else ''
    except Exception:
        return ''


def _extract_text_class(driver, class_name, timeout=3):
    """Extrait le texte d'un élément via CLASS_NAME avec un timeout."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        txt = el.text or driver.execute_script(
            "return (arguments[0].innerText || arguments[0].textContent || '').trim();", el)
        print('extratc text class : ', txt.strip())
        return txt.strip() if txt else ''
    except Exception:
        return ''


def _extract_all_text_class(driver, class_name, timeout=3):
    """Extrait le texte de tous les éléments via CLASS_NAME."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name)))
        els = driver.find_elements(By.CLASS_NAME, class_name)
        return [e.text.strip() for e in els if e.text.strip()]
    except Exception:
        return []


def _parse_new_site(driver, info):
    """Parse la modal de validation pour le new_site."""

    # --- Cote ---
    try:
        cote_text = _extract_text_class(driver, 'ui-coupon-modal-bet-market__coef')
        if cote_text:
            info['cote'] = cote_text
    except Exception:
        pass

    # --- Numéro de coupon ---
    try:
        coupon_text = _extract_text_class(driver, 'ui-coupon-modal-header__info')
        if coupon_text:
            # Garder uniquement la valeur numérique
            numeric = ''.join(c for c in coupon_text if c.isdigit())
            if numeric:
                info['coupon'] = numeric
    except Exception:
        pass

    # --- Noms des équipes / match ---
    try:
        teams = _extract_all_text_class(driver, 'ui-coupon-bet-teams__name')
        if not teams:
            # Fallback: chercher les noms dans la section coupon-bet
            teams_text = _extract_text_class(driver, 'ui-coupon-modal-bet__teams')
            if teams_text and ' - ' in teams_text:
                teams = [t.strip() for t in teams_text.split(' - ', 1)]
        if len(teams) >= 2:
            info['equipe_1'] = teams[0]
            info['equipe_2'] = teams[1]
            info['match'] = f"{teams[0]} - {teams[1]}"
        elif len(teams) == 1:
            info['match'] = teams[0]
    except Exception:
        pass

    # --- Type de pari ---
    try:
        bet_type = _extract_text_class(driver, 'ui-coupon-modal-bet-market__name')
        if bet_type:
            parts = [p.strip() for p in bet_type.split(':', 1) if p is not None]
            if len(parts) >= 2:
                info['type_de_pari'] = parts[0]
                info['bet'] = info['match']+' : '+parts[1]
            elif len(parts) == 1:
                # Si il n'y a qu'une partie, la mettre dans type_de_pari et laisser bet vide
                info['bet'] = info['match']+' : '+parts[0]
            else:
                # Valeur inattendue, stocker la chaîne brute
                info['bet'] = info['match']+' : '+bet_type

    except Exception:
        pass

    # --- Montant / mise ---
    try:
        info['montant'] = float(config.mise)
    except Exception:
        pass

    return info


def _parse_mobile_site(driver, info):
    """Parse la modal de validation pour le mobile_site."""

    # --- Cote ---
    try:
        config.cote = ''.join(filter(lambda x: x.isdigit() or x in ',.',
                                     driver.find_elements(By.CLASS_NAME,
                                                          config.classes['coef_value'][config.site_type])[0].text))
    except Exception as e:
        print(e)
        config.log('erreur recup cote', 'info', False)
    else:
        info['cote'] = config.cote
        print('cote', info['cote'])

    # --- Noms des équipes ---
    try:
        teams = _extract_text_class(driver, 'quick-coupon-events-card-team')
        if not teams:
            teams_text = _extract_text_class(driver, 'quick-coupon-events-card__teams')
            if teams_text and ' - ' in teams_text:
                teams = [t.strip() for t in teams_text.split(' - ', 1)]
        if len(teams) >= 2:
            info['equipe_1'] = teams[0]
            info['equipe_2'] = teams[1]
            info['match'] = f"{teams[0]} - {teams[1]}"
        elif len(teams) == 1:
            info['match'] = teams[0]
    except Exception:
        pass
    else:
        print('equipe_1', info['equipe_1'])
        print('equipe_2', info['equipe_2'])
        print('match', info['match'])

    # --- Type de pari ---
    try:
        bet_wrapper = driver.find_element(By.CLASS_NAME, 'quick-coupon-events-card-bets__list')
        bet_types = bet_wrapper.find_elements(By.CLASS_NAME, 'quick-coupon-events-card-bets__bet')
        if not bet_types:
            bet_types = bet_wrapper.find_elements(By.CLASS_NAME, 'ui-caption--color-clr-decent')
        for bet_type in bet_types:
            parts = [p.strip() for p in bet_type.text.split(':', 1) if p is not None]
            if len(parts) >= 2:
                info['type_de_pari'] = parts[len(parts) - 2]
                info['bet'] = parts[-1]
            elif len(parts) == 1:
                # Si il n'y a qu'une partie, la mettre dans type_de_pari et laisser bet vide
                info['bet'] = parts[0]
            else:
                # Valeur inattendue, stocker la chaîne brute
                info['bet'] = bet_type.text

    except Exception as e:
        print(e)

    return info


def _parse_old_site(driver, info):
    """Parse la modal de validation pour le old_site (fallback)."""

    # --- Cote ---
    try:
        cote_text = _extract_text_class(driver, 'cpn-bet__coef')
        if cote_text:
            info['cote'] = cote_text
    except Exception:
        pass

    # --- Noms des équipes ---
    try:
        teams_text = _extract_text(driver, '.cpn-bet__teams, .c-coupon-modal__teams')
        if teams_text and ' - ' in teams_text:
            teams = [t.strip() for t in teams_text.split(' - ', 1)]
            if len(teams) >= 2:
                info['equipe_1'] = teams[0]
                info['equipe_2'] = teams[1]
                info['match'] = f"{teams[0]} - {teams[1]}"
    except Exception:
        pass

    return info


if __name__ == "__main__":
    # driver.switch_to.window(driver.window_handles[0])
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver

    num_fenetre = 1
    driver = get_script_driver(num_fenetre)
    config.site_type = 'mobile_site'
    config.mise = 0.2
    result = GetCouponInfo(driver)
    print(result)
