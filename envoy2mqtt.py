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

from envoy_api import EnvoyAPI
import config

# Désactiver les warnings SSL pour les certificats auto-signés de l'Envoy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,  # Temporairement DEBUG pour diagnostiquer le téléinfo
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
        
        # Configuration téléinfo
        self.teleinfo_topic = getattr(config, 'TELEINFO_TOPIC', None)
        
        # Configuration des intervalles
        self.raw_data_interval = getattr(config, 'RAW_DATA_INTERVAL_SECONDS', 1)
        
        # Construction des topics MQTT
        self.topic_raw = f"{self.base_topic}/{self.serial}/raw"
        self.topic_data = f"{self.base_topic}/{self.serial}/data"
        
        # Capteurs pour calculs journaliers
        self.daily_sensors = [
            'conso_all_eim_whLifetime',
            'conso_net_eim_whLifetime', 
            'prod_eim_whLifetime'
        ]
        
        # Stockage des références minuit (chargées depuis MQTT)
        self.midnight_references = {}
        
        # Valeur téléinfo actuelle
        self.teleinfo_index = None
        
        # Dernière vérification de minuit
        self._last_midnight_check = None

        if self._mqtt_client:
            try:
                await self._publish_status("offline")
            except:
                pass
    
    async def _midnight_reference_listener(self):
        """Coroutine qui reste abonnée aux topics de référence et met à jour les valeurs à chaque message."""
        topics = [f"{self.topic_data}/{sensor}_00h" for sensor in self.daily_sensors]
        if self.teleinfo_topic:
            topics.append(f"{self.topic_data}/teleinfo_index_00h")
        for topic in topics:
            await self._mqtt_client.subscribe(topic)
            _LOGGER.info(f"🟢 Abonné à {topic} pour suivi des références minuit")
        async with self._mqtt_client.messages() as messages:
            async for message in messages:
                topic = message.topic.value
                payload = message.payload.decode()
                _LOGGER.debug(f"📨 Message MQTT reçu sur {topic}: {payload}")
                for sensor in self.daily_sensors:
                    ref_topic = f"{self.topic_data}/{sensor}_00h"
                    if topic == ref_topic:
                        try:
                            self.midnight_references[sensor] = float(payload)
                            _LOGGER.info(f"🔄 Référence {sensor} mise à jour: {payload} Wh")
                        except Exception as e:
                            _LOGGER.error(f"❌ Erreur conversion référence {sensor}: {e}")
                if topic == f"{self.topic_data}/teleinfo_index_00h":
                    try:
                        self.midnight_references['teleinfo_index'] = float(payload)
                        _LOGGER.info(f"🔄 Référence téléinfo mise à jour: {payload} Wh")
                    except Exception as e:
                        _LOGGER.error(f"❌ Erreur conversion référence téléinfo: {e}")

    async def _load_midnight_references(self):
        """Initialise les références à None au démarrage (elles seront mises à jour par le listener)."""
        _LOGGER.info("📖 Initialisation des références minuit à None (elles seront mises à jour par MQTT)")
        for sensor in self.daily_sensors:
            self.midnight_references[sensor] = None
        if self.teleinfo_topic:
            self.midnight_references['teleinfo_index'] = None

    async def start(self):
        """Démarrer le service MQTT."""
        _LOGGER.info("� Démarrage du service MQTT pour Envoy %s", self.serial)
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
                    # Initialiser les références à None
                    await self._load_midnight_references()
                    # Lancer le listener de référence minuit
                    listener_task = asyncio.create_task(self._midnight_reference_listener())
                    # Publier un message de statut
                    await self._publish_status("online")
                    # Attendre que les messages retained arrivent (tempo)
                    await asyncio.sleep(5)
                    # Démarrer les tâches de publication (en parallèle du listener)
                    await self._run_publishing_tasks()
                    # Annuler le listener à l'arrêt
                    listener_task.cancel()
            except Exception as err:
                _LOGGER.error("❌ Erreur MQTT: %s", err)
                            _LOGGER.debug("📊 Téléinfo mis à jour: %.0f → %.0f Wh", old_value or 0, new_value)
                    else:
                        _LOGGER.debug("⚠️ EAST.value non trouvé lors du rafraîchissement")
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    _LOGGER.debug("❌ Erreur parsing téléinfo lors du rafraîchissement: %s", e)
                
        except Exception as err:
            _LOGGER.debug("Erreur rafraîchissement téléinfo: %s", err)

    async def _initialize_missing_references(self, current_data: Dict[str, Any]):
        """Initialiser les références manquantes avec les valeurs actuelles."""
        for sensor in self.daily_sensors:
            if sensor in current_data and self.midnight_references.get(sensor) is None:
                value = current_data[sensor]
                self.midnight_references[sensor] = value
                
                # Publier la nouvelle référence (retained)
                topic = f"{self.topic_data}/{sensor}_00h"
                await self._mqtt_client.publish(topic, str(value), retain=True)
                
                _LOGGER.info("🆕 Nouvelle référence créée %s: %.2f Wh", sensor, value)
        
        # Initialiser la référence téléinfo si manquante
        if self.teleinfo_index is not None and self.midnight_references.get('teleinfo_index') is None:
            self.midnight_references['teleinfo_index'] = self.teleinfo_index
            
            # Publier la référence téléinfo (retained)
            topic = f"{self.topic_data}/teleinfo_index_00h"
            await self._mqtt_client.publish(topic, str(self.teleinfo_index), retain=True)
            
            _LOGGER.info("🆕 Nouvelle référence téléinfo créée: %.0f Wh", self.teleinfo_index)

    async def _check_and_update_midnight_references(self, current_data: Dict[str, Any]):
        """Vérifier si on est à minuit et mettre à jour les références."""
        now = datetime.now()
        current_date = now.date()
        
        # Vérifier si on est passé minuit depuis la dernière vérification
        if self._last_midnight_check is None or self._last_midnight_check < current_date:
            is_near_midnight = now.time() <= dt_time(0, 5)  # Dans les 5 premières minutes
            
            if is_near_midnight or self._last_midnight_check is None:
                _LOGGER.info("🕛 Mise à jour des références minuit...")
                
                for sensor in self.daily_sensors:
                    if sensor in current_data:
                        value = current_data[sensor]
                        self.midnight_references[sensor] = value
                        
                        # Publier la nouvelle référence (retained)
                        topic = f"{self.topic_data}/{sensor}_00h"
                        await self._mqtt_client.publish(topic, str(value), retain=True)
                        
                        _LOGGER.info("✅ Nouvelle référence %s: %.2f Wh", sensor, value)
                
                # Mettre à jour la référence téléinfo si disponible
                if self.teleinfo_index is not None:
                    self.midnight_references['teleinfo_index'] = self.teleinfo_index
                    
                    topic = f"{self.topic_data}/teleinfo_index_00h"
                    await self._mqtt_client.publish(topic, str(self.teleinfo_index), retain=True)
                    
                    _LOGGER.info("✅ Nouvelle référence téléinfo: %.0f Wh", self.teleinfo_index)
                
                self._last_midnight_check = current_date

    def _calculate_daily_values(self, current_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculer les valeurs journalières depuis minuit."""
        daily_values = {}
        
        # Calculs des capteurs de base
        for sensor in self.daily_sensors:
            if sensor in current_data and self.midnight_references.get(sensor) is not None:
                current_value = current_data[sensor]
                midnight_ref = self.midnight_references[sensor]
                daily_value = current_value - midnight_ref
                
                # Créer le nom du capteur journalier
                daily_sensor_name = sensor.replace('_whLifetime', '_today')
                daily_values[daily_sensor_name] = max(0, daily_value)  # Éviter les valeurs négatives
        
        # Calculs des capteurs dérivés (grid_eim_today et eco_eim_today)
        conso_all_today = daily_values.get('conso_all_eim_today')
        conso_net_today = daily_values.get('conso_net_eim_today')
        
        # Debug téléinfo
        _LOGGER.debug("📊 État téléinfo - index: %s, ref: %s", 
                     self.teleinfo_index, 
                     self.midnight_references.get('teleinfo_index'))
        
        # Calculer conso_grid_today (téléinfo) si disponible
        conso_grid_today = None
        if (self.teleinfo_index is not None and 
            self.midnight_references.get('teleinfo_index') is not None):
            conso_grid_today = max(0, self.teleinfo_index - self.midnight_references['teleinfo_index'])
            _LOGGER.debug("📊 Téléinfo journalier calculé: %.2f Wh", conso_grid_today)
        else:
            _LOGGER.debug("⚠️ Téléinfo indisponible pour calculs journaliers")
        
        # eco_eim_today = conso_all_today - conso_grid_today (autoconsommation)
        if conso_all_today is not None and conso_grid_today is not None:
            daily_values['eco_eim_today'] = max(0, conso_all_today - conso_grid_today)
            _LOGGER.debug("📊 eco_eim_today: %.2f Wh", daily_values['eco_eim_today'])
        
        # grid_eim_today = conso_grid_today - conso_net_today (import réseau)
        if conso_grid_today is not None and conso_net_today is not None:
            daily_values['grid_eim_today'] = max(0, conso_grid_today - conso_net_today)
            _LOGGER.debug("📊 grid_eim_today: %.2f Wh", daily_values['grid_eim_today'])
        
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
                

                # # Publier également en JSON complet
                # await self._mqtt_client.publish(
                #     f"{self.topic_raw}/json", 
                #     json.dumps(raw_data)
                # )
                
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
                    await self._mqtt_client.publish(topic, json.dumps(value), retain=True)
                # Publier les valeurs journalières
                for field, value in daily_values.items():
                    topic = f"{self.topic_data}/{field}"
                    await self._mqtt_client.publish(topic, str(value), retain=True)
                total_fields = len(full_data) + len(daily_values)
                _LOGGER.info("✅ Données complètes publiées (%d champs + %d journaliers)", len(full_data), len(daily_values))
                # Calculer le temps d'attente pour maintenir 1 minute
                elapsed = time.time() - start_time
                sleep_time = max(0, 60.0 - elapsed)
                if elapsed > 30.0:
                    _LOGGER.warning("⏰ Récupération données complètes lente: %.2fs", elapsed)
                await asyncio.sleep(sleep_time)
            except Exception as err:
                _LOGGER.error("❌ Erreur publication données complètes: %s", err)
                await asyncio.sleep(60)

    async def _publish_status(self, status: str):
        """Publier le statut du service."""
        if self._mqtt_client:
            # status_data = {
            #     "status": status,
            #     "timestamp": int(time.time())
            # }
            
            await self._mqtt_client.publish(
                f"{self.base_topic}/{self.serial}/lwt",
                status,
                retain=True
            )
            
            _LOGGER.info("📡 Statut publié: %s", status)



async def main():
    """Fonction principale."""
    # Créer le service (utilise automatiquement config.py)
    service = EnvoyMQTTService()
    
    # Gestionnaire de signaux pour arrêt propre
    def signal_handler(signum, frame):
        _LOGGER.info("Signal %s reçu, arrêt du service...", signum)
        asyncio.create_task(service.stop())
    
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


if __name__ == "__main__":
    asyncio.run(main())
