# Makefile pour l'authentification Envoy S
# Facilite l'utilisation du projet

.PHONY: help install test auth demo monitor clean uninstall config

# Variables
VENV_DIR = venv
CONFIG_FILE = config.py
CONFIG_EXAMPLE = config_example.py

# Commande par défaut
help:
	@echo "🚀 Authentification Envoy S - Commandes disponibles:"
	@echo
	@echo "  make install   - Installer le projet (crée l'environnement virtuel)"
	@echo "  make config    - Ouvrir le fichier de configuration"
	@echo "  make test      - Tester la configuration"
	@echo "  make auth      - Tester l'authentification"
	@echo "  make demo      - Démonstration complète"
	@echo "  make monitor   - Surveillance continue"
	@echo "  make clean     - Nettoyer les fichiers temporaires"
	@echo "  make uninstall - Désinstaller complètement"
	@echo
	@echo "📝 Workflow typique:"
	@echo "  1. make install"
	@echo "  2. make config"
	@echo "  3. make test"
	@echo "  4. make auth ou make monitor"

# Installation
install:
	@echo "🔧 Installation de l'environnement..."
	./install.sh

# Configuration
config:
	@if [ ! -f $(CONFIG_FILE) ]; then \
		echo "📝 Création du fichier de configuration..."; \
		cp $(CONFIG_EXAMPLE) $(CONFIG_FILE); \
	fi
	@echo "📝 Ouverture du fichier de configuration..."
	@nano $(CONFIG_FILE) || vi $(CONFIG_FILE) || echo "Éditez manuellement $(CONFIG_FILE)"

# Test de configuration
test:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "❌ Environnement virtuel non trouvé. Lancez 'make install' d'abord."; \
		exit 1; \
	fi
	@echo "🧪 Test de la configuration..."
	@./run.sh test

# Test d'authentification
auth:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "❌ Environnement virtuel non trouvé. Lancez 'make install' d'abord."; \
		exit 1; \
	fi
	@echo "🔐 Test d'authentification..."
	@./run.sh auth

# Démonstration
demo:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "❌ Environnement virtuel non trouvé. Lancez 'make install' d'abord."; \
		exit 1; \
	fi
	@echo "🎯 Démonstration complète..."
	@./run.sh demo

# Surveillance continue
monitor:
	@if [ ! -d $(VENV_DIR) ]; then \
		echo "❌ Environnement virtuel non trouvé. Lancez 'make install' d'abord."; \
		exit 1; \
	fi
	@echo "📊 Surveillance continue (Ctrl+C pour arrêter)..."
	@./run.sh monitor

# Nettoyage
clean:
	@echo "🧹 Nettoyage des fichiers temporaires..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "*.pyo" -delete 2>/dev/null || true
	@find . -name "*.log" -delete 2>/dev/null || true
	@echo "✅ Nettoyage terminé"

# Désinstallation complète
uninstall:
	@echo "🗑️  Désinstallation..."
	@if [ -f uninstall.sh ]; then \
		./uninstall.sh; \
	else \
		echo "Script de désinstallation non trouvé"; \
	fi
