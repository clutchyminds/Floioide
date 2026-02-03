import pygame
import pytmx
import math
import os
from pygame.locals import *


# =================================================================
# CONFIG GÉNÉRALE
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
font_small = pygame.font.Font(None, 30)

# --- MODES DEBUG / GAMEPLAY ---
FLY_MODE = False          # voler
BREAK_MODE = False        # casser des blocs
PLAYER_SPEED_MULT = 1.0   # multiplicateur de vitesse

# --- DOSSIERS / FICHIERS ---
ASSETS_DIR = "assets"
ATTACK_DIR = os.path.join(ASSETS_DIR, "attaque")
PLAYER_IMG = os.path.join(ASSETS_DIR, "player", "player.png")
MAP_FILE = os.path.join(ASSETS_DIR, "maps", "map.tmx")
BOSS_DIR = os.path.join(ASSETS_DIR, "boss", "test")

# Frames d’attaque : assets/attaque/frame_00_delay-0.1s.png -> ...15...
PLANT_ATTACK_FRAMES = [
    os.path.join(ATTACK_DIR, f"frame_{i:02d}_delay-0.1s.png")
    for i in range(16)
]

# 0.1 s entre chaque frame = 100 ms
ATTACK_FRAME_DURATION = 100  # ms


def load_img(path, scale):
    """Charge une image, ou renvoie un carré rouge si échec."""
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(
            img,
            (int(img.get_width() * scale), int(img.get_height() * scale))
        )
    except Exception as e:
        print("ERREUR LOAD:", path, e)
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        s.fill((255, 0, 50, 255))
        return s


