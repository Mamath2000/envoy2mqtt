#!/usr/bin/env python3
"""
Script de test pour l'API Envoy
Teste tous les endpoints et sauvegarde les résultats dans le répertoire debug
"""

import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from pathlib import Path

import aiohttp

from envoy_api import EnvoyAPI
import config

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Répertoire de debug
DEBUG_DIR = Path("debug")


async def save_json_result(filename: str, data: any, success: bool = True) -> None:
    """Sauvegarder le résultat au format JSON."""
    DEBUG_DIR.mkdir(exist_ok=True)
    
    # Timestamp pour le nom de fichier
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Statut
    status = "SUCCESS" if success else "ERROR"
    
    # Nom de fichier avec timestamp et statut
    file_path = DEBUG_DIR / f"{timestamp}_{status}_{filename}.json"
    
    # Données à sauvegarder
    result = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "data": data,
        "config": {
            "serial_number": config.SERIAL_NUMBER,
            "envoy_host": config.LOCAL_ENVOY_URL,
            "username": config.USERNAME
        }
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        
        _LOGGER.info("💾 Sauvegardé: %s", file_path)
        
    except Exception as e:
        _LOGGER.error("❌ Erreur sauvegarde %s: %s", file_path, e)


async def test_endpoint(api: EnvoyAPI, method_name: str, description: str) -> None:
    """Tester un endpoint spécifique."""
    _LOGGER.info("🧪 Test: %s", description)
    
    try:
        # Obtenir la méthode
        method = getattr(api, method_name)
        
        # Exécuter la méthode
        start_time = datetime.now()
        result = await method()
        end_time = datetime.now()
        
        # Calculer la durée
        duration = (end_time - start_time).total_seconds()
        
        # Préparer les données de résultat
        test_result = {
            "method": method_name,
            "description": description,
            "duration_seconds": duration,
            "result": result
        }
        
        # Sauvegarder le résultat
        await save_json_result(f"test_{method_name}", test_result, success=True)
        
        _LOGGER.info("✅ %s - Durée: %.2fs - Éléments: %s", 
                    description, duration, 
                    len(result) if isinstance(result, (dict, list)) else "N/A")
        
    except Exception as e:
        error_info = {
            "method": method_name,
            "description": description,
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
        await save_json_result(f"error_{method_name}", error_info, success=False)
        
        _LOGGER.error("❌ %s - Erreur: %s", description, e)


async def test_authentication(api: EnvoyAPI) -> bool:
    """Tester l'authentification."""
    _LOGGER.info("🔐 Test d'authentification...")
    
    try:
        start_time = datetime.now()
        await api.authenticate()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        auth_result = {
            "method": "authenticate",
            "description": "Authentification complète",
            "duration_seconds": duration,
            "session_id": api._session_id[:8] + "..." if api._session_id else None,
            "token_preview": api._auth_token[:30] + "..." if api._auth_token else None,
            "token_expires_at": api._token_expires_at.isoformat() if api._token_expires_at else None,
            "is_token_valid": api.is_token_valid
        }
        
        await save_json_result("test_authenticate", auth_result, success=True)
        
        _LOGGER.info("✅ Authentification réussie - Durée: %.2fs", duration)
        return True
        
    except Exception as e:
        error_info = {
            "method": "authenticate",
            "description": "Authentification complète",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
        await save_json_result("error_authenticate", error_info, success=False)
        
        _LOGGER.error("❌ Authentification échouée: %s", e)
        return False


async def test_token_validation(api: EnvoyAPI) -> None:
    """Tester la validation du token."""
    _LOGGER.info("🧪 Test de validation du token...")
    
    try:
        start_time = datetime.now()
        is_valid = await api.validate_token()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        validation_result = {
            "method": "validate_token",
            "description": "Validation du token",
            "duration_seconds": duration,
            "is_valid": is_valid,
            "token_preview": api._auth_token[:30] + "..." if api._auth_token else None
        }
        
        await save_json_result("test_validate_token", validation_result, success=True)
        
        _LOGGER.info("✅ Validation token - Durée: %.2fs - Valide: %s", duration, is_valid)
        
    except Exception as e:
        error_info = {
            "method": "validate_token",
            "description": "Validation du token",
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        
        await save_json_result("error_validate_token", error_info, success=False)
        
        _LOGGER.error("❌ Validation token échouée: %s", e)


# async def test_raw_endpoints(api: EnvoyAPI) -> None:
#     """Tester les endpoints bruts."""
#     _LOGGER.info("🔧 Test des endpoints bruts...")
    
#     raw_endpoints = [
#         ("/ivp/meters", "Informations des compteurs"),
#         ("/ivp/meters/readings", "Lectures des compteurs"),
#         ("/ivp/meters/reports/consumption", "Rapports de consommation"),
#         ("/api/v1/production", "Production V1"),
#         ("/auth/check_jwt", "Vérification JWT")
#     ]
    
#     for endpoint, description in raw_endpoints:
#         try:
#             _LOGGER.info("🌐 Test endpoint: %s", endpoint)
            
#             start_time = datetime.now()
#             result = await api._make_request(endpoint)
#             end_time = datetime.now()
            
#             duration = (end_time - start_time).total_seconds()
            
#             endpoint_result = {
#                 "endpoint": endpoint,
#                 "description": description,
#                 "duration_seconds": duration,
#                 "result": result
#             }
            
#             # Nom de fichier sécurisé
#             safe_name = endpoint.replace("/", "_").replace("?", "_")
#             await save_json_result(f"raw_endpoint{safe_name}", endpoint_result, success=True)
            
#             _LOGGER.info("✅ %s - Durée: %.2fs", description, duration)
            
#         except Exception as e:
#             error_info = {
#                 "endpoint": endpoint,
#                 "description": description,
#                 "error": str(e),
#                 "traceback": traceback.format_exc()
#             }
            
#             safe_name = endpoint.replace("/", "_").replace("?", "_")
#             await save_json_result(f"error_raw_endpoint{safe_name}", error_info, success=False)
            
#             _LOGGER.error("❌ %s - Erreur: %s", description, e)


async def run_complete_test() -> None:
    """Exécuter le test complet de l'API Envoy."""
    _LOGGER.info("🚀 Démarrage du test complet de l'API Envoy")
    _LOGGER.info("📁 Répertoire de debug: %s", DEBUG_DIR.absolute())
    
    # Nettoyer le répertoire debug
    if DEBUG_DIR.exists():
        for file in DEBUG_DIR.glob("*.json"):
            file.unlink()
        _LOGGER.info("🧹 Répertoire debug nettoyé")
    
    # Informations de configuration
    config_info = {
        "serial_number": config.SERIAL_NUMBER,
        "envoy_host": config.LOCAL_ENVOY_URL,
        "username": config.USERNAME,
        "mqtt_host": config.MQTT_HOST,
        "mqtt_base_topic": config.MQTT_BASE_TOPIC,
        "raw_data_interval": getattr(config, 'RAW_DATA_INTERVAL_SECONDS', 1)
    }
    
    await save_json_result("config_info", config_info, success=True)
    
    async with aiohttp.ClientSession() as session:
        # Initialiser l'API
        api = EnvoyAPI(
            username=config.USERNAME,
            password=config.PASSWORD,
            envoy_host=config.LOCAL_ENVOY_URL,
            serial_number=config.SERIAL_NUMBER,
            session=session
        )
        
        # Test 1: Authentification
        auth_success = await test_authentication(api)
        
        if not auth_success:
            _LOGGER.error("💥 Arrêt des tests - Authentification échouée")
            return
        
        # Test 2: Validation du token
        await test_token_validation(api)
        
        # Test 3: Endpoints haut niveau
        endpoints_to_test = [
            ("get_meters_info", "Informations des compteurs (avec cache)"),
            ("get_meters_readings", "Lectures des compteurs (traitées)"),
            ("get_consumption_reports", "Rapports de consommation (traités)"),
            ("get_production_v1", "Production V1"),
            ("get_raw_data", "Données brutes (pour MQTT 1Hz)"),
            ("get_all_envoy_data", "Toutes les données (pour MQTT 1/min)")
        ]
        
        for method_name, description in endpoints_to_test:
            await test_endpoint(api, method_name, description)
            # Petite pause entre les tests
            await asyncio.sleep(0.5)
        
        # # Test 4: Endpoints bruts
        # await test_raw_endpoints(api)
        
        # Test 5: Cache
        _LOGGER.info("🧪 Test du cache...")
        api.clear_cache()
        await test_endpoint(api, "get_meters_info", "Informations des compteurs (après clear cache)")
    
    _LOGGER.info("🎉 Test complet terminé!")
    _LOGGER.info("📁 Résultats disponibles dans: %s", DEBUG_DIR.absolute())
    
    # Résumé des fichiers créés
    json_files = list(DEBUG_DIR.glob("*.json"))
    success_files = [f for f in json_files if "SUCCESS" in f.name]
    error_files = [f for f in json_files if "ERROR" in f.name]
    
    _LOGGER.info("📊 Résumé:")
    _LOGGER.info("  - Tests réussis: %d", len(success_files))
    _LOGGER.info("  - Tests en erreur: %d", len(error_files))
    _LOGGER.info("  - Total fichiers: %d", len(json_files))


def main():
    """Point d'entrée principal."""
    try:
        asyncio.run(run_complete_test())
    except KeyboardInterrupt:
        _LOGGER.info("🛑 Test interrompu par l'utilisateur")
    except Exception as e:
        _LOGGER.error("💥 Erreur fatale: %s", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
