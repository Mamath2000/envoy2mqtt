#!/usr/bin/env python3
"""
Service MQTT pour Enphase Envoy
Publie les données Envoy vers MQTT selon les spécifications :
- envoy/{serial}/raw/+ : données brutes toutes les 1 seconde
- envoy/{serial}/data/+ : données complètes toutes les minutes
"""

import asyncio
import json
import logging
import signal
import sys
import time
import urllib3
from typing import Dict, Any, Optional

import aiohttp
import asyncio_mqtt as aiomqtt

from envoy_api import EnvoyAPI
import config

# Désactiver les warnings SSL pour les certificats auto-signés de l'Envoy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)


class EnvoyMQTTService:
    """Service MQTT pour publier les données Envoy."""

    def __init__(self):
        """Initialise le service MQTT Envoy"""
        self.envoy_api = None
        self.mqtt_client = None
        self.running = False
        
        # Configuration MQTT depuis config.py
        self.mqtt_host = config.MQTT_HOST
        self.mqtt_port = config.MQTT_PORT
        self.mqtt_username = config.MQTT_USERNAME
        self.mqtt_password = config.MQTT_PASSWORD
        self.base_topic = config.MQTT_BASE_TOPIC
        self.serial = config.SERIAL_NUMBER
        
        # Construction des topics MQTT
        self.topic_raw = f"{self.base_topic}/{self.serial}/raw"
        self.topic_data = f"{self.base_topic}/{self.serial}/data"

    async def start(self):
        """Démarrer le service MQTT."""
        _LOGGER.info("🟢 Démarrage du service MQTT pour Envoy %s", self.serial)
        
        self._running = True
        
        async with aiohttp.ClientSession() as session:
            # Initialiser l'API Envoy
            self._envoy_api = EnvoyAPI(
                username=self.username,
                password=self.password,
                envoy_host=self.envoy_host,
                serial_number=self.serial,
                session=session
            )
            
            # Authentifier au démarrage
            try:
                await self._envoy_api.authenticate()
                _LOGGER.info("✅ Authentification Envoy réussie")
            except Exception as err:
                _LOGGER.error("❌ Échec authentification Envoy: %s", err)
                return
            
            # Connecter MQTT
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
                    
                    # Publier un message de statut
                    await self._publish_status("online")
                    
                    # Démarrer les tâches de publication
                    await self._run_publishing_tasks()
                    
            except Exception as err:
                _LOGGER.error("❌ Erreur MQTT: %s", err)
                
    async def stop(self):
        """Arrêter le service."""
        _LOGGER.info("🔴 Arrêt du service MQTT")
        self._running = False
        
        if self._mqtt_client:
            try:
                await self._publish_status("offline")
            except:
                pass

    async def _run_publishing_tasks(self):
        """Exécuter les tâches de publication en parallèle."""
        tasks = [
            asyncio.create_task(self._publish_raw_data_loop()),
            asyncio.create_task(self._publish_full_data_loop()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            _LOGGER.info("Tâches de publication annulées")
        except Exception as err:
            _LOGGER.error("❌ Erreur dans les tâches de publication: %s", err)

    async def _publish_raw_data_loop(self):
        """Publier les données brutes toutes les 1 seconde."""
        _LOGGER.info("📊 Démarrage publication données brutes (1s)")
        
        while self._running:
            try:
                start_time = time.time()
                
                # Récupérer les données brutes
                raw_data = await self._envoy_api.get_raw_data()
                
                # Publier chaque champ dans un topic séparé
                for field, value in raw_data.items():
                    topic = f"{self.topic_raw}/{field}"
                    await self._mqtt_client.publish(topic, json.dumps(value))
                
                # Publier également en JSON complet
                await self._mqtt_client.publish(
                    f"{self.topic_raw}/json", 
                    json.dumps(raw_data)
                )
                
                # Calculer le temps d'attente pour maintenir 1Hz
                elapsed = time.time() - start_time
                sleep_time = max(0, 1.0 - elapsed)
                
                if elapsed > 1.0:
                    _LOGGER.warning("⏰ Récupération données brutes lente: %.2fs", elapsed)
                
                await asyncio.sleep(sleep_time)
                
            except Exception as err:
                _LOGGER.error("❌ Erreur publication données brutes: %s", err)
                await asyncio.sleep(1)

    async def _publish_full_data_loop(self):
        """Publier les données complètes toutes les minutes."""
        _LOGGER.info("📈 Démarrage publication données complètes (60s)")
        
        while self._running:
            try:
                start_time = time.time()
                
                # Récupérer toutes les données
                full_data = await self._envoy_api.get_all_envoy_data()
                
                # Publier chaque champ dans un topic séparé
                for field, value in full_data.items():
                    topic = f"{self.topic_data}/{field}"
                    await self._mqtt_client.publish(topic, json.dumps(value))
                
                # Publier également en JSON complet
                await self._mqtt_client.publish(
                    f"{self.topic_data}/json", 
                    json.dumps(full_data)
                )
                
                _LOGGER.info("✅ Données complètes publiées (%d champs)", len(full_data))
                
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
            status_data = {
                "status": status,
                "timestamp": int(time.time()),
                "serial": self.serial
            }
            
            await self._mqtt_client.publish(
                f"{self.base_topic}/{self.serial}/status",
                json.dumps(status_data),
                retain=True
            )
            
            _LOGGER.info("📡 Statut publié: %s", status)


def load_config():
    """Charger la configuration depuis config.py."""
    try:
        import config
        return {
            'username': config.USERNAME,
            'password': config.PASSWORD,
            'serial_number': config.SERIAL_NUMBER,
            'envoy_host': config.LOCAL_ENVOY_URL,
            'mqtt_host': getattr(config, 'MQTT_HOST', 'localhost'),
            'mqtt_port': getattr(config, 'MQTT_PORT', 1883),
            'mqtt_username': getattr(config, 'MQTT_USERNAME', None),
            'mqtt_password': getattr(config, 'MQTT_PASSWORD', None),
        }
    except ImportError:
        _LOGGER.error("❌ Fichier config.py non trouvé")
        return None
    except AttributeError as e:
        _LOGGER.error("❌ Configuration incomplète: %s", e)
        return None


async def main():
    """Fonction principale."""
    # Charger la configuration
    config_data = load_config()
    if not config_data:
        print("❌ Impossible de charger la configuration")
        sys.exit(1)
    
    # Créer le service
    service = EnvoyMQTTService(
        username=config_data['username'],
        password=config_data['password'],
        envoy_host=config_data['envoy_host'],
        serial_number=config_data['serial_number'],
        mqtt_host=config_data['mqtt_host'],
        mqtt_port=config_data['mqtt_port'],
        mqtt_username=config_data['mqtt_username'],
        mqtt_password=config_data['mqtt_password'],
    )
    
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
