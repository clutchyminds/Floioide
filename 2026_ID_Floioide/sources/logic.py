import arcade
import random

def gerer_collisions(tiroirs):
    """ Gère les impacts des attaques sur les ennemis et les boss """
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
        
        # Initialise le set de détection pour éviter les dégâts multiples par frame
        if not hasattr(attaque, "deja_touche"):
            attaque.deja_touche = set()

        for ennemi in ennemis_touches:
            if ennemi not in attaque.deja_touche:
                multiplicateur = 2 if "argentx2.png" in joueur.inventaire_charmes else 1

                # On vérifie l'invulnérabilité du mob s'il en a une
                if hasattr(ennemi, "invul_timer"):
                    if ennemi.invul_timer <= 0:
                        # ON ENLÈVE EXACTEMENT 1 DÉGÂT
                        if hasattr(ennemi, "pv"): ennemi.pv -= 1
                        elif hasattr(ennemi, "points_de_vie"): ennemi.points_de_vie -= 1
                        
                        gains = getattr(ennemi, "drop_hit", 1)
                        joueur.monnaie += (gains * multiplicateur)
                        ennemi.invul_timer = getattr(ennemi, "temps_invul", 0.5)
                        attaque.deja_touche.add(ennemi)
                else:
                    # Si pas d'invul_timer, il prend 1 dégât direct
                    if hasattr(ennemi, "pv"): ennemi.pv -= 1
                    elif hasattr(ennemi, "points_de_vie"): ennemi.points_de_vie -= 1
                    
                    joueur.monnaie += (1 * multiplicateur)
                    attaque.deja_touche.add(ennemi)

                # --- VÉRIFICATION MORT ---
                vie_actuelle = getattr(ennemi, "vie", getattr(ennemi, "pv", getattr(ennemi, "points_de_vie", 0)))
                
                if vie_actuelle <= 0:
                    if hasattr(ennemi, "drop_death"): joueur.monnaie += (ennemi.drop_death * multiplicateur)
                    elif not hasattr(ennemi, "invul_timer"): joueur.monnaie += (2 * multiplicateur)
                        
                    if hasattr(ennemi, "au_deces"):
                        nouveaux = ennemi.au_deces()
                        if nouveaux:
                            for n in nouveaux:
                                if "boss" in tiroirs: tiroirs["boss"].append(n)
                                else: tiroirs["ennemis"].append(n)
                                
                    ennemi.remove_from_sprite_lists()

def gerer_separation_mobs(liste_mobs, liste_murs):
    """ 
    Empêche les mobs de se chevaucher (Anti-stacking).
    S'ils se touchent, ils sont poussés vers la zone libre la plus proche.
    """
    for i, mob in enumerate(liste_mobs):
        # On vérifie les collisions avec les autres mobs
        # On utilise une boucle simple pour éviter de se comparer à soi-même
        for j in range(i + 1, len(liste_mobs)):
            autre = liste_mobs[j]
            
            if arcade.check_for_collision(mob, autre):
                # Calcul de la direction de séparation
                diff_x = mob.center_x - autre.center_x
                diff_y = mob.center_y - autre.center_y
                
                # Sécurité si les deux sont exactement au même pixel
                if diff_x == 0 and diff_y == 0:
                    diff_x = 1
                
                # Distance pour normalisation
                dist = (diff_x**2 + diff_y**2)**0.5
                if dist == 0: dist = 1
                
                # Force de poussée (2 pixels)
                poussee_x = (diff_x / dist) * 2
                poussee_y = (diff_y / dist) * 2
                
                # Appliquer la poussée au MOB A (si pas de mur)
                mob.center_x += poussee_x
                if arcade.check_for_collision_with_list(mob, liste_murs):
                    mob.center_x -= poussee_x
                    
                mob.center_y += poussee_y
                if arcade.check_for_collision_with_list(mob, liste_murs):
                    mob.center_y -= poussee_y
                
                # Appliquer la poussée inverse au MOB B (si pas de mur)
                autre.center_x -= poussee_x
                if arcade.check_for_collision_with_list(autre, liste_murs):
                    autre.center_x += poussee_x
                    
                autre.center_y -= poussee_y
                if arcade.check_for_collision_with_list(autre, liste_murs):
                    autre.center_y += poussee_y


def separer_mobs(liste_mobs, liste_murs):
    """ Éloigne les mobs les uns des autres s'ils se chevauchent. """
    for i in range(len(liste_mobs)):
        for j in range(i + 1, len(liste_mobs)):
            mob_a = liste_mobs[i]
            mob_b = liste_mobs[j]
            
            if arcade.check_for_collision(mob_a, mob_b):
                # Calcul de la distance
                dx = mob_a.center_x - mob_b.center_x
                dy = mob_a.center_y - mob_b.center_y
                
                # Sécurité si superposés exactement
                if dx == 0 and dy == 0:
                    dx, dy = random.choice([-1, 1]), random.choice([-1, 1])
                    
                dist = (dx**2 + dy**2)**0.5
                force = 2.0  # Force de répulsion (ajustable)
                
                push_x = (dx / dist) * force
                push_y = (dy / dist) * force
                
                # Pousser Mob A
                mob_a.center_x += push_x
                if liste_murs and arcade.check_for_collision_with_list(mob_a, liste_murs):
                    mob_a.center_x -= push_x
                mob_a.center_y += push_y
                if liste_murs and arcade.check_for_collision_with_list(mob_a, liste_murs):
                    mob_a.center_y -= push_y
                    
                # Pousser Mob B dans l'autre sens
                mob_b.center_x -= push_x
                if liste_murs and arcade.check_for_collision_with_list(mob_b, liste_murs):
                    mob_b.center_x += push_x
                mob_b.center_y -= push_y
                if liste_murs and arcade.check_for_collision_with_list(mob_b, liste_murs):
                    mob_b.center_y += push_y