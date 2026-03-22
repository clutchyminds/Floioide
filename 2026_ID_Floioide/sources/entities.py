from math import dist
import math
import random 
import os
import arcade
from sources.constantes import DOSSIER_DATA, DOSSIER_BOSS, GRAVITE, TAILLE_TUILE, VITESSE_MARCHE, VITESSE_DASH, VITESSE_SAUT, VITESSE_TIR, DISTANCE_MAX_TIR
from arcade.hitbox import HitBox


class EntiteAnimee(arcade.Sprite):
    def __init__(self, x, y, scale=1.0):
        # appel du constructeur parent
        super().__init__(scale=scale)
        self.center_x = x
        self.center_y = y
        
        # variables pour l'animation
        self.frame_actuelle = 0
        self.temps_ecoule = 0
        self.vitesse_animation = 0.1
        self.etat = "IDLE"
        
        # stockage de la hitbox personnalisee
        self.hit_box_perso = None
        
    def update_animation(self, delta_time=1/60):
        # gestion du temps pour les images
        self.temps_ecoule += delta_time

class Joueur(EntiteAnimee):
    def __init__(self, x, y):
        self.flip_left_right = False


        # --- SYSTÈME D'INVENTAIRE (4 CASES) ---
        self.inventaire = [None, None, None, None] # 4 emplacements vides
        self.index_inventaire = 0

        # initialisation avec scale 0.4
        super().__init__(x, y, scale=0.1)
        
        # dossiers des images
        doss_p = os.path.join(DOSSIER_DATA, "player")
        doss_m = os.path.join(doss_p, "mouvements")
        
        # 1. chargement des textures de base
        self.tex_idle = arcade.load_texture(os.path.join(doss_p, "player.png"))
        self.tex_saut = arcade.load_texture(os.path.join(doss_m, "saut.png"))
        self.tex_dash = arcade.load_texture(os.path.join(doss_m, "Dash.png"))
        
        # animations de marche (1 a 4)
        self.anims_marche = []
        for i in range(1, 5):
            self.anims_marche.append(arcade.load_texture(os.path.join(doss_m, f"avancer ({i}).png")))
            
        # animations de grimper (1 a 3)
        self.anims_grimper = []
        for i in range(1, 4):
            self.anims_grimper.append(arcade.load_texture(os.path.join(doss_m, f"grimper ({i}).png")))

        # animations d attaque (1 a 12)
        self.textures_attaque = []
        for i in range(1, 13):
            self.textures_attaque.append(arcade.load_texture(os.path.join(doss_p, "attaque", f"attaque{i}.png")))

        
        
        # 2. variables de statistiques (noms corriges pour main.py)
        self.vie = 20              # utilise "vie" au lieu de "pv"
        self.eau = 100
        self.nrj_dash = 100
        self.monnaie = 0
        
        self.energie = 100
        self.timer_dash = 0        
        self.timer_attaque = 0
        self.timer_recup_eau = 0
        self.timer_energie = 0
        
        # etats pour l animation
        self.face_gauche = False
        self.en_dash = False
        self.en_escalade = False
        self.au_sol = False
        
        # 3. hitbox fixe obligatoire pour arcade 3.0
        self.hit_box_algorithm = "None"
        t = 45 
        self.hit_box_perso = HitBox([(-t, -t), (t, -t), (t, t), (-t, t)])
        self.hit_box = self.hit_box_perso

    def update_animation(self, delta_time=1/60):
        # calcul du temps pour changer d image
        self.temps_ecoule += delta_time
        
        # choix de la liste d images
        textures_a_voir = [self.tex_idle]
        vit = self.vitesse_animation

        if self.change_x < 0:
            self.flip_left_right = True  # Regarde à gauche
        elif self.change_x > 0:
            self.flip_left_right = False # Regarde à droite

        # logic de selection des images
        if self.etat == "ATTAQUE":
            textures_a_voir = self.textures_attaque
            vit = 0.05
        elif self.en_dash:
            textures_a_voir = [self.tex_dash]
        elif self.en_escalade:
            textures_a_voir = self.anims_grimper
        # si change_y est different de 0, on considere qu'on saute (securite)
        elif abs(self.change_y) > 0.1: 
            textures_a_voir = [self.tex_saut]
        elif abs(self.change_x) > 0.1:
            textures_a_voir = self.anims_marche
        else:
            textures_a_voir = [self.tex_idle]

        # changement d image si le temps est ecoule
        if self.temps_ecoule > vit:
            self.temps_ecoule = 0
            self.frame_actuelle += 1
            
            # remise a zero si fin de liste
            if self.frame_actuelle >= len(textures_a_voir):
                self.frame_actuelle = 0
                if self.etat == "ATTAQUE":
                    self.etat = "IDLE"

            # selection de la texture
            base = textures_a_voir[self.frame_actuelle]
            
            # gestion du sens (gauche ou droite)
            if self.change_x < -0.1: self.face_gauche = True
            elif self.change_x > 0.1: self.face_gauche = False
            
            if self.face_gauche:
                self.texture = base.flip_left_right()
            else:
                self.texture = base

        # securite pour garder la meme hitbox
        self.hit_box = self.hit_box_perso


