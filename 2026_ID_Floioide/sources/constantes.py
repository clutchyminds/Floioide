import os

LARGEUR = 1280
HAUTEUR = 720
TITRE = "FLOIOIDE"

CHEMIN_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(CHEMIN_BASE, "data")
DOSSIER_MAPS = os.path.join(DOSSIER_DATA, "maps")

# nouvelles constantes pour le joueur
VITESSE_MARCHE = 5
VITESSE_DASH = 12
VITESSE_SAUT = 12
VITESSE_TIR = 10
DISTANCE_MAX_TIR = 256 # 4 blocs de 64 pixels environ