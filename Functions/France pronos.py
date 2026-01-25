import json

def extract_pronos(driver, output_path="pronos.json"):
    """
    Extrait les données de chaque prono depuis les balises <app-prono-recap> et les sauvegarde dans un fichier JSON.
    """
    pronos = []
    elements = driver.find_elements(By.TAG_NAME, "app-prono-recap")
    for el in elements:
        try:
            # Cibler le div interne
            recap_div = el.find_element(By.CSS_SELECTOR, "div.app-prono-recap")
            sport = recap_div.find_element(By.CSS_SELECTOR, ".sport-label").text.strip()
            tags = [tag.text.strip() for tag in recap_div.find_elements(By.CSS_SELECTOR, ".tag")]
            date = recap_div.find_element(By.CSS_SELECTOR, ".date.bold").text.strip()
            hour = recap_div.find_element(By.CSS_SELECTOR, ".date.hour.bold").text.strip()
            tournoi = recap_div.find_element(By.CSS_SELECTOR, ".title-3").text.strip()
            description = recap_div.find_element(By.CSS_SELECTOR, ".description").text.strip()
            # Bloc Cote/Mise/Gain/Perte/Bénéfice
            number_blocks = recap_div.find_elements(By.CSS_SELECTOR, ".number-block")
            # Extraction par titre
            def get_number_value(blocks, titre):
                for block in blocks:
                    try:
                        title_elem = block.find_element(By.CSS_SELECTOR, ".number-title")
                        if titre.lower() in title_elem.text.lower():
                            value_elem = block.find_element(By.CSS_SELECTOR, ".number-value")
                            return value_elem.text.strip()
                    except Exception:
                        continue
                # Si aucune correspondance exacte, retourner la première valeur trouvée
                for block in blocks:
                    try:
                        value_elem = block.find_element(By.CSS_SELECTOR, ".number-value")
                        return value_elem.text.strip()
                    except Exception:
                        continue
                return ""
            cote = get_number_value(number_blocks, "Cote")
            mise = get_number_value(number_blocks, "Mise")
            gain = get_number_value(number_blocks, "Gain")
            perte = get_number_value(number_blocks, "Perte")
            benefice = get_number_value(number_blocks, "Bénéfice")
            # Statut du prono (bouton)
            try:
                statut = recap_div.find_element(By.CSS_SELECTOR, ".details-button .mdc-button__label").text.strip()
            except Exception:
                statut = ""
            prono = {
                "sport": sport,
                "tags": tags,
                "date": date,
                "hour": hour,
                "tournoi": tournoi,
                "description": description,
                "cote": cote,
                "mise": mise,
                "gain": gain,
                "perte": perte,
                "benefice": benefice,
                "statut": statut
            }
            pronos.append(prono)
        except Exception as e:
            print(f"Erreur lors de l'extraction d'un prono : {e}")

    # Sauvegarde dans un fichier JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pronos, f, ensure_ascii=False, indent=2)
    print(f"{len(pronos)} pronos extraits et sauvegardés dans {output_path}")
import time
import os
import sys
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    TimeoutException,
    StaleElementReferenceException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

import json

def extract_pronos(driver, output_path="pronos.json"):
    """
    Extrait les données de chaque prono depuis les balises <app-prono-recap> et les sauvegarde dans un fichier JSON.

    Args:
        driver (webdriver.Chrome): Instance du navigateur Selenium
        output_path (str): Chemin du fichier de sortie JSON
    """
    pronos = []
    elements = driver.find_elements(By.TAG_NAME, "app-prono-recap")
    for el in elements:
        try:
            sport = el.find_element(By.CSS_SELECTOR, ".sport-label").text.strip()
            print(sport)
            date = el.find_element(By.CSS_SELECTOR, ".date.bold").text.strip()
            print(date)
            hour = el.find_element(By.CSS_SELECTOR, ".date.hour.bold").text.strip()
            print(hour)
            tournoi = el.find_element(By.CSS_SELECTOR, ".title-3").text.strip()
            print(tournoi)
            description = el.find_element(By.CSS_SELECTOR, ".description").text.strip()
            print(description)
            cote = el.find_element(By.XPATH, ".//div[contains(@class,'number-title') and contains(text(),'Cote')]/following-sibling::div").text.strip()
            print(cote)
            mise = el.find_element(By.XPATH, ".//div[contains(@class,'number-title') and contains(text(),'Mise')]/following-sibling::div").text.strip()
            print(mise) 
            gain = el.find_element(By.XPATH, ".//div[contains(@class,'number-title') and contains(text(),'Gain')]/following-sibling::div").text.strip()
            print(gain)
            statut = el.find_element(By.CSS_SELECTOR, ".details-button .mdc-button__label").text.strip()
            print(statut)

            prono = {
                "sport": sport,
                "date": date,
                "hour": hour,
                "tournoi": tournoi,
                "description": description,
                "cote": cote,
                "mise": mise,
                "gain": gain,
                "statut": statut
            }
            pronos.append(prono)
        except Exception as e:
            print(f"Erreur lors de l'extraction d'un prono : {e}")

    # Sauvegarde dans un fichier JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pronos, f, ensure_ascii=False, indent=2)
    print(f"{len(pronos)} pronos extraits et sauvegardés dans {output_path}")

# Exemple d'utilisation dans ton script principal :
# extract_pronos(driver)
def scroll_to_bottom(driver):
    """
    Fait défiler la page jusqu'en bas.

    Args:
        driver (webdriver.Chrome): Instance du navigateur Selenium
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def main():
    """
    Ouvre la page web, clique sur le bouton 'Charger 50 paris de plus' tant qu'il est présent,
    et gère les exceptions pour garantir la robustesse du script.
    """
    try:
        config.localhost = 43151
        from ChromeDriver.SetDriver import get_script_driver

        num_fenetre = 0
        driver = get_script_driver(num_fenetre)
        wait = WebDriverWait(driver, 10)

        while True:
            scroll_to_bottom(driver)
            try:
                # XPATH robuste pour ignorer les espaces multiples et caractères invisibles
                button = wait.until(
                    EC.visibility_of_element_located((
                        By.XPATH,
                        "//button[.//div[@class='label' and contains(translate(normalize-space(.), ' ', ' '), 'Charger') and contains(translate(normalize-space(.), ' ', ' '), '50 paris de plus')]]"
                    ))
                )
                button.click()
                time.sleep(1)
                scroll_to_bottom(driver)
            except TimeoutException:
                # Le bouton n'est plus présent ou visible
                print("Bouton 'Charger 50 paris de plus' introuvable, fin du script.")
                break
            except (ElementClickInterceptedException, StaleElementReferenceException) as e:
                print(f"Exception lors du clic : {e}. Nouvelle tentative après 1 seconde.")
                time.sleep(1)
                continue
            except NoSuchElementException:
                print("Bouton non trouvé, fin du script.")
                break

    finally:
        driver.quit()
        print("Script terminé proprement.")


if __name__ == "__main__":
    config.localhost = 43151
    from ChromeDriver.SetDriver import get_script_driver

    num_fenetre = 0
    driver = get_script_driver(num_fenetre)
    extract_pronos(driver)
