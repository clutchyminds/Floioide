import pygame

def load_img(path, scale):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
    except:
        s = pygame.Surface((64, 64)); s.fill((255, 0, 50)); return s