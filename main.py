import pygame
import pytmx # Pour lire les fichiers de carte Tiled (.tmx)
import settings
from entities import Player, Boss
import ui

def main():
    pygame.init()
    # Création de la fenêtre réelle
    screen = pygame.display.set_mode((settings.WIN_W, settings.WIN_H))
    # Création de la surface de dessin (plus petite, pour l'effet Pixel Art)
    render_surface = pygame.Surface(settings.INTERNAL_RES)
    clock = pygame.time.Clock()
    font_hud = pygame.font.Font(None, 24)
    font_big = pygame.font.Font(None, 50)

    # Fonction pour remettre le jeu à zéro (quand on meurt)
    def reset_game():
        tm = pytmx.load_pygame(settings.MAP_FILE)
        p, b = Player(100, 100), Boss(29, 92, 32)
        return tm, p, b

    tmx_data, player, boss = reset_game()
    collision_tiles, spawn_trigger_tiles = [], []
    
    # Lecture des couches de la carte Tiled
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid:
                    rect = pygame.Rect(x*32, y*32, 32, 32)
                    # Si la couche s'appelle "hit-box", c'est un mur solide
                    if layer.name == "hit-box": collision_tiles.append(rect)
                    # Si c'est "boss-test", c'est la zone qui fait apparaître le boss
                    elif layer.name == "boss-test": spawn_trigger_tiles.append(rect)

    boss_spawned, show_f3, running = False, False, True

    # BOUCLE DE JEU (Tourne 60 fois par seconde)
    while running:
        # CALCUL DE LA CAMÉRA (suit le joueur)
        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width*32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height*32 - 600))
        
        # Position de la souris convertie pour correspondre au monde du jeu
        m_pos = pygame.mouse.get_pos()
        mx = (m_pos[0] * 800 / 1280) + cam_x
        my = (m_pos[1] * 600 / 720) + cam_y
        
        # ÉVÉNEMENTS (Clavier / Souris / Quitter)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: ui.show_pause_menu(screen, font_big)
                if event.key == pygame.K_F3: show_f3 = not show_f3

        # ZONE DE SPAWN DU BOSS
        if not boss_spawned:
            for t in spawn_trigger_tiles:
                if player.rect.colliderect(t): boss_spawned = True; break

        # MISE À JOUR DES PERSONNAGES
        player.update(pygame.key.get_pressed(), pygame.mouse.get_pressed(), collision_tiles, boss, (mx, my))
        if boss_spawned: boss.update(collision_tiles, player)
        
        # MORT DU JOUEUR
        if player.hp <= 0:
            ui.show_game_over(screen, font_big)
            tmx_data, player, boss = reset_game(); boss_spawned = False

        # --- DESSIN (RENDERING) ---
        render_surface.fill((25, 25, 30)) # Efface l'écran avec un gris foncé
        
        # Dessin du décor (on ne dessine que ce qui est visible à l'écran pour gagner du FPS)
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x in range(int(cam_x//32), int((cam_x+832)//32)):
                    for y in range(int(cam_y//32), int((cam_y+632)//32)):
                        if 0 <= x < tmx_data.width and 0 <= y < tmx_data.height:
                            gid = layer.data[y][x]
                            if gid: render_surface.blit(tmx_data.get_tile_image_by_gid(gid), (x*32-cam_x, y*32-cam_y))

        # Dessin des personnages
        if boss_spawned: boss.draw(render_surface, cam_x, cam_y)
        player.draw(render_surface, cam_x, cam_y)
        
        # Dessin du HUD (Interface)
        ui.draw_hud(render_surface, player, boss, font_hud, font_big, clock, boss_spawned)
        if show_f3: ui.draw_debug_f3(render_surface, player, clock, font_hud)

        # On agrandit la petite surface (800x600) vers la taille de la fenêtre (1280x720)
        screen.blit(pygame.transform.scale(render_surface, (1280, 720)), (0, 0))
        pygame.display.flip() # Met à jour l'image à l'écran
        clock.tick(60) # Limite à 60 FPS

    pygame.quit()

if __name__ == "__main__": main()