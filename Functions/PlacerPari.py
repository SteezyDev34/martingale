# -*- coding: utf-8 -*-
import json
import os
import sys
import time

# Ajouter le chemin du projet au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

import Functions.Functions_telegram
import config
from Functions.Functions_telegram import send_telegram
from Functions.OneXBetBridge import find_and_prepare_bet


def log_message(message, level="INFO", flush_output=True):
    """
    Fonction utilitaire pour l'affichage des messages avec flush automatique
    pour éviter les freezes du terminal
    """
    timestamp = time.strftime("%H:%M:%S")
    formatted_message = f"[{timestamp}] {level}: {message}"
    print(formatted_message, flush=flush_output)
    return formatted_message


def placer_pari(codeList):
    """
    Fonction pour placer un pari sur 1xBet via l'extension Chrome (bridge WebSocket)

    :param codeList: Données du pari au format {'matches': [...], 'tipster': '...'}
    :return: Dictionnaire avec le résultat de l'opération
    """
    config.site_type = 'mobile_site'
    tentative = 0
    
    # Nouveau format : {'matches': [...], 'tipster': '...'}
    matches_list = codeList['matches']
    global_tipster = codeList.get('tipster', '')
    
    while tentative < 3:
        log_message('Début de tentative de placement de pari')
        success = True
        # Traiter chaque match de la liste
        for match in matches_list:
            log_message("=== DONNÉES ===")
            log_message(f"Match: {match['equipe_1']} vs {match['equipe_2']}")
            log_message(f"Date: {match['date']}")
            log_message(f"Catégorie de pari: {match['categorie']}")
            log_message(f"Type de pari: {match['type_de_pari']}")
            log_message(f"Sélection: {match['selection']}")
            log_message(f"Sport: {match.get('sport', None)}")
            log_message(f"Tipster: {global_tipster or match.get('tipster', '')}")
            log_message("=" * 50)
            log_message('Traitement du match en cours...')

            equipe1 = match['equipe_1']
            equipe2 = match['equipe_2']
            categorie = match['categorie']
            type_de_pari = match['type_de_pari']
            selection = match['selection']  # "Plus De 20.5"
            sport_id = match.get('sport', None)  # Valeur par défaut si 'sport' n'est pas présent
            # Normaliser et gérer différents formats de `selection`:
            # - Si c'est une chaîne JSON sérialisée représentant une liste -> convertir en tableau de paris
            # - Si c'est déjà une liste Python -> l'utiliser comme tableau
            # - Sinon -> retourner un tableau contenant l'élément d'origine (marqué comme 'Combiné')
            
            if equipe1 is None or equipe2 is None:
                log_message("❌ Données d'équipe manquantes, impossible de traiter ce match", "ERROR")
                return False
            combined_paris = None
            try:
                if isinstance(selection, str):
                    s = selection.strip()
                    combined_paris = []
                    if s.startswith('[') and s.endswith(']'):
                        parsed = json.loads(selection)
                        if isinstance(parsed, list) and len(parsed) > 0:
                            for item in parsed:
                                new_pari = match.copy()
                                if isinstance(item, dict):
                                    new_pari['categorie'] = item.get('categorie', new_pari.get('categorie'))
                                    new_pari['type_de_pari'] = item.get('type_de_pari', new_pari.get('type_de_pari'))
                                    new_pari['selection'] = item.get('selection', new_pari.get('selection'))
                                    new_pari['odds'] = item.get('odds', new_pari.get('odds'))
                                combined_paris.append(new_pari)
                    else:
                        new_pari = match.copy()
                        new_pari['categorie'] = match.get('categorie', new_pari.get('categorie'))
                        new_pari['type_de_pari'] = match.get('type_de_pari', new_pari.get('type_de_pari'))
                        new_pari['selection'] = match.get('selection', new_pari.get('selection'))
                        new_pari['odds'] = match.get('odds', new_pari.get('odds'))
                        combined_paris.append(new_pari)
            except Exception as e:
                print(f"Erreur lors du parsing/normalisation de 'selection': {e}", flush=True)
            else:
                # Construction de la liste des sélections
                selections_list = "\n".join([f"  - {pari['selection']}" for pari in combined_paris])
                
                formatted_telegram_msg = f"📊 Nouveau pari à placer:\n" \
                                    f"Match: {equipe1} vs {equipe2}\n" \
                                    f"Date: {match['date']}\n" \
                                    f"Catégorie de pari: {categorie}\n" \
                                    f"Type de pari: {type_de_pari}\n" \
                                    f"Sélection:\n{selections_list}\n" \
                                    f"Sport: {sport_id}\n" \
                                    f"Tipster: {global_tipster}"
                
            config.tipster = global_tipster
            config.match_name = equipe1 + ' - ' + equipe2
            log_message(f"🌐 Recherche du match {equipe1} vs {equipe2} sur 1xBet (extension)...")

            prepared = find_and_prepare_bet(combined_paris)
            if not prepared.get('success'):
                log_message(f"❌ Erreur lors de la préparation du pari: {prepared.get('error')}", "ERROR")
                if prepared.get('error') == 'match_not_found':
                    send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la recherche du match : {formatted_telegram_msg}")
                    success = False
                    break
                tentative = tentative + 1
                continue

            # Cote globale : celle lue en direct pour un pari simple, sinon le produit
            # des cotes fournies par le tipster pour chaque leg d'un combiné
            if len(combined_paris) > 1:
                global_odds = 1.0
                for pari in combined_paris:
                    try:
                        global_odds *= float(pari.get('odds') or 1)
                    except Exception:
                        pass
            else:
                global_odds = prepared.get('cote') or float(combined_paris[0].get('odds') or 0)
            config.cote = global_odds

        from Functions.GetMise import get_recommended_stake
        try:
            stake_data = get_recommended_stake(cote=config.cote, tipster=global_tipster)
            config.mise = round(float(stake_data.get('recommended_stake') or 0), 2) or 0.2
        except Exception as e:
            log_message(f"⚠️ Mise recommandée indisponible ({e}), fallback 0.2€", "WARNING")
            config.mise = 0.2

        from websocket_server import bridge
        stake_result = bridge.set_stake(config.mise)
        if not stake_result.get('success'):
            send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la mise du pari : {formatted_telegram_msg}")
            tentative += 1
            continue

        validation = bridge.validate_bet(confirm=True)
        if not validation.get('validated'):
            send_telegram(Functions.Functions_telegram.alertGroup, f"Erreur lors de la validation du pari : {formatted_telegram_msg}")
            tentative += 1
            continue
        try:
            # Formatage des événements selon le nouveau format API
            formatted_events = []
            for pari in combined_paris:
                event_data = {
                    "team1": equipe1,
                    "team2": equipe2,
                    "league": pari.get('league', 'Ligue Inconnue'),  # À ajuster selon vos données
                    "description": pari['intitule'],
                    "odds": float(pari.get('odds', config.cote)),
                    "sport_id": sport_id or 1  # Valeur par défaut si sport_id est None
                }
                formatted_events.append(event_data)
            
            # Structure des données selon le nouveau format API
            bet_data = {
                "bet_date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "global_odds": float(config.cote),
                "bet_code": f"auxobot-{config.tipster.lower()}" if config.tipster else "auxobot-multi",
                "stake": float(config.mise),
                "stake_type": "currency",
                "events": formatted_events
            }

            # Configuration de la nouvelle API
            api_url = getattr(config, 'AUXOTRACK_API_URL', "https://api.auxotracker.lan/api/auxobot/bets")
            
            # Récupération du token depuis les variables d'environnement
            auxobot_token = getattr(config, 'AUXOBOT_TOKEN')
            
            if not auxobot_token:
                raise Exception("AUXOBOT_TOKEN non configuré dans le fichier .env")
            
            headers = {
                'Authorization': f'Bearer {auxobot_token}',
                'Content-Type': 'application/json'
            }

            print(f"Envoi des données à l'API: {api_url}")
            print(f"Données envoyées: {json.dumps(bet_data, indent=2, ensure_ascii=False)}")

            response = requests.post(
                api_url,
                headers=headers,
                json=bet_data,
                timeout=30,
                verify=False  # Pour éviter les erreurs SSL avec -k comme dans curl
            )

            print(f"Code de statut de la réponse: {response.status_code}")
            print(f"En-têtes de la réponse: {dict(response.headers)}")
            print(f"Contenu brut de la réponse: '{response.text}'")

            # Vérification de la réponse
            if not response.ok:
                raise Exception(f"Erreur HTTP: {response.status_code} - {response.text}")

            # Traitement de la réponse - gestion des réponses vides
            response_data = {}
            if response.content and response.content.strip():
                try:
                    response_data = response.json()
                except json.JSONDecodeError as json_error:
                    print(f"Erreur de décodage JSON: {json_error}")
                    print(f"Contenu de la réponse: {response.text}")
                    response_data = {'raw_response': response.text}
            else:
                print("Réponse vide de l'API - considérée comme succès")

            return {
                'success': True,
                'message': 'Pari ajouté avec succès à l\'API',
                'details': {
                    'equipes': f"{equipe1} vs {equipe2}",
                    'type_de_pari': type_de_pari,
                    'mise': config.mise,
                    'cote': config.cote,
                    'api_response': response_data
                }
            }

        except requests.exceptions.RequestException as e:
            print(f'Erreur lors de l\'appel à l\'API: {str(e)}')
            return {
                'success': False,
                'message': f'Erreur lors de l\'appel à l\'API: {str(e)}',
                'error': str(e)
            }
        except Exception as e:
            print(f'Erreur lors de l\'ajout du pari: {str(e)}')
            return {
                'success': False,
                'message': f'Impossible d\'ajouter le pari. Veuillez réessayer plus tard.',
                'error': str(e)
            }
        finally:
            # Pari traité avec le nouveau format
            print(f"Pari traité avec succès")

        # Si on arrive ici sans exception, le traitement a réussi pour ce match
        
        # Fin de la boucle for (tous les matches traités)
        # Si tous les matches ont été traités avec succès
        if success:
            return {
                'success': True,
                'message': 'Tous les paris ont été traités',
                'processed_count': len(matches_list)
            }
        
        # Si il y a eu un échec, incrémenter tentative et recommencer
        tentative += 1
        print(f"Tentative {tentative} échouée, nouvelle tentative...")

    # Si on sort de la boucle while, toutes les tentatives ont échoué
    return {
        'success': False,
        'message': 'Échec après 3 tentatives',
        'processed_count': 0
    }


def avec_donnees_exemple():
    """
    Fonction de test utilisant les données d'exemple fournies (nécessite le bridge
    WebSocket démarré et l'extension Chrome connectée sur une page 1xBet).
    """
    from websocket_server import start_bridge

    donnees_test = {
        "date": "05/09/2025",
        "equipe_1": "Earthquakes",
        "equipe_2": "Austin",
        "categorie": "Temps réglementaire",
        "type_de_pari": "Handicap",
        "selection": "Handicap 1 (-1)",
        "odds": "1.1",
        "tipster": 'TEST'
    }

    start_bridge(wait_timeout=30)
    resultat = placer_pari({'matches': [donnees_test], 'tipster': 'TEST'})

    print("RÉSULTAT DU TEST:")
    print(json.dumps(resultat, indent=2, ensure_ascii=False))

    return resultat


if __name__ == "__main__":
    config.site_type = 'new_site'
    # Test avec les données d'exemple
    print("Lancement du test avec les données d'exemple...")
    config.scriptType = 'LIVE'
    avec_donnees_exemple()
