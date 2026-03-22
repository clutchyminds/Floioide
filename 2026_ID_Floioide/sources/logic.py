import arcade

def gerer_collisions(tiroirs):
    if "attaques" not in tiroirs or not tiroirs["attaques"]:
        return

    for attaque in tiroirs["attaques"]:
        # On vérifie les collisions avec les ENNEMIS et les BOSS
        cibles = []
        if "ennemis" in tiroirs: cibles.extend(tiroirs["ennemis"])
        if "boss" in tiroirs: cibles.extend(tiroirs["boss"])
        
        ennemis_touches = arcade.check_for_collision_with_list(attaque, arcade.SpriteList(use_spatial_hash=False, sprite_list=cibles))
        
        if not hasattr(attaque, "deja_touche"):
            attaque.deja_touche = set()

        for ennemi in ennemis_touches:
            # --- CAS A : C'est un BOSS (avec sécurité invul_timer) ---
            if hasattr(ennemi, "invul_timer"):
                if ennemi.invul_timer <= 0:
                    ennemi.pv -= 1
                    ennemi.invul_timer = 0.75 # Sécurité de 0.75s
            
            # --- CAS B : C'est un MOB normal ou P3 ---
            else:
                if ennemi not in attaque.deja_touche:
                    # On gère les deux noms de variables possibles (pv ou points_de_vie)
                    if hasattr(ennemi, "pv"):
                        ennemi.pv -= 1
                    elif hasattr(ennemi, "points_de_vie"):
                        ennemi.points_de_vie -= 1
                    
                    attaque.deja_touche.add(ennemi)

            # --- VÉRIFICATION MORT ---
            vie = getattr(ennemi, "pv", getattr(ennemi, "points_de_vie", 0))
            if vie <= 0:
                ennemi.remove_from_sprite_lists()