import pygame      # Bibliothèque principale pour créer des jeux
import pytmx       # Pour lire les cartes créées avec le logiciel Tiled
import math        # Pour les calculs mathématiques (comme l'arc de l'attaque)
import os          # Pour gérer les dossiers et fichiers sur l'ordinateur
from pygame.locals import * # Importe les raccourcis clavier (K_UP, K_SPACE, etc.)

# =================================================================
# CONFIGURATION GÉNÉRALE : On définit les règles du monde
# =================================================================
pygame.init()
WIN_W, WIN_H = 1280, 720          # Taille de la fenêtre visible
INTERNAL_RES = (800, 600)         # Résolution interne (plus petite pour un style rétro)
screen = pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | HWSURFACE)
render_surface = pygame.Surface(INTERNAL_RES) # Surface sur laquelle on dessine avant de l'agrandir

FPS = 60                          # Vitesse du jeu (60 images par seconde)
GRAVITY = 0.8                     # Force qui attire les personnages vers le bas
JUMP_SMALL, JUMP_BIG = -5, -15    # Puissance des sauts (normal et sur zone spéciale)
MOVE_SPEED = 5                    # Vitesse de marche
DASH_SPEED, DASH_DURATION, DASH_COOLDOWN = 20, 10, 300 # Réglages de la charge rapide
CLIMB_SPEED = 4                   # Vitesse pour grimper aux murs

clock = pygame.time.Clock()       # Horloge pour stabiliser les FPS
font_hud = pygame.font.Font(None, 22)   # Police d'écriture pour les stats
font_small = pygame.font.Font(None, 30) # Police pour le score et le menu

# --- GESTION DES DOSSIERS ---
ASSETS_DIR = "assets"
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_DIR = os.path.join(ASSETS_DIR, "boss", "test")

# Fonction pour charger une image sans faire planter le jeu si elle manque
def load_img(path, scale):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
    except:
        # Si l'image n'existe pas, on crée un rectangle rouge par défaut
        s = pygame.Surface((64, 64)); s.fill((255, 0, 50)); return s

# =================================================================
# CLASSE BOSS : Le comportement de l'ennemi
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp = 50              # Points de vie du boss
        self.is_dead = False      # Est-ce qu'il est mort ?
        scale = 3                 # On agrandit le boss 3 fois
        
        # On charge les images pour l'animation d'attaque
        self.anim_attack = [load_img(os.path.join(BOSS_DIR, f"attaque{i:02d}.png"), scale) for i in range(33)]
        # On charge les images pour l'animation de repos
        p1 = load_img(os.path.join(BOSS_DIR, "pause1.png"), scale)
        p2 = load_img(os.path.join(BOSS_DIR, "pause2.png"), scale)
        self.anim_pause = [p1, p2] * 10 

        self.current_anim = self.anim_attack # Animation actuelle
        self.is_attacking = True             # État du boss
        self.frame_index = 0                 # Image actuelle dans l'animation
        self.image = self.current_anim[0]    # L'image affichée
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size)) # Position
        self.mask = pygame.mask.from_surface(self.image) # Masque pour collisions précises
        
        self.vel_y = 0            # Vitesse verticale (gravité)
        self.anim_timer = 0       # Compteur pour changer d'image
        self.hit_flash = 0        # Compteur pour l'effet de clignotement quand touché

    def take_damage(self):
        """ Appelé quand le joueur frappe le boss """
        if not self.is_dead:
            self.hp -= 1
            self.hit_flash = 5    # Clignote pendant 5 images
            if self.hp <= 0:
                self.is_dead = True
                return True       # Renvoie True pour dire "il vient de mourir"
        return False

    def update(self, collision_tiles):
        """ Gère les mouvements et l'animation du boss """
        if self.is_dead: return   # Si mort, on ne fait rien

        # On définit la vitesse de l'animation selon l'état
        speed = 15 if self.is_attacking else 45
        self.anim_timer += 1
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            # Si l'animation finit, on change d'état (attaque <-> repos)
            if self.frame_index == 0:
                self.is_attacking = not self.is_attacking
                self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            self.image = self.current_anim[self.frame_index]
            self.mask = pygame.mask.from_surface(self.image)

        # Gravité du boss (pour qu'il touche le sol)
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: self.rect.bottom = t.top; self.vel_y = 0

    def draw(self, surface, cam_x, cam_y):
        """ Dessine le boss à l'écran par rapport à la caméra """
        if self.is_dead: return
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.hit_flash > 0:
            # Crée un effet blanc quand le boss prend des dégâts
            flash_surf = self.image.copy()
            flash_surf.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(flash_surf, pos)
            self.hit_flash -= 1
        else:
            surface.blit(self.image, pos)

