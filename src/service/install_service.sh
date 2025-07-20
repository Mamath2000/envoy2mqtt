#!/bin/bash

# Script pour installer le service systemd envoy2mqtt

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/envoy2mqtt.service"
SYSTEMD_DIR="/etc/systemd/system"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Installation du service systemd envoy2mqtt${NC}"

# Vérifier que nous sommes root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Ce script doit être exécuté en tant que root (sudo)${NC}"
    exit 1
fi

# Vérifier que le fichier service existe
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}Fichier service non trouvé: $SERVICE_FILE${NC}"
    exit 1
fi

# Modifier le fichier service pour l'utilisateur actuel
REAL_USER=$(who am i | awk '{print $1}')
REAL_HOME=$(eval echo ~$REAL_USER)

echo -e "${YELLOW}Configuration pour l'utilisateur: $REAL_USER${NC}"
echo -e "${YELLOW}Répertoire home: $REAL_HOME${NC}"

# Créer un fichier service temporaire avec les bons chemins
TMP_SERVICE="/tmp/envoy2mqtt.service"
sed -e "s|User=pi|User=$REAL_USER|g" \
    -e "s|Group=pi|Group=$REAL_USER|g" \
    -e "s|{WorkingDirectory}|$SCRIPT_DIR|g" \
    "$SERVICE_FILE" > "$TMP_SERVICE"

# Copier le fichier service
echo -e "${YELLOW}Installation du fichier service...${NC}"
cp "$TMP_SERVICE" "$SYSTEMD_DIR/envoy2mqtt.service"
rm "$TMP_SERVICE"

# Recharger systemd
echo -e "${YELLOW}Rechargement de systemd...${NC}"
systemctl daemon-reload

# Activer le service
echo -e "${YELLOW}Activation du service...${NC}"
systemctl enable envoy2mqtt.service

echo -e "${GREEN}✅ Service installé avec succès!${NC}"
echo
echo "Commandes utiles:"
echo "  sudo systemctl start envoy2mqtt     # Démarrer le service"
echo "  sudo systemctl stop envoy2mqtt      # Arrêter le service"
echo "  sudo systemctl status envoy2mqtt    # Voir le statut"
echo "  sudo journalctl -u envoy2mqtt -f    # Voir les logs en temps réel"
echo "  sudo systemctl disable envoy2mqtt   # Désactiver le service"
echo
echo -e "${YELLOW}Pour démarrer maintenant: sudo systemctl start envoy2mqtt${NC}"
