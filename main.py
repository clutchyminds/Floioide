import pygame
import pytmx
import math
import random
from pygame.locals import *

# --- CONFIGURATION ---
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -14
MOVE_SPEED = 5
CLIMB_SPEED = 4 # Vitesse quand on grimpe au mur
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# =================================================================
# PROJECTILES (PÉTALES)
# =================================================================
class Petal(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 182, 193), (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        self.speed = 12
        self.vx = (dx / dist * self.speed) if dist != 0 else 0
        self.vy = (dy / dist * self.speed) if dist != 0 else 0

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

# =================================================================
# BOSS : DÉPLACEMENT + SUIVI
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.tile_size = tile_size
        self.hp = 10
        self.active = False
        self.states_anims = {}
        try:
            for i in range(1, 5):
                self.states_anims[f"attack_{i}"] = pygame.image.load(f"assets/boss/attack{i}.png").convert_alpha()
                self.states_anims[f"pause_{i}"] = pygame.image.load(f"assets/boss/pause{i}.png").convert_alpha()
        except:
            for i in range(1, 5):
                s = pygame.Surface((64, 64)); s.fill((200, 0, 0)); self.states_anims[f"attack_{i}"] = s
                p = pygame.Surface((64, 64)); p.fill((0, 0, 200)); self.states_anims[f"pause_{i}"] = p

        self.current_state = "attack_1"
        self.image = self.states_anims[self.current_state]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))
        self.state_timer = 0
        self.duration = 5 * FPS 
        self.is_paused = False
        self.speed = 2

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0: self.active = False

    def update(self, player_rect):
        if not self.active or self.hp <= 0: return
        self.state_timer += 1
        if self.state_timer >= self.duration:
            self.state_timer = 0
            self.is_paused = not self.is_paused
            rand_num = random.randint(1, 4)
            mode = "pause" if self.is_paused else "attack"
            self.current_state = f"{mode}_{rand_num}"
            self.image = self.states_anims[self.current_state]

        dx = player_rect.x - self.rect.x
        dy = player_rect.y - self.rect.y
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
# JOUEUR : AVEC CAPACITÉ DE GRIMPER (WALL CLIMB)
# =================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try: self.image = pygame.image.load("assets/player/player.png").convert_alpha()
        except: self.image = pygame.Surface((32, 48)); self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x, self.vel_y = 0, 0
        self.on_ground = False
        self.is_on_wall = False # Est-ce qu'on touche un mur ?

    def update(self, tiles):
        keys = pygame.key.get_pressed()
        
        # --- PHYSIQUE NORMALE OU GRIMPE ---
        if self.is_on_wall and not self.on_ground:
            # On annule la gravité si on grimpe
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]:
                self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]:
                self.vel_y = CLIMB_SPEED
        else:
            self.vel_y += GRAVITY

        # Mouvement horizontal
        self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
        
        # Saut
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.on_ground = False

        # --- COLLISIONS & DÉTECTION MUR ---
        self.is_on_wall = False # Reset à chaque frame
        
        # Déplacement X
        self.rect.x += self.vel_x
        for t in tiles:
            if self.rect.colliderect(t):
                # Si on touche un mur en étant en l'air, on active la grimpe
                if not self.on_ground:
                    self.is_on_wall = True
                
                if self.vel_x > 0: self.rect.right = t.left
                if self.vel_x < 0: self.rect.left = t.right
        
        # Déplacement Y
        self.rect.y += self.vel_y
        self.on_ground = False
        for t in tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: 
                    self.rect.bottom = t.top
                    self.vel_y = 0
                    self.on_ground = True
                if self.vel_y < 0: 
                    self.rect.top = t.bottom
                    self.vel_y = 0

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
    map_data = TiledMap("assets/maps/map.tmx")
    player = Player(100, 100)
    boss = Boss(29, 93, map_data.tile_size)
    
    collision_tiles = map_data.get_layer_rects("hit-box")
    boss_triggers = map_data.get_layer_rects("boss-test")
    
    petals = []
    font = pygame.font.Font(None, 26)
    cam_x, cam_y = 0, 0

    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); return
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mx, my = pygame.mouse.get_pos()
                petals.append(Petal(player.rect.centerx, player.rect.centery, mx + cam_x, my + cam_y))

        player.update(collision_tiles)
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
        px, py = player.rect.x, player.rect.y
        tx, ty = px // map_data.tile_size, py // map_data.tile_size
        climb_txt = " | GRIMPE!" if player.is_on_wall else ""
        debug_str = f"FPS: {int(clock.get_fps())} | Pos: {px},{py} | Tuile: [{tx},{ty}]{climb_txt}"
        debug_surf = font.render(debug_str, True, (0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (10, 10, debug_surf.get_width() + 10, 25))
        screen.blit(debug_surf, (15, 13))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()