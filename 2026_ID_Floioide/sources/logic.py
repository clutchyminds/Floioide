import arcade

def gerer_collisions(tiroir_tirs, tiroir_ennemis):
    """
    Vérifie si les projectiles touchent les ennemis.
    Si oui, le projectile et l'ennemi sont supprimés.
    """
    for tir in tiroir_tirs:
        ennemis_touches = arcade.check_for_collision_with_list(tir, tiroir_ennemis)
        if ennemis_touches:
            tir.remove_from_sprite_lists()
            for ennemi in ennemis_touches:
                ennemi.points_de_vie -= 1
                if ennemi.points_de_vie <= 0:
                    ennemi.remove_from_sprite_lists()