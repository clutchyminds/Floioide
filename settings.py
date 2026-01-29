import pygame
import os

# Fenêtre
WIN_W, WIN_H = 1280, 720
INTERNAL_RES = (800, 600)
FPS = 60

# Physique
GRAVITY = 0.8
JUMP_SMALL, JUMP_BIG = -5, -15
MOVE_SPEED = 5
DASH_SPEED, DASH_DURATION, DASH_COOLDOWN = 20, 10, 300
CLIMB_SPEED = 4

# Dossiers
ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_DIR = os.path.join(ASSETS_DIR, "boss", "test")