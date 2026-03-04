import arcade
import os
import math
from sources.constantes import DOSSIER_DATA, DISTANCE_MAX_TIR

def charger_droite_gauche(chemin):
    tex_droite = arcade.load_texture(chemin)
    tex_gauche = tex_droite.flip_left_right()
    return [tex_droite, tex_gauche]

class EntiteAnimee(arcade.Sprite):
    def __init__(self, x, y, taille=1.0):
        super().__init__()
        self.textures = []
        self.center_x = x
        self.center_y = y
        self.scale = taille
        self.frame_actuelle = 0
        self.temps = 0

    def update_animation(self, delta_time=1/60):
        if self.textures:
            self.temps += delta_time
            if self.temps > 0.15:
                self.temps = 0
                self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures)
                self.texture = self.textures[self.frame_actuelle]

class Joueur(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = 0.4
        self.direction = 0 
        self.en_dash = False
        self.en_escalade = False
        self.temps = 0
        self.index_marche = 0
        self.index_grimpe = 0
        
        d_player = os.path.join(DOSSIER_DATA, "player")
        d_mouv = os.path.join(d_player, "mouvements")
        
        try:
            self.tex_repos = charger_droite_gauche(os.path.join(d_player, "player.png"))
            self.tex_dash = charger_droite_gauche(os.path.join(d_mouv, "Dash.png"))
            self.tex_marche = [charger_droite_gauche(os.path.join(d_mouv, f"avancer ({i}).png")) for i in range(1, 5)]
            self.tex_grimpe = [arcade.load_texture(os.path.join(d_mouv, f"grimper ({i}).png")) for i in range(1, 4)]
            self.texture = self.tex_repos[0]
        except Exception as e:
            t = arcade.make_soft_square_texture(50, (0, 255, 0))
            self.tex_repos = [t, t]; self.tex_dash = [t, t]; self.tex_marche = [[t, t]]; self.tex_grimpe = [t]
            self.texture = t

    def update_animation(self, delta_time=1/60):
        if self.change_x < -0.1: self.direction = 1
        elif self.change_x > 0.1: self.direction = 0
            
        if self.en_escalade:
            self.temps += delta_time
            if self.temps > 0.15:
                self.temps = 0
                self.index_grimpe = (self.index_grimpe + 1) % len(self.tex_grimpe)
            self.texture = self.tex_grimpe[self.index_grimpe]
        elif self.en_dash:
            self.texture = self.tex_dash[self.direction]
        elif abs(self.change_x) > 0.1:
            self.temps += delta_time
            if self.temps > 0.1:
                self.temps = 0
                self.index_marche = (self.index_marche + 1) % len(self.tex_marche)
            self.texture = self.tex_marche[self.index_marche][self.direction]
        else:
            self.texture = self.tex_repos[self.direction]

# Classes Ennemi, LeBoss et Projectile identiques (inchangees)
class Ennemi(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y)
        try:
            d = os.path.join(DOSSIER_DATA, "mobtest")
            self.textures = [arcade.load_texture(os.path.join(d, "mob-1.png")), arcade.load_texture(os.path.join(d, "mob-2.png"))]
            self.texture = self.textures[0]
        except: self.texture = arcade.make_soft_square_texture(64, (255, 0, 0))

class LeBoss(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=2.5)
        try:
            d = os.path.join(DOSSIER_DATA, "boss", "test")
            for i in range(33): self.textures.append(arcade.load_texture(os.path.join(d, f"attaque{i:02d}.png")))
            self.texture = self.textures[0]
        except: self.texture = arcade.make_soft_square_texture(120, (150, 0, 0))

class Projectile(EntiteAnimee):
    def __init__(self, x_depart, y_depart, x_cible, y_cible, vitesse):
        super().__init__(x_depart, y_depart, taille=0.5)
        angle_rad = math.atan2(y_cible - y_depart, x_cible - x_depart)
        self.change_x = math.cos(angle_rad) * vitesse
        self.change_y = math.sin(angle_rad) * vitesse
        self.angle = math.degrees(angle_rad)
        self.distance_parcourue = 0
        try:
            d_att = os.path.join(DOSSIER_DATA, "player", "attaque")
            for i in range(16): self.textures.append(arcade.load_texture(os.path.join(d_att, f"frame_{i:02d}_delay-0.1s.png")))
            self.texture = self.textures[0]
        except: self.texture = arcade.make_soft_square_texture(20, (255, 255, 0))
    def update(self):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.distance_parcourue += math.sqrt(self.change_x**2 + self.change_y**2)
        if self.distance_parcourue > DISTANCE_MAX_TIR: self.remove_from_sprite_lists()