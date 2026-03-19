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
dossier_attaques = os.path.join(DOSSIER_DATA, "player", "attaque")

# --- RÉGLAGES DU JOUEUR ---
VITESSE_MARCHE = 30
VITESSE_DASH = 20
VITESSE_SAUT = 12
VITESSE_TIR = 10
DISTANCE_MAX_TIR = 256

# --- ENNEMIS ---
DISTANCE_DETECTION = 320 # 5 tuiles de 64px
VITESSE_MOB = 2
GRAVITE = 0.5