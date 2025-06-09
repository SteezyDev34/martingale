from selenium import webdriver
from selenium.webdriver.chrome.service import Service

service = Service(r"/Users/steezy/PycharmProjects/1xbot/venv/bin/chromedriver")
driver = webdriver.Chrome(service=service)
