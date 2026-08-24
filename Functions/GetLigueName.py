# get_ligue_name
from selenium.webdriver.common.by import By
from urllib.parse import unquote

import config


def main(bet_ligue):
    config.ligue_name = False
    try:
        div_ligue_name = bet_ligue.find_element(By.TAG_NAME, 'div')
    except Exception as e:
        config.ligue_name = False
    else:
        try:
            config.ligue_name = div_ligue_name.find_element(By.CLASS_NAME,
                                                            config.classes['dashboard_champ_name'][config.site_type])
            config.ligue_name = config.ligue_name.text.lower()
            config.ligue_name = config.ligue_name.replace('.', '')
        except Exception as e:
            config.log(f'#E0005 Une erreur est survenue : {e}', 'warning', True, 2, False)
            config.ligue_name = False
    return config.ligue_name


# GetLigueNameFromUrl
def fromUrl(driver):
    from Functions.BridgeAdapter import bridge_active
    if bridge_active():
        try:
            from websocket_server import bridge
            state = bridge.get_state()
            url = (state or {}).get('url', '') or ''
        except Exception:
            url = ''
        if 'tennis/' in url:
            try:
                path_after = url.split('tennis/', 1)[1]
                first_segment = path_after.split('/', 1)[0]
                first_segment = first_segment.replace('?platform_type=mobile', '')
                from urllib.parse import unquote
                first_segment = unquote(first_segment)
                parts = first_segment.split('-') if first_segment else []
                if len(parts) > 1:
                    parts = parts[1:]
                ligue = ' '.join([p for p in parts if p]).strip()
                config.ligue_name = ligue or False
            except Exception:
                config.ligue_name = False
        else:
            config.ligue_name = False
        return [config.ligue_name, url]
    """
    Extrait le nom de la ligue depuis l'URL du driver.

    Retourne une liste [ligue_name|False, url_courante].
    La fonction gère les URL qui ne contiennent pas le segment attendu.
    """
    url = driver.current_url or ""

    # Si l'URL ne contient pas le segment attendu, on renvoie False
    if 'tennis/' not in url:
        config.ligue_name = False
        return [config.ligue_name, url]

    try:
        path_after = url.split('tennis/', 1)[1]
    except Exception:
        config.ligue_name = False
        return [config.ligue_name, url]

    # Récupère la première portion avant le slash
    first_segment = path_after.split('/', 1)[0]
    first_segment = first_segment.replace('?platform_type=mobile', '')
    first_segment = unquote(first_segment)

    parts = first_segment.split('-') if first_segment else []

    # Si la découpe ne donne rien d'utile
    if len(parts) <= 1:
        ligue = ' '.join(parts).strip() if parts else False
        config.ligue_name = ligue or False
        return [config.ligue_name, url]

    # Supprime le premier élément s'il s'agit d'un préfixe
    parts = parts[1:]
    ligue = ' '.join([p for p in parts if p]).strip()
    config.ligue_name = ligue or False
    return [config.ligue_name, url]


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    print(fromUrl(driver))
