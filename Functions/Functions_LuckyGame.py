import datetime
import json
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

import config
import random


def save_session_data(data):
    try:
        # Read existing data
        try:
            with open('session_data.json', 'r') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        # Append new data
        existing_data.append(data)

        # Write back all data
        with open('session_data.json', 'w') as f:
            json.dump(existing_data, f, indent=4)
    except Exception as e:
        print(f"Error saving session data: {e}")


def get_result(driver):
    result = driver.find_element(By.XPATH,
                                 '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[3]/div/div[2]/div/div/input')
    result = result.get_attribute('value')
    return result


def getSolde(driver, older_solde):
    i = 0
    solde = driver.find_element(By.XPATH,
                                '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[1]/div[2]/div[1]/div/input').get_attribute(
        'value')
    while str(solde) == str(older_solde) and i < 100:
        i = i + 1
        solde = driver.find_element(By.XPATH,
                                    '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[1]/div[2]/div[1]/div/input').get_attribute(
            'value')
    return solde


def all_script(driver):
    win_session = config.win_session
    win = False
    min_unit = config.min_unit
    unit = config.unit
    old_unit = config.old_unit
    perte = config.perte
    side = config.side
    old_side = config.old_side
    old_result = config.old_result
    xpath_over = config.xpath_over
    xpath_under = config.xpath_under
    time.sleep(3)
    while not win or win < 100:

        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[1]/div[2]/div[1]/div/input'))
            )
            old_solde = driver.find_element(By.XPATH,
                                            '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[1]/div[2]/div[1]/div/input').get_attribute(
                'value')
            suggestedNumbers = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[3]/div/div[1]/div/div/input'))
            )
            suggestedNumbers = driver.find_element(By.XPATH,
                                                   '//*[@id="root"]/div[1]/div[2]/div[1]/div/section/div/div[3]/div/div[1]/div/div/input')
        except Exception as e:
            print(f"#E0001\nUne erreur est suggestedNumbers : {e}")
        else:
            try:

                suggestedNumbers.clear()
                if side == 'over' and old_side != side:
                    suggestedNumbers.send_keys("50")
                    button = driver.find_element(By.XPATH, xpath_over)
                    button.click()
                elif side == 'under' and old_side != side:
                    suggestedNumbers.send_keys("48")
                    button = driver.find_element(By.XPATH, xpath_under)
                    button.click()


            except Exception as e:
                print(f"#E0002\nUne erreur send key suggestedNumbers : {e}")
        # AMOUNT
        try:
            bet = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[2]/div[1]/div[1]/div[2]/input'))
            )
            bet = driver.find_element(By.XPATH,
                                      '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[2]/div[1]/div[1]/div[2]/input')
        except Exception as e:
            print(f"#E0003\nUne erreur send key suggestedNumbers : {e}")
        else:
            if unit <= min_unit:
                driver.find_element(By.XPATH,
                                    '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[2]/div[1]/div[1]/div[1]/div/div[3]').click()
                unit = min_unit
                old_unit = unit
            else:
                bet.clear()
                bet.send_keys(f"{unit:.8f}")  # Format with 9 decimal places to ensure proper decimal representation
                old_unit = unit
        # BET
        try:
            bet_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH,
                                                '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[2]/div[2]/button[1]')))
            bet_button = driver.find_element(By.XPATH,
                                             '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[2]/div[2]/button[1]')
        except Exception as e:
            print(f"#E0004\nUne erreur send key suggestedNumbers : {e}")
        else:

            bet_button.click()
            i = 0
            while 'danger' in driver.find_element(By.XPATH,
                                                  '//*[@id="root"]/div[1]/div[2]/div[1]/div/div/div/div[2]/div[2]/button[1]').get_attribute(
                'color'):
                i += 1
                if i > 20:
                    time.sleep(1)
                    if i > 25:
                        driver.get('https://luckygames.io/')
            old_side = side
            # solde = getSolde(driver, old_solde)
            result = get_result(driver)
            if str(result) == str(old_result):
                time.sleep(1)
                result = get_result(driver)
                if str(result) == str(old_result):
                    print('result == old_result')
                    old_result = False
                    old_side = False
                    # solde = 0
                    # old_solde = 1
                    driver.get('https://luckygames.io/')
                    win = False
            elif side == 'under' and int(result) < 48:
                win = True
            elif side == 'over' and int(result) > 50:
                win = True
            else:
                win = False
            old_result = result
        if win:
            print(f'{config.GREEN}WIN')
            print(f"result : {result}")
            print('side :', side)
            perte = perte - unit + min_unit
            gain = unit
            print(f"unit : {unit:.8f}")
            print(f"gain : {gain:.8f}")
            print(f"perte total : {perte:.8f}")
            # print(f"solde : {solde}")
            if perte > 0.00000000:
                unit = (unit * 2) + min_unit
                if unit - perte > min_unit:
                    unit = perte + min_unit
            else:
                perte = 0
                unit = min_unit
                win_session = True
                gain = -perte
                if not win:
                    win = 0
                else:
                    win = win + 1
                print('WIN SESSION')
            save_session_data({
                'WIN': True,
                'unit': f"{unit:.8f}",
                'perte': f"{perte:.8f}",
                'side': old_side,
                # 'solde': solde,
                'result': result,
                'gain': f"{gain:.8f}",
                'win_session': win_session,
                'time': datetime.datetime.now().strftime("%H:%M:%S")
            })
        else:
            print(f'{config.RED}LOSE')
            print('side :', side)
            print(f"result : {result}")
            side = random.choice(['over', 'under'])
            perte = perte + unit + min_unit
            gain = -unit
            print(f"perte : {perte:.8f}")
            print(f"unit : {unit:.8f}")
            print(f"gain : {gain:.8f}")
            print(f"perte total : {perte:.8f}")
            # print(f"solde : {solde}")
            unit = unit - min_unit
            if unit < min_unit:
                unit = min_unit
            save_session_data({
                'LOSE': True,
                'unit': f"{unit:.8f}",
                'perte': f"{perte:.8f}",
                'gain': f"{gain:.8f}",
                'side': old_side,
                # 'solde': solde,
                'result': result,
                'time': datetime.datetime.now().strftime("%H:%M:%S")
            })
