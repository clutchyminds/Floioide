from math import dist
import math
import random 
import os
import arcade
from sources.constantes import DOSSIER_DATA, GRAVITE, TAILLE_TUILE, VITESSE_MARCHE

class EntiteAnimee(arcade.Sprite):
    def __init__(self, x, y, taille=1.0):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = taille
        
        # Variables d'animation (pour éviter le crash AttributeError)
        self.textures = []
        self.frame_actuelle = 0
        self.temps_ecoule = 0
        self.vitesse_animation = 0.15
        
        # Variables de mouvement
        self.timer_dash = 0
        self.change_x = 2 # Vitesse de patrouille
        self.x_depart = x
        self.distance_cible = random.randint(100, 300)

    def orienter_vers_joueur(self, joueur):
        # Si tes mobs regardaient dans le mauvais sens, on inverse ici :
        # Si le joueur est à droite, on ne flip pas (False), sinon on flip (True)
        if joueur.center_x > self.center_x:
            self.flipped_horizontally = False 
        else:
            self.flipped_horizontally = True

    def logique_sol(self, liste_hitbox):
        # 1. Appliquer la gravité
        self.change_y -= GRAVITE
        self.center_y += self.change_y

        # 2. Collision sol + "Anti-blocage" (remonter si dans un bloc)
        blocs_touches = arcade.check_for_collision_with_list(self, liste_hitbox)
        if blocs_touches:
            for bloc in blocs_touches:
                # Si on tombe ou si on est déjà trop bas dans le bloc
                if self.change_y < 0 or self.bottom < bloc.top:
                    self.bottom = bloc.top # On se pose au-dessus
                    self.change_y = 0
        
        # 3. Patrouille (Gauche à Droite)
        self.center_x += self.change_x
        if abs(self.center_x - self.x_depart) >= self.distance_cible:
            self.change_x *= -1
            self.x_depart = self.center_x
            self.distance_cible = random.randint(100, 400)
            
