# Configuration pour l'authentification Envoy
# Copiez ce fichier en config.py et remplissez vos informations

# Informations de connexion Enphase
# Utilisez les mêmes identifiants que pour le site enlighten.enphaseenergy.com
USERNAME = "votre-email@example.com"  # Votre email Enphase
PASSWORD = "votre-mot-de-passe"       # Votre mot de passe Enphase

# Numéro de série de votre passerelle Envoy S
# Trouvez-le sur l'étiquette de votre Envoy ou dans l'app Enphase
SERIAL_NUMBER = "123456789012"        # Format: 12 chiffres

# URL locale de votre passerelle Envoy
# Trouvez l'IP de votre Envoy sur votre réseau local
# Généralement quelque chose comme 192.168.1.xxx ou 192.168.0.xxx
LOCAL_ENVOY_URL = "https://192.168.1.100"  # Remplacez par l'IP de votre Envoy

# Configuration MQTT
MQTT_HOST = "localhost"               # Adresse du broker MQTT
MQTT_PORT = 1883                      # Port du broker MQTT
MQTT_USERNAME = None                  # Nom d'utilisateur MQTT (optionnel)
MQTT_PASSWORD = None                  # Mot de passe MQTT (optionnel)
MQTT_BASE_TOPIC = "envoy"             # Topic de base MQTT (ex: envoy/{serial}/data/...)

# Paramètres optionnels
REFRESH_INTERVAL_MINUTES = 10  # Intervalle de rafraîchissement du token
RAW_DATA_INTERVAL_SECONDS = 1  # Intervalle de publication des données brutes (en secondes, 0 = désactivé)
LOG_LEVEL = "INFO"             # DEBUG, INFO, WARNING, ERROR

# Active/désactive la publication des sensors PV production sur le topic dédié
PV_PROD_SENSOR = False  # True pour activer, False pour désactiver
PV_PROD_TOPIC = "envoy/pv_production_energy"  # Topic MQTT pour la publication PV production sensors
PV_PROD_SENSOR_NAME = "PV Production Energy"  # Nom du capteur PV production pour Home Assistant

# Active/désactive la publication des sensors de consommation nette
CONSO_NET_SENSOR = False  # True pour activer, False pour désactiver
CONSO_NET_TOPIC = "envoy/conso_net_energy"  # Topic MQTT pour la publication de la consommation nette
CONSO_NET_SENSOR_NAME = "Conso Nette Energy"  # Nom du capteur de consommation nette pour Home Assistant

# Exemples d'URLs Envoy typiques:
# LOCAL_ENVOY_URL = "https://192.168.1.100"   # IP fixe
# LOCAL_ENVOY_URL = "https://envoy.local"      # Nom mDNS (si supporté)
# LOCAL_ENVOY_URL = "https://192.168.0.50"    # Autre plage IP courante

# Exemples de configuration MQTT:
# MQTT_HOST = "192.168.1.10"          # Broker MQTT sur le réseau local
# MQTT_HOST = "homeassistant.local"    # Home Assistant avec Mosquitto
# MQTT_USERNAME = "mqtt_user"          # Si authentification requise
# MQTT_PASSWORD = "mqtt_password"      # Si authentification requise
# MQTT_BASE_TOPIC = "solar"            # Pour utiliser solar/{serial}/data/... au lieu de envoy/
