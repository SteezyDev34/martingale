import requests
import json
import config
config.scriptType= "40A"
config.ligue_name = "ATP"
#config.perte = 10
def getPerte():
    if getCompetRecup():
        url = "https://auxobetting.fr/strategy"+config.scriptType+"/get_perte.php"
        try:
            # Envoyer une requête GET à l'URL
            response = requests.get(url)
            # Vérifier que la requête a réussi
            response.raise_for_status()
            # Parser le JSON depuis la réponse
            pertes = response.json()[0]
            # Afficher les données pour vérification
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la récupération des données : {e}")
            return
        except json.JSONDecodeError as e:
            print(f"Erreur lors du parsing du JSON : {e}")
            return
        else:
            return pertes
    else:
        return
def delPerte(id):
    url = "https://auxobetting.fr/strategy40A/del_perte.php?id="+str(id)
    try:
        # Envoyer une requête GET à l'URL
        response = requests.get(url)
        # Vérifier que la requête a réussi
        response.raise_for_status()
        # Parser le JSON depuis la réponse
        result = response.json()[0]
        # Afficher les données pour vérification
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des données : {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Erreur lors du parsing du JSON : {e}")
        return
    else:
        print(result)
        return True

def getCompetRecup():
    url = "https://auxobetting.fr/strategy"+config.scriptType+"/get_compet_recup.php"
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
    else:
        compet_ok_list = compets["compet_recup_ok"]
        print(compet_ok_list)
        compet_not_ok_list = compets["compet_recup_not_ok"]
        print(compet_not_ok_list)
        try:
            if any(compet_ok in config.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config.ligue_name for
                compet_not_ok in compet_not_ok_list):
                print("COMPET RECUP OK")
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
    else:
        compet_ok_list = compets["compet_ok"]
        print(compet_ok_list)
        compet_not_ok_list = compets["compet_not_ok"]
        print(compet_not_ok_list)
        try:
            if any(compet_ok in config.ligue_name for compet_ok in
                   compet_ok_list) and not any(
                compet_not_ok in config.ligue_name for
                compet_not_ok in compet_not_ok_list):
                print("COMPET RECUP OK")
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
    else:
        if result['status'] == "success":
            print(str(perte)+ "> Perte insert in strategy"+str(scriptType))
            return True
        else:
            print(result)
            return False
def DispatchPerte():
    while config.perte >1:
        if SendPerte("4030",2):
            config.perte -= 1
        if config.perte>1:
            if SendPerte("40A",1):
                config.perte -= 1
        if config.perte>1:
            if SendPerte("30A",1):
                config.perte -= 1
        if config.perte>1:
            if SendPerte("15A",1):
                config.perte -= 1
    if config.perte >0.2:
        SendPerte("4030",config.perte)

getCompet()