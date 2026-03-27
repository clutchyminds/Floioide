import os

#configuration de la fenetre
LARGEUR = 1280
HAUTEUR = 720
TITRE = "FLOIOIDE"

#chemins des fichiers pa rapport à ce fichier
# On remonte d'un niveau pour sortir de 'sources' et trouver 'data'
CHEMIN_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(CHEMIN_BASE, "data")
DOSSIER_MAPS = os.path.join(DOSSIER_DATA, "maps")
DOSSIER_ATTAQUES = os.path.join(DOSSIER_DATA, "player", "attaque")
DOSSIER_BOSS = os.path.join(DOSSIER_DATA, "boss")

#reglages du joueur
VITESSE_MARCHE = 5
VITESSE_DASH = 60
VITESSE_SAUT = 12
VITESSE_TIR = 448
DISTANCE_MAX_TIR = 256

#des ennemis
DISTANCE_DETECTION = 320 # 5 tuiles de 64px
VITESSE_MOB = 2
MAX_MOBS_SOL = 5
MAX_MOBS_AIR = 5

#du monde
TAILLE_TUILE = 64
GRAVITE = 0.5