# =================================================================
# CLASSE JOUEUR : Vos contrôles et votre vie
# =================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_img(PLAYER_IMG, 1)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.hp = 20              # Points de vie du joueur
        self.max_hp = 20
        self.score = 0            # Score (Niveau)
        self.invul_timer = 0      # Temps d'invincibilité après un coup
        self.vel_x, self.vel_y = 0, 0
        self.facing_right = True  # Regarde vers la droite ?
        self.on_ground = False    # Touche le sol ?
        self.is_on_wall = False   # Touche un mur ?
        self.dash_cooldown = 0
        self.dash_timer = 0
        self.is_attacking = False
        self.atk_frame = 0

    def update(self, collision_tiles, jump_tiles, boss):
        keys = pygame.key.get_pressed() # On récupère les touches pressées
        
        # --- GESTION DES DÉGÂTS ---
        if self.invul_timer > 0: self.invul_timer -= 1
        if not boss.is_dead:
            # On vérifie si les pixels du joueur touchent ceux du boss
            offset = (boss.rect.x - self.rect.x, boss.rect.y - self.rect.y)
            if self.mask.overlap(boss.mask, offset) and self.invul_timer <= 0:
                self.hp -= 1
                self.invul_timer = 60 # Invincible pendant 1 seconde

        # --- ATTAQUE (Touche X ou C) ---
        if (keys[K_x] or keys[K_c]) and not self.is_attacking:
            self.is_attacking = True
            self.atk_frame = 12
            # On crée une zone d'attaque devant le joueur
            atk_rect = pygame.Rect(0, 0, 80, 80)
            if self.facing_right: atk_rect.midleft = self.rect.midright
            else: atk_rect.midright = self.rect.midleft
            
            # Si le boss est dans cette zone, il prend cher !
            if not boss.is_dead:
                atk_offset = (boss.rect.x - atk_rect.x, boss.rect.y - atk_rect.y)
                atk_mask = pygame.mask.Mask((80, 80)); atk_mask.fill()
                if atk_mask.overlap(boss.mask, atk_offset):
                    if boss.take_damage(): self.score += 1 # +1 score si le boss meurt

        if self.is_attacking:
            self.atk_frame -= 1
            if self.atk_frame <= 0: self.is_attacking = False

        # --- MOUVEMENTS ET DASH (Touche A) ---
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if keys[K_a] and self.dash_cooldown == 0:
            self.dash_timer, self.dash_cooldown = DASH_DURATION, DASH_COOLDOWN

        # Gestion de la grimpe aux murs
        if self.is_on_wall and not self.on_ground:
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]: self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]: self.vel_y = CLIMB_SPEED
        else:
            self.vel_y += GRAVITY # Gravité normale

        # Dash ou déplacement normal
        if self.dash_timer > 0:
            self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            self.vel_y, self.dash_timer = 0, self.dash_timer - 1
        else:
            self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
            if self.vel_x > 0: self.facing_right = True
            elif self.vel_x < 0: self.facing_right = False

        # Saut
        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground:
            # Si on est sur une case "saut-activé", on saute plus haut
            can_jump_big = any(self.rect.colliderect(jt) for jt in jump_tiles)
            self.vel_y = JUMP_BIG if can_jump_big else JUMP_SMALL
            self.on_ground = False

        # --- COLLISIONS PHYSIQUES (Ne pas traverser les murs) ---
        self.rect.x += self.vel_x
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_x > 0: self.rect.right = t.left
                else: self.rect.left = t.right
        
        self.rect.y += self.vel_y
        self.on_ground = False
        self.is_on_wall = False
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: self.rect.bottom = t.top; self.vel_y, self.on_ground = 0, True
                else: self.rect.top = t.bottom; self.vel_y = 0
        
        # Vérification si on touche un mur (pour grimper)
        if not self.on_ground:
            wall_check = self.rect.inflate(4, 0)
            for t in collision_tiles:
                if wall_check.colliderect(t): self.is_on_wall = True; break

    def draw(self, surface, cam_x, cam_y):
        """ Dessine le joueur et ses effets """
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        # Clignotement si invincible
        if self.invul_timer % 10 < 5: surface.blit(self.image, pos)
        # Dessin de l'attaque
        if self.is_attacking:
            color = (0, 255, 255)
            r_atk = pygame.Rect(pos[0] + (20 if self.facing_right else -60), pos[1] - 10, 50, 50)
            pygame.draw.arc(surface, color, r_atk, -math.pi/2 if self.facing_right else math.pi/2, math.pi/2 if self.facing_right else 3*math.pi/2, 4)

