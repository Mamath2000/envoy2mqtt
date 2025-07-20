# Envoy2MQTT

## 🧩 Fonctionnalités principales

```mermaid
flowchart TD
    A[Passerelle Envoy S Metered]
    subgraph MQTT
        B1[Publication sensors complets]
        B2[Publication sensors PRODUCT & CONSO NETTE]
        B3[Publication haute fréquence (1Hz) de métriques clés]
    end
    subgraph Home Assistant
        C1[Autodiscovery & intégration sensors]
        C2[Automatisations & pilotage équipements]
    end

    A --> B1
    A --> B2
    A --> B3
    B1 --> C1
    B2 --> C1
    B3 --> C2

    %% Explications
    classDef exp fill:#f9f,stroke:#333,stroke-width:2px;
    class B1,B2,B3 exp;
```

Ce programme propose plusieurs fonctionnalités autour de la passerelle Enphase Envoy S Metered :

### 1. Récupération et exposition des sensors de la passerelle

- Récupère de nombreux capteurs de la passerelle Envoy : index de consommation, index de production, énergie renvoyée au réseau, économie réalisée, etc.
- Tire parti des deux capteurs ampèremétriques internes de la passerelle Envoy S Metered pour suivre précisément la consommation et la production.
- Expose tous ces sensors côté Home Assistant via MQTT et autodiscovery, permettant un suivi complet et une intégration domotique avancée.

### 2. Publication dédiée des deux sensors principaux

- Publie deux sensors MQTT correspondant aux deux capteurs ampèremétriques :
  - **PRODUCT** : suivi de la production photovoltaïque instantanée et cumulée.
  - **CONSO NETTE** : suivi de la consommation nette (après soustraction de la production locale).
- Ces sensors sont déclarés automatiquement pour Home Assistant et utilisables dans vos automatisations.

### 3. Publication haute fréquence (1 Hz) de métriques clés

- Publie à haute fréquence (par exemple 1 Hz) les valeurs instantanées :
  - `conso_all_eim_wNow` : puissance totale consommée
  - `conso_net_eim_wNow` : puissance nette consommée
  - `prod_eim_wNow` : puissance instantanée produite
- Ces publications MQTT permettent de piloter en temps réel des équipements d’optimisation de la consommation, comme un routeur solaire (ex : gestion d’un chauffe-eau).



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
cp src/config/config_example.py src/config/config.py
nano src/config/config.py  # Éditez avec vos identifiants Enphase

# 3. Lancer le service
make run
```


## 📝 Configuration

Éditez le fichier `src/config/config.py` avec les paramètres suivants :

- **USERNAME / PASSWORD** : Identifiants Enphase Enlighten
- **SERIAL_NUMBER** : Numéro de série de votre Envoy S (12 chiffres)
- **LOCAL_ENVOY_URL** : IP locale de votre Envoy (ex: https://192.168.1.100)
- **MQTT_HOST / MQTT_PORT / MQTT_USERNAME / MQTT_PASSWORD** : Configuration du broker MQTT
- **MQTT_BASE_TOPIC** : Topic de base MQTT (ex: envoy)
- **RAW_DATA_INTERVAL_SECONDS** : Intervalle de publication des données brutes (secondes, 0 = désactivé)
- **REFRESH_INTERVAL_MINUTES** : Intervalle de rafraîchissement du token
- **LOG_LEVEL** : Niveau de log (DEBUG, INFO, WARNING, ERROR)

### Flags et options avancées

- **HA_AUTODISCOVERY** : Active la publication Home Assistant autodiscovery (True/False)
- **PV_PROD_SENSOR** : Active la publication du sensor PV production sur le topic dédié (True/False)
- **PV_PROD_TOPIC** : Topic MQTT pour la publication du sensor PV production (ex: envoy/pv_production_energy)
- **PV_PROD_SENSOR_NAME** : Nom du capteur PV production pour Home Assistant (ex: "PV Production Energy")
- **CONSO_NET_SENSOR** : Active la publication du sensor de consommation nette sur le topic dédié (True/False)
- **CONSO_NET_TOPIC** : Topic MQTT pour la publication du sensor consommation nette (ex: envoy/conso_net_energy)
- **CONSO_NET_SENSOR_NAME** : Nom du capteur consommation nette pour Home Assistant (ex: "Conso Nette Energy")

### Description des sensors publiés

#### Sensors standards envoyés sur MQTT

- **prod_eim_kwhLifetime** : Énergie totale produite (kWh)
- **prod_eim_wNow** : Puissance instantanée produite (W)
- **prod_eim_pwrFactor** : Facteur de puissance production
- **prod_eim_voltage** : Tension production (V)
- **prod_eim_current** : Courant production (A)
- **conso_net_eim_kwhLifetime** : Énergie nette consommée (kWh)
- **conso_net_eim_wNow** : Puissance nette consommée (W)
- **conso_net_eim_pwrFactor** : Facteur de puissance consommation nette
- **conso_net_eim_voltage** : Tension consommation nette (V)
- **conso_net_eim_current** : Courant consommation nette (A)

#### Sensors Home Assistant autodiscovery

Si activé, chaque sensor est déclaré automatiquement pour Home Assistant avec les attributs :
- `unique_id`, `object_id`, `device`, `device_class`, `unit_of_measurement`, `state_class`, `state_topic`, `json_attributes_topic`, `value_template`, etc.

Exemple pour le sensor PV production :
```json
{
  "unique_id": "pv_production_energy_energy",
  "object_id": "pv_production_energy_energy",
  "device": {
    "identifiers": ["envoy_122226051519"],
    "model": "Envoy Meter S",
    "manufacturer": "Mamath",
    "name": "PV Production Energy"
  },
  "enabled_by_default": true,
  "device_class": "energy",
  "unit_of_measurement": "kWh",
  "state_class": "total_increasing",
  "state_topic": "envoy/pv_production_energy",
  "json_attributes_topic": "envoy/pv_production_energy",
  "value_template": "{{ value_json.energy }}"
}
```

#### Sensors journaliers

Pour chaque capteur, les valeurs suivantes sont calculées et publiées :
- `{sensor}_00h` : Référence minuit (valeur à minuit)
- `{sensor}_today` : Valeur journalière (depuis minuit)
- `{sensor}_yesterday` : Valeur de la veille

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

### `authenticate()`
Authentifie l’utilisateur auprès de l’API Enlighten et récupère un token d’accès pour les requêtes locales.

### `get_raw_data()`
Récupère les données brutes (production, consommation, etc.) depuis la passerelle Envoy.

### `get_all_envoy_data()`
Récupère toutes les données consolidées (production, consommation nette, etc.) depuis la passerelle.

### `refresh_token()`
Rafraîchit le token d’accès si nécessaire (intervalle configurable).

### `get_meters_info()`
Retourne les informations sur les compteurs connectés à la passerelle.

### `get_status()`
Retourne le statut actuel de la passerelle (connectivité, état, etc.).

## Exemple d’utilisation

```python
api = EnvoyAPI(username, password, envoy_host, serial_number)
await api.authenticate()
data = await api.get_all_envoy_data()
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
