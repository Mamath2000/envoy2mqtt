#!/usr/bin/env python3
"""
Service MQTT pour Enphase Envoy
Publie les données Envoy vers MQTT selon les spécifications :
- envoy/{serial}/raw/+ : données brutes toutes les 1 seconde
- envoy/{serial}/data/+ : données complètes toutes les minutes
"""

import asyncio
from datetime import datetime, time as dt_time
import json
import logging
import signal
import sys
import time
import urllib3
from typing import Dict, Any, Optional

import aiohttp
import aiomqtt

from src.envoy_api import EnvoyAPI
import src.config.config as config
import os

from src.utils.ha_discovery import publish_ha_autodiscovery_dynamic
from src.utils.energy_sensors import publish_pv_production_sensors, publish_energy_sensor_discovery,publish_consumption_sensors

# Désactiver les warnings SSL pour les certificats auto-signés de l'Envoy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


class EnvoyMQTTService:
    """Service MQTT pour publier les données Envoy."""

    def __init__(self):
        """Initialise le service MQTT Envoy"""
        self._envoy_api = None
        self._mqtt_client = None
        self._running = False
        
        # Configuration MQTT depuis config.py
        self.mqtt_host = config.MQTT_HOST
        self.mqtt_port = config.MQTT_PORT
        self.mqtt_username = config.MQTT_USERNAME
        self.mqtt_password = config.MQTT_PASSWORD
        self.base_topic = config.MQTT_BASE_TOPIC
        self.serial = config.SERIAL_NUMBER
        
        # Configuration des intervalles
        self.raw_data_interval = getattr(config, 'RAW_DATA_INTERVAL_SECONDS', 1)
        self.refresh_interval = getattr(config, 'REFRESH_INTERVAL_MINUTES', 30)

        # Flag pour activer/désactiver la publication PV production sensors
        self.pv_prod_sensor_enabled = getattr(config, 'PV_PROD_SENSOR', False)
        self.pv_prod_sensor_topic = getattr(config, 'PV_PROD_TOPIC', f"{self.base_topic}/pv_production_energy")
        self.pv_prod_sensor_name = getattr(config, 'PV_PROD_SENSOR_NAME', "PV Production Energy")

        self.conso_net_sensor_enabled = getattr(config, 'CONSO_NET_SENSOR', False)
        self.conso_net_sensor_topic = getattr(config, 'CONSO_NET_TOPIC', f"{self.base_topic}/conso_net_energy")
        self.conso_net_sensor_name = getattr(config, 'CONSO_NET_SENSOR_NAME', "Conso Nette Energy")

        # Construction des topics MQTT
        self.topic_raw = f"{self.base_topic}/{self.serial}/raw"
        self.topic_data = f"{self.base_topic}/{self.serial}/data"
        
        # Capteurs pour calculs journaliers
        self.daily_sensors = [
            'conso_all_eim_whLifetime',
            'conso_net_eim_whLifetime', 
            'prod_eim_whLifetime',
            'grid_eim_whLifetime',
            'eco_eim_whLifetime',
            'import_eim_whLifetime'
        ]
        
        # Stockage des références minuit (chargées depuis MQTT)
        self.midnight_references = {}
        
        # Dernière vérification de minuit
        self._last_midnight_check = None

        # Device info pour Home Assistant
        self.ha_device = {
            "identifiers": [self.serial],
            "manufacturer": "Enphase",
            "model": "Envoy S Meter",
            "name": "Envoy"
        }

        # Charger les noms des capteurs Home Assistant depuis device-def/sensors-def.json
        ha_sensors_file = os.path.join(os.path.dirname(__file__), "device-def/sensors-def.json")
        try:
            with open(ha_sensors_file, "r", encoding="utf-8") as f:
                self.ha_sensors_name = json.load(f)
                _LOGGER.info("✅ Noms des capteurs Home Assistant chargés depuis device-def/sensors-def.json")
        except Exception as e:
            _LOGGER.warning(f"Impossible de charger device-def/sensors-def.json: {e}")
            self.ha_sensors_name = {}

    async def _midnight_reference_listener(self):
        """Écoute les messages retained sur les topics de référence minuit et met à jour les valeurs."""
        for sensor in self.daily_sensors:
            topic = f"{self.topic_data}/{sensor}_00h"
            await self._mqtt_client.subscribe(topic)
            _LOGGER.info(f"🟢 Abonné à {topic} pour suivi des références minuit")

        async for message in self._mqtt_client.messages:
            topic = message.topic.value
            payload = message.payload.decode()
            _LOGGER.info(f"📨 Message MQTT reçu sur {topic}: {payload}")
            for sensor in self.daily_sensors:
                ref_topic = f"{self.topic_data}/{sensor}_00h"
                if topic == ref_topic:
                    try:
                        self.midnight_references[sensor] = float(payload)
                        _LOGGER.info(f"🔄 Référence {sensor} mise à jour: {payload} Wh")
                    except Exception as e:
                        _LOGGER.error(f"❌ Erreur conversion référence {sensor}: {e}")

    async def start(self):
        """Démarrer le service MQTT."""
        _LOGGER.info("🚀 Démarrage du service MQTT pour Envoy %s", self.serial)
        self._running = True
        async with aiohttp.ClientSession() as session:
            self._envoy_api = EnvoyAPI(
                username=config.USERNAME,
                password=config.PASSWORD,
                envoy_host=config.LOCAL_ENVOY_URL,
                serial_number=self.serial,
                session=session
            )

            try:
                await self._envoy_api.authenticate()
                _LOGGER.info("✅ Authentification Envoy réussie")
            except Exception as err:
                _LOGGER.error("❌ Échec authentification Envoy: %s", err)
                return

            mqtt_args = {
                "hostname": self.mqtt_host,
                "port": self.mqtt_port,
            }

            if self.mqtt_username:
                mqtt_args["username"] = self.mqtt_username
            if self.mqtt_password:
                mqtt_args["password"] = self.mqtt_password

            try:
                async with aiomqtt.Client(**mqtt_args) as mqtt_client:
                    self._mqtt_client = mqtt_client
                    _LOGGER.info("✅ Connexion MQTT réussie sur %s:%s", self.mqtt_host, self.mqtt_port)
                    await self._publish_status("online")

                    listener_task = asyncio.create_task(self._midnight_reference_listener())

                    await asyncio.sleep(10)  # Attendre 10 secondes pour laisser arriver les messages retained

                    # Charger les références minuit depuis MQTT
                    _LOGGER.info("🔄 Chargement des références minuit depuis MQTT...")
                    current_data = await self._envoy_api.get_all_envoy_data()
                    await self._initialize_missing_references(current_data)

                    # Ajout de logs pour HA_AUTODISCOVERY
                    if getattr(config, "HA_AUTODISCOVERY", False):
                        _LOGGER.info("🔄 HA_AUTODISCOVERY activé, publication autodiscovery Home Assistant...")
                        daily_values = self._calculate_daily_values(current_data).keys()
                        yesterday_keys = [sensor.replace('_today', '_yesterday') for sensor in daily_values]
                        all_fields = list(current_data.keys()) + list(daily_values) + yesterday_keys
                        await publish_ha_autodiscovery_dynamic(
                            self._mqtt_client,
                            self.ha_device,
                            self.topic_data,
                            all_fields,
                            self.ha_sensors_name
                        )

                        if self.pv_prod_sensor_enabled:
                            _LOGGER.info("🔄 Publication capteurs PV production...")
                            await publish_energy_sensor_discovery(
                                    self._mqtt_client, 
                                    self.pv_prod_sensor_topic, 
                                    self.pv_prod_sensor_name, 
                                    "energy"
                                )

                        if self.conso_net_sensor_enabled:
                            _LOGGER.info("🔄 Publication capteurs de consommation nette...")
                            await publish_energy_sensor_discovery(
                                    self._mqtt_client, 
                                    self.conso_net_sensor_topic, 
                                    self.conso_net_sensor_name, 
                                    "energy"
                                )

                        _LOGGER.info("✅ Publication autodiscovery Home Assistant terminée")

                    await self._run_publishing_tasks()
                    listener_task.cancel()

            except Exception as err:
                _LOGGER.error("❌ Erreur MQTT: %s", err)

    async def _initialize_missing_references(self, current_data: Dict[str, Any]):
        """Initialiser les références manquantes avec les valeurs actuelles (sans écraser celles déjà présentes)."""
        for sensor in self.daily_sensors:
            # Ne modifie QUE si la référence est absente
            if sensor in current_data and self.midnight_references.get(sensor) is None:
                value = current_data[sensor]
                self.midnight_references[sensor] = value
                # Publier la nouvelle référence (retained)
                topic = f"{self.topic_data}/{sensor}_00h"
                await self._mqtt_client.publish(topic, str(value), retain=True)
                _LOGGER.info("🆕 Nouvelle référence créée %s: %.2f Wh", sensor, value)
            else:
                # Log pour debug
                _LOGGER.debug("Référence %s déjà présente (%.2f Wh), conservée", sensor, self.midnight_references.get(sensor))

    async def _check_and_update_midnight_references(self, current_data: Dict[str, Any]):
        """Vérifier si on est à minuit et mettre à jour les références."""
        now = datetime.now()
        current_date = now.date()
        is_near_midnight = now.time() <= dt_time(0, 5)  # Dans les 5 premières minutes

        # Mise à jour UNIQUEMENT si on est passé minuit depuis la dernière vérification
        if is_near_midnight and (self._last_midnight_check is None or self._last_midnight_check < current_date):

            _LOGGER.info("🕛 Mise à jour des références minuit...")
            # Sauvegarder les valeurs journalières dans _yesterday
            daily_values = self._calculate_daily_values(current_data)
            for sensor, value in daily_values.items():
                yesterday_field = sensor.replace('_today', '_yesterday')
                self.midnight_references[yesterday_field] = value
                topic = f"{self.topic_data}/{yesterday_field}"
                await self._mqtt_client.publish(topic, value, retain=True)
                _LOGGER.info("🕛 Valeur d'hier sauvegardée %s: %.2f Wh", yesterday_field, value)
            
            for sensor in self.daily_sensors:
                if sensor in current_data:
                    value = current_data[sensor]
                    self.midnight_references[sensor] = value
                    
                    # Publier la nouvelle référence (retained)
                    topic = f"{self.topic_data}/{sensor}_00h"
                    await self._mqtt_client.publish(topic, value, retain=True)

                    _LOGGER.info("✅ Nouvelle référence %s: %.2f Wh", sensor, value)
            
            self._last_midnight_check = current_date

            # Ajout de logs pour HA_AUTODISCOVERY
            if getattr(config, "HA_AUTODISCOVERY", False):
                _LOGGER.info("🔄 HA_AUTODISCOVERY activé, publication autodiscovery Home Assistant...")
                yesterday_keys = [sensor.replace('_today', '_yesterday') for sensor in daily_values.keys()]
                all_fields = list(current_data.keys()) + list(daily_values.keys()) + yesterday_keys
                _LOGGER.debug("Champs pour autodiscovery: %s", all_fields)
                await publish_ha_autodiscovery_dynamic(
                    self._mqtt_client,
                    self.ha_device,
                    self.topic_data,
                    all_fields,
                    self.ha_sensors_name
                )
                _LOGGER.info("✅ Publication autodiscovery Home Assistant terminée")

                if self.pv_prod_sensor_enabled:
                    _LOGGER.info("🔄 Publication capteurs PV production...")
                    await publish_energy_sensor_discovery(
                            self._mqtt_client, 
                            self.pv_prod_sensor_topic, 
                            self.pv_prod_sensor_name, 
                            "energy"
                        )

                if self.conso_net_sensor_enabled:
                    _LOGGER.info("🔄 Publication capteurs de consommation nette...")
                    await publish_energy_sensor_discovery(
                            self._mqtt_client, 
                            self.conso_net_sensor_topic, 
                            self.conso_net_sensor_name, 
                            "energy"
                        )

    def _calculate_daily_values(self, current_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculer les valeurs journalières depuis minuit."""
        daily_values = {}
        
        # Calculs des capteurs de base
        for sensor in self.daily_sensors:
            if sensor in current_data and self.midnight_references.get(sensor) is not None:
                current_value = current_data[sensor]
                midnight_ref = self.midnight_references[sensor]
                daily_value = round(current_value - midnight_ref, 0)
                
                # Créer le nom du capteur journalier
                daily_sensor_name = sensor.replace('_whLifetime', '_today')
                daily_values[daily_sensor_name] = max(0, daily_value)  # Éviter les valeurs négatives
                _LOGGER.info("📊 %s: %.2f Wh (actuel: %.2f, minuit: %.2f)", daily_sensor_name, daily_values[daily_sensor_name], current_value, midnight_ref)
        
        return daily_values

    async def _run_publishing_tasks(self):
        """Exécuter les tâches de publication en parallèle."""
        tasks = []
        
        # Ajouter la tâche de données brutes seulement si l'intervalle > 0
        if self.raw_data_interval > 0:
            tasks.append(asyncio.create_task(self._publish_raw_data_loop()))
        else:
            _LOGGER.info("📊 Publication données brutes désactivée (RAW_DATA_INTERVAL_SECONDS = 0)")
        
        # Toujours ajouter la tâche de données complètes
        tasks.append(asyncio.create_task(self._publish_full_data_loop()))
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            _LOGGER.info("Tâches de publication annulées")
        except Exception as err:
            _LOGGER.error("❌ Erreur dans les tâches de publication: %s", err)

    async def _publish_raw_data_loop(self):
        """Publier les données brutes selon l'intervalle configuré."""
        _LOGGER.info("📊 Démarrage publication données brutes (%ss)", self.raw_data_interval)
        
        while self._running:
            try:
                start_time = time.time()
                
                # Récupérer les données brutes
                raw_data = await self._envoy_api.get_raw_data()
                
                # Publier chaque champ dans un topic séparé
                for field, value in raw_data.items():
                    topic = f"{self.topic_raw}/{field}"
                    await self._mqtt_client.publish(topic, json.dumps(value))
                                
                # Calculer le temps d'attente pour maintenir l'intervalle configuré
                elapsed = time.time() - start_time
                sleep_time = max(0, self.raw_data_interval - elapsed)
                
                if elapsed > self.raw_data_interval:
                    _LOGGER.warning("⏰ Récupération données brutes lente: %.2fs (intervalle: %ss)", elapsed, self.raw_data_interval)
                
                await asyncio.sleep(sleep_time)
                
            except Exception as err:
                _LOGGER.error("❌ Erreur publication données brutes: %s", err)
                await asyncio.sleep(self.raw_data_interval)

    async def _publish_full_data_loop(self):
        """Publier les données complètes toutes les minutes."""
        _LOGGER.info("📈 Démarrage publication données complètes (60s)")
        while self._running:
            try:
                start_time = time.time()
                # Récupérer toutes les données
                full_data = await self._envoy_api.get_all_envoy_data()
                # Initialiser les références manquantes (premier démarrage)
                await self._initialize_missing_references(full_data)
                # Vérifier et mettre à jour les références minuit si nécessaire
                await self._check_and_update_midnight_references(full_data)
                # Calculer les valeurs journalières
                daily_values = self._calculate_daily_values(full_data)

                # Publier chaque champ dans un topic séparé
                for field, value in full_data.items():
                    topic = f"{self.topic_data}/{field}"
                    await self._mqtt_client.publish(topic, value, retain=True)

                # Publier les valeurs journalières
                for field, value in daily_values.items():
                    topic = f"{self.topic_data}/{field}"
                    await self._mqtt_client.publish(topic, str(value), retain=True)

                _LOGGER.info("✅ Données complètes publiées (%d champs + %d journaliers)", len(full_data), len(daily_values))
                
                # Publication PV production sensors si activé
                if self.pv_prod_sensor_enabled:
                    await publish_pv_production_sensors(self._mqtt_client, self.pv_prod_sensor_topic, full_data)

                if self.conso_net_sensor_enabled:
                    await publish_consumption_sensors(self._mqtt_client, self.conso_net_sensor_topic, full_data)

                # Calculer le temps d'attente pour maintenir 1 minute
                elapsed = time.time() - start_time
                sleep_time = max(0, self.refresh_interval - elapsed)
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                _LOGGER.info("Tâche publication annulée")
                break
            except Exception as err:
                _LOGGER.error("❌ Erreur publication données complètes: %s", err)
                await asyncio.sleep(60)

    async def _publish_status(self, status: str):
        """Publier le statut du service."""
        if self._mqtt_client:
            await self._mqtt_client.publish(
                f"{self.base_topic}/{self.serial}/lwt",
                status,
                retain=True
            )
            _LOGGER.info("📡 Statut publié: %s", status)

    async def stop(self):
        """Arrêt propre du service MQTT."""
        self._running = False
        # Annuler toutes les tâches asynchrones si tu les stockes dans une liste
        # for task in self._tasks:
        #     task.cancel()
        #     try:
        #         await task
        #     except asyncio.CancelledError:
        #         pass

        # Publier le statut offline tant que le client est connecté
        if self._mqtt_client:
            try:
                await self._publish_status("offline")
            except Exception as err:
                _LOGGER.warning("Impossible de publier le statut offline : %s", err)
        _LOGGER.info("🛑 Service arrêté proprement")
        sys.exit(0)

async def main():
    """Fonction principale."""
    service = EnvoyMQTTService()
    
    def signal_handler(signum, frame):
        _LOGGER.info("Signal %s reçu, arrêt du service...", signum)
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(asyncio.create_task, service.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        _LOGGER.info("Arrêt demandé par l'utilisateur")
    except Exception as err:
        _LOGGER.error("❌ Erreur fatale: %s", err)
        sys.exit(1)
    finally:
        await service.stop()


# if __name__ == "__main__":
#     asyncio.run(main())
