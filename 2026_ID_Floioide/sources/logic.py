import arcade

def gerer_collisions(tiroirs):
    # 1. On vérifie si une attaque est en cours
    if "attaques" not in tiroirs or not tiroirs["attaques"]:
        return
    
    if "joueur" in tiroirs and len(tiroirs["joueur"]) > 0:
        joueur = tiroirs["joueur"][0]
    else:
        return

    for attaque in tiroirs["attaques"]:
        # 2. On prépare la liste des cibles (mobs + boss)
        # Au lieu de créer une SpriteList compliquée, on utilise check_for_collision_with_lists
        listes_a_verifier = []
        if "ennemis" in tiroirs: listes_a_verifier.append(tiroirs["ennemis"])
        if "boss" in tiroirs: listes_a_verifier.append(tiroirs["boss"])
        
        # On récupère tous les ennemis touchés dans ces listes
        ennemis_touches = []
        for liste in listes_a_verifier:
            touches = arcade.check_for_collision_with_list(attaque, liste)
            ennemis_touches.extend(touches)
        
        # 3. On initialise le set anti-multi-frappe si besoin
        if not hasattr(attaque, "deja_touche"):
            attaque.deja_touche = set()

        # 4. On applique les dégâts
        # 4. On applique les dégâts
        for ennemi in ennemis_touches:
            if ennemi not in attaque.deja_touche:
                
                # Vérifie le multiplicateur
                multiplicateur = 2 if "argentx2.png" in joueur.inventaire_charmes else 1

                # --- CAS A : BOSS ---
                if hasattr(ennemi, "invul_timer"):
                    if ennemi.invul_timer <= 0:
                        joueur.monnaie += (2 * multiplicateur)
                        ennemi.pv -= 1
                        ennemi.invul_timer = 0.75
                
                # --- CAS B : MOBS NORMAUX ---
                else:
                    if hasattr(ennemi, "pv"):
                        ennemi.pv -= 1
                        joueur.monnaie += (1 * multiplicateur)
                    elif hasattr(ennemi, "points_de_vie"):
                        ennemi.points_de_vie -= 1
                        joueur.monnaie += (2 * multiplicateur)
                    
                    # On marque comme touché par cette instance d'attaque
                    attaque.deja_touche.add(ennemi)

                # --- VÉRIFICATION MORT ---
                vie = getattr(ennemi, "pv", getattr(ennemi, "points_de_vie", 0))
                if vie <= 0:
                    # Si c'est un boss qui doit spawn la phase suivante
                    if hasattr(ennemi, "au_deces"):
                        nouveaux = ennemi.au_deces()
                        if nouveaux:
                            for n in nouveaux:
                                tiroirs["boss"].append(n)
                    
                    ennemi.remove_from_sprite_lists()