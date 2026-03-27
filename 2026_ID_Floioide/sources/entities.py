from math import dist
import math
import random 
import os
import arcade
from constantes import DOSSIER_BOSS, LARGEUR, HAUTEUR, VITESSE_MARCHE, VITESSE_DASH, VITESSE_SAUT, VITESSE_TIR, DISTANCE_MAX_TIR, DOSSIER_DATA, TAILLE_TUILE, VITESSE_MOB, GRAVITE
from arcade.hitbox import HitBox


class EntiteAnimee(arcade.Sprite):
    def __init__(self, x, y, scale=1.0):
        # appel constructeur parent
        super().__init__(scale=scale)
        self.center_x = x
        self.center_y = y
        
        # variables pour animation
        self.frame_actuelle = 0
        self.temps_ecoule = 0
        self.vitesse_animation = 0.1
        self.etat = "IDLE"
        
        # stockage hitbox personnalisee
        self.hit_box_perso = None
        
    def update_animation(self, delta_time=1/60):
        # gestion temps pour images
        self.temps_ecoule += delta_time

class Joueur(EntiteAnimee):
    def __init__(self, x, y):
        self.flip_left_right = False


        # systeme inventaire (4 cases)
        # 3 cases pour consommable/armes (dictionnaire)
        self.inventaire_items = [None, None, None] 
        # 4 cases maximum pour charmes (stockage nom fichier)
        self.inventaire_charmes = ["dash.png"] 
        self.index_selection = 0 # case selectionnee (0 1 ou 2)
        
        # variables pour effets charmes
        self.double_saut_dispo = False 
        self.etat_suppression = False # confirmation abandon item
        self.index_inventaire = 0

        # initialisation avec scale 0 1
        super().__init__(x, y, scale=0.1)
        
        chemin = os.path.join(DOSSIER_DATA, "player", "player.png")
        self.texture = arcade.load_texture(chemin)

        # dossiers images
        doss_p = os.path.join(DOSSIER_DATA, "player")
        doss_m = os.path.join(doss_p, "mouvements")
        
        # 1 chargement textures base
        self.tex_idle = arcade.load_texture(os.path.join(doss_p, "player.png"))
        self.tex_saut = arcade.load_texture(os.path.join(doss_m, "saut.png"))
        self.tex_dash = arcade.load_texture(os.path.join(doss_m, "Dash.png"))
        
        # animations marche (1 a 4)
        self.anims_marche = []
        for i in range(1, 5):
            self.anims_marche.append(arcade.load_texture(os.path.join(doss_m, f"avancer ({i}).png")))
            
        # animations grimper (1 a 3)
        self.anims_grimper = []
        for i in range(1, 4):
            self.anims_grimper.append(arcade.load_texture(os.path.join(doss_m, f"grimper ({i}).png")))

        # animations attaque (1 a 12)
        self.textures_attaque = []
        for i in range(1, 13):
            self.textures_attaque.append(arcade.load_texture(os.path.join(doss_p, "attaque", f"attaque{i}.png")))

        
        
        # 2 variables statistiques

        self.vie = 100
        self.vie_max = 100  
        self.eau = 100
        self.nrj_dash = 100
        self.monnaie = 0
        
        self.energie = 100
        self.timer_dash = 0        
        self.timer_attaque = 0
        self.timer_recup_eau = 0
        self.timer_energie = 0
        self.invul_timer = 0.0
        # etats pour animation
        self.face_gauche = False
        self.en_dash = False
        self.en_escalade = False
        self.au_sol = False
        

        self.timer_dash = 0.0  # minuteur actuel (0 pret)
        self.delai_dash = 5.0  # dash met 5 secondes a recharger
        self.eau = 100.0       # eau actuelle
        self.eau_max = 100.0   # eau maximum

        self.vitesse = VITESSE_MARCHE
        self.vitesse_dash = VITESSE_DASH
        self.puissance_saut = VITESSE_SAUT
        self.noclip = False

        # 3 hitbox fixe obligatoire pour arcade 3 0
        self.hit_box_algorithm = None
        t = 45 
        self.hit_box_perso = HitBox([(-t, -t), (t, -t), (t, t), (-t, t)])
        self.hit_box = self.hit_box_perso

        self.dash_cooldown = 0.0  # pour fleur (5 0 a 0)
        self.dash_duree = 0.0

    def update_animation(self, delta_time=1/60):
        # 1 gestion timers
        if self.invul_timer > 0:
            self.invul_timer -= delta_time
        
        if self.dash_cooldown > 0:
            self.dash_cooldown -= delta_time

        # gestion dash (mouvement et duree)
        if self.en_dash:
            self.dash_duree += delta_time
            if self.dash_duree > 0.2:
                self.en_dash = False
                self.dash_duree = 0
                self.change_x = 0

        # 2 determination sens (orientation)
        # changement direction seulement si mouvement
        # si arret pour attaque garder valeur
        if self.change_x < -0.1:
            self.face_gauche = True
        elif self.change_x > 0.1:
            self.face_gauche = False

        # 3 selection liste images (priorites)
        if self.en_dash:
            self.etat = "DASH"
            textures_a_voir = [self.tex_dash]
            vit = 0.1
        elif self.etat == "ATTAQUE":
            # attaque reste tant que animation pas finie
            textures_a_voir = self.textures_attaque
            vit = 0.05
        elif self.en_escalade:
            textures_a_voir = self.anims_grimper
            vit = self.vitesse_animation
        elif abs(self.change_y) > 0.1: 
            self.etat = "SAUT"
            textures_a_voir = [self.tex_saut]
            vit = 0.1
        elif abs(self.change_x) > 0.1:
            self.etat = "MARCHE"
            textures_a_voir = self.anims_marche
            vit = self.vitesse_animation
        else:
            self.etat = "IDLE"
            textures_a_voir = [self.tex_idle]
            vit = self.vitesse_animation

        # 4 gestion timer animation
        self.temps_ecoule += delta_time
        
        # securite si changement animation
        if self.frame_actuelle >= len(textures_a_voir):
            self.frame_actuelle = 0

        if self.temps_ecoule > vit:
            self.temps_ecoule = 0
            self.frame_actuelle += 1
            
            # si fin liste images
            if self.frame_actuelle >= len(textures_a_voir):
                self.frame_actuelle = 0
                # quitter etat attaque ici
                if self.etat == "ATTAQUE":
                    self.etat = "IDLE"

        # 5 application finale texture et miroir
        # recuperation image actuelle dans liste
        base = textures_a_voir[self.frame_actuelle]
        
        # application miroir a chaque frame
        if self.face_gauche:
            self.texture = base.flip_left_right()
        else:
            self.texture = base

        # securite hitbox
        self.hit_box = self.hit_box_perso

        # diminuer timer invulnerabilite
        if hasattr(self, "invul_timer") and self.invul_timer > 0:
            self.invul_timer -= delta_time
            
            # effet visuel clignotement
            # variation opacite entre 255 et 100
            self.alpha = 150 if int(self.invul_timer * 10) % 2 == 0 else 255
        else:
            self.alpha = 255 # redevient normal

