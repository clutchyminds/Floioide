import arcade
import math
from sources.constantes import LARGEUR, HAUTEUR

class HUD:
    def __init__(self):
        self.barre_vie_couleur = arcade.color.RED
        self.eau_couleur = arcade.color.AZURE_MIST
        self.dash_couleur = arcade.color.GOLD

    def dessiner(self, joueur):
        # --- 1. BARRE DE VIE ---
        arcade.draw_rect_filled(arcade.LBWH(20, HAUTEUR - 40, 200, 20), arcade.color.BLACK)
        largeur_vie = (joueur.vie / 100) * 200
        if largeur_vie > 0:
            arcade.draw_lrbt_rectangle_filled(20, 20 + largeur_vie, HAUTEUR - 40, HAUTEUR - 20, self.barre_vie_couleur)

        # --- 2. JAUGE D'EAU (Cercle) ---
        centre_eau_x, centre_eau_y = 60, HAUTEUR - 100
        rayon = 30
        
        # Fond gris du cercle
        arcade.draw_circle_filled(centre_eau_x, centre_eau_y, rayon, arcade.color.DARK_GRAY)
        
        # On s'assure que le niveau d'eau ne dépasse pas les bornes
        niveau_eau = max(0, min(100, joueur.eau))
        angle_remplissage = (niveau_eau / 100) * 360
        
        # UNE SEULE FONCTION : On remplit à partir de 90° (le haut) dans le sens horaire
        if niveau_eau > 0:
            arcade.draw_arc_filled(
                centre_eau_x, centre_eau_y, 
                rayon*2, rayon*2, 
                self.eau_couleur, 
                90 - angle_remplissage, 90
            )
        
        arcade.draw_text("H2O", centre_eau_x - 15, centre_eau_y - 5, arcade.color.WHITE, 10, bold=True)

        # --- 3. RECHARGEMENT DASH (Triangle) ---
        centre_dash_x, centre_dash_y = 140, HAUTEUR - 100
        taille_tri = 35
        
        # Fond du triangle
        p1 = (centre_dash_x, centre_dash_y + taille_tri)
        p2 = (centre_dash_x - taille_tri, centre_dash_y - taille_tri)
        p3 = (centre_dash_x + taille_tri, centre_dash_y - taille_tri)
        arcade.draw_polygon_filled([p1, p2, p3], arcade.color.DARK_GRAY)

        # Progression du cooldown (0.0 à 1.0)
        progression_dash = max(0.0, min(1.0, 1 - (joueur.timer_dash / 7.0)))
        
        if progression_dash > 0:
            if progression_dash >= 1.0: # Dash prêt !
                arcade.draw_polygon_filled([p1, p2, p3], self.dash_couleur)
            else:
                # Triangle de remplissage qui monte
                arcade.draw_triangle_filled(
                    centre_dash_x, centre_dash_y - taille_tri + (taille_tri * 2 * progression_dash),
                    centre_dash_x - (taille_tri * progression_dash), centre_dash_y - taille_tri,
                    centre_dash_x + (taille_tri * progression_dash), centre_dash_y - taille_tri,
                    self.dash_couleur
                )

        arcade.draw_text("DASH", centre_dash_x - 18, centre_dash_y - 25, arcade.color.WHITE, 8, bold=True)