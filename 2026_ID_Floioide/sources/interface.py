import os
import arcade
import math
from constantes import LARGEUR, HAUTEUR, DOSSIER_DATA

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
        # On gère l'affichage jusqu'à 15 coeurs (si le charme coeurs+5.png est là)
        coeurs_a_dessiner = 15 if "coeurs+5.png" in joueur.inventaire_charmes else 10
        
        for i in range(coeurs_a_dessiner):
            # Les 10 premiers cœurs sur la ligne du bas, les 5 autres au-dessus
            ligne = i // 10
            colonne = i % 10
            x_coeur = 50 + colonne * 35 
            y_coeur = 130 + ligne * 40 # +40 pixels plus haut pour la 2ème ligne
            
            seuil_plein = (i + 1) * 10
            seuil_demi = seuil_plein - 5
            
            if joueur.vie >= seuil_plein: tex = self.tex_vie_1
            elif joueur.vie > seuil_demi: tex = self.tex_vie_05
            else: tex = self.tex_vie_0
                
            arcade.draw_texture_rect(tex, arcade.rect.XYWH(x_coeur, y_coeur, 32, 32))

    def dessiner_inventaire_et_monnaie(self, joueur):
        # 1. MONNAIE
        arcade.draw_texture_rect(self.tex_monnaie, arcade.rect.XYWH(LARGEUR - 150, 50, 40, 40))
        arcade.draw_text(f"{joueur.monnaie} $", LARGEUR - 100, 40, arcade.color.YELLOW, 18, bold=True)
        
        # 2. INVENTAIRE CONSOMMABLES (3 cases, horizontal, au milieu)
        start_x = LARGEUR // 2 - 100
        for i in range(3):
            x_slot = start_x + i * 80
            y_slot = 50
            taille = 70 if i == joueur.index_selection else 60 # Grossit si sélectionné
            rect = arcade.rect.XYWH(x_slot, y_slot, taille, taille)
            
            couleur_bord = arcade.color.YELLOW if i == joueur.index_selection else arcade.color.WHITE
            arcade.draw_rect_outline(rect, couleur_bord, 3)

            item = joueur.inventaire_items[i]
            if item is not None:
                arcade.draw_texture_rect(item["tex"], arcade.rect.XYWH(x_slot, y_slot, taille - 10, taille - 10))
                # Dessiner le nombre de l'item (stack) en bas à droite de la case
                arcade.draw_text(f"x{item['qte']}", x_slot + 10, y_slot - 25, arcade.color.WHITE, 12, bold=True)
                
        # 3. INVENTAIRE CHARMES (4 cases, vertical, à gauche de l'écran par exemple)
        for i in range(4):
            x_slot = 40
            y_slot = HAUTEUR // 2 + (i * 70) - 100
            rect = arcade.rect.XYWH(x_slot, y_slot, 50, 50)
            arcade.draw_rect_outline(rect, arcade.color.LIGHT_GRAY, 2)
            
            if i < len(joueur.inventaire_charmes):
                nom_fichier = joueur.inventaire_charmes[i]
                # Essai de chargement rapide de la texture du charme
                try:
                    tex_charme = arcade.load_texture(os.path.join(DOSSIER_DATA, "mobs", "PNJ", "items", nom_fichier))
                    arcade.draw_texture_rect(tex_charme, arcade.rect.XYWH(x_slot, y_slot, 40, 40))
                except: pass # Si image introuvable, on laisse vide

        # 4. GOUTTE D'EAU ET FLEUR DASH
        val_eau = max(0, min(100, int(joueur.eau // 25) * 25))
        arcade.draw_texture_rect(self.textures_eau[val_eau], arcade.rect.XYWH(650, 140, 64, 64))
        arcade.draw_text(f"{int(joueur.eau)}", 670, 130, arcade.color.CYAN, 18, bold=True)

        temps_restant = math.ceil(getattr(joueur, 'timer_dash', 0))
        if temps_restant >= 5: val_nrj = 0
        elif temps_restant == 4: val_nrj = 25
        elif temps_restant == 3: val_nrj = 50
        elif temps_restant == 2: val_nrj = 75
        else: val_nrj = 100
        
        arcade.draw_texture_rect(self.textures_nrj[val_nrj], arcade.rect.XYWH(740, 140, 64, 64))
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
        # --- Chargement des Items (remplacer l'ancien bloc par ça) ---
        self.items = []
        self.charger_item("Eau de source", 10, "eau.1.png", "conso")
        self.charger_item("Eau minérale", 25, "eau.2.png", "conso")
        self.charger_item("Eau pure", 50, "eau.3.png", "conso")
        self.charger_item("Petit Soin", 40, "Heal1.png", "conso")
        self.charger_item("Grand Soin", 80, "Heal2.png", "conso")
        self.charger_item("Piou Piou", 100, "piou.png", "arme")
        # Les charmes
        self.charger_item("Double Saut", 150, "2_saut.png", "charme")
        self.charger_item("Argent x2", 200, "argentx2.png", "charme")
        self.charger_item("Coeurs +5", 250, "coeurs+5.png", "charme")

        # Dimensions
        self.btn_largeur = 200
        self.btn_hauteur = 50
        self.espacement_x = 195
        self.espacement_y = 70

    def charger_item(self, nom, prix, fichier, type_item):
        path = os.path.join(self.chemin_items, fichier)
        try:
            tex = arcade.load_texture(path)
        except:
            tex = arcade.make_soft_square_texture(40, arcade.color.BLUE)
        self.items.append({"nom": nom, "prix": prix, "fichier": fichier, "type": type_item, "icon": tex, "achete": False})

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



class InterfaceDev:
    def __init__(self):
        self.ouvert = False
        self.souris_x = 0
        self.souris_y = 0
        
        # Ce qu'on peut modifier et de combien ça augmente/baisse à chaque clic
        self.lignes = [
            {"nom": "Vitesse", "attr": "vitesse", "step": 1},
            {"nom": "Saut", "attr": "puissance_saut", "step": 1},
            {"nom": "Vitesse Dash", "attr": "vitesse_dash", "step": 5},
            {"nom": "Taille", "attr": "scale", "step": 0.1},
            {"nom": "Vie Max", "attr": "vie_max", "step": 10},
            {"nom": "Vie", "attr": "vie", "step": 10},
            {"nom": "Monnaie", "attr": "monnaie", "step": 10},
        ]

    def update_souris(self, x, y):
        self.souris_x = x
        self.souris_y = y

    def dessiner(self, joueur):
        if not self.ouvert: return
        
        # Fond semi-transparent
        arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, 400, 450), (0, 0, 0, 220))
        arcade.draw_text("MENU DÉVELOPPEUR (F4)", LARGEUR//2, HAUTEUR//2 + 180, arcade.color.YELLOW, 18, bold=True, anchor_x="center")
        
        start_y = HAUTEUR//2 + 120
        # Affichage des statistiques
        for i, ligne in enumerate(self.lignes):
            y = start_y - i * 40
            valeur = getattr(joueur, ligne["attr"])
            if isinstance(valeur, float): valeur = round(valeur, 2)
            
            # Nom de la stat
            arcade.draw_text(f"{ligne['nom']} : {valeur}", LARGEUR//2 - 60, y, arcade.color.WHITE, 14, anchor_x="center", anchor_y="center")
            
            # Bouton [-]
            couleur_m = arcade.color.RED if abs(self.souris_x - (LARGEUR//2 - 150)) < 15 and abs(self.souris_y - y) < 15 else arcade.color.DARK_RED
            arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2 - 150, y, 30, 30), couleur_m)
            arcade.draw_text("-", LARGEUR//2 - 150, y, arcade.color.WHITE, 16, bold=True, anchor_x="center", anchor_y="center")

            # Bouton [+]
            couleur_p = arcade.color.GREEN if abs(self.souris_x - (LARGEUR//2 + 150)) < 15 and abs(self.souris_y - y) < 15 else arcade.color.DARK_GREEN
            arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2 + 150, y, 30, 30), couleur_p)
            arcade.draw_text("+", LARGEUR//2 + 150, y, arcade.color.WHITE, 16, bold=True, anchor_x="center", anchor_y="center")

        # Bouton Noclip (Vol)
        y_noclip = start_y - len(self.lignes) * 40 - 20
        couleur_noclip = arcade.color.GREEN if joueur.noclip else arcade.color.RED
        arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, y_noclip, 200, 40), couleur_noclip)
        texte_noclip = "Noclip / Vol : ON" if joueur.noclip else "Noclip / Vol : OFF"
        arcade.draw_text(texte_noclip, LARGEUR//2, y_noclip, arcade.color.WHITE, 14, bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_press(self, x, y, joueur):
        start_y = HAUTEUR//2 + 120
        for i, ligne in enumerate(self.lignes):
            ly = start_y - i * 40
            
            # Détection du clic
            if abs(y - ly) < 15:
                # --- CALCUL DU CHANGEMENT ---
                changement = 0
                if abs(x - (LARGEUR//2 - 150)) < 15: # Bouton [-]
                    changement = -ligne["step"]
                elif abs(x - (LARGEUR//2 + 150)) < 15: # Bouton [+]
                    changement = ligne["step"]

                if changement != 0:
                    # Cas spécial pour la TAILLE (Scale) car c'est un tuple dans Arcade 3.0
                    if ligne["attr"] == "scale":
                        ancienne_taille = joueur.scale # On prend la largeur actuelle
                        nouvelle_taille = max(0.1, ancienne_taille + changement)
                        joueur.scale = (nouvelle_taille, nouvelle_taille)
                    else:
                        valeur_actuelle = getattr(joueur, ligne["attr"])
                        setattr(joueur, ligne["attr"], valeur_actuelle + changement)

        # --- CLIC SUR LE BOUTON NOCLIP (C'est ici que ça coince souvent) ---
        y_noclip = start_y - len(self.lignes) * 40 - 20
        # On vérifie si la souris est dans le rectangle central du Noclip
        if abs(x - LARGEUR//2) < 100 and abs(y - y_noclip) < 20:
            joueur.noclip = not joueur.noclip
            print(f"Noclip basculé : {joueur.noclip}") # Pour vérifier dans la console