class Boss(EntiteAnimee):
    def __init__(self, x, y):
        # definition taille desiree une seule fois
        self.taille_fixe = 4.0 
        super().__init__(x, y)

        self.hit_box_perso = HitBox([(-100, -100), (100, -100), (100, 100), (-100, 100)])
        self.hit_box =self.hit_box_perso
        self.scale = 2.0  # pour gros boss
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
        self.vie = 50  # modifier selon resistance voulue

        if self.textures_attaque:
            self.texture = self.textures_attaque[0]

    def update_animation(self, delta_time=1/60):
        self.temps_ecoule += delta_time
        
        # gestion textures
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

        # gestion regard (sans tete en bas)
        if self.cible:
            # utiliser taille fixe pour rester coherent
            if self.cible.center_x < self.center_x:
                # si images regardent a gauche
                self.width = abs(self.width)  # largeur normale
            else:
                # forcer largeur negative pour miroir
                self.width = -abs(self.width) 
            
            # ne jamais toucher height ou scale ici
            # eviter que boss se retrouve tete en bas
        self.hit_box = self.hit_box_perso
        
        def logique_ia(self, joueur):
            pass

class ProjectileEnnemi(arcade.Sprite):
    def __init__(self, x, y, cible_x, cible_y, degats=1):
        super().__init__(os.path.join(DOSSIER_DATA, "mobs", "projectile.png"), 0.5) # ajuster chemin
        self.center_x = x
        self.center_y = y
        self.degats = degats
        
        # calcul trajectoire
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
        
        # chargement automatique textures
        self.textures_marche = []
        for i in range(1, nb_anim + 1):
            chemin = os.path.join(DOSSIER_DATA, "mobs", dossier, f"mob{i}.png")
            if os.path.exists(chemin):
                self.textures_marche.append(arcade.load_texture(chemin))
        
        if self.textures_marche:
            self.texture = self.textures_marche[0]

        # stats base
        self.vie = 2
        self.vitesse = 2
        self.direction = 1 # 1 pour droite et -1 pour gauche
        
    def logique_sol(self, liste_murs):
        # deplacement simple
        self.change_x = self.vitesse * self.direction
        
        # inverse direction si touche mur
        if arcade.check_for_collision_with_list(self, liste_murs):
            self.direction *= -1
            self.center_x += self.direction * 5

    def orienter_vers_joueur(self, joueur):
        # changer direction pour faire face joueur
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
            # miroir selon direction
            if self.direction == -1:
                # appliquer texture normale
                self.texture = base
                # effet miroir
                self.flip_left_right = self.face_gauche
            else:
                self.texture = base

class PNJ(arcade.Sprite):
    def __init__(self, x, y, nom="pnj"):
        super().__init__(center_x=x, center_y=y, scale=0.5)
        chemin_pnj = os.path.join(DOSSIER_DATA, "mobs", "PNJ")
        self.est_marchand = True
        # securite si images n existent pas
        try:
            self.tex1 = arcade.load_texture(os.path.join(chemin_pnj, "PNJ1.png"))
            self.tex2 = arcade.load_texture(os.path.join(chemin_pnj, "PNJ2.png"))
        except:
            self.tex1 = arcade.make_soft_square_texture(50, arcade.color.BLUE)
            self.tex2 = arcade.make_soft_square_texture(50, arcade.color.LIGHT_BLUE)

        self.est_marchand = True
        self.texture = self.tex1
        self.timer_anim = 0
        self.est_survole = False
        self.nom = nom
        self.mouse_over = False  # pour savoir si souris dessus
        self.original_x = x

    def update_animation(self, delta_time=1/60):
        # 1 animation (switch toutes les 0 5s)
        self.timer_anim += delta_time
        if self.timer_anim > 0.5:
            self.timer_anim = 0
            self.texture = self.tex2 if self.texture == self.tex1 else self.tex1

        # 2 changement couleur au survol
        if self.est_survole:
            self.color = arcade.color.YELLOW
        else:
            self.color = arcade.color.WHITE

        if self.mouse_over:
            # tremblement aleatoire
            self.center_x = self.original_x + random.uniform(-2, 2)
        else:
            # retour a position normale
            self.center_x = self.original_x

    def draw(self, **kwargs):
        # 1 dessiner sprite normalement
        super().draw(**kwargs)
        
        # 2 si survole ajout contour blanc
        if self.est_survole:
            # dessiner rectangle vide autour sprite
            # utiliser dimensions sprite
            arcade.draw_rect_outline(
                rect=self.rect,
                color=arcade.color.WHITE,
                border_width=3
            )

