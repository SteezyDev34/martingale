import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.DeleteBet import DeleteBet
from Functions.GetIfNewSite import GetIfNewSite
from Functions.ModalHandler import ModalHandler
from Functions.PlacerMise import PlacerMise
from Functions.ValidationDuParis import ValidationDuParis


# from ChromeDriver.SetDriver1 import driver


def PlacerCode(driver, code):
    sending_mise = False
    tentative = 0
    config.scriptType = 'LIVE'
    config.site_type = 'new_site'

    # Fonctions utilitaires pour manipuler proprement les champs (fallback JS si non interactif)
    def safe_clear(el):
        try:
            tag = el.tag_name.lower()
            readonly = el.get_attribute('readonly')
            disabled = el.get_attribute('disabled')
            if tag in ('input', 'textarea') and el.is_enabled() and not readonly and not disabled:
                try:
                    el.clear()
                except Exception:
                    # fallback JS clear
                    driver.execute_script(
                        "arguments[0].value = ''; arguments[0].setAttribute('value',''); arguments[0].textContent=''; arguments[0].innerText=''; arguments[0].dispatchEvent(new Event('input',{bubbles:true})); arguments[0].dispatchEvent(new Event('change',{bubbles:true})); arguments[0].blur();",
                        el)
            else:
                # clear wrapper/input via JS and try to clear visible text in parent containers
                driver.execute_script(
                    "var el=arguments[0]; try{ el.value=''; el.setAttribute('value',''); el.textContent=''; el.innerText=''; }catch(e){}; var p=el.parentElement; if(p){ try{ var d=p.querySelector('.input__field, .input-field, .input-base__container, .input-base'); if(d){ d.textContent=''; d.innerText=''; } }catch(e){} } ; try{ el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); el.blur(); }catch(e){}",
                    el)
        except Exception as e:
            config.log(f"safe_clear error: {e}")

    def force_set_value(el, value):
        """Forcer la valeur visible/attributs d'un input et de ses wrappers, puis déclencher les events."""
        try:
            driver.execute_script(
                "var el=arguments[0]; var v=arguments[1]; try{ el.value=v; el.setAttribute('value',v); el.textContent=v; el.innerText=v; }catch(e){}; var p=el.parentElement; if(p){ try{ var d=p.querySelector('.input__field, .input-field, .input-base__container, .input-base'); if(d){ d.textContent=v; d.innerText=v; } }catch(e){} } ; try{ el.dispatchEvent(new Event('input',{bubbles:true})); el.dispatchEvent(new Event('change',{bubbles:true})); el.focus(); el.blur(); }catch(e){}",
                el, str(value))
        except Exception as e:
            config.log(f"force_set_value error: {e}")

    def safe_send_keys(el, value):
        try:
            tag = el.tag_name.lower()
            readonly = el.get_attribute('readonly')
            disabled = el.get_attribute('disabled')
            if tag in ('input', 'textarea') and el.is_enabled() and not readonly and not disabled:
                try:
                    el.click()
                except Exception:
                    pass
                try:
                    el.clear()
                except Exception:
                    pass
                # Essayer de taper caractère par caractère pour déclencher les events frameworks
                try:
                    # s'assurer que le champ est sélectionné pour remplacer le contenu existant
                    try:
                        el.click()
                        driver.execute_script("arguments[0].select();", el)
                    except Exception:
                        pass
                    for ch in str(value):
                        el.send_keys(ch)
                        time.sleep(0.03)
                    # déclencher événements supplémentaires
                    driver.execute_script(
                        "arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true})); arguments[0].blur();",
                        el)
                    return
                except Exception:
                    # fallback JS si send_keys échoue
                    driver.execute_script(
                        "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true})); arguments[0].blur();",
                        el, value)
                    try:
                        force_set_value(el, value)
                    except Exception:
                        pass
                    return
            else:
                driver.execute_script(
                    "arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true})); arguments[0].blur();",
                    el, value)
        except Exception as e:
            config.log(f"safe_send_keys error: {e}")

    def resolve_to_input(el):
        """Si l'élément trouvé est un wrapper, retourner l'input descendant réel si possible."""
        try:
            tag = el.tag_name.lower()
        except Exception:
            return el
        if tag in ('input', 'textarea'):
            return el
        # chercher un input descendant
        try:
            return el.find_element(By.TAG_NAME, 'input')
        except Exception:
            try:
                return el.find_element(By.CSS_SELECTOR, 'input')
            except Exception:
                return el

    while not sending_mise:
        tentative += 1
        DeleteBet(driver)
        try:

            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['coupon_loader_toggle'][config.site_type])))
            cpn_setting = driver.find_element(By.CLASS_NAME, config.classes['coupon_loader_toggle'][config.site_type])
            # Ne cliquer le toggle que si aucun input coupon_loader_input visible n'est présent
            try:
                input_selector = config.classes['coupon_loader_input'][config.site_type]
                inputs = driver.find_elements(By.CLASS_NAME, input_selector)
                any_visible = False
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            any_visible = True
                            break
                    except Exception:
                        continue
                if not any_visible:
                    try:
                        cpn_setting.click()
                        print('click')
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", cpn_setting)
                            print('click(js)')
                        except Exception:
                            config.log('Impossible de cliquer sur coupon_loader_toggle')
                else:
                    config.log('coupon_loader_input déjà présent, pas de click toggle')
            except Exception:
                # en cas de problème, essayer de cliquer pour ouvrir le panneau
                try:
                    cpn_setting.click()
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", cpn_setting)
                    except Exception:
                        config.log('Erreur lors du click fallback sur coupon_loader_toggle')
        except Exception as e:
            config.log("        CHAMP DE COUPON NON TROUVÉ")
            if tentative > 10:
                return False
            if tentative > 2:
                ModalHandler(driver)
        else:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, config.classes['coupon_loader_input'][config.site_type])))
            raw = driver.find_element(By.CLASS_NAME,
                                      config.classes['coupon_loader_input'][config.site_type])
            cpn_setting = resolve_to_input(raw)
            # Ne cliquer sur le wrapper que si aucun <input> descendant
            try:
                if cpn_setting is raw:
                    try:
                        raw.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", raw)
                        except Exception:
                            pass
                else:
                    # si on a un <input>, ne pas cliquer le wrapper — laisser safe_send_keys gérer le focus
                    pass
            except Exception:
                pass
            safe_clear(cpn_setting)
            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, config.classes['coupon_loader_input'][config.site_type])))
                raw = driver.find_element(By.CLASS_NAME,
                                          config.classes['coupon_loader_input'][config.site_type])
                cpn_setting = resolve_to_input(raw)
                try:
                    if cpn_setting is raw:
                        try:
                            raw.click()
                        except Exception:
                            try:
                                driver.execute_script("arguments[0].click();", raw)
                            except Exception:
                                pass
                    else:
                        pass
                except Exception:
                    pass
                safe_clear(cpn_setting)
            except Exception as e:
                cpn_events_input_selector = config.classes['coupon_loader_input'][config.site_type]
                config.log(f"Erreur de recherche {cpn_events_input_selector} ")
                if tentative > 10:
                    return False
                if tentative > 2:
                    ModalHandler(driver)
            else:

                # conserver une référence à l'input pour debug
                safe_send_keys(cpn_setting, str(code))
                input_el = cpn_setting
                l = input_el.get_attribute("value")
                config.log("code insérré : " + str(l))
                # Si la valeur visible n'apparaît pas, collecter des informations diagnostiques
                if str(l) != str(code):
                    try:
                        tag = input_el.tag_name
                    except Exception:
                        tag = '<unknown>'
                    try:
                        attrs = driver.execute_script(
                            "var el=arguments[0]; var at={}; for(var i=0;i<el.attributes.length;i++){at[el.attributes[i].name]=el.attributes[i].value;} return at;",
                            input_el)
                    except Exception:
                        attrs = {}
                    try:
                        textc = input_el.get_attribute('textContent') or driver.execute_script(
                            "return arguments[0].textContent;", input_el)
                    except Exception:
                        textc = ''
                    try:
                        inn = driver.execute_script("return arguments[0].innerText;", input_el)
                    except Exception:
                        inn = ''
                    config.log(f"DEBUG input tag:{tag} attrs:{attrs} textContent:{textc} innerText:{inn} value:{l}")
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'}); arguments[0].focus();",
                                              input_el)
                    except Exception:
                        pass
                    # Fallback: tenter de définir innerText/textContent/value via JS (pour contenteditable ou frameworks)
                    try:
                        driver.execute_script(
                            "arguments[0].innerText = arguments[1]; arguments[0].textContent = arguments[1]; arguments[0].value = arguments[1]; arguments[0].setAttribute('value', arguments[1]); arguments[0].dispatchEvent(new Event('input',{bubbles:true})); arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                            input_el, str(code))
                        try:
                            force_set_value(input_el, str(code))
                        except Exception:
                            pass
                    except Exception as e:
                        config.log(f"DEBUG fallback set error: {e}")
                    time.sleep(0.4)
                    try:
                        l2 = driver.execute_script(
                            "return arguments[0].value || arguments[0].getAttribute('value') || arguments[0].textContent || arguments[0].innerText;",
                            input_el)
                    except Exception:
                        l2 = None
                    config.log("DEBUG après fallback value: " + str(l2))
                if str(l) == str(code):
                    # Attendre la présence d'au moins un bouton (même désactivé), puis le chercher
                    cpn_btn_theme_brand_selector = config.classes['coupon_loader_button'][config.site_type]
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CLASS_NAME, cpn_btn_theme_brand_selector)))
                    except Exception:
                        config.log(
                            f"DEBUG: aucun bouton {cpn_btn_theme_brand_selector} trouvé dans le DOM pour le moment")

                    # Recherche du bouton 'Charger' UNIQUEMENT dans un .coupon-loader__box
                    def find_charger_button_in_box():
                        """Cherche le bouton contenant le texte 'Charger' uniquement dans les .coupon-loader__box."""
                        try:
                            boxes = driver.find_elements(By.CSS_SELECTOR, '.coupon-loader__box')
                            for box in boxes:
                                try:
                                    buttons = box.find_elements(By.TAG_NAME, 'button')
                                    for btn in buttons:
                                        try:
                                            txt = driver.execute_script(
                                                "return (arguments[0].innerText || arguments[0].textContent || '').trim().toLowerCase();",
                                                btn)
                                        except Exception:
                                            txt = ''
                                        if 'charger' in txt:
                                            config.log(f"DEBUG bouton 'Charger' trouvé dans coupon-loader__box: {txt}")
                                            return btn
                                except Exception:
                                    continue
                        except Exception:
                            pass
                        return None

                    try:
                        print('Recherche du bouton charger dans .coupon-loader__box...')
                        cpn_setting = find_charger_button_in_box()
                        if not cpn_setting:
                            config.log("DEBUG: bouton 'Charger' introuvable dans .coupon-loader__box")
                            raise Exception('Bouton Charger non trouvé dans coupon-loader__box')
                        if not cpn_setting:
                            # Debug: compter les éléments trouvés par classe et afficher leur HTML
                            els = driver.find_elements(By.CLASS_NAME, cpn_btn_theme_brand_selector)
                            config.log(f"DEBUG: {len(els)} element(s) trouvés pour {cpn_btn_theme_brand_selector}")
                            for i, e in enumerate(els[:5]):
                                try:
                                    outer = driver.execute_script("return arguments[0].outerHTML;", e)
                                except Exception:
                                    outer = '<outerHTML unavailable>'
                                config.log(f"DEBUG element {i}: {outer}")
                            # afficher le HTML autour de l'input (si disponible)
                            try:
                                surrounding = driver.execute_script(
                                    "return arguments[0].parentElement ? arguments[0].parentElement.outerHTML : ''",
                                    input_el)
                            except Exception:
                                surrounding = ''
                            config.log(f"DEBUG input surrounding: {surrounding}")
                            raise Exception('load button not found')

                        # Forcer activation si besoin
                        try:
                            is_disabled_attr = cpn_setting.get_attribute('disabled')
                        except Exception:
                            is_disabled_attr = None
                        try:
                            classes_btn = cpn_setting.get_attribute('class') or ''
                        except Exception:
                            classes_btn = ''
                        try:
                            txt = (cpn_setting.text or driver.execute_script(
                                "return arguments[0].innerText||arguments[0].textContent;",
                                cpn_setting) or '').strip().lower()
                        except Exception:
                            txt = ''
                        if (is_disabled_attr or 'ui-button--is-disabled' in classes_btn) and 'charger' in txt:
                            try:
                                driver.execute_script(
                                    "arguments[0].removeAttribute('disabled'); arguments[0].classList.remove('ui-button--is-disabled');",
                                    cpn_setting)
                                time.sleep(0.05)
                            except Exception:
                                pass

                        # Tentatives de click avec fallbacks
                        clicked = False
                        try:
                            cpn_setting.click()
                            clicked = True
                        except Exception:
                            try:
                                driver.execute_script("arguments[0].click();", cpn_setting)
                                clicked = True
                            except Exception:
                                try:
                                    driver.execute_script(
                                        "var e = document.createEvent('MouseEvents'); e.initEvent('click', true, true); arguments[0].dispatchEvent(e);",
                                        cpn_setting)
                                    clicked = True
                                except Exception as click_err:
                                    config.log(f"DEBUG click error: {click_err}")
                        if not clicked:
                            raise Exception('click failed')

                        validate_bet = False
                        config.log('On place la mise', 'infos', True, 2)
                        config.log_clear_line()
                        while not PlacerMise(driver):
                            config.log('On vérifie le score pour valider le paris', 'info', False, 2)
                            config.log_clear_line()
                            ##VALIDATION DU PARIS SI SCORE OK
                        while not validate_bet:
                            # VÉRIFICATION DU SCORE ACTUEL
                            tentative = tentative + 1
                            if ValidationDuParis(driver):
                                validate_bet = True
                                return True
                    except Exception as e:
                        config.log(f'{e}')
                        if tentative > 2:
                            ModalHandler(driver)
                            if tentative > 10:
                                return False



                else:
                    config.log('mauvaise code insérée!', 'warning')
                    time.sleep(1)


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    config.site_type = 'new_site'

    GetIfNewSite(driver)
    code = 'V82KD'
    PlacerCode(driver, code)
