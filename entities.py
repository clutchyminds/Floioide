import pygame
import math
import settings
import os

class RainParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # On importe random une seule fois au début ou on utilise un import global
        import random
        self.vy = random.uniform(10, 15)
        self.vx = -2
        self.lifetime = 100
        self.length = random.randint(5, 10)
        self.alive = True

    def update(self, tiles, particles_list):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        
        # OPTIMISATION : Collision mathématique simple au lieu de Rect.colliderect
        # On ne teste que les tuiles proches du joueur pour économiser les calculs
        for tile in tiles:
            # Si le bas de la goutte est à l'intérieur d'une tuile
            if tile.x < self.x < tile.x + 32:
                if tile.y < self.y + self.length < tile.y + 32:
                    # EFFET D'EXPLOSION (Splash)
                    import random
                    for _ in range(2): # On réduit à 2 gouttes de splash pour gagner en FPS
                        splash = Particle(self.x, self.y, (180, 200, 255)) 
                        splash.vx = random.uniform(-2, 2)
                        splash.vy = random.uniform(-2, -1)
                        splash.radius = random.randint(1, 2)
                        splash.lifetime = 10
                        particles_list.append(splash)
                    
                    self.alive = False 
                    break

    def draw(self, surface, cam_x, cam_y):
        pygame.draw.line(surface, (150, 150, 255), 
                         (self.x - cam_x, self.y - cam_y), 
                         (self.x - cam_x, self.y - cam_y + self.length), 1)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        # On donne une direction au hasard (vers le haut, gauche ou droite)
        import random
        self.vx = random.uniform(-1, 1) # Vitesse horizontale aléatoire
        self.vy = random.uniform(-1, 0) # Vitesse verticale (monte un peu)
        self.lifetime = 3000 # La particule va vivre 20 images (frames)
        self.radius = random.randint(6, 12) # Taille de départ

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1 # Elle vieillit
        if self.radius > 0.1:
            self.radius -= 0.2 # Elle rétrécit progressivement

    def draw(self, surface, cam_x, cam_y):
        # On dessine un petit cercle à la position de la particule
        pygame.draw.circle(surface, self.color, (int(self.x - cam_x), int(self.y - cam_y)), int(self.radius))


# --- LA CLASSE BOSS ---
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp = 50
        self.is_dead = False
        self.invul_timer = 0 # Temps d'invincibilité après avoir été frappé
        scale = 3 # Le boss est affiché 3 fois plus grand
        
        # Chargement des images d'attaque et de repos
        self.anim_attack = [settings.load_img(f"{settings.BOSS_DIR}/attaque{i:02d}.png", scale) for i in range(33)]
        p1 = settings.load_img(f"{settings.BOSS_DIR}/pause1.png", scale)
        p2 = settings.load_img(f"{settings.BOSS_DIR}/pause2.png", scale)
        self.anim_pause = [p1, p2] * 10
        
        self.current_anim = self.anim_attack
        self.is_attacking, self.frame_index = True, 0
        self.image = self.current_anim[0]
        # Positionnement sur la carte
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))
        # Le masque sert pour la collision pixel-perfect (ignore le vide autour du boss)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.anim_timer, self.hit_flash = 0, 0
        self.facing_right = False

    def take_damage(self):
        # Si le boss n'est pas mort et n'est pas déjà en train de clignoter
        if not self.is_dead and self.invul_timer <= 0:
            self.hp -= 1
            self.hit_flash = 5 # Clignote blanc pendant 5 frames
            self.invul_timer = 60 # Invincible pendant 1 seconde (60 frames)
            if self.hp <= 0: self.is_dead = True
            return True
        return False

    def update(self, collision_tiles, player):
        if self.is_dead: return
        if self.invul_timer > 0: self.invul_timer -= 1
        
        # Le boss regarde toujours vers le joueur
        self.facing_right = player.hitbox.centerx > self.rect.centerx
        
        # Gestion de la vitesse de l'animation
        speed = settings.BOSS_ATK_SPEED if self.is_attacking else settings.BOSS_IDLE_SPEED
        self.anim_timer += 1
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            # Si l'animation est finie, on alterne entre Attaque et Repos
            if self.frame_index == 0:
                self.is_attacking = not self.is_attacking
                self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            
            img = self.current_anim[self.frame_index]
            # On retourne l'image si le boss regarde à droite
            self.image = pygame.transform.flip(img, True, False) if self.facing_right else img
            # On remet à jour le masque car l'image a changé
            self.mask = pygame.mask.from_surface(self.image)

        # COLLISION AVEC LE JOUEUR
        if player.invul_timer <= 0:
            # On calcule la distance entre le haut-gauche du boss et celui du joueur
            offset_x = player.rect.x - self.rect.x
            offset_y = player.rect.y - self.rect.y
            # Si leurs pixels opaques se touchent :
            if self.mask.overlap(player.mask, (offset_x, offset_y)):
                player.hp -= 2
                player.invul_timer = 60 # Le joueur devient invincible
                # Le joueur est repoussé en arrière
                player.vel_x = 15 if player.hitbox.centerx > self.rect.centerx else -15

    def draw(self, surface, cam_x, cam_y):
        if self.is_dead: return
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.invul_timer % 10 < 5: # Effet de clignotement
            if self.hit_flash > 0:
                f = self.image.copy()
                f.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
                surface.blit(f, pos); self.hit_flash -= 1
            else: surface.blit(self.image, pos)

