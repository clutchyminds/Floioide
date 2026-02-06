import arcade

def dessiner_statistiques(quantite_eau, nb_petales):
    # 1. Dessiner le contour de la barre d'eau
    arcade.draw_lrtb_rectangle_outline(20, 220, 600, 580, arcade.color.WHITE)
    
    # 2. Dessiner le remplissage (la largeur dépend de l'eau)
    largeur = (quantite_eau / 100) * 200
    arcade.draw_lrtb_rectangle_filled(20, 20 + largeur, 600, 580, arcade.color.BLUE)
    
    # 3. Afficher le texte
    arcade.draw_text(f"Pétales: {nb_petales}", 20, 550, arcade.color.WHITE, 12)