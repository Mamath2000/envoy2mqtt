# Authentification Envoy S en Python

Ce projet reproduit le processus d'authentification Node-RED pour les passerelles Envoy S d'Enphase Energy, permettant d'accéder aux données de production solaire.

## Fonctionnalités

- ✅ Authentification complète avec les serveurs Enphase
- ✅ Validation automatique des tokens JWT
- ✅ Rafraîchissement périodique des tokens
- ✅ Gestion des erreurs et des reconnexions
- ✅ Interface simple pour récupérer les données Envoy

## Installation automatique (recommandée)

### Option 1 : Avec Makefile (le plus simple)

```bash
make install    # Installation automatique
make config     # Ouvrir et configurer le fichier de configuration
make test       # Tester la configuration
make auth       # Tester l'authentification
```

### Option 2 : Script d'installation classique

```bash
chmod +x install.sh
./install.sh
# Puis éditez config.py avec vos informations
```

Le script d'installation va automatiquement :
- ✅ Créer un environnement virtuel Python
- ✅ Installer toutes les dépendances nécessaires
- ✅ Créer le fichier de configuration à partir du modèle
- ✅ Créer des scripts de lancement simplifiés
- ✅ Créer un script de désinstallation

## Installation manuelle

Si vous préférez installer manuellement :

1. Créez un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Copiez et configurez le fichier de configuration :
```bash
cp config_example.py config.py
```

## Workflow recommandé

Pour une première utilisation :

```bash
# 1. Installation
make install

# 2. Configuration (ouvre l'éditeur)
make config

# 3. Test de la configuration
make test

# 4. Test d'authentification
make auth

# 5. Surveillance continue
make monitor
```

## Configuration

Après l'installation (automatique ou manuelle), éditez le fichier `config.py` :

```python
USERNAME = "votre-email@enphase.com"
PASSWORD = "votre-mot-de-passe"
SERIAL_NUMBER = "123456789012"  # Numéro de série de votre Envoy
LOCAL_ENVOY_URL = "https://192.168.1.100"  # IP de votre Envoy
```

## Utilisation rapide (après installation automatique)

### Avec Makefile (recommandé)

```bash
make test       # Test de configuration
make auth       # Test d'authentification
make demo       # Démonstration complète
make monitor    # Surveillance continue
make help       # Voir toutes les commandes
```

### Avec les scripts directs

```bash
./run.sh test     # Test de configuration
./run.sh auth     # Test d'authentification
./run.sh demo     # Démonstration complète
./run.sh monitor  # Surveillance continue
./run.sh          # Voir l'aide
```

## Utilisation avancée (programmation)

Si vous avez installé avec les scripts automatiques, activez d'abord l'environnement virtuel :

```bash
source venv/bin/activate
```

### Authentification simple

```python
from envoy_auth import EnvoyAuth

# Créer l'instance d'authentification
auth = EnvoyAuth(
    username="votre-email@enphase.com",
    password="votre-mot-de-passe", 
    serial_number="123456789012",
    local_envoy_url="https://192.168.1.100"
)

# S'authentifier
if auth.authenticate():
    print("Authentification réussie!")
    
    # Récupérer les en-têtes pour les requêtes API
    headers = auth.get_auth_headers()
    
    # Utiliser ces en-têtes pour vos requêtes vers l'Envoy
    import requests
    response = requests.get(
        "https://192.168.1.100/production.json",
        headers=headers,
        verify=False
    )
```

### Utilisation avec le client avancé

```python
from envoy_auth import EnvoyAuth
from example_usage import EnvoyClient

# Authentification
auth = EnvoyAuth(username, password, serial_number, local_envoy_url)
auth.authenticate()

# Création du client
client = EnvoyClient(auth)

# Récupération des données
production = client.get_production_data()
inventory = client.get_inventory()
info = client.get_info()
```

## Processus d'authentification

Le script reproduit fidèlement le processus Node-RED :

1. **Validation du token existant** : Vérifie si un token JWT est déjà valide
2. **Connexion Enphase** : Login sur `enlighten.enphaseenergy.com` avec email/mot de passe
3. **Récupération du session_id** : Obtient un ID de session temporaire
4. **Demande de token** : Utilise le session_id + numéro de série pour obtenir un token JWT
5. **Validation du token** : Vérifie que le token fonctionne avec votre Envoy local
6. **Rafraîchissement automatique** : Renouvelle le token toutes les 10 minutes

## API Endpoints disponibles

Une fois authentifié, vous pouvez accéder aux endpoints suivants sur votre Envoy :

- `/production.json` - Données de production en temps réel
- `/inventory.json` - Inventaire des micro-onduleurs
- `/info.json` - Informations système
- `/auth/check_jwt` - Validation du token JWT

## Surveillance continue

Pour une surveillance en continu avec rafraîchissement automatique :

```python
# Démarrer la surveillance continue
auth.refresh_token_periodically(interval_minutes=10)
```

## Gestion des erreurs

Le script gère automatiquement :

- Les tokens expirés (réauthentification automatique)
- Les erreurs de réseau (retry avec logging)
- Les erreurs d'authentification (messages explicites)
- La validation des certificats SSL (désactivée comme dans Node-RED)

## Sécurité

⚠️ **Important** : 
- Ne commitez jamais vos identifiants dans un repository public
- Utilisez des variables d'environnement en production
- La vérification SSL est désactivée pour correspondre au comportement Node-RED

## Logs

Le script utilise le module `logging` de Python pour tracer les opérations :

```python
import logging
logging.basicConfig(level=logging.DEBUG)  # Pour plus de détails
```

## Exemples d'utilisation

Voir `example_usage.py` pour des exemples complets incluant :

- Récupération ponctuelle de données
- Surveillance continue avec rafraîchissement automatique
- Gestion des erreurs et reconnexions

## Troubleshooting

### Token invalide
- Vérifiez vos identifiants Enphase
- Assurez-vous que le numéro de série est correct
- Vérifiez que l'IP de votre Envoy est accessible

### Erreurs de réseau
- Vérifiez la connectivité vers les serveurs Enphase
- Assurez-vous que votre Envoy est accessible localement
- Vérifiez les paramètres de pare-feu

### Erreurs SSL
- Le script désactive la vérification SSL par défaut
- Si nécessaire, vous pouvez l'activer en modifiant `session.verify = True`

# envoy2mqtt
