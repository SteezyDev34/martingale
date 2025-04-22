from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# Accéder à une extension en utilisant son ID
def get_authenticator_code(driver):
    """
    Opens the authenticator extension and retrieves the code from the HTML element
    """
    extension_id = "bhghoamapcdpbohphigoooaddinpkbai"
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
        auth_dropdown = driver.find_elements(By.CSS_SELECTOR, '[data-component="AuthDropdown"]')
        # If element exists (length > 0), user is not logged in
        return len(auth_dropdown) == 0
    except Exception as e:
        print(f"Error checking login status: {e}")
        return False


def loginProcess(driver, username="7696755", password="Scorpio971n#1xbet3"):
    """
    Logs into the account using provided credentials
    """
    try:
        # Click on auth dropdown to open login form
        print("Opening login form...")
        auth_dropdown = driver.find_element(By.CSS_SELECTOR, '[data-component="AuthDropdown"]')
        auth_dropdown.click()

        # Wait for form fields to be present
        print("Waiting for login form fields...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "auth-form-fields"))
        )

        # Find and fill username field
        print("Entering username...")
        username_field = driver.find_element(By.ID, "username")
        username_field.clear()
        username_field.send_keys(username)

        # Find and fill password field
        print("Entering password...")
        password_field = driver.find_element(By.ID, "username-password")
        password_field.clear()
        password_field.send_keys(password)

        # Click submit button
        print("Submitting login credentials...")
        submit_button = driver.find_element(By.CLASS_NAME, "auth-form-fields__submit")
        submit_button.click()

        # Wait for login to complete (auth dropdown to disappear)
        print("Waiting for initial login to complete...")
        WebDriverWait(driver, 10).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-component="AuthDropdown"]'))
        )

        # Wait for two-factor authentication form
        print("Waiting for 2FA form...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "auth-form-two-step"))
        )

        # Get authentication code
        print("Getting 2FA code from authenticator...")
        auth_code = get_authenticator_code(driver)

        # Find and fill 2FA code input field
        print("Entering 2FA code...")
        code_field = driver.find_element(By.CSS_SELECTOR, ".auth-form-two-step__field input")
        code_field.clear()
        code_field.send_keys(auth_code)

        # Click confirm button
        print("Submitting 2FA code...")
        confirm_button = driver.find_element(By.CSS_SELECTOR, ".auth-form-two-step__submit")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".auth-form-two-step__submit"))
        )
        confirm_button.click()
        print("Login process completed successfully")
        return True

    except Exception as e:
        print(f"Error during login: {e}")
        return False
