#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de notification pour les événements importants
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationManager:
    """
    Gestionnaire de notifications pour les événements importants
    """
    
    def __init__(self, config_manager=None, logger=None):
        """
        Initialisation du gestionnaire de notifications
        
        Args:
            config_manager: Instance du gestionnaire de configuration
            logger: Instance du système de journalisation
        """
        self.config_manager = config_manager
        self.logger = logger
        
        # Configuration par défaut
        self.email_enabled = False
        self.email_config = {
            "smtp_server": "",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_email": "",
            "to_email": ""
        }
        
        self.telegram_enabled = False
        self.telegram_config = {
            "bot_token": "",
            "chat_id": ""
        }
        
        # Charger la configuration
        self._load_config()
    
    def _load_config(self):
        """
        Charge la configuration des notifications
        """
        if self.config_manager:
            # Configuration des notifications par email
            email_config = self.config_manager.config.get("notifications", {}).get("email", {})
            self.email_enabled = email_config.get("enabled", False)
            if self.email_enabled:
                self.email_config.update(email_config)
            
            # Configuration des notifications Telegram
            telegram_config = self.config_manager.config.get("notifications", {}).get("telegram", {})
            self.telegram_enabled = telegram_config.get("enabled", False)
            if self.telegram_enabled:
                self.telegram_config.update(telegram_config)
    
    def send_email(self, subject, message):
        """
        Envoie une notification par email
        
        Args:
            subject: Sujet de l'email
            message: Contenu de l'email
            
        Returns:
            bool: True si l'email a été envoyé avec succès, False sinon
        """
        if not self.email_enabled:
            if self.logger:
                self.logger.warning("Les notifications par email ne sont pas activées")
            return False
        
        try:
            # Créer le message
            msg = MIMEMultipart()
            msg['From'] = self.email_config["from_email"]
            msg['To'] = self.email_config["to_email"]
            msg['Subject'] = subject
            
            # Ajouter le corps du message
            msg.attach(MIMEText(message, 'plain'))
            
            # Connexion au serveur SMTP
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            
            # Envoyer l'email
            server.send_message(msg)
            server.quit()
            
            if self.logger:
                self.logger.info(f"Email envoyé avec succès: {subject}")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lors de l'envoi de l'email: {e}")
            return False
    
    def send_telegram(self, message):
        """
        Envoie une notification via Telegram
        
        Args:
            message: Message à envoyer
            
        Returns:
            bool: True si le message a été envoyé avec succès, False sinon
        """
        if not self.telegram_enabled:
            if self.logger:
                self.logger.warning("Les notifications Telegram ne sont pas activées")
            return False
        
        try:
            # URL de l'API Telegram
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            
            # Paramètres de la requête
            params = {
                "chat_id": self.telegram_config["chat_id"],
                "text": message,
                "parse_mode": "Markdown"
            }
            
            # Envoyer la requête
            response = requests.post(url, params=params)
            
            # Vérifier la réponse
            if response.status_code == 200:
                if self.logger:
                    self.logger.info("Message Telegram envoyé avec succès")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Erreur lors de l'envoi du message Telegram: {response.text}")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Erreur lors de l'envoi du message Telegram: {e}")
            return False
    
    def notify(self, title, message, notification_type="all"):
        """
        Envoie une notification via tous les canaux activés ou un canal spécifique
        
        Args:
            title: Titre de la notification
            message: Contenu de la notification
            notification_type: Type de notification (all, email, telegram)
            
        Returns:
            dict: Résultats des envois par canal
        """
        results = {}
        
        if notification_type in ["all", "email"]:
            results["email"] = self.send_email(title, message)
        
        if notification_type in ["all", "telegram"]:
            results["telegram"] = self.send_telegram(f"*{title}*\n\n{message}")
        
        return results
    
    def notify_pari_place(self, strategie, match_data, mise):
        """
        Envoie une notification pour un pari placé
        
        Args:
            strategie: Nom de la stratégie
            match_data: Données du match
            mise: Montant de la mise
        """
        title = f"Pari placé - {strategie}"
        message = f"Un pari a été placé avec la stratégie {strategie}.\n"
        message += f"Match: {match_data.get('home_team')} vs {match_data.get('away_team')}\n"
        message += f"Mise: {mise}\n"
        message += f"Date: {match_data.get('date')}"
        
        return self.notify(title, message)
    
    def notify_pari_gagne(self, strategie, match_data, gain):
        """
        Envoie une notification pour un pari gagné
        
        Args:
            strategie: Nom de la stratégie
            match_data: Données du match
            gain: Montant du gain
        """
        title = f"Pari gagné - {strategie}"
        message = f"Un pari a été gagné avec la stratégie {strategie}.\n"
        message += f"Match: {match_data.get('home_team')} vs {match_data.get('away_team')}\n"
        message += f"Gain: {gain}\n"
        message += f"Date: {match_data.get('date')}"
        
        return self.notify(title, message)
    
    def notify_pari_perdu(self, strategie, match_data, perte):
        """
        Envoie une notification pour un pari perdu
        
        Args:
            strategie: Nom de la stratégie
            match_data: Données du match
            perte: Montant de la perte
        """
        title = f"Pari perdu - {strategie}"
        message = f"Un pari a été perdu avec la stratégie {strategie}.\n"
        message += f"Match: {match_data.get('home_team')} vs {match_data.get('away_team')}\n"
        message += f"Perte: {perte}\n"
        message += f"Date: {match_data.get('date')}"
        
        return self.notify(title, message)
    
    def notify_erreur(self, message, details=None):
        """
        Envoie une notification pour une erreur
        
        Args:
            message: Message d'erreur
            details: Détails supplémentaires
        """
        title = "Erreur système"
        notification_message = f"{message}\n"
        
        if details:
            notification_message += f"Détails: {details}"
        
        return self.notify(title, notification_message)