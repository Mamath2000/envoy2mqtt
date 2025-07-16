#!/usr/bin/env python3
"""
Affiche un résumé des fichiers du projet Envoy Auth
"""

import os
import sys

def show_project_summary():
    """Affiche un résumé du projet"""
    
    print("=== Projet Authentification Envoy S ===\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    files_info = {
        'install.sh': 'Script d\'installation automatique',
        'Makefile': 'Commandes simplifiées (make help)',
        'run.sh': 'Script de lancement principal',
        'envoy_auth.py': 'Classe principale d\'authentification',
        'example_usage.py': 'Exemples d\'utilisation et client Envoy',
        'test_config.py': 'Script de test de configuration',
        'config_example.py': 'Fichier de configuration d\'exemple',
        'config.py': 'Fichier de configuration (à créer)',
        'requirements.txt': 'Dépendances Python',
        'README.md': 'Documentation complète',
        'venv/': 'Environnement virtuel Python (créé après installation)',
        'uninstall.sh': 'Script de désinstallation (créé après installation)'
    }
    
    print("📁 Fichiers du projet:")
    print("-" * 60)
    
    for filename, description in files_info.items():
        filepath = os.path.join(script_dir, filename)
        
        if os.path.exists(filepath):
            status = "✅"
            size_info = ""
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                if size > 1024:
                    size_info = f" ({size//1024}KB)"
                else:
                    size_info = f" ({size}B)"
        else:
            status = "❌" if filename in ['config.py'] else "⏳"
            size_info = ""
        
        print(f"{status} {filename:<20} {description}{size_info}")
    
    print("\n" + "=" * 60)
    
    # Vérifier l'état de l'installation
    config_exists = os.path.exists(os.path.join(script_dir, 'config.py'))
    venv_exists = os.path.exists(os.path.join(script_dir, 'venv'))
    launcher_exists = os.path.exists(os.path.join(script_dir, 'run.sh'))
    
    if not venv_exists and not launcher_exists:
        print("🚀 Pour commencer:")
        print("   Option 1: make install && make config && make test")
        print("   Option 2: ./install.sh puis ./run.sh")
    elif not config_exists:
        print("⚠️  Installation détectée mais configuration manquante:")
        print("   1. make config (ou: cp config_example.py config.py)")
        print("   2. Éditez config.py avec vos identifiants")
        print("   3. make test")
    else:
        print("✅ Installation complète détectée!")
        print("   • make test     (ou: ./run.sh test)")
        print("   • make auth     (ou: ./run.sh auth)")
        print("   • make monitor  (ou: ./run.sh monitor)")
        print("   • make help     (voir toutes les commandes)")
    
    print("\n💡 Tapez 'make' pour voir toutes les commandes disponibles")
    
    print("\n📖 Voir README.md pour la documentation complète")


if __name__ == "__main__":
    show_project_summary()
