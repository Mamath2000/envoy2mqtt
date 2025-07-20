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
    for field in fields:
        if field.endswith('_00h'):
            continue  # On ignore les références minuit

        sensor_def = get_sensor_def(field, sensors_def)
        if not sensor_def:
            continue  # Catégorie non définie
        config_topic = f"homeassistant/{sensor_def.get('platform', 'sensor')}/envoy_{device['identifiers'][0]}/{field}/config"
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
            "device": device
        }
        # Nettoyage des clés None
        payload = {k: v for k, v in payload.items() if v is not None}
        
        await mqtt_client.publish(config_topic, json.dumps(payload), retain=True)
        _LOGGER.info(f"📢 HA autodiscovery publié pour {field} ({payload['platform']})")