class Joueur(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=0.4)

        self.timer_dash = 0

        self.flipped_horizontally = False

        self.dernier_coup_timer = 0

        self.en_attaque = False
        self.cote_attaque = 1  # 1 pour droite, -1 pour gauche

        self.monnaie = 100
        self.eau = 100       # De 0 à 100
        self.energie = 0     # Commence à 0, monte à 100
        self.timer_energie = 0

        self.en_escalade = False
        self.en_dash = False

        self.vie_max = 20
        self.vie = 20
        
        self.inventaire = [None] * 5  # 5 slots vides

        # 1. Chargement de l'image de base (Idle)
        # Chemin selon l'image : data/player/player.png
        self.tex_idle = arcade.load_texture(os.path.join(DOSSIER_DATA, "player", "player.png"))        
        # 2. Chargement des animations (Toutes dans data/player/mouvements)
        # Définir le chemin vers ton dossier regroupé
        chemin_mouvements = os.path.join(DOSSIER_DATA, "player", "mouvements")

        # Lister tous les fichiers présents dans ce dossier
        tous_les_fichiers = sorted(os.listdir(chemin_mouvements))

        # Fonction pour extraire les images selon le début de leur nom
        def charger_liste(prefixe):
            liste = []
            for f in tous_les_fichiers:
                if f.startswith(prefixe) and f.endswith(".png"):
                    liste.append(arcade.load_texture(os.path.join(chemin_mouvements, f)))
            return liste

        # Assigner les animations en fonction des noms visibles sur ta capture
        self.anims_marche = charger_liste("avancer")   # Charge avancer (1).png, etc.
        self.anims_dash = charger_liste("Dash")        # Charge Dash.png
        self.anims_escalade = charger_liste("grimper") # Charge grimper (1).png, etc.

        self.texture = self.tex_idle

        self.etat = "IDLE"
        self.textures_attaque = []
        # --- CHARGEMENT DES ATTAQUES ---
        self.textures_attaque = []
        chemin_attaque = os.path.join(DOSSIER_DATA, "player", "attaque")
        
        # Remplace "1, 6" selon le nombre de frames que tu as. 
        # (Ici ça chargera attaque1.png jusqu'à attaque5.png)
        for i in range(1, 13): 
            nom_fichier = f"attaque{i}.png" # <-- Mets le bon nom ici
            tex = arcade.load_texture(os.path.join(chemin_attaque, nom_fichier))
            self.textures_attaque.append(tex)

    def update_animation(self, delta_time=1/60):
        # --- 1. SÉCURITÉ : Si aucune texture n'est chargée, on arrête ---
        if self.etat == "ATTAQUE":
            textures_a_utiliser = self.textures_attaque
        elif self.en_dash:
            textures_a_utiliser = self.anims_dash
        elif self.en_escalade:
            textures_a_utiliser = self.anims_escalade
        elif abs(self.change_x) > 0.1:
            textures_a_utiliser = self.anims_marche
        else:
            # On utilise une liste contenant juste l'image IDLE
            textures_a_utiliser = [self.tex_idle]

        if not textures_a_utiliser:
            return

        # --- 2. GESTION DU TIMER ---
        self.temps_ecoule += delta_time
        vitesse = 0.05 if self.etat == "ATTAQUE" else self.vitesse_animation

        if self.temps_ecoule > vitesse:
            self.temps_ecoule = 0
            self.frame_actuelle += 1

            # --- 3. LOGIQUE SELON L'ÉTAT ---
            if self.etat == "ATTAQUE":
                if self.frame_actuelle >= len(self.textures_attaque):
                    self.frame_actuelle = 0
                    self.etat = "IDLE"  # On repasse en mode normal
                else:
                    self.texture = self.textures_attaque[self.frame_actuelle]
            else:
                # Animation normale (IDLE/MARCHE)
                self.frame_actuelle %= len(textures_a_utiliser)
                self.texture = textures_a_utiliser[self.frame_actuelle]

        # --- 4. ORIENTATION (Flip / Rotation) ---
        if self.etat == "ATTAQUE" and self.direction_attaque == "HAUT":
            self.angle = 90
        else:
            self.angle = 0
            if hasattr(self, "flipped_horizontally"):
                if self.flipped_horizontally:
                    self.width = -abs(self.width)
                else:
                    self.width = abs(self.width)
        if self.en_attaque:
            # On utilise tes images d'attaque (ex: attaque1, attaque2...)
            # Assure-toi d'avoir une liste self.textures_attaque chargée
            self.texture = self.textures_attaque[self.frame_actuelle % len(self.textures_attaque)]
        
        # Gestion du miroir (Flip) selon la souris
        if self.cote_attaque == -1:
            self.texture = self.texture.flip_left_right()

    def escalader(self, liste_murs, direction_x):
        # On vérifie s'il y a un mur juste à côté de nous dans la direction où on avance
        mur_touche = arcade.check_for_collision_with_list(self, liste_murs)
        
        if mur_touche and direction_x != 0:
            self.en_escalade = True
            self.change_y = VITESSE_MARCHE # On monte à la même vitesse qu'on marche
        else:
            self.en_escalade = False


class Boss(EntiteAnimee):
    def __init__(self, x, y):
        # On définit la taille désirée une seule fois ici (ex: 4.0)
        self.taille_fixe = 4.0 
        super().__init__(x, y, taille=self.taille_fixe)
        
        self.textures_attaque = []
        self.textures_pause = []
        
        d = os.path.join(DOSSIER_DATA, "boss", "test")
        
        if os.path.exists(d):
            fichiers = sorted(os.listdir(d))
            for f in fichiers:
                if f.startswith("attaque") and f.endswith(".png"):
                    self.textures_attaque.append(arcade.load_texture(os.path.join(d, f)))
                elif f.startswith("pause") and f.endswith(".png"):
                    self.textures_pause.append(arcade.load_texture(os.path.join(d, f)))

        self.etat = "ATTAQUE"
        self.vitesse_animation = 0.12
        self.timer_pause = 0
        self.frame_actuelle = 0
        self.cible = None 
        self.vie = 50  # Modifie selon la résistance voulue

        if self.textures_attaque:
            self.texture = self.textures_attaque[0]

    def update_animation(self, delta_time=1/60):
        self.temps_ecoule += delta_time
        
        # --- Gestion des textures ---
        if self.etat == "ATTAQUE" and self.textures_attaque:
            if self.temps_ecoule > self.vitesse_animation:
                self.temps_ecoule = 0
                self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_attaque)
                self.texture = self.textures_attaque[self.frame_actuelle]
                if self.frame_actuelle == 0:
                    self.etat = "PAUSE"
                    self.timer_pause = 0
        
        elif self.etat == "PAUSE" and self.textures_pause:
            self.timer_pause += delta_time
            if self.temps_ecoule > 0.3:
                self.temps_ecoule = 0
                self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_pause)
                self.texture = self.textures_pause[self.frame_actuelle]
            if self.timer_pause >= 5.0:
                self.etat = "ATTAQUE"

        # --- GESTION DU REGARD (SANS TÊTE EN BAS) ---
        if self.cible:
            # On utilise self.taille_fixe pour rester cohérent
            if self.cible.center_x < self.center_x:
                # Si tes images regardent à GAUCHE par défaut :
                self.width = abs(self.width)  # Largeur normale
            else:
                # On force la largeur en négatif pour le miroir horizontal uniquement
                self.width = -abs(self.width) 
            
            # Note : On ne touche JAMAIS à self.height ou self.scale ici 
            # pour éviter que le boss ne se retrouve la tête en bas.

        def logique_ia(self, joueur):
            pass
