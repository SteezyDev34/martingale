import asyncio
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetJeuActuel import GetJeuActuel
from Functions.GetSetActuel import GetSetActuel


# Fonction: Version asynchrone de GetScoreActuel pour surveillance continue des scores
# Commentaire: Surveille les scores en arrière-plan pendant l'exécution du script principal
async def GetScoreActuelAsync(driver, stop_event=None):
    """
    Version asynchrone de GetScoreActuel qui surveille continuellement les scores
    
    Args:
        driver: Instance du driver Selenium
        stop_event: Event asyncio pour arrêter la surveillance
    
    Returns:
        bool: True si la surveillance s'est bien déroulée, False en cas d'erreur
    """
    config.score_actuel = False
    tentative = 0
    first = True
    
    while stop_event is None or not stop_event.is_set():
        try:
            # Attendre que l'élément soit visible
            score_teams = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.CLASS_NAME,
                                                  config.classes['score_container'][config.site_type]))
            )
            score_teams = driver.find_elements(By.CLASS_NAME, config.classes['score_container'][config.site_type])
        except Exception as e:
            score_container_selector = config.classes['score_container'][config.site_type]
            print(f"#E0020\nUne erreur est survenue : {score_container_selector}")
            if not GetIfMatchPage(driver):
                config.error = True
                return False
            tentative = tentative + 1
            await asyncio.sleep(1)  # Attente asynchrone
            if tentative == 5:
                config.error = True
                return False
        else:
            try:
                nouveau_score = score_teams[0].text + ':' + score_teams[1].text
            except Exception as e:
                await asyncio.sleep(0.5)  # Petite pause avant de réessayer
                continue
            else:
                if config.saved_score != nouveau_score:
                    config.score_actuel = nouveau_score
                    if not first:
                        await record_scores_async(driver)
                    else:
                        first = False
                        await asyncio.sleep(2)  # Attente asynchrone
                        continue
                config.saved_score = nouveau_score
                
        # Pause entre les vérifications pour éviter une surcharge
        await asyncio.sleep(1)
    
    return True


# Fonction: Version asynchrone de record_scores
# Commentaire: Enregistre les scores de manière asynchrone
async def record_scores_async(driver):
    """
    Version asynchrone de record_scores
    
    Args:
        driver: Instance du driver Selenium
    """
    GetSetActuel(driver)
    GetJeuActuel(driver)
    nouveau_score = {'set': config.set_actuel, 'jeu': config.jeu_actuel, 'score': config.score_actuel}
    config.log(nouveau_score, indent=2)
    # Si le dictionnaire n'existe pas encore, l'ajouter
    config.all_scores.update({len(config.all_scores): nouveau_score})


# Fonction: Démarrer la surveillance asynchrone des scores
# Commentaire: Lance la surveillance en arrière-plan
async def start_score_monitoring(driver):
    """
    Démarre la surveillance asynchrone des scores
    
    Args:
        driver: Instance du driver Selenium
    
    Returns:
        tuple: (task, stop_event) pour contrôler la surveillance
    """
    stop_event = asyncio.Event()
    task = asyncio.create_task(GetScoreActuelAsync(driver, stop_event))
    return task, stop_event


# Fonction: Arrêter la surveillance asynchrone des scores
# Commentaire: Arrête proprement la surveillance
async def stop_score_monitoring(task, stop_event):
    """
    Arrête la surveillance asynchrone des scores
    
    Args:
        task: Tâche asyncio de surveillance
        stop_event: Event pour arrêter la surveillance
    """
    stop_event.set()
    try:
        await asyncio.wait_for(task, timeout=5.0)
    except asyncio.TimeoutError:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver
    
    async def test_async():
        config.site_type = 'old_site'
        task, stop_event = await start_score_monitoring(driver)
        
        # Simuler une exécution pendant 30 secondes
        await asyncio.sleep(30)
        
        # Arrêter la surveillance
        await stop_score_monitoring(task, stop_event)
    
    # Exécuter le test
    asyncio.run(test_async())
    
    while True:
        time.sleep(3)
        print('test')
        