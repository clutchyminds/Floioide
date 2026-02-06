# Projet : Floioide
# Auteurs : Laure Ducourneau, Victor Dauphin, Corentin Gelineau, Thomas Lewis

import os

#dimentions et titre de la fenetre 
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Floïoïde - L'éveil de la fleur"

#physique du joueur
GRAVITY = 0.5
PLAYER_JUMP_SPEED = 12
PLAYER_MOVEMENT_SPEED = 5
DASH_SPEED = 15
DASH_DURATION = 0.2 # en secondes

#mécanique avec l'eau et les pétales 
MAX_WATER = 100
WATER_LOSS_DRY_SOIL = 0.1  # Perte sur métal/roche
WATER_GAIN_GRASS = 0.05    # Gain sur herbe
MAX_PETALS = 5

#chemins (avec os pour fonctionnement sur tt les)
#j'utilise os.path.join
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(BASE_PATH, "..", "data")