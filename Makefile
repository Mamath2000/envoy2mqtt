# Envoy2MQTT - Makefile
.PHONY: help install run service-install service-start service-stop service-status service-logs service-remove clean

help:
	@echo "🌞 Envoy2MQTT - Passerelle Enphase vers MQTT"
	@echo ""
	@echo "⚡ COMMANDES PRINCIPALES:"
	@echo "  make install        - Installer les dépendances"
	@echo "  make run            - Lancer envoy2mqtt (mode interactif)"
	@echo "  make test           - Tester l'API Envoy (debug)"
	@echo "  make diagnostic     - Diagnostic complet (réponses brutes)"
	@echo ""
	@echo "🔧 SERVICE SYSTEMD:"
	@echo "  make service-install - Installer le service systemd"
	@echo "  make service-start   - Démarrer le service"
	@echo "  make service-stop    - Arrêter le service"
	@echo "  make service-status  - Voir le statut du service"
	@echo "  make service-logs    - Voir les logs en temps réel"
	@echo "  make service-remove  - Désinstaller le service"

install:
	@echo "🔧 Installation des dépendances..."
	@if [ ! -d venv ]; then python3 -m venv venv; fi
	@venv/bin/pip install --upgrade pip
	@venv/bin/pip install -r requirements.txt
	@echo "✅ Installation terminée!"

run:
	@if [ ! -f src/config/config.py ]; then echo "❌ Fichier config.py manquant!"; exit 1; fi
	@echo "🚀 Lancement d'envoy2mqtt..."
	PYTHONPATH=. venv/bin/python src/main.py


service-install:
	@echo "🔧 Installation du service systemd..."
	@sudo ./src/service/install_service.sh

service-start:
	@sudo systemctl start envoy2mqtt
	@echo "✅ Service démarré!"

service-stop:
	@sudo systemctl stop envoy2mqtt
	@echo "✅ Service arrêté!"

service-status:
	@sudo systemctl status envoy2mqtt

service-logs:
	@sudo journalctl -u envoy2mqtt -f

service-remove:
	@sudo systemctl stop envoy2mqtt 2>/dev/null || true
	@sudo systemctl disable envoy2mqtt 2>/dev/null || true
	@sudo rm -f /etc/systemd/system/envoy2mqtt.service
	@sudo systemctl daemon-reload
	@echo "✅ Service désinstallé!"

clean:
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Nettoyage terminé!"

test:
	@echo "🧪 Test de l'API Envoy..."
	PYTHONPATH=. venv/bin/python tests/test_envoy_api.py

diagnostic:
	@echo "🔍 Diagnostic complet Envoy (réponses brutes)..."
	PYTHONPATH=. venv/bin/python src/utils/diagnostic_envoy.py

