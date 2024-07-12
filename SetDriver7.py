from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
opt = Options()
opt.add_experimental_option("debuggerAddress", "localhost:7972")
service = Service(r"/Users/steezy/PycharmProjects/1xbot/venv/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=opt)