class EffetAttaque(arcade.Sprite):
    def __init__(self, joueur, dossier):
        super().__init__(scale=0.4)
        
        self.direction = -1 if joueur.face_gauche else 1

        self.center_x = joueur.center_x + (self.direction * 50)
        self.center_y = joueur.center_y
        
        # correction erreur (utiliser miroir)
        # si joueur regarde a gauche attaque a gauche
       
        
        # decaler effet devant joueur
        self.center_x += self.direction * 40

        # chargement textures
        self.textures = []
        for i in range(1, 13):
            chemin = os.path.join(dossier, f"attaque{i}.png")
            tex = arcade.load_texture(chemin)
            # si joueur retourne retourner effet
            if self.direction == -1:
                self.textures.append(tex.flip_left_right())
            else:
                self.textures.append(tex)
        
        self.texture = self.textures[0]
        self.frame = 0
        self.timer = 0
        self.vitesse_frame = 0.03 # vitesse animation

    def update_animation(self, delta_time=1/60):
        self.timer += delta_time
        if self.timer > self.vitesse_frame:
            self.timer = 0
            self.frame += 1
            if self.frame < len(self.textures):
                self.texture = self.textures[self.frame]
            else:
                self.remove_from_sprite_lists() # fin attaque

class ProjectileEnnemi(arcade.Sprite):
    def __init__(self, x, y, joueur, degats=1, vitesse=5, image="foret/air/boule_bleue.png"):
        # construire chemin vers image
        chemin_image = os.path.join(DOSSIER_DATA, "mobs", image)
        super().__init__(chemin_image, scale=0.4)
        
        self.center_x = x
        self.center_y = y
        self.degats = degats
        
        # calcul angle vers joueur
        diff_x = joueur.center_x - x
        diff_y = joueur.center_y - y
        angle = math.atan2(diff_y, diff_x)
        
        # application vitesse
        self.change_x = math.cos(angle) * vitesse
        self.change_y = math.sin(angle) * vitesse

    def update(self, delta_time: float = 1/60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        # supprimer si hors ecran

class EntiteBoss(arcade.Sprite):
    def __init__(self, x, y, image, scale=1.0):
        super().__init__(image, scale)
        self.center_x = x
        self.center_y = y
        self.vie =1
        self.vie_max = 1
        self.degats = 1
        self.etat = "idle"
        self.timer_action = 0
        self.timer_tremblement = 0
        self.pos_x_base = x
        self.vie_max = 10

    def dessiner_barre_vie(self):
        """ afficher barre de vie au dessus boss """
        if self.vie > 0:
            largeur_totale = 60
            hauteur = 8
            # calcul ratio vie (evite division par zero)
            max_vie = getattr(self, "vie_max", self.vie)
            ratio = self.vie / self.vie_max
            
            # 1 creer objets rectangles
            # fond rouge
            fond_rect = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale, 
                hauteur
            )
            
            # barre verte
            vie_rect = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale * ratio, 
                hauteur
            )

            # 2 dessiner rectangles
            arcade.draw_rect_filled(fond_rect, arcade.color.RED)
            arcade.draw_rect_filled(vie_rect, arcade.color.GREEN)

    def appliquer_physique(self, murs):
        # gerer gravite et collisions
        self.change_y -= GRAVITE
        self.center_y += self.change_y
        self.timer_attaque = 0
        self.invul_timer = 0

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

class EntiteBossTron(arcade.Sprite):
    def __init__(self, scale=1.0):
        super().__init__(scale=scale) # initialisation vide
        self.vie_max = 0 # defini par phases
        self.invul_timer = 0

    def appliquer_physique(self, murs):
        # gravite
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
                
        # mouvement x
        self.center_x += self.change_x
        hit_list = arcade.check_for_collision_with_list(self, murs)
        for mur in hit_list:
            if self.change_x > 0: self.right = mur.left
            elif self.change_x < 0: self.left = mur.right
            self.change_x = 0

    def dessiner_barre_vie(self):
        """ afficher barre de vie au dessus boss """
        if self.vie > 0:
            largeur_totale = 60
            hauteur = 8
            
            # 1 creer objet rectangle pour fond (rouge)
            # gauche bas largeur hauteur
            rect_fond = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale, 
                hauteur
            )
            # dessiner avec objet et couleur
            arcade.draw_rect_filled(rect_fond, arcade.color.RED)

            # 2 creer objet rectangle pour vie (verte)
            max_p = getattr(self, "vie_max", self.vie)
            ratio = self.vie / max_p
            
            rect_vie = arcade.LBWH(
                self.center_x - largeur_totale / 2, 
                self.top + 15, 
                largeur_totale * ratio, 
                hauteur
            )
            arcade.draw_rect_filled(rect_vie, arcade.color.GREEN)

    def update_boss(self, delta_time, liste_projectiles, murs):
        """ gerer temps de securite pour degats """
        if self.invul_timer > 0:
            self.invul_timer -= delta_time

