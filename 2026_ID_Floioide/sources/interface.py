import os
import arcade
import math
from sources.constantes import LARGEUR, HAUTEUR, DOSSIER_DATA

class HUD:
    def __init__(self):
        self.barre_vie_couleur = arcade.color.RED
        self.eau_couleur = arcade.color.AZURE_MIST
        self.dash_couleur = arcade.color.GOLD
        chemin_vies = os.path.join(DOSSIER_DATA, "player", "vies")
        self.tex_plein = arcade.load_texture(os.path.join(chemin_vies, "vie1.png"))
        self.tex_demi = arcade.load_texture(os.path.join(chemin_vies, "vie0.5.png"))
        self.tex_vide = arcade.load_texture(os.path.join(chemin_vies, "vie0.png"))
        
    def dessiner(self, joueur):
        # --- AFFICHAGE DES 10 CŒURS ---
        x_depart = 40
        y_position = HAUTEUR - 40
        espacement = 35 
        
        for i in range(10):
            seuil_vie = (i * 2) + 1
            x_actuel = x_depart + (i * espacement)
            
            if joueur.vie >= seuil_vie + 1:
                texture = self.tex_plein
            elif joueur.vie == seuil_vie:
                texture = self.tex_demi
            else:
                texture = self.tex_vide
            
            arcade.draw_texture_rect(
                texture=texture,
                rect=arcade.rect.XYWH(x_actuel, y_position, 30, 30)
            )

        # --- JAUGE D'EAU (Cercle) ---
        centre_eau_x, centre_eau_y = 60, HAUTEUR - 100
        rayon = 30
        arcade.draw_circle_filled(centre_eau_x, centre_eau_y, rayon, arcade.color.DARK_GRAY)
        
        if joueur.eau > 0:
            angle_remplissage = (joueur.eau / 100) * 360
            arcade.draw_arc_filled(
                centre_eau_x, centre_eau_y, rayon*2, rayon*2, 
                self.eau_couleur, 90 - angle_remplissage, 90
            )
        arcade.draw_text("H2O", centre_eau_x - 15, centre_eau_y - 5, arcade.color.WHITE, 10, bold=True)

        # --- 3. RECHARGEMENT DASH (Triangle) ---
        centre_dash_x, centre_dash_y = 140, HAUTEUR - 100
        taille_tri = 35

        # Points du triangle
        p1 = (centre_dash_x, centre_dash_y + taille_tri)
        p2 = (centre_dash_x - taille_tri, centre_dash_y - taille_tri)
        p3 = (centre_dash_x + taille_tri, centre_dash_y - taille_tri)

        # Fond
        arcade.draw_polygon_filled([p1, p2, p3], arcade.color.DARK_GRAY)

        # Progression (Remplacement du triangle partiel par un contour ou un remplissage simple)
        progression_dash = max(0.0, min(1.0, 1 - (joueur.timer_dash / 7.0)))

        if progression_dash >= 1.0:
            arcade.draw_polygon_filled([p1, p2, p3], self.dash_couleur)
        elif progression_dash > 0:
            # On dessine un contour qui se remplit ou change de couleur
            arcade.draw_polygon_outline([p1, p2, p3], self.dash_couleur, 2)
    
    def dessiner_inventaire_et_monnaie(self, joueur):
        """ Affiche la monnaie et les 5 slots d'inventaire """
        # Affichage Monnaie (Haut droite)
        arcade.draw_text(f"Monnaie : {joueur.monnaie}", LARGEUR - 180, HAUTEUR - 40, arcade.color.GOLD, 16, bold=True)

        # Affichage Inventaire (Bas Centre)
        taille_slot = 60
        espacement = 10
        debut_x = (LARGEUR - (5 * taille_slot + 4 * espacement)) / 2
        y = 40

        for i in range(5):
            posX = debut_x + i * (taille_slot + espacement)
            # On définit le rectangle par son coin bas-gauche (LBWH : Left, Bottom, Width, Height)
            slot_rect = arcade.rect.LBWH(posX, y, taille_slot, taille_slot)
            
            # Fond du slot
            arcade.draw_rect_filled(rect=slot_rect, color=(30, 30, 30, 200))
            # Bordure
            arcade.draw_rect_outline(rect=slot_rect, color=arcade.color.WHITE, border_width=2)

