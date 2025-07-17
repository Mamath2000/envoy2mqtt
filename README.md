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
