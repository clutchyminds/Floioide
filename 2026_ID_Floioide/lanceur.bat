@echo off
echo ****************************
echo   Jeu Floioide Windows
echo Avec environnement virtuel
echo ****************************

:: Vérification si Python est bien installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
)

:: Check si l'environnement virtual est présent.
:: Le crée s'il n'est pas encore
if not exist ".venv" (
    echo [INFO] Creation de l'environnement virtuel .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de creer le .venv.
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel cree.
) else (
    echo [OK] Environnement virtuel .venv deja present.
)

:: Utilisation de l'enviromment virtuel
:: Installe les dépendances si ce n'est pas fait.
echo [INFO] Installation des dependances ...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des dependances.
    pause
    exit /b 1
)
echo [OK] Dependances installees.

:: On  lance le jeu
echo.
echo [INFO] Lancement de Floioide ...
echo.
python main.py

:: On attend une touche du clavier pour quitter le programme.
pause
