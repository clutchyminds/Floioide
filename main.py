import pygame
import pytmx
import math
import os
from pygame.locals import *

# =================================================================
# CONFIGURATION GÉNÉRALE
# =================================================================
pygame.init()
WIN_W, WIN_H = 1280, 720
INTERNAL_RES = (800, 600)
screen = pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | HWSURFACE)
render_surface = pygame.Surface(INTERNAL_RES)

FPS = 60
GRAVITY = 0.8
JUMP_SMALL, JUMP_BIG = -5, -15
MOVE_SPEED = 5
DASH_SPEED, DASH_DURATION, DASH_COOLDOWN = 20, 10, 300
CLIMB_SPEED = 4 

clock = pygame.time.Clock()
font_hud = pygame.font.Font(None, 22)
font_menu = pygame.font.Font(None, 60)
font_small = pygame.font.Font(None, 30)

# --- CHEMINS DES ASSETS ---
ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_DIR = os.path.join(ASSETS_DIR, "boss", "test")

def load_and_scale(path, scale_factor):
    """Charge une image et la redimensionne proprement."""
    try:
        img = pygame.image.load(path).convert_alpha()
        w, h = img.get_size()
        return pygame.transform.scale(img, (int(w * scale_factor), int(h * scale_factor)))
    except:
        surf = pygame.Surface((64 * scale_factor, 64 * scale_factor))
        surf.fill((255, 0, 50)) # Rouge si fichier manquant
        return surf

# =================================================================
# CLASSE BOSS
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp = 20
        self.active = True
        scale = 3
        
        # Chargement Attaque : attaque00.png à attaque32.png
        self.anim_attack = [load_and_scale(os.path.join(BOSS_DIR, f"attaque{i:02d}.png"), scale) for i in range(33)]
        
        # Chargement Pause : pause1.png et pause2.png répétés 10 fois
        p1 = load_and_scale(os.path.join(BOSS_DIR, "pause1.png"), scale)
        p2 = load_and_scale(os.path.join(BOSS_DIR, "pause2.png"), scale)
        self.anim_pause = [p1, p2] * 10 

        self.current_anim = self.anim_attack
        self.is_attacking = True
        self.frame_index = 0
        self.image = self.current_anim[0]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))
        
        self.vel_y = 0
        self.anim_timer = 0
        self.hit_shake = 0

    def take_damage(self):
        self.hp -= 1
        self.hit_shake = 10 # Effet de tremblement

    def update(self, collision_tiles):
        if not self.active or self.hp <= 0: return

        # Rythme : 0.25s (15 frames) en attaque / 0.75s (45 frames) en pause
        anim_speed = 15 if self.is_attacking else 45

        self.anim_timer += 1
        if self.anim_timer >= anim_speed:
            self.anim_timer = 0
            self.frame_index += 1
            
            if self.frame_index >= len(self.current_anim):
                self.frame_index = 0
                self.is_attacking = not self.is_attacking
                self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            
            self.image = self.current_anim[self.frame_index]

        # Gravité simple
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: self.rect.bottom = t.top; self.vel_y = 0

    def draw(self, surface, cam_x, cam_y):
        if self.active and self.hp > 0:
            draw_x = self.rect.x - cam_x
            if self.hit_shake > 0:
                draw_x += math.sin(pygame.time.get_ticks() * 0.5) * 5
                self.hit_shake -= 1
            
            surface.blit(self.image, (draw_x, self.rect.y - cam_y))
            # Barre de vie
            pygame.draw.rect(surface, (50, 0, 0), (draw_x, self.rect.y - cam_y - 20, 100, 8))
            pygame.draw.rect(surface, (0, 255, 120), (draw_x, self.rect.y - cam_y - 20, self.hp * 5, 8))

