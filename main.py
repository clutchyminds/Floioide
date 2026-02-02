import pygame
import pytmx
import settings
from entities import Player, Boss
import ui

def main():
    pygame.init()
    screen = pygame.display.set_mode((settings.WIN_W, settings.WIN_H))
    render_surface = pygame.Surface(settings.INTERNAL_RES)
    clock, font_hud, font_big = pygame.time.Clock(), pygame.font.Font(None, 24), pygame.font.Font(None, 50)

    def reset_game():
        tm = pytmx.load_pygame(settings.MAP_FILE)
        p, b = Player(100, 100), Boss(29, 92, 32)
        return tm, p, b

    tmx_data, player, boss = reset_game()
    collision_tiles, spawn_trigger_tiles = [], []
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid:
                    rect = pygame.Rect(x*32, y*32, 32, 32)
                    if layer.name == "hit-box": collision_tiles.append(rect)
                    elif layer.name == "boss-test": spawn_trigger_tiles.append(rect)

    boss_spawned, show_f3, running = False, False, True

    while running:
        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width*32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height*32 - 600))
        m_pos = pygame.mouse.get_pos()
        # Calcul des coordonnées monde pour la souris
        mx = (m_pos[0] * 800 / 1280) + cam_x
        my = (m_pos[1] * 600 / 720) + cam_y
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: ui.show_pause_menu(screen, font_big)
                if event.key == pygame.K_F3: show_f3 = not show_f3

        if not boss_spawned:
            for t in spawn_trigger_tiles:
                if player.rect.colliderect(t): boss_spawned = True; break

        player.update(pygame.key.get_pressed(), pygame.mouse.get_pressed(), collision_tiles, boss, (mx, my))
        if boss_spawned: boss.update(collision_tiles, player)
        
        if player.hp <= 0:
            ui.show_game_over(screen, font_big)
            tmx_data, player, boss = reset_game(); boss_spawned = False

        render_surface.fill((25, 25, 30))
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x in range(int(cam_x//32), int((cam_x+832)//32)):
                    for y in range(int(cam_y//32), int((cam_y+632)//32)):
                        if 0 <= x < tmx_data.width and 0 <= y < tmx_data.height:
                            gid = layer.data[y][x]
                            if gid: render_surface.blit(tmx_data.get_tile_image_by_gid(gid), (x*32-cam_x, y*32-cam_y))

        if boss_spawned: boss.draw(render_surface, cam_x, cam_y)
        player.draw(render_surface, cam_x, cam_y)
        ui.draw_hud(render_surface, player, boss, font_hud, font_big, clock, boss_spawned)
        if show_f3: ui.draw_debug_f3(render_surface, player, clock, font_hud)

        screen.blit(pygame.transform.scale(render_surface, (1280, 720)), (0, 0))
        pygame.display.flip(); clock.tick(60)
    pygame.quit()

if __name__ == "__main__": main()