class ProjectileEnnemi(arcade.Sprite):
    def __init__(self, x, y, cible_x, cible_y, degats=1):
        super().__init__(os.path.join(DOSSIER_DATA, "mobs", "projectile.png"), 0.5) # Ajuste le chemin
        self.center_x = x
        self.center_y = y
        self.degats = degats
        
        # Calcul de la trajectoire
        angle = math.atan2(cible_y - y, cible_x - x)
        self.change_x = math.cos(angle) * 5
        self.change_y = math.sin(angle) * 5
        self.angle = math.degrees(angle)

    def update(self, delta_time=1/60): 
        self.center_x += self.change_x
        self.center_y += self.change_y

class Mob(EntiteAnimee):
    def __init__(self, x, y, vie_max, volant, dossier_anim):
        super().__init__(x, y)
        self.vie_max = vie_max
        self.points_de_vie = vie_max
        self.volant = volant
        self.temps_de_vie = 0
        self.timer_attaque = 0
        self.cible = None
        
        # Chargement automatique des textures du dossier
        chemin = os.path.join(DOSSIER_DATA, "mobs", dossier_anim)
        if os.path.exists(chemin):
            for fichier in sorted(os.listdir(chemin)):
                if fichier.endswith(".png"):
                    self.textures.append(arcade.load_texture(os.path.join(chemin, fichier)))
        if self.textures:
            self.texture = self.textures[0]

    def dessiner_barre_vie(self):
        if self.points_de_vie < self.max_points_de_vie:
            y_barre = self.top + 10
            largeur = 40
            hauteur = 5
            
            # Calcul du point de départ à gauche (Left) pour centrer la barre
            x_gauche = self.center_x - largeur / 2

            # Barre de fond (Rouge)
            # LBWH = Left, Bottom, Width, Height
            arcade.draw_rect_filled(
                arcade.rect.LBWH(x_gauche, y_barre, largeur, hauteur),
                arcade.color.RED
            )
            
            # Barre de vie actuelle (Verte)
            vie_ratio = max(0, self.points_de_vie / self.max_points_de_vie)
            arcade.draw_rect_filled(
                arcade.rect.LBWH(x_gauche, y_barre, largeur * vie_ratio, hauteur),
                arcade.color.GREEN
            )

    def verifier_despawn(self, delta_time):
        self.temps_de_vie += delta_time
        if self.temps_de_vie >= 120.0: # 2 minutes
            self.remove_from_sprite_lists()

