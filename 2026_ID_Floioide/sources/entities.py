# Projet : Floioide
# Auteurs : Laure Ducourneau, Victor Dauphin, Corentin Gelineau, Thomas Lewis

import arcade

class Ennemi(arcade.Sprite):
    def update(self):
        # CORENTIN : C'est ici que tu gères le mouvement de l'ennemi
        self.center_x += self.change_x
        # Si l'ennemi touche une limite, il fait demi-tour
        pass

class Floioide(arcade.Sprite):
    def __init__(self):
        super().__init__("data/images/fleur.png", 0.5)
        self.eau = 100
        self.petales = 5