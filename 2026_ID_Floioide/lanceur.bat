@echo off
echo ===========================
echo   Lanceur Floioide
echo ===========================
echo.

:: Verification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH.
    pause
    exit /b 1
)

:: Creation ou verification du .venv
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

:: Activation du .venv et installation des dependances
echo [INFO] Installation des dependances ...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERREUR] Echec de l'installation des dependances.
    pause
    exit /b 1
)
echo [OK] Dependances installees.

:: Lancement du jeu
echo.
echo [INFO] Lancement de Floioide ...
echo.
python main.py

pause
