import pygame
import settings

def ui_draw_text(surface, text, font, color, pos):
    shadow = font.render(text, True, (20, 20, 20))
    surface.blit(shadow, (pos[0]+2, pos[1]+2))
    img = font.render(text, True, color)
    surface.blit(img, pos)

def draw_hud(surface, player, boss, font, font_big, clock, boss_spawned):
    # HP
    pygame.draw.rect(surface, (50, 50, 50), (20, 20, 150, 15))
    hp_w = (player.hp / player.max_hp) * 150
    pygame.draw.rect(surface, settings.GREEN, (20, 20, hp_w, 15))
    ui_draw_text(surface, f"HP: {player.hp}", font, settings.WHITE, (25, 18))

    # Dash
    pygame.draw.rect(surface, (50, 50, 50), (20, 40, 100, 8))
    dash_ready = max(0, settings.DASH_COOLDOWN - player.dash_cooldown)
    dash_w = (dash_ready / settings.DASH_COOLDOWN) * 100
    c = settings.BLUE_DASH if player.dash_cooldown <= 0 else (100, 100, 100)
    pygame.draw.rect(surface, c, (20, 40, dash_w, 8))

    if boss_spawned and not boss.is_dead:
        pygame.draw.rect(surface, (50, 50, 50), (200, 550, 400, 20))
        boss_hp_w = (boss.hp / 50) * 400
        pygame.draw.rect(surface, settings.RED, (200, 550, boss_hp_w, 20))
        ui_draw_text(surface, "BOSS - THE TEST", font, settings.WHITE, (320, 525))

def draw_debug_f3(surface, player, clock, font):
    debug_surf = pygame.Surface((250, 140), pygame.SRCALPHA)
    debug_surf.fill(settings.DEBUG_BG)
    surface.blit(debug_surf, (10, 50))
    info = [
        f"FPS: {int(clock.get_fps())}",
        f"TILE POS: {player.rect.x // 32} / {player.rect.y // 32}",
        f"DASH: {player.dash_cooldown}f",
        f"GROUND: {player.on_ground}"
    ]
    for i, line in enumerate(info):
        img = font.render(line, True, settings.WHITE)
        surface.blit(img, (20, 60 + i * 20))

def show_game_over(screen, font_big):
    overlay = pygame.Surface((settings.WIN_W, settings.WIN_H), pygame.SRCALPHA)
    overlay.fill((150, 0, 0, 150)); screen.blit(overlay, (0, 0))
    msg = font_big.render("GAME OVER", True, settings.WHITE)
    retry = font_big.render("R pour Recommencer", True, settings.GOLD)
    screen.blit(msg, (settings.WIN_W//2 - msg.get_width()//2, 250))
    screen.blit(retry, (settings.WIN_W//2 - retry.get_width()//2, 350))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: waiting = False

def show_pause_menu(screen, font_big):
    paused = True
    while paused:
        screen.fill((20, 20, 20))
        ui_draw_text(screen, "PAUSE - ESC pour reprendre", font_big, settings.WHITE, (300, 300))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: paused = False
            if e.type == pygame.QUIT: pygame.quit(); exit()