class InterfaceShop:
    def __init__(self):
        self.ouvert = False
        self.largeur = 500
        self.hauteur = 400
        
        # On garde une trace de l'élément survolé pour l'effet de zoom
        self.index_survole = -1 
        self.croix_survolee = False

        # Chemins (adaptés à ton arborescence)
        chemin_pnj = os.path.join(DOSSIER_DATA, "mobs", "PNJ")
        chemin_items = os.path.join(chemin_pnj, "items")
        
        # Chargement textures
        self.tex_gui = arcade.load_texture(os.path.join(chemin_pnj, "gui.png"))
        self.tex_bouton = arcade.load_texture(os.path.join(chemin_pnj, "boutton1.png"))
        # Pour la croix, on peut utiliser une texture ou un simple texte "X"
        # self.tex_croix = arcade.load_texture(os.path.join(chemin_pnj, "croix.png"))

        self.items_en_vente = [
            {"nom": "Graine de vie", "prix": 10, "texture": arcade.load_texture(os.path.join(chemin_items, "test.png"))},
            {"nom": "Engrais Turbo", "prix": 25, "texture": arcade.load_texture(os.path.join(chemin_items, "test.png"))}
        ]

    def update_souris(self, x, y):
        """Appelé depuis main.py pour mettre à jour les effets de survol"""
        if not self.ouvert:
            return

        cx, cy = LARGEUR / 2, HAUTEUR / 2
        self.index_survole = -1
        self.croix_survolee = False

        # 1. Détection survol des boutons d'items
        for i in range(len(self.items_en_vente)):
            y_item = cy + 60 - (i * 80)
            # On crée un rectangle imaginaire pour la zone du bouton (400x60)
            if cx - 200 < x < cx + 200 and y_item - 30 < y < y_item + 30:
                self.index_survole = i

        # 2. Détection survol de la croix (en haut à droite du GUI)
        if cx + 210 < x < cx + 240 and cy + 170 < y < cy + 195:
            self.croix_survolee = True

    def dessiner(self):
        if not self.ouvert:
            return

        cx, cy = LARGEUR / 2, HAUTEUR / 2
        
        # FOND DU MENU
        arcade.draw_texture_rect(self.tex_gui, arcade.rect.XYWH(cx, cy, self.largeur, self.hauteur))

        # LA CROIX DE FERMETURE
        couleur_croix = arcade.color.RED if self.croix_survolee else arcade.color.WHITE
        taille_croix = 25 if self.croix_survolee else 20
        arcade.draw_text("X", cx + 225, cy + 180, couleur_croix, taille_croix, anchor_x="center", anchor_y="center", bold=True)

        # AFFICHAGE DES OBJETS
        for i, item in enumerate(self.items_en_vente):
            y_item = cy + 60 - (i * 80)
            
            # Calcul du coefficient de grossissement (scale)
            # Si survolé, on multiplie la taille par 1.05 (5% plus gros)
            coeff = 1.05 if self.index_survole == i else 1.0
            
            # Dessin du bouton avec le coefficient
            arcade.draw_texture_rect(
                texture=self.tex_bouton,
                rect=arcade.rect.XYWH(cx, y_item, 400 * coeff, 60 * coeff)
            )
            
            # Icône de l'objet
            arcade.draw_texture_rect(
                texture=item["texture"],
                rect=arcade.rect.XYWH(cx - 150, y_item, 40 * coeff, 40 * coeff)
            )
            
            # Texte (on augmente un peu la taille de police si survolé)
            taille_police = 16 if self.index_survole == i else 14
            arcade.draw_text(f"{item['nom']} : {item['prix']} $", cx - 90, y_item - 6, arcade.color.WHITE, taille_police)