class Boss(EntiteAnimee):
    def __init__(self, x, y):
        # On définit la taille désirée une seule fois ici (ex: 4.0)
        self.taille_fixe = 4.0 
        super().__init__(x, y)

        self.hit_box_perso = HitBox([(-100, -100), (100, -100), (100, 100), (-100, 100)])
        self.hit_box =self.hit_box_perso
        self.scale = 2.0  # Par exemple, pour un gros boss
        self.points_de_vie = 50
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
        self.hit_box = self.hit_box_perso
        
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

class Ennemi(EntiteAnimee):
    def __init__(self, x, y, dossier, nb_anim=4):
        super().__init__(x, y, scale=0.5)
        
        # chargement automatique des textures
        self.textures_marche = []
        for i in range(1, nb_anim + 1):
            chemin = os.path.join(DOSSIER_DATA, "mobs", dossier, f"mob{i}.png")
            if os.path.exists(chemin):
                self.textures_marche.append(arcade.load_texture(chemin))
        
        if self.textures_marche:
            self.texture = self.textures_marche[0]

        # stats de base
        self.vie = 2
        self.vitesse = 2
        self.direction = 1 # 1 pour droite, -1 pour gauche
        
    def logique_sol(self, liste_murs):
        # deplacement simple
        self.change_x = self.vitesse * self.direction
        
        # inverse la direction si on touche un mur
        if arcade.check_for_collision_with_list(self, liste_murs):
            self.direction *= -1
            self.center_x += self.direction * 5

    def orienter_vers_joueur(self, joueur):
        # on change la direction pour faire face au joueur
        if joueur.center_x < self.center_x:
            self.direction = -1
        else:
            self.direction = 1

    def update_animation(self, delta_time=1/60):
        super().update_animation(delta_time)
        if not self.textures_marche:
            return

        if self.temps_ecoule > self.vitesse_animation:
            self.temps_ecoule = 0
            self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_marche)
            
            base = self.textures_marche[self.frame_actuelle]
            # miroir selon la direction
            if self.direction == -1:
                self.texture = base.flip_left_right()
            else:
                self.texture = base

# on cree des alias pour que main.py ne crashe pas avec les anciens noms
class MobForetSol(Ennemi):
    def __init__(self, x, y):
        super().__init__(x, y, os.path.join("foret", "sol"), nb_anim=4)

class MobDesertSol(Ennemi):
    def __init__(self, x, y):
        super().__init__(x, y, os.path.join("desert", "sol"), nb_anim=4)

class MobVilleSol(Ennemi):
    def __init__(self, x, y):
        super().__init__(x, y, os.path.join("ville", "sol"), nb_anim=4)


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
    def __init__(self, joueur, dossier):
        super().__init__(scale=0.4)
        
        self.direction = -1 if joueur.flip_left_right else 1
        self.center_x = joueur.center_x + (self.direction * 50) # Décale de 50 pixels devant le nez du joueur
        self.center_y = joueur.center_y
        
        # Correction de l'erreur : on utilise flip_left_right
        # Si le joueur regarde à gauche, l'attaque doit être à gauche
        self.direction = -1 if joueur.flip_left_right else 1
        
        # On décale l'effet un peu devant le joueur
        self.center_x += self.direction * 40

        # Chargement des textures
        self.textures = []
        for i in range(1, 13):
            chemin = os.path.join(dossier, f"attaque{i}.png")
            tex = arcade.load_texture(chemin)
            # Si le joueur est retourné, on retourne aussi l'effet
            if self.direction == -1:
                self.textures.append(tex.flip_left_right())
            else:
                self.textures.append(tex)
        
        self.texture = self.textures[0]
        self.frame = 0
        self.timer = 0
        self.vitesse_frame = 0.03 # Vitesse de l'animation

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