class ProjectileBoss(arcade.Sprite):
    def __init__(self, x, y, joueur): # passer objet joueur entier
        super().__init__(scale=1.2)
        
        self.joueur = joueur
        self.timer_vie = 0
        self.degats = 4 # points de vie enleves
        
        # chargement animation (1 a 5)
        chemin = os.path.join(DOSSIER_DATA, "boss", "boss arbre")
        self.textures_animation = []
        for i in range(1, 6):
            try:
                tex = arcade.load_texture(os.path.join(chemin, f"Attaque.{i}.png"))
                self.textures_animation.append(tex)
            except Exception as e:
                print(f"erreur chargement image {i} {e}")
        
        # definir texture de depart
        if self.textures_animation:
            self.texture = self.textures_animation[0]
        self.cur_texture_index = 0
        self.animation_speed = 0.1 # vitesse changement image

        # position et direction
        self.center_x = x
        self.center_y = y

        vitesse = 7
        diff_x = joueur.center_x - x
        diff_y = joueur.center_y - y
        angle = math.atan2(diff_y, diff_x)
        
        self.change_x = math.cos(angle) * vitesse
        self.change_y = math.sin(angle) * vitesse
        self.angle = math.degrees(angle)

    def update(self, delta_time: float):
        super().update()
        self.timer_vie += delta_time

        # 1 animation changer image selon temps
        if self.textures_animation:
            self.cur_texture_index += self.animation_speed
            if self.cur_texture_index >= len(self.textures_animation):
                self.cur_texture_index = 0
            self.texture = self.textures_animation[int(self.cur_texture_index)]

        # 2 collision avec joueur
        if arcade.check_for_collision(self, self.joueur):
            # verifier si joueur pas invulnerable
            if self.joueur.invul_timer <= 0:
                self.joueur.vie -= self.degats
                self.joueur.invul_timer = 1.0 # 1 seconde invulnerabilite
                print(f"aie vie restants {self.joueur.vie}")
            
            self.remove_from_sprite_lists() # projectile disparait apres impact

        # 3 suppression si trop vieux (hors ecran)
        if self.timer_vie > 4.0:
            self.remove_from_sprite_lists()

class BossArbreP1(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=1.7)
        self.texture = arcade.load_texture(os.path.join(DOSSIER_DATA, "boss", "boss arbre", "P1.png"))
        self.center_x = x
        self.center_y = y
        self.joueur = joueur
        self.vie =10
        self.vie_max = 10
        self.timer_tir = 0.0
        self.timer_attaque = 0
    
    def lancer_baton(self, liste_projectiles):
        """ 
        creer objet et envoyer vers joueur
        """
        # creer projectile aux coordonnees boss
        baton = ProjectileBoss(
            self.center_x, 
            self.center_y, 
            self.joueur
        )
        liste_projectiles.append(baton)

    def update_boss(self, delta_time, liste_projectiles, murs):
        # 1 appeler logique de base (timer et invul)
        super().update_boss(delta_time, liste_projectiles, murs)
        self.timer_attaque += delta_time

        if self.invul_timer > 0:
            self.invul_timer -= delta_time

        self.appliquer_physique(murs)

        # print pour tester
        

        if self.timer_attaque >= 5.0:
            print("boss essaie de tirer") # print de test
            self.timer_attaque = 0
            self.lancer_baton(liste_projectiles)

        # 2 si timer au dessus de 5s tirer
        if self.timer_attaque >= 5.0:
            self.timer_attaque = 0
            # creer baton coordonnees boss vers joueur
            nouveau_baton = ProjectileBoss(
                self.center_x, 
                self.center_y, 
                self.joueur.center_x, 
                self.joueur.center_y
            )
            liste_projectiles.append(nouveau_baton)
            self.timer_attaque += delta_time

    def au_deces(self):
        # libere deux p2
        return [BossArbreP2(self.center_x - 40, self.center_y, self.joueur),
                BossArbreP2(self.center_x + 40, self.center_y, self.joueur)]
        self.joueur.monnaie += 5
    
class BossArbreP2(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=1.0)
        chemin_base = os.path.join(DOSSIER_DATA, "boss", "boss arbre")
        self.tex_sol = arcade.load_texture(os.path.join(chemin_base, "P2.png"))
        self.tex_saut = arcade.load_texture(os.path.join(chemin_base, "P2.saut.png"))
        self.texture = self.tex_sol
        self.center_x, self.center_y = x, y
        self.joueur = joueur
        self.vie =5
        self.vie_max = 5
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
        if arcade.check_for_collision(self, self.joueur):
            if self.joueur.invul_timer <= 0:
                self.joueur.vie -= self.degats # enleve 3 vies
                self.joueur.invul_timer = 1.0
                print(f"p2 touche vie restants {self.joueur.vie}")

    def au_deces(self):
        # libere deux p3 (donc 4 au total)
        return [BossArbreP3(self.center_x - 20, self.center_y, self.joueur),
                BossArbreP3(self.center_x + 20, self.center_y, self.joueur)]
        self.joueur.monnaie += 5

class BossArbreP3(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=1.5)
        self.texture = arcade.load_texture(os.path.join(DOSSIER_DATA, "boss", "boss arbre", "P3.png"))
        self.center_x, self.center_y = x, y
        self.joueur = joueur
        self.vie =2
        self.vie_max = 2
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
        if arcade.check_for_collision(self, self.joueur):
            if self.joueur.invul_timer <= 0:
                self.joueur.vie -= self.degats # enleve 1 vie
                self.joueur.invul_timer = 1.0
                print(f"p3 touche vie restants {self.joueur.vie}")

