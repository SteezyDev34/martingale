import base64
import os
import sys
import time

# Ajouter le chemin du projet au PYTHONPATH pour permettre l'importation de config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import config


def cleanJson(raw_response):
    cleaned_response = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
    return cleaned_response


# Initialisation du client OpenAI avec la clé API
from openai import OpenAI

# Initialiser le client OpenAI
client = OpenAI(
    api_key='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')


# 🖼️ Charger l'image et la convertir en base64
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# 🧾 Envoyer l'image à ChatGPT avec des instructions spécifiques
def extraire_pari_depuis_image(image_path):
    image_b64 = image_to_base64(image_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Tu es un lecteur d'image pour retourner le texte contenu dans un image en texte brut. "
                           "Les images envoyées sont des captures d'écran de ticket de paris sportifs. "
                           "Il faut extraire les équipes,la catégorie, le type de pari placé, la selection et la cote. "
                           "Si le mot corner ou cartons jaunes, ou fautes ou un autre est en surbrillance il s'agit de la categorie"
                           "Voici le dictionnaire de référence categorie:type de parie à respecter : "
                           f"{config.xbet_type_list}."
                           "la date du paris est dans le nom de l'image, si  il n'y a pas de date, tu mets la date d'aujourd'hui."
                           "Si tu vois générateur de paris, c'est qu'il ya plusieurs evenement sur le meme match, tu renvoie une erreur avec le texte de l'image."
                           "par exemple si le fichier s'appelle media_20250413_204440.jpg, la date est donc 13/04/2025. "
                           "par exemple si le fichier s'appelle img.jpg, la date est aujourd'hui. "
                           "par exemple si le fichier s'appelle Capture-decran_1-4-2025_205148_stake.bet_.jpeg, la date est donc 01/04/2025. "
                           "Si le fichier n'a pas de date, tu mets la date d'aujourd"
                           "Tu dois retourner un JSON avec uniquement ces données extraites sans raisonement ou explication de ce que tu fais, par exemple : "
                           "{\"date\": \"30/10/1989\", "
                           "{\"equipe_1\": \"Kopriva, Vit\", \"equipe_2\": \"Sonego, Lorenzo\", "
                           "\"categorie\": \"Temps réglementaire\",\"type_de_pari\": \"Les deux équipes qui marquent\", "
                           "\"selection\": \"oui\", \"odds\": \"1.52\", \"tipster\": \"marco\"}"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": f"Voici une capture d'écran de ticket de pari, le fichier s'appelle {image_path} merci d'extraire les données au format JSON. et de retourner uniquement le json"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                ]
            }
        ],
        max_tokens=500
    )
    return cleanJson(response.choices[0].message.content)


def fordate(date_str):
    # Convert date format if needed
    return date_str


def submit_bet_to_website(driver, betslist):
    for bets in betslist:
        driver.get("https://auxobeg.cluster030.hosting.ovh.net/bilan/add-bet.php")
        bets[0] = fordate(bets[0])
        driver.find_element(By.CLASS_NAME, 'champ_date_du_paris').send_keys(bets[0])
        driver.find_element(By.CLASS_NAME, 'champ_sport').send_keys('Autre')
        driver.find_element(By.CLASS_NAME, 'champ_intitule').send_keys(bets[1])
        driver.find_element(By.CLASS_NAME, 'champ_cote').send_keys(str(bets[2].replace(',', '.')))
        driver.find_element(By.CLASS_NAME, 'champ_mise').send_keys(str(bets[3]))
        driver.find_element(By.CLASS_NAME, 'champ_code').send_keys('code' + str(time.time()))
        select_element = driver.find_element(By.CLASS_NAME, 'champ_etat')
        select = Select(select_element)
        select.select_by_value(bets[4])

        driver.find_element(By.CLASS_NAME, 'send_bet').click()

        time.sleep(2)


if __name__ == "__main__":
    # Example usage
    # Utiliser un chemin absolu pour l'image
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    image_path = os.path.join(project_path, "media_20250413_204440.jpg")

    if os.path.exists(image_path):
        result = extraire_pari_depuis_image(image_path)
        # Initialize your webdriver here
        # driver = webdriver.Chrome()  # or whatever driver you're using
        # submit_bet_to_website(driver, result)
        print(result)
    else:
        print(f"Erreur: Le fichier image {image_path} n'existe pas.")
