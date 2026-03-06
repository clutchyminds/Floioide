import arcade
import os
import math
from sources.constantes import DOSSIER_DATA, DISTANCE_MAX_TIR

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

        # 1. Chargement des textures
        self.tex_idle = arcade.load_texture(os.path.join(DOSSIER_DATA, "player", "player.png"))
        
        # Fonction utilitaire pour charger un dossier d'images
        def charger_dossier(nom_dossier):
            liste = []
            chemin = os.path.join(DOSSIER_DATA, nom_dossier)
            if os.path.exists(chemin):
                fichiers = sorted([f for f in os.listdir(chemin) if f.endswith(".png")])
                for f in fichiers:
                    liste.append(arcade.load_texture(os.path.join(chemin, f)))
            return liste

        self.anims_marche = charger_dossier("mouvement")
        self.anims_dash = charger_dossier("dash")
        self.anims_escalade = charger_dossier("escalade")

        self.texture = self.tex_idle

    def update_animation(self, delta_time=1/60):
        # --- CHOIX DE LA LISTE D'ANIMATIONS ---
        nouvelle_liste = []

        if self.en_escalade:
            nouvelle_liste = self.anims_escalade
        elif self.en_dash:
            nouvelle_liste = self.anims_dash
        elif abs(self.change_x) > 0.1:
            nouvelle_liste = self.anims_marche

        # --- APPLICATION DE L'ANIMATION ---
        if nouvelle_liste:
            self.textures = nouvelle_liste
            super().update_animation(delta_time)
        else:
            self.texture = self.tex_idle

        # Orientation du regard
        if self.change_x > 0:
            self.flipped_horizontally = False
        elif self.change_x < 0:
            self.flipped_horizontally = True

            
# Garde tes classes Boss, PetitMob et Projectile en dessous...
class Boss(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=2.0)
        d = os.path.join(DOSSIER_DATA, "boss", "test")
        for i in range(33):
            try:
                self.textures.append(arcade.load_texture(os.path.join(d, f"attaque{i:02d}.png")))
            except: pass
        self.texture = self.textures[0] if self.textures else arcade.make_soft_square_texture(100, (255,0,0))

class PetitMob(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=0.5)
        self.vitesse = 2
        self.texture = arcade.make_soft_square_texture(40, arcade.color.RED)