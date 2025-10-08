#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module de base pour les stratégies de martingale
"""

import sys
import os
import time
import json
import requests
from abc import ABC, abstractmethod
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from typing import Dict, Any, Optional
from Functions.GetScoreActuel import GetScoreActuel
from Functions.GetSetActuel import GetSetActuel
from Functions.GetIfMatchPage import GetIfMatchPage
from Functions.GetScoreActuel import record_scores as record_scores_global
from Functions.ModalHandler import ModalHandler

# Ajouter le répertoire racine au path pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class ScriptConfig:
    """
    Classe pour gérer la configuration spécifique à chaque type de script de martingale
    """
    _instances = {}  # Dictionnaire pour stocker les instances par type de script

    def __init__(self, script_type, api_url="http://auxobetbot.sc2vagr6376.universe.wf"):
        """
        Initialise la configuration pour un type de script donné
        
        Args:
            script_type (str): Type de script (ex: '40A', '300', '15A', etc.)
            api_url (str): URL de l'API pour récupérer la configuration
        """
        self.script_type = script_type
        self.api_url = api_url
        # Récupérer l'instance existante si elle existe, sinon en créer une nouvelle
        if script_type in ScriptConfig._instances:
            self.variables = ScriptConfig._instances[script_type].variables
        else:
            self.variables = self._init_variables()
            ScriptConfig._instances[script_type] = self

    def _init_variables(self):
        """
        Initialise les variables de configuration depuis l'API
        
        Returns:
            dict: Dictionnaire des variables de configuration
        """
        url = f"{self.api_url}/strategy{self.script_type}/"
        strategy = self._get_json_data(url)
        print(f'Initialisation de la configuration pour le script {self.script_type}')
        
        # Configuration par défaut selon le type de script
        default_configs = {}
        config = default_configs.get(self.script_type, {})
        
        if strategy:
            for key, strat in strategy.items():
                config[key] = strat
            config['error'] = False
            config['validated_bet'] = {}
            config['print_running_text'] = False
            config['print_match_live_text'] = False
            config['win_type'] = ''
            config['netprofit'] = 0
            config['gain'] = 0
            config['looking_game'] = False
            config['placed_game'] = False
            config['saved_score'] = False
            config['rattrape_perte'] = False
            config['result'] = False

        return config

    def _get_json_data(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Récupère et parse les données JSON depuis une URL
        
        Args:
            url (str): L'URL à partir de laquelle récupérer les données JSON
            
        Returns:
            dict: Un dictionnaire contenant les données JSON ou None en cas d'erreur
        """
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    return data[0]
                return None
            except requests.exceptions.RequestException as e:
                print(f"Tentative {attempt + 1}/{max_attempts} - Erreur lors de la récupération des données : {e}")
            except json.JSONDecodeError as e:
                print(f"Tentative {attempt + 1}/{max_attempts} - Erreur lors du parsing du JSON : {e}")

            # Attendre un peu plus longtemps entre chaque tentative
            if attempt < max_attempts - 1:
                time.sleep(1 * (attempt + 1))

        return None

    def get(self, var_name):
        """
        Récupère une variable par son nom
        
        Args:
            var_name (str): Nom de la variable
            
        Returns:
            any: Valeur de la variable ou None si elle n'existe pas
        """
        return self.variables.get(var_name)

    def set(self, var_name, value):
        """
        Définit une variable
        
        Args:
            var_name (str): Nom de la variable
            value (any): Valeur à assigner
        """
        self.variables[var_name] = value

    def reset(self):
        """
        Force la réinitialisation de la configuration
        
        Returns:
            ScriptConfig: Instance réinitialisée
        """
        self.variables = self._init_variables()
        ScriptConfig._instances[self.script_type] = self
        return self

