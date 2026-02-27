import arcade
import os
from sources.constantes import DOSSIER_DATA

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

class Ennemi(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y)
        try:
            # dossier data/mobtest d apres tes photos
            d = os.path.join(DOSSIER_DATA, "mobtest")
            self.textures = [
                arcade.load_texture(os.path.join(d, "mob-1.png")),
                arcade.load_texture(os.path.join(d, "mob-2.png"))
            ]
            self.texture = self.textures[0]
        except Exception as e:
            print(f"erreur mob: {e}")
            self.texture = arcade.make_soft_square_texture(64, (255, 0, 0))

class LeBoss(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=2.5)
        try:
            # dossier data/boss/test d apres tes photos
            d = os.path.join(DOSSIER_DATA, "boss", "test")
            for i in range(33):
                nom = f"attaque{i:02d}.png"
                self.textures.append(arcade.load_texture(os.path.join(d, nom)))
            self.texture = self.textures[0]
        except Exception as e:
            print(f"erreur boss: {e}")
            self.texture = arcade.make_soft_square_texture(120, (150, 0, 0))