class BouleBleue(arcade.Sprite):
    def __init__(self, x, y, dest_x, dest_y, degats, chemin_texture):
        super().__init__(chemin_texture, scale=1.0)
        self.center_x = x
        self.center_y = y
        self.degats = degats
        self.timer_vie = 0.0
        
        # calcul trajectoire
        angle_rad = math.atan2(dest_y - y, dest_x - x)
        vitesse_proj = 300 # va assez vite
        self.change_x = math.cos(angle_rad) * vitesse_proj
        self.change_y = math.sin(angle_rad) * vitesse_proj

    def update_proj(self, delta_time):
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        self.timer_vie += delta_time
        if self.timer_vie >= 5.0: # disparait au bout de 5s
            self.remove_from_sprite_lists()

class NouveauMobBase(EntiteAnimee):
    def __init__(self, x, y, joueur, stats, textures_paths):
        # taille standard de 0 5 pour tous mobs
        super().__init__(x, y, scale=0.5) 
        self.joueur = joueur
        self.vie =stats["vie"]
        self.degats = stats["degats"]
        self.drop_hit = stats["drop_hit"]
        self.drop_death = stats["drop_death"]
        self.invul_timer = 0.0 
        
        self.vie_max = stats.get("vie", 2) 
        self.vie =self.vie_max

        # mecanique touche joueur
        self.touche_joueur = 0
        self.timer_touche_joueur = 0.0

        # chargement textures animation
        self.textures_anim = [arcade.load_texture(path) for path in textures_paths]
        self.texture = self.textures_anim[0]
        self.anim_timer = 0.0
        
    def gerer_invulnerabilite_et_animation(self, delta_time):
        # invulnerabilite (clignotement mob)
        if self.invul_timer > 0:
            self.invul_timer -= delta_time
            self.alpha = 150 
        else:
            self.alpha = 255
            
        # timer pour retoucher joueur
        if self.timer_touche_joueur > 0:
            self.timer_touche_joueur -= delta_time
            if self.timer_touche_joueur <= 0:
                self.touche_joueur = 0 # mob peut reattaquer
                
        # animation en boucle
        self.anim_timer += delta_time
        if self.anim_timer > 0.2: 
            self.anim_timer = 0.0
            self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_anim)
            self.texture = self.textures_anim[self.frame_actuelle]

        # orientation vers joueur (arcade 3 0 utilise tuples pour miroir)
        if self.joueur.center_x > self.center_x:
            self.scale = (-0.5, 0.5) # retournement horizontal en gardant taille
        else:
            self.scale = (0.5, 0.5) # regarde a gauche avec taille 0 5

    def anti_stuck(self, murs):
        # tp a tuile libre la plus proche si coince
        if arcade.check_for_collision_with_list(self, murs):
            origine_x, origine_y = self.center_x, self.center_y
            # recherche en spirale (rayon 1 a 3 tuiles)
            for rayon in range(1, 4):
                for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
                    self.center_x = origine_x + dx * TAILLE_TUILE * rayon
                    self.center_y = origine_y + dy * TAILLE_TUILE * rayon
                    if not arcade.check_for_collision_with_list(self, murs):
                        return # emplacement libre trouve
            # si vraiment tout est bloque remettre a place
            self.center_x, self.center_y = origine_x, origine_y

class MobSol(NouveauMobBase):
    def __init__(self, x, y, joueur, stats, textures_paths):
        super().__init__(x, y, joueur, stats, textures_paths)
        # suppression scale (gere par base)
        self.vie =stats.get("vie", 2)
        self.degats = stats.get("degats", 1.0)

    def update_mob(self, delta_time, murs):
        self.gerer_invulnerabilite_et_animation(delta_time)
        self.change_y -= GRAVITE
        
        # 3 ia (se diriger vers joueur)
        if self.joueur.center_x < self.center_x:
            self.change_x = -VITESSE_MOB
        else:
            self.change_x = VITESSE_MOB

        self.center_x += self.change_x
        if arcade.check_for_collision_with_list(self, murs):
            self.center_x -= self.change_x
            
        self.center_y += self.change_y
        hit_list_y = arcade.check_for_collision_with_list(self, murs)
        if hit_list_y:
            if self.change_y < 0: # tombe
                self.bottom = hit_list_y[0].top
            elif self.change_y > 0: # touche plafond
                self.top = hit_list_y[0].bottom
            self.change_y = 0

        self.anti_stuck(murs)

