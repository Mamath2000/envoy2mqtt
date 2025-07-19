# Fonctionnalité Calculs Journaliers - envoy2mqtt

## 📊 Vue d'ensemble

Cette fonctionnalité ajoute des capteurs journaliers qui calculent la consommation et production depuis minuit pour les compteurs lifetime de l'Envoy.

## 🎯 Capteurs concernés

### Capteurs sources (lifetime):
- `conso_all_eim_whLifetime` - Consommation totale lifetime
- `conso_net_eim_whLifetime` - Consommation nette lifetime  
- `prod_eim_whLifetime` - Production lifetime

### Téléinfo (TIC mode standard):
- Topic configuré: `teleinfo/{serial}` (JSON avec `EAST.value`)
- Référence: `teleinfo_index_00h` (index compteur à minuit)

### Nouveaux capteurs journaliers créés:
- `conso_all_eim_today` - Consommation totale depuis minuit
- `conso_net_eim_today` - Consommation nette depuis minuit
- `prod_eim_today` - Production depuis minuit
- `eco_eim_today` - **Autoconsommation** (conso_all - import_réseau)
- `grid_eim_today` - **Import réseau** (compteur - conso_nette)

## 📡 Topics MQTT

### Topics de référence (retained):
```
envoy/{serial}/data/conso_all_eim_whLifetime_00h
envoy/{serial}/data/conso_net_eim_whLifetime_00h  
envoy/{serial}/data/prod_eim_whLifetime_00h
envoy/{serial}/data/teleinfo_index_00h
```

### Topics des valeurs journalières (retained):
```
envoy/{serial}/data/conso_all_eim_today
envoy/{serial}/data/conso_net_eim_today
envoy/{serial}/data/prod_eim_today
envoy/{serial}/data/eco_eim_today
envoy/{serial}/data/grid_eim_today
```

## 🔄 Logique de fonctionnement

### 1. Au démarrage du service:
- Chargement des références minuit depuis les topics MQTT retained
- Si une référence n'existe pas → création avec la valeur actuelle
- Les capteurs `_today` affichent 0 pour les nouvelles références

### 2. Fonctionnement normal:
- Calcul: `valeur_today = valeur_lifetime_actuelle - référence_00h`
- Publication des valeurs `_today` toutes les minutes (retained)

### 3. Gestion de minuit:
- Détection: entre 00:00 et 00:05
- Mise à jour automatique des références `_00h` avec les valeurs actuelles
- Reset des compteurs journaliers

## 💾 Persistance des données

- **Topics retained**: Les références minuit et valeurs journalières survivent aux redémarrages
- **Récupération automatique**: Au redémarrage, le service recharge les références depuis MQTT
- **Pas de perte de données**: Continuité assurée même après coupure

## 🕛 Exemple de cycle journalier

### Minuit (00:02):
```
prod_eim_whLifetime = 25000 Wh
→ prod_eim_whLifetime_00h = 25000 (nouvelle référence)
→ prod_eim_today = 0 Wh
```

### 14:00:
```
prod_eim_whLifetime = 25750 Wh
→ prod_eim_today = 25750 - 25000 = 750 Wh
```

### Minuit suivant (00:01):
```
prod_eim_whLifetime = 26200 Wh
→ prod_eim_whLifetime_00h = 26200 (mise à jour référence)
→ prod_eim_today = 0 Wh (reset)
```

## 🏠 Intégration Home Assistant

Les capteurs `_today` peuvent être directement utilisés dans Home Assistant:

```yaml
sensor:
  - name: "Production Solaire Aujourd'hui"
    state_topic: "envoy/122226051519/data/prod_eim_today"
    unit_of_measurement: "Wh"
    device_class: "energy"
    
  - name: "Consommation Aujourd'hui"  
    state_topic: "envoy/122226051519/data/conso_all_eim_today"
    unit_of_measurement: "Wh"
    device_class: "energy"
```

## ⚠️ Considérations importantes

- **Fenêtre de minuit**: Détection entre 00:00 et 00:05 pour éviter les problèmes de timing
- **Valeurs négatives**: Protection contre les valeurs négatives (max(0, daily_value))
- **Premier démarrage**: Création automatique des références manquantes
- **Robustesse**: Gestion des erreurs et timeout lors du chargement des références

## 🔧 Configuration

Configuration dans `config.py` :
