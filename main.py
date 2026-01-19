import pygame

pygame.init()
LARGEUR, HAUTEUR = 800, 600
ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
pygame.display.set_caption("Platformer NSI")
clock = pygame.time.Clock()

# ===== CONSTANTES =====
GRAVITE = 0.8
SAUT_FORCE = -15
DEATH_Y = 800

TILE_W = 200
TILE_H = 40

# ===== IMAGES =====
background_img = pygame.image.load("assets/background.png").convert()
background_img = pygame.transform.scale(background_img, (LARGEUR, HAUTEUR))

player_img = pygame.image.load("assets/player.png").convert_alpha()
player_img = pygame.transform.scale(player_img, (40, 60))

platform_img = pygame.image.load("assets/platform.png").convert_alpha()
platform_img = pygame.transform.scale(platform_img, (TILE_W, TILE_H))

# ===== POLICE POUR LE TEXTE =====
font = pygame.font.SysFont(None, 24)  # petite police par défaut [web:105]

# ===== JOUEUR =====
player_x = 100
player_y = 300
vx = 0
vy = 0

player_rect = player_img.get_rect()
player_rect.x = player_x
player_rect.y = player_y

# ===== PLATEFORMES =====
blocs_coords = [
    (-600, 500),
    (-400, 500),
    (-200, 500),
    (0,    500),
    (200,  500),
    (400,  500),
    (600,  500),
    (800,  500),

    (200,  400),
    (600,  350),
]

plateformes = []
for bx, by in blocs_coords:
    plateformes.append(pygame.Rect(bx, by, TILE_W, TILE_H))

# ===== CAMERA =====
camera_x = 0
camera_y = 0


def respawn():
    global player_x, player_y, vx, vy, player_rect
    player_x = 100
    player_y = 300
    vx = 0
    vy = 0
    player_rect.x = player_x
    player_rect.y = player_y


def appliquer_gravite():
    global vy
    vy += GRAVITE


def deplacer_joueur():
    global player_x, player_y, player_rect
    player_x += vx
    player_y += vy
    player_rect.x = player_x
    player_rect.y = player_y


def gerer_collisions():
    """Collision plateforme : par le dessus, par le dessous, et un peu sur les côtés."""
    global player_x, player_y, vx, vy, player_rect
    au_sol = False

    for p in plateformes:
        if player_rect.colliderect(p):

            # on calcule les chevauchements sur chaque côté [web:100]
            dx_droite = p.right - player_rect.left
            dx_gauche = player_rect.right - p.left
            dy_bas = p.bottom - player_rect.top
            dy_haut = player_rect.bottom - p.top

            # on regarde où la collision est la plus "petite"
            min_overlap = min(dx_droite, dx_gauche, dy_bas, dy_haut)

            if min_overlap == dy_haut and vy > 0:
                # le joueur arrive d'en haut -> posé sur la plateforme
                player_rect.bottom = p.top
                player_y = player_rect.y
                vy = 0
                au_sol = True
            elif min_overlap == dy_bas and vy < 0:
                # collision par dessous -> on bloque, il ne traverse pas
                player_rect.top = p.bottom
                player_y = player_rect.y
                vy = 0
            elif min_overlap == dx_droite and vx < 0:
                # collision sur la droite -> on bloque horizontalement
                player_rect.left = p.right
                player_x = player_rect.x
                vx = 0
            elif min_overlap == dx_gauche and vx > 0:
                # collision sur la gauche
                player_rect.right = p.left
                player_x = player_rect.x
                vx = 0

    return au_sol


def mettre_a_jour_camera():
    global camera_x, camera_y
    camera_x = player_x - LARGEUR // 2
    camera_y = player_y - HAUTEUR // 2


def dessiner():
    # fond fixe (pas d’offset ni caméra)
    ecran.blit(background_img, (0, 0))

    # offset pour le monde
    offset_x = -camera_x
    offset_y = -camera_y

    # plateformes
    for p in plateformes:
        ecran.blit(platform_img, (p.x + offset_x, p.y + offset_y))

    # joueur
    ecran.blit(player_img, (player_rect.x + offset_x, player_rect.y + offset_y))

    # texte coordonnées joueur en haut à gauche (coord monde)
    txt = f"x={int(player_x)}  y={int(player_y)}"
    img_txt = font.render(txt, True, (255, 255, 255))  # blanc [web:105]
    ecran.blit(img_txt, (10, 10))


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # clavier
    touches = pygame.key.get_pressed()
    vx = 0
    if touches[pygame.K_LEFT]:
        vx = -5
    if touches[pygame.K_RIGHT]:
        vx = 5
    demande_saut = touches[pygame.K_SPACE]

    # physique
    appliquer_gravite()
    deplacer_joueur()
    au_sol = gerer_collisions()

    if demande_saut and au_sol:
        vy = SAUT_FORCE

    if player_y > DEATH_Y:
        respawn()

    mettre_a_jour_camera()

    dessiner()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
