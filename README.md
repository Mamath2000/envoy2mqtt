# Envoy2MQTT

🌞 **Passerelle Enphase Envoy vers MQTT**

Ce projet permet de publier les données de votre passerelle Enphase Envoy S vers un broker MQTT en temps réel.

## ⚡ Commande principale pour lancer envoy2mqtt

```bash
make run
```

Cette commande lance le service en mode interactif (Ctrl+C pour arrêter).

## 🚀 Installation rapide

```bash
# 1. Installer les dépendances
make install

# 2. Configurer vos identifiants
cp config_example.py config.py
nano config.py  # Éditez avec vos identifiants Enphase

# 3. Lancer le service
make run
```

## 📝 Configuration

Éditez le fichier `config.py` avec :

- **USERNAME/PASSWORD** : Vos identifiants Enphase (mêmes que sur enlighten.enphaseenergy.com)
- **SERIAL_NUMBER** : Numéro de série de votre Envoy S (12 chiffres)
- **LOCAL_ENVOY_URL** : IP locale de votre Envoy (ex: https://192.168.1.100)
- **MQTT_HOST** : Adresse de votre broker MQTT
- **MQTT_BASE_TOPIC** : Topic de base MQTT (par défaut "envoy")
- **RAW_DATA_INTERVAL_SECONDS** : Intervalle de publication des données brutes en secondes (par défaut 1, 0 = désactivé)

## 📡 Topics MQTT

Les données sont publiées sur :

- `{base_topic}/{serial}/raw/{field}` : Données brutes (intervalle configurable, par défaut 1s, 0 = désactivé)
- `{base_topic}/{serial}/data/{field}` : Données complètes (1/min)
- `{base_topic}/{serial}/status` : Statut du service

Exemple avec `MQTT_BASE_TOPIC = "solar"` et `SERIAL_NUMBER = "123456789012"` :
- `solar/123456789012/raw/production`
- `solar/123456789012/data/complete`
- `solar/123456789012/status`

## 🔧 Service systemd (optionnel)

Pour faire tourner envoy2mqtt en arrière-plan :

```bash
# Installer le service
make service-install

# Démarrer le service
make service-start

# Voir les logs
make service-logs

# Arrêter le service
make service-stop

# Désinstaller le service
make service-remove
```

## 🛠️ Commandes disponibles

```bash
make help              # Afficher l'aide
make install           # Installer les dépendances
make run               # Lancer envoy2mqtt (COMMANDE PRINCIPALE)
make service-install   # Installer le service systemd
make service-start     # Démarrer le service
make service-stop      # Arrêter le service
make service-status    # Voir le statut du service
make service-logs      # Voir les logs en temps réel
make service-remove    # Désinstaller le service
make clean             # Nettoyer les fichiers temporaires
```

## 🔍 Dépannage

1. **Erreur d'authentification** : Vérifiez vos identifiants Enphase
2. **Envoy non trouvé** : Vérifiez l'IP locale de votre Envoy
3. **MQTT ne fonctionne pas** : Vérifiez l'adresse de votre broker

Utilisez `make service-logs` pour voir les logs détaillés.

## ✅ Status du service

Si vous voyez ces messages, tout fonctionne correctement :
- `✅ Authentification Envoy réussie`
- `✅ Connexion MQTT réussie`
- `📡 Statut publié: online`
- `📊 Démarrage publication données brutes (1s)`
- `📈 Démarrage publication données complètes (60s)`

# EnvoyAPI – Documentation de la classe

La classe `EnvoyAPI` permet d’interagir avec la passerelle Enphase Envoy S via son API locale et l’API Enlighten. Elle gère l’authentification, la récupération des données et le rafraîchissement du token.

## Attributs principaux

- `username`, `password` : Identifiants Enlighten
- `envoy_host` : Adresse locale de la passerelle
- `serial_number` : Numéro de série Envoy
- `_session` : Session HTTP aiohttp

## Méthodes principales

### `async authenticate()`
**Rôle** : Authentifie l’utilisateur auprès de l’API Enlighten et récupère un token JWT pour les requêtes locales.

**Paramètres** : Aucun  
**Retour** : None (met à jour l’état interne du client)

**Exemple d’appel** :
```python
await api.authenticate()
```

---

### `async get_raw_data()`
**Rôle** : Récupère les données brutes de production et de consommation depuis la passerelle.

**Paramètres** : Aucun  
**Retour** : `Dict[str, Any]`

**Exemple d’appel** :
```python
raw = await api.get_raw_data()
print(raw["production"])
```
**Exemple de sortie** :
```python
{
    "production": 1234.5,
    "consumption": 678.9,
    "timestamp": 1721460000
}
```

---

### `async get_all_envoy_data()`
**Rôle** : Récupère toutes les données consolidées : production, consommation nette, énergie injectée, etc.

**Paramètres** : Aucun  
**Retour** : `Dict[str, Any]`

**Exemple d’appel** :
```python
data = await api.get_all_envoy_data()
print(data["prod_eim_whLifetime"])
```
**Exemple de sortie** :
```python
{
    "prod_eim_whLifetime": 9354611.767,
    "conso_all_eim_whLifetime": 33253406.226,
    "conso_net_eim_whLifetime": 23899915.788,
    "grid_eim_whLifetime": 2126308.666,
    "eco_eim_whLifetime": 7242918.837,
    "timestamp": 1721460000
}
```

---

### `async refresh_token()`
**Rôle** : Rafraîchit le token JWT si nécessaire (selon l’intervalle défini).

**Paramètres** : Aucun  
**Retour** : None

**Exemple d’appel** :
```python
await api.refresh_token()
```

---

### `async get_meters_info()`
**Rôle** : Retourne les informations sur les compteurs connectés à la passerelle (EID, type, etc.).

**Paramètres** : Aucun  
**Retour** : `List[Dict[str, Any]]`

**Exemple d’appel** :
```python
meters = await api.get_meters_info()
for meter in meters:
    print(meter["type"], meter["eid"])
```
**Exemple de sortie** :
```python
[
    {"eid": 704643328, "type": "production", "state": "active"},
    {"eid": 704643584, "type": "net-consumption", "state": "active"}
]
```

---

### `async get_status()`
**Rôle** : Retourne le statut actuel de la passerelle (connectivité, état, erreurs éventuelles).

**Paramètres** : Aucun  
**Retour** : `Dict[str, Any]`

**Exemple d’appel** :
```python
status = await api.get_status()
print(status["status"])
```
**Exemple de sortie** :
```python
{
    "status": "normal",
    "last_update": "2025-07-20T14:23:45",
    "errors": []
}
```

---

## Exemple d’utilisation complet

```python
api = EnvoyAPI(username, password, envoy_host, serial_number)
await api.authenticate()
data = await api.get_all_envoy_data()
print("Production totale :", data["prod_eim_whLifetime"])
meters = await api.get_meters_info()
print("Compteurs :", meters)
status = await api.get_status()
print("Statut Envoy :", status["status"])
```

---

# Fonctionnement de la gestion des sensors journaliers dans envoy2mqtt

Le script [envoy2mqtt.py](http://_vscodecontentref_/0) publie les données Envoy sur MQTT et gère le calcul des valeurs journalières pour chaque capteur.

## Principes

- À chaque démarrage, les références "minuit" sont récupérées via MQTT (messages retained).
- Si une référence est absente, elle est initialisée avec la valeur actuelle.
- Chaque minute, les valeurs actuelles sont lues et la différence avec la référence minuit est calculée pour obtenir la valeur journalière.
- À minuit, les références sont mises à jour et la valeur de la veille est sauvegardée.

## Méthodes clés

- `_initialize_missing_references(data)` : Initialise les références minuit manquantes.
- `_check_and_update_midnight_references(data)` : Met à jour les références à minuit et sauvegarde les valeurs de la veille.
- `_calculate_daily_values(data)` : Calcule les valeurs journalières pour chaque capteur.

## Topics MQTT utilisés

- `{base_topic}/{serial}/data/{sensor}_00h` : Référence minuit (retained)
- `{base_topic}/{serial}/data/{sensor}_today` : Valeur journalière
- `{base_topic}/{serial}/data/{sensor}_yesterday` : Valeur de la veille

---

# Endpoints API appelés sur la passerelle Envoy

Voici les principaux endpoints utilisés pour récupérer les données :

- `/api/v1/production`  
  → Données de production instantanée et cumulée.

- `/api/v1/consumption`  
  → Données de consommation instantanée et cumulée.

- `/api/v1/meters`  
  → Informations sur les compteurs connectés (EID, type, etc.).

- `/auth/check_jwt`  
  → Vérification du token JWT pour l’accès local.

- `/api/v1/status`  
  → Statut général de la passerelle (connectivité, erreurs).

**Remarque :** Certains endpoints nécessitent un token JWT obtenu via l’API Enlighten.

---

N’hésite pas à demander si tu veux un format ou des détails supplémentaires
