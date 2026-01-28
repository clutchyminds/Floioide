import pygame
import pytmx
import math
import random
import os
from PIL import Image, ImageSequence
from pygame.locals import *

# --- CONFIGURATION ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.8
JUMP_SMALL = -5      # Saut de base
JUMP_BIG = -15       # Saut sur calque "saut-activé"
MOVE_SPEED = 5
DASH_SPEED = 20
DASH_DURATION = 10
DASH_COOLDOWN = 300  # 5 secondes
CLIMB_SPEED = 4 

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# --- GESTION DES CHEMINS (OS) ---
ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_GIF_DIR = os.path.join(ASSETS_DIR, "boss", "test")

# =================================================================
# UTILITAIRE : CHARGEMENT ET REDIMENSIONNEMENT DU GIF
# =================================================================
def load_gif(filename, scale_factor=2):
    """Découpe un GIF et l'agrandit pour Pygame"""
    try:
        pil_image = Image.open(filename)
        frames = []
        for frame in ImageSequence.Iterator(pil_image):
            frame = frame.convert('RGBA')
            pygame_surface = pygame.image.fromstring(
                frame.tobytes(), frame.size, frame.mode
            ).convert_alpha()
            
            # Redimensionnement
            w, h = pygame_surface.get_size()
            pygame_surface = pygame.transform.scale(pygame_surface, (w * scale_factor, h * scale_factor))
            frames.append(pygame_surface)
        return frames
    except Exception as e:
        print(f"Erreur GIF {filename}: {e}")
        surf = pygame.Surface((128, 128)); surf.fill((255, 0, 0))
        return [surf]

# =================================================================
# PROJECTILES (PÉTALES)
# =================================================================
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
        self.rect.x += self.vx
        self.rect.y += self.vy

# =================================================================
# BOSS : AGRANDI, STATIQUE, GRAVITÉ
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp = 10
        self.active = False
        
        # GIFs agrandis x2
        self.anim_pause = load_gif(os.path.join(BOSS_GIF_DIR, "pause.gif"), 2)
        self.anim_attack = load_gif(os.path.join(BOSS_GIF_DIR, "attaque.gif"), 2)

        self.current_anim = self.anim_pause
        self.frame_index = 0
        self.image = self.current_anim[0]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))

        self.vel_y = 0
        self.state_timer = 0
        self.is_attacking = False

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.active = False

    def update(self, collision_tiles):
        if not self.active or self.hp <= 0: return

        # Cycle : Pause 5s (300 f) / Attaque 3s (180 f)
        self.state_timer += 1
        limit = 180 if self.is_attacking else 300
        
        if self.state_timer >= limit:
            self.state_timer = 0
            self.is_attacking = not self.is_attacking
            self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            self.frame_index = 0

        # Animation GIF
        if pygame.time.get_ticks() % 6 == 0:
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            self.image = self.current_anim[self.frame_index]

        # Physique : Gravité + Collisions (Statique horizontalement)
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0:
                    self.rect.bottom = t.top
                    self.vel_y = 0

    def draw(self, screen, cam_x, cam_y):
        if self.active and self.hp > 0:
            screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
            pygame.draw.rect(screen, (255,0,0), (self.rect.x - cam_x, self.rect.y - cam_y - 20, self.hp * 10, 8))

# =================================================================
# JOUEUR : DASH, GRIMPE, SAUT DYNAMIQUE
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
        
        # Dash Cooldown
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if keys[K_a] and self.dash_cooldown == 0:
            self.dash_timer, self.dash_cooldown = DASH_DURATION, DASH_COOLDOWN

        # Physique : Grimpe vs Gravité
        if self.is_on_wall and not self.on_ground:
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]: self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]: self.vel_y = CLIMB_SPEED
        else:
            self.vel_y += GRAVITY

        # Mouvement ou Dash
        if self.dash_timer > 0:
            self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            self.vel_y = 0; self.dash_timer -= 1
        else:
            self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
            if self.vel_x > 0: self.facing_right = True
            elif self.vel_x < 0: self.facing_right = False

        # Saut dynamique (Petit vs Gros)
        self.can_jump_big = any(self.rect.colliderect(jt) for jt in jump_tiles)
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            self.vel_y = JUMP_BIG if self.can_jump_big else JUMP_SMALL
            self.on_ground = False

        # Détection Murale & Collisions
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

# =================================================================
# CARTE ET SYSTÈME DE JEU
# =================================================================
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

def main():
    map_data = TiledMap(MAP_FILE)
    player = Player(100, 100)
    boss = Boss(29, 93, map_data.tile_size)
    
    collision_tiles = map_data.get_layer_rects("hit-box")
    jump_tiles = map_data.get_layer_rects("saut-activé")
    boss_triggers = map_data.get_layer_rects("boss-test")
    
    petals, cam_x, cam_y = [], 0, 0
    font = pygame.font.Font(None, 24)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); return
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mx, my = pygame.mouse.get_pos()
                petals.append(Petal(player.rect.centerx, player.rect.centery, mx + cam_x, my + cam_y))

        # Updates
        player.update(collision_tiles, jump_tiles)
        cam_x = max(0, min(player.rect.centerx - 400, map_data.width - 800))
        cam_y = max(0, min(player.rect.centery - 300, map_data.height - 600))

        for trigger in boss_triggers:
            if player.rect.colliderect(trigger): boss.active = True

        boss.update(collision_tiles)

        for p in petals[:]:
            p.update()
            if boss.active and p.rect.colliderect(boss.rect):
                boss.take_damage(1); petals.remove(p); continue
            if math.hypot(p.rect.x - player.rect.x, p.rect.y - player.rect.y) > 1000: petals.remove(p)

        # Dessin
        screen.fill((200, 200, 200))
        for layer in map_data.data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    img = map_data.data.get_tile_image_by_gid(gid)
                    if img: screen.blit(img, (x*32 - cam_x, y*32 - cam_y))

        for p in petals: screen.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
        boss.draw(screen, cam_x, cam_y)
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y - cam_y))

        # HUD
        tx, ty = player.rect.x // 32, player.rect.y // 32
        dash_txt = "DASH PRET" if player.dash_cooldown == 0 else f"DASH: {player.dash_cooldown//60}s"
        debug_surf = font.render(f"Saut: {'BOOST' if player.can_jump_big else 'NORMAL'} | {dash_txt} | Tuile: [{int(tx)},{int(ty)}]", True, (0,0,0))
        screen.blit(debug_surf, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()