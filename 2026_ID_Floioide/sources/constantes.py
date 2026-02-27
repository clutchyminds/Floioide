import os

# Reglages de la fenetre
LARGEUR = 1280
HAUTEUR = 720
TITRE = "FLOIOIDE"

# Gestion des chemins
# On remonte de un niveau depuis sources pour arriver a la racine du projet
CHEMIN_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(CHEMIN_BASE, "data")
DOSSIER_MAPS = os.path.join(DOSSIER_DATA, "maps")

# Couleurs pour le HUD
COULEUR_VIE = (255, 0, 0)
COULEUR_EAU = (0, 0, 255)
COULEUR_FOND_BARRE = (50, 50, 50)