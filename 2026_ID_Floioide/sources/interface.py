#PROJET:FLOÏOIDE
#EQUIPE : THOMAS, VICTOR, CORENTIN, LAURE

import arcade
#réglages
HAUTEUR = 720
LARGEUR = 1280

TITRE_JEU = "Floïoide" 

#écran menu
class MenuDepart(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
    def on_draw(self):
        self.clear()
        arcade.draw_text(TITRE_JEU, LARGEUR/2, HAUTEUR*0.7, arcade.color.GREEN, 60, anchor_x="center")
        arcade.draw_text("Appuyez sur entrée pour lancer", LARGEUR/2, HAUTEUR*0.4, arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text("Appuyez sur h pour l'aide", LARGEUR/2, HAUTEUR*0.4, arcade.color.WHITE, 20, anchor_x="center")
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            vue_jeu = MonJeu()
            vue_jeu.setup()
            self.Window.show_view(vue_jeu)

class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        self.liste_joueur = None
        self.fleur = None
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_hud = arcade.camera.Camera2D()
        self.vie = 100
        self.eau = 100