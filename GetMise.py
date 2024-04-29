#GetMise
from selenium.webdriver.common.by import By


def main(driver,rattrape_perte,wantwin,perte):
    #driver.switch_to.window(driver.window_handles[0])
    #rattrape_perte = 0
    if rattrape_perte == 0:
        print('Pas de rattrapage, cote : 3')
        cote= 3
    elif rattrape_perte == 2 :
        print('Bonne proba, cote : 3')
        cote = 3
    else:
        print("Rattrapage, recuperation de la cote")
        try:
            cote = driver.find_elements(By.CLASS_NAME,
                'cpn-total__coef')[
                0].text
        except:
            print('erreur recup cote : 3')
            cote = 3
        else:
            print('cote recupéré ' + cote)
            if cote != '':
                try:
                    cote = float(cote)
                except:
                    print('error float cote : cote = 3')
                    cote = 3
            else:
                cote = 3
    mise = (float(wantwin) + float(perte)) / (float(cote) - 1)
    mise = round(mise, 2)
    if mise < 0.2:
        mise = 0.5
        print("cote : " + str(cote)+" | perte : " + str(
            perte) + " | wantwin : " + str(
            wantwin) + " | mise : " + str(mise))

    return [mise,cote]