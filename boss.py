import pygame
import os
from settings import *
from utils import load_img

class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp_max = 50
        self.hp = self.hp_max
        self.is_dead = False
        scale = 3 
        
        self.anim_attack = [load_img(os.path.join(BOSS_DIR, f"attaque{i:02d}.png"), scale) for i in range(33)]
        p1 = load_img(os.path.join(BOSS_DIR, "pause1.png"), scale)
        p2 = load_img(os.path.join(BOSS_DIR, "pause2.png"), scale)
        self.anim_pause = [p1, p2] * 10 

        self.current_anim = self.anim_attack
        self.is_attacking = True
        self.frame_index = 0
        self.image = self.current_anim[0]
        self.rect = self.image.get_rect(topleft=(tile_x * tile_size, tile_y * tile_size))
        self.mask = pygame.mask.from_surface(self.image)
        
        self.vel_y = 0
        self.anim_timer = 0
        self.hit_flash = 0

    def take_damage(self):
        if not self.is_dead:
            self.hp -= 1
            self.hit_flash = 5
            if self.hp <= 0:
                self.is_dead = True
                return True # Mort
        return False

    def update(self, collision_tiles):
        if self.is_dead: return
        speed = 15 if self.is_attacking else 45
        self.anim_timer += 1
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            if self.frame_index == 0:
                self.is_attacking = not self.is_attacking
                self.current_anim = self.anim_attack if self.is_attacking else self.anim_pause
            self.image = self.current_anim[self.frame_index]
            self.mask = pygame.mask.from_surface(self.image)

        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0: self.rect.bottom = t.top; self.vel_y = 0

    def draw(self, surface, cam_x, cam_y):
        if self.is_dead: return
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        
        # Dessin de la barre de vie locale (au-dessus du boss)
        bar_w = 100
        pygame.draw.rect(surface, (100, 0, 0), (pos[0], pos[1] - 15, bar_w, 8))
        pygame.draw.rect(surface, (255, 0, 0), (pos[0], pos[1] - 15, int(bar_w * (self.hp/self.hp_max)), 8))

        if self.hit_flash > 0:
            flash_surf = self.image.copy()
            flash_surf.fill((255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(flash_surf, pos)
            self.hit_flash -= 1
        else:
            surface.blit(self.image, pos)