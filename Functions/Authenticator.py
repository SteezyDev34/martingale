import platform
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from Functions.SimulateClick import click_with_real_mouse_input, click_with_real_mouse_login_button


# Accéder à une extension en utilisant son ID
def get_authenticator_code(driver):
    """
    Opens the authenticator extension and retrieves the code from the HTML element
    """
    extension_id = "bhghoamapcdpbohphigoooaddinpkbai"
    original_tab = driver.current_window_handle  # 1) onglet courant

    driver.switch_to.new_window("tab")

    driver.get(f"chrome-extension://{extension_id}/view/popup.html")

    # Wait for the codes element to be present and get the code
    try:
        # Wait for the code element with timeout class to be visible
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "code.timeout"))
        )

        # Wait for the timeout class to disappear
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "timeout"))
        )

        # Get the code element and its value after timeout disappeared
        code_element = driver.find_element(By.CLASS_NAME, "code")
        auth_code = code_element.text
        # 4) Ferme l’onglet courant
        driver.close()

        # 5) Reviens à l’onglet d’origine
        driver.switch_to.window(original_tab)
        return auth_code
    except Exception as e:
        print(f"Error getting authentication code: {e}")
        return None


def is_logged_in(driver):
    """
    Check if user is logged in by verifying if the AuthDropdown element exists
    Returns True if logged in, False otherwise
    """
    try:
        # Check if AuthDropdown element exists
        auth_dropdown = driver.find_elements(By.CLASS_NAME, 'auth-dropdown-trigger')
        # If element exists (length > 0), user is not logged in
        return len(auth_dropdown) == 0
    except Exception as e:
        print(f"Error checking login status: {e}")
        return False


def is_code_valid(driver, timeout=5):
    """
    Vérifie la présence du message d’erreur « Code incorrect».
    Retourne True si le code est valide (pas de message d’erreur),
    False si le message apparaît.
    """
    error_locator = (By.CSS_SELECTOR,
                     ".input-base__message.input-base__message--error.input-base-message")

    try:
        # On attend brièvement pour voir si le message d’erreur devient visible
        msg_is_present = WebDriverWait(driver, timeout).until(
            EC.text_to_be_present_in_element(error_locator, "Code incorrect")
        )
        # Si le texte apparaît, le code est incorrect
        return not msg_is_present  # -> False
    except TimeoutException:
        # Pas de message d’erreur pendant le délai : code probablement correct
        return True


def clear_field(driver, field):
    try:
        driver.execute_script("arguments[0].value = '';", field)
    except:
        mod = Keys.COMMAND if platform.system() == "Darwin" else Keys.CONTROL
        field.send_keys(mod, 'a')
        field.send_keys(Keys.BACKSPACE)


def loginProcess(driver, username="7696755", password="…"):
    loginsuccessful = False
    while not loginsuccessful:
        print('try login')
        try:
            driver.get("https://ca.1xbet.com/fr/")
            print('auht')
            # --- ouverture du formulaire
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.auth-dropdown-trigger')))
            click_with_real_mouse_login_button(driver, '.auth-dropdown-trigger')

            # --- attente du formulaire
            authFields = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".auth-form-fields")))

            # --- username
            user = authFields.find_element(By.CSS_SELECTOR, "input#username")
            # click_with_real_mouse_input(driver, 'input#username')
            # clear_field(driver, user)
            # user.send_keys(username)

            # --- password
            pw = authFields.find_element(By.CSS_SELECTOR, "input#username-password")
            # click_with_real_mouse_input(driver, 'input#username-password')
            # clear_field(driver, pw)
            ##pw.send_keys(password)

            # Click submit button
            print("Submitting login credentials...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "auth-form-fields__submit"))
            )
            submit_button = driver.find_element(By.CLASS_NAME, "auth-form-fields__submit")
            submit_button.click()

            # --- attente de disparition du formulaire
            WebDriverWait(driver, 10).until_not(EC.presence_of_element_located((By.CSS_SELECTOR, '.auth-form-fields')))
            loginsuccessful = True
            return True

        except Exception as e:
            print("Erreur loginProcess, retrying:", e)
            time.sleep(1)
            # on retentera sans lever d'exception bloquante


def processClick(driver, timeout=10):
    driver.switch_to.window(driver.window_handles[0])
    auth_dropdown = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, 'auth-dropdown-trigger'))
    )

    click_with_real_mouse_input(driver, 'auth-dropdown-trigger')


if __name__ == "__main__":
    from ChromeDriver.SetDriver1 import driver

    # Setup Chrome driver
    # 1) Lancez Chrome et ouvrez la page
    driver.get("https://ca.1xbet.com/fr/live/tennis")

    # Attempt login
    processClick(driver)
