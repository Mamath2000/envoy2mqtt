#!/usr/bin/env python3
"""
Script de test rapide pour vérifier la configuration
"""

def test_configuration():
    """Test de la configuration et des dépendances"""
    
    print("=== Test de Configuration Envoy ===\n")
    
    # Test 1: Vérifier l'importation des modules
    print("1. Test des dépendances...")
    try:
        import requests
        import json
        import time
        print("   ✅ Modules Python importés avec succès")
    except ImportError as e:
        print(f"   ❌ Erreur d'import: {e}")
        return False
    
    # Test 2: Vérifier la configuration
    print("\n2. Test du fichier de configuration...")
    try:
        import config
        required_fields = ['USERNAME', 'PASSWORD', 'SERIAL_NUMBER', 'LOCAL_ENVOY_URL']
        
        for field in required_fields:
            value = getattr(config, field, None)
            if not value or value.startswith('votre-'):
                print(f"   ❌ Champ '{field}' non configuré")
                return False
            else:
                # Masquer les informations sensibles
                if field in ['PASSWORD']:
                    display_value = "***"
                elif field in ['USERNAME']:
                    display_value = value[:3] + "***@" + value.split('@')[-1] if '@' in value else "***"
                else:
                    display_value = value
                print(f"   ✅ {field}: {display_value}")
                
        print("   ✅ Configuration valide")
    except ImportError:
        print("   ❌ Fichier config.py non trouvé")
        print("      Copiez config_example.py vers config.py et configurez-le")
        return False
    except AttributeError as e:
        print(f"   ❌ Configuration incomplète: {e}")
        return False
    
    # Test 3: Vérifier la connectivité réseau
    print("\n3. Test de connectivité réseau...")
    try:
        import requests
        
        # Test connexion aux serveurs Enphase
        print("   Test connexion enlighten.enphaseenergy.com...")
        response = requests.get("https://enlighten.enphaseenergy.com", timeout=10)
        if response.status_code < 400:
            print("   ✅ Serveurs Enphase accessibles")
        else:
            print("   ⚠️  Serveurs Enphase non accessibles (peut être normal)")
            
        # Test connexion Envoy local
        print(f"   Test connexion {config.LOCAL_ENVOY_URL}...")
        try:
            response = requests.get(config.LOCAL_ENVOY_URL, timeout=5, verify=False)
            print("   ✅ Envoy local accessible")
        except:
            print("   ⚠️  Envoy local non accessible (vérifiez l'IP)")
            
    except Exception as e:
        print(f"   ⚠️  Erreur de connectivité: {e}")
    
    # Test 4: Test d'authentification basique
    print("\n4. Test d'authentification...")
    try:
        from envoy_auth import EnvoyAuth
        
        auth = EnvoyAuth(
            username=config.USERNAME,
            password=config.PASSWORD,
            serial_number=config.SERIAL_NUMBER,
            local_envoy_url=config.LOCAL_ENVOY_URL
        )
        
        print("   ✅ Classe EnvoyAuth initialisée")
        print("   💡 Pour tester l'authentification complète, utilisez:")
        print("      make auth   ou   ./run.sh auth")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'initialisation: {e}")
        return False
    
    print("\n=== Test de Configuration Terminé ===")
    print("✅ Configuration prête pour l'utilisation")
    return True


if __name__ == "__main__":
    test_configuration()
