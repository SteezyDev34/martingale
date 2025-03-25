from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
Path = os.path.dirname(os.path.abspath(__file__))
opt = Options()
try:
    print(Path+'\chromedriver.exe')
    opt.add_experimental_option("debuggerAddress", "localhost:7975")
    driver = webdriver.Chrome(executable_path='..\chromedriver.exe')
    driver = webdriver.Chrome(options=opt)
except Exception as e:
    print('tent 1',e)
    try:
        opt.add_experimental_option("debuggerAddress", "localhost:7975")
        service = Service(executable_path=Path+"\chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=opt)
    except Exception as e:
        print('tent 2',e)
        try:
            opt = webdriver.ChromeOptions()
            opt.add_experimental_option("debuggerAddress", "localhost:7975")
            opt.binary_location =Path+"\chromedriver.exe"

            # Initialiser l'instance de WebDriver avec les options
            driver = webdriver.Chrome(options=opt)
        except Exception as e:
            print(f'Une erreur est survenue : {e}')
            print('Merci de réessayer.')
        else:
            success = 1
    else:
        success = 1
else:
    success = 1

