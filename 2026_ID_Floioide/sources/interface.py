import os
import arcade
import math
from sources.constantes import LARGEUR, HAUTEUR, DOSSIER_DATA

class HUD:
    def __init__(self):
        # --- TES CŒURS ---
        chemin_vies = os.path.join(DOSSIER_DATA, "player", "vies")
        self.tex_plein = arcade.load_texture(os.path.join(chemin_vies, "vie1.png"))
        self.tex_demi = arcade.load_texture(os.path.join(chemin_vies, "vie0.5.png"))
        self.tex_vide = arcade.load_texture(os.path.join(chemin_vies, "vie0.png"))
        
        # --- CHARGEMENT DES 5 SPRITES D'EAU ---
        self.tex_eau = {}
        chemin_eau = os.path.join(DOSSIER_DATA, "player", "barres", "eau")
        for p in [0, 25, 50, 75, 100]:
            self.tex_eau[p] = arcade.load_texture(os.path.join(chemin_eau, f"{p}.png"))

        # --- CHARGEMENT DES 5 SPRITES D'ENERGIE ---
        self.tex_nrj = {}
        chemin_nrj = os.path.join(DOSSIER_DATA, "player", "barres", "nrj")
        for p in [0, 25, 50, 75, 100]:
            self.tex_nrj[p] = arcade.load_texture(os.path.join(chemin_nrj, f"{p}.png"))

    def get_texture(self, dictionnaire, valeur):
        """Prend un dictionnaire (eau ou nrj) et renvoie le bon palier"""
        if valeur >= 100: return dictionnaire[100]
        if valeur >= 75:  return dictionnaire[75]
        if valeur >= 50:  return dictionnaire[50]
        if valeur >= 25:  return dictionnaire[25]
        return dictionnaire[0]

    def dessiner(self, joueur):
        # 1. AFFICHAGE DES 10 CŒURS
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
                
            arcade.draw_texture_rect(texture, arcade.rect.XYWH(x_actuel, y_position, 30, 30))

        # 2. AFFICHAGE DE LA MONNAIE
        arcade.draw_rect_filled(
            arcade.rect.LBWH(40, HAUTEUR - 90, 120, 35),
            (0, 0, 0, 120) 
        )
        arcade.draw_text(
            f"Monnaie: {joueur.monnaie} $",
            50, HAUTEUR - 82,
            arcade.color.GOLD,
            16,
            bold=True
        )

        # 2. Dessin de la barre d'EAU (Utilise le dossier eau)
        t_eau = self.get_texture(self.tex_eau, joueur.eau)
        arcade.draw_texture_rect(t_eau, arcade.rect.XYWH(LARGEUR - 100, HAUTEUR - 40, 150, 40))

        # 3. Dessin de la barre d'ÉNERGIE (Utilise le dossier nrj)
        t_nrj = self.get_texture(self.tex_nrj, joueur.energie)
        arcade.draw_texture_rect(t_nrj, arcade.rect.XYWH(LARGEUR - 100, HAUTEUR - 90, 150, 40))

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
        # On ne dessine rien si la boutique n'est pas ouverte
        if not self.ouvert:
            return

        # Calcul du centre de l'écran pour positionner le menu
        cx, cy = LARGEUR / 2, HAUTEUR / 2
        
        # --- 1. FOND DU MENU (gui.png) ---
        arcade.draw_texture_rect(
            texture=self.tex_gui,
            rect=arcade.rect.XYWH(cx, cy, self.largeur, self.hauteur)
        )

        # --- 2. BOUTON FERMER (CROIX) ---
        # Elle change de couleur et de taille si la souris passe dessus
        couleur_croix = arcade.color.RED if self.croix_survolee else arcade.color.WHITE
        taille_croix = 24 if self.croix_survolee else 20
        
        # On la place en haut à droite du panneau
        arcade.draw_text(
            "X", 
            cx + (self.largeur / 2) - 30, 
            cy + (self.hauteur / 2) - 30, 
            couleur_croix, 
            taille_croix, 
            anchor_x="center", 
            anchor_y="center", 
            bold=True
        )

        # Titre du shop
        arcade.draw_text("BOUTIQUE", cx, cy + 160, arcade.color.WHITE, 22, anchor_x="center", bold=True)

        # --- 3. LISTE DES ITEMS ---
        for i, item in enumerate(self.items_en_vente):
            # Position Y calculée pour que les items se suivent vers le bas
            y_item = cy + 60 - (i * 90)
            
            # Effet de zoom (scale) si survolé
            coeff = 1.1 if self.index_survole == i else 1.0
            
            # Fond du bouton (boutton1.png)
            arcade.draw_texture_rect(
                texture=self.tex_bouton,
                rect=arcade.rect.XYWH(cx, y_item, 400 * coeff, 75 * coeff)
            )
            
            # Icône de l'objet (test.png)
            arcade.draw_texture_rect(
                texture=item["texture"],
                rect=arcade.rect.XYWH(cx - 150, y_item, 45 * coeff, 45 * coeff)
            )
            
            # Texte : Nom de l'objet
            arcade.draw_text(
                item['nom'], 
                cx - 100, y_item + 5, 
                arcade.color.WHITE, 
                14 * coeff, 
                bold=True
            )
            
            # Texte : Prix (en doré)
            arcade.draw_text(
                f"Prix: {item['prix']} $", 
                cx - 100, y_item - 15, 
                arcade.color.GOLD, 
                13 * coeff
            )

    def check_achat(self, x, y, joueur, chat):
        if not self.ouvert: 
            return False

        cx, cy = LARGEUR / 2, HAUTEUR / 2
        
        # 1. Croix de fermeture
        cote_droit = cx + (self.largeur / 2)
        cote_haut = cy + (self.hauteur / 2)
        if cote_droit - 50 < x < cote_droit and cote_haut - 50 < y < cote_haut:
            self.ouvert = False
            return True

        # 2. Boutons d'achat
        for i, item in enumerate(self.items_en_vente):
            y_item = cy + 60 - (i * 90)
            if cx - 200 < x < cx + 200 and y_item - 35 < y < y_item + 35:
                if joueur.monnaie >= item["prix"]:
                    joueur.monnaie -= item["prix"]
                    # On envoie "couleur="
                    chat.ajouter_message(f"Achat : {item['nom']} !", couleur=arcade.color.GREEN)
                else:
                    chat.ajouter_message("Pas assez d'argent !", couleur=arcade.color.RED)
                return True
        return False

class Chat:
    def __init__(self):
        self.messages = [] 
        self.actif = False
        self.texte_saisie = ""

    def ajouter_message(self, texte, couleur=arcade.color.WHITE):
        # On utilise "couleur" ici
        self.messages.append({"texte": texte, "couleur": couleur, "timer": 5.0})

    def update(self, delta_time):
        for msg in self.messages:
            msg["timer"] -= delta_time
        self.messages = [m for m in self.messages if m["timer"] > 0]

    def dessiner(self):
        # Dessin des messages
        for i, msg in enumerate(reversed(self.messages)):
            y = 50 + (i * 25)
            arcade.draw_rect_filled(arcade.rect.LBWH(10, y-5, 300, 22), (0,0,0, 100))
            # CORRECTION ICI : On utilise msg["couleur"] et pas msg["color"]
            arcade.draw_text(msg["texte"], 15, y, msg["couleur"], 12)
        
        # Saisie de texte
        if self.actif:
            arcade.draw_rect_filled(arcade.rect.LBWH(10, 20, 400, 25), (0,0,0, 150))
            arcade.draw_text(f"> {self.texte_saisie}_", 15, 25, arcade.color.GREEN, 14)