# ================= M롭게 FORET =================
class MobForetAir(Mob):
    def __init__(self, x, y):
        super().__init__(x, y, vie_max=1, volant=True, dossier_anim="foret/air")
        self.vitesse = 4
        self.angle_cercle = 0
        self.max_points_de_vie = 3

    def logique_ia(self, joueur, tirs_ennemis):
        distance = math.dist((self.center_x, self.center_y), (joueur.center_x, joueur.center_y))
        
        # Orientation visuelle
        self.flipped_horizontally = self.center_x > joueur.center_x

        if distance <= 7 * TAILLE_TUILE:
            if distance > 2 * TAILLE_TUILE:
                # S'approche
                angle = math.atan2(joueur.center_y - self.center_y, joueur.center_x - self.center_x)
                self.change_x = math.cos(angle) * self.vitesse
                self.change_y = math.sin(angle) * self.vitesse
            else:
                self.change_x = 0
                self.change_y = 0
                
            # Attaque
            self.timer_attaque += 1/60
            if self.timer_attaque >= 2.0:
                tir = ProjectileEnnemi(self.center_x, self.center_y, joueur, degats=1, vitesse=5, image="foret/air/boule_bleue.png")
                tirs_ennemis.append(tir)
                self.timer_attaque = 0
        else:
            # Cercle
            self.angle_cercle += 0.05
            self.change_x = math.cos(self.angle_cercle) * 2
            self.change_y = math.sin(self.angle_cercle) * 2

    def update_air(self, joueur):
        hauteur_cible = joueur.center_y + 100 # Toujours 100px au-dessus

        self.orienter_vers_joueur(self.joueur)
        
        if self.center_y < hauteur_cible:
            self.change_y = 1.5 # Remonte doucement
        else:
            # Petit mouvement de flottaison sinus
            self.change_y = math.sin(arcade.get_time_total()) * 0.5
    
        self.center_y += self.change_y

class MobForetSol(Mob):
    def __init__(self, x, y):
        super().__init__(x, y, vie_max=4, volant=False, dossier_anim="foret/sol/gentil")
        self.enerve = False
        self.vitesse = 2
        self.degats_contact = 0
        self.max_points_de_vie = 3

    def devenir_enerve(self):
        if not self.enerve:
            self.enerve = True
            self.degats_contact = 4
            self.textures.clear()
            # Charger les textures énervées
            chemin = os.path.join(DOSSIER_DATA, "mobs", "foret", "sol", "nrv")
            if os.path.exists(chemin):
                for f in sorted(os.listdir(chemin)):
                    if f.endswith(".png"):
                        self.textures.append(arcade.load_texture(os.path.join(chemin, f)))

    def logique_ia(self, joueur, tirs_ennemis):
        if self.points_de_vie < self.vie_max:
            self.devenir_enerve()

        if self.enerve:
            # Dash vers le joueur
            if self.center_x < joueur.center_x:
                self.change_x = 6
            else:
                self.change_x = -6
        else:
            # Patrouille simple
            self.timer_attaque += 1/60
            if self.timer_attaque > 3.0:
                self.change_x = random.choice([-2, 2])
                self.timer_attaque = 0

    def update_sol(self, liste_murs):
        # 1. Gravité : descendre si on ne touche pas la hit-box
        self.change_y -= 0.5 # Utilise la constante GRAVITE si définie
        self.center_y += self.change_y
        # 2. Test de collision avec le calque "hit-box" (liste_murs)
        blocs_touches = arcade.check_for_collision_with_list(self, liste_murs)
    
        if blocs_touches:
            for bloc in blocs_touches:
                # Si on est "coincé" dans un bloc, TP vers le haut
                if self.bottom < bloc.top and self.top > bloc.bottom:
                    self.bottom = bloc.top
                    self.change_y = 0

# ================= MOBS DESERT =================
class MobDesertAir(Mob):
    def __init__(self, x, y, taille=1.2):
        super().__init__(x, y, vie_max=2, volant=True, dossier_anim="desert/air", taille=taille)
        self.degats_contact = 1
        self.max_points_de_vie = 3

    def logique_ia(self, joueur, tirs_ennemis):
        distance = math.dist((self.center_x, self.center_y), (joueur.center_x, joueur.center_y))
        if distance <= 10 * TAILLE_TUILE:
            angle = math.atan2(joueur.center_y - self.center_y, joueur.center_x - self.center_x)
            self.change_x = math.cos(angle) * 7 # Très rapide
            self.change_y = math.sin(angle) * 7

    def update_air(self, joueur):
        hauteur_cible = joueur.center_y + 100 # Toujours 100px au-dessus
    
        if self.center_y < hauteur_cible:
            self.change_y = 1.5 # Remonte doucement
        else:
            # Petit mouvement de flottaison sinus
            self.change_y = math.sin(arcade.get_time_total()) * 0.5
    
        self.center_y += self.change_y

