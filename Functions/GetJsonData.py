import requests
import json
import config
#config.scriptType= "40A"
#config.ligue_name = "ATP"
#config.perte = 10
# Configuration du proxy
proxy = {
    "http": "http://auxobettingproxy:Scorpion971@209.200.239.22:51523",
    "https": "http://auxobettingproxy:Scorpion971@209.200.239.22:51523",
}
def getPerte():
    if getCompetRecup():
        url = "https://auxobetting.fr/"+config.scriptType+"/get_perte.php"
        try:
            # Envoyer une requête GET à l'URL
            response = requests.get(url,proxies=proxy)
            # Vérifier que la requête a réussi
            response.raise_for_status()
            print(response.json())
            # Parser le JSON depuis la réponse
            if len(response.json())>0:
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
            config.rattrape_perte = 1
            return pertes
    else:
        return
def delPerte(id):
    url = "https://auxobetting.fr/strategy"+config.scriptType+"/del_perte.php?id="+str(id)
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url,proxies=proxy)
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
    url = "https://auxobetting.fr/strategy"+config.scriptType+"/get_compet_recup.php"
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url,proxies=proxy)
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
        #config.saveLog(compet_ok_list,0)
        compet_not_ok_list = compets["compet_recup_not_ok"]
        #config.saveLog(compet_not_ok_list,0)
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
    url = "https://auxobetting.fr/strategy"+config.scriptType+"/get_compet.php"
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url,proxies=proxy)
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
        print(f"Pas de suppression de perte {e}")
    else:
        compet_ok_list = compets["compet_ok"]
        #config.saveLog(compet_ok_list,0)
        compet_not_ok_list = compets["compet_not_ok"]
        #config.saveLog(compet_not_ok_list,0)

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
def SendPerte(scriptType,perte):
    url = "https://auxobetting.fr/strategy"+str(scriptType)+"/insert_perte.php?perte="+str(perte)
    # URL du lien JSON de la strategy
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url,proxies=proxy)
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
            print(str(perte)+ "> Perte insert in strategy"+str(scriptType))
            config.perte -=perte
            return True
        else:
            print(result)
            return False
def DispatchPerte():
    print("perte befor dispatch",config.perte)
    while config.perte >200:
        if SendPerte("4030",1):
            print('pertte ajouté')
        else:
            print('non ajoute', SendPerte)
        """if config.perte>1:
            if SendPerte("40A",1):
                config.perte -= 1
        if config.perte>1:
            if SendPerte("30A",1):
                config.perte -= 1
        if config.perte>1:
            if SendPerte("15A",1):
                config.perte -= 1"""
    if config.perte >0.2:
        SendPerte(config.scriptType,config.perte)
    print('perte after dispatch',config.perte)

