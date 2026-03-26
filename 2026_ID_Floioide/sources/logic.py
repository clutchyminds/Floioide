import arcade

def gerer_collisions(tiroirs):
    if "attaques" not in tiroirs or not tiroirs["attaques"]:
        return
    
    if "joueur" in tiroirs and len(tiroirs["joueur"]) > 0:
        joueur = tiroirs["joueur"][0]
    else:
        return

    for attaque in tiroirs["attaques"]:
        listes_a_verifier = []
        if "ennemis" in tiroirs: listes_a_verifier.append(tiroirs["ennemis"])
        if "boss" in tiroirs: listes_a_verifier.append(tiroirs["boss"])
        
        ennemis_touches = []
        for liste in listes_a_verifier:
            touches = arcade.check_for_collision_with_list(attaque, liste)
            ennemis_touches.extend(touches)
        
        if not hasattr(attaque, "deja_touche"):
            attaque.deja_touche = set()

        for ennemi in ennemis_touches:
            if ennemi not in attaque.deja_touche:
                multiplicateur = 2 if "argentx2.png" in joueur.inventaire_charmes else 1

                # --- CAS A : BOSS ET NOUVEAUX MOBS ---
                if hasattr(ennemi, "invul_timer"):
                    if ennemi.invul_timer <= 0:
                        # On récupère les stats custom (si elles existent), sinon des valeurs par défaut
                        gains = getattr(ennemi, "drop_hit", 2)
                        temps_invul = getattr(ennemi, "temps_invul", 0.75)
                        
                        joueur.monnaie += (gains * multiplicateur)
                        ennemi.pv -= 1
                        ennemi.invul_timer = temps_invul
                
                # --- CAS B : ANCIENS MOBS NORMAUX ---
                else:
                    if hasattr(ennemi, "pv"):
                        ennemi.pv -= 1
                        joueur.monnaie += (1 * multiplicateur)
                    elif hasattr(ennemi, "points_de_vie"):
                        ennemi.points_de_vie -= 1
                        joueur.monnaie += (2 * multiplicateur)
                
                # On valide la touche pour ne pas infliger 60 dégâts en 1 frame !
                attaque.deja_touche.add(ennemi)

                # --- VÉRIFICATION MORT ---
                vie = getattr(ennemi, "pv", getattr(ennemi, "points_de_vie", 0))
                if vie <= 0:
                    if hasattr(ennemi, "drop_death"):
                        joueur.monnaie += (ennemi.drop_death * multiplicateur)
                        
                    if hasattr(ennemi, "au_deces"):
                        nouveaux = ennemi.au_deces()
                        if nouveaux:
                            for n in nouveaux:
                                tiroirs["boss"].append(n)
                                
                    ennemi.remove_from_sprite_lists()