class Martingale(ABC):
    """
    Classe abstraite de base pour toutes les stratégies de martingale
    """
    
    def __init__(self, config_manager=None, script_type=None):
        """
        Initialisation de la classe de base Martingale
        
        Args:
            config_manager: Instance du gestionnaire de configuration
            script_type (str): Type de script pour cette instance de martingale
        """
        self.config_manager = config_manager
        self.script_type = script_type or self.get_script_type()
        self.script_config = ScriptConfig(self.script_type) if self.script_type else None
        self.nom_strategie = "base"  # À surcharger dans les classes dérivées
        self.priorite = 0  # Plus le nombre est élevé, plus la priorité est haute
        self.en_cours = False
        self.match_actuel = None
        self.etat_jeu = {
            "gain": 0,
            "perte": 0,
            "mise": 0,
            "mise_base": 0,
            "cote_base": 0,
            "nb_tour": 0,
            "tour_actuel": 0,
            "proba_mini": 0,
            "increment": 0,
            "netprofit": 0,
            "cote": 0,
            "wantwin": 0,
            "misemax": 0,
            "rattrape_perte": 0,
            "script_type": "",
            "tipster": "",
            "site_type": "",
            "classes": {}
        }
        
        # Initialiser les variables depuis la configuration du script
        self.init_variables()
        
        # Les variables globales partagées (classes, site_type, set_actuel, saved_score, all_scores)
        # restent accessibles via le module config et ne sont plus initialisées localement ici.

    @abstractmethod
    def get_script_type(self) -> str:
        """
        Retourne le type de script pour cette stratégie
        À implémenter dans les classes dérivées
        
        Returns:
            str: Type de script (ex: '40A', '300', '15A', etc.)
        """
        pass

    def init_variables(self):
        """
        Initialise les variables globales depuis les données de stratégie
        """
        if not self.script_config:
            return
            
        config_global = self.script_config

        # Initialiser les variables depuis la configuration
        error = config_global.get("error")
        validated_bet = config_global.get("validated_bet")

        # Game settings
        val = config_global.get("cote_base")
        if val is not None:
            self.etat_jeu["cote_base"] = float(val)
            
        val = config_global.get("mise")
        if val is not None:
            self.etat_jeu["mise"] = float(val)
            self.etat_jeu["mise_base"] = float(val)

        val = config_global.get("nb_tour")
        if val is not None:
            self.etat_jeu["nb_tour"] = int(val)

        val = config_global.get("proba_mini")
        if val is not None:
            self.etat_jeu["proba_mini"] = float(val)

        # Game state
        val = config_global.get("gain")
        if val is not None:
            self.etat_jeu["gain"] = float(val)

        val = config_global.get("increment")
        if val is not None:
            self.etat_jeu["increment"] = float(val)

        val = config_global.get("netprofit")
        if val is not None:
            self.etat_jeu["netprofit"] = float(val)

        val = config_global.get("perte")
        if val is not None:
            self.etat_jeu["perte"] = float(val)

        val = config_global.get("rattrape_perte")
        if val is not None:
            self.etat_jeu["rattrape_perte"] = int(val)

        val = config_global.get("wantwin")
        if val is not None:
            self.etat_jeu["wantwin"] = float(val)

        # Autres variables
        self.etat_jeu["script_type"] = self.script_type
        
        # Synchronisation avec le module config global si nécessaire
        self._sync_with_global_config()

    def save_variables(self):
        """
        Sauvegarde l'état actuel des variables dans la configuration
        """
        if not self.script_config:
            return
            
        config_global = self.script_config

        # Sauvegarder les paramètres de jeu
        config_global.set("cote_base", self.etat_jeu["cote_base"])
        config_global.set("mise", self.etat_jeu["mise"])
        config_global.set("nb_tour", self.etat_jeu["nb_tour"])
        config_global.set("proba_mini", self.etat_jeu["proba_mini"])

        # Sauvegarder l'état du jeu
        config_global.set("gain", self.etat_jeu["gain"])
        config_global.set("increment", self.etat_jeu["increment"])
        config_global.set("netprofit", self.etat_jeu["netprofit"])
        config_global.set("perte", self.etat_jeu["perte"])
        config_global.set("rattrape_perte", self.etat_jeu["rattrape_perte"])
        config_global.set("wantwin", self.etat_jeu["wantwin"])

        # Synchronisation avec le module config global si nécessaire
        self._sync_to_global_config()

    def switch_script(self, new_script_type):
        """
        Change le type de script et recharge la configuration
        
        Args:
            new_script_type (str): Nouveau type de script
        """
        # Sauvegarder l'état actuel
        self.save_variables()
        
        # Changer le type de script
        self.script_type = new_script_type
        self.script_config = ScriptConfig(new_script_type)
        
        # Recharger les variables
        self.init_variables()

    def _sync_with_global_config(self):
        """
        Synchronise avec le module config global pour la compatibilité
        """
        try:
            import config as global_config
            self.etat_jeu["cote"] = getattr(global_config, 'cote', self.etat_jeu["cote_base"])
            self.etat_jeu["tipster"] = getattr(global_config, 'tipster', '1xbet')
            self.etat_jeu["site_type"] = getattr(global_config, 'site_type', 'new_site')
        except ImportError:
            # Le module config global n'est pas disponible
            pass

    def _sync_to_global_config(self):
        """
        Synchronise vers le module config global pour la compatibilité
        """
        try:
            import config as global_config
            global_config.mise = self.etat_jeu["mise"]
            global_config.perte = self.etat_jeu["perte"]
            global_config.wantwin = self.etat_jeu["wantwin"]
            global_config.gain = self.etat_jeu["gain"]
            global_config.netprofit = self.etat_jeu["netprofit"]
            global_config.rattrape_perte = self.etat_jeu["rattrape_perte"]
            global_config.cote = self.etat_jeu["cote"]
            global_config.scriptType = self.script_type
        except ImportError:
            # Le module config global n'est pas disponible
            pass
    
    def charger_configuration(self):
        """
        Charge la configuration spécifique à la stratégie
        """
        if self.config_manager:
            config = self.config_manager.get_strategy_config(self.nom_strategie)
            if config:
                self.etat_jeu["mise_base"] = config.get("mise", 1)
                self.etat_jeu["mise"] = self.etat_jeu["mise_base"]
                self.etat_jeu["cote_base"] = config.get("cote_base", 1.5)
                self.etat_jeu["nb_tour"] = config.get("nb_tour", 3)
                self.etat_jeu["proba_mini"] = config.get("proba_mini", 60)
                self.etat_jeu["increment"] = config.get("increment", 0)
                
        # Initialisation des attributs pour get_mise depuis le module config global
        try:
            import config as global_config
            self.etat_jeu["cote"] = getattr(global_config, 'cote', self.etat_jeu["cote_base"])
            self.etat_jeu["wantwin"] = getattr(global_config, 'wantwin', 0)
            self.etat_jeu["perte"] = getattr(global_config, 'perte', 0)
            self.etat_jeu["rattrape_perte"] = getattr(global_config, 'rattrape_perte', 0)
            self.etat_jeu["script_type"] = getattr(global_config, 'scriptType', '')
            self.etat_jeu["tipster"] = getattr(global_config, 'tipster', '')
            self.etat_jeu["site_type"] = getattr(global_config, 'site_type', '')
            self.etat_jeu["classes"] = getattr(global_config, 'classes', {})
        except ImportError:
            pass
    
    def reinitialiser_etat(self):
        """
        Réinitialise l'état du jeu pour une nouvelle série
        """
        self.etat_jeu["tour_actuel"] = 0
        self.etat_jeu["mise"] = self.etat_jeu["mise_base"]
        self.en_cours = False
        self.match_actuel = None
    
    def enregistrer_resultat(self, gagne, montant=None):
        """
        Enregistre le résultat d'un pari
        
        Args:
            gagne: Booléen indiquant si le pari est gagné
            montant: Montant gagné ou perdu (optionnel)
        """
        if gagne:
            gain = montant if montant else self.etat_jeu["mise"] * self.etat_jeu["cote_base"] - self.etat_jeu["mise"]
            self.etat_jeu["gain"] += gain
            self.etat_jeu["netprofit"] += gain
            self.reinitialiser_etat()
        else:
            perte = montant if montant else self.etat_jeu["mise"]
            self.etat_jeu["perte"] += perte
            self.etat_jeu["netprofit"] -= perte
            self.etat_jeu["tour_actuel"] += 1
            
            # Si on a atteint le nombre maximum de tours, on réinitialise
            if self.etat_jeu["tour_actuel"] >= self.etat_jeu["nb_tour"]:
                self.reinitialiser_etat()
            else:
                # Sinon on augmente la mise selon la stratégie
                self.calculer_prochaine_mise()
    
    def calculer_prochaine_mise(self):
        """
        Calcule la prochaine mise selon la stratégie.
        Comportement par défaut: retourne la mise actuelle stockée dans l'état du jeu.
        Les classes dérivées peuvent surcharger pour appliquer une logique personnalisée.
        
        Returns:
            float: Montant de la prochaine mise
        """
        return self.etat_jeu.get("mise", 0)
    
    def get_mise(self, driver, log_callback=None):
        """
        Calcule la mise selon la stratégie de martingale.
        Cette méthode encapsule la logique de calcul de mise en utilisant
        les attributs de la classe au lieu des variables globales.
        
        Args:
            driver: Instance du driver Selenium pour interagir avec le site
            log_callback: Fonction de callback pour les logs (optionnel)
            
        Returns:
            bool: True si la mise a été calculée avec succès
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        # Gestion de la cote selon le rattrapage de perte
        if self.etat_jeu["rattrape_perte"] == 3:
            log('Bonne proba, cote : 3', 'info')
            self.etat_jeu["cote"] = self.etat_jeu["cote_base"]
        else:
            log("Rattrapage, récupération de la cote", 'info')
            try:
                # Récupération de la cote depuis le site
                if self.etat_jeu["classes"] and self.etat_jeu["site_type"]:
                    cote_elements = driver.find_elements(
                        By.CLASS_NAME,
                        self.etat_jeu["classes"].get('coef_value', {}).get(self.etat_jeu["site_type"], '')
                    )
                    if cote_elements:
                        self.etat_jeu["cote"] = cote_elements[0].text
                    else:
                        raise Exception("Élément cote non trouvé")
                else:
                    raise Exception("Configuration des classes manquante")
            except Exception:
                log('Erreur récupération cote : utilisation cote de base', 'warning')
                self.etat_jeu["cote"] = self.etat_jeu["cote_base"]
            else:
                log(f'Cote récupérée : {self.etat_jeu["cote"]}', 'info')
                # Validation de la cote
                if (self.etat_jeu["cote"] == '' or 
                    str(self.etat_jeu["cote"]) in ['0', '1'] or 
                    self.etat_jeu["cote"] == 0):
                    self.etat_jeu["cote"] = self.etat_jeu["cote_base"]
        
        # Calcul de la mise selon le type de script
        if self.etat_jeu["script_type"] == 'LIVE':
            # Calcul via API pour les scripts LIVE
            try:
                api_url = (f'https://bettracker.sc2vagr6376.universe.wf/backend/api.php'
                          f'?action=recommended_stake&tipster={self.etat_jeu["tipster"]}'
                          f'&odds={self.etat_jeu["cote"]}&target_percentage=1&recover_losses=1')
                req = requests.get(api_url, verify=False)
                self.etat_jeu["mise"] = round(float(req.json()['recommended_stake']), 2)
                return True
            except Exception:
                log('Erreur API, calcul manuel de la mise', 'warning')
        
        # Calcul manuel de la mise
        try:
            cote_float = float(self.etat_jeu["cote"])
            if cote_float <= 1:
                log('Cote invalide, utilisation cote de base', 'warning')
                cote_float = float(self.etat_jeu["cote_base"])
            
            self.etat_jeu["mise"] = (float(self.etat_jeu["wantwin"]) + float(self.etat_jeu["perte"])) / (cote_float - 1)
        except (ValueError, ZeroDivisionError):
            log('Erreur calcul mise, utilisation mise de base', 'error')
            self.etat_jeu["mise"] = self.etat_jeu["mise_base"]
        
        # Arrondi et validation de la mise minimale
        self.etat_jeu["mise"] = round(self.etat_jeu["mise"], 2)
        if self.etat_jeu["mise"] < 0.2:
            self.etat_jeu["mise"] = 0.2
        
        log(f"Cote : {self.etat_jeu['cote']} | Perte : {self.etat_jeu['perte']} | "
            f"Gain souhaité : {self.etat_jeu['wantwin']} | Mise : {self.etat_jeu['mise']}", 'info')
        
        # Récupération de la mise maximale (optionnel)
        self._get_mise_max(driver, log)
        
        return True
    
    def _get_mise_max(self, driver, log_callback=None):
        """
        Méthode privée pour récupérer la mise maximale depuis le site
        
        Args:
            driver: Instance du driver Selenium
            log_callback: Fonction de callback pour les logs
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        getmisemax = False
        tentative = 0
        
        while not getmisemax and tentative < 5:
            try:
                btn_extra = driver.find_elements(By.CLASS_NAME, 'cpn-extra__btn')[0]
                btn_extra.click()
                
                # Attente de l'activation du dropdown
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'cpn-dropdown--is-active'))
                )
                
                # Navigation dans le dropdown
                dropdown = driver.find_elements(By.CLASS_NAME, 'cpn-dropdown--is-active')[0]
                content = dropdown.find_elements(By.CLASS_NAME, 'cpn-dropdown__content')[0]
                item = content.find_elements(By.CLASS_NAME, 'cpn-extra-settings__item')[0]
                btn_text = item.find_elements(By.CLASS_NAME, 'cpn-extra-settings__btn')[0].text
                
                # Extraction de la mise maximale
                self.etat_jeu["misemax"] = float(btn_text.split(' EUR')[0].replace(' ', ''))
                getmisemax = True
                
            except Exception:
                tentative += 1
                if tentative >= 5:
                    log('Impossible de récupérer la mise maximale', 'warning')
                    self.etat_jeu["misemax"] = 0
                    getmisemax = True
    
    def verifier_conditions_match(self, match_data):
        """
        Vérifie si un match correspond aux critères de la stratégie.
        Comportement par défaut: retourne True (aucun filtre).
        Les classes dérivées peuvent surcharger pour appliquer des critères spécifiques.
        
        Args:
            match_data: Données du match à vérifier
            
        Returns:
            bool: True si le match correspond aux critères, False sinon
        """
        return True
    
    def placer_pari(self, match_data, stake):
        """
        Place un pari sur un match selon la stratégie.
        Comportement par défaut: ne place pas de pari et retourne False.
        Les classes dérivées doivent surcharger pour implémenter le placement réel.
        
        Args:
            match_data: Données du match sur lequel parier
            stake: Montant de la mise
            
        Returns:
            bool: True si le pari a été placé avec succès, False sinon
        """
        return False
    
    def sauvegarder_etat(self):
        """
        Sauvegarde l'état actuel de la martingale
        
        Returns:
            dict: État actuel de la martingale
        """
        return {
            "nom_strategie": self.nom_strategie,
            "en_cours": self.en_cours,
            "match_actuel": self.match_actuel,
            "etat_jeu": self.etat_jeu.copy()
        }
    
    def charger_etat(self, etat):
        """
        Charge un état sauvegardé
        
        Args:
            etat: État à charger
        """
        if etat["nom_strategie"] == self.nom_strategie:
            self.en_cours = etat["en_cours"]
            self.match_actuel = etat["match_actuel"]
            self.etat_jeu = etat["etat_jeu"].copy()
    
    def placer_mise(self, driver, log_callback=None):
        """
        Place la mise calculée sur le site de paris.
        Cette méthode encapsule la logique de placement de mise en utilisant
        les attributs de la classe au lieu des variables globales.
        
        Args:
            driver: Instance du driver Selenium pour interagir avec le site
            log_callback: Fonction de callback pour les logs (optionnel)
            
        Returns:
            bool: True si la mise a été placée avec succès
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        sending_mise = False
        
        try:
            # Attendre que le champ de mise soit présent
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.CLASS_NAME, 
                    self.etat_jeu["classes"].get('cpn_amount', {}).get(self.etat_jeu["site_type"], '')
                ))
            )
        except Exception:
            log("CHAMP DE MISE NON TROUVÉ", 'error')
            return False
        
        try:
            # Localiser le champ de saisie de la mise
            cpn_setting = driver.find_element(
                By.CLASS_NAME, 
                self.etat_jeu["classes"].get('cpn_amount', {}).get(self.etat_jeu["site_type"], '')
            )
            cpn_setting = cpn_setting.find_element(
                By.CLASS_NAME, 
                self.etat_jeu["classes"].get('cpn_amount_input', {}).get(self.etat_jeu["site_type"], '')
            )
            
            tentative = 0
            while not sending_mise and tentative < 10:
                # Recalculer la mise si nécessaire
                self.get_mise(driver, log_callback)
                
                # Effacer et saisir la nouvelle mise
                cpn_setting.clear()
                cpn_setting.send_keys(str(self.etat_jeu["mise"]))
                
                # Vérifier que la mise a été correctement saisie
                valeur_saisie = cpn_setting.get_attribute("value")
                log(f"Mise insérée : {valeur_saisie}", 'info')
                
                if str(valeur_saisie) == str(self.etat_jeu["mise"]):
                    sending_mise = True
                else:
                    tentative += 1
                    log('Mauvaise mise insérée!', 'warning')
                    time.sleep(1)
                    
        except Exception as e:
            log(f"Erreur lors du placement de la mise : {e}", 'error')
            return False
        
        return sending_mise

    def get_bet(self, driver, next_bet=False, selection='', log_callback=None):
        """
        Recherche et sélectionne un pari selon le type de script.
        Cette méthode encapsule la logique de recherche de paris en utilisant
        les attributs de la classe au lieu des variables globales.
        
        Args:
            driver: Instance du driver Selenium pour interagir avec le site
            next_bet: Indique s'il faut chercher le prochain pari
            selection: Sélection spécifique pour le pari
            log_callback: Fonction de callback pour les logs (optionnel)
            
        Returns:
            bool: True si un pari a été trouvé et sélectionné
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        # Redirection vers l'ancienne version du site si nécessaire
        if self.etat_jeu["site_type"] == 'old_site':
            return self._get_bet_old(driver, next_bet, selection, log_callback)
        else:
            return self._get_bet_new(driver, next_bet, selection, log_callback)
    
    def _get_bet_new(self, driver, next_bet=False, selection='', log_callback=None):
        """
        Implémentation pour le nouveau site.
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        log(f"RECHERCHE DES PARIS {self.etat_jeu['script_type']}....", 'info')
        
        # Configuration des types de paris selon le script
        if self.etat_jeu["script_type"] == "40A":
            s_type = ": 40-40"
            self.etat_jeu["win_type"] = '40:40'
        elif self.etat_jeu["script_type"] == "30A":
            s_type = " 30-30"
            self.etat_jeu["win_type"] = '30:30'
        elif self.etat_jeu["script_type"] == "15A":
            s_type = " 15-15"
            self.etat_jeu["win_type"] = '15:15'
        elif self.etat_jeu["script_type"] == "1SET":
            s_type = self.etat_jeu["win_type"]
        else:
            s_type = ""
        
        try:
            # Localiser le conteneur des paris
            canvas = WebDriverWait(driver, 1).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'market-grid-canvas__container'))
            )
        except:
            log('Erreur récupération market-grid-canvas__container', 'error')
            return False
        
        # Cette méthode nécessiterait une implémentation complète
        # Pour l'instant, on retourne False en attendant l'implémentation complète
        log("Méthode get_bet en cours d'implémentation", 'warning')
        return False
    
    def _get_bet_old(self, driver, next_bet=False, selection='', log_callback=None):
        """
        Implémentation pour l'ancien site.
        """
        # Placeholder pour l'ancienne version
        return False

    def validation_du_paris(self, driver, next_bet=False, log_callback=None):
        """
        Valide le pari placé sur le site.
        Cette méthode encapsule la logique de validation de paris en utilisant
        les attributs de la classe au lieu des variables globales.
        
        Args:
            driver: Instance du driver Selenium pour interagir avec le site
            next_bet: Indique s'il s'agit du prochain pari
            log_callback: Fonction de callback pour les logs (optionnel)
            
        Returns:
            bool: True si le pari a été validé avec succès
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        try:
            # Localiser le bouton de validation
            btn_validation = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.CLASS_NAME,
                    self.etat_jeu["classes"].get('cpn_btn', {}).get(self.etat_jeu["site_type"], '')
                ))
            )
            
            # Cliquer sur le bouton de validation
            btn_validation.click()
            log("Pari validé avec succès", 'info')
            
            # Envoyer les données du pari à l'API si configuré
            self._send_bet_data(log_callback)
            
            return True
            
        except Exception as e:
            log(f"Erreur lors de la validation du pari : {e}", 'error')
            return False
    
    def _send_bet_data(self, log_callback=None):
        """
        Envoie les données du pari à l'API.
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        try:
            url = "https://p-com.studio/api/insert_paris.php"
            
            # Préparation des données à envoyer
            data = {
                'coupon_number': '0',
                'type_pari': self.etat_jeu.get("win_type", ""),
                'mise': self.etat_jeu["mise"],
                'gains_potentiels': self.etat_jeu["netprofit"],
                'match_details': json.dumps({
                    'teams': self.etat_jeu.get("teams", []),
                    'league': self.etat_jeu.get("ligue_name", "")
                }),
                'cote': self.etat_jeu["cote"],
                'script': self.etat_jeu["script_type"]
            }
            
            # Envoi de la requête POST
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                log("Données du pari envoyées avec succès à l'API", 'info')
            else:
                log(f"Erreur envoi API : {response.status_code}", 'warning')
                
        except Exception as e:
            log(f"Erreur lors de l'envoi des données : {e}", 'error')

    def first_game_bet(self, driver, log_callback=None):
        """
        Prépare et place le premier pari du jeu.
        Cette méthode encapsule la logique du premier pari en utilisant
        les attributs de la classe au lieu des variables globales.
        
        Args:
            driver: Instance du driver Selenium pour interagir avec le site
            log_callback: Fonction de callback pour les logs (optionnel)
            
        Returns:
            bool: True si le premier pari a été placé avec succès
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        log('PRÉPARATION PREMIER PARI', 'title')
        
        # Initialisation des variables pour le nouveau set
        self.etat_jeu["newset"] = int(self.etat_jeu.get("set_actuel", "1")) + 1
        bet_placed = False
        tentative = 0
        next_bet = False
        
        # Récupération du jeu actuel
        if not self._get_jeu_actuel(driver, log_callback):
            log('Erreur lors de la récupération du jeu actuel', 'error')
            return False
        
        while not bet_placed and not self.etat_jeu.get("error", False) and tentative < 3:
            # Récupération du score actuel
            if not self._get_score_actuel(driver, log_callback):
                log('Erreur lors de la récupération du score actuel', 'error')
                tentative += 1
                continue
            self.etat_jeu["looking_game"] = int(self.etat_jeu.get("jeu_actuel", 1))
            
            # Vérification des conditions selon le type de script
            if self.etat_jeu["script_type"] in ['30A', '4030', '4015']:
                if self.etat_jeu.get("score_actuel") not in ["0:0", "0:15", "15:0", "15:15"]:
                    log(f'Score : {self.etat_jeu.get("score_actuel")} ...1er jeu passé !', 'warning')
                    next_bet = True
                    self.etat_jeu["looking_game"] = int(self.etat_jeu.get("jeu_actuel", 1)) + 1
                    
            elif self.etat_jeu["script_type"] in ['15A', '400', '030', '300', '6P', '5P', '4P']:
                if self.etat_jeu.get("score_actuel") != "0:0":
                    log(f'Score : {self.etat_jeu.get("score_actuel")} ...1er jeu passé !', 'warning')
                    next_bet = True
                    self.etat_jeu["looking_game"] = int(self.etat_jeu.get("jeu_actuel", 1)) + 1
                    
            elif self.etat_jeu["script_type"] == '40A':
                if self.etat_jeu.get("score_actuel") in ["40:40", "A:40", "40:A"]:
                    log(f'Score : {self.etat_jeu.get("score_actuel")} ...1er jeu passé !', 'warning')
                    next_bet = True
                    self.etat_jeu["looking_game"] = int(self.etat_jeu.get("jeu_actuel", 1)) + 1
            
            # S'assurer que looking_game est au minimum 1
            if int(self.etat_jeu.get("looking_game", 1)) == 0:
                self.etat_jeu["looking_game"] = 1
            
            # Affichage des paris
            if not self._afficher_paris(driver, log_callback):
                log('Erreur lors de l\'affichage des paris', 'error')
                tentative += 1
                continue
            
            # Recherche et sélection du pari
            if not self.get_bet(driver, next_bet, log_callback=log_callback):
                log('Erreur lors de la recherche du pari', 'error')
                tentative += 1
                continue
            
            # Placement de la mise
            if not self.placer_mise(driver, log_callback):
                log('Erreur lors du placement de la mise', 'error')
                tentative += 1
                continue
            
            # Validation du pari
            if self.validation_du_paris(driver, next_bet, log_callback):
                bet_placed = True
                log('Premier pari placé avec succès', 'info')
            else:
                tentative += 1
                log('Erreur lors de la validation du pari', 'error')
        
        return bet_placed
    
    def _afficher_paris(self, driver, log_callback=None, categorie='', type_de_pari=''):
        """
        Méthode pour afficher et sélectionner les paris disponibles.
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        log('recherche du champ déroulant...', 'info')
        
        # Utilise le module global config pour les variables partagées
        try:
            import config as global_config
        except ImportError:
            global_config = None

        # Liste des scripts supportés (globale)
        all_types = []
        if global_config and hasattr(global_config, 'allScriptType'):
            all_types = global_config.allScriptType
        else:
            all_types = ['40A', '30A', '15A', '1SET', 'BREAK', '4030', '4015', '400', '6P', '5P', '4P']

        script_type = None
        if global_config and hasattr(global_config, 'scriptType'):
            script_type = global_config.scriptType
        else:
            script_type = self.etat_jeu.get('script_type', '')

        if script_type in all_types:
            self._get_set_actuel(driver)
            self._get_score_actuel(driver)

            current_set = '1'
            if global_config and hasattr(global_config, 'set_actuel') and global_config.set_actuel:
                current_set = str(global_config.set_actuel)
            else:
                current_set = str(self.etat_jeu.get('set_actuel', '1'))

            if current_set == "1":
                theset = "1er"
            else:
                theset = current_set + "ème"

            if script_type in ['1SET', 'BREAK']:
                args = ' set'
            else:
                args = ' set Evénements rapides'

            if script_type in ['4030', '4015', '400']:
                key = 'Gagne le jeu avec le score.'
            elif script_type in ['6P', '5P', '4P']:
                key = 'Nombre exact de points dans un jeu'
            elif script_type == '1SET':
                key = '1X2'
            elif script_type == 'BREAK':
                key = 'Gagne dans le jeu'
            else:
                site_type = (global_config.site_type if global_config and hasattr(global_config, 'site_type')
                             else self.etat_jeu.get('site_type', 'new_site'))
                if site_type == 'old_site':
                    key = 'Score de la partie. ' + theset + args
                else:
                    key = 'Score du jeu. ' + theset + args
        else:
            theset = ''
            args = categorie
            key = type_de_pari

        selection = False
        tentative = 1
        
        while not selection and tentative < 6:
            # Pré-calcul du nom de classe pour éviter les variables potentiellement non initialisées
            cfg_classes = (getattr(global_config, 'classes', None) if global_config else None)
            cfg_site_type = (getattr(global_config, 'site_type', None) if global_config else self.etat_jeu.get('site_type', 'new_site'))
            st_key = str(cfg_site_type or 'new_site')
            period_select_class = ''
            if cfg_classes and isinstance(cfg_classes, dict):
                period_select_class = cfg_classes.get('period_select', {}).get(st_key, '')
            else:
                period_select_class = self.etat_jeu.get('classes', {}).get('period_select', {}).get(st_key, '')

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, period_select_class)
                    )
                )
            except Exception as e:
                log(f"Champ déroulant {period_select_class} introuvable !", "warning")
                log(f'tentative {tentative}', 'warning')
                tentative += 1
            else:
                select_form = driver.find_elements(By.CLASS_NAME, period_select_class)
                try:
                    select_form[0].click()
                except Exception as e:
                    log("#E0013 Erreur lors du clic sur le champ deroulant", 'warning')
                    self._modal_handler(driver)
                    tentative += 1
                else:
                    log('ouverture du champ déroulant...', 'info')
                    time.sleep(1)
                    # Pré-calcul des classes pour le multiselect
                    ms_container_class = ''
                    ms_element_class = ''
                    if cfg_classes and isinstance(cfg_classes, dict):
                        ms_container_class = cfg_classes.get('multiselect_container_wrapper', {}).get(st_key, '')
                        ms_element_class = cfg_classes.get('multiselect_element', {}).get(st_key, '')
                    else:
                        ms_container_class = self.etat_jeu.get('classes', {}).get('multiselect_container_wrapper', {}).get(st_key, '')
                        ms_element_class = self.etat_jeu.get('classes', {}).get('multiselect_element', {}).get(st_key, '')

                    try:
                        element = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located(
                                (By.CLASS_NAME, ms_container_class)
                            )
                        )
                    except Exception as e:
                        log('#E0014 aucun element dans le champ déroulant', 'error')
                        tentative += 1
                        log(f'tentative {tentative}', 'warning')
                    else:
                        select_form_set_1 = driver.find_elements(By.CLASS_NAME, ms_element_class)
                        
                        if len(select_form_set_1) > 0:
                            for select_option in select_form_set_1:
                                if selection:
                                    break
                                try:
                                    select_option_text = select_option.text
                                    if key in select_option_text:
                                        select_option.click()
                                        selection = True
                                        log(f'Sélection effectuée : {select_option_text}', 'info')
                                        break
                                except Exception as e:
                                    log('#E0015 aucun élements multiselect__option', 'error')
                                    tentative += 1
                                    log(f'tentative {tentative}', 'warning')
                        
                        if not selection:
                            tentative += 1
                            
        return selection
    
    def _get_jeu_actuel(self, driver, log_callback=None):
        """
        Méthode pour obtenir le numéro du jeu actuel.
        """
        def log(message, level='info'):
            """Helper pour les logs"""
            if log_callback:
                log_callback(message, level)
            else:
                print(f"[{level.upper()}] {message}")
        
        try:
            import config as global_config
        except ImportError:
            global_config = None

        saved_jeu = (global_config.jeu_actuel if global_config and hasattr(global_config, 'jeu_actuel') else self.etat_jeu.get('jeu_actuel', 1))
        if global_config:
            global_config.jeu_actuel = False
        else:
            self.etat_jeu['jeu_actuel'] = False
        tentative = 0
        
        while not ((global_config and global_config.jeu_actuel) or (not global_config and self.etat_jeu['jeu_actuel'])):
            try:
                # Pré-calcul du nom de classe pour le conteneur de jeux
                cfg_classes = (getattr(global_config, 'classes', None) if global_config else None)
                cfg_site_type = (getattr(global_config, 'site_type', None) if global_config else self.etat_jeu.get('site_type', 'new_site'))
                st_key = str(cfg_site_type or 'new_site')
                jeu_container_class = ''
                if cfg_classes and isinstance(cfg_classes, dict):
                    jeu_container_class = cfg_classes.get('jeu_container', {}).get(st_key, '')
                else:
                    jeu_container_class = self.etat_jeu.get('classes', {}).get('jeu_container', {}).get(st_key, '')

                WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, jeu_container_class))
                )
                jeu_elements = driver.find_elements(By.CLASS_NAME, jeu_container_class)
            except Exception as e:
                log(f"#E0009\nUne erreur est survenue : {e}")
                log("erreur : c-scoreboard-player-score__row")
                tentative += 1
                if not self._get_if_match_page(driver):
                    if global_config:
                        global_config.error = True
                        global_config.jeu_actuel = saved_jeu
                    else:
                        self.etat_jeu['error'] = True
                        self.etat_jeu['jeu_actuel'] = saved_jeu
                    return False
                else:
                    tentative += 1
                    if tentative == 5:
                        if global_config:
                            global_config.jeu_actuel = saved_jeu
                            global_config.error = True
                        else:
                            self.etat_jeu['jeu_actuel'] = saved_jeu
                            self.etat_jeu['error'] = True
                        return False
            else:
                try:
                    self._get_set_actuel(driver)
                    
                    site_type = (global_config.site_type if global_config and hasattr(global_config, 'site_type') else self.etat_jeu.get('site_type'))
                    site_type = str(site_type or 'new_site')
                    if site_type == 'old_site':
                        jeu_actuel_player1 = jeu_elements[0].find_elements(
                            By.CLASS_NAME, (
                                (getattr(global_config, 'classes', {}).get('jeu_cell', {}).get(site_type, '') if global_config else self.etat_jeu.get('classes', {}).get('jeu_cell', {}).get(site_type, ''))
                            ))[-1]
                        jeu_actuel_player2 = jeu_elements[1].find_elements(
                            By.CLASS_NAME, (
                                (getattr(global_config, 'classes', {}).get('jeu_cell', {}).get(site_type, '') if global_config else self.etat_jeu.get('classes', {}).get('jeu_cell', {}).get(site_type, ''))
                            ))[-1]
                        current_val = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                        if global_config:
                            global_config.jeu_actuel = current_val
                        else:
                            self.etat_jeu['jeu_actuel'] = current_val
                    else:
                        # Nouveau site
                        set_index = int(global_config.set_actuel) if global_config and hasattr(global_config, 'set_actuel') else int(self.etat_jeu.get('set_actuel', '1'))
                        if 1 <= set_index <= 5:
                            jeu_actuel_player1 = jeu_elements[set_index].find_elements(
                                By.CLASS_NAME, (
                                    (getattr(global_config, 'classes', {}).get('jeu_cell', {}).get(site_type, '') if global_config else self.etat_jeu.get('classes', {}).get('jeu_cell', {}).get(site_type, ''))
                                ))[0]
                            jeu_actuel_player2 = jeu_elements[set_index].find_elements(
                                By.CLASS_NAME, (
                                    (getattr(global_config, 'classes', {}).get('jeu_cell', {}).get(site_type, '') if global_config else self.etat_jeu.get('classes', {}).get('jeu_cell', {}).get(site_type, ''))
                                ))[1]
                            current_val = int(jeu_actuel_player1.text) + int(jeu_actuel_player2.text) + 1
                            if global_config:
                                global_config.jeu_actuel = current_val
                            else:
                                self.etat_jeu['jeu_actuel'] = current_val
                        else:
                            if global_config:
                                global_config.jeu_actuel = saved_jeu
                            else:
                                self.etat_jeu['jeu_actuel'] = saved_jeu
                            return False
                            
                except Exception as e:
                    log(f"#JEU0010\nUne erreur est survenue : {e}")
                    log("erreur : numjeu")
                    if global_config:
                        global_config.jeu_actuel = saved_jeu
                    else:
                        self.etat_jeu['jeu_actuel'] = saved_jeu
                    if not self._get_if_match_page(driver):
                        if global_config:
                            global_config.error = True
                        else:
                            self.etat_jeu['error'] = True
                        return False
                    else:
                        tentative += 1
                        if tentative == 5:
                            if global_config:
                                global_config.jeu_actuel = saved_jeu
                                global_config.error = True
                            else:
                                self.etat_jeu['jeu_actuel'] = saved_jeu
                                self.etat_jeu['error'] = True
                            return False
                            
        return True
    
    def _get_score_actuel(self, driver, log_callback=None):
        """
        Délègue la récupération du score au module Functions.GetScoreActuel.
        """
        return GetScoreActuel(driver)
    
    def _record_scores(self, driver):
        """
        Délègue l'enregistrement des scores à la fonction globale.
        """
        return record_scores_global(driver)

    def _get_set_actuel(self, driver):
        """
        Délègue au module Functions.GetSetActuel.
        """
        return GetSetActuel(driver)

    def _get_if_match_page(self, driver):
        """
        Délègue au module Functions.GetIfMatchPage.
        """
        return GetIfMatchPage(driver)

    def _modal_handler(self, driver):
        """
        Délègue au module Functions.ModalHandler.
        """
        return ModalHandler(driver)