import pygame
import math
from pygame.locals import *
from settings import *
from utils import load_img

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_img(PLAYER_IMG, 1)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        
        # Stats et XP
        self.hp, self.max_hp = 20, 20
        self.exp, self.exp_needed = 0, 100
        self.level = 1
        
        self.invul_timer = 0
        self.vel_x, self.vel_y = 0, 0
        self.facing_right = True
        self.on_ground = False
        self.is_on_wall = False
        self.dash_cooldown, self.dash_timer = 0, 0
        self.is_attacking, self.atk_frame = False, 0

    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= self.exp_needed:
            self.exp -= self.exp_needed
            self.level += 1
            self.exp_needed = int(self.exp_needed * 1.2) # Le prochain niveau est plus dur

    def update(self, collision_tiles, jump_tiles, boss):
        keys = pygame.key.get_pressed()
        
        # Dégâts
        if self.invul_timer > 0: self.invul_timer -= 1
        if not boss.is_dead:
            offset = (boss.rect.x - self.rect.x, boss.rect.y - self.rect.y)
            if self.mask.overlap(boss.mask, offset) and self.invul_timer <= 0:
                self.hp -= 1
                self.invul_timer = 60

        # Attaque
        if (keys[K_x] or keys[K_c]) and not self.is_attacking:
            self.is_attacking = True
            self.atk_frame = 12
            atk_rect = pygame.Rect(0, 0, 80, 80)
            if self.facing_right: atk_rect.midleft = self.rect.midright
            else: atk_rect.midright = self.rect.midleft
            
            if not boss.is_dead:
                atk_offset = (boss.rect.x - atk_rect.x, boss.rect.y - atk_rect.y)
                atk_mask = pygame.mask.Mask((80, 80)); atk_mask.fill()
                if atk_mask.overlap(boss.mask, atk_offset):
                    if boss.take_damage(): self.gain_exp(50) # Exp si mort
                    else: self.gain_exp(2) # Exp si touche

        if self.is_attacking: self.atk_frame -= 1; self.is_attacking = (self.atk_frame > 0)

        # Mouvement et Physique (Simplifié pour le bloc)
        self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * MOVE_SPEED
        if self.vel_x != 0: self.facing_right = self.vel_x > 0
        
        self.vel_y += GRAVITY
        if keys[K_SPACE] and self.on_ground: self.vel_y = JUMP_SMALL; self.on_ground = False

        self.rect.x += self.vel_x
        # (Insérer ici ta logique de collision avec collision_tiles)
        self.rect.y += self.vel_y
        if self.rect.bottom > 550: self.rect.bottom = 550; self.vel_y = 0; self.on_ground = True

    def draw(self, surface, cam_x, cam_y):
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.invul_timer % 10 < 5: surface.blit(self.image, pos)