"""API client pour Enphase Envoy - Version intégrée pour envoy2mqtt."""

import asyncio
import json
import logging
import time
import urllib3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp

from const import (
    ENLIGHTEN_LOGIN_URL,
    ENTREZ_TOKEN_URL,
    ENVOY_AUTH_CHECK_ENDPOINT,
    ERROR_AUTHENTICATION_FAILED,
    ERROR_CONNECTION_FAILED,
    ERROR_TOKEN_INVALID,
    ERROR_TOKEN_MISSING,
)

# Désactiver les warnings SSL pour les certificats auto-signés de l'Envoy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LOGGER = logging.getLogger(__name__)


class EnvoyAPI:
    """Client API pour Enphase Envoy avec authentification automatique."""

    def __init__(
        self,
        username: str,
        password: str,
        envoy_host: str,
        serial_number: str,
        session: Optional[aiohttp.ClientSession] = None,
    ) -> None:
        """Initialiser le client API."""
        self.username = username
        self.password = password
        self.envoy_host = envoy_host.rstrip("/")
        self.serial_number = serial_number
        
        # Session HTTP
        self._session = session
        self._own_session = session is None
        
        # État d'authentification
        self._session_id: Optional[str] = None
        self._auth_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Cache pour les infos statiques
        self._eid_mapping_cache: Optional[Dict[int, str]] = None
        
        _LOGGER.info("🚀 EnvoyAPI initialisé pour %s @ %s", serial_number, envoy_host)

    async def __aenter__(self):
        """Gestionnaire de contexte async - entrée."""
        if self._own_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Gestionnaire de contexte async - sortie."""
        if self._own_session and self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        """Obtenir la session HTTP."""
        if not self._session:
            raise RuntimeError("Session HTTP non initialisée")
        return self._session

    @property
    def is_token_valid(self) -> bool:
        """Vérifier si le token est valide et n'a pas expiré."""
        if not self._auth_token:
            return False
        
        if self._token_expires_at and datetime.now() > self._token_expires_at:
            return False
            
        return True

    async def authenticate(self) -> None:
        """Authentifier avec Enphase et obtenir un token - Workflow Node-RED."""
        _LOGGER.info("🔐 Début authentification Enphase pour %s", self.username)
        
        try:
            # Étape 1: Login Enlighten
            _LOGGER.debug("🌐 Étape 1: Login Enlighten...")
            await self._login_to_enlighten()
            
            # Étape 2: Token Envoy avec session_id
            _LOGGER.debug("🎟️ Étape 2: Récupération token Envoy...")
            await self._get_auth_token()
            
            # Étape 3: Validation du token
            _LOGGER.debug("✅ Étape 3: Validation du token...")
            is_valid = await self.validate_token()
            
            if is_valid:
                # Définir l'expiration du token (12 heures)
                self._token_expires_at = datetime.now() + timedelta(hours=12)
                _LOGGER.info("🎉 Authentification réussie! Token valide jusqu'à %s", self._token_expires_at)
            else:
                _LOGGER.error("❌ Token récupéré mais validation échouée")
                raise aiohttp.ClientError("Token invalide après récupération")
            
        except Exception as err:
            _LOGGER.error("❌ Erreur authentification pour %s: %s", self.serial_number, err)
            raise

    async def _login_to_enlighten(self) -> None:
        """Se connecter à Enlighten pour obtenir un session_id."""
        payload = {
            "user": {
                "email": self.username,
                "password": self.password
            }
        }
        
        _LOGGER.debug("📡 POST %s", ENLIGHTEN_LOGIN_URL)
        
        try:
            async with self.session.post(
                ENLIGHTEN_LOGIN_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Envoy2MQTT"
                },
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                _LOGGER.debug("📡 Réponse Enlighten: %s", response.status)
                
                if response.status == 200:
                    result = await response.json()
                    
                    if result.get("message") == "success":
                        self._session_id = result.get("session_id")
                        
                        if self._session_id:
                            _LOGGER.info("✅ Login Enlighten réussi, session_id: %s...", self._session_id[:8])
                            return
                        else:
                            raise ValueError("Pas de session_id dans la réponse")
                    else:
                        raise ValueError(f"Login échoué: {result.get('message', 'Erreur inconnue')}")
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            raise aiohttp.ClientError("Timeout login Enlighten")
        except Exception as err:
            raise aiohttp.ClientError(f"{ERROR_AUTHENTICATION_FAILED}: {err}")

    async def _get_auth_token(self) -> None:
        """Obtenir le token Envoy avec session_id."""
        if not self._session_id:
            raise ValueError("Session ID requis pour récupérer le token")
            
        payload = {
            "session_id": self._session_id,
            "serial_num": self.serial_number,
            "username": self.username
        }
        
        _LOGGER.debug("📡 POST %s", ENTREZ_TOKEN_URL)
        
        try:
            async with self.session.post(
                ENTREZ_TOKEN_URL,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Envoy2MQTT"
                },
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    token_text = await response.text()
                    
                    if token_text and len(token_text.strip()) > 20:
                        self._auth_token = token_text.strip()
                        _LOGGER.info("✅ Token Envoy récupéré: %s...", self._auth_token[:30])
                        return
                    else:
                        raise ValueError("Token vide")
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            raise aiohttp.ClientError("Timeout récupération token")
        except Exception as err:
            raise aiohttp.ClientError(f"{ERROR_AUTHENTICATION_FAILED}: {err}")

    async def validate_token(self) -> bool:
        """Valider le token JWT avec l'Envoy local."""
        if not self._auth_token:
            _LOGGER.warning("⚠️ %s", ERROR_TOKEN_MISSING)
            return False
            
        url = f"{self.envoy_host}{ENVOY_AUTH_CHECK_ENDPOINT}"
        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
            "User-Agent": "Envoy2MQTT"
        }
        
        _LOGGER.debug("🧪 Validation token sur %s", url)
        
        try:
            async with self.session.get(
                url,
                headers=headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                
                if response.status == 200:
                    payload = await response.text()
                    
                    if "Valid token." in payload:
                        _LOGGER.info("✅ Token validé avec succès")
                        return True
                    else:
                        _LOGGER.warning("❌ Token invalide: %s", payload)
                        return False
                else:
                    _LOGGER.warning("❌ Erreur validation HTTP %s", response.status)
                    return False
                    
        except Exception as err:
            _LOGGER.error("❌ Erreur validation token: %s", err)
            return False

    async def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Effectuer une requête authentifiée vers l'Envoy."""
        if not self.is_token_valid:
            _LOGGER.debug("🔄 Token expiré, ré-authentification...")
            await self.authenticate()
        
        url = f"{self.envoy_host}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Accept": "application/json",
            "User-Agent": "Envoy2MQTT"
        }
        
        try:
            async with self.session.get(
                url,
                headers=headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                
                if response.status == 200:
                    try:
                        # Vérifier le Content-Type
                        content_type = response.headers.get('content-type', '').lower()
                        if 'application/json' not in content_type:
                            text_data = await response.text()
                            try:
                                return json.loads(text_data)
                            except Exception as e:
                                _LOGGER.warning("⚠️ Réponse non-JSON de %s (Réponse: %s)", endpoint, text_data[:200])
                                raise aiohttp.ClientError(
                                    f"Content-Type inattendu pour {endpoint}: {content_type}. "
                                    f"Impossible de parser en JSON: {e}. Réponse: {text_data[:200]}"
                                )
                        
                        return await response.json()
                    except aiohttp.ContentTypeError as e:
                        text_data = await response.text()
                        _LOGGER.warning("⚠️ Erreur ContentType sur %s: %s", endpoint, str(e))
                        raise aiohttp.ClientError(f"ContentType invalide pour {endpoint}: {str(e)}. Réponse: {text_data[:200]}")
                    except json.JSONDecodeError as e:
                        text_data = await response.text()
                        _LOGGER.warning("⚠️ JSON invalide sur %s: %s", endpoint, str(e))
                        raise aiohttp.ClientError(f"JSON invalide pour {endpoint}: {str(e)}. Réponse: {text_data[:200]}")
                        
                elif response.status == 401:
                    # Token expiré, ré-authentifier et retry
                    _LOGGER.warning("🔒 Token expiré, ré-authentification...")
                    await self.authenticate()
                    
                    # Retry avec le nouveau token
                    headers["Authorization"] = f"Bearer {self._auth_token}"
                    async with self.session.get(url, headers=headers, ssl=False, timeout=aiohttp.ClientTimeout(total=15)) as retry_response:
                        if retry_response.status == 200:
                            return await retry_response.json()
                        else:
                            error_text = await retry_response.text()
                            raise aiohttp.ClientError(f"HTTP {retry_response.status} après retry: {error_text}")
                else:
                    error_text = await response.text()
                    raise aiohttp.ClientError(f"HTTP {response.status}: {error_text}")
                    
        except asyncio.TimeoutError:
            raise aiohttp.ClientError(f"Timeout sur {endpoint}")

    async def get_meters_info(self) -> Dict[str, Any]:
        """Récupérer les informations des compteurs avec cache."""
        if self._eid_mapping_cache is not None:
            return self._eid_mapping_cache

        meters_info = await self._make_request("/ivp/meters")
        
        # Créer un mapping EID -> rôle
        eid_mapping = {}
        
        if isinstance(meters_info, list):
            for meter_config in meters_info:
                if isinstance(meter_config, dict):
                    eid = meter_config.get("eid")
                    measurement_type = meter_config.get("measurementType", "").lower()
                    if eid and measurement_type in ["production", "net-consumption"]:
                        eid_mapping[eid] = measurement_type
                        _LOGGER.debug("Mapping EID %s -> %s", eid, measurement_type)

        self._eid_mapping_cache = eid_mapping
        _LOGGER.info("💾 Cache meters_info: %d compteurs", len(eid_mapping))
        
        return eid_mapping

    async def get_meters_readings(self) -> Dict[str, Any]:
        """Récupérer les relevés des compteurs."""
        meters_info = await self.get_meters_info()
        meters_readings = await self._make_request("/ivp/meters/readings")

        if not meters_info:
            return {}

        processed = {}
        
        if isinstance(meters_readings, list):
            for meter in meters_readings:
                if isinstance(meter, dict):
                    eid = meter.get("eid")
                    if eid and eid in meters_info:
                        role = meters_info[eid]
                        processed[role] = meter
                        
        return processed

    async def get_consumption_reports(self) -> Dict[str, Any]:
        """Récupérer les rapports de consommation."""
        consumption_reports = await self._make_request("/ivp/meters/reports/consumption")

        reports = {}
        if isinstance(consumption_reports, list):
            for report in consumption_reports:
                if isinstance(report, dict):
                    report_type = report.get("reportType")
                    if report_type in ["total-consumption", "net-consumption"]:
                        reports[report_type] = report.get("cumulative", {})

        return reports

    async def get_production_v1(self) -> Dict[str, Any]:
        """Récupérer les données de production V1."""
        return await self._make_request("/api/v1/production")

    async def get_raw_data(self) -> Dict[str, Any]:
        """Récupérer les données brutes (toutes les 1 seconde)."""
        try:
            meters_data = await self.get_meters_readings()
            consumption_data = await self.get_consumption_reports()
            
            production_meter = meters_data.get("production", {})
            net_consumption_meter = meters_data.get("net-consumption", {})
            total_consumption = consumption_data.get("total-consumption", {})
            
            raw_data = {
                "conso_all_eim_wNow": total_consumption.get("currW", 0),
                "conso_net_eim_wNow": net_consumption_meter.get("instantaneousDemand", 0),
                "prod_eim_wNow": production_meter.get("instantaneousDemand", 0),
                "timestamp": int(time.time())
            }

            return raw_data
            
        except Exception as err:
            _LOGGER.error("❌ Erreur get_raw_data: %s", err)
            raise

    async def get_all_envoy_data(self) -> Dict[str, Any]:
        """Récupérer toutes les données Envoy (toutes les minutes)."""
        try:
            # Récupérer les données en parallèle
            meters_task = asyncio.create_task(self.get_meters_readings())
            consumption_task = asyncio.create_task(self.get_consumption_reports())
            production_v1_task = asyncio.create_task(self.get_production_v1())
            
            meters_data = await meters_task
            consumption_data = await consumption_task
            production_v1_data = await production_v1_task

            # Traitement des données
            production_meter = meters_data.get("production", {})
            net_consumption_meter = meters_data.get("net-consumption", {})
            
            processed_data = self._process_meters_production_data(production_meter)
            processed_data.update(self._process_meters_net_consumption_data(net_consumption_meter))

            # Calculs dérivés
            net_demand = net_consumption_meter.get("instantaneousDemand", 0)
            prod_demand = production_meter.get("instantaneousDemand", 0)

            processed_data["grid_eim_wNow"] = abs(net_demand) if net_demand < 0 else 0
            processed_data["eco_eim_wNow"] = (prod_demand + net_demand) if net_demand < 0 else prod_demand

            processed_data["eco_eim_whLifetime"] = round(processed_data.get("prod_eim_whLifetime", 0) - processed_data.get("grid_eim_whLifetime", 0), 3)

            # Données de consommation
            total_consumption = consumption_data.get("total-consumption", {})
            net_consumption_reports = consumption_data.get("net-consumption", {})
            
            processed_data.update(self._process_reports_consumption_total_data(total_consumption))
            processed_data.update(self._process_reports_consumption_net_data(net_consumption_reports))

            # Production V1
            processed_data["prod_eim_wattHoursToday"] = production_v1_data.get("wattHoursToday", 0)
            
            # Métadonnées
            processed_data["timestamp"] = int(time.time())

            return processed_data
            
        except Exception as err:
            _LOGGER.error("❌ Erreur get_all_envoy_data: %s", err)
            raise

    def _process_meters_production_data(self, meters_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter les données de production des compteurs."""
        rename_mapping = {
            "instantaneousDemand": "prod_eim_wNow",
            "actEnergyDlvd": "prod_eim_whLifetime",
            "today": "prod_eim_today"
        }

        processed = {}
        for key, value in meters_data.items():
            if isinstance(value, (int, float)) and key in rename_mapping:
                processed[rename_mapping[key]] = value
                
                if key == "actEnergyDlvd":
                    processed["prod_eim_kwhLifetime"] = round(value / 1000, 3)
                    
        return processed

    def _process_meters_net_consumption_data(self, meters_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter les données de consommation nette des compteurs."""
        rename_mapping = {
            "instantaneousDemand": "conso_net_eim_wNow",
            "actEnergyRcvd": "grid_eim_whLifetime",
            "actEnergyDlvd": "import_eim_whLifetime",
        }

        processed = {}
        for key, value in meters_data.items():
            if isinstance(value, (int, float)) and key in rename_mapping:
                processed[rename_mapping[key]] = value
                if key == "actEnergyRcvd":
                    processed["grid_eim_kwhLifetime"] = round(value / 1000, 3)
                elif key == "actEnergyDlvd":
                    processed["import_eim_kwhLifetime"] = round(value / 1000, 3)

        return processed

    def _process_reports_consumption_total_data(self, consumption_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter les données de consommation totale des rapports."""
        rename_mapping = {
            "currW": "conso_all_eim_wNow",
            "rmsCurrent": "conso_all_eim_rmsCurrent",
            "rmsVoltage": "conso_all_eim_rmsVoltage",
            "whDlvdCum": "conso_all_eim_whLifetime"
        }

        processed = {}
        for key, value in consumption_data.items():
            if isinstance(value, (int, float)) and key in rename_mapping:
                processed[rename_mapping[key]] = value
                
                if key == "whDlvdCum":
                    processed["conso_all_eim_kwhLifetime"] = round(value / 1000, 3)

        return processed

    def _process_reports_consumption_net_data(self, net_consumption_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traiter les données de consommation nette des rapports."""
        rename_mapping = {
            "whDlvdCum": "conso_net_eim_whLifetime"
        }

        processed = {}
        for key, value in net_consumption_data.items():
            if isinstance(value, (int, float)) and key in rename_mapping:
                processed[rename_mapping[key]] = value
                
                if key == "whDlvdCum":
                    processed["conso_net_eim_kwhLifetime"] = round(value / 1000, 3)

        return processed

    def clear_cache(self) -> None:
        """Vider le cache."""
        self._eid_mapping_cache = None
        _LOGGER.info("🗑️ Cache vidé")