# =================================================================
# CLASSE JOUEUR
# =================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_and_scale(PLAYER_IMG, 1)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x, self.vel_y = 0, 0
        self.on_ground = False
        self.is_on_wall = False
        self.facing_right = True
        self.dash_cooldown = 0
        self.dash_timer = 0
        self.is_attacking = False
        self.attack_duration = 0
        self.attack_rect = pygame.Rect(0, 0, 60, 60)

    def update(self, collision_tiles, jump_tiles, boss):
        keys = pygame.key.get_pressed()
        
        # --- ATTAQUE ---
        if (keys[K_x] or keys[K_c]) and self.attack_duration <= 0:
            self.is_attacking = True
            self.attack_duration = 20 # Durée de la hitbox
            if self.facing_right: self.attack_rect.midleft = self.rect.midright
            else: self.attack_rect.midright = self.rect.midleft
            
            if boss.active and self.attack_rect.colliderect(boss.rect):
                boss.take_damage()

        if self.attack_duration > 0:
            self.attack_duration -= 1
            if self.attack_duration <= 0: self.is_attacking = False

        # --- MOUVEMENTS & DASH ---
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if keys[K_a] and self.dash_cooldown == 0:
            self.dash_timer, self.dash_cooldown = DASH_DURATION, DASH_COOLDOWN

        if self.is_on_wall and not self.on_ground:
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]: self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]: self.vel_y = CLIMB_SPEED
        else: self.vel_y += GRAVITY

        if self.dash_timer > 0:
            self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            self.vel_y, self.dash_timer = 0, self.dash_timer - 1
        else:
            self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
            if self.vel_x > 0: self.facing_right = True
            elif self.vel_x < 0: self.facing_right = False

        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            can_jump_big = any(self.rect.colliderect(jt) for jt in jump_tiles)
            self.vel_y = JUMP_BIG if can_jump_big else JUMP_SMALL
            self.on_ground = False

        # --- COLLISIONS ---
        self.is_on_wall = False
        wall_check = self.rect.inflate(4, 0)
        if not self.on_ground:
            for t in collision_tiles:
                if wall_check.colliderect(t): self.is_on_wall = True; break

        self.rect.x += self.vel_x
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_x > 0: self.rect.right = t.left
                else: self.rect.left = t.right
        
        self.rect.y += self.vel_y
        self.on_ground = False
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: self.rect.bottom = t.top; self.vel_y, self.on_ground = 0, True
                else: self.rect.top = t.bottom; self.vel_y = 0

    def draw(self, surface, cam_x, cam_y):
        surface.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
        if self.is_attacking:
            pygame.draw.rect(surface, (255, 255, 255), (self.attack_rect.x - cam_x, self.attack_rect.y - cam_y, 60, 60), 2)

# =================================================================
# SYSTÈME DE MENU
# =================================================================
def show_pause_menu():
    paused = True
    selected = 0
    options = ["REPRENDRE", "AIDE ET REGLES", "QUITTER"]
    overlay = pygame.Surface(INTERNAL_RES, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))

    while paused:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: paused = False
                if event.key == K_UP: selected = (selected - 1) % len(options)
                if event.key == K_DOWN: selected = (selected + 1) % len(options)
                if event.key == K_RETURN:
                    if selected == 0: paused = False
                    if selected == 1: pass # Aide
                    if selected == 2: pygame.quit(); exit()

        render_surface.blit(overlay, (0,0))
        for i, opt in enumerate(options):
            color = (0, 255, 200) if i == selected else (255, 255, 255)
            prefix = "> " if i == selected else "  "
            txt = font_small.render(prefix + opt, True, color)
            render_surface.blit(txt, (INTERNAL_RES[0]//2 - 100, 240 + i * 50))
        
        screen.blit(pygame.transform.scale(render_surface, (WIN_W, WIN_H)), (0,0))
        pygame.display.flip()
        clock.tick(30)

# =================================================================
# BOUCLE PRINCIPALE
# =================================================================
def main():
    try:
        tmx_data = pytmx.load_pygame(MAP_FILE)
    except:
        print("Erreur : Fichier TMX introuvable."); return

    player = Player(100, 100)
    boss = Boss(30, 20, 32) # Coordonnées tuiles (30, 20)
    
    collision_tiles = []
    jump_tiles = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid:
                    r = pygame.Rect(x*32, y*32, 32, 32)
                    if layer.name == "hit-box": collision_tiles.append(r)
                    if layer.name == "saut-activé": jump_tiles.append(r)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE: show_pause_menu()

        # Update
        player.update(collision_tiles, jump_tiles, boss)
        boss.update(collision_tiles)
        
        # Caméra
        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width * 32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height * 32 - 600))

        # Dessin
        render_surface.fill((25, 25, 30))
        
        # Rendu Map (Culling)
        start_x, end_x = int(cam_x // 32), int((cam_x + 800) // 32) + 1
        start_y, end_y = int(cam_y // 32), int((cam_y + 600) // 32) + 1
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x in range(start_x, end_x):
                    for y in range(start_y, end_y):
                        if 0 <= x < tmx_data.width and 0 <= y < tmx_data.height:
                            gid = layer.data[y][x]
                            if gid:
                                img = tmx_data.get_tile_image_by_gid(gid)
                                if img: render_surface.blit(img, (x*32 - cam_x, y*32 - cam_y))

        boss.draw(render_surface, cam_x, cam_y)
        player.draw(render_surface, cam_x, cam_y)

        # HUD (Haut à droite)
        stats = [f"FPS: {int(clock.get_fps())}", 
                 f"TUILE: {player.rect.x//32}, {player.rect.y//32}", 
                 f"BOSS HP: {boss.hp}"]
        for i, s in enumerate(stats):
            txt = font_hud.render(s, True, (0, 255, 180))
            render_surface.blit(txt, (INTERNAL_RES[0] - txt.get_width() - 15, 15 + i * 20))

        # Affichage Final
        screen.blit(pygame.transform.scale(render_surface, (WIN_W, WIN_H)), (0,0))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()