# --- LA CLASSE JOUEUR ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        path = "assets/mouvements"
        
        # Petite fonction pour charger et diviser par 5 la taille des images
        def load_small(file_path):
            img = pygame.image.load(file_path).convert_alpha()
            return pygame.transform.scale(img, (img.get_width() // 5, img.get_height() // 5))

        # Chargement des différentes animations
        self.img_dash = load_small(os.path.join(path, "Dash.png"))
        self.anim_move = [load_small(os.path.join(path, f"avancer ({i}).png")) for i in range(1, 5)]
        self.anim_climb = [load_small(os.path.join(path, f"grimper ({i}).png")) for i in range(1, 4)]
        
        self.image = self.anim_move[0]
        
        # LA HITBOX HYPER SERRÉE (Le secret pour ne pas avoir d'espace vide)
        # On demande à Pygame de trouver le rectangle qui touche vraiment les pixels
        inner_rect = self.image.get_bounding_rect()
        self.hitbox = pygame.Rect(x, y, inner_rect.width, inner_rect.height)
        # 'rect' sert uniquement à placer l'image visuelle par-dessus la hitbox
        self.rect = self.image.get_rect(center=self.hitbox.center)
        self.mask = pygame.mask.from_surface(self.image)
        
        # Variables de mouvement
        self.hp, self.max_hp = 20, 20
        self.vel_x, self.vel_y = 0, 0 # Vitesses actuelle
        self.on_ground, self.is_on_wall, self.facing_right = False, False, True
        self.invul_timer, self.dash_timer, self.dash_cooldown = 0, 0, 0
        self.can_double_jump, self.jump_cooldown = False, 0
        
        # Variables de l'attaque magique
        self.is_attacking = False
        self.atk_start_time = 0
        self.atk_duration = 1000 
        self.atk_current_pos = [0, 0]
        self.atk_dir, self.plant_angle = [0, 0], 0
        self.atk_frame_index, self.atk_speed = 0, (5 * 32) / 60 
        
        # Chargement des 16 images de l'attaque plante
        size = (settings.ATTACK_SIZE_PX, settings.ATTACK_SIZE_PX)
        self.plant_frames = [pygame.transform.scale(pygame.image.load(p).convert_alpha(), size) for p in settings.PLANT_ATTACK_FRAMES]
        self.frame_index, self.anim_timer, self.anim_speed = 0, 0, 12

    def animate(self):
        self.anim_timer += 1
        # On choisit l'image selon l'état (dash, grimpe ou marche)
        if self.dash_timer > 0:
            new_img = self.img_dash
        elif self.is_on_wall and not self.on_ground:
            if self.anim_timer >= self.anim_speed:
                self.anim_timer, self.frame_index = 0, (self.frame_index + 1) % len(self.anim_climb)
            new_img = self.anim_climb[self.frame_index % len(self.anim_climb)]
        else:
            if self.anim_timer >= self.anim_speed:
                self.anim_timer, self.frame_index = 0, (self.frame_index + 1) % len(self.anim_move)
            new_img = self.anim_move[self.frame_index % len(self.anim_move)]

        # On applique la direction (gauche ou droite)
        self.image = pygame.transform.flip(new_img, not self.facing_right, False)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, keys, mouse_buttons, tiles, boss, m_world, particles):
        # Gestion des chronomètres (timers)
        if self.invul_timer > 0: self.invul_timer -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.jump_cooldown > 0: self.jump_cooldown -= 1
        # Si on marche au sol, on crée de la poussière sous les pieds
        
        if self.on_ground and abs(self.vel_x) > 0:
            particles.append(Particle(self.hitbox.centerx, self.hitbox.bottom, (0, 250, 0)))

        # Une traînée bleue pendant le dash
        if self.dash_timer > 0:
            particles.append(Particle(self.hitbox.centerx, self.hitbox.centery, (0, 150, 255)))

        # ATTAQUE (CLIC DROIT)
        if mouse_buttons[2] and not self.is_attacking:
            self.is_attacking, self.atk_start_time = True, pygame.time.get_ticks()
            self.atk_current_pos = list(self.hitbox.center)
            # Calcul de la direction vers la souris
            dx, dy = m_world[0] - self.hitbox.centerx, m_world[1] - self.hitbox.centery
            dist = math.hypot(dx, dy) if math.hypot(dx, dy) != 0 else 1
            self.atk_dir = [dx/dist, dy/dist]
            # Angle pour faire pivoter l'image vers la cible
            self.plant_angle = -math.degrees(math.atan2(dy, dx))

        if self.is_attacking:
            elapsed = pygame.time.get_ticks() - self.atk_start_time
            if elapsed < self.atk_duration:
                # La plante avance
                self.atk_current_pos[0] += self.atk_dir[0] * self.atk_speed
                self.atk_current_pos[1] += self.atk_dir[1] * self.atk_speed
                self.atk_frame_index = int((elapsed / self.atk_duration) * 15)
                # Collision plante contre boss
                atk_rect = pygame.Rect(self.atk_current_pos[0]-20, self.atk_current_pos[1]-20, 40, 40)
                if atk_rect.colliderect(boss.rect): boss.take_damage()
            else: self.is_attacking = False

        # DASH (TOUCHE A)
        if keys[pygame.K_a] and self.dash_cooldown <= 0:
            self.dash_timer, self.dash_cooldown = settings.DASH_DURATION, settings.DASH_COOLDOWN

        if self.dash_timer > 0:
            self.dash_timer -= 1
            self.vel_x = settings.DASH_SPEED if self.facing_right else -settings.DASH_SPEED
            self.vel_y = 0
        else:
            # MOUVEMENT NORMAL
            move = (keys[pygame.K_d] - keys[pygame.K_q]) # Donne 1 (D), -1 (Q) ou 0
            self.vel_x = move * settings.MOVE_SPEED
            if move != 0: self.facing_right = move > 0
            
            # ESCALADE AUTO
            if self.is_on_wall and not self.on_ground:
                if move != 0: self.vel_y = -settings.CLIMB_SPEED
                else: self.vel_y = 2
                if keys[pygame.K_SPACE] and self.jump_cooldown <= 0:
                    self.vel_y = settings.JUMP_SMALL; self.jump_cooldown = 15
            else:
                # GRAVITÉ ET SAUT
                self.vel_y += settings.GRAVITY
                if keys[pygame.K_SPACE] and self.jump_cooldown <= 0:
                    if self.on_ground:
                        self.vel_y, self.on_ground, self.can_double_jump, self.jump_cooldown = settings.JUMP_SMALL, False, True, 15
                    elif self.can_double_jump:
                        self.vel_y, self.can_double_jump, self.jump_cooldown = settings.JUMP_SMALL, False, 15

        # COLLISIONS (Le moment le plus important)
        # Horizontal
        self.hitbox.x += self.vel_x
        for t in tiles:
            if self.hitbox.colliderect(t):
                if self.vel_x > 0: self.hitbox.right = t.left
                else: self.hitbox.left = t.right
        
        # Vertical
        self.hitbox.y += self.vel_y
        self.on_ground = False
        for t in tiles:
            if self.hitbox.colliderect(t):
                if self.vel_y > 0: # On tombe sur le sol
                    self.hitbox.bottom = t.top; self.vel_y = 0; self.on_ground = True
                else: # On cogne le plafond
                    self.hitbox.top = t.bottom; self.vel_y = 0
        
        # On vérifie si un mur est à côté (pour grimper)
        self.is_on_wall = False
        check_rect = self.hitbox.inflate(4, 0)
        for t in tiles:
            if check_rect.colliderect(t) and not self.on_ground:
                self.is_on_wall = True; break

        self.animate()
        # On aligne l'image visuelle (rect) sur la hitbox technique
        self.rect.center = self.hitbox.center

    def draw(self, surface, cam_x, cam_y):
        p = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.invul_timer % 10 < 5: 
            surface.blit(self.image, p)

        if self.is_attacking:
            f = self.plant_frames[min(self.atk_frame_index, 15)]
            rot = pygame.transform.rotate(f, self.plant_angle - 90)
            rect = rot.get_rect(center=(self.atk_current_pos[0] - cam_x, self.atk_current_pos[1] - cam_y))
            surface.blit(rot, rect)