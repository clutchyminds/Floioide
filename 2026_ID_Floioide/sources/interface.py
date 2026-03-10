import os
from sources.constantes import DOSSIER_DATA
import arcade
import math
from sources.constantes import LARGEUR, HAUTEUR

class HUD:
    def __init__(self):
        self.barre_vie_couleur = arcade.color.RED
        self.eau_couleur = arcade.color.AZURE_MIST
        self.dash_couleur = arcade.color.GOLD
        chemin_vies = os.path.join(DOSSIER_DATA, "player", "vies")
        self.tex_plein = arcade.load_texture(os.path.join(chemin_vies, "vie1.png"))
        self.tex_demi = arcade.load_texture(os.path.join(chemin_vies, "vie0.5.png"))
        self.tex_vide = arcade.load_texture(os.path.join(chemin_vies, "vie0.png"))
        
    def dessiner(self, joueur):
        # --- AFFICHAGE DES 10 CŒURS ---
        x_depart = 40
        y_position = HAUTEUR - 40
        espacement = 35 
        
        # On crée une liste de sprites temporaire
        liste_coeurs = arcade.SpriteList()
        
        for i in range(10):
            seuil_vie = (i * 2) + 1
            x_actuel = x_depart + (i * espacement)
            
            if joueur.vie >= seuil_vie + 1:
                tex = self.tex_plein
            elif joueur.vie == seuil_vie:
                tex = self.tex_demi
            else:
                tex = self.tex_vide

            # On crée le sprite
            coeur = arcade.Sprite(tex, scale=0.07)
            coeur.center_x = x_actuel
            coeur.center_y = y_position
            
            # On l'ajoute à la liste au lieu de le dessiner direct
            liste_coeurs.append(coeur)

        # On dessine toute la liste d'un coup
        liste_coeurs.draw()

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