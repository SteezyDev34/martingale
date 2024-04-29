# Function_GetMatchScore
from selenium.webdriver.common.by import By


def main(div_bet_score,score_to_start):
    get_bet_score = False
    get_if_icon_ball = div_bet_score.find_elements(By.XPATH,
                                                   './/span[@class="c-events-scoreboard__ball"]/div[not(contains(@style,"display: none;"))]')
    try:
        bet_score = div_bet_score.text
        bet_score = bet_score.replace(
        '\n', '')
    except:
        print('Impossible de lire le score du match!')
        get_bet_score = False
    else:
        #print('score en cours : '+bet_score)
        if any(
                score_ok in bet_score
                for score_ok in
                score_to_start) and len(get_if_icon_ball) > 0:
            get_bet_score = True

    return get_bet_score