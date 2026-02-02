import pygame
import math
import settings
import os

class Boss(pygame.sprite.Sprite):
    # ... (le code du boss reste identique, il utilise déjà les masks pour la précision)
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp = 50
        self.is_dead = False
        self.invul_timer = 0 
        scale = 3
        self.anim_attack = [settings.load_img(f"{settings.BOSS_DIR}/attaque{i:02d}.png", scale) for i in range(33)]
        p1 = settings.load_img(f"{settings.BOSS_DIR}/pause1.png", scale)
        p2 = settings.load_img(f"{settings.BOSS_DIR}/pause2.png", scale)
        self.anim_pause = [p1, p2] * 10
        self.current_anim = self.anim_attack
        self.is_attacking, self.frame_index = True, 0
        self.image = self.current_anim[0]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))
        self.mask = pygame.mask.from_surface(self.image)
        self.anim_timer, self.hit_flash = 0, 0
        self.facing_right = False

    def take_damage(self):
        if not self.is_dead and self.invul_timer <= 0:
            self.hp -= 1
            self.hit_flash = 5
            self.invul_timer = 60 
            if self.hp <= 0: self.is_dead = True
            return True
        return False

    def update(self, collision_tiles, player):
        if self.is_dead: return
        if self.invul_timer > 0: self.invul_timer -= 1
        self.facing_right = player.hitbox.centerx > self.rect.centerx # Changé rect -> hitbox
        speed = settings.BOSS_ATK_SPEED if self.is_attacking else settings.BOSS_IDLE_SPEED
        self.anim_timer += 1
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            if self.frame_index == 0:
                self.is_attacking = not self.is_attacking
                self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            img = self.current_anim[self.frame_index]
            self.image = pygame.transform.flip(img, True, False) if self.facing_right else img
            self.mask = pygame.mask.from_surface(self.image)

        if player.invul_timer <= 0:
            offset_x = player.hitbox.x - self.rect.x
            offset_y = player.hitbox.y - self.rect.y
            if self.mask.overlap(player.mask, (offset_x, offset_y)):
                player.hp -= 2
                player.invul_timer = 60
                player.vel_x = 15 if player.hitbox.centerx > self.rect.centerx else -15

    def draw(self, surface, cam_x, cam_y):
        if self.is_dead: return
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.invul_timer % 10 < 5:
            if self.hit_flash > 0:
                f = self.image.copy()
                f.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
                surface.blit(f, pos); self.hit_flash -= 1
            else: surface.blit(self.image, pos)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        path = "assets/mouvements"
        
        def load_small(file_path):
            img = pygame.image.load(file_path).convert_alpha()
            new_size = (img.get_width() // 5, img.get_height() // 5)
            return pygame.transform.scale(img, new_size)

        self.img_dash = load_small(os.path.join(path, "Dash.png"))
        self.anim_move = [load_small(os.path.join(path, f"avancer ({i}).png")) for i in range(1, 5)]
        self.anim_climb = [load_small(os.path.join(path, f"grimper ({i}).png")) for i in range(1, 4)]
        
        self.image = self.anim_move[0]
        # On utilise une hitbox plus petite que l'image
        # On réduit la largeur de 40% et la hauteur de 20% pour ignorer le vide
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect.inflate(-self.rect.width * 0.4, -self.rect.height * 0.1)
        self.mask = pygame.mask.from_surface(self.image)
        
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 12 
        
        self.hp, self.max_hp = 20, 20
        self.vel_x, self.vel_y = 0, 0
        self.on_ground, self.is_on_wall, self.facing_right = False, False, True
        self.invul_timer, self.dash_timer, self.dash_cooldown = 0, 0, 0
        self.can_double_jump, self.jump_cooldown = False, 0
        
        self.is_attacking = False
        self.atk_start_time = 0
        self.atk_duration = 1000 
        self.atk_current_pos = [0, 0]
        self.atk_dir = [0, 0]
        self.plant_angle = 0
        self.atk_frame_index = 0
        self.atk_speed = (5 * 32) / 60 
        
        size = (settings.ATTACK_SIZE_PX, settings.ATTACK_SIZE_PX)
        self.plant_frames = [pygame.transform.scale(pygame.image.load(p).convert_alpha(), size) for p in settings.PLANT_ATTACK_FRAMES]

    def animate(self):
        self.anim_timer += 1
        if self.dash_timer > 0:
            new_img = self.img_dash
        elif self.is_on_wall and not self.on_ground:
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.anim_climb)
            new_img = self.anim_climb[self.frame_index % len(self.anim_climb)]
        else:
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.anim_move)
            new_img = self.anim_move[self.frame_index % len(self.anim_move)]

        self.image = pygame.transform.flip(new_img, not self.facing_right, False)
        # On met à jour le mask pour que la transparence soit gérée contre le boss
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, keys, mouse_buttons, tiles, boss, m_world):
        if self.invul_timer > 0: self.invul_timer -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1
        if self.jump_cooldown > 0: self.jump_cooldown -= 1

        if mouse_buttons[2] and not self.is_attacking:
            self.is_attacking = True
            self.atk_start_time = pygame.time.get_ticks()
            self.atk_current_pos = list(self.hitbox.center)
            dx, dy = m_world[0] - self.hitbox.centerx, m_world[1] - self.hitbox.centery
            dist = math.hypot(dx, dy) if math.hypot(dx, dy) != 0 else 1
            self.atk_dir = [dx/dist, dy/dist]
            self.plant_angle = -math.degrees(math.atan2(dy, dx))

        if self.is_attacking:
            elapsed = pygame.time.get_ticks() - self.atk_start_time
            if elapsed < self.atk_duration:
                self.atk_current_pos[0] += self.atk_dir[0] * self.atk_speed
                self.atk_current_pos[1] += self.atk_dir[1] * self.atk_speed
                self.atk_frame_index = int((elapsed / self.atk_duration) * 15)
                atk_rect = pygame.Rect(self.atk_current_pos[0]-40, self.atk_current_pos[1]-40, 80, 80)
                if atk_rect.colliderect(boss.rect): boss.take_damage()
            else: self.is_attacking = False

        if keys[pygame.K_a] and self.dash_cooldown <= 0:
            self.dash_timer, self.dash_cooldown = settings.DASH_DURATION, settings.DASH_COOLDOWN

        if self.dash_timer > 0:
            self.dash_timer -= 1
            self.vel_x = settings.DASH_SPEED if self.facing_right else -settings.DASH_SPEED
            self.vel_y = 0
        else:
            move = (keys[pygame.K_d] - keys[pygame.K_q])
            self.vel_x = move * settings.MOVE_SPEED
            if move != 0: self.facing_right = move > 0
            
            if self.is_on_wall and not self.on_ground:
                if keys[pygame.K_SPACE]: self.vel_y = -settings.CLIMB_SPEED
                else: self.vel_y = 2
            else:
                self.vel_y += settings.GRAVITY
                if keys[pygame.K_SPACE] and self.jump_cooldown <= 0:
                    if self.on_ground:
                        self.vel_y = settings.JUMP_SMALL
                        self.on_ground, self.can_double_jump, self.jump_cooldown = False, True, 15
                    elif self.can_double_jump:
                        self.vel_y = settings.JUMP_SMALL
                        self.can_double_jump, self.jump_cooldown = False, 15

        # --- COLLISIONS UTILISANT LA HITBOX RÉDUITE ---
        self.hitbox.x += self.vel_x
        for t in tiles:
            if self.hitbox.colliderect(t):
                if self.vel_x > 0: self.hitbox.right = t.left
                else: self.hitbox.left = t.right
        
        self.hitbox.y += self.vel_y
        self.on_ground = False
        for t in tiles:
            if self.hitbox.colliderect(t):
                if self.vel_y > 0: 
                    self.hitbox.bottom = t.top
                    self.vel_y = 0
                    self.on_ground = True
                else: 
                    self.hitbox.top = t.bottom
                    self.vel_y = 0
        
        self.is_on_wall = False
        check = self.hitbox.inflate(8, 0)
        for t in tiles:
            if check.colliderect(t) and not self.on_ground: self.is_on_wall = True; break

        # On aligne le visuel (rect) sur la hitbox
        self.rect.center = self.hitbox.center
        self.animate()

    def draw(self, surface, cam_x, cam_y):
        p = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.invul_timer % 10 < 5: surface.blit(self.image, p)
        if self.is_attacking:
            f = self.plant_frames[min(self.atk_frame_index, 15)]
            rot = pygame.transform.rotate(f, self.plant_angle - 90)
            rect = rot.get_rect(center=(self.atk_current_pos[0] - cam_x, self.atk_current_pos[1] - cam_y))
            surface.blit(rot, rect)