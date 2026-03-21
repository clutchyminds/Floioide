import os
import arcade
import math
from sources.constantes import LARGEUR, HAUTEUR, DOSSIER_DATA

class HUD:
    def __init__(self):
        # 1. CHARGEMENT DES TEXTURES
        chemin_vies = os.path.join(DOSSIER_DATA, "player", "vies")
        self.tex_vie_1 = arcade.load_texture(os.path.join(chemin_vies, "vie1.png"))
        self.tex_vie_05 = arcade.load_texture(os.path.join(chemin_vies, "vie0.5.png"))
        self.tex_vie_0 = arcade.load_texture(os.path.join(chemin_vies, "vie0.png"))
        
        self.textures_eau = {}
        self.textures_nrj = {}
        for val in [0, 25, 50, 75, 100]:
            path_eau = os.path.join(DOSSIER_DATA, "player", "barres", "eau", f"{val}.png")
            path_nrj = os.path.join(DOSSIER_DATA, "player", "barres", "nrj", f"{val}.png")
            self.textures_eau[val] = arcade.load_texture(path_eau)
            self.textures_nrj[val] = arcade.load_texture(path_nrj)

        self.tex_monnaie = arcade.load_texture(os.path.join(DOSSIER_DATA, "mobs", "PNJ", "monnaie.png"))

    def dessiner(self, joueur):
        """Dessine les coeurs et les barres (Eau/Énergie)"""
        # Coeurs (Vies)
        for i in range(10):
            x = 40 + (i * 35)
            y = HAUTEUR - 40
            if joueur.vie >= (i + 1) * 2:
                tex = self.tex_vie_1
            elif joueur.vie == (i * 2) + 1:
                tex = self.tex_vie_05
            else:
                tex = self.tex_vie_0
            arcade.draw_texture_rect(tex, arcade.rect.XYWH(x, y, 30, 30))

        # Barres d'Eau et Énergie
        p_eau = max(0, min(100, (joueur.eau // 25) * 25))
        p_nrj = max(0, min(100, (joueur.energie // 25) * 25))
        arcade.draw_texture_rect(self.textures_eau[p_eau], arcade.rect.XYWH(LARGEUR - 100, HAUTEUR - 40, 120, 40))
        arcade.draw_texture_rect(self.textures_nrj[p_nrj], arcade.rect.XYWH(LARGEUR - 230, HAUTEUR - 40, 120, 40))

    def dessiner_inventaire_et_monnaie(self, joueur):
        """Méthode appelée par main.py pour l'inventaire et l'argent"""
        # 1. Monnaie
        arcade.draw_texture_rect(self.tex_monnaie, arcade.rect.XYWH(LARGEUR - 330, HAUTEUR - 40, 30, 30))
        arcade.draw_text(f"{joueur.monnaie}", LARGEUR - 310, HAUTEUR - 50, arcade.color.WHITE, 16, bold=True)

        # 2. Inventaire (4 cases en bas)
        taille_case = 60
        espacement = 10
        x_start = LARGEUR // 2 - ((taille_case * 4 + espacement * 3) // 2)
        
        for i in range(4):
            x = x_start + i * (taille_case + espacement)
            y = 50
            
            # Fond de la case
            couleur_fond = (0, 0, 0, 150)
            # CORRECTION : draw_rect_filled au lieu de draw_rectangle_filled
            arcade.draw_rect_filled(arcade.rect.XYWH(x, y, taille_case, taille_case), couleur_fond)
            
            # Bordure (plus épaisse si sélectionnée)
            epaisseur = 3 if joueur.index_inventaire == i else 1
            couleur_bord = arcade.color.WHITE if joueur.index_inventaire == i else (200, 200, 200)
            # CORRECTION : draw_rect_outline au lieu de draw_rectangle_outline
            arcade.draw_rect_outline(arcade.rect.XYWH(x, y, taille_case, taille_case), couleur_bord, epaisseur)
            
            # Contenu de la case (si un objet est présent)
            if joueur.inventaire[i] is not None:
                arcade.draw_texture_rect(joueur.inventaire[i].texture, arcade.rect.XYWH(x, y, 45, 45))
            
            # Petit numéro de la case
            arcade.draw_text(str(i+1), x - 25, y + 15, arcade.color.GRAY, 10)

    def dessiner_vie_boss(self, boss):
        ratio = max(0, boss.vie / boss.vie_max)
        # CORRECTION : draw_rect_filled
        arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, 120, 400, 20), arcade.color.BLACK)
        arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2 - (400*(1-ratio)/2), 120, 400 * ratio, 15), arcade.color.RED)
        arcade.draw_text(boss.nom, LARGEUR//2, 145, arcade.color.WHITE, 12, bold=True, anchor_x="center")

class InterfaceShop:
    def __init__(self):
        self.ouvert = False
        self.souris_x = 0
        self.souris_y = 0
        self.items = [
            {"nom": "Soin (25%)", "prix": 10, "type": "SOIN"},
            {"nom": "Munitions", "prix": 5, "type": "EAU"},
            {"nom": "Force +1", "prix": 50, "type": "BUFF"}
        ]

    def update_souris(self, x, y):
        """Met à jour la position de la souris pour le survol"""
        self.souris_x = x
        self.souris_y = y

    def dessiner(self):
        if not self.ouvert:
            return

        # 1. Fond sombre semi-transparent
        arcade.draw_rect_filled(
            arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, 500, 400),
            (0, 0, 0, 220)
        )
        arcade.draw_rect_outline(
            arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, 500, 400),
            arcade.color.GOLDENROD, 2
        )

        arcade.draw_text("BOUTIQUE DU VILLAGE", LARGEUR//2, HAUTEUR//2 + 160, 
                         arcade.color.GOLD, 22, anchor_x="center", bold=True)

        # 2. Liste des items
        for i, item in enumerate(self.items):
            y_item = HAUTEUR//2 + 50 - (i * 60)
            
            # Détection du survol
            est_survole = (abs(self.souris_x - LARGEUR//2) < 200 and 
                           abs(self.souris_y - y_item) < 25)
            
            couleur_fond = (50, 50, 50, 200) if not est_survole else (100, 100, 100, 255)
            
            # Dessin de la ligne d'item
            arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, y_item, 400, 50), couleur_fond)
            
            # Texte de l'item
            arcade.draw_text(f"{item['nom']}", LARGEUR//2 - 180, y_item - 10, arcade.color.WHITE, 16)
            arcade.draw_text(f"{item['prix']} $", LARGEUR//2 + 120, y_item - 10, arcade.color.YELLOW, 16, bold=True)

    def on_mouse_press(self, x, y, joueur, chat):
        if not self.ouvert:
            return False

        for i, item in enumerate(self.items):
            y_item = HAUTEUR//2 + 50 - (i * 60)
            if abs(x - LARGEUR//2) < 200 and abs(y - y_item) < 25:
                if joueur.monnaie >= item["prix"]:
                    joueur.monnaie -= item["prix"]
                    chat.ajouter_message(f"Achat réussi : {item['nom']}", arcade.color.GREEN)
                    # Ici on pourra ajouter l'effet de l'objet plus tard
                else:
                    chat.ajouter_message("Pas assez d'argent !", arcade.color.RED)
                return True
        return False
    
class Chat:
    def __init__(self):
        self.messages = []
        self.actif = False
        self.texte_saisie = ""
        
    def ajouter_message(self, texte, couleur=arcade.color.WHITE):
        self.messages.append({"texte": texte, "couleur": couleur, "timer": 5.0})

    def update(self, delta_time):
        for msg in self.messages:
            msg["timer"] -= delta_time
        self.messages = [m for m in self.messages if m["timer"] > 0]

    def dessiner(self):
        for i, msg in enumerate(reversed(self.messages)):
            y = 150 + (i * 25)
            arcade.draw_text(msg["texte"], 20, y, msg["couleur"], 14)