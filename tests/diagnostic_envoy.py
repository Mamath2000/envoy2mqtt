#!/usr/bin/env python3
"""
Script de diagnostic pour l'API Envoy
Teste tous les endpoints et sauvegarde les réponses brutes (même HTML)
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from pathlib import Path

import config
from envoy_auth import EnvoyAuth

class EnvoyDiagnostic:
    """Diagnostic complet de l'API Envoy."""
    
    def __init__(self):
        self.envoy_host = config.LOCAL_ENVOY_URL
        self.serial_number = config.SERIAL_NUMBER
        self.username = config.USERNAME
        self.password = config.PASSWORD
        self.session = None
        self.auth_token = None
        
        # Créer le répertoire de diagnostic
        self.debug_dir = Path("debug_raw")
        self.debug_dir.mkdir(exist_ok=True)
        
        # Endpoints à tester
        self.endpoints = [
            "/ivp/meters",
            "/ivp/meters/readings",
            "/ivp/meters/reports/consumption",
            "/ivp/meters/reports/production",
            "/production",
            "/production.json",
            "/api/v1/production",
            "/api/v1/production/inverters",
            "/inventory",
            "/info",
            "/home",
            "/home.json"
        ]
    
    async def authenticate(self):
        """Authentifier avec l'Envoy."""
        print("🔐 Authentification...")
        auth = EnvoyAuth()
        success = await asyncio.to_thread(auth.authenticate)
        
        if success:
            self.auth_token = auth.token
            print(f"✅ Authentification réussie")
            return True
        else:
            print("❌ Échec de l'authentification")
            return False
    
    async def test_endpoint_raw(self, endpoint: str):
        """Tester un endpoint et sauvegarder la réponse brute."""
        url = f"{self.envoy_host}{endpoint}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        headers = {
            "User-Agent": "Envoy2MQTT-Diagnostic"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        try:
            async with self.session.get(
                url,
                headers=headers,
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                content_type = response.headers.get('content-type', 'unknown')
                status = response.status
                
                # Lire la réponse brute
                if 'application/json' in content_type:
                    try:
                        data = await response.json()
                        content = json.dumps(data, indent=2)
                        file_ext = "json"
                    except:
                        content = await response.text()
                        file_ext = "txt"
                else:
                    content = await response.text()
                    file_ext = "html" if 'text/html' in content_type else "txt"
                
                # Nom de fichier sécurisé
                endpoint_safe = endpoint.replace("/", "_").replace("?", "_")
                filename = f"{timestamp}_{status}_{endpoint_safe}.{file_ext}"
                filepath = self.debug_dir / filename
                
                # Sauvegarder
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Créer aussi un fichier de métadonnées
                meta_data = {
                    "endpoint": endpoint,
                    "url": url,
                    "status": status,
                    "content_type": content_type,
                    "headers": dict(response.headers),
                    "timestamp": timestamp,
                    "content_length": len(content)
                }
                
                meta_filename = f"{timestamp}_{status}_{endpoint_safe}_meta.json"
                meta_filepath = self.debug_dir / meta_filename
                
                with open(meta_filepath, 'w', encoding='utf-8') as f:
                    json.dump(meta_data, f, indent=2)
                
                print(f"📄 {endpoint} -> {status} ({content_type}) -> {filename}")
                return True
                
        except Exception as e:
            # Sauvegarder l'erreur
            error_data = {
                "endpoint": endpoint,
                "url": url,
                "error": str(e),
                "timestamp": timestamp
            }
            
            endpoint_safe = endpoint.replace("/", "_").replace("?", "_")
            error_filename = f"{timestamp}_ERROR_{endpoint_safe}.json"
            error_filepath = self.debug_dir / error_filename
            
            with open(error_filepath, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2)
            
            print(f"❌ {endpoint} -> ERREUR: {str(e)}")
            return False
    
    async def run_diagnostic(self):
        """Exécuter le diagnostic complet."""
        print("🚀 Démarrage du diagnostic Envoy")
        print(f"📂 Résultats dans: {self.debug_dir}")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Authentifier
            if not await self.authenticate():
                return
            
            print(f"\n🔍 Test de {len(self.endpoints)} endpoints...")
            
            success_count = 0
            for i, endpoint in enumerate(self.endpoints, 1):
                print(f"[{i:2d}/{len(self.endpoints)}] ", end="")
                if await self.test_endpoint_raw(endpoint):
                    success_count += 1
                
                # Petite pause entre les requêtes
                await asyncio.sleep(0.5)
            
            print(f"\n✅ Diagnostic terminé: {success_count}/{len(self.endpoints)} endpoints réussis")
            print(f"📂 Résultats dans: {self.debug_dir.absolute()}")

async def main():
    diagnostic = EnvoyDiagnostic()
    await diagnostic.run_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())
