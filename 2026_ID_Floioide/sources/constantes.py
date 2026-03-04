import os

# --- CONFIGURATION FENÊTRE ---
LARGEUR = 1280
HAUTEUR = 720
TITRE = "FLOIOIDE"

# --- CHEMINS DES FICHIERS (Calculés par rapport à ce fichier) ---
# On remonte d'un niveau pour sortir de 'sources' et trouver 'data'
CHEMIN_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(CHEMIN_BASE, "data")
DOSSIER_MAPS = os.path.join(DOSSIER_DATA, "maps")

# --- RÉGLAGES DU JOUEUR ---
VITESSE_MARCHE = 5
VITESSE_DASH = 12
VITESSE_SAUT = 12
VITESSE_TIR = 10
DISTANCE_MAX_TIR = 256