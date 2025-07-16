#!/usr/bin/env python3
"""
Script d'authentification pour passerelle Envoy S d'Enphase
Reproduit le processus Node-RED pour obtenir et valider les tokens JWT
"""

import requests
import time
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnvoyAuth:
    """Classe pour gérer l'authentification avec la passerelle Envoy S"""
    
    def __init__(self, username: str, password: str, serial_number: str, local_envoy_url: str):
        """
        Initialise la classe d'authentification
        
        Args:
            username: Email du compte Enphase
            password: Mot de passe du compte Enphase  
            serial_number: Numéro de série de la passerelle Envoy
            local_envoy_url: URL locale de la passerelle Envoy (ex: https://192.168.1.100)
        """
        self.username = username
        self.password = password
        self.serial_number = serial_number
        self.local_envoy_url = local_envoy_url.rstrip('/')
        
        # Variables d'état
        self.session_id: Optional[str] = None
        self.auth_token: Optional[str] = None
        self.cookies: Optional[Dict] = None
        
        # URLs des services Enphase
        self.login_url = "https://enlighten.enphaseenergy.com/login/login.json"
        self.token_url = "https://entrez.enphaseenergy.com/tokens"
        
        # Configuration des requêtes
        self.session = requests.Session()
        self.session.verify = False  # Désactive la vérification SSL comme dans Node-RED
        
    def validate_token(self) -> bool:
        """
        Valide le token JWT actuel
        
        Returns:
            True si le token est valide, False sinon
        """
        if not self.auth_token:
            logger.warning("Aucun token à valider")
            return False
            
        try:
            url = f"{self.local_envoy_url}/auth/check_jwt"
            headers = {
                'Authorization': f'Bearer {self.auth_token.strip()}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Validation du token sur {url}")
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                if "Valid token." in response.text:
                    logger.info("Token valide")
                    # Mise à jour des cookies si présents
                    if response.cookies:
                        self.cookies = dict(response.cookies)
                    return True
                else:
                    logger.warning("Token non valide selon la réponse")
                    return False
            else:
                logger.error(f"Erreur HTTP lors de la validation: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la validation du token: {e}")
            return False
    
    def login(self) -> bool:
        """
        Effectue la connexion sur le portail Enphase
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            payload = {
                "user": {
                    "email": self.username,
                    "password": self.password
                }
            }
            
            logger.info(f"Connexion sur {self.login_url}")
            response = self.session.post(
                self.login_url, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "session_id" in data:
                    self.session_id = data["session_id"]
                    logger.info(f"Connexion réussie, session_id: {self.session_id}")
                    return True
                else:
                    logger.error("session_id manquant dans la réponse")
                    return False
            else:
                logger.error(f"Échec de la connexion: {response.status_code}")
                logger.debug(f"Réponse: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de décodage JSON: {e}")
            return False
    
    def get_token(self) -> bool:
        """
        Récupère le token d'authentification
        
        Returns:
            True si le token est obtenu, False sinon
        """
        if not self.session_id:
            logger.error("session_id requis pour obtenir le token")
            return False
            
        try:
            payload = {
                "session_id": self.session_id,
                "serial_num": self.serial_number,
                "username": self.username
            }
            
            logger.info(f"Récupération du token sur {self.token_url}")
            response = self.session.post(
                self.token_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.auth_token = response.text.strip()
                logger.info("Token d'authentification obtenu")
                return True
            else:
                logger.error(f"Échec de récupération du token: {response.status_code}")
                logger.debug(f"Réponse: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération du token: {e}")
            return False
    
    def authenticate(self) -> bool:
        """
        Processus complet d'authentification
        
        Returns:
            True si l'authentification réussit, False sinon
        """
        logger.info("Début du processus d'authentification")
        
        # 1. Vérifier si nous avons déjà un token valide
        if self.auth_token and self.validate_token():
            logger.info("Token existant toujours valide")
            return True
        
        # 2. Connexion
        if not self.login():
            logger.error("Échec de la connexion")
            return False
        
        # 3. Récupération du token
        if not self.get_token():
            logger.error("Échec de la récupération du token")
            return False
        
        # 4. Validation du nouveau token
        if not self.validate_token():
            logger.error("Le nouveau token n'est pas valide")
            return False
        
        logger.info("Authentification réussie")
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Retourne les en-têtes d'authentification pour les requêtes API
        
        Returns:
            Dictionnaire des en-têtes HTTP
        """
        if not self.auth_token:
            raise ValueError("Aucun token d'authentification disponible")
            
        return {
            'Authorization': f'Bearer {self.auth_token.strip()}',
            'Content-Type': 'application/json'
        }
    
    def refresh_token_periodically(self, interval_minutes: int = 10):
        """
        Actualise le token périodiquement (comme le délai de 10 minutes dans Node-RED)
        
        Args:
            interval_minutes: Intervalle en minutes entre les actualisations
        """
        logger.info(f"Démarrage de l'actualisation périodique du token (toutes les {interval_minutes} minutes)")
        
        while True:
            try:
                time.sleep(interval_minutes * 60)
                logger.info("Actualisation périodique du token")
                
                if not self.validate_token():
                    logger.warning("Token invalide, réauthentification nécessaire")
                    if not self.authenticate():
                        logger.error("Échec de la réauthentification")
                    
            except KeyboardInterrupt:
                logger.info("Arrêt de l'actualisation périodique")
                break
            except Exception as e:
                logger.error(f"Erreur lors de l'actualisation périodique: {e}")


def load_config():
    """Charge la configuration depuis le fichier config.py"""
    try:
        import config
        return {
            'username': config.USERNAME,
            'password': config.PASSWORD,
            'serial_number': config.SERIAL_NUMBER,
            'local_envoy_url': config.LOCAL_ENVOY_URL,
            'refresh_interval': getattr(config, 'REFRESH_INTERVAL_MINUTES', 10),
            'log_level': getattr(config, 'LOG_LEVEL', 'INFO')
        }
    except ImportError:
        logger.error("Fichier config.py non trouvé. Copiez config_example.py vers config.py et configurez-le.")
        return None
    except AttributeError as e:
        logger.error(f"Configuration incomplète dans config.py: {e}")
        return None


def main():
    """Fonction principale pour tester l'authentification"""
    
    # Charger la configuration
    config_data = load_config()
    if not config_data:
        print("❌ Impossible de charger la configuration")
        print("Copiez config_example.py vers config.py et configurez vos informations")
        return
    
    # Configurer le niveau de log
    log_level = getattr(logging, config_data['log_level'].upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    
    # Créer l'instance d'authentification
    auth = EnvoyAuth(
        username=config_data['username'],
        password=config_data['password'],
        serial_number=config_data['serial_number'],
        local_envoy_url=config_data['local_envoy_url']
    )
    
    # Tenter l'authentification
    if auth.authenticate():
        print("✅ Authentification réussie!")
        print(f"Token: {auth.auth_token[:20]}...")
        
        # Exemple d'utilisation des en-têtes d'authentification
        headers = auth.get_auth_headers()
        print(f"En-têtes d'authentification prêts")
        
        print(f"\nVous pouvez maintenant utiliser ces en-têtes pour accéder à:")
        print(f"  - {config_data['local_envoy_url']}/production.json")
        print(f"  - {config_data['local_envoy_url']}/inventory.json")
        print(f"  - {config_data['local_envoy_url']}/info.json")
        
        # Démarrer l'actualisation périodique (optionnel)
        # auth.refresh_token_periodically(config_data['refresh_interval'])
        
    else:
        print("❌ Échec de l'authentification")


if __name__ == "__main__":
    main()
