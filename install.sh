#!/bin/bash

# Script d'installation pour l'authentification Envoy S
# Utilise un environnement virtuel Python pour isoler les dépendances

set -e  # Arrêter le script en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
CONFIG_FILE="$SCRIPT_DIR/config.py"

print_info "=== Installation de l'authentification Envoy S ==="
print_info "Répertoire du projet: $SCRIPT_DIR"

# Vérifier que Python 3 est installé
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1-2)
print_info "Version Python détectée: $PYTHON_VERSION"

# Vérifier que pip est disponible
if ! python3 -m pip --version &> /dev/null; then
    print_error "pip n'est pas disponible. Veuillez installer python3-pip."
    exit 1
fi

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "$VENV_DIR" ]; then
    print_info "Création de l'environnement virtuel..."
    python3 -m venv "$VENV_DIR"
    print_success "Environnement virtuel créé dans: $VENV_DIR"
else
    print_warning "L'environnement virtuel existe déjà"
fi

# Activer l'environnement virtuel
print_info "Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"

# Mettre à jour pip dans l'environnement virtuel
print_info "Mise à jour de pip..."
python -m pip install --upgrade pip

# Installer les dépendances
print_info "Installation des dépendances..."
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    pip install -r "$SCRIPT_DIR/requirements.txt"
    print_success "Dépendances installées avec succès"
else
    print_warning "Fichier requirements.txt non trouvé, installation manuelle..."
    pip install requests urllib3
fi

# Créer le fichier de configuration s'il n'existe pas
if [ ! -f "$CONFIG_FILE" ]; then
    print_info "Création du fichier de configuration..."
    cp "$SCRIPT_DIR/config_example.py" "$CONFIG_FILE"
    print_success "Fichier de configuration créé: $CONFIG_FILE"
    print_warning "Veuillez éditer $CONFIG_FILE avec vos informations avant d'utiliser le script"
else
    print_info "Le fichier de configuration existe déjà: $CONFIG_FILE"
fi

# Créer un script de lancement facile
LAUNCHER_SCRIPT="$SCRIPT_DIR/run.sh"
cat > "$LAUNCHER_SCRIPT" << 'EOF'
#!/bin/bash

# Script de lancement pour l'authentification Envoy
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Vérifier que l'environnement virtuel existe
if [ ! -d "$VENV_DIR" ]; then
    echo "Erreur: Environnement virtuel non trouvé. Exécutez d'abord ./install.sh"
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
EOF

chmod +x "$LAUNCHER_SCRIPT"
print_success "Script de lancement créé: $LAUNCHER_SCRIPT"

# Créer un script de désinstallation
UNINSTALL_SCRIPT="$SCRIPT_DIR/uninstall.sh"
cat > "$UNINSTALL_SCRIPT" << 'EOF'
#!/bin/bash

# Script de désinstallation pour l'authentification Envoy

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "Désinstallation de l'environnement virtuel..."

if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
    echo "Environnement virtuel supprimé"
else
    echo "Aucun environnement virtuel trouvé"
fi

# Supprimer les scripts générés
if [ -f "$SCRIPT_DIR/run.sh" ]; then
    rm "$SCRIPT_DIR/run.sh"
    echo "Script de lancement supprimé"
fi

# Demander si on supprime le fichier de configuration
if [ -f "$SCRIPT_DIR/config.py" ]; then
    read -p "Supprimer le fichier de configuration config.py ? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm "$SCRIPT_DIR/config.py"
        echo "Fichier de configuration supprimé"
    fi
fi

echo "Désinstallation terminée"
EOF

chmod +x "$UNINSTALL_SCRIPT"
print_success "Script de désinstallation créé: $UNINSTALL_SCRIPT"

# Afficher les instructions finales
echo
print_success "=== Installation terminée avec succès ! ==="
echo
print_info "Prochaines étapes:"
echo "1. Éditez le fichier de configuration:"
echo "   nano $CONFIG_FILE"
echo
echo "2. Testez d'abord la configuration:"
echo "   ./run.sh test"
echo
echo "3. Puis testez l'authentification:"
echo "   ./run.sh auth"
echo
echo "4. Ou lancez la démonstration complète:"
echo "   ./run.sh demo"
echo
echo "5. Pour la surveillance continue:"
echo "   ./run.sh monitor"
echo
print_info "Fichiers créés:"
echo "  - $VENV_DIR (environnement virtuel)"
echo "  - $CONFIG_FILE (configuration)"
echo "  - $LAUNCHER_SCRIPT (script de lancement)"
echo "  - $UNINSTALL_SCRIPT (désinstallation)"
echo
print_warning "N'oubliez pas de configurer vos identifiants dans config.py !"
