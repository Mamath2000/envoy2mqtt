#!/bin/bash

# Script de lancement pour l'authentification Envoy
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Vérifier que l'environnement virtuel existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Erreur: Environnement virtuel non trouvé. Exécutez d'abord install.sh"
    exit 1
fi

# Activer l'environnement virtuel
source "$VENV_DIR/bin/activate"

# Vérifier que le fichier de configuration existe
if [ ! -f "$SCRIPT_DIR/config.py" ]; then
    echo "Erreur: Fichier config.py non trouvé. Copiez et configurez config_example.py"
    exit 1
fi

# Lancer le script selon l'argument
case "$1" in
    "auth")
        echo "Lancement du test d'authentification..."
        python "$SCRIPT_DIR/envoy_auth.py"
        ;;
    "demo")
        echo "Lancement de la démonstration..."
        python "$SCRIPT_DIR/example_usage.py"
        ;;
    "monitor")
        echo "Lancement de la surveillance continue..."
        python -c "
from example_usage import continuous_monitoring
continuous_monitoring()
"
        ;;
    "test")
        echo "Test de la configuration..."
        python "$SCRIPT_DIR/test_config.py"
        ;;
    *)
        echo "Usage: $0 {auth|demo|monitor|test}"
        echo "  test    - Test de la configuration"
        echo "  auth    - Test d'authentification simple"
        echo "  demo    - Démonstration avec récupération de données"
        echo "  monitor - Surveillance continue"
        exit 1
        ;;
esac