class MobAir(NouveauMobBase):
    def __init__(self, x, y, joueur, stats, textures_paths, projectile_texture, liste_projectiles):
        super().__init__(x, y, joueur, stats, textures_paths)
        # suppression scale et vie parasites
        
        self.chemin_boule = arcade.load_texture(os.path.join(DOSSIER_DATA, "mobs", "air", "boule.png"))
        self.liste_projectiles = liste_projectiles
        
        self.vie =stats.get("vie", 2)
        self.degats = stats.get("degats", 0.5)
        self.timer_tir = 0

        self.timer_vie_air = 10.0

    def update_mob(self, delta_time, murs):

        self.timer_vie_air -= delta_time
        if self.timer_vie_air <= 0:
            self.remove_from_sprite_lists()
            return

        self.gerer_invulnerabilite_et_animation(delta_time)

        self.gerer_invulnerabilite_et_animation(delta_time)
        
        # deplacement (reste a 2 tuiles du joueur)
        distance = math.dist((self.center_x, self.center_y), (self.joueur.center_x, self.joueur.center_y))
        
        if distance > TAILLE_TUILE * 2:
            angle_rad = math.atan2(self.joueur.center_y - self.center_y, self.joueur.center_x - self.center_x)
            self.change_x = math.cos(angle_rad) * VITESSE_MOB
            self.change_y = math.sin(angle_rad) * VITESSE_MOB
        else:
            self.change_x = 0
            self.change_y = 0

        self.center_x += self.change_x
        self.center_y += self.change_y
        
        self.anti_stuck(murs)

        # mecanique de tir (toutes les 3 secondes)
        self.timer_tir += delta_time
        if self.timer_tir >= 3.0:
            self.timer_tir = 0.0
            boule = BouleBleue(self.center_x, self.center_y, self.joueur.center_x, self.joueur.center_y, self.degats, self.chemin_boule)
            self.liste_projectiles.append(boule)

class BossVerDeTerre(EntiteBossTron):
    def __init__(self, x, y, joueur):
        # taille multipliee par 4
        super().__init__(scale=2.0) 
        self.center_x = x
        self.center_y = y
        self.joueur = joueur

        self.vie =25
        self.vie_max = 25
        self.degats = 10
        self.drop_hit = 1 
        self.drop_death = 10 
        self.temps_invul = 1.0 
        
        self.timer_phase = 0.0
        self.phase_actuelle = 0
        self.animations = []
        
        # chargement textures (garde logique dossiers)
        def charger_phase(dossier, prefix, delay, debut, fin, zfill_val):
            frames = []
            chemin_base = os.path.join(DOSSIER_DATA, "boss", "Ver de terre", dossier)
            for i in range(debut, fin + 1):
                num = str(i).zfill(zfill_val) 
                nom_fichier = f"{prefix}{num}_delay-{delay}.png"
                try:
                    frames.append(arcade.load_texture(os.path.join(chemin_base, nom_fichier)))
                except:
                    pass
            return frames if frames else [arcade.make_soft_square_texture(100, arcade.color.GREEN)]

        self.animations.append(charger_phase("anime", "frame_", "0.13s", 0, 6, 1))
        self.animations.append(charger_phase("plongeon", "frame_", "0.13s", 0, 13, 2))
        self.animations.append(charger_phase("saut bougeant", "frame_", "0.1s", 0, 12, 2))
        self.animations.append(charger_phase("saut court", "frame_", "0.1s", 0, 10, 2))
        self.animations.append(charger_phase("Saut simple", "frame_", "0.1s", 0, 12, 2))
        
        self.texture = self.animations[0][0]

    def appliquer_physique(self, murs):
        # aucune gravite
        pass

    def update_boss(self, delta_time, liste_projectiles, murs):
        # 1 invulnerabilite
        if self.invul_timer > 0:
            self.invul_timer -= delta_time
            self.alpha = 150
        else:
            self.alpha = 255
            
        # 2 gestion temps phase (5 secondes par phase)
        self.timer_phase += delta_time
        if self.timer_phase >= 5.0:
            self.timer_phase = 0.0
            self.phase_actuelle = (self.phase_actuelle + 1) % 5
            
        # 3 animation unique sur 5 secondes
        # calcul index image
        frames_actuelles = self.animations[self.phase_actuelle]
        nb_frames = len(frames_actuelles)
        
        # progression sur les 5 secondes
        progression = self.timer_phase / 5.0
        # choix image correspondante
        index_image = min(int(progression * nb_frames), nb_frames - 1)
        self.texture = frames_actuelles[index_image]
            
        # 4 collision degats
        if arcade.check_for_collision(self, self.joueur):
            if self.joueur.invul_timer <= 0:
                self.joueur.vie -= self.degats
                self.joueur.invul_timer = 1.0
                direction = 1 if self.joueur.center_x > self.center_x else -1
                self.joueur.center_x += direction * 50

    def update_animation(self, delta_time=1/60):
        super().update_animation(delta_time)
        if not self.textures_marche:
            return
            
        if self.temps_ecoule > self.vitesse_animation:
            self.temps_ecoule = 0
            self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_marche)
            
            base = self.textures_marche[self.frame_actuelle]
            
            # correction orientation
            # si de base vers la gauche
            if self.direction == -1:
                # joueur a gauche (texture normale)
                self.texture = base 
            else:
                # joueur a droite (inverse texture)
                self.texture = base.flip_left_right()

class ProjectileRobot(arcade.Sprite):
    def __init__(self, x, y, joueur):
        chemin = os.path.join(DOSSIER_DATA, "boss", "boss fin", "attaques", "Attaque 4", "projectile.png")
        super().__init__(chemin, scale=0.3)
        self.center_x = x
        self.center_y = y
        self.joueur = joueur
        self.degats = 5  # un demi coeur
        self.timer_vie = 0.0

        # calcul angle vers joueur
        diff_x = joueur.center_x - x
        diff_y = joueur.center_y - y
        angle_rad = math.atan2(diff_y, diff_x)
        
        # tourner sprite vers joueur
        self.angle = math.degrees(angle_rad) + 90 
        
        vitesse = 6
        self.change_x = math.cos(angle_rad) * vitesse
        self.change_y = math.sin(angle_rad) * vitesse

    def update(self, delta_time=1/60):
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.timer_vie += delta_time
        
        # collision joueur
        if arcade.check_for_collision(self, self.joueur):
            if self.joueur.invul_timer <= 0:
                self.joueur.vie -= self.degats
                self.joueur.invul_timer = 1.0
            self.remove_from_sprite_lists()

        if self.timer_vie > 5.0:
            self.remove_from_sprite_lists()