# --- systeme de boss ---

class EntiteBoss(arcade.Sprite):
    def __init__(self, x, y, image, scale=1.0):
        super().__init__(image, scale)
        self.center_x = x
        self.center_y = y
        self.pv = 1
        self.pv_max = 1
        self.degats = 1
        self.etat = "idle"
        self.timer_action = 0
        self.timer_tremblement = 0
        self.pos_x_base = x

    def dessiner_barre_vie(self):
        """ Affiche la barre de vie au-dessus du boss (Version Arcade 3.0) """
        if self.pv > 0:
            largeur_totale = 60
            hauteur = 8
            # Calcul du ratio de vie (évite la division par zéro si pv_max n'existe pas)
            max_pv = getattr(self, "pv_max", self.pv)
            ratio = self.pv / max_pv
            
            # 1. Créer les objets rectangles (LBWH = Left, Bottom, Width, Height)
            # Fond rouge
            fond_rect = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale, 
                hauteur
            )
            
            # Barre verte
            vie_rect = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale * ratio, 
                hauteur
            )

            # 2. Dessiner les rectangles avec les nouvelles fonctions
            arcade.draw_rect_filled(fond_rect, arcade.color.RED)
            arcade.draw_rect_filled(vie_rect, arcade.color.GREEN)

    def appliquer_physique(self, murs):
        # gere la gravite et les collisions basiques avec la hit box du decor
        self.change_y -= GRAVITE
        self.center_y += self.change_y
        
        collisions_y = arcade.check_for_collision_with_list(self, murs)
        for mur in collisions_y:
            if self.change_y > 0:
                self.top = mur.bottom
            elif self.change_y < 0:
                self.bottom = mur.top
            self.change_y = 0

        self.center_x += self.change_x
        collisions_x = arcade.check_for_collision_with_list(self, murs)
        for mur in collisions_x:
            if self.change_x > 0:
                self.right = mur.left
            elif self.change_x < 0:
                self.left = mur.right
            self.change_x = 0

# --- CLASSE DE BASE POUR LA PHYSIQUE ET LA VIE ---
class EntiteBossTron(arcade.Sprite):
    def __init__(self, scale=1.0):
        super().__init__(scale=scale) # Initialisation vide pour éviter le bug "multiple values"
        self.pv_max = 0 # Sera défini par les phases
        self.invul_timer = 0

    def appliquer_physique(self, murs):
        # Gravité
        self.change_y -= GRAVITE
        self.center_y += self.change_y
        hit_list = arcade.check_for_collision_with_list(self, murs)
        for mur in hit_list:
            if self.change_y < 0:
                self.bottom = mur.top
                self.change_y = 0
            elif self.change_y > 0:
                self.top = mur.bottom
                self.change_y = 0
                
        # Mouvement X
        self.center_x += self.change_x
        hit_list = arcade.check_for_collision_with_list(self, murs)
        for mur in hit_list:
            if self.change_x > 0: self.right = mur.left
            elif self.change_x < 0: self.left = mur.right
            self.change_x = 0

    def dessiner_barre_vie(self):
        """ Affiche la barre de vie au-dessus du boss (Version Arcade 3.0) """
        if self.pv > 0:
            largeur_totale = 60
            hauteur = 8
            
            # 1. On crée l'objet rectangle pour le FOND (Rouge)
            # arcade.LBWH signifie : Left, Bottom, Width, Height
            rect_fond = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale, 
                hauteur
            )
            # On dessine en passant l'objet + la couleur (2 arguments seulement)
            arcade.draw_rect_filled(rect_fond, arcade.color.RED)

            # 2. On crée l'objet rectangle pour la VIE (Verte)
            max_p = getattr(self, "pv_max", self.pv)
            ratio = self.pv / max_p
            
            rect_vie = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale * ratio, 
                hauteur
            )
            arcade.draw_rect_filled(rect_vie, arcade.color.GREEN)

    def update_boss(self, delta_time, liste_projectiles, murs):
        """ Gère le temps de sécurité pour les dégâts """
        if self.invul_timer > 0:
            self.invul_timer -= delta_time

