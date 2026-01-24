import pygame
import pytmx
import math
import random
import os
from pygame.locals import *

# --- CONFIGURATION ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.8
JUMP_SMALL = -5      # Petit saut par défaut
JUMP_BIG = -15        # Saut puissant sur le calque
MOVE_SPEED = 5
DASH_SPEED = 20
DASH_DURATION = 10
DASH_COOLDOWN = 300
CLIMB_SPEED = 4 

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Gestion os
ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")

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
# BOSS
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.tile_size = tile_size
        self.hp = 10
        self.active = False
        self.states_anims = {}
        boss_path = os.path.join(ASSETS_DIR, "boss")
        try:
            for i in range(1, 5):
                self.states_anims[f"attack_{i}"] = pygame.image.load(os.path.join(boss_path, f"attack{i}.png")).convert_alpha()
                self.states_anims[f"pause_{i}"] = pygame.image.load(os.path.join(boss_path, f"pause{i}.png")).convert_alpha()
        except:
            for i in range(1, 5):
                s = pygame.Surface((64, 64)); s.fill((200, 0, 0)); self.states_anims[f"attack_{i}"] = s
                p = pygame.Surface((64, 64)); p.fill((0, 0, 200)); self.states_anims[f"pause_{i}"] = p

        self.current_state = "attack_1"
        self.image = self.states_anims[self.current_state]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))
        self.state_timer, self.duration = 0, 5 * FPS 
        self.is_paused, self.speed = False, 2

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.active = False

    def update(self, player_rect):
        if not self.active or self.hp <= 0: return
        self.state_timer += 1
        if self.state_timer >= self.duration:
            self.state_timer, self.is_paused = 0, not self.is_paused
            self.current_state = f"{'pause' if self.is_paused else 'attack'}_{random.randint(1,4)}"
            self.image = self.states_anims[self.current_state]

        dx, dy = player_rect.x - self.rect.x, player_rect.y - self.rect.y
        dist = math.hypot(dx, dy)
        if dist > 150:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed
        elif dist < 100:
            self.rect.x -= (dx / dist) * self.speed
            self.rect.y -= (dy / dist) * self.speed

    def draw(self, screen, cam_x, cam_y):
        if self.active and self.hp > 0:
            screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
            pygame.draw.rect(screen, (255,0,0), (self.rect.x - cam_x, self.rect.y - cam_y - 10, self.hp * 6, 5))

# =================================================================
# JOUEUR
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
        
        # 1. Dash logic
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if keys[K_a] and self.dash_cooldown == 0:
            self.dash_timer, self.dash_cooldown = DASH_DURATION, DASH_COOLDOWN

        # 2. Physique : Grimpe ou Gravité
        if self.is_on_wall and not self.on_ground:
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]: self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]: self.vel_y = CLIMB_SPEED
        else:
            self.vel_y += GRAVITY

        # Mouvement ou Dash
        if self.dash_timer > 0:
            self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            self.vel_y = 0
            self.dash_timer -= 1
        else:
            self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
            if self.vel_x > 0: self.facing_right = True
            elif self.vel_x < 0: self.facing_right = False

        # 3. Saut dynamique
        self.can_jump_big = any(self.rect.colliderect(jt) for jt in jump_tiles)
        
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            # Si sur le calque -> gros saut, sinon -> petit saut
            self.vel_y = JUMP_BIG if self.can_jump_big else JUMP_SMALL
            self.on_ground = False

        # 4. Collisions améliorées pour la grimpe
        self.is_on_wall = False
        
        # Détection murale préventive (on regarde 2 pixels à gauche et à droite)
        wall_check_rect = self.rect.inflate(4, 0) 
        if not self.on_ground:
            for t in collision_tiles:
                if wall_check_rect.colliderect(t):
                    self.is_on_wall = True
                    break

        self.rect.x += self.vel_x
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_x > 0: self.rect.right = t.left
                if self.vel_x < 0: self.rect.left = t.right
        
        self.rect.y += self.vel_y
        self.on_ground = False
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: 
                    self.rect.bottom = t.top
                    self.vel_y, self.on_ground = 0, True
                if self.vel_y < 0: 
                    self.rect.top = t.bottom
                    self.vel_y = 0

class TiledMap:
    def __init__(self, path):
        self.data = pytmx.load_pygame(path)
        self.tile_size = self.data.tilewidth
        self.width, self.height = self.data.width * self.tile_size, self.data.height * self.tile_size

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
    boss_triggers = map_data.get_layer_rects("boss-test")
    jump_enabled_tiles = map_data.get_layer_rects("saut-activé")
    
    petals, cam_x, cam_y = [], 0, 0
    font = pygame.font.Font(None, 26)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); return
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mx, my = pygame.mouse.get_pos()
                petals.append(Petal(player.rect.centerx, player.rect.centery, mx + cam_x, my + cam_y))

        player.update(collision_tiles, jump_enabled_tiles)
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
                    if img: screen.blit(img, (x*map_data.tile_size - cam_x, y*map_data.tile_size - cam_y))

        for p in petals: screen.blit(p.image, (p.rect.x - cam_x, p.rect.y - cam_y))
        boss.draw(screen, cam_x, cam_y)
        screen.blit(player.image, (player.rect.x - cam_x, player.rect.y - cam_y))

        # HUD
        tx, ty = player.rect.x // map_data.tile_size, player.rect.y // map_data.tile_size
        dash_txt = "PRET" if player.dash_cooldown == 0 else f"{player.dash_cooldown // 60}s"
        jump_txt = "BOOST" if player.can_jump_big else "PETIT"
        climb_txt = " | GRIMPE!" if player.is_on_wall else ""
        
        debug_str = f"Saut: {jump_txt} | Dash: {dash_txt} | Tuile: [{tx},{ty}]{climb_txt}"
        debug_surf = font.render(debug_str, True, (0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (10, 10, debug_surf.get_width() + 10, 25))
        screen.blit(debug_surf, (15, 13))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()