class MobDesertSol(Mob):
    def __init__(self, x, y):
        super().__init__(x, y, vie_max=6, volant=False, dossier_anim="desert/sol")
        self.degats_contact = 3

    def logique_ia(self, joueur, tirs_ennemis):
        distance = math.dist((self.center_x, self.center_y), (joueur.center_x, joueur.center_y))
        if distance <= 5 * TAILLE_TUILE:
            self.change_x = 1.5 if joueur.center_x > self.center_x else -1.5

    def update_sol(self, liste_murs):
        # 1. Gravité : descendre si on ne touche pas la hit-box
        self.change_y -= 0.5 # Utilise la constante GRAVITE si définie
        self.center_y += self.change_y
        # 2. Test de collision avec le calque "hit-box" (liste_murs)
        blocs_touches = arcade.check_for_collision_with_list(self, liste_murs)
    
        if blocs_touches:
            for bloc in blocs_touches:
                # Si on est "coincé" dans un bloc, TP vers le haut
                if self.bottom < bloc.top and self.top > bloc.bottom:
                    self.bottom = bloc.top
                    self.change_y = 0

# ================= MOBS VILLE =================
class MobVilleAir(Mob):
    def __init__(self, x, y):
        super().__init__(x, y, vie_max=5, volant=True, dossier_anim="ville/air")
        self.max_points_de_vie = 3

    def logique_ia(self, joueur, tirs_ennemis):
        distance = math.dist((self.center_x, self.center_y), (joueur.center_x, joueur.center_y))
        if distance <= 14 * TAILLE_TUILE:
            if distance > 5 * TAILLE_TUILE:
                angle = math.atan2(joueur.center_y - self.center_y, joueur.center_x - self.center_x)
                self.change_x = math.cos(angle) * 2
                self.change_y = math.sin(angle) * 2
            else:
                self.change_x, self.change_y = 0, 0

            self.timer_attaque += 1/60
            if self.timer_attaque >= 2.0:
                # Rafale de 3 balles
                for i in range(-1, 2):
                    tir = ProjectileEnnemi(self.center_x, self.center_y + (i*10), joueur, degats=2, vitesse=6, image="ville/air/balle_grise.png")
                    tirs_ennemis.append(tir)
                self.timer_attaque = 0

    def update_air(self, joueur):
        hauteur_cible = joueur.center_y + 100 # Toujours 100px au-dessus
    
        if self.center_y < hauteur_cible:
            self.change_y = 1.5 # Remonte doucement
        else:
            # Petit mouvement de flottaison sinus
            self.change_y = math.sin(arcade.get_time_total()) * 0.5
    
        self.center_y += self.change_y

class MobVilleSol(Mob):
    def __init__(self, x, y):
        super().__init__(x, y, vie_max=2, volant=False, dossier_anim="ville/sol")
        self.max_points_de_vie = 3

    def logique_ia(self, joueur, tirs_ennemis):
        distance = math.dist((self.center_x, self.center_y), (joueur.center_x, joueur.center_y))
        if distance <= 15 * TAILLE_TUILE:
            self.change_x = 0 # S'arrête
            self.timer_attaque += 1/60
            if self.timer_attaque >= 3.0:
                tir = ProjectileEnnemi(self.center_x, self.center_y, joueur, degats=3, vitesse=4, image="ville/sol/grosse_balle.png", taille=2.0)
                tirs_ennemis.append(tir)
                self.timer_attaque = 0
        else:
            # Se déplace aléatoirement
            self.timer_attaque += 1/60
            if self.timer_attaque > 4.0:
                self.change_x = random.choice([-1.5, 0, 1.5])
                self.timer_attaque = 0
        
    def update_sol(self, liste_murs):
        # 1. Gravité : descendre si on ne touche pas la hit-box
        self.change_y -= 0.5 # Utilise la constante GRAVITE si définie
        self.center_y += self.change_y
        # 2. Test de collision avec le calque "hit-box" (liste_murs)
        blocs_touches = arcade.check_for_collision_with_list(self, liste_murs)
    
        if blocs_touches:
            for bloc in blocs_touches:
                # Si on est "coincé" dans un bloc, TP vers le haut
                if self.bottom < bloc.top and self.top > bloc.bottom:
                    self.bottom = bloc.top
                    self.change_y = 0
        