# =================================================================
# SYSTÈME DE PAUSE (Touche ESC)
# =================================================================
def show_pause_menu():
    paused = True
    selected = 0
    options = ["REPRENDRE", "AIDE", "QUITTER"]
    overlay = pygame.Surface(INTERNAL_RES, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200)) # Fond noir transparent

    while paused:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE: paused = False
                if event.key == K_UP: selected = (selected - 1) % len(options)
                if event.key == K_DOWN: selected = (selected + 1) % len(options)
                if event.key == K_RETURN:
                    if selected == 0: paused = False
                    if selected == 2: pygame.quit(); exit()

        render_surface.blit(overlay, (0,0))
        for i, opt in enumerate(options):
            color = (0, 255, 200) if i == selected else (255, 255, 255)
            txt = font_small.render("> " + opt if i == selected else opt, True, color)
            render_surface.blit(txt, (INTERNAL_RES[0]//2 - txt.get_width()//2, 250 + i * 50))
        screen.blit(pygame.transform.scale(render_surface, (WIN_W, WIN_H)), (0,0))
        pygame.display.flip()
        clock.tick(30)

# =================================================================
# MAIN LOOP : Le cœur du jeu
# =================================================================
def main():
    # Chargement de la carte Tiled
    tmx_data = pytmx.load_pygame(MAP_FILE)
    player = Player(100, 100) # Création du joueur
    boss = Boss(30, 20, 32)   # Création du boss
    
    # On sépare les tuiles selon leur calque (collisions vs sauts)
    collision_tiles = []
    jump_tiles = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid:
                    r = pygame.Rect(x*32, y*32, 32, 32)
                    if layer.name == "hit-box": collision_tiles.append(r)
                    if layer.name == "saut-activé": jump_tiles.append(r)

    # BOUCLE INFINIE
    while True:
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE: show_pause_menu()

        # Mise à jour des personnages
        player.update(collision_tiles, jump_tiles, boss)
        boss.update(collision_tiles)
        
        # Calcul de la position de la caméra (suit le joueur)
        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width * 32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height * 32 - 600))

        # On efface l'écran
        render_surface.fill((20, 20, 25))
        
        # DESSIN DE LA CARTE (Culling : on ne dessine que ce qui est visible)
        start_x, end_x = int(cam_x // 32), int((cam_x + 800) // 32) + 1
        start_y, end_y = int(cam_y // 32), int((cam_y + 600) // 32) + 1
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x in range(start_x, end_x):
                    for y in range(start_y, end_y):
                        if 0 <= x < tmx_data.width and 0 <= y < tmx_data.height:
                            gid = layer.data[y][x]
                            if gid: render_surface.blit(tmx_data.get_tile_image_by_gid(gid), (x*32 - cam_x, y*32 - cam_y))

        # Dessin des personnages
        boss.draw(render_surface, cam_x, cam_y)
        player.draw(render_surface, cam_x, cam_y)

        # --- DESSIN DU HUD (Interface : Score et Vie) ---
        hud_cx, hud_y = INTERNAL_RES[0] // 2, INTERNAL_RES[1] - 50
        txt_lvl = font_small.render(f"NIVEAU : {player.score}", True, (255, 255, 255))
        render_surface.blit(txt_lvl, (hud_cx - txt_lvl.get_width()//2, hud_y - 30))
        
        # Dessin de la barre de vie
        bar_w, bar_h = 200, 15
        pygame.draw.rect(render_surface, (50, 0, 0), (hud_cx - bar_w//2, hud_y, bar_w, bar_h)) # Fond rouge sombre
        pygame.draw.rect(render_surface, (0, 255, 100), (hud_cx - bar_w//2, hud_y, int(bar_w * (player.hp/player.max_hp)), bar_h)) # Vie verte
        pygame.draw.rect(render_surface, (255, 255, 255), (hud_cx - bar_w//2, hud_y, bar_w, bar_h), 1) # Bordure blanche

        # Affichage technique (FPS et Coordonnées)
        tech_stats = [f"FPS: {int(clock.get_fps())}", f"COORDS: {player.rect.x//32}, {player.rect.y//32}"]
        for i, s in enumerate(tech_stats):
            txt = font_hud.render(s, True, (0, 255, 150))
            render_surface.blit(txt, (INTERNAL_RES[0] - txt.get_width() - 15, 15 + i * 20))

        # On affiche tout sur la fenêtre principale
        screen.blit(pygame.transform.scale(render_surface, (WIN_W, WIN_H)), (0,0))
        pygame.display.flip()
        clock.tick(FPS) # On attend pour rester à 60 FPS

if __name__ == "__main__":
    main()