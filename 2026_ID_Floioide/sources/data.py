import arcade

class InputHeadler:
    def __init__(self):
        #on regroupe des états ici
        self.gauche = False
        self.droite = False
        self.haut = False #pour l'escalade (z)
        self.shift = False #pour le dash
    
    def on_key_press(self, key):
        #on met a jour l'etat quand on appuie sur une touche
        if key == arcade.key.Q: self.gauche = True
        elif key == arcade.key.D: self.droite = True
        elif key == arcade.key.Z: self.haut = True
        elif key == arcade.key.LSHIFT: self.shift = True

    def on_key_release(self, key):
        #met a jour l'etat quand on relache une touche
        if key == arcade.key.Q: self.gauche = False
        elif key == arcade.key.D: self.droite = False
        elif key == arcade.key.Z: self.haut = False
        elif key == arcade.key.LSHIFT: self.shift = False
