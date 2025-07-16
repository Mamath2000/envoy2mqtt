#!/usr/bin/env python3
"""
Exemple d'utilisation avancée de l'authentification Envoy
Démontre comment utiliser la classe EnvoyAuth pour récupérer des données
"""

import time
import json
import requests
from envoy_auth import EnvoyAuth

class EnvoyClient:
    """Client pour interagir avec l'API Envoy après authentification"""
    
    def __init__(self, auth: EnvoyAuth):
        """
        Initialise le client Envoy
        
        Args:
            auth: Instance d'EnvoyAuth authentifiée
        """
        self.auth = auth
        self.session = requests.Session()
        self.session.verify = False
    
    def get_production_data(self):
        """Récupère les données de production"""
        try:
            url = f"{self.auth.local_envoy_url}/production.json"
            headers = self.auth.get_auth_headers()
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur lors de la récupération des données de production: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    def get_inventory(self):
        """Récupère l'inventaire des équipements"""
        try:
            url = f"{self.auth.local_envoy_url}/inventory.json"
            headers = self.auth.get_auth_headers()
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur lors de la récupération de l'inventaire: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erreur: {e}")
            return None
    
    def get_info(self):
        """Récupère les informations système"""
        try:
            url = f"{self.auth.local_envoy_url}/info.json"
            headers = self.auth.get_auth_headers()
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erreur lors de la récupération des informations: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Erreur: {e}")
            return None


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
        print("❌ Fichier config.py non trouvé. Copiez config_example.py vers config.py et configurez-le.")
        return None
    except AttributeError as e:
        print(f"❌ Configuration incomplète dans config.py: {e}")
        return None


def demo_envoy_data():
    """Démonstration de récupération de données Envoy"""
    
    print("=== Démonstration Client Envoy ===")
    
    # Charger la configuration
    config_data = load_config()
    if not config_data:
        return
    
    # 1. Authentification
    print("1. Authentification...")
    auth = EnvoyAuth(
        config_data['username'], 
        config_data['password'], 
        config_data['serial_number'], 
        config_data['local_envoy_url']
    )
    
    if not auth.authenticate():
        print("❌ Échec de l'authentification")
        return
    
    print("✅ Authentification réussie")
    
    # 2. Création du client
    client = EnvoyClient(auth)
    
    # 3. Récupération des données
    print("\n2. Récupération des données...")
    
    # Informations système
    print("\n--- Informations système ---")
    info = client.get_info()
    if info:
        print(json.dumps(info, indent=2))
    
    # Données de production
    print("\n--- Données de production ---")
    production = client.get_production_data()
    if production:
        print(json.dumps(production, indent=2))
    
    # Inventaire
    print("\n--- Inventaire ---")
    inventory = client.get_inventory()
    if inventory:
        print(json.dumps(inventory, indent=2))


def continuous_monitoring():
    """Surveillance continue avec rafraîchissement automatique du token"""
    
    print("=== Surveillance Continue ===")
    
    # Charger la configuration
    config_data = load_config()
    if not config_data:
        return
    
    # Authentification
    auth = EnvoyAuth(
        config_data['username'], 
        config_data['password'], 
        config_data['serial_number'], 
        config_data['local_envoy_url']
    )
    
    if not auth.authenticate():
        print("❌ Échec de l'authentification")
        return
    
    client = EnvoyClient(auth)
    
    print("Surveillance démarrée (Ctrl+C pour arrêter)")
    
    try:
        while True:
            # Vérifier et rafraîchir le token si nécessaire
            if not auth.validate_token():
                print("Token expiré, réauthentification...")
                if not auth.authenticate():
                    print("❌ Échec de la réauthentification")
                    break
            
            # Récupérer les données de production
            production = client.get_production_data()
            if production and 'production' in production:
                current_power = production['production'][1]['wNow']
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{timestamp}] Production actuelle: {current_power} W")
            
            # Attendre 60 secondes avant la prochaine mesure
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nSurveillance arrêtée")


if __name__ == "__main__":
    # Choisissez le mode de démonstration
    
    # Mode 1: Récupération simple des données
    demo_envoy_data()
    
    # Mode 2: Surveillance continue (décommentez pour utiliser)
    # continuous_monitoring()
