import json

import requests

import config


# config.scriptType= "40A"
# config.ligue_name = "ATP"
# config.perte = 10
# Configuration du proxy

def getPerte():
    if getCompetRecup():
        url = "http://p-com.studio/api/strategy" + config.scriptType + "/get_perte.php"
        try:
            # Envoyer une requête GET à l'URL
            response = requests.get(url)
            # Vérifier que la requête a réussi
            response.raise_for_status()
            print(response.json())
            # Parser le JSON depuis la réponse
            if len(response.json()) > 0:
                pertes = response.json()[0]
            else:
                return False
            # Afficher les données pour vérification
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des données : {e}")
            return
        except json.JSONDecodeError as e:
            print(f"Erreur lors du parsing du JSON : {e}")
            return
        except Exception as e:
            print(f"pas de perte {e}")
        else:
            return pertes
    else:
        return


def getGlobalPerte():
    url = "http://p-com.studio/api/strategy40A/get_global_perte.php"
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        if len(response.json()) > 0:
            pertes = response.json()[0]
        else:
            return False
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    except Exception as e:
        print(f"pas de perte {e}")
    else:
        if float(pertes["perte"]) > 0:
            config.rattrape_perte = 1
        config.log(f'Perte global : {str(pertes["perte"])}', 'info', False, 2)

        return pertes


def delPerte(id):
    url = "http://p-com.studio/api/strategy" + config.scriptType + "/del_perte.php?id=" + str(id)
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        print(response.json())
        result = response.json()
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    except Exception as e:
        print(f"Pas de suppression de perte {e}")
    else:
        print(result)
        return True


def getCompetRecup():
    url = "http://p-com.studio/api/strategy" + config.scriptType + "/get_compet_recup.php"
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        compets = response.json()
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    except Exception as e:
        print(f"Pas de compet {e}")
    else:
        compet_ok_list = compets["compet_recup_ok"]
        config.log(compet_ok_list, 1)
        compet_not_ok_list = compets["compet_recup_not_ok"]
        config.log(compet_not_ok_list, 1)
        try:
            if any(compet_ok in config.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config.ligue_name for
                compet_not_ok in compet_not_ok_list):
                return True

            else:
                return False

        except Exception as e:
            print(e)
            return False


def getCompet():
    config.log('Recherche compet', 'info', False, 3)
    config.log_clear_line()
    url = "http://p-com.studio/api/strategy" + config.scriptType + "/get_compet.php"
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        compets = response.json()
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        config.log(f'Erreur lors de la récupération des données : {e}', 'warning', False, 3)
        return
    except json.JSONDecodeError as e:
        config.log(f'Erreur lors du parsing du JSON : {e}', 'warning', False, 3)
        return
    except Exception as e:
        config.log(f'Pas de données de compet : {e}', 'warning', False, 3)
    else:
        compet_ok_list = compets["compet_ok"]
        config.log(compet_ok_list, 0)
        compet_not_ok_list = compets["compet_not_ok"]
        config.log(compet_not_ok_list, 0)

        try:
            if any(compet_ok in config.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config.ligue_name for
                compet_not_ok in compet_not_ok_list):
                config.log(f'Ligue OK!', 'info', True, 3)
                config.log_clear_line()
                return True

            else:
                print(config.ligue_name)
                config.log(f'Ligue NOT OK!', 'warning', True, 3)
                config.log_clear_line()
                return False

        except Exception as e:
            config.log(f'Erreur get compet : {e}', 'warning', False, 3)
            return False


def SendPerte(scriptType, perte):
    url = "http://p-com.studio/api/strategy" + str(scriptType) + "/insert_perte.php?perte=" + str(perte)
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        result = response.json()
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    except Exception as e:
        print(f"Pas d'envoi de perte {e}")
    else:
        if result['status'] == "success":
            config.log(str(perte) + "> Perte insert in strategy" + str(scriptType))
            config.log_clear_line()
            config.perte -= perte
            return True
        else:
            print(result)
            return False


def SendGlobalPerte(scriptType, mise):
    url = "http://p-com.studio/api/strategy" + str(scriptType) + "/insert_global_perte.php?mise=" + str(mise)
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        result = response.json()
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    except Exception as e:
        print(f"Pas d'envoi de perte {e}")
    else:
        if result['status'] == "success":
            config.log(f"{str(mise)} insert in strategy" + str(scriptType), 'info', False, 2)
            config.log_clear_line()
            return True
        else:
            config.log(f"        {result}", 'info', False)
            config.log_clear_line()
            return False


def SendBetPlaced(scriptType, mise):
    # Construction de l'URL de l'API
    url = "http://p-com.studio/api/strategy" + str(scriptType) + "/insert_bet_placed.php"
    # URL du lien JSON de la strategy
    try:
        # Préparation des données à envoyer en POST
        data = {
            'mise': config.mise,
            'jeu': config.jeu_actuel,
            'set': config.set_actuel,
            'cote': config.cote,
            'script': config.scriptType,
            'url': config.match_Url,
            'perte': config.perte,
            'compet': config.ligue_name,
            'teams': config.teams,

        }
        # Envoi de la requête POST avec les données
        response = requests.post(url, data=data)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        result = response.json()
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    except Exception as e:
        print(f"Pas d'envoi de perte {e}")
    else:
        if result['status'] == "success":
            config.log(f"{str(mise)} insert in strategy" + str(scriptType), 'info', False, 2)
            config.log_clear_line()
            return True
        else:
            config.log(f"        {result}", 'info', False)
            config.log_clear_line()
            return False


def DispatchPerte():
    SendGlobalPerte(config.scriptType, config.perte)
    config.perte = 0


def a_DispatchPerte():
    m = 1
    n = 0.5
    if config.perte > 20:
        m = 2
        n = 1
    if config.perte > 50:
        m = 3
        n = 2
    if config.perte > 100:
        m = 5
        n = 2
    while config.perte >= n:
        SendPerte("15A", n)
        if config.perte >= m:
            SendPerte("30A", m)
        if config.perte >= m:
            SendPerte("4030", m)
        if config.perte > m:
            SendPerte("4015", m)
        if config.perte >= m:
            SendPerte("40A", n)
        SendPerte("400", n)
    if config.perte > 0:
        # SendPerte(config.scriptType,config.perte)
        SendPerte("15A", config.perte)
