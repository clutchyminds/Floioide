import pygame
import settings

# Fonction pour écrire du texte avec une petite ombre portée derrière
def ui_draw_text(surface, text, font, color, pos):
    # On dessine d'abord le texte en noir décalé de 2 pixels (l'ombre)
    shadow = font.render(text, True, (20, 20, 20))
    surface.blit(shadow, (pos[0]+2, pos[1]+2))
    # On dessine le texte principal par-dessus
    img = font.render(text, True, color)
    surface.blit(img, pos)

# Dessine les barres de vie et de dash en haut à gauche
def draw_hud(surface, player, boss, font, font_big, clock, boss_spawned):
    # Barre de vie du Joueur (Fond gris, puis rectangle vert)
    pygame.draw.rect(surface, (50, 50, 50), (20, 20, 150, 15))
    hp_w = (player.hp / player.max_hp) * 150 # Calcul de la largeur selon les PV
    pygame.draw.rect(surface, settings.GREEN, (20, 20, hp_w, 15))
    ui_draw_text(surface, f"HP: {player.hp}", font, settings.WHITE, (25, 18))

    # Petite barre de Dash (Bleue si prêt, Grise si en attente)
    pygame.draw.rect(surface, (50, 50, 50), (20, 40, 100, 8))
    dash_ready = max(0, settings.DASH_COOLDOWN - player.dash_cooldown)
    dash_w = (dash_ready / settings.DASH_COOLDOWN) * 100
    c = settings.BLUE_DASH if player.dash_cooldown <= 0 else (100, 100, 100)
    pygame.draw.rect(surface, c, (20, 40, dash_w, 8))

    # Si le boss est là, on affiche sa grande barre de vie en bas
    if boss_spawned and not boss.is_dead:
        pygame.draw.rect(surface, (50, 50, 50), (200, 550, 400, 20))
        boss_hp_w = (boss.hp / 50) * 400
        pygame.draw.rect(surface, settings.RED, (200, 550, boss_hp_w, 20))
        ui_draw_text(surface, "BOSS - THE TEST", font, settings.WHITE, (320, 525))

# Menu de débogage F3 (affiche les données techniques)
def draw_debug_f3(surface, player, clock, font):
    debug_surf = pygame.Surface((250, 140), pygame.SRCALPHA)
    debug_surf.fill(settings.DEBUG_BG)
    surface.blit(debug_surf, (10, 50))
    info = [
        f"FPS: {int(clock.get_fps())}",
        f"TILE POS: {player.rect.x // 32} / {player.rect.y // 32}", # Position en cases
        f"DASH: {player.dash_cooldown}f",
        f"GROUND: {player.on_ground}"
    ]
    for i, line in enumerate(info):
        img = font.render(line, True, settings.WHITE)
        surface.blit(img, (20, 60 + i * 20))

# Écran rouge quand on meurt
def show_game_over(screen, font_big):
    overlay = pygame.Surface((settings.WIN_W, settings.WIN_H), pygame.SRCALPHA)
    overlay.fill((150, 0, 0, 150)); screen.blit(overlay, (0, 0))
    msg = font_big.render("GAME OVER", True, settings.WHITE)
    retry = font_big.render("R pour Recommencer", True, settings.GOLD)
    screen.blit(msg, (settings.WIN_W//2 - msg.get_width()//2, 250))
    screen.blit(retry, (settings.WIN_W//2 - retry.get_width()//2, 350))
    pygame.display.flip()
    # On bloque le jeu ici jusqu'à ce que le joueur appuie sur R
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: waiting = False