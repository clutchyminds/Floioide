import arcade

def gerer_collisions(tiroir_tirs, tiroir_ennemis):
    """
    Vérifie si les projectiles touchent les ennemis.
    Si oui, le projectile et l'ennemi sont supprimés.
    """
    for tir in tiroir_tirs:
        # On vérifie si ce tir touche un ou plusieurs ennemis
        ennemis_touches = arcade.check_for_collision_with_list(tir, tiroir_ennemis)
        
        if ennemis_touches:
            tir.remove_from_sprite_lists() # Le projectile disparaît
            for ennemi in ennemis_touches:
                ennemi.remove_from_sprite_lists() # L'ennemi disparaît