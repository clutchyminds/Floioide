import arcade
from sources.constantes import LARGEUR, HAUTEUR

class HUD:
    def __init__(self):
        self.barre_vie_couleur = arcade.color.RED

    def dessiner(self, joueur):
        # Fond noir (Bas: H-40, Haut: H-20)
        arcade.draw_lrbt_rectangle_filled(20, 220, HAUTEUR - 40, HAUTEUR - 20, arcade.color.BLACK)
        
        # Barre rouge
        largeur_vie = (joueur.vie / 100) * 200
        if largeur_vie > 0:
            arcade.draw_lrbt_rectangle_filled(20, 20 + largeur_vie, HAUTEUR - 40, HAUTEUR - 20, self.barre_vie_couleur)

        # Texte Eau
        arcade.draw_text(f"EAU: {int(joueur.eau)}%", 20, HAUTEUR - 70, arcade.color.WHITE, 14)