from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
projectPath = os.path.dirname(os.path.abspath(__file__))
opt = Options()
opt.add_experimental_option("debuggerAddress", "localhost:7968")
service = Service(r"/Users/steezy/PycharmProjects/1xbot/venv/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=opt)
print(7968)