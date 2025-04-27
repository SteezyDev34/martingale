from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.ModalHandler import ModalHandler
from Functions.PlacerMise import PlacerMise


def ValidationDuParis(driver, nexbet=False):
    validation = False
    tentative = 0
    config.log('validation paris', 'info', False, 2)
    config.log_clear_line()
    while not validation and tentative < 2:
        config.log('Vérification des paris validés')
        config.log_clear_line()
        config.log('        tentative', str(tentative))
        config.log_clear_line()

        # Vérification que le jeu actuel et le set actuel n'ont pas déjà été pariés
        if hasattr(config, 'validated_bet') and config.validated_bet is not None:
            current_qt = getattr(config, 'qt_actuel', None)

            if (config.looking_game is not None and current_qt is not None and
                    config.validated_bet.get('jeu') == config.looking_game and
                    config.validated_bet.get('qt') == current_qt):
                config.log(f"Ce jeu ({config.looking_game}) et ce set ({current_qt}) ont déjà été pariés. Annulation.")
                validation = True
                break  # Sortir de la boucle si le jeu et le set ont déjà été pariés
        config.log('boucle validation paris')
        config.log_clear_line()
        try:
            cpn_setting = driver.find_elements(By.CLASS_NAME, 'ui-number-input__field')[0]
            l = cpn_setting.get_attribute("value")
            config.log("mise insérée : " + str(l), 'info', False, 2)
        except Exception as e:
            config.log(e)
            tentative += 1
            config.log('erreur verification mise')
            break
        else:
            if str(l) == str(config.mise):
                sending_mise = 1
                config.log('RECHERCHE DU BOUTON PLACER UN PARIS', 'info', False, 2)
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME,
                                                        'coupon-buttons'))
                    )
                except Exception as e:
                    config.log(f"#E0021\nUne erreur est survenue : {e}")
                    config.log('zone de bouton non trouvé!')
                    tentative = tentative + 1
                    validation = ModalHandler(driver)
                else:
                    try:
                        PlacerMise(driver)
                        cpn_setting = driver.find_elements(By.CLASS_NAME, 'ui-number-input__field')[0]
                        l = cpn_setting.get_attribute(
                            "value")
                        config.log("mise insérrer : " + str(l))
                    except Exception as e:
                        config.log(f"#E005689\nUne erreur est survenue : {e}")
                        tentative = tentative + 1
                        if ModalHandler(driver):
                            validation = True
                    else:
                        if str(l) == str(config.mise):
                            getbtn = driver.find_element(By.CLASS_NAME, 'coupon-buttons')
                            try:
                                getbtn.click()
                            except:
                                tentative = tentative + 1
                                if ModalHandler(driver):
                                    validation = True
                            else:
                                tentative = tentative + 1
                                preloader = 1
                                printtext = 0
                                while preloader == 1:
                                    try:
                                        WebDriverWait(driver, 3).until(EC.visibility_of_element_located(
                                            (By.CLASS_NAME, "coupon-main-tab__preloader")))
                                    except:
                                        config.log('        pas de loader')
                                        preloader = 0
                                    else:
                                        if printtext == 0:
                                            config.log('        loading...')
                                            printtext = 1

                                if ModalHandler(driver):
                                    validation = True
                        else:
                            PlacerMise(driver)
                            tentative = tentative + 1
            else:
                PlacerMise(driver)
                tentative = tentative + 1
    if validation:
        # Store bet information in validated_bet variable
        from datetime import datetime
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config.validated_bet = {
            'montant': config.mise,
            'qt': config.qt_actuel if hasattr(config, 'qt_actuel') else None,
            'win': config.win_type,
            'timestamp': current_timestamp
        }
        config.placed_game = config.looking_game
        config.log(f'           {config.validated_bet}', 'info', True)
        config.perte = float(config.perte) + float(config.mise)
        config.wantwin = float(config.wantwin) + float(config.increment)
        # Calculate net profit based on stake, odds and losses
        config.netprofit = round(
            (float(config.mise) * float(config.cote)) - float(config.perte), 2)
        config.log(f'Potential Net profit: {config.netprofit}')
    return validation


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    driver.switch_to.window(driver.window_handles[0])
    config.mise = 0.2
    ValidationDuParis(driver)
