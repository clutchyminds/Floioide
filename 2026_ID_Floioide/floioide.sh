#!/bin/bash

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Création du venv floioide..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip
fi

"$VENV_DIR/bin/pip" install -r "requirements.txt"
"$VENV_DIR/bin/python" main.py
