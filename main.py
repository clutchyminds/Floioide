import pygame
import pytmx
import math
from pygame.locals import *

# --- INITIALISATION ---
pygame.init()

# Constantes
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -12  # Ajusté pour un saut plus naturel
MOVE_SPEED = 5

# Couleurs
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
PINK = (255, 182, 193)

# Initialisation de l'écran
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mon Jeu de Plateforme - Pétales")
clock = pygame.time.Clock()

# --- CLASSES ---

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Chargement de la texture
        try:
            self.image = pygame.image.load("assets/player/player.png").convert_alpha()
        except Exception as e:
            print(f"⚠️ Texture perso introuvable : {e}")
            self.image = pygame.Surface((32, 48))
            self.image.fill(BLUE)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Physique
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False

    def update(self, collision_tiles):
        # Gravité
        self.velocity_y += GRAVITY
        
        # Contrôles
        keys = pygame.key.get_pressed()
        self.velocity_x = 0
        if keys[K_LEFT] or keys[K_q]:
            self.velocity_x = -MOVE_SPEED
        if keys[K_RIGHT] or keys[K_d]:
            self.velocity_x = MOVE_SPEED
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            self.velocity_y = JUMP_STRENGTH
            self.on_ground = False
        
        # Déplacement X
        self.rect.x += self.velocity_x
        self.check_collisions_x(collision_tiles)
        
        # Déplacement Y
        self.rect.y += self.velocity_y
        self.check_collisions_y(collision_tiles)

    def check_collisions_x(self, collision_tiles):
        for tile in collision_tiles:
            if self.rect.colliderect(tile):
                if self.velocity_x > 0: self.rect.right = tile.left
                elif self.velocity_x < 0: self.rect.left = tile.right

    def check_collisions_y(self, collision_tiles):
        self.on_ground = False
        for tile in collision_tiles:
            if self.rect.colliderect(tile):
                if self.velocity_y > 0:
                    self.rect.bottom = tile.top
                    self.velocity_y = 0
                    self.on_ground = True
                elif self.velocity_y < 0:
                    self.rect.top = tile.bottom
                    self.velocity_y = 0

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class Petal(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, PINK, (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        
        # Calcul du vecteur de direction
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        
        self.speed = 12
        if dist != 0:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
        else:
            self.vx, self.vy = 0, 0

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

    def draw(self, screen, camera_x, camera_y):
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

    def update(self, target):
        self.x = target.rect.centerx - SCREEN_WIDTH // 2
        self.y = target.rect.centery - SCREEN_HEIGHT // 2
        # Limites de la carte
        self.x = max(0, min(self.x, self.width - SCREEN_WIDTH))
        self.y = max(0, min(self.y, self.height - SCREEN_HEIGHT))


class TiledMap:
    def __init__(self, filename):
        self.tmx_data = pytmx.load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        self.collision_tiles = self.get_collision_tiles()

    def get_collision_tiles(self):
        rects = []
        for layer in self.tmx_data.visible_layers:
            if layer.name.lower() == "hit-box":
                for x, y, gid in layer:
                    if gid:
                        rects.append(pygame.Rect(x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight,
                                               self.tmx_data.tilewidth, self.tmx_data.tileheight))
        return rects

    def draw_layer(self, screen, layer_name, camera_x, camera_y):
        for layer in self.tmx_data.visible_layers:
            if layer.name.lower() == layer_name.lower() and isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            screen.blit(tile, (x * self.tmx_data.tilewidth - camera_x, 
                                             y * self.tmx_data.tileheight - camera_y))

# --- FONCTION PRINCIPALE ---

def main():
    try:
        tiled_map = TiledMap("assets/maps/map.tmx")
    except Exception as e:
        print(f"❌ Erreur map : {e}")
        return

    player = Player(100, 100)
    camera = Camera(tiled_map.width, tiled_map.height)
    petals = []
    font = pygame.font.Font(None, 28)

    running = True
    while running:
        # 1. Événements
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            
            # Tir au clic droit (bouton 3)
            if event.type == MOUSEBUTTONDOWN and event.button == 3:
                mx, my = pygame.mouse.get_pos()
                # Conversion écran -> monde
                world_mx = mx + camera.x
                world_my = my + camera.y
                petals.append(Petal(player.rect.centerx, player.rect.centery, world_mx, world_my))

        # 2. Mise à jour
        player.update(tiled_map.collision_tiles)
        camera.update(player)
        
        for p in petals[:]:
            p.update()
            # Supprime si trop loin du joueur (distance de 1000px)
            if math.hypot(p.rect.x - player.rect.x, p.rect.y - player.rect.y) > 1000:
                petals.remove(p)

        # 3. Rendu
        screen.fill(WHITE)
        
        tiled_map.draw_layer(screen, "base", camera.x, camera.y)
        tiled_map.draw_layer(screen, "hit-box", camera.x, camera.y)
        
        for p in petals:
            p.draw(screen, camera.x, camera.y)
            
        player.draw(screen, camera.x, camera.y)

        # Debug HUD
        px, py = player.rect.x, player.rect.y
        tx, ty = px // tiled_map.tmx_data.tilewidth, py // tiled_map.tmx_data.tileheight
        debug_str = f"FPS: {int(clock.get_fps())} | Pos: {px},{py} | Tuile: {tx},{ty}"
        debug_surf = font.render(debug_str, True, (0, 0, 0))
        pygame.draw.rect(screen, (255, 255, 255), (10, 10, debug_surf.get_width() + 10, 30))
        screen.blit(debug_surf, (15, 15))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()