class ZoneRougeAvertissement(arcade.SpriteSolidColor):
    def __init__(self, x, y, type_attaque, joueur):
        super().__init__(32*5, 50, arcade.color.RED_DEVIL)
        self.center_x = x
        self.center_y = y
        self.timer = 1.0
        self.type_attaque = type_attaque
        self.joueur = joueur

    def update(self, delta_time=1/60):
        self.timer -= delta_time

class AttaqueDeZoneBoss(arcade.Sprite):
    def __init__(self, x, y, type_attaque, joueur):
        super().__init__(scale=0.7)
        self.center_x = x
        self.center_y = y
        self.joueur = joueur
        self.type_attaque = type_attaque
        self.timer_duree = 0.0
        self.timer_degat = 0.0
        
        self.frames = []
        self.frame_idx = 0
        self.anim_timer = 0.0
        
        chemin_base = os.path.join(DOSSIER_DATA, "boss", "boss fin", "attaques")
        
        if type_attaque == 1:
            # attaque 1
            chemins = [os.path.join(chemin_base, "attaque 1", f"attaque.{i}.png") for i in range(1, 6)]
            chemins += chemins[-2::-1] # ajoute retour
            for c in chemins: self.frames.append(arcade.load_texture(c))
            self.duree_max = 5.0

        elif type_attaque == 2:
            # attaque 2 (tourne vers bas)
            chemins = [os.path.join(chemin_base, "attaque 2", f"{i}.png") for i in range(1, 7)]
            chemins += chemins[-2::-1]
            for c in chemins: self.frames.append(arcade.load_texture(c))
            self.duree_max = 5.0
            self.angle = 270 # pointe vers bas
            
        elif type_attaque == 3:
            # attaque 3 (sweep sol)
            chemins = [os.path.join(chemin_base, "attaque 3", f"{i}.png") for i in range(9)]
            for c in chemins:
                tex = arcade.load_texture(c)
                # si joueur a gauche retourner image
                if joueur.center_x < x:
                    tex = tex.flip_left_right()
                self.frames.append(tex)
            self.duree_max = 1.0

        if self.frames:
            self.texture = self.frames[0]
            # vitesse pour que animation prenne toute duree
            self.vitesse_anim = self.duree_max / len(self.frames) 

    def update(self, delta_time=1/60):
        self.timer_duree += delta_time
        self.timer_degat -= delta_time
        self.anim_timer += delta_time
        
        # animation
        if self.anim_timer >= self.vitesse_anim:
            self.anim_timer = 0
            self.frame_idx += 1
            if self.frame_idx < len(self.frames):
                self.texture = self.frames[self.frame_idx]
                
        # degats (1 par seconde)
        if arcade.check_for_collision(self, self.joueur) and self.timer_degat <= 0:
            if self.joueur.invul_timer <= 0:
                self.joueur.vie -= 1
                self.joueur.invul_timer = 0.2
            self.timer_degat = 1.0 # attend 1 seconde
            
        if self.timer_duree >= self.duree_max:
            self.remove_from_sprite_lists()

class BossRobot(EntiteBossTron):
    def __init__(self, x, y, joueur):
        super().__init__(scale=2.0)
        self.center_x = x
        self.center_y = y
        self.joueur = joueur
        
        self.vie = 12
        self.vie_max = 12
        self.degats = 10 # degats contact direct
        
        # chargement textures
        chemin = os.path.join(DOSSIER_DATA, "boss", "Boss robot")
        self.textures_phases = {
            1: [arcade.load_texture(os.path.join(chemin, "bot1.1.png")), arcade.load_texture(os.path.join(chemin, "bot1.2.png"))],
            2: [arcade.load_texture(os.path.join(chemin, "bot2.1.png")), arcade.load_texture(os.path.join(chemin, "bot2.2.png"))],
            3: [arcade.load_texture(os.path.join(chemin, "bot3.1.png")), arcade.load_texture(os.path.join(chemin, "bot3.2.png"))]
        }
        self.anim_timer = 0.0
        self.frame = 0
        self.texture = self.textures_phases[1][0]
        
        # mecaniques vol
        self.en_vol = True
        self.timer_vol_chute = 0.0 # alterne entre 10s et 5s
        
        # timers attaques
        self.timer_proj_global = 0.0  # attaque toutes les 5s
        self.timer_attaque_vol = random.uniform(2, 4) # attaque 1 ou 2
        self.timer_attaque_sol = 5.0  # attaque 3

        # listes temporaires
        self.nouvelles_zones = []

    def update_boss(self, delta_time, liste_projectiles, murs):
        if self.invul_timer > 0:
            self.invul_timer -= delta_time

        # 1 gestion phase et animation
        if self.vie >= 8: phase = 1
        elif self.vie >= 4: phase = 2
        else: phase = 3
        
        self.anim_timer += delta_time
        if self.anim_timer > 0.3:
            self.anim_timer = 0
            self.frame = (self.frame + 1) % 2
            self.texture = self.textures_phases[phase][self.frame]

        # 2 gestion vol gravite
        self.timer_vol_chute += delta_time
        if self.en_vol:
            self.change_y = 0
            # remonte doucement
            if self.center_y < 1600:
                self.center_y += 3
            if self.timer_vol_chute >= 10.0:
                self.en_vol = False
                self.timer_vol_chute = 0.0
        else:
            self.appliquer_physique(murs) # active gravite
            if self.timer_vol_chute >= 5.0:
                self.en_vol = True
                self.timer_vol_chute = 0.0

        # verifier si boss touche sol
        collisions = arcade.check_for_collision_with_list(self, murs)
        touche_sol = False
        for mur in collisions:
            if self.bottom <= mur.top + 5: # marge tolerance
                touche_sol = True

        # 3 attaque globale (projectile 5s)
        self.timer_proj_global += delta_time
        if self.timer_proj_global >= 5.0:
            self.timer_proj_global = 0.0
            liste_projectiles.append(ProjectileRobot(self.center_x, self.center_y, self.joueur))

        # 4 attaques en vol
        if self.en_vol and not touche_sol:
            self.timer_attaque_vol -= delta_time
            if self.timer_attaque_vol <= 0:
                self.timer_attaque_vol = random.uniform(4, 6)
                type_att = random.choice([1, 2])
                
                if type_att == 1:
                    # sous joueur
                    hauteur_y = 1621
                    zone = ZoneRougeAvertissement(self.joueur.center_x, hauteur_y, 1, self.joueur)
                else:
                    # au dessus joueur
                    zone = ZoneRougeAvertissement(self.joueur.center_x, self.joueur.top + 222, 2, self.joueur)
                    
                self.nouvelles_zones.append(zone)

        # 5 attaques au sol
        if touche_sol:
            self.timer_attaque_sol -= delta_time
            if self.timer_attaque_sol <= 0:
                self.timer_attaque_sol = 5.0
                # spawn attaque 3
                att3 = AttaqueDeZoneBoss(self.center_x, self.center_y, 3, self.joueur)
                self.nouvelles_zones.append(att3)

