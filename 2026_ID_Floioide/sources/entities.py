import arcade
import os
from sources.constantes import DOSSIER_DATA

class EntiteAnimee(arcade.Sprite):
    def __init__(self, x, y, taille=1.0):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = taille
        self.textures = []
        self.frame_actuelle = 0
        self.temps_ecoule = 0
        self.vitesse_animation = 0.15

    def update_animation(self, delta_time=1/60):
        if not self.textures:
            return
        self.temps_ecoule += delta_time
        if self.temps_ecoule > self.vitesse_animation:
            self.temps_ecoule = 0
            self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures)
            self.texture = self.textures[self.frame_actuelle]

class Joueur(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=0.4)
        self.vie = 100
        self.eau = 100
        self.en_escalade = False
        self.en_dash = False

        # 1. Chargement de l'image de base (Idle)
        # Chemin selon ton image : data/player/player.png
        self.tex_idle = arcade.load_texture(os.path.join(DOSSIER_DATA, "player", "player.png"))        
        # 2. Chargement des animations (Toutes dans data/player/mouvements)
        # Définir le chemin vers ton dossier regroupé
        chemin_mouvements = os.path.join(DOSSIER_DATA, "player", "mouvements")

        # Lister tous les fichiers présents dans ce dossier
        tous_les_fichiers = sorted(os.listdir(chemin_mouvements))

        # Fonction pour extraire les images selon le début de leur nom
        def charger_liste(prefixe):
            liste = []
            for f in tous_les_fichiers:
                if f.startswith(prefixe) and f.endswith(".png"):
                    liste.append(arcade.load_texture(os.path.join(chemin_mouvements, f)))
            return liste

        # Assigner les animations en fonction des noms visibles sur ta capture
        self.anims_marche = charger_liste("avancer")   # Charge avancer (1).png, etc.
        self.anims_dash = charger_liste("Dash")        # Charge Dash.png
        self.anims_escalade = charger_liste("grimper") # Charge grimper (1).png, etc.

        self.texture = self.tex_idle

    def update_animation(self, delta_time=1/60):
        nouvelle_liste = []

        if self.en_escalade:
            nouvelle_liste = self.anims_escalade
        elif self.en_dash:
            nouvelle_liste = self.anims_dash
        elif abs(self.change_x) > 0.1:
            nouvelle_liste = self.anims_marche

        if nouvelle_liste:
            self.textures = nouvelle_liste
            super().update_animation(delta_time)
        else:
            self.texture = self.tex_idle

        # Orientation
        if self.change_x > 0:
            self.flipped_horizontally = False
        elif self.change_x < 0:
            self.flipped_horizontally = True

class Boss(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=2.0)
        # On cherche dans data/boss/test comme indiqué dans tes dossiers
        d = os.path.join(DOSSIER_DATA, "boss", "test")
        if os.path.exists(d):
            fichiers = sorted([f for f in os.listdir(d) if f.endswith(".png")])
            for f in fichiers:
                self.textures.append(arcade.load_texture(os.path.join(d, f)))
        
        # Texture de secours si le dossier est vide
        self.texture = self.textures[0] if self.textures else arcade.make_soft_square_texture(100, (255, 0, 0))

class PetitMob(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=0.5)
        self.vitesse = 2
        # Utilise un carré rouge temporaire ou une image de mobtest
        self.texture = arcade.make_soft_square_texture(40, (255, 0, 0))