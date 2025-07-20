import logging
import json

_LOGGER = logging.getLogger(__name__)

async def publish_pv_production_sensors(mqtt_client, topic, data):
    """
    Publie les données PV production sur le topic dédié.
    Args:
        mqtt_client: client MQTT connecté
        topic: topic MQTT cible
        data: dict contenant les valeurs des capteurs
    """

    pv_data = {
                        "energy": data.get("prod_eim_kwhLifetime"),
                        "power": data.get("prod_eim_wNow"),
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
