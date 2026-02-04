import pygame
import os

# --- FENÊTRE ET RÉSOLUTION ---
# La taille réelle de la fenêtre sur ton écran
WIN_W, WIN_H = 1280, 720 
# Le jeu est dessiné sur une surface plus petite puis agrandi (donne un style Pixel Art)
INTERNAL_RES = (800, 600) 
FPS = 60 # Images par seconde (la fluidité)

# --- PHYSIQUE DU JOUEUR ---
GRAVITY = 0.8       # Force qui tire vers le bas à chaque image
JUMP_SMALL = -12    # Puissance du saut (Négatif car en maths Pygame, le haut est vers 0)
MOVE_SPEED = 5      # Vitesse de marche
DASH_SPEED = 22     # Vitesse pendant une ruée (dash)
DASH_DURATION = 12  # Combien de frames dure le dash
DASH_COOLDOWN = 50  # Temps d'attente avant de pouvoir re-dasher
CLIMB_SPEED = 4     # Vitesse pour monter aux murs

# --- BOSS ---
BOSS_ATK_SPEED = 10  # Vitesse d'animation en attaque (plus petit = plus rapide)
BOSS_IDLE_SPEED = 30 # Vitesse d'animation quand il attend

# --- GAMEPLAY ET COULEURS ---
ATTACK_SIZE_PX = 200 # Taille de l'impact de l'attaque plante
# Définition de couleurs (Rouge, Vert, Bleu) pour éviter de taper des chiffres partout
WHITE, BLACK, RED, GREEN, GOLD, BLUE_DASH = (255,255,255), (0,0,0), (200,0,0), (0,200,0), (255,215,0), (0,150,255)
DEBUG_BG = (0, 0, 0, 150) # Fond noir transparent pour le menu F3

# --- CHEMINS DES DOSSIERS (ASSETS) ---
ASSETS_DIR = "assets"
# os.path.join permet de créer un chemin compatible Windows/Mac/Linux
BOSS_DIR = os.path.join(ASSETS_DIR, "boss", "test")
ATTACK_DIR = os.path.join(ASSETS_DIR, "attaque")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")

# Création d'une liste contenant les 16 noms d'images pour l'attaque
PLANT_ATTACK_FRAMES = [os.path.join(ATTACK_DIR, f"frame_{i:02d}_delay-0.1s.png") for i in range(16)]

# --- FONCTION POUR CHARGER UNE IMAGE ---
def load_img(path, scale):
    try:
        # Charge l'image et gère la transparence (alpha)
        img = pygame.image.load(path).convert_alpha()
        # Redimensionne l'image selon le multiplicateur 'scale'
        return pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
    except:
        # Si l'image n'est pas trouvée, on crée un carré rose pour éviter que le jeu plante
        s = pygame.Surface((64, 64)); s.fill((255, 0, 50)); return s