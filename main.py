import pygame
import pytmx
from pygame.locals import *

# Initialisation de Pygame
pygame.init()

# Constantes
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5

# Couleurs
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)

# Initialisation de l'écran
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platformer TMX")
clock = pygame.time.Clock()


class Player(pygame.sprite.Sprite):
    """Classe du personnage joueur"""
    
    def __init__(self, x, y):
        super().__init__()
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
        """Met à jour la position et gère les collisions"""
        
        # Application de la gravité
        self.velocity_y += GRAVITY
        
        # Gestion des entrées clavier
        keys = pygame.key.get_pressed()
        self.velocity_x = 0
        
        if keys[K_LEFT] or keys[K_q]:
            self.velocity_x = -MOVE_SPEED
        if keys[K_RIGHT] or keys[K_d]:
            self.velocity_x = MOVE_SPEED
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            self.velocity_y = JUMP_STRENGTH
            self.on_ground = False
        
        # Déplacement horizontal
        self.rect.x += self.velocity_x
        self.check_collisions_x(collision_tiles)
        
        # Déplacement vertical
        self.rect.y += self.velocity_y
        self.check_collisions_y(collision_tiles)
    
    def check_collisions_x(self, collision_tiles):
        """Vérifie les collisions horizontales"""
        for tile in collision_tiles:
            if self.rect.colliderect(tile):
                if self.velocity_x > 0:  # Collision à droite
                    self.rect.right = tile.left
                elif self.velocity_x < 0:  # Collision à gauche
                    self.rect.left = tile.right
    
    def check_collisions_y(self, collision_tiles):
        """Vérifie les collisions verticales"""
        self.on_ground = False
        for tile in collision_tiles:
            if self.rect.colliderect(tile):
                if self.velocity_y > 0:  # Collision en bas
                    self.rect.bottom = tile.top
                    self.velocity_y = 0
                    self.on_ground = True
                elif self.velocity_y < 0:  # Collision en haut
                    self.rect.top = tile.bottom
                    self.velocity_y = 0
    
    def draw(self, screen, camera_x, camera_y):
        """Dessine le joueur avec offset de caméra"""
        screen.blit(self.image, (self.rect.x - camera_x, self.rect.y - camera_y))


class Camera:
    """Classe pour gérer la caméra qui suit le joueur"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
    
    def update(self, target):
        """Centre la caméra sur le joueur"""
        self.x = target.rect.centerx - SCREEN_WIDTH // 2
        self.y = target.rect.centery - SCREEN_HEIGHT // 2
        
        # Limiter la caméra aux bords de la carte
        self.x = max(0, min(self.x, self.width - SCREEN_WIDTH))
        self.y = max(0, min(self.y, self.height - SCREEN_HEIGHT))


class TiledMap:
    """Classe pour gérer la carte TMX"""
    
    def __init__(self, filename):
        self.tmx_data = pytmx.load_pygame(filename)
        self.width = self.tmx_data.width * self.tmx_data.tilewidth
        self.height = self.tmx_data.height * self.tmx_data.tileheight
        
        # Récupération des calques
        self.base_layer = None
        self.hitbox_layer = None
        
        for layer in self.tmx_data.visible_layers:
            if layer.name.lower() == "hit-box":
                self.hitbox_layer = layer
            elif layer.name.lower() == "base":
                self.base_layer = layer
        
        # Extraction des tiles de collision
        self.collision_tiles = self.get_collision_tiles()
    
    def get_collision_tiles(self):
        """Récupère tous les rectangles de collision du calque hit-box"""
        collision_rects = []
        
        if self.hitbox_layer:
            for x, y, gid in self.hitbox_layer:
                if gid:
                    tile_x = x * self.tmx_data.tilewidth
                    tile_y = y * self.tmx_data.tileheight
                    rect = pygame.Rect(
                        tile_x,
                        tile_y,
                        self.tmx_data.tilewidth,
                        self.tmx_data.tileheight
                    )
                    collision_rects.append(rect)
        
        return collision_rects
    
    def draw_layer(self, screen, layer_name, camera_x, camera_y):
        """Dessine un calque spécifique avec offset de caméra"""
        for layer in self.tmx_data.visible_layers:
            if layer.name.lower() == layer_name.lower():
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        if gid:
                            tile = self.tmx_data.get_tile_image_by_gid(gid)
                            if tile:
                                screen.blit(
                                    tile,
                                    (x * self.tmx_data.tilewidth - camera_x,
                                     y * self.tmx_data.tileheight - camera_y)
                                )


def main():
    """Fonction principale du jeu"""
    
    # Charger la carte TMX (remplace par ton fichier)
    try:
        tiled_map = TiledMap("assets/maps/map.tmx")
    except Exception as e:
        print(f"❌ Erreur de chargement de la carte: {e}")
        print("📝 Assure-toi que 'map.tmx' existe dans le même dossier")
        return
    
    # Créer le joueur
    player = Player(100, 100)
    
    # Créer la caméra
    camera = Camera(tiled_map.width, tiled_map.height)
    
    # Boucle principale
    running = True
    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
        
        # Mise à jour
        player.update(tiled_map.collision_tiles)
        camera.update(player)
        
        # Affichage
        screen.fill(WHITE)
        
        # 1. Dessiner le calque hit-box (collisions)
        tiled_map.draw_layer(screen, "hit-box", camera.x, camera.y)
        
        # 2. Dessiner le calque base (décors)
        tiled_map.draw_layer(screen, "base", camera.x, camera.y)
        
        # 3. Dessiner le joueur
        player.draw(screen, camera.x, camera.y)
        
        # Afficher les FPS (optionnel)
        fps_text = pygame.font.Font(None, 30).render(
            f"FPS: {int(clock.get_fps())}", True, (0, 0, 0)
        )
        screen.blit(fps_text, (10, 10))
        # Création de la police (idéalement à faire une seule fois avant la boucle while pour optimiser)
        font = pygame.font.Font(None, 30)
        
        # Récupération des coordonnées (pixels)
        px, py = player.rect.x, player.rect.y
        
        # Calcul des coordonnées en "Tuiles" (Case de la grille)
        # Utile pour savoir sur quelle case de Tiled on se trouve
        # On divise la position par la taille des tuiles (32x32 par défaut souvent)
        tile_x = px // tiled_map.tmx_data.tilewidth
        tile_y = py // tiled_map.tmx_data.tileheight

        # Création du texte complet
        # Format : FPS | Pixel X, Y | Tuile Col, Row
        debug_text = f"FPS: {int(clock.get_fps())}  |  Pos: {px}, {py}  |  Tuile: [{tile_x}, {tile_y}]"
        
        # Rendu et affichage
        text_surface = font.render(debug_text, True, (0, 0, 0)) # Noir
        
        # On ajoute un fond blanc semi-transparent pour que ce soit lisible sur le décor
        bg_rect = text_surface.get_rect(topleft=(10, 10))
        pygame.draw.rect(screen, (255, 255, 255), bg_rect) # Fond blanc
        screen.blit(text_surface, (10, 10))

        pygame.display.flip()
        clock.tick(FPS)
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()


if __name__ == "__main__":
    main()