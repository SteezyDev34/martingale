from selenium.webdriver.chrome.service import Service

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
opt = Options()
try:
    opt.add_experimental_option("debuggerAddress", "localhost:7985")
    driver = webdriver.Chrome(executable_path='chromedriver.exe')
    driver = webdriver.Chrome(options=opt)
except Exception as e:
    print('tent 1')
    try:
        opt.add_experimental_option("debuggerAddress", "localhost:7985")
        service = Service(executable_path="chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=opt)
    except Exception as e:
        print('tent 2')
        try:
            opt = webdriver.ChromeOptions()
            opt.add_experimental_option("debuggerAddress", "localhost:7985")
            opt.binary_location = "chromedriver.exe"

            # Initialiser l'instance de WebDriver avec les options
            driver = webdriver.Chrome(options=opt)
        except:
            print(f'Une erreur est survenue : {e}')
            print('Merci de réessayer.')
        else:
            success = 1
    else:
        success = 1
else:
    success = 1