class BossFin(BossRobot): # herite logique robot
    def __init__(self, x, y, joueur):
        # pv et attaques robot
        super().__init__(x, y, joueur)
        
        # textures boss fin
        self.textures_marche = []
        chemin_fin = os.path.join(DOSSIER_DATA, "boss", "boss fin")
        for i in range(1, 4):
            # charge marche
            tex = arcade.load_texture(os.path.join(chemin_fin, f"marche.{i}.png"))
            self.textures_marche.append(tex)
        
        self.texture = self.textures_marche[0]
        self.frame_marche = 0
        self.timer_marche = 0

    def update_animation(self, delta_time=1/60):
        # animation en boucle
        self.timer_marche += delta_time
        if self.timer_marche > 0.15:
            self.timer_marche = 0
            self.frame_marche = (self.frame_marche + 1) % len(self.textures_marche)
            self.texture = self.textures_marche[self.frame_marche]

    def update_boss(self, delta_time, projectiles_ennemis, murs):
        # attaque robot mais propre animation
        super().update_boss(delta_time, projectiles_ennemis, murs)
        self.update_animation(delta_time)

class BossDVD(EntiteAnimee):
    def __init__(self, x, y, joueur):
        super().__init__(x, y)
        self.joueur = joueur
        self.vie_max = 50 
        self.vie = 50
        self.vitesse = 6  # augmentation vitesse
        
        # direction initiale (diagonale)
        self.change_x = self.vitesse
        self.change_y = self.vitesse

        # timer pour blesser joueur (2 secondes)
        self.timer_degats_joueur = 0

        # chargement textures
        self.textures_animation = []
        chemin_dvd = os.path.join(DOSSIER_DATA, "boss", "DVD")
        for i in range(1, 6):
            self.textures_animation.append(arcade.load_texture(os.path.join(chemin_dvd, f"DVD{i}.png")))
        
        self.texture = self.textures_animation[0]
        self.frame_anim = 0
        self.timer_anim = 0

    def update_boss(self, delta_time, liste_projectiles, liste_murs):
        # 1 animation
        self.update_animation(delta_time)

        # 2 gestion cooldown degats
        if self.timer_degats_joueur > 0:
            self.timer_degats_joueur -= delta_time

        # 3 mouvement x et rebond murs
        self.center_x += self.change_x
        if arcade.check_for_collision_with_list(self, liste_murs):
            self.center_x -= self.change_x # annule mouvement
            self.change_x *= -1 # inverse direction

        # 4 mouvement y et rebond murs
        self.center_y += self.change_y
        if arcade.check_for_collision_with_list(self, liste_murs):
            self.center_y -= self.change_y # annule mouvement
            self.change_y *= -1 # inverse direction

        # 5 collision avec joueur
        if arcade.check_for_collision(self, self.joueur) and self.timer_degats_joueur <= 0:
            self.joueur.vie -= 2 
            self.timer_degats_joueur = 2.0 # 2 secondes attente

    def update_animation(self, delta_time):
        self.timer_anim += delta_time
        if self.timer_anim > 0.2:
            self.timer_anim = 0
            self.frame_anim = (self.frame_anim + 1) % len(self.textures_animation)
            self.texture = self.textures_animation[self.frame_anim]

    def dessiner_barre_vie(self):
        if self.vie <= 0: return
        largeur_totale = 100
        hauteur_barre = 10
        x = self.center_x - largeur_totale / 2
        y = self.top + 15
        arcade.draw_lrbt_rectangle_filled(x, x + largeur_totale, y, y + hauteur_barre, arcade.color.RED)
        vie_ratio = self.vie / self.vie_max
        if vie_ratio > 0:
            arcade.draw_lrbt_rectangle_filled(x, x + (largeur_totale * vie_ratio), y, y + hauteur_barre, arcade.color.GREEN)