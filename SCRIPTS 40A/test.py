import time

from selenium.webdriver.common.by import By

print('START')
import os

#Chargement de Chrome driver
from ChromeDriver.SetDriver10 import driver

all_bets = driver.find_element(By.CLASS_NAME, 'all-bets')

each_bet = all_bets.find_elements(By.TAG_NAME,'app-prono-recap')
betslist = []
for bet in each_bet:
    data = []
    top_info = bet.find_element(By.CLASS_NAME,'top-container')
    first_block = top_info.find_element(By.CLASS_NAME,'first-block')
    tags_container = first_block.find_element(By.CLASS_NAME,'tags-container')
    tags = tags_container.find_element(By.CLASS_NAME,'tags')
    sport = tags.find_element(By.CLASS_NAME,'sport-label').text
    thedate = tags_container.find_element(By.CLASS_NAME,'dates')
    thedate = thedate.find_elements(By.CLASS_NAME,'date')[0].text
    data.append(thedate)
    description = first_block.find_element(By.CLASS_NAME,'description').text
    data.append(description)
    secondblock = top_info.find_element(By.CLASS_NAME,'second-block')
    cote = secondblock.find_elements(By.CLASS_NAME,'number-block')[0].find_element(By.CLASS_NAME,'number-value').text
    data.append(cote)
    mise = secondblock.find_elements(By.CLASS_NAME,'number-block')[1].find_element(By.CLASS_NAME,'number-value').text.replace('€','')
    mise = float(mise) /10
    data.append(mise)
    win = secondblock.find_elements(By.CLASS_NAME,'number-block')[3].find_element(By.CLASS_NAME,'number-value').text
    if "-" in win:
        win ="Lost"
    elif win == "0€":
        win = "Refund"
    else:
        win = "Win"
    data.append(win)

    betslist.append(data)
print(betslist)

from datetime import datetime
def fordate(d):
    # Date au format JJ/MM/AAAA
    date_str = d

    # Conversion de la chaîne en objet datetime
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")

    # Conversion de l'objet datetime en chaîne au format AAAA-MM-JJ
    formatted_date = date_obj.strftime("%Y-%m-%d")

    return formatted_date
from selenium.webdriver.support.ui import Select
i=0
for bets in betslist:
    driver.get("https://www.auxobetting.fr/bilan/add-bet.php")
    bets[0] = fordate(bets[0])
    driver.find_element(By.CLASS_NAME,'champ_date_du_paris').send_keys(bets[0])
    driver.find_element(By.CLASS_NAME, 'champ_sport').send_keys('Baseball')
    driver.find_element(By.CLASS_NAME, 'champ_intitule').send_keys(bets[1])
    driver.find_element(By.CLASS_NAME, 'champ_cote').send_keys(str(bets[2].replace(',','.')))
    driver.find_element(By.CLASS_NAME, 'champ_mise').send_keys(str(bets[3]))
    select_element = driver.find_element(By.CLASS_NAME, 'champ_etat')
    select = Select(select_element)
    select.select_by_value(bets[4])
    if bets[4]  == "Lost":
        i+=1
        if i == 0:

            i=0
        else:
            driver.find_element(By.CLASS_NAME, 'send_bet').click()
    else:
        driver.find_element(By.CLASS_NAME, 'send_bet').click()


    time.sleep(2)