class PNJ(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(center_x=x, center_y=y, scale=0.5)
        chemin_pnj = os.path.join(DOSSIER_DATA, "mobs", "PNJ")
        
        # Sécurité si les images n'existent pas encore
        try:
            self.tex1 = arcade.load_texture(os.path.join(chemin_pnj, "PNJ1.png"))
            self.tex2 = arcade.load_texture(os.path.join(chemin_pnj, "PNJ2.png"))
        except:
            self.tex1 = arcade.make_soft_square_texture(50, arcade.color.BLUE)
            self.tex2 = arcade.make_soft_square_texture(50, arcade.color.LIGHT_BLUE)

        self.texture = self.tex1
        self.timer_anim = 0
        self.est_survole = False

    def update_animation(self, delta_time=1/60):
        # 1. Animation (switch toutes les 0.5s)
        self.timer_anim += delta_time
        if self.timer_anim > 0.5:
            self.timer_anim = 0
            self.texture = self.tex2 if self.texture == self.tex1 else self.tex1

        # 2. Changement de couleur au survol
        if self.est_survole:
            self.color = arcade.color.YELLOW
        else:
            self.color = arcade.color.WHITE

    def draw(self, **kwargs):
        # 1. Dessiner le sprite normalement
        super().draw(**kwargs)
        
        # 2. Si survolé, on ajoute un contour blanc (Glow effect)
        if self.est_survole:
            # On dessine un rectangle vide autour du sprite
            # On utilise les dimensions du sprite
            arcade.draw_rect_outline(
                rect=self.rect,
                color=arcade.color.WHITE,
                border_width=3
            )

class EffetAttaque(arcade.Sprite):
    def __init__(self, joueur, dossier_attaque):
        super().__init__()
        # 1. Orientation basée sur le sprite du joueur
        # On regarde si le joueur est "flipped" ou non
        self.direction = -1 if joueur.flipped_horizontally else 1
        
        # 2. Positionnement
        distance = 50 
        self.center_x = joueur.center_x + (distance * self.direction)
        self.center_y = joueur.center_y
        
        # 3. Chargement des 12 textures
        self.textures = []
        for i in range(1, 13): # de 1 à 12
            nom_fichier = os.path.join(dossier_attaque, f"attaque{i}.png")
            if os.path.exists(nom_fichier):
                tex = arcade.load_texture(nom_fichier)
                if self.direction == -1:
                    tex = tex.flip_left_right()
                self.textures.append(tex)
        
        if self.textures:
            self.texture = self.textures[0]
        
        self.frame = 0
        self.timer = 0
        # 0.4s pour 12 images => ~0.0333s par image
        self.vitesse_frame = 0.4 / 12 

    def update_animation(self, delta_time=1/60):
        self.timer += delta_time
        if self.timer > self.vitesse_frame:
            self.timer = 0
            self.frame += 1
            if self.frame < len(self.textures):
                self.texture = self.textures[self.frame]
            else:
                self.remove_from_sprite_lists() # Fin de l'attaques

class ProjectileEnnemi(arcade.Sprite):
    def __init__(self, x, y, joueur, degats=1, vitesse=5, image="foret/air/boule_bleue.png"):
        # On construit le chemin vers l'image
        chemin_image = os.path.join(DOSSIER_DATA, "mobs", image)
        super().__init__(chemin_image, scale=0.4)
        
        self.center_x = x
        self.center_y = y
        self.degats = degats
        
        # Calcul de l'angle vers le joueur
        diff_x = joueur.center_x - x
        diff_y = joueur.center_y - y
        angle = math.atan2(diff_y, diff_x)
        
        # Application de la vitesse passée en argument
        self.change_x = math.cos(angle) * vitesse
        self.change_y = math.sin(angle) * vitesse

    def update(self, delta_time: float = 1/60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        # Supprimer si hors écran (optionnel mais recommandé)