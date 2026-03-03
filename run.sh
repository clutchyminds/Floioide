#!/bin/bash

VENV_DIR="/home/obooklage/PythonVirtualEnvs/floioide"
PROJECT_DIR="$(dirname "$0")/2026_ID_Floioide"

if [ ! -d "$VENV_DIR" ]; then
    echo "Création du venv floioide..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
fi

cd "$PROJECT_DIR" && "$VENV_DIR/bin/python" main.py
