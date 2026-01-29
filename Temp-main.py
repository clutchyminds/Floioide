import pygame, sys, pytmx
from settings import *
from player import Player
from boss import Boss

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    render_surf = pygame.Surface(INTERNAL_RES)
    clock = pygame.time.Clock()
    f_debug = pygame.font.Font(None, 20)
    f_hud = pygame.font.Font(None, 24)

    player = Player(100, 100)
    boss = Boss(15, 10, 32)
    tmx_data = pytmx.load_pygame(MAP_FILE)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

        # Update
        player.update([], [], boss)
        boss.update([])
        cam_x = max(0, min(player.rect.centerx - 400, tmx_data.width*32 - 800))
        cam_y = max(0, min(player.rect.centery - 300, tmx_data.height*32 - 600))

        # Dessin
        render_surf.fill((20, 20, 25))
        boss.draw(render_surf, cam_x, cam_y)
        player.draw(render_surf, cam_x, cam_y)

        # --- HUD : BARRE XP ---
        bx, by, bw, bh = 20, 20, 150, 12
        pygame.draw.rect(render_surf, (50, 50, 50), (bx, by, bw, bh))
        pygame.draw.rect(render_surf, (0, 200, 255), (bx, by, int(bw * (player.exp/player.exp_needed)), bh))
        render_surf.blit(f_hud.render(f"LVL {player.level}", True, (255, 255, 255)), (bx, by + 15))

        # --- DEBUG MENU (Haut Droite) ---
        infos = [f"FPS: {int(clock.get_fps())}", f"X: {player.rect.x} Y: {player.rect.y}", f"Boss HP: {boss.hp}"]
        for i, txt in enumerate(infos):
            s = f_debug.render(txt, True, (0, 255, 150))
            render_surf.blit(s, (INTERNAL_RES[0] - s.get_width() - 10, 10 + i*18))

        screen.blit(pygame.transform.scale(render_surf, (WIN_W, WIN_H)), (0,0))
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__": main()