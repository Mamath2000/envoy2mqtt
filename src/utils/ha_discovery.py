import json
import logging
import re

_LOGGER = logging.getLogger(__name__)


_HA_DISCOVERY_PREFIX = "homeassistant"


def _sanitize_ha_id(value: str) -> str:
    """Sanitize an ID to match HA discovery topic restrictions: [a-zA-Z0-9_-]."""
    value = str(value)
    value = re.sub(r"[^a-zA-Z0-9_-]", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "id"


def _value_template_for(sensor_def: dict) -> str:
    """Return a value_template according to unit rules.

    Règle demandée : si unit_of_measurement == 'A', conserver 2 décimales.
    """
    unit = sensor_def.get("unit_of_measurement")
    if unit == "A":
        return "{{ value | float(default=0) | round(2) }}"
    return sensor_def.get("value_template", "{{ value | float(default=0) | round(0) }}")

def get_sensor_def(field, sensors_def):
    # Trie les suffixes par longueur décroissante pour éviter les confusions
    if field in sensors_def:
        return sensors_def.get(field)
    else:
        return None

async def publish_ha_autodiscovery_dynamic(mqtt_client, device, topic_data, fields, sensors_def):

    """Publie la configuration d'autodécouverte Home Assistant pour les capteurs dynamiques.

    Implémentation : MQTT discovery *device-based*.
    Un seul topic de config est publié :
      homeassistant/device/<device_id>/config
    avec tous les composants sous la clé `components`.
    """
    _LOGGER.debug("Début de la publication HA autodiscovery dynamique (device-based)")

    serial = None
    try:
        serial = device.get("identifiers", [None])[0]
    except Exception:
        serial = None
    if not serial:
        _LOGGER.error("❌ device['identifiers'][0] manquant: impossible de publier l'autodiscovery")
        return

    device_id = _sanitize_ha_id(f"envoy_{serial}")
    config_topic = f"{_HA_DISCOVERY_PREFIX}/device/{device_id}/config"

    components = {}
    published_fields = 0
    for field in fields:
        _LOGGER.debug(f"Traitement du champ: {field}")
        if field.endswith("_00h"):
            _LOGGER.debug(f"Champ ignoré (suffixe '_00h'): {field}")
            continue  # On ignore les références minuit

        sensor_def = get_sensor_def(field, sensors_def)
        if not sensor_def:
            _LOGGER.warning(f"⚠️ Aucune définition de capteur trouvée pour le champ: {field}")
            continue

        platform = sensor_def.get("platform", "sensor")
        component_id = _sanitize_ha_id(field)

        name = sensor_def.get("name")
        object_id = None
        if isinstance(name, str) and name.strip():
            object_id = (
                "envoy_"
                + name.replace(" ", "_")
                .replace("(", "")
                .replace(")", "")
                .lower()
            )

        component_payload = {
            "platform": platform,
            "name": name,
            "state_topic": f"{topic_data}/{field}",
            "unit_of_measurement": sensor_def.get("unit_of_measurement"),
            "device_class": sensor_def.get("device_class"),
            "state_class": sensor_def.get("state_class"),
            "icon": sensor_def.get("icon"),
            "expire_after": sensor_def.get("expire_after", 120),
            "value_template": _value_template_for(sensor_def),
            "unique_id": f"envoy_{serial}_{field}",
            "object_id": object_id,
            "force_update": True,
            "has_entity_name": True,
            "payload_on": sensor_def.get("payload_on"),
            "payload_off": sensor_def.get("payload_off"),
        }

        # Nettoyage des clés None
        component_payload = {k: v for k, v in component_payload.items() if v is not None}
        components[component_id] = component_payload
        published_fields += 1

    if not components:
        _LOGGER.warning("⚠️ Aucun composant à publier en autodiscovery (device-based)")
        return

    payload = {
        "device": device,
        "origin": {
            "name": "envoy2mqtt",
        },
        "components": components,
    }

    await mqtt_client.publish(config_topic, json.dumps(payload), retain=True)
    _LOGGER.info(
        "📢 HA autodiscovery (device-based) publié sur %s (%d composants)",
        config_topic,
        published_fields,
    )
    _LOGGER.debug("Fin de la publication HA autodiscovery dynamique (device-based)")