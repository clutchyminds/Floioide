import pygame
import pytmx
import sys
import time

pygame.init()

# ===================== PARAMETRES GENERAUX =====================
# Taille d'une tuile originale (dans le tileset) et scale pour l'affichage
SCALE = 2
TILE_ORIG_W, TILE_ORIG_H = 16, 16
MAP_WIDTH, MAP_HEIGHT = 200, 200  # taille de la map en tuiles
MAP_TILE_W, MAP_TILE_H = TILE_ORIG_W * SCALE, TILE_ORIG_H * SCALE  # taille des tuiles affichées

# Taille de la fenêtre de jeu
SCREEN_W, SCREEN_H = 960, 640
fenetre = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Grow a Game")

# Chargement de la map Tiled (.tmx) avec pytmx
map_file = "ma_map.tmx"
tmx_data = pytmx.util_pygame.load_pygame(map_file)

# Police pour l'affichage des coordonnées du joueur
font_coords = pygame.font.SysFont("arial", 24)

# ============================================================
#                  OBJETS & INVENTAIRE
# ============================================================

class Item:
    """
    Représente un type d'objet (ex: potion, clé).
    - name: nom logique de l'objet
    - icon: image 32x32 pour l'affichage dans l'inventaire
    - stackable: True si l'objet peut être empilé (plusieurs dans un slot)
    """
    def __init__(self, name, icon_path, stackable=True):
        self.name = name
        self.icon = pygame.image.load(icon_path).convert_alpha()
        self.icon = pygame.transform.scale(self.icon, (32, 32))
        self.stackable = stackable


