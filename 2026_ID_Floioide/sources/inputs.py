import arcade

class InputHandler:
    def __init__(self):
        self.gauche = False
        self.droite = False
        self.haut = False
        self.shift = False
        self.bas = False

    def on_key_press(self, key):
        if key == arcade.key.Q: self.gauche = True
        elif key == arcade.key.D: self.droite = True
        elif key == arcade.key.Z: self.haut = True
        elif key == arcade.key.S: self.bas = True
        elif key == arcade.key.LSHIFT: self.shift = True
        
    def on_key_release(self, key):
        if key == arcade.key.Q: self.gauche = False
        elif key == arcade.key.D: self.droite = False
        elif key == arcade.key.Z: self.haut = False
        elif key == arcade.key.S: self.bas = False
        elif key == arcade.key.LSHIFT: self.shift = False