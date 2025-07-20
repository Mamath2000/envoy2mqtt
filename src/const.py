"""Constantes pour l'API Enphase Envoy."""

# URLs des services Enphase
ENLIGHTEN_LOGIN_URL = "https://enlighten.enphaseenergy.com/login/login.json"
ENTREZ_TOKEN_URL = "https://entrez.enphaseenergy.com/tokens"

# Endpoints Envoy
ENVOY_AUTH_CHECK_ENDPOINT = "/auth/check_jwt"

# Messages d'erreur
ERROR_AUTHENTICATION_FAILED = "Échec de l'authentification"
ERROR_CONNECTION_FAILED = "Erreur de connexion"
ERROR_TOKEN_INVALID = "Token invalide"
ERROR_TOKEN_MISSING = "Token manquant"

# Configuration
TOKEN_REFRESH_INTERVAL = 60  # minutes
