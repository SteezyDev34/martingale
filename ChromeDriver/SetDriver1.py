import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

import config

Path = os.path.dirname(os.path.abspath(__file__))
opt = Options()
if config.systeme == 'Windows':
    Path = Path + '\\chromedriver.exe'
else:
    Path = Path + '/chromedriver'
try:
    # 7978
    # 43151
    # 1035
    opt.add_experimental_option("debuggerAddress", "localhost:7879")
    # Utilisation correcte du chemin pour macOS
    driver = webdriver.Chrome(executable_path=Path, options=opt)
except Exception as e:
    try:
        opt.add_experimental_option("debuggerAddress", "localhost:7879")
        service = Service(executable_path=Path)  # Modification du chemin
        driver = webdriver.Chrome(service=service, options=opt)
    except Exception as e:
        try:
            opt = webdriver.ChromeOptions()
            opt.add_experimental_option("debuggerAddress", "localhost:7879")
            opt.binary_location = Path  # Chemin binaire adapté pour macOS
            # Initialiser l'instance de WebDriver avec les options
            driver = webdriver.Chrome(options=opt)
        except Exception as e:
            sys.stdout.write(f'\rUne erreur est survenue : {e}\n')
            sys.stdout.write('Merci de réessayer.\n')
        else:
            success = 1
    else:
        success = 1
else:
    success = 1
