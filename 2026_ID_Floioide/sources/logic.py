import arcade

def gerer_collisions(tiroirs):
    """
    Gère les dégâts de l'attaque de mêlée sur les ennemis.
    """
    # On vérifie si une attaque est en cours
    if "attaques" not in tiroirs or not tiroirs["attaques"]:
        return

    for attaque in tiroirs["attaques"]:
        # On récupère la liste des ennemis touchés par l'animation actuelle
        ennemis_touches = arcade.check_for_collision_with_list(attaque, tiroirs["ennemis"])
        
        # On crée un set sur l'objet attaque pour ne taper chaque mob qu'une seule fois
        if not hasattr(attaque, "deja_touche"):
            attaque.deja_touche = set()

        for ennemi in ennemis_touches:
            if ennemi not in attaque.deja_touche:
                # Appliquer 1 point de dégât
                ennemi.points_de_vie -= 1
                attaque.deja_touche.add(ennemi)
                
                # Feedback visuel optionnel : on peut faire clignoter le mob ici
                
                if ennemi.points_de_vie <= 0:
                    ennemi.remove_from_sprite_lists()