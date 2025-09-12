import time

import requests
from selenium.webdriver.common.by import By

import config


def SendBetData(driver):
    """
    Fonction pour extraire les informations d'un pari depuis une modale avec Selenium
    et envoyer les données à une API.

    :param driver: Instance de Selenium WebDriver.
    """
    try:
        # Attendre que la modal soit chargée
        time.sleep(5)

        # Récupérer la modal
        modal = driver.find_element(By.CLASS_NAME, "modal__content")

        # Extraire les informations de la modal
        coupon_number = modal.find_element(By.CLASS_NAME, "ui-coupon-modal-header__info").text.replace("Coupon № ", "")
        cote_globale = modal.find_element(By.XPATH,
                                          "//span[contains(text(), 'Cote globale')]/following-sibling::div/span").text
        type_pari = modal.find_element(By.XPATH,
                                       "//span[contains(text(), 'Type de pari')]/following-sibling::div/span").text
        mise = modal.find_element(By.XPATH, "//span[contains(text(), 'Mise')]/following-sibling::div/span").text
        gains_potentiels = modal.find_element(By.XPATH,
                                              "//span[contains(text(), 'Gains potentiels')]/following-sibling::div/span").text

        # Récupérer les informations du match
        match = modal.find_element(By.CLASS_NAME, "ui-coupon-bet-teams").text
        cote = modal.find_element(By.CLASS_NAME, "ui-coupon-coef__value").text

        # Construire un dictionnaire avec les informations
        bet_data = {
            "coupon_number": coupon_number,
            "cote_globale": cote_globale,
            "type_pari": type_pari,
            "mise": mise,
            "gains_potentiels": gains_potentiels,
            "match": match,
            "cote": cote,
            "statut": None,
            "script": config.scriptType
        }

        print("✅ Informations extraites :", bet_data)

        # Envoyer les données à l'API en JSON
        api_url = f"{config.api_url}/save_bet" + config.scriptType + "/"
        response = requests.post(api_url, json=bet_data)

        # Vérifier la réponse de l'API
        if response.status_code == 200:
            print("✅ Données envoyées avec succès à l'API !")
        else:
            print(f"❌ Erreur lors de l'envoi à l'API : {response.text}")

    except Exception as e:
        print(f"❌ Erreur : {e}")
