import pygame
import os

# Fenêtre et Résolution
WIN_W, WIN_H = 1280, 720
INTERNAL_RES = (800, 600)
FPS = 60

# Physique Joueur
GRAVITY = 0.8
JUMP_SMALL = -12
MOVE_SPEED = 5
DASH_SPEED = 22
DASH_DURATION = 12
DASH_COOLDOWN = 50
CLIMB_SPEED = 4

# Boss
BOSS_ATK_SPEED = 10
BOSS_IDLE_SPEED = 30

# Gameplay
ATTACK_SIZE_PX = 200
WHITE, BLACK, RED, GREEN, GOLD, BLUE_DASH = (255,255,255), (0,0,0), (200,0,0), (0,200,0), (255,215,0), (0,150,255)
DEBUG_BG = (0, 0, 0, 150)

# Chemins
ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_DIR = os.path.join(ASSETS_DIR, "boss", "test")
ATTACK_DIR = os.path.join(ASSETS_DIR, "attaque")

PLANT_ATTACK_FRAMES = [os.path.join(ATTACK_DIR, f"frame_{i:02d}_delay-0.1s.png") for i in range(16)]

def load_img(path, scale):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
    except:
        s = pygame.Surface((64, 64)); s.fill((255, 0, 50)); return s