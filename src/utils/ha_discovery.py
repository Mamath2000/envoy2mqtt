import json
import logging

_LOGGER = logging.getLogger(__name__)

def get_sensor_def(field, sensors_def):
    # Trie les suffixes par longueur décroissante pour éviter les confusions
    if field in sensors_def:
        return sensors_def.get(field)
    else:
        return None

async def publish_ha_autodiscovery_dynamic(mqtt_client, device, topic_data, fields, sensors_def):

    """Publie la configuration d'autodécouverte Home Assistant pour les capteurs dynamiques."""
    _LOGGER.debug("Début de la publication HA autodiscovery dynamique")
    for field in fields:
        _LOGGER.debug(f"Traitement du champ: {field}")
        if field.endswith('_00h'):
            _LOGGER.debug(f"Champ ignoré (suffixe '_00h'): {field}")
            continue  # On ignore les références minuit

        sensor_def = get_sensor_def(field, sensors_def)
        if not sensor_def:
            _LOGGER.warning(f"⚠️ Aucune définition de capteur trouvée pour le champ: {field}")
            continue  # Catégorie non définie
        config_topic = f"homeassistant/{sensor_def.get('platform', 'sensor')}/envoy_{device['identifiers'][0]}/{field}/config"
        _LOGGER.debug(f"Topic de configuration: {config_topic}")

        payload = {
            "name": sensor_def.get("name"),
            "state_topic": f"{topic_data}/{field}",
            "unit_of_measurement": sensor_def.get("unit_of_measurement"),
            "device_class": sensor_def.get("device_class"),
            "state_class": sensor_def.get("state_class"),
            "icon": sensor_def.get("icon"),
            "expire_after": sensor_def.get("expire_after",120),
            "value_template": sensor_def.get("value_template", "{{ value | float(default=0) | round(0) }}"),
            "unique_id": f"envoy_{device['identifiers'][0]}_{field}",
            "object_id": f"envoy_{sensor_def.get('name').replace(' ', '_').replace('(', '').replace(')', '').lower()}",
            "force_update": True,
            "has_entity_name": True,
            "payload_on": sensor_def.get("payload_on"),
            "payload_off": sensor_def.get("payload_off"),
            "device": device
        }
        
        # Nettoyage des clés None
        payload = {k: v for k, v in payload.items() if v is not None}
        # _LOGGER.debug(f"Payload généré pour {field}: {payload}")
        # Publication de la configuration dans Home Assistant

        await mqtt_client.publish(config_topic, json.dumps(payload), retain=True)
        _LOGGER.info(f"📢 HA autodiscovery publié pour {field} ({sensor_def.get('platform', 'sensor')})")
    _LOGGER.debug("Fin de la publication HA autodiscovery dynamique")