class Inventory:
    """
    Inventaire façon Minecraft simplifié:
    - 36 slots au total:
      * 0 à 26  -> sac (3 lignes de 9 slots)
      * 27 à 35 -> hotbar (barre d'inventaire en bas de l'écran)
    - gère:
      * ajout/retrait d'items
      * ouverture/fermeture de la fenêtre d'inventaire
      * drag & drop à la souris
      * sélection du slot hotbar (1-9)
    """
    def __init__(self):
        # Nombre total de slots
        self.size = 36
        self.slots = [None] * self.size  # chaque slot contient soit None, soit {"item": Item, "qty": int}
        self.open = False  # True si la fenêtre d'inventaire est ouverte

        # Etats pour le drag & drop
        self.dragging = False          # True si on est en train de déplacer un item avec la souris
        self.drag_item = None          # Item en cours de déplacement
        self.drag_qty = 0              # Quantité déplacée
        self.drag_slot_index = None    # Index du slot d'origine

        # Hotbar (barre 1-9 en bas de l'écran)
        self.selected_hotbar = 0  # index 0..8 -> correspond aux slots globaux 27..35

        # Layout de la fenêtre d'inventaire (sac 3x9)
        self.inv_cols = 9
        self.inv_rows = 3  # 3 lignes pour le sac
        self.slot_size = 40
        self.slot_margin = 6
        self.inv_width = self.inv_cols * (self.slot_size + self.slot_margin) + self.slot_margin
        self.inv_height = self.inv_rows * (self.slot_size + self.slot_margin) + self.slot_margin + 40  # +40 pour le titre

        # Polices pour texte (quantité, titre)
        self.font = pygame.font.SysFont("arial", 16)
        self.title_font = pygame.font.SysFont("arial", 22)

    # ---------- logique items de base ----------
    def add_item(self, item, qty=1):
        """
        Ajoute qty exemplaires de 'item' à l'inventaire.
        Si l'objet est stackable, essaie d'abord de le rajouter à un stack existant,
        sinon cherche un slot vide.
        Retourne True si ça a marché, False si inventaire plein.
        """
        # Essai de stack sur un slot qui contient déjà ce type d'item
        if item.stackable:
            for slot in self.slots:
                if slot is not None and slot["item"].name == item.name:
                    slot["qty"] += qty
                    return True

        # Sinon, cherche un slot vide
        for i in range(self.size):
            if self.slots[i] is None:
                self.slots[i] = {"item": item, "qty": qty}
                return True

        # Pas de place
        return False

    def remove_item(self, item_name, qty=1):
        """
        Retire qty items portant le nom 'item_name'.
        Retourne True si au moins un item a été retiré, False sinon.
        """
        for i, slot in enumerate(self.slots):
            if slot is not None and slot["item"].name == item_name:
                if slot["qty"] > qty:
                    slot["qty"] -= qty
                else:
                    self.slots[i] = None
                return True
        return False

    def has_item(self, item_name, qty=1):
        """
        Vérifie s'il y a au moins 'qty' items de type 'item_name' dans l'inventaire.
        """
        total = 0
        for slot in self.slots:
            if slot is not None and slot["item"].name == item_name:
                total += slot["qty"]
                if total >= qty:
                    return True
        return False

    # ---------- drop depuis la hotbar ----------
    def drop_from_hotbar(self, joueur_px, joueur_py):
        """
        Drop 1 item du slot hotbar sélectionné (comme Minecraft) au sol.
        - Réduit la quantité dans le slot.
        - Calcule la tuile où l'on drop (ici: la tuile du joueur).
        - Retourne (item, tile_x, tile_y) si drop, ou False si aucun item.
        NB: la création de l'objet au sol (ItemOnGround) est faite dans le main.
        """
        # Slot global correspondant à la hotbar sélectionnée
        idx = 27 + self.selected_hotbar
        slot = self.slots[idx]
        if slot is None:
            return False  # rien à drop

        item = slot["item"]

        # On enlève 1 item (comme dans Minecraft)
        slot["qty"] -= 1
        if slot["qty"] <= 0:
            self.slots[idx] = None

        # Ici on drop sur la même tuile que le joueur.
        # Tu peux ajuster pour drop devant le joueur selon la direction si tu veux.
        drop_tile_x = joueur_px // MAP_TILE_W
        drop_tile_y = joueur_py // MAP_TILE_H

        return item, drop_tile_x, drop_tile_y

    # ---------- ouverture / fermeture de la fenêtre d'inventaire ----------
    def toggle_open(self):
        """
        Ouvre/ferme la fenêtre d'inventaire.
        Si on ferme et qu'on était en train de déplacer un item, on le remet dans son slot d'origine.
        """
        self.open = not self.open
        if not self.open and self.dragging:
            if self.drag_slot_index is not None and self.drag_slot_index < self.size:
                self.slots[self.drag_slot_index] = {
                    "item": self.drag_item,
                    "qty": self.drag_qty
                }
            self.dragging = False
            self.drag_item = None
            self.drag_qty = 0
            self.drag_slot_index = None

    # ---------- gestion de la souris (drag & drop) ----------
    def get_inventory_slot_at_pos(self, mouse_pos):
        """
        Renvoie l'index de slot (0-26) si la souris clique dans la grille d'inventaire,
        ou None si on clique en dehors.
        """
        if not self.open:
            return None

        inv_x = (SCREEN_W - self.inv_width) // 2
        inv_y = (SCREEN_H - self.inv_height) // 2

        mx, my = mouse_pos
        grid_y = inv_y + 40  # 40px pour le titre au-dessus

        for row in range(self.inv_rows):
            for col in range(self.inv_cols):
                idx = row * self.inv_cols + col
                sx = inv_x + self.slot_margin + col * (self.slot_size + self.slot_margin)
                sy = grid_y + self.slot_margin + row * (self.slot_size + self.slot_margin)
                rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
                if rect.collidepoint(mx, my):
                    return idx
        return None

    def get_hotbar_slot_at_pos(self, mouse_pos):
        """
        Renvoie l'index global (27-35) si la souris clique sur la hotbar,
        ou None si en dehors.
        """
        mx, my = mouse_pos

        cols = 9
        bar_width = cols * (self.slot_size + self.slot_margin) + self.slot_margin
        x = (SCREEN_W - bar_width) // 2
        y = SCREEN_H - self.slot_size - 16  # marge bas

        for i in range(cols):
            sx = x + self.slot_margin + i * (self.slot_size + self.slot_margin)
            sy = y
            rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
            if rect.collidepoint(mx, my):
                return 27 + i
        return None

    def handle_mouse_down(self, mouse_pos, button):
        """
        Gère le clic souris (MOUSEBUTTONDOWN) pour commencer un drag & drop.
        - Si bouton gauche et clic sur un slot non vide -> on prend l'item en main (dragging).
        """
        if button != 1:
            return

        inv_idx = self.get_inventory_slot_at_pos(mouse_pos)
        hot_idx = self.get_hotbar_slot_at_pos(mouse_pos)

        slot_idx = inv_idx if inv_idx is not None else hot_idx
        if slot_idx is None:
            return

        slot = self.slots[slot_idx]
        if slot is not None:
            # On commence un drag: on retire l'item du slot et on le met "dans la souris"
            self.dragging = True
            self.drag_item = slot["item"]
            self.drag_qty = slot["qty"]
            self.drag_slot_index = slot_idx
            self.slots[slot_idx] = None

    def handle_mouse_up(self, mouse_pos, button):
        """
        Gère le relâchement de la souris (MOUSEBUTTONUP) pour poser un item (drag & drop).
        - Si on relâche sur un slot:
            * vide -> on pose
            * même type stackable -> on fusionne
            * différent -> on échange
        - Si on relâche hors des slots -> on remet l'item dans son slot d'origine.
        """
        if button != 1 or not self.dragging:
            return

        inv_idx = self.get_inventory_slot_at_pos(mouse_pos)
        hot_idx = self.get_hotbar_slot_at_pos(mouse_pos)
        target_idx = inv_idx if inv_idx is not None else hot_idx

        if target_idx is None:
            # Relâché hors des slots -> remettre dans le slot d'origine
            if self.drag_slot_index is not None and self.drag_slot_index < self.size:
                if self.slots[self.drag_slot_index] is None:
                    self.slots[self.drag_slot_index] = {
                        "item": self.drag_item,
                        "qty": self.drag_qty
                    }
                else:
                    # Si le slot d'origine n'est plus vide, on échange
                    tmp = self.slots[self.drag_slot_index]
                    self.slots[self.drag_slot_index] = {
                        "item": self.drag_item,
                        "qty": self.drag_qty
                    }
                    self.drag_item = tmp["item"]
                    self.drag_qty = tmp["qty"]
            # On arrête le drag
            self.dragging = False
            self.drag_item = None
            self.drag_qty = 0
            self.drag_slot_index = None
            return

        # Si on relâche sur un slot valide
        target_slot = self.slots[target_idx]
        if target_slot is None:
            # Slot vide: on pose l'item
            self.slots[target_idx] = {"item": self.drag_item, "qty": self.drag_qty}
        else:
            # Slot non vide
            if target_slot["item"].name == self.drag_item.name and self.drag_item.stackable:
                # Même objet et empilable -> on fusionne les quantités
                target_slot["qty"] += self.drag_qty
            else:
                # Objets différents -> on échange
                tmp = self.slots[target_idx]
                self.slots[target_idx] = {"item": self.drag_item, "qty": self.drag_qty}
                # On remet l'ancien contenu au slot d'origine si possible
                if self.drag_slot_index is not None and self.drag_slot_index < self.size:
                    self.slots[self.drag_slot_index] = tmp

        # On arrête le drag
        self.dragging = False
        self.drag_item = None
        self.drag_qty = 0
        self.drag_slot_index = None

    # ---------- hotbar sélection (touche 1-9) ----------
    def select_hotbar_index(self, index_0_to_8):
        """
        Change le slot hotbar sélectionné (0..8).
        Appelé depuis le main quand on appuie sur 1-9.
        """
        if 0 <= index_0_to_8 < 9:
            self.selected_hotbar = index_0_to_8

    # ---------- dessin inventaire + hotbar + item en drag ----------
    def draw(self, surface):
        """
        Fonction appelée à chaque frame pour dessiner:
        - la fenêtre d'inventaire (si open)
        - la hotbar
        - l'item en cours de drag sous la souris
        """
        if self.open:
            self.draw_inventory_window(surface)
        self.draw_hotbar(surface)
        self.draw_drag_item(surface)

    def draw_inventory_window(self, surface):
        """
        Dessine la fenêtre d'inventaire (sac 3x9) au centre de l'écran.
        """
        inv_x = (SCREEN_W - self.inv_width) // 2
        inv_y = (SCREEN_H - self.inv_height) // 2

        # Fond et bordure
        bg_rect = pygame.Rect(inv_x, inv_y, self.inv_width, self.inv_height)
        pygame.draw.rect(surface, (20, 20, 40), bg_rect)
        pygame.draw.rect(surface, (200, 200, 255), bg_rect, 2)

        # Titre
        title = self.title_font.render("Inventaire (I pour fermer)", True, (255, 255, 255))
        surface.blit(title, (inv_x + 10, inv_y + 8))

        # Grille de slots du sac
        grid_y = inv_y + 40
        for row in range(self.inv_rows):
            for col in range(self.inv_cols):
                idx = row * self.inv_cols + col
                sx = inv_x + self.slot_margin + col * (self.slot_size + self.slot_margin)
                sy = grid_y + self.slot_margin + row * (self.slot_size + self.slot_margin)

                rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)
                pygame.draw.rect(surface, (60, 60, 90), rect)
                pygame.draw.rect(surface, (150, 150, 220), rect, 1)

                # Si le slot contient un item, on dessine l'icône + la quantité
                slot = self.slots[idx]
                if slot is not None:
                    item = slot["item"]
                    qty = slot["qty"]
                    icon_x = sx + (self.slot_size - item.icon.get_width()) // 2
                    icon_y = sy + (self.slot_size - item.icon.get_height()) // 2
                    surface.blit(item.icon, (icon_x, icon_y))
                    txt = self.font.render(str(qty), True, (255, 255, 255))
                    surface.blit(txt, (sx + self.slot_size - txt.get_width(),
                                        sy + self.slot_size - txt.get_height()))

    def draw_hotbar(self, surface):
        """
        Dessine la hotbar en bas de l'écran (9 slots).
        Le slot sélectionné est surligné.
        """
        cols = 9
        bar_width = cols * (self.slot_size + self.slot_margin) + self.slot_margin
        x = (SCREEN_W - bar_width) // 2
        y = SCREEN_H - self.slot_size - 16

        for i in range(cols):
            idx = 27 + i  # slots globaux 27..35
            sx = x + self.slot_margin + i * (self.slot_size + self.slot_margin)
            sy = y
            rect = pygame.Rect(sx, sy, self.slot_size, self.slot_size)

            # Couleur différente si c'est le slot sélectionné
            color = (80, 80, 120)
            if i == self.selected_hotbar:
                color = (120, 120, 180)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (230, 230, 255), rect, 2)

            slot = self.slots[idx]
            if slot is not None:
                item = slot["item"]
                qty = slot["qty"]
                icon_x = sx + (self.slot_size - item.icon.get_width()) // 2
                icon_y = sy + (self.slot_size - item.icon.get_height()) // 2
                surface.blit(item.icon, (icon_x, icon_y))
                txt = self.font.render(str(qty), True, (255, 255, 255))
                surface.blit(txt, (sx + self.slot_size - txt.get_width(),
                                    sy + self.slot_size - txt.get_height()))

    def draw_drag_item(self, surface):
        """
        Si on est en train de drag un item, dessine l'icône sous la souris + quantité.
        """
        if not self.dragging or self.drag_item is None:
            return
        mx, my = pygame.mouse.get_pos()
        icon = self.drag_item.icon
        surface.blit(icon, (mx - icon.get_width() // 2, my - icon.get_height() // 2))
        txt = self.font.render(str(self.drag_qty), True, (255, 255, 255))
        surface.blit(txt, (mx + 8, my + 8))


class ItemOnGround:
    """
    Représente un objet posé au sol.
    - item: référence à l'Item
    - tile_x, tile_y: position en coordonnées de tuile
    - rect: utilisé pour détecter si le joueur est dessus (collision)
    """
    def __init__(self, item, tile_x, tile_y):
        self.item = item
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.rect = pygame.Rect(
            tile_x * MAP_TILE_W,
            tile_y * MAP_TILE_H,
            MAP_TILE_W,
            MAP_TILE_H
        )

    def draw(self, surface, camera_x, camera_y):
        """
        Dessine l'icône de l'objet au sol, en fonction de la caméra.
        """
        screen_x = self.tile_x * MAP_TILE_W - camera_x
        screen_y = self.tile_y * MAP_TILE_H - camera_y
        icon = self.item.icon
        dx = screen_x + (MAP_TILE_W - icon.get_width()) // 2
        dy = screen_y + (MAP_TILE_H - icon.get_height()) // 2
        surface.blit(icon, (dx, dy))

# ============================================================
#                  JOUEUR & ANIMATIONS
# ============================================================

def load_animation_images(prefix, nb_frames):
    """
    Charge les différentes frames d'animation d'une direction du joueur.
    Exemple: player_right_0.png, player_right_1.png, ...
    """
    images = []
    for i in range(nb_frames):
        img = pygame.image.load(f"{prefix}_{i}.png").convert_alpha()
        img = pygame.transform.scale(img, (MAP_TILE_W, MAP_TILE_H))
        images.append(img)
    return images

# Nombre de frames par direction
NB_FRAMES = 4
anim_right = load_animation_images("player_right", NB_FRAMES)
anim_left = load_animation_images("player_left", NB_FRAMES)
anim_up = load_animation_images("player_up", NB_FRAMES)
anim_down = load_animation_images("player_down", NB_FRAMES)

# Position initiale du joueur (au centre de la map, en pixels)
joueur_px = (MAP_WIDTH // 2) * MAP_TILE_W
joueur_py = (MAP_HEIGHT // 2) * MAP_TILE_H
vitesse = 2  # vitesse en pixels par frame (simple)

# Etat d'animation / direction
direction = "down"
anim_index = 0
anim_timer = 0
anim_speed = 0.12  # temps entre deux frames

# ============================================================
#                  CALQUES / COLLISIONS / TP
# ============================================================

# Noms des calques dans le fichier Tiled (.tmx)
calque_bas = "Calque 1"
calques_haut = ["Calque 2", "Calque 3", "Calque 4", "Calque 41", "Calque 5", "Calque 6", "Calque 61", "Calque 7"]
calque_collision = "Calque 2"
calque_tp4 = "Calque 4"
calque_tp41 = "Calque 41"
calque_tp6 = "Calque 6"
calque_tp61 = "Calque 61"

def pos_to_grid(px, py):
    """
    Convertit des coordonnées en pixels en coordonnées de tuile (x, y).
    """
    return int(px // MAP_TILE_W), int(py // MAP_TILE_H)

def tile_in_layer(px, py, layer_name):
    """
    Renvoie True si la tuile à la position (px, py) (en pixels)
    est non vide dans le calque 'layer_name'.
    Utilisé pour les collisions et la téléportation.
    """
    grid_x, grid_y = pos_to_grid(px, py)
    if 0 <= grid_x < MAP_WIDTH and 0 <= grid_y < MAP_HEIGHT:
        for layer in tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == layer_name:
                gid = layer.data[grid_y][grid_x]
                return gid != 0
    return False

def tile_blocking(px, py):
    """
    Renvoie True si la tuile est bloquante (collision).
    """
    return tile_in_layer(px, py, calque_collision)

def tile_tp4(px, py):
    return tile_in_layer(px, py, calque_tp4)

def tile_tp41(px, py):
    return tile_in_layer(px, py, calque_tp41)

def tile_tp6(px, py):
    return tile_in_layer(px, py, calque_tp6)

def tile_tp61(px, py):
    return tile_in_layer(px, py, calque_tp61)

# ============================================================
#                  MENU & ECRAN DE REGLES
# ============================================================

def afficher_regles(fenetre):
    """
    Affiche un écran simple avec les règles du jeu.
    On en sort avec ESC, Entrée ou clic.
    """
    font = pygame.font.SysFont("arial", 32)
    petit = pygame.font.SysFont("arial", 25)
    en_regles = True
    while en_regles:
        fenetre.fill((25, 30, 50))
        titre = font.render("Règles du jeu", True, (250, 230, 80))
        ligne1 = petit.render("Déplace-toi avec les flèches. Evite les obstacles.", True, (230, 230, 250))
        ligne2 = petit.render("Tu peux te téléporter sur les tuiles spéciales.", True, (230, 230, 250))
        ligne3 = petit.render("Appuie sur ESC ou Retour pour revenir au menu.", True, (220, 220, 220))

        fenetre.blit(titre, (SCREEN_W // 2 - titre.get_width() // 2, 130))
        fenetre.blit(ligne1, (SCREEN_W // 2 - ligne1.get_width() // 2, 220))
        fenetre.blit(ligne2, (SCREEN_W // 2 - ligne2.get_width() // 2, 260))
        fenetre.blit(ligne3, (SCREEN_W // 2 - ligne3.get_width() // 2, 340))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN):
                en_regles = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                en_regles = False

def afficher_menu(fenetre):
    """
    Affiche un menu simple avec 2 boutons: Jouer / Règles.
    Navigation possible à la souris ou au clavier (flèches + Entrée).
    """
    font = pygame.font.SysFont("arial", 52)
    font_btn = pygame.font.SysFont("arial", 36)
    btn_jouer = pygame.Rect(SCREEN_W//2 - 105, 300, 210, 60)
    btn_regles = pygame.Rect(SCREEN_W//2 - 105, 380, 210, 60)
    selected = 0

    while True:
        fenetre.fill((30, 30, 50))
        titre = font.render("Grow a Game", True, (255, 255, 255))
        fenetre.blit(titre, (SCREEN_W // 2 - titre.get_width() // 2, 130))
        mouse_pos = pygame.mouse.get_pos()

        # Dessin des boutons avec surbrillance
        for i, (rect, txt) in enumerate([(btn_jouer, "Jouer"), (btn_regles, "Règles")]):
            color = (90, 180, 220) if rect.collidepoint(mouse_pos) or selected == i else (120, 120, 180)
            pygame.draw.rect(fenetre, color, rect, border_radius=8)
            label = font_btn.render(txt, True, (255, 255, 255))
            fenetre.blit(label, (rect.x + rect.width // 2 - label.get_width() // 2,
                                 rect.y + rect.height // 2 - label.get_height() // 2))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = max(0, selected - 1)
                if event.key == pygame.K_DOWN:
                    selected = min(1, selected + 1)
                if event.key == pygame.K_RETURN:
                    if selected == 0:
                        return  # démarrer le jeu
                    elif selected == 1:
                        afficher_regles(fenetre)
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_jouer.collidepoint(event.pos):
                    return
                elif btn_regles.collidepoint(event.pos):
                    afficher_regles(fenetre)

# ============================================================
#                  INITIALISATION INVENTAIRE & OBJETS
# ============================================================

# Création de l'inventaire du joueur
inventaire = Inventory()

# Création de quelques types d'objets (adapte les chemins d'image à ton projet)
potion = Item("Potion", "items/potion.png", stackable=True)
cle_maison = Item("Cle maison", "items/cle.png", stackable=False)

# On donne 2 potions au joueur au départ, par exemple
inventaire.add_item(potion, qty=2)

# Liste des objets actuellement au sol
items_sol = []
items_sol.append(ItemOnGround(potion, 100, 100))      # potion sur la tuile (100, 100)
items_sol.append(ItemOnGround(cle_maison, 105, 100))  # clé sur la tuile (105, 100)

# ============================================================
#                  DEMARRAGE DU JEU
# ============================================================

clock = pygame.time.Clock()
afficher_menu(fenetre)  # affiche le menu principal au lancement

last_time = time.time()  # pour calculer dt (delta time)

# ============================================================
#                  BOUCLE PRINCIPALE
# ============================================================

en_cours = True
while en_cours:
    # Calcul du delta temps (temps écoulé depuis la frame précédente)
    now = time.time()
    dt = now - last_time
    last_time = now

    # ----------------- GESTION EVENEMENTS -----------------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            en_cours = False

        if event.type == pygame.KEYDOWN:
            # Quitter avec ESC
            if event.key == pygame.K_ESCAPE:
                en_cours = False

            # Ouvrir / fermer l'inventaire avec I
            if event.key == pygame.K_i:
                inventaire.toggle_open()

            # Changer le slot sélectionné de la hotbar avec 1-9
            if pygame.K_1 <= event.key <= pygame.K_9:
                index = event.key - pygame.K_1  # 0..8
                inventaire.select_hotbar_index(index)

            # Drop l'item du slot hotbar sélectionné avec Q
            if event.key == pygame.K_q:
                res = inventaire.drop_from_hotbar(joueur_px, joueur_py)
                if res:
                    item, tx, ty = res
                    items_sol.append(ItemOnGround(item, tx, ty))
                    print(f"Item droppé: {item.name}")

        # Drag & drop dans l'inventaire / hotbar avec la souris
        if event.type == pygame.MOUSEBUTTONDOWN:
            inventaire.handle_mouse_down(event.pos, event.button)
        if event.type == pygame.MOUSEBUTTONUP:
            inventaire.handle_mouse_up(event.pos, event.button)

    # ----------------- INPUT CLAVIER CONTINU (déplacement) -----------------
    touches = pygame.key.get_pressed()
    nx, ny = joueur_px, joueur_py  # nouvelles coordonnées potentielles

    moved = False
    if touches[pygame.K_LEFT]:
        direction = "left"
        if not tile_blocking(nx - vitesse, ny):
            nx -= vitesse
            moved = True
    elif touches[pygame.K_RIGHT]:
        direction = "right"
        if not tile_blocking(nx + vitesse + MAP_TILE_W - 1, ny):
            nx += vitesse
            moved = True
    elif touches[pygame.K_UP]:
        direction = "up"
        if not tile_blocking(nx, ny - vitesse):
            ny -= vitesse
            moved = True
    elif touches[pygame.K_DOWN]:
        direction = "down"
        if not tile_blocking(nx, ny + vitesse + MAP_TILE_H - 1):
            ny += vitesse
            moved = True

    # Limite les coordonnées du joueur dans la map
    nx = max(0, min(nx, MAP_WIDTH * MAP_TILE_W - MAP_TILE_W))
    ny = max(0, min(ny, MAP_HEIGHT * MAP_TILE_H - MAP_TILE_H))
    joueur_px, joueur_py = nx, ny

    # ----------------- ANIMATION DU JOUEUR -----------------
    if moved:
        anim_timer += dt
        if anim_timer >= anim_speed:
            anim_index = (anim_index + 1) % NB_FRAMES
            anim_timer = 0
    else:
        anim_index = 0  # immobile -> première frame

    if direction == "left":
        image_affiche = anim_left[anim_index]
    elif direction == "right":
        image_affiche = anim_right[anim_index]
    elif direction == "up":
        image_affiche = anim_up[anim_index]
    else:
        image_affiche = anim_down[anim_index]

    # ----------------- COLLISION AVEC OBJETS AU SOL (RAMASSER) -----------------
    # Rect du joueur pour la collision avec les items
    joueur_rect = pygame.Rect(joueur_px, joueur_py, MAP_TILE_W, MAP_TILE_H)

    # Si le joueur maintient la touche E, il ramasse les objets présents sur sa case
    if touches[pygame.K_e]:
        for item_ground in items_sol[:]:  # copie pour pouvoir enlever pendant la boucle
            if joueur_rect.colliderect(item_ground.rect):
                pris = inventaire.add_item(item_ground.item, qty=1)
                if pris:
                    items_sol.remove(item_ground)
                    print(f"Ramassé: {item_ground.item.name}")
                else:
                    print("Inventaire plein !")

    # ----------------- TELEPORTATIONS -----------------
    if tile_tp4(joueur_px, joueur_py):
        dest_x, dest_y = 107, 73
        joueur_px = dest_x * MAP_TILE_W
        joueur_py = dest_y * MAP_TILE_H
        print("Téléportation !")

    if tile_tp41(joueur_px, joueur_py):
        dest_x, dest_y = 92, 98
        joueur_px = dest_x * MAP_TILE_W
        joueur_py = dest_y * MAP_TILE_H
        print("Téléportation !")

    if tile_tp6(joueur_px, joueur_py):
        dest_x, dest_y = 171, 123
        joueur_px = dest_x * MAP_TILE_W
        joueur_py = dest_y * MAP_TILE_H
        print("Téléportation !")

    if tile_tp61(joueur_px, joueur_py):
        dest_x, dest_y = 121, 94
        joueur_px = dest_x * MAP_TILE_W
        joueur_py = dest_y * MAP_TILE_H
        print("Téléportation !")

    # ----------------- CAMERA -----------------
    # La caméra est centrée sur le joueur
    camera_x = joueur_px - SCREEN_W // 2 + MAP_TILE_W // 2
    camera_y = joueur_py - SCREEN_H // 2 + MAP_TILE_H // 2

    # On empêche la caméra de sortir de la map
    camera_x = max(0, min(camera_x, MAP_WIDTH * MAP_TILE_W - SCREEN_W))
    camera_y = max(0, min(camera_y, MAP_HEIGHT * MAP_TILE_H - SCREEN_H))

    # ----------------- RENDU (DESSIN) -----------------
    fenetre.fill((0, 0, 0))

    # Calcul des tuiles visibles à l'écran pour ne pas tout dessiner
    visible_tile_x = SCREEN_W // MAP_TILE_W + 2
    visible_tile_y = SCREEN_H // MAP_TILE_H + 2
    first_tile_x = camera_x // MAP_TILE_W
    first_tile_y = camera_y // MAP_TILE_H

    # Dessin de la carte (calque bas + calques haut)
    for y in range(first_tile_y, first_tile_y + visible_tile_y):
        for x in range(first_tile_x, first_tile_x + visible_tile_x):
            if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                # Calque "bas"
                for layer in tmx_data.visible_layers:
                    if isinstance(layer, pytmx.TiledTileLayer) and layer.name == calque_bas:
                        gid = layer.data[y][x]
                        if gid != 0:
                            image = tmx_data.get_tile_image_by_gid(gid)
                            if image:
                                image = pygame.transform.scale(image, (MAP_TILE_W, MAP_TILE_H))
                                fenetre.blit(image, (x * MAP_TILE_W - camera_x, y * MAP_TILE_H - camera_y))
                # Calques "haut" (dessinés par-dessus le joueur)
                for layer in tmx_data.visible_layers:
                    if isinstance(layer, pytmx.TiledTileLayer) and layer.name in calques_haut:
                        gid = layer.data[y][x]
                        if gid != 0:
                            image = tmx_data.get_tile_image_by_gid(gid)
                            if image:
                                image = pygame.transform.scale(image, (MAP_TILE_W, MAP_TILE_H))
                                fenetre.blit(image, (x * MAP_TILE_W - camera_x, y * MAP_TILE_H - camera_y))

    # Dessin des objets au sol
    for item_ground in items_sol:
        item_ground.draw(fenetre, camera_x, camera_y)

    # Dessin du joueur (toujours au centre de l'écran)
    fenetre.blit(image_affiche, (SCREEN_W // 2 - MAP_TILE_W // 2, SCREEN_H // 2 - MAP_TILE_H // 2))

    # Affichage des coordonnées du joueur (en tuiles)
    coord_text = font_coords.render(f"X: {joueur_px // MAP_TILE_W}  Y: {joueur_py // MAP_TILE_H}", True, (255, 255, 0))
    fenetre.blit(coord_text, (SCREEN_W - coord_text.get_width() - 20, 20))

    # Dessin de l'inventaire (fenêtre + hotbar + item en drag)
    inventaire.draw(fenetre)

    # Flip de l'écran pour afficher tout ce qui a été dessiné
    pygame.display.flip()
    clock.tick(60)  # limite à 60 FPS

pygame.quit()