# =================================================================
# CLASSE BOSS
# =================================================================
class Boss(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y, tile_size):
        super().__init__()
        self.hp = 50
        self.is_dead = False
        scale = 3

        self.anim_attack = [
            load_img(os.path.join(BOSS_DIR, f"attaque{i:02d}.png"), scale)
            for i in range(33)
        ]
        p1 = load_img(os.path.join(BOSS_DIR, "pause1.png"), scale)
        p2 = load_img(os.path.join(BOSS_DIR, "pause2.png"), scale)
        self.anim_pause = [p1, p2] * 10

        self.current_anim = self.anim_attack
        self.is_attacking = True
        self.frame_index = 0
        self.image = self.current_anim[0]
        self.rect = self.image.get_rect(
            topleft=(tile_x * tile_size, tile_y * tile_size)
        )
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
                return True
        return False

    def update(self, collision_tiles):
        if self.is_dead:
            return

        speed = 15 if self.is_attacking else 45
        self.anim_timer += 1
        if self.anim_timer >= speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.current_anim)
            if self.frame_index == 0:
                self.is_attacking = not self.is_attacking
                self.current_anim = (
                    self.anim_attack if self.is_attacking else self.anim_pause
                )
            self.image = self.current_anim[self.frame_index]
            self.mask = pygame.mask.from_surface(self.image)

        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0:
                    self.rect.bottom = t.top
                    self.vel_y = 0

    def draw(self, surface, cam_x, cam_y):
        if self.is_dead:
            return
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.hit_flash > 0:
            flash_surf = self.image.copy()
            flash_surf.fill((255, 255, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(flash_surf, pos)
            self.hit_flash -= 1
        else:
            surface.blit(self.image, pos)


# =================================================================
# CLASSE JOUEUR
# =================================================================
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = load_img(PLAYER_IMG, 1)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.mask = pygame.mask.from_surface(self.image)

        self.hp = 20
        self.max_hp = 20
        self.score = 0
        self.level = 1
        self.exp = 0
        self.exp_needed = 10
        self.invul_timer = 0
        self.vel_x, self.vel_y = 0, 0
        self.facing_right = True
        self.on_ground = False
        self.is_on_wall = False
        self.dash_cooldown = 0
        self.dash_timer = 0

        # --- ATTAQUE PLANTE ---
        self.is_attacking = False
        self.atk_frame_index = 0
        self.atk_start_time = 0

        # Chargement brut, puis scale plus grand (16x16 -> 48x48)
        base_frames = [
            pygame.image.load(path).convert_alpha()
            for path in PLANT_ATTACK_FRAMES
        ]
        SCALE = 3  # 16 * 3 = 48
        ATTACK_SIZE = (int(16 * SCALE), int(16 * SCALE))
        self.plant_frames = [
            pygame.transform.scale(img, ATTACK_SIZE)
            for img in base_frames
        ]

        self.plant_angle = 0
        self.attack_origin = (0, 0)

    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_needed:
            self.exp -= self.exp_needed
            self.level += 1
            self.exp_needed += 5
            self.hp = self.max_hp

    def start_attack(self):
        self.is_attacking = True
        self.atk_frame_index = 0
        self.atk_start_time = pygame.time.get_ticks()

        foot_x = self.rect.centerx
        foot_y = self.rect.bottom
        self.attack_origin = (foot_x, foot_y)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_x = mouse_x * INTERNAL_RES[0] / WIN_W
        mouse_y = mouse_y * INTERNAL_RES[1] / WIN_H

        dx = mouse_x - foot_x
        dy = mouse_y - foot_y
        self.plant_angle = -math.degrees(math.atan2(dy, dx))

    def update_attack_anim(self):
        if not self.is_attacking:
            return
        now = pygame.time.get_ticks()
        elapsed = now - self.atk_start_time
        frame_count = len(self.plant_frames)
        self.atk_frame_index = elapsed // ATTACK_FRAME_DURATION
        if self.atk_frame_index >= frame_count:
            self.is_attacking = False
            self.atk_frame_index = frame_count - 1

    def apply_attack_damage(self, boss):
        if not self.is_attacking or boss.is_dead:
            return
        ox, oy = self.attack_origin
        angle_rad = -math.radians(self.plant_angle)
        hit_x = ox + math.cos(angle_rad) * 80
        hit_y = oy + math.sin(angle_rad) * 80

        atk_rect = pygame.Rect(0, 0, 80, 80)
        atk_rect.center = (hit_x, hit_y)

        atk_mask = pygame.mask.Mask((80, 80))
        atk_mask.fill()
        atk_offset = (boss.rect.x - atk_rect.x, boss.rect.y - atk_rect.y)
        if atk_mask.overlap(boss.mask, atk_offset):
            if boss.take_damage():
                self.score += 1
                self.add_exp(5)

    def update(self, collision_tiles, jump_tiles, boss):
        global FLY_MODE, BREAK_MODE, PLAYER_SPEED_MULT

        keys = pygame.key.get_pressed()

        if self.invul_timer > 0:
            self.invul_timer -= 1
        if not boss.is_dead:
            offset = (boss.rect.x - self.rect.x, boss.rect.y - self.rect.y)
            if self.mask.overlap(boss.mask, offset) and self.invul_timer <= 0:
                self.hp -= 1
                self.invul_timer = 60

        if (keys[K_x] or keys[K_c]) and not self.is_attacking:
            self.start_attack()
            self.apply_attack_damage(boss)

        self.update_attack_anim()

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if keys[K_a] and self.dash_cooldown == 0:
            self.dash_timer, self.dash_cooldown = DASH_DURATION, DASH_COOLDOWN

        # Gravité / vol
        if self.is_on_wall and not self.on_ground:
            self.vel_y = 0
            if keys[K_UP] or keys[K_z]:
                self.vel_y = -CLIMB_SPEED
            elif keys[K_DOWN] or keys[K_s]:
                self.vel_y = CLIMB_SPEED
        else:
            if FLY_MODE:
                self.vel_y = (keys[K_DOWN] - keys[K_UP] + keys[K_s] - keys[K_z]) * MOVE_SPEED
            else:
                self.vel_y += GRAVITY

        # Vitesse horizontale avec multiplicateur
        if self.dash_timer > 0:
            self.vel_x = DASH_SPEED if self.facing_right else -DASH_SPEED
            self.vel_y = 0
            self.dash_timer -= 1
        else:
            speed = MOVE_SPEED * PLAYER_SPEED_MULT
            self.vel_x = (keys[K_RIGHT] - keys[K_LEFT]) * speed
            if self.vel_x > 0:
                self.facing_right = True
            elif self.vel_x < 0:
                self.facing_right = False

        if (keys[K_SPACE] or keys[K_UP] or keys[K_z]) and self.on_ground and not FLY_MODE:
            can_jump_big = any(self.rect.colliderect(jt) for jt in jump_tiles)
            self.vel_y = JUMP_BIG if can_jump_big else JUMP_SMALL
            self.on_ground = False

        # Casser des blocs autour du joueur si BREAK_MODE + clic gauche
        if BREAK_MODE and pygame.mouse.get_pressed()[0]:
            hit_rect = self.rect.inflate(20, 20)
            collision_tiles[:] = [t for t in collision_tiles if not t.colliderect(hit_rect)]

        self.rect.x += self.vel_x
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_x > 0:
                    self.rect.right = t.left
                else:
                    self.rect.left = t.right

        self.rect.y += self.vel_y
        self.on_ground = False
        self.is_on_wall = False
        for t in collision_tiles:
            if self.rect.colliderect(t):
                if self.vel_y > 0:
                    self.rect.bottom = t.top
                    self.vel_y = 0
                    self.on_ground = True
                else:
                    self.rect.top = t.bottom
                    self.vel_y = 0

        if not self.on_ground:
            wall_check = self.rect.inflate(4, 0)
            for t in collision_tiles:
                if wall_check.colliderect(t):
                    self.is_on_wall = True
                    break

    def draw(self, surface, cam_x, cam_y):
        pos = (self.rect.x - cam_x, self.rect.y - cam_y)
        if self.invul_timer % 10 < 5:
            surface.blit(self.image, pos)

        if self.is_attacking and self.plant_frames:
            frame = self.plant_frames[min(self.atk_frame_index, len(self.plant_frames) - 1)]
            rotated = pygame.transform.rotate(frame, self.plant_angle)
            plant_rect = rotated.get_rect()

            ox, oy = self.attack_origin
            foot_x = ox - cam_x
            foot_y = oy - cam_y
            plant_rect.center = (foot_x, foot_y)

            surface.blit(rotated, plant_rect)


# =================================================================
# MENU PAUSE / DEBUG
# =================================================================
def show_pause_menu():
    global FLY_MODE, BREAK_MODE, PLAYER_SPEED_MULT

    paused = True
    selected = 0
    options = [
        "REPRENDRE",
        "TOGGLE FLY MODE",
        "TOGGLE BREAK MODE",
        "VITESSE +",
        "VITESSE -",
        "QUITTER"
    ]
    overlay = pygame.Surface(INTERNAL_RES, pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))

    while paused:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    paused = False
                if event.key == K_UP:
                    selected = (selected - 1) % len(options)
                if event.key == K_DOWN:
                    selected = (selected + 1) % len(options)
                if event.key == K_RETURN:
                    if options[selected] == "REPRENDRE":
                        paused = False
                    elif options[selected] == "TOGGLE FLY MODE":
                        FLY_MODE = not FLY_MODE
                    elif options[selected] == "TOGGLE BREAK MODE":
                        BREAK_MODE = not BREAK_MODE
                    elif options[selected] == "VITESSE +":
                        PLAYER_SPEED_MULT = min(3.0, PLAYER_SPEED_MULT + 0.5)
                    elif options[selected] == "VITESSE -":
                        PLAYER_SPEED_MULT = max(0.5, PLAYER_SPEED_MULT - 0.5)
                    elif options[selected] == "QUITTER":
                        pygame.quit()
                        exit()

        render_surface.blit(overlay, (0, 0))

        title_txt = font_small.render("MENU DEBUG", True, (0, 255, 200))
        render_surface.blit(
            title_txt,
            (INTERNAL_RES[0] // 2 - title_txt.get_width() // 2, 150)
        )

        status_lines = [
            f"Fly: {'ON' if FLY_MODE else 'OFF'}",
            f"Break: {'ON' if BREAK_MODE else 'OFF'}",
            f"Speed x{PLAYER_SPEED_MULT:.1f}",
        ]
        for i, s in enumerate(status_lines):
            st = font_hud.render(s, True, (200, 200, 200))
            render_surface.blit(st, (50, 50 + i * 20))

        for i, opt in enumerate(options):
            color = (0, 255, 200) if i == selected else (255, 255, 255)
            txt = font_small.render(
                "> " + opt if i == selected else opt,
                True,
                color
            )
            render_surface.blit(
                txt,
                (INTERNAL_RES[0] // 2 - txt.get_width() // 2, 220 + i * 40)
            )

        screen.blit(pygame.transform.scale(render_surface, (WIN_W, WIN_H)), (0, 0))
        pygame.display.flip()
        clock.tick(30)


# =================================================================
# MAIN LOOP
# =================================================================
def main():
    tmx_data = pytmx.load_pygame(MAP_FILE)
    player = Player(100, 100)
    boss = Boss(29, 92, 32)  # boss en 29, 92

    collision_tiles = []
    jump_tiles = []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid:
                    r = pygame.Rect(x * 32, y * 32, 32, 32)
                    if layer.name == "hit-box":
                        collision_tiles.append(r)
                    if layer.name == "saut-activé":
                        jump_tiles.append(r)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                show_pause_menu()

        debug_infos = [
            f"FPS: {int(clock.get_fps())}",
            f"Player Pos: {player.rect.x}, {player.rect.y}",
            f"Tile Coords: {player.rect.x // 32}, {player.rect.y // 32}",
            f"On Ground: {player.on_ground}",
            f"On Wall: {player.is_on_wall}",
            f"Dash Cooldown: {player.dash_cooldown}",
        ]

        render_surface.fill((20, 20, 25))
        for i, info in enumerate(debug_infos):
            text_surf = font_hud.render(info, True, (255, 255, 255))
            x_pos = INTERNAL_RES[0] - text_surf.get_width() - 10
            render_surface.blit(text_surf, (x_pos, 10 + i * 20))

        player.update(collision_tiles, jump_tiles, boss)
        boss.update(collision_tiles)

        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width * 32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height * 32 - 600))

        start_x, end_x = int(cam_x // 32), int((cam_x + 800) // 32) + 1
        start_y, end_y = int(cam_y // 32), int((cam_y + 600) // 32) + 1
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x in range(start_x, end_x):
                    for y in range(start_y, end_y):
                        if 0 <= x < tmx_data.width and 0 <= y < tmx_data.height:
                            gid = layer.data[y][x]
                            if gid:
                                render_surface.blit(
                                    tmx_data.get_tile_image_by_gid(gid),
                                    (x * 32 - cam_x, y * 32 - cam_y),
                                )

        boss.draw(render_surface, cam_x, cam_y)
        player.draw(render_surface, cam_x, cam_y)

        # Barre de vie boss centrée en haut
        if not boss.is_dead:
            bar_w = 200
            bar_h = 12
            bar_x = INTERNAL_RES[0] // 2 - bar_w // 2
            bar_y = 40
            pygame.draw.rect(render_surface, (100, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            health_width = int(bar_w * (boss.hp / 50))
            pygame.draw.rect(
                render_surface, (0, 255, 0), (bar_x, bar_y, health_width, bar_h)
            )
            pygame.draw.rect(
                render_surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 1
            )

        # HUD joueur : level + barre de vie en haut à droite
        bar_w, bar_h = 200, 15
        margin = 10
        bar_x = INTERNAL_RES[0] - bar_w - margin
        bar_y = margin

        txt_lvl = font_small.render(f"LVL : {player.level}", True, (255, 215, 0))
        lvl_x = INTERNAL_RES[0] - txt_lvl.get_width() - margin
        lvl_y = bar_y - txt_lvl.get_height() - 5
        render_surface.blit(txt_lvl, (lvl_x, lvl_y))

        pygame.draw.rect(
            render_surface,
            (50, 0, 0),
            (bar_x, bar_y, bar_w, bar_h)
        )
        pygame.draw.rect(
            render_surface,
            (0, 255, 100),
            (bar_x, bar_y, int(bar_w * (player.hp / player.max_hp)), bar_h)
        )
        pygame.draw.rect(
            render_surface,
            (255, 255, 255),
            (bar_x, bar_y, bar_w, bar_h),
            1
        )

        # Barre d’XP centrée en bas
        exp_bar_w = 200
        exp_x = INTERNAL_RES[0] // 2 - exp_bar_w // 2
        exp_y = INTERNAL_RES[1] - 80
        pygame.draw.rect(render_surface, (50, 50, 50), (exp_x, exp_y, exp_bar_w, 10))
        if player.exp_needed > 0:
            current_exp_w = int(exp_bar_w * (player.exp / player.exp_needed))
        else:
            current_exp_w = 0
        pygame.draw.rect(
            render_surface,
            (0, 191, 255),
            (exp_x, exp_y, current_exp_w, 10)
        )

        tech_stats = [
            f"FPS: {int(clock.get_fps())}",
            f"COORDS: {player.rect.x // 32}, {player.rect.y // 32}",
        ]
        for i, s in enumerate(tech_stats):
            txt = font_hud.render(s, True, (0, 255, 150))
            render_surface.blit(
                txt, (INTERNAL_RES[0] - txt.get_width() - 15, 15 + i * 20)
            )

        screen.blit(pygame.transform.scale(render_surface, (WIN_W, WIN_H)), (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
