import pygame
import pytmx
import math
import random
import os
from PIL import Image, ImageSequence # Pour gérer les GIFs
from pygame.locals import *

# --- CONFIGURATION ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.8
JUMP_SMALL, JUMP_BIG = -5, -15
MOVE_SPEED = 5
DASH_SPEED, DASH_DURATION, DASH_COOLDOWN = 20, 10, 300
CLIMB_SPEED = 4 

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_GIF_DIR = os.path.join(ASSETS_DIR, "boss", "test")

# =================================================================
# UTILITAIRE : CHARGEMENT DE GIF ANIMÉ
# =================================================================
def load_gif(filename):
    """Découpe un GIF en liste de surfaces Pygame"""
    pil_image = Image.open(filename)
    frames = []
    for frame in ImageSequence.Iterator(pil_image):
        frame = frame.convert('RGBA')
        pygame_surface = pygame.image.fromstring(
            frame.tobytes(), frame.size, frame.mode
        ).convert_alpha()
        frames.append(pygame_surface)
    return frames

# =================================================================
# BOSS : CYCLES GIF 5s PAUSE / 3s ATTAQUE
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.tile_size = tile_size
        self.hp = 10
        self.active = False
        
        # Chargement des GIFs
        try:
            self.anim_pause = load_gif(os.path.join(BOSS_GIF_DIR, "pause.gif"))
            self.anim_attack = load_gif(os.path.join(BOSS_GIF_DIR, "attaque.gif"))
        except Exception as e:
            print(f"Erreur chargement GIF: {e}")
            # Fallback si erreur
            surf = pygame.Surface((64, 64)); surf.fill((255,0,0))
            self.anim_pause = [surf]; self.anim_attack = [surf]

        self.current_anim = self.anim_pause
        self.frame_index = 0
        self.image = self.current_anim[0]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))

        # Timers
        self.state_timer = 0
        self.is_attacking = False
        self.speed = 2

    def update(self, player_rect):
        if not self.active or self.hp <= 0: return

        # --- GESTION DU CYCLE ---
        self.state_timer += 1
        
        # Cycle : Pause (5s = 300 frames) -> Attaque (3s = 180 frames)
        limit = 180 if self.is_attacking else 300
        
        if self.state_timer >= limit:
            self.state_timer = 0
            self.is_attacking = not self.is_attacking
            self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            self.frame_index = 0 # Reset l'anim au changement d'état

        # --- ANIMATION DU GIF ---
        # On change de frame toutes les 5 frames pour que ce soit fluide
        if pygame.time.get_ticks() % 5 == 0: 
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            self.image = self.current_anim[self.frame_index]

        # --- MOUVEMENT ---
        dx, dy = player_rect.x - self.rect.x, player_rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        if dist > 120:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed

    def draw(self, screen, cam_x, cam_y):
        if self.active and self.hp > 0:
            screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
            pygame.draw.rect(screen, (255,0,0), (self.rect.x - cam_x, self.rect.y - cam_y - 10, self.hp * 6, 5))

# =================================================================
# JOUEUR (AVEC DASH, GRIMPE ET SAUT DYNAMIQUE)
# =================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try: self.image = pygame.image.load(PLAYER_IMG).convert_alpha()
        except: self.image = pygame.Surface((32, 48)); self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x, self.vel_y = 0, 0
        self.on_ground = False
        self.is_on_wall = False
        self.can_jump_big = False 
        self.dash_timer, self.dash_cooldown = 0, 0
        self.facing_right = True

    def update(self, collision_tiles, jump_tiles):
        keys = pygame.key.get_pressed()
        
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if keys[K_a] and self.dash_cooldown == 0:
            self.dash_timer, self.dash_cooldown = DASH_DURATION, DASH_COOLDOWN

        if self.is_on_wall and not self.on_ground:
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]: self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]: self.vel_y = CLIMB_SPEED
        else:
            self.vel_y += GRAVITY

        if self.dash_timer > 0:
            self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            self.vel_y = 0; self.dash_timer -= 1
        else:
            self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
            if self.vel_x > 0: self.facing_right = True
            elif self.vel_x < 0: self.facing_right = False

        self.can_jump_big = any(self.rect.colliderect(jt) for jt in jump_tiles)
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            self.vel_y = JUMP_BIG if self.can_jump_big else JUMP_SMALL
            self.on_ground = False

        # Collision & Grimpe
        self.is_on_wall = False
        wall_check = self.rect.inflate(4, 0)
        if not self.on_ground:
            for t in collision_tiles:
                if wall_check.colliderect(t): self.is_on_wall = True; break

        self.rect.x += self.vel_x
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_x > 0: self.rect.right = t.left
                if self.vel_x < 0: self.rect.left = t.right
        
        self.rect.y += self.vel_y
        self.on_ground = False
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: self.rect.bottom = t.top; self.vel_y, self.on_ground = 0, True
                if self.vel_y < 0: self.rect.top = t.bottom; self.vel_y = 0

# --- Classes Petal et TiledMap restent identiques aux précédentes ---
class Petal(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 182, 193), (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        dx, dy = target_x - x, target_y - y
        dist = math.hypot(dx, dy)
        self.speed = 12
        self.vx = (dx / dist * self.speed) if dist != 0 else 0
        self.vy = (dy / dist * self.speed) if dist != 0 else 0
    def update(self):
        self.rect.x += self.vx; self.rect.y += self.vy

class TiledMap:
    def __init__(self, path):
        self.data = pytmx.load_pygame(path)
        self.tile_size = self.data.tilewidth
        self.width = self.data.width * self.tile_size
        self.height = self.data.height * self.tile_size
    def get_layer_rects(self, name):
        rects = []
        for layer in self.data.visible_layers:
            if layer.name.lower() == name.lower():
                for x, y, gid in layer:
                    if gid: rects.append(pygame.Rect(x*self.tile_size, y*self.tile_size, self.tile_size, self.tile_size))
        return rects

# =================================================================
# MAIN
# =================================================================
def main():
    map_data = TiledMap(MAP_FILE)
    player = Player(100, 100)
    boss = Boss(29, 93, map_data.tile_size)
    
    collision_tiles = map_data.get_layer_rects("hit-box")
    jump_tiles = map_data.get_layer_rects("saut-activé")
    boss_triggers = map_data.get_layer_rects("boss-test")
    
    petals = []
    cam_x, cam_y = 0, 0

    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); return
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mx, my = pygame.mouse.get_pos()
                petals.append(Petal(player.rect.centerx, player.rect.centery, mx + cam_x, my + cam_y))

        player.update(collision_tiles, jump_tiles)
        cam_x = max(0, min(player.rect.centerx - 400, map_data.width - 800))
        cam_y = max(0, min(player.rect.centery - 300, map_data.height - 600))

        for trigger in boss_triggers:
            if player.rect.colliderect(trigger): boss.active = True

        boss.update(player.rect)

        for p in petals[:]:
            p.update()
            if boss.active and p.rect.colliderect(boss.rect):
                boss.take_damage(1); petals.remove(p); continue
            if math.hypot(p.rect.x - player.rect.x, p.rect.y - player.rect.y) > 1000: petals.remove(p)

        screen.fill((255, 255, 255))
        for layer in map_data.data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    img = map_data.data.get_tile_image_by_gid(gid)
                    if img: screen.blit(img, (x*32 - cam_x, y*32 - cam_y))

        for p in petals: screen.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
        boss.draw(screen, cam_x, cam_y)
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y - cam_y))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()