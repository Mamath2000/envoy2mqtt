import logging
import json

_LOGGER = logging.getLogger(__name__)

async def publish_energy_sensor_discovery(mqtt_client, base_topic, name, field):
    """
    Publie la déclaration Home Assistant pour le capteur d'énergie.
    Args:
        mqtt_client: client MQTT connecté
        base_topic: topic de base (ex: envoy/pv_production_energy)
        name: nom du capteur (ex: "PV Production Energy")
        sensor_id: identifiant unique du senseur (ex: pv_production_energy)
        field: champ spécifique du capteur (ex: energy)
    """
 
    sensor_id = name.lower().replace(" ", "_").replace("(", "").replace(")", "")  # Normalisation de l'ID du capteur
    discovery_topic = f"homeassistant/sensor/{sensor_id}/{field}/config"
    payload = {
        "unique_id": f"{sensor_id}_{field}",
        "object_id": f"{sensor_id}_{field}",
        "device": {
            "identifiers": [sensor_id],
            "model": "Envoy Meter S",
            "manufacturer": "Mamath",
            "name": name
        },
        "enabled_by_default": True,
        "device_class": "energy",
        "unit_of_measurement": "kWh",
        "state_class": "total_increasing",
        "state_topic": base_topic,
        "json_attributes_topic": base_topic,
        "value_template": "{{ value_json.energy }}",
        "origin": {"name": "envoy2mqtt"}
    }

    try:
        await mqtt_client.publish(discovery_topic, json.dumps(payload), retain=True)
        _LOGGER.info(f"📢 HA autodiscovery publié pour le sensor '{name}' ({field}) sur {base_topic}")
        _LOGGER.debug(f"payload: {json.dumps(payload)}")
    except Exception as e:
        _LOGGER.error(f"❌ Erreur publication discovery sensor PV production: {e}")

async def publish_pv_production_sensors(mqtt_client, topic, data):
    """
    Publie les données PV production sur le topic dédié.
    Args:
        mqtt_client: client MQTT connecté
        topic: topic MQTT cible
        data: dict contenant les valeurs des capteurs
    """

    power = data.get("prod_eim_wNow", 0)
    pv_data = {
        "energy": data.get("prod_eim_kwhLifetime"),
        "power": power if power >= 5 else 0,
        "facteur_de_puiss": data.get("prod_eim_pwrFactor"),
        "voltage": data.get("prod_eim_voltage"),
        "current": data.get("prod_eim_current"),
    }
    
    try:
        payload = json.dumps(pv_data)
        await mqtt_client.publish(topic, payload, retain=True)
        _LOGGER.info(f"✅ PV production sensors publiés sur {topic}")
        _LOGGER.debug(f"payload: {payload}")
    except Exception as e:
        _LOGGER.error(f"❌ Erreur publication PV production sensors: {e}")

async def publish_consumption_sensors(mqtt_client, topic, data):
    """
    Publie les données de consommation sur le topic dédié.
    Args:
        mqtt_client: client MQTT connecté
        topic: topic MQTT cible
        data: dict contenant les valeurs des capteurs
    """

    pv_data = {
        "energy": data.get("conso_net_eim_kwhLifetime"),
        "energy_flow": "consuming" if data.get("conso_net_eim_wNow", 0) > 0 else "producing",
        "power_cons": max(0, data.get("conso_net_eim_wNow", 0)),  # Assure que la puissance est positive
        "power": data.get("conso_net_eim_wNow"),
        "facteur_de_puiss": data.get("conso_net_eim_pwrFactor"),
        "voltage": data.get("conso_net_eim_voltage"),
        "current": data.get("conso_net_eim_current"),
    }
    
    try:
        payload = json.dumps(pv_data)
        await mqtt_client.publish(topic, payload, retain=True)
        _LOGGER.info(f"✅ Net Consumption sensors publiés sur {topic}")
        _LOGGER.debug(f"payload: {payload}")
    except Exception as e:
        _LOGGER.error(f"❌ Erreur publication Net Consumption sensors: {e}")
