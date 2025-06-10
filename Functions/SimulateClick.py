import platform
import time

import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def click_with_real_mouse_login_button(driver, css_selector, timeout=5, move_duration=0.5):
    # 1) Attendre que l'élément soit cliquable
    wait = WebDriverWait(driver, timeout)
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))

    # 2) Le centrer dans la vue
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    time.sleep(0.2)

    # 3) Récupérer position/tailles + screenX/Y + DPR d’un seul coup
    data = driver.execute_script("""
        const r = arguments[0].getBoundingClientRect();
        return {
            left: r.left, top: r.top,
            width: r.width, height: r.height,
            screenX: window.screenX, screenY: window.screenY,
            dpr: window.devicePixelRatio
        };
    """, elem)

    # 4) Calculer le centre en CSS pixels absolus
    css_center_x = data['screenX'] + data['left'] + data['width'] / 4
    css_center_y = data['screenY'] + data['top'] + data['height'] + 50

    # 5) Si macOS, convertir en device pixels (Retina)
    if platform.system() == "Darwin":
        screen_x = int(css_center_x * data['dpr'])
        screen_y = int(css_center_y)
    else:
        print('screen_x', css_center_x)
        screen_x = int(css_center_x)
        screen_y = int(css_center_y)
    driver.switch_to.window(driver.window_handles[0])
    # 6) Déplacer la souris et cliquer
    pyautogui.moveTo(screen_x, screen_y, duration=move_duration)
    pyautogui.click()
    time.sleep(2)


def click_with_real_mouse_input(driver, css_selector, timeout=5, move_duration=0.5):
    # 1) Attendre que l'élément soit cliquable
    wait = WebDriverWait(driver, timeout)
    elem = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector)))

    # 2) Le centrer dans la vue
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
    time.sleep(0.2)

    # 3) Récupérer position/tailles + screenX/Y + DPR d’un seul coup
    data = driver.execute_script("""
        const r = arguments[0].getBoundingClientRect();
        return {
            left: r.left, top: r.top,
            width: r.width, height: r.height,
            screenX: window.screenX, screenY: window.screenY,
            dpr: window.devicePixelRatio
        };
    """, elem)

    # 4) Calculer le centre en CSS pixels absolus
    css_center_x = data['screenX'] + data['left'] + data['width'] / 2
    css_center_y = data['screenY'] + data['top'] + data['height'] + 30

    # 5) Si macOS, convertir en device pixels (Retina)
    if platform.system() == "Darwin":
        screen_x = int(css_center_x * data['dpr'])
        screen_y = int(css_center_y)
    else:
        screen_x = int(css_center_x)
        screen_y = int(css_center_y)
    driver.switch_to.window(driver.window_handles[0])
    # 6) Déplacer la souris et cliquer
    pyautogui.moveTo(screen_x, screen_y, duration=move_duration)
    time.sleep(2)
