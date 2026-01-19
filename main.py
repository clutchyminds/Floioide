import pygame

pygame.init()

ecran = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
player_rect = pygame.Rect(400, 300, 40, 60)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    ecran.fill((0,0,0))
    pygame.draw.rect(ecran, (0,0,255), player_rect)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
