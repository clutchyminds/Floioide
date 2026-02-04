import pygame

def draw_hud(surface, player, boss, font_hud, font_big, clock, boss_spawned):
    # Barre HP (En haut à droite)
    pygame.draw.rect(surface, (30, 30, 30), (580, 25, 200, 12))
    hp_w = max(0, (player.hp / 20) * 200)
    pygame.draw.rect(surface, (46, 204, 113), (580, 25, hp_w, 12))
    surface.blit(font_hud.render(f"HP: {player.hp}", True, (255, 255, 255)), (580, 8))

    # Barre Dash
    pygame.draw.rect(surface, (30, 30, 30), (580, 42, 200, 4))
    dash_w = (player.dash_cooldown / 60) * 200
    pygame.draw.rect(surface, (52, 152, 219), (580, 42, 200 - dash_w, 4))

    if boss_spawned:
        pygame.draw.rect(surface, (50, 0, 0), (200, 560, 400, 15))
        b_w = (boss.hp / 100) * 400
        pygame.draw.rect(surface, (231, 76, 60), (200, 560, b_w, 15))

def show_pause_menu(screen, font):
    paused = True
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    while paused:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: paused = False
        screen.blit(overlay, (0, 0))
        txt = font.render("PAUSE", True, (255, 255, 255))
        screen.blit(txt, (screen.get_width()//2 - 60, screen.get_height()//2))
        pygame.display.flip()

def show_game_over(screen, font):
    screen.fill((0, 0, 0))
    txt = font.render("GAME OVER - ESPACE", True, (200, 0, 0))
    screen.blit(txt, (200, 300))
    pygame.display.flip()
    wait = True
    while wait:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE: wait = False

def draw_debug_f3(surface, player, clock, font):
    fps = str(int(clock.get_fps()))
    surface.blit(font.render(f"FPS: {fps}", True, (255, 255, 255)), (10, 10))