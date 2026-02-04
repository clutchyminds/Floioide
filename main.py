import pygame
import pytmx
import settings
from entities import Player, Boss, Particle, RainParticle
import ui
import random

# --- FONCTION POUR LE HALO JAUNE (FONDU PROGRESSIF) ---
def create_light_halo(radius):
    surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        # Calcul de l'alpha pour le fondu
        alpha = int(255 * (1 - (r / radius)**1.1)) 
        
        # COULEUR JAUNE LÉGER : (Rouge, Vert, Bleu)
        # On garde beaucoup de rouge, un peu moins de vert, et peu de bleu
        color = (alpha, int(alpha * 0.85), int(alpha * 0.5))
        
        pygame.draw.circle(surface, color, (radius, radius), r)
    return surface

def main():
    pygame.init()
    screen = pygame.display.set_mode((settings.WIN_W, settings.WIN_H))
    render_surface = pygame.Surface(settings.INTERNAL_RES)
    light_mask = pygame.Surface(settings.INTERNAL_RES)
    
    clock = pygame.time.Clock()
    font_hud = pygame.font.Font(None, 24)
    font_big = pygame.font.Font(None, 50)

    # Zone de lumière encore plus grande et plus douce
    halo_radius = 280  
    halo_img = create_light_halo(halo_radius)

    def reset_game():
        tm = pytmx.load_pygame(settings.MAP_FILE)
        p, b = Player(100, 100), Boss(29, 92, 32)
        return tm, p, b

    tmx_data, player, boss = reset_game()
    particles = [] 
    collision_tiles = []
    spawn_trigger_tiles = []
    
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid:
                    rect = pygame.Rect(x*32, y*32, 32, 32)
                    if layer.name == "hit-box": collision_tiles.append(rect)
                    elif layer.name == "boss-test": spawn_trigger_tiles.append(rect)

    boss_spawned, show_f3, running = False, False, True
    lightning_seq = []
    lightning_timer = 0

    while running:
        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width*32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height*32 - 600))
        
        m_pos = pygame.mouse.get_pos()
        mx, my = (m_pos[0] * 800 / 1280) + cam_x, (m_pos[1] * 600 / 720) + cam_y
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: ui.show_pause_menu(screen, font_big)
                if event.key == pygame.K_F3: show_f3 = not show_f3

        if not boss_spawned:
            for t in spawn_trigger_tiles:
                if player.rect.colliderect(t): boss_spawned = True; break

        player.update(pygame.key.get_pressed(), pygame.mouse.get_pressed(), collision_tiles, boss, (mx, my), particles)
        if boss_spawned: boss.update(collision_tiles, player)
        
        if player.hp <= 0:
            ui.show_game_over(screen, font_big)
            tmx_data, player, boss = reset_game(); boss_spawned = False; particles = []

        # --- DESSIN DU MONDE ---
        render_surface.fill((20, 20, 25)) 
        
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x in range(int(cam_x//32), int((cam_x+832)//32)):
                    for y in range(int(cam_y//32), int((cam_y+632)//32)):
                        if 0 <= x < tmx_data.width and 0 <= y < tmx_data.height:
                            gid = layer.data[y][x]
                            if gid: render_surface.blit(tmx_data.get_tile_image_by_gid(gid), (x*32-cam_x, y*32-cam_y))

        if boss_spawned: boss.draw(render_surface, cam_x, cam_y)
        player.draw(render_surface, cam_x, cam_y)

        # PLUIE
        if cam_y < 10000 and len(particles) < 500:
            for _ in range(12):
                if random.random() > 0.4:
                    particles.append(RainParticle(random.randint(int(cam_x-50), int(cam_x+850)), cam_y-20))

        active_tiles = [t for t in collision_tiles if pygame.Rect(cam_x-32, cam_y-32, 864, 664).colliderect(t)]

        for p in particles[:]:
            if isinstance(p, RainParticle): p.update(active_tiles, particles)
            else: p.update()
            if p.lifetime <= 0 or (isinstance(p, RainParticle) and not p.alive):
                if p in particles: particles.remove(p)
            else: p.draw(render_surface, cam_x, cam_y)

        # --- SYSTÈME DE LUMIÈRE JAUNE ---
        light_mask.fill((10, 10, 15)) 
        
        # Gestion des éclairs saccadés
        lightning_timer -= 1
        if not lightning_seq and lightning_timer <= 0:
            if random.random() > 0.997:
                lightning_seq = [255, 0, 180, 0, 0, 80, 0]
                lightning_timer = 180

        flash_val = 0
        if lightning_seq:
            flash_val = lightning_seq.pop(0)
            light_mask.fill((flash_val//2 + 10, flash_val//2 + 10, flash_val//2 + 20))

        # Dessin du halo JAUNE
        px, py = player.rect.centerx - cam_x, player.rect.centery - cam_y
        # BLEND_RGBA_ADD permet au jaune de s'ajouter sur l'obscurité
        light_mask.blit(halo_img, (px - halo_radius, py - halo_radius), special_flags=pygame.BLEND_RGBA_ADD)

        # Fusion finale (Multiplier le jeu par le masque de lumière)
        render_surface.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        # HUD
        ui.draw_hud(render_surface, player, boss, font_hud, font_big, clock, boss_spawned)
        if show_f3: ui.draw_debug_f3(render_surface, player, clock, font_hud)

        screen.blit(pygame.transform.scale(render_surface, (1280, 720)), (0, 0))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__": main()