@echo off
REM Script d'installation pour Windows - Authentification Envoy S
REM Utilise un environnement virtuel Python

setlocal EnableDelayedExpansion

echo === Installation de l'authentification Envoy S ===

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python depuis https://python.org
    pause
    exit /b 1
)

echo [INFO] Version Python detectee:
python --version

REM Définir les variables
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv
set CONFIG_FILE=%SCRIPT_DIR%config.py

echo [INFO] Repertoire du projet: %SCRIPT_DIR%

REM Créer l'environnement virtuel s'il n'existe pas
if not exist "%VENV_DIR%" (
    echo [INFO] Creation de l'environnement virtuel...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERREUR] Échec de la création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo [SUCCESS] Environnement virtuel créé
) else (
    echo [WARNING] L'environnement virtuel existe déjà
)

REM Activer l'environnement virtuel
echo [INFO] Activation de l'environnement virtuel...
call "%VENV_DIR%\Scripts\activate.bat"

REM Mettre à jour pip
echo [INFO] Mise à jour de pip...
python -m pip install --upgrade pip

REM Installer les dépendances
echo [INFO] Installation des dépendances...
if exist "%SCRIPT_DIR%requirements.txt" (
    pip install -r "%SCRIPT_DIR%requirements.txt"
    echo [SUCCESS] Dépendances installées avec succès
) else (
    echo [WARNING] Fichier requirements.txt non trouvé, installation manuelle...
    pip install requests urllib3
)

REM Créer le fichier de configuration s'il n'existe pas
if not exist "%CONFIG_FILE%" (
    echo [INFO] Création du fichier de configuration...
    copy "%SCRIPT_DIR%config_example.py" "%CONFIG_FILE%"
    echo [SUCCESS] Fichier de configuration créé: %CONFIG_FILE%
    echo [WARNING] Veuillez éditer %CONFIG_FILE% avec vos informations
) else (
    echo [INFO] Le fichier de configuration existe déjà
)

REM Créer le script de lancement Windows
set LAUNCHER_SCRIPT=%SCRIPT_DIR%run_envoy_auth.bat
(
echo @echo off
echo REM Script de lancement pour l'authentification Envoy - Windows
echo setlocal
echo.
echo set SCRIPT_DIR=%%~dp0
echo set VENV_DIR=%%SCRIPT_DIR%%venv
echo.
echo REM Vérifier que l'environnement virtuel existe
echo if not exist "%%VENV_DIR%%" ^(
echo     echo Erreur: Environnement virtuel non trouvé. Exécutez d'abord install.bat
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Activer l'environnement virtuel
echo call "%%VENV_DIR%%\Scripts\activate.bat"
echo.
echo REM Vérifier que le fichier de configuration existe
echo if not exist "%%SCRIPT_DIR%%config.py" ^(
echo     echo Erreur: Fichier config.py non trouvé. Copiez et configurez config_example.py
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Lancer le script selon l'argument
echo if "%%1"=="auth" ^(
echo     echo Lancement du test d'authentification...
echo     python "%%SCRIPT_DIR%%envoy_auth.py"
echo ^) else if "%%1"=="demo" ^(
echo     echo Lancement de la démonstration...
echo     python "%%SCRIPT_DIR%%example_usage.py"
echo ^) else if "%%1"=="monitor" ^(
echo     echo Lancement de la surveillance continue...
echo     python -c "from example_usage import continuous_monitoring; continuous_monitoring()"
echo ^) else ^(
echo     echo Usage: %%0 {auth^|demo^|monitor}
echo     echo   auth    - Test d'authentification simple
echo     echo   demo    - Démonstration avec récupération de données
echo     echo   monitor - Surveillance continue
echo     pause
echo     exit /b 1
echo ^)
echo.
echo pause
) > "%LAUNCHER_SCRIPT%"

echo [SUCCESS] Script de lancement créé: %LAUNCHER_SCRIPT%

REM Créer le script de désinstallation Windows
set UNINSTALL_SCRIPT=%SCRIPT_DIR%uninstall.bat
(
echo @echo off
echo REM Script de désinstallation pour l'authentification Envoy - Windows
echo.
echo set SCRIPT_DIR=%%~dp0
echo set VENV_DIR=%%SCRIPT_DIR%%venv
echo.
echo echo Désinstallation de l'environnement virtuel...
echo.
echo if exist "%%VENV_DIR%%" ^(
echo     rmdir /s /q "%%VENV_DIR%%"
echo     echo Environnement virtuel supprimé
echo ^) else ^(
echo     echo Aucun environnement virtuel trouvé
echo ^)
echo.
echo REM Demander si on supprime le fichier de configuration
echo if exist "%%SCRIPT_DIR%%config.py" ^(
echo     set /p choice="Supprimer le fichier de configuration config.py ? (y/N): "
echo     if /i "!choice!"=="y" ^(
echo         del "%%SCRIPT_DIR%%config.py"
echo         echo Fichier de configuration supprimé
echo     ^)
echo ^)
echo.
echo echo Désinstallation terminée
echo pause
) > "%UNINSTALL_SCRIPT%"

echo [SUCCESS] Script de désinstallation créé: %UNINSTALL_SCRIPT%

REM Afficher les instructions finales
echo.
echo [SUCCESS] === Installation terminée avec succès ! ===
echo.
echo [INFO] Prochaines étapes:
echo 1. Éditez le fichier de configuration:
echo    notepad %CONFIG_FILE%
echo.
echo 2. Remplissez vos informations:
echo    - USERNAME: votre email Enphase
echo    - PASSWORD: votre mot de passe
echo    - SERIAL_NUMBER: numéro de série de votre Envoy
echo    - LOCAL_ENVOY_URL: IP de votre Envoy (ex: https://192.168.1.100)
echo.
echo 3. Testez l'authentification:
echo    run_envoy_auth.bat auth
echo.
echo 4. Ou lancez la démonstration complète:
echo    run_envoy_auth.bat demo
echo.
echo 5. Pour la surveillance continue:
echo    run_envoy_auth.bat monitor
echo.
echo [INFO] Fichiers créés:
echo   - %VENV_DIR% (environnement virtuel)
echo   - %CONFIG_FILE% (configuration)
echo   - %LAUNCHER_SCRIPT% (script de lancement)
echo   - %UNINSTALL_SCRIPT% (désinstallation)
echo.
echo [WARNING] N'oubliez pas de configurer vos identifiants dans config.py !
echo.
pause
