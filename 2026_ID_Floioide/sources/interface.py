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
        # On commence à 300 pour avoir la place pour 10 cœurs
        for i in range(10):
            x_coeur = 50 + i * 35  # Espacement de 35 pixels entre chaque cœur
            y_coeur = 130          # Juste au-dessus de l'inventaire
            
            # Détermination de la texture (1 cœur = 10 PV)
            seuil_plein = (i + 1) * 10
            seuil_demi = seuil_plein - 5
            
            if joueur.vie >= seuil_plein:
                tex = self.tex_vie_1
            elif joueur.vie > seuil_demi:
                tex = self.tex_vie_05
            else:
                tex = self.tex_vie_0
                
            arcade.draw_texture_rect(tex, arcade.rect.XYWH(x_coeur, y_coeur, 32, 32))
        

    def dessiner_inventaire_et_monnaie(self, joueur):
        # --- 1. MONNAIE ---
        # CORRECTION ICI : Remplacement de arcade.Rect par arcade.rect.XYWH
        arcade.draw_texture_rect(self.tex_monnaie, arcade.rect.XYWH(LARGEUR - 150, 50, 40, 40))
        arcade.draw_text(f"{joueur.monnaie} $", LARGEUR - 100, 40, arcade.color.YELLOW, 18, bold=True)

        # --- 2. INVENTAIRE (Au centre en bas) ---
        for i in range(4):
            x_slot = 400 + i * 100
            y_slot = 50
            rect = arcade.rect.XYWH(x_slot, y_slot, 80, 80)
            arcade.draw_rect_outline(rect, arcade.color.WHITE, 3)

            if joueur.inventaire[i] is not None:
                # Code pour dessiner l'item ici plus tard
                pass

        # --- 3. GOUTTE D'EAU / MANA (En haut à droite de l'inventaire) ---
        val_eau = max(0, min(100, int(joueur.eau // 25) * 25))
        # TAILLE CORRIGÉE : 64x64 pour que la goutte soit parfaitement proportionnée
        # CORRECTION ICI : Remplacement de arcade.Rect par arcade.rect.XYWH
        arcade.draw_texture_rect(self.textures_eau[val_eau], arcade.rect.XYWH(650, 140, 64, 64))
        # Le texte s'affiche juste à côté de l'icône
        arcade.draw_text(f"{int(joueur.eau)}", 670, 130, arcade.color.CYAN, 18, bold=True)

        # --- 4. FLEUR / DASH (À côté de la goutte d'eau) ---
        temps_restant = math.ceil(getattr(joueur, 'timer_dash', 0))
        
        if temps_restant >= 5: val_nrj = 0
        elif temps_restant == 4: val_nrj = 25
        elif temps_restant == 3: val_nrj = 50
        elif temps_restant == 2: val_nrj = 75
        else: val_nrj = 100
        
        # TAILLE CORRIGÉE : 64x64 pour que la fleur soit parfaite
        # CORRECTION ICI : Remplacement de arcade.Rect par arcade.rect.XYWH
        arcade.draw_texture_rect(self.textures_nrj[val_nrj], arcade.rect.XYWH(740, 140, 64, 64))
        
        # Texte du minuteur de dash
        if temps_restant > 0:
            arcade.draw_text(f"{temps_restant}s", 765, 130, arcade.color.ORANGE, 18, bold=True)
        else:
            arcade.draw_text("Prêt", 765, 130, arcade.color.GREEN, 14, bold=True)

class InterfaceShop:
    def __init__(self):
        self.ouvert = False
        self.souris_x = 0
        self.souris_y = 0

        # --- Chemins des dossiers ---
        self.chemin_pnj = os.path.join(DOSSIER_DATA, "mobs", "PNJ")
        self.chemin_items = os.path.join(self.chemin_pnj, "items") # Chemin corrigé

        # --- Chargement du GUI ---
        try:
            self.tex_gui = arcade.load_texture(os.path.join(self.chemin_pnj, "gui.png"))
            self.tex_btn = arcade.load_texture(os.path.join(self.chemin_pnj, "boutton.png"))
        except:
            self.tex_gui = None
            self.tex_btn = None

        # --- Chargement des Items ---
        self.items = []
        self.charger_item("Eau de source", 10, "eau.1.png")
        self.charger_item("Eau minérale", 25, "eau.2.png")
        self.charger_item("Eau pure", 50, "eau.3.png")
        self.charger_item("Petit Soin", 40, "Heal.1.png")
        self.charger_item("Grand Soin", 80, "Heal.2.png")

        # Dimensions
        self.btn_largeur = 130
        self.btn_hauteur = 50
        self.espacement_x = 195
        self.espacement_y = 70

    def charger_item(self, nom, prix, fichier):
        path = os.path.join(self.chemin_items, fichier)
        try:
            tex = arcade.load_texture(path)
        except:
            # Si l'image bug, on met un carré bleu par défaut
            tex = arcade.make_soft_square_texture(40, arcade.color.BLUE)
        
        self.items.append({"nom": nom, "prix": prix, "icon": tex})

    def update_souris(self, x, y):
        self.souris_x = x
        self.souris_y = y

    def dessiner(self):
        if not self.ouvert:
            return

        # 1. Fond
        if self.tex_gui:
            arcade.draw_texture_rect(self.tex_gui, arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, 650, 450))
        else:
            arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, 650, 450), arcade.color.DARK_GRAY)

        # 2. Croix de fermeture (Position précise)
        croix_x = LARGEUR//2 + 285
        croix_y = HAUTEUR//2 + 195
        survol_croix = abs(self.souris_x - croix_x) < 25 and abs(self.souris_y - croix_y) < 25
        couleur = arcade.color.RED if survol_croix else arcade.color.DARK_RED
        
        arcade.draw_rect_filled(arcade.rect.XYWH(croix_x, croix_y, 40, 40), couleur)
        arcade.draw_text("X", croix_x, croix_y, arcade.color.WHITE, 20, bold=True, anchor_x="center", anchor_y="center")

        # 3. Grille d'items
        start_x = LARGEUR//2 - 195
        start_y = HAUTEUR//2 + 80

        for i, item in enumerate(self.items):
            col = i % 3
            lig = i // 3
            bx = start_x + (col * self.espacement_x)
            by = start_y - (lig * self.espacement_y)

            survol = abs(self.souris_x - bx) < self.btn_largeur//2 and abs(self.souris_y - by) < self.btn_hauteur//2
            teinte = arcade.color.LIGHT_GRAY if survol else arcade.color.WHITE

            if self.tex_btn:
                arcade.draw_texture_rect(self.tex_btn, arcade.rect.XYWH(bx, by, self.btn_largeur, self.btn_hauteur), color=teinte)
            
            # Icône de l'item
            arcade.draw_texture_rect(item["icon"], arcade.rect.XYWH(bx - 60, by, 40, 40))
            
            # Textes
            arcade.draw_text(item['nom'], bx - 30, by + 5, arcade.color.WHITE, 10, anchor_x="left")
            arcade.draw_text(f"{item['prix']} $", bx - 30, by - 12, arcade.color.YELLOW, 11, bold=True, anchor_x="left")

    def on_mouse_press(self, x, y):
        # Vérification Croix
        cx, cy = LARGEUR//2 + 285, HAUTEUR//2 + 195
        if abs(x - cx) < 25 and abs(y - cy) < 25:
            return "FERMER"

        # Vérification Boutons
        start_x, start_y = LARGEUR//2 - 195, HAUTEUR//2 + 80
        for i, item in enumerate(self.items):
            bx = start_x + (i % 3 * self.espacement_x)
            by = start_y - (i // 3 * self.espacement_y)
            if abs(x - bx) < self.btn_largeur//2 and abs(y - by) < self.btn_hauteur//2:
                return item # On retourne l'item acheté
        
        return None
    
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