# --- PROJECTILE (LE BATON) ---
class ProjectileArbre(arcade.Sprite):
    def __init__(self, x, y, joueur):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.degats = 4  # CHANGEMENT : 4 points de dégâts
        self.duree_vie = 5.0
        self.temps_ecoule = 0.0
        
        self.timer_attaque = 0

        chemin_base = os.path.join(DOSSIER_DATA, "boss", "boss arbre")
        self.textures = [arcade.load_texture(os.path.join(chemin_base, f"Attaque.{i}.png")) for i in range(1, 6)]
        self.texture = self.textures[0]
        
        angle = math.atan2(joueur.center_y - self.center_y, joueur.center_x - self.center_x)
        self.change_x = math.cos(angle) * 8 # Rapide
        self.change_y = math.sin(angle) * 8

    def update(self, delta_time: float = 1/60):
        if self.timer_attaque >= 5.0:
            self.timer_attaque = 0

        self.center_x += self.change_x
        self.center_y += self.change_y
        self.temps_ecoule += delta_time
        frame = int((self.temps_ecoule % 0.5) / 0.1)
        if frame < 5: self.texture = self.textures[frame]
        if self.temps_ecoule >= self.duree_vie: self.remove_from_sprite_lists()

# --- PHASES ---
class BossArbreP1(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=1.0)
        self.texture = arcade.load_texture(os.path.join(DOSSIER_DATA, "boss", "boss arbre", "P1.png"))
        self.center_x = x
        self.center_y = y
        self.joueur = joueur
        self.pv = 5
        self.pv_max = 5
        self.timer_tir = 0.0
        self.timer_attaque = 0

    def update_boss(self, delta_time, liste_projectiles, murs):
        super().update_boss(delta_time, liste_projectiles, murs)
        self.appliquer_physique(murs)

        # Lancer le bâton toutes les 5 secondes
        self.timer_tir += delta_time
        if self.timer_tir >= 5.0:
            self.timer_tir = 0
            self.lancer_baton(liste_projectiles)

        self.appliquer_physique(murs)
        if self.invul_timer > 0:
            self.invul_timer -= delta_time

    def au_deces(self):
        # Libère deux P2
        return [BossArbreP2(self.center_x - 40, self.center_y, self.joueur),
                BossArbreP2(self.center_x + 40, self.center_y, self.joueur)]

class BossArbreP2(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=1.0)
        chemin_base = os.path.join(DOSSIER_DATA, "boss", "boss arbre")
        self.tex_sol = arcade.load_texture(os.path.join(chemin_base, "P2.png"))
        self.tex_saut = arcade.load_texture(os.path.join(chemin_base, "P2.saut.png"))
        self.texture = self.tex_sol
        self.center_x, self.center_y = x, y
        self.joueur = joueur
        self.pv = 3
        self.pv_max = 3
        self.degats = 3
        self.timer_saut = 0.0

    def update_boss(self, delta_time, liste_projectiles, murs):
        self.appliquer_physique(murs)
        if self.invul_timer > 0:
            self.invul_timer -= delta_time
        if self.change_y == 0:
            self.texture = self.tex_sol
            self.change_x = 0
            self.timer_saut += delta_time
            if self.timer_saut >= 2.0:
                self.timer_saut = 0.0
                self.change_y = 12
                self.change_x = 5 if self.joueur.center_x > self.center_x else -5
        else:
            self.texture = self.tex_saut

    def au_deces(self):
        # Libère deux P3 (donc 4 au total si les deux P2 meurent)
        return [BossArbreP3(self.center_x - 20, self.center_y, self.joueur),
                BossArbreP3(self.center_x + 20, self.center_y, self.joueur)]

class BossArbreP3(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=0.6)
        self.texture = arcade.load_texture(os.path.join(DOSSIER_DATA, "boss", "boss arbre", "P3.png"))
        self.center_x, self.center_y = x, y
        self.joueur = joueur
        self.pv = 1
        self.pv_max = 1
        self.degats = 1
        self.timer_saut = 0.0

    def update_boss(self, delta_time, liste_projectiles, murs):
        if self.invul_timer > 0:
            self.invul_timer -= delta_time
        self.appliquer_physique(murs)
        if self.change_y == 0:
            self.change_x = 0
            self.timer_saut += delta_time
            if self.timer_saut >= 1.5:
                self.timer_saut = 0.0
                self.change_y = 8
                self.change_x = 4 if self.joueur.center_x > self.center_x else -4