@echo off
echo Lancement de Floioide...

:: On cree le venv s'il existe pas encore
if not exist ".venv" (
    echo Creation du venv !
    python -m venv .venv
)

:: On active le venv et on installe les modules
call .venv\Scripts\activate.bat
pip install -r requirements.txt

:: On lance le jeu
python main.py
pause
