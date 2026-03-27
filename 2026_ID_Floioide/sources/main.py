import arcade
import random
import os
from constantes import *
from inputs import InputHandler
from logic import gerer_collisions, separer_mobs
from entities import Joueur, MobAir, PNJ, EffetAttaque, BossArbreP1, MobSol, BossArbreP2, BossArbreP3, BossVerDeTerre, BossRobot, AttaqueDeZoneBoss, ZoneRougeAvertissement, BossFin, BossDVD
from interface import HUD, Chat, InterfaceShop, InterfaceDev
import math
from arcade.hitbox import HitBox
import time

class ProjectileJoueur(arcade.Sprite):
    def __init__(self, x, y, dest_x, dest_y):
        chemin = os.path.join(DOSSIER_DATA, "mobs", "PNJ", "items", "balle.png")
        try: 
            tex = arcade.load_texture(chemin)
        except: 
            tex = arcade.Texture.create_filled("balle_secours", (10, 10), arcade.color.YELLOW)
        
        super().__init__(tex, scale=0.8)
        self.center_x, self.center_y = x, y
        self.degats = 2
        self.timer_vie = 0  # chronometre de vie
        
        # calcul de l angle vers le curseur
        angle_rad = math.atan2(dest_y - y, dest_x - x)
        
        # vitesse basee sur la constante
        self.change_x = math.cos(angle_rad) * VITESSE_TIR
        self.change_y = math.sin(angle_rad) * VITESSE_TIR
        
        # orientation de la texture
        self.angle = math.degrees(angle_rad)

    def update_proj(self, delta_time):
        # deplacement simple
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        
        # gestion de la duree de vie
        self.timer_vie += delta_time
        if self.timer_vie >= 7.0:
            self.remove_from_sprite_lists()

class EcranChargementView(arcade.View):
    def __init__(self, vue_suivante_class):
        super().__init__()
        self.vue_suivante_class = vue_suivante_class
        self.timer = 0
        self.indice_chargement = 1
        self.temp_anim = 0

        self.frames_chargement = [] 
        
        self.logo = arcade.load_texture(os.path.join(DOSSIER_DATA, "Logo_.png"))

        # chargement des 6 images de chargement dans la variable
        for i in range(1, 7):
            chemin = os.path.join(DOSSIER_DATA, "chargement", f"{i}.png")
            if os.path.exists(chemin):
                self.frames_chargement.append(arcade.load_texture(chemin))
            else:
                # texture de secours si fichier manquant
                self.frames_chargement.append(arcade.make_soft_square_texture(50, arcade.color.WHITE))

    def on_update(self, delta_time):
        self.timer += delta_time
        self.temp_anim += delta_time
        if self.temp_anim > 0.1:
            self.indice_chargement += 1
            if self.indice_chargement > 6: self.indice_chargement = 1
            self.temp_anim = 0

        if self.timer > 2.5: # temps de chargement
            vue = self.vue_suivante_class()
            if hasattr(vue, "setup"): vue.setup()
            self.window.show_view(vue)

    def on_draw(self):
        self.clear()
        arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, LARGEUR, HAUTEUR), arcade.color.BLACK)
        
        # logo echelle 0 5 plus petit avec pulsation
        echelle = 0.5 + math.sin(self.timer * 3) * 0.05
        arcade.draw_texture_rect(self.logo, arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2 + 80, 
                                 self.logo.width * echelle, self.logo.height * echelle))
        
        # animation du petit chargement
        tex = self.frames_chargement[self.indice_chargement - 1]
        arcade.draw_texture_rect(tex, arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2 - 120, 120, 120))

class MenuAideView(arcade.View):
    def __init__(self):
        super().__init__()
        # texte de aide
        self.texte_aide = (
            "--- COMMANDES DU JEU ---\n\n"
            "Mouvement : q : gauche ; d : droite\n"
            "Sauter : espace\n"
            "Attaquer : clic Gauche\n"
            "Dash : touche majuscule (Shift)\n"
            "Boutique : contacte avec un PNJ\n"
            "Chat : touche t (votre texte) puis entré (ne sert a rien)\n\n"
            "Utiliser un item du shop : touche entrée en séléctionant l'item avec la molette\n\n"
            "Cliquez n'importe où pour retourner au menu principal."
        )

    def on_draw(self):
        self.clear()
        arcade.draw_rect_filled(arcade.LBWH(0, 0, LARGEUR, HAUTEUR), arcade.color.DARK_SLATE_GRAY)
        
        arcade.draw_text("AIDE", LARGEUR//2, HAUTEUR - 100, arcade.color.WHITE, 40, bold=True, anchor_x="center", anchor_y="center")
        arcade.draw_text(self.texte_aide, LARGEUR//2, HAUTEUR//2, arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", align="center", multiline=True, width=600)

    def on_mouse_press(self, x, y, button, modifiers):
        self.window.show_view(MenuPrincipalView())

class MenuPrincipalView(arcade.View):
    def __init__(self):
        super().__init__()
        
        self.w_btn_base, self.h_btn_base = 320, 110
        self.x_btn = LARGEUR // 2
        self.y_jouer = HAUTEUR // 2 - 20
        self.y_aide = HAUTEUR // 2 - 150
        
        # variables pour animation
        self.timer = 0
        self.mouse_x = 0
        self.mouse_y = 0

        # chemins des images
        try:
            self.fond = arcade.load_texture(os.path.join(DOSSIER_DATA, "intro", "image 1.1.png"))
            self.logo = arcade.load_texture(os.path.join(DOSSIER_DATA, "Logo_.png"))
            self.btn_jouer = arcade.load_texture(os.path.join(DOSSIER_DATA, "jouer.png"))
            self.btn_aide = arcade.load_texture(os.path.join(DOSSIER_DATA, "aide.png"))
        except:
            # securite si les images ne sont pas encore creees
            self.fond = arcade.make_soft_square_texture(LARGEUR, arcade.color.BLACK)
            self.logo = arcade.make_soft_square_texture(200, arcade.color.GOLD)
            self.btn_jouer = arcade.make_soft_square_texture(200, arcade.color.DARK_GREEN)
            self.btn_aide = arcade.make_soft_square_texture(200, arcade.color.DARK_BLUE)
            
        self.historique = []
        # code 1 h h b b g d g d a b s
        self.code_dev_1 = [arcade.key.H, arcade.key.H, arcade.key.B, arcade.key.B, arcade.key.G, arcade.key.D, arcade.key.G, arcade.key.D, arcade.key.A, arcade.key.B, arcade.key.S]
        # code 2 haut haut bas bas gauche droite gauche droite a b entree
        self.code_dev_2 = [arcade.key.UP, arcade.key.UP, arcade.key.DOWN, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT, arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.B, arcade.key.ENTER]

        

    def on_update(self, delta_time):
        self.timer += delta_time

    def on_mouse_motion(self, x, y, dx, dy):
        # sauvegarde en memoire la position de la souris
        self.mouse_x = x
        self.mouse_y = y

    def on_draw(self):
        self.clear()
        # fond
        arcade.draw_texture_rect(self.fond, arcade.LBWH(0, 0, LARGEUR, HAUTEUR))
        
        # calcul de la pulsation de base (grossit/retrecit)
        pulsation = math.sin(self.timer * 4) * 0.05
        
        # logo plus petit avec pulsation
        scale_logo = 0.5 + pulsation
        arcade.draw_texture_rect(self.logo, arcade.rect.XYWH(LARGEUR//2, HAUTEUR - 150, self.logo.width * scale_logo, self.logo.height * scale_logo))
        
        # bouton jouer detection du survol
        survol_jouer = abs(self.mouse_x - self.x_btn) < self.w_btn_base/2 and abs(self.mouse_y - self.y_jouer) < self.h_btn_base/2
        scale_jouer = 1.15 if survol_jouer else 1.0 + pulsation # gros et fixe si survole sinon pulse
        
        w_jouer = self.w_btn_base * scale_jouer
        h_jouer = self.h_btn_base * scale_jouer
        arcade.draw_texture_rect(self.btn_jouer, arcade.rect.XYWH(self.x_btn, self.y_jouer, w_jouer, h_jouer))
        arcade.draw_text("", self.x_btn, self.y_jouer, arcade.color.WHITE, int(20 * scale_jouer), bold=True, anchor_x="center", anchor_y="center")
        
        # bouton aide detection du survol
        survol_aide = abs(self.mouse_x - self.x_btn) < self.w_btn_base/2 and abs(self.mouse_y - self.y_aide) < self.h_btn_base/2
        scale_aide = 1.15 if survol_aide else 1.0 + pulsation
        
        w_aide = self.w_btn_base * scale_aide
        h_aide = self.h_btn_base * scale_aide
        arcade.draw_texture_rect(self.btn_aide, arcade.rect.XYWH(self.x_btn, self.y_aide, w_aide, h_aide))
        arcade.draw_text("", self.x_btn, self.y_aide, arcade.color.WHITE, int(20 * scale_aide), bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # utiliser les dimensions de base pour la zone de clic
            if abs(x - self.x_btn) < self.w_btn_base/2 and abs(y - self.y_jouer) < self.h_btn_base/2:
                self.window.show_view(EcranChargementView(CinematiqueView))
            elif abs(x - self.x_btn) < self.w_btn_base/2 and abs(y - self.y_aide) < self.h_btn_base/2:
                self.window.show_view(MenuAideView())

    def on_key_press(self, key, modifiers):
        self.historique.append(key)
        # garder que les 11 dernieres touches
        if len(self.historique) > 11:
            self.historique.pop(0)

        # lancer jeu en dev mode avec code
        if self.historique == self.code_dev_1 or self.historique == self.code_dev_2:
            print("MODE DÉVELOPPEUR ACTIVÉ !")
            vue_jeu = MonJeu(mode_dev=True)
            vue_jeu.setup()
            self.window.show_view(vue_jeu)

class CinematiqueView(arcade.View):
    def __init__(self):
        super().__init__()
        self.scene_actuelle = 1
        self.timer_animation = 0
        chemin_musique = os.path.join(DOSSIER_DATA, "sounds", "FLOIOIDE_bossfight_1.mp3")
        self.musique_fond = arcade.load_sound(chemin_musique)
        self.lecteur_musique = arcade.play_sound(self.musique_fond, volume=0.5, loop=True)

        

        # 12 textes pour intro du jeu
        self.textes = [
            "J'ai toujours aimé la nature, les arbres et les fleurs",
            "Mais mes paretns refusaient que j'aille courir ailleurs",
            "Un jour, mes copains sont venus taper à ma fenêtre,",
            "Pour m'emmener jouer dehors, là où tout pouvait naître.",
            "Arrivés dans la forêt, on jouait à chat sans peur,",
            "Je suis grimpé sur un puits pour montrer que j'étais le meilleur.",
            "Mais j'ai ri trop fort,",
            "et mon pied a glissé en douceur.",
            "Je suis tmbé dans le puits, tout s'est éteint d'un coup.",
            "Quand je me suis réveillé, mes jambes n'étaient plus du tout.",
            "A la place, des pétales... Ma tête avait disparu.",
            "Et dans le noir du puits, je suis devenu une fleur, perdue."
        ]
        
        self.texte_affiche = ""
        self.index_lettre = 0
        self.timer_texte = 0
        self.charger_scene()

    def charger_scene(self):
        # construction des chemins des images en alternance (anime)
        chemin = os.path.join(DOSSIER_DATA, "intro")
        nom1 = f"image {self.scene_actuelle}.1.PNG"
        nom2 = f"image {self.scene_actuelle}.2.PNG"
        
        self.img1 = arcade.load_texture(os.path.join(chemin, nom1))
        self.img2 = arcade.load_texture(os.path.join(chemin, nom2))
        self.texture_active = self.img1
        
        self.texte_affiche = ""
        self.index_lettre = 0

    def on_update(self, delta_time):
        # animation de l alternance entre les images 1 et 2
        self.timer_animation += delta_time
        if self.timer_animation > 0.5:
            self.texture_active = self.img2 if self.texture_active == self.img1 else self.img1
            self.timer_animation = 0

        # effet ecriture automatique
        if self.index_lettre < len(self.textes[self.scene_actuelle - 1]):
            self.timer_texte += delta_time
            if self.timer_texte > 0.04:
                self.index_lettre += 1
                self.texte_affiche = self.textes[self.scene_actuelle - 1][:self.index_lettre]
                self.timer_texte = 0
        

    def on_draw(self):
        self.clear()
        
        # utiliser draw lrbt rectangle filled avec la texture si possible
        # sinon dessiner la texture avec les coordonnees simples
        
        # dessiner une texture sur tout ecran
        arcade.draw_texture_rect(
            self.texture_active, 
            arcade.LBWH(0, 0, LARGEUR, HAUTEUR) # lbwh left bottom width height
        )
        
        # bandeau de texte noir en bas
        # utiliser lbwh plus simple que rect
        rect = arcade.LBWH(0, 0, LARGEUR, 150)
        arcade.draw_rect_filled(rect, arcade.color.BROWN)
        
        # affichage du texte
        arcade.draw_text(
            self.texte_affiche, 
            50, 80, 
            arcade.color.WHITE, 
            20, 
            width=LARGEUR-100, 
            multiline=True
        )
        
        arcade.draw_text("Appuyez sur [ENTRÉE] pour continuer", LARGEUR - 350, 20, arcade.color.GRAY, 10)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            if self.scene_actuelle < 12:
                self.scene_actuelle += 1
                self.charger_scene()
            else:
                # 1 arreter la musique de intro
                arcade.stop_sound(self.lecteur_musique)
                
                # 2 lancer ecran de chargement
                # ne pas faire game view setup ici
                chargement = EcranChargementView(MonJeu) 
                self.window.show_view(chargement)

class MonJeu(arcade.View):
    def __init__(self, mode_dev=False):
        super().__init__()
        

        self.timer_general = 0.0

        self.invul_timer = 0.0

        self.timer_spawn_mobs = 0.0

        self.etat_boss_tron = 0

        self.etat = "MENU"

        # boutons pause et mort
        self.btn_pause_jeu = arcade.Sprite(os.path.join(CHEMIN_BASE, "data", "pause.png"), scale=0.5)
        self.btn_pause_jeu.center_x = LARGEUR - 40
        self.btn_pause_jeu.center_y = HAUTEUR - 40
        
        self.btn_reprendre = arcade.Sprite(os.path.join(CHEMIN_BASE, "data", "reprendre.png"), center_x=LARGEUR//2, center_y=HAUTEUR//2 + 50, scale=0.5)
        self.btn_menu = arcade.Sprite(os.path.join(CHEMIN_BASE, "data", "menue.png"), center_x=LARGEUR//2, center_y=HAUTEUR//2 - 50, scale=0.5)
        self.btn_aide = arcade.Sprite(os.path.join(CHEMIN_BASE, "data", "aide.png"), center_x=LARGEUR//2, center_y=HAUTEUR//2 - 150, scale=0.5)
        self.btn_rejouer = arcade.Sprite(os.path.join(CHEMIN_BASE, "data", "rejouer.png"), center_x=LARGEUR//2, center_y=HAUTEUR//2 + 50, scale=0.5)

        self.mode_dev = mode_dev

        self.interface_dev = InterfaceDev()

        self.camera_sprites = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        self.camera_bg = arcade.camera.Camera2D()

        self.lecteur_musique = None

        self.mouse_world_x = 0
        self.mouse_world_y = 0
        # pour faire tourner les charmes
       

        # 1 organisation des listes objets (spritelists)
        self.tiroirs = {
            "murs": arcade.SpriteList(),
            "front": arcade.SpriteList(),
            "background": arcade.SpriteList(),
            "boss_test": arcade.SpriteList(),
            "ennemis": arcade.SpriteList(),
            "tirs": arcade.SpriteList(),
            "joueur": arcade.SpriteList(),
            "pnjs": arcade.SpriteList(),
            "boss": arcade.SpriteList(),
            "projectiles_ennemis": arcade.SpriteList(),
            "projectiles_joueur": arcade.SpriteList(),
            "attaques": arcade.SpriteList()
        }
        
        self.tiroirs["projectiles_joueur"] = arcade.SpriteList()

        self.ennemis = arcade.SpriteList()
        self.projectiles_ennemis = arcade.SpriteList()
        self.tiroirs["ennemis"] = self.ennemis

        # variables pour gerer le systeme de boss
        self.boss_actif = False
        self.liste_boss = arcade.SpriteList()
        self.liste_projectiles_boss = arcade.SpriteList()
        self.murs_boss = arcade.SpriteList() # contenir les collisions et le calque declencheur
        self.scene = None
        # 2 initialisation des outils
        self.fleur = None
        self.physique = None
        self.inputs = InputHandler()
        self.hud = HUD()
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        self.temps_depuis_dernier_mob = 0

        self.timer_spawn_sol = 0.0
        self.timer_spawn_air = 0.0
        # si timer general utiliser
        self.timer_spawn = 0.0
        
        chemin_musique = os.path.join(DOSSIER_DATA, "sounds", "FLOIOIDE_bossfight_1.mp3")
        self.musique_fond = arcade.load_sound(chemin_musique)

        self.lecteur_musique = None

        self.son_saut = arcade.load_sound(os.path.join(DOSSIER_DATA, "sounds", "saut.wav"))
        self.son_pas = arcade.load_sound(os.path.join(DOSSIER_DATA, "sounds", "deplacement.ogg"))
        self.lecteur_pas = None 

        self.cooldown_shop = 0.0

        self.show_debug = False
        self.fps = 0

        self.timer_degats = 0
        self.show_hitboxes = True

        self.timer_soin_fontaine = 0

        self.shop = InterfaceShop()
        self.chat = Chat()

        self.timer_spawn = 0

        self.camera_jeu = arcade.camera.Camera2D() # pour le monde
        self.camera_gui = arcade.camera.Camera2D() # pour interface

        self.window.ctx.default_filter = (arcade.gl.NEAREST, arcade.gl.NEAREST)

        self.timer_vie_air = 10.0

        self.boss_fin_spawned = False
        self.boss_dvd_spawned = False

    def setup(self):    

        self.camera_sprites = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()

        # dezoom 0 5 pour voir plus large
        self.camera_jeu.zoom = 0.7

        """ configuration initiale du niveau et du spawn """
        # 1 chargement map tiled
        map_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        nom_murs = "hit-box" 
        
        layer_options = {nom_murs: {"use_spatial_hash": True}}
        self.tile_map = arcade.load_tilemap(map_path, scaling=2.0, layer_options=layer_options)
        
        # creer scene unique
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        

        # 2 creation joueur avant le reste
        self.fleur = Joueur(2026, 1800)
        self.fleur.scale = 0.5  # changer scale fleur
        self.fleur.hit_box = HitBox(self.fleur.texture.hit_box_points) # assurer collision

        # recuperation securisee des calques
        def charger_calque(nom_tiled, nom_tiroir):
            if nom_tiled in self.scene:
                self.tiroirs[nom_tiroir] = self.scene[nom_tiled]
            else:
                self.tiroirs[nom_tiroir] = arcade.SpriteList()

        
        # remplir tiroirs et murs pour physique
        charger_calque("hit-box", "murs")
        charger_calque("fontaine", "fontaines")
        charger_calque("tron", "tron")
        charger_calque("ver de terre", "trigger_ver")
        self.boss_ver_spawne = False # empecher double spawn
        charger_calque("bot", "trigger_robot")
        self.boss_robot_spawne = False # faire spawn une seule fois
        # nouvelle liste pour zones attaques robot
        self.tiroirs["attaques_boss"] = arcade.SpriteList()
        charger_calque("boss-test", "declencheurs")
        charger_calque("front", "front")
        charger_calque("back-ground", "background")

        # initialisation listes entites
        self.tiroirs["joueur"] = arcade.SpriteList()
        self.tiroirs["joueur"].append(self.fleur)
        
        self.tiroirs["pnj"] = arcade.SpriteList()

        coords_pnj = [
            (2765, 2797), (5893, 877), (12373, 2989), 
            (15154, 3949), (18868, 2989), (29084, 2733)
        ]

        # creer calque murs vide pour eviter crash
        if "murs" not in self.scene:
            self.scene.add_sprite_list("murs")

        # configuration cameras parallax
        self.camera_bg0 = arcade.camera.Camera2D()
        self.camera_bg1 = arcade.camera.Camera2D()
        
        # recuperer calques et retirer de scene principale pour gerer propre camera
        try:
            self.bg_parallax_0 = self.scene.get_sprite_list("font-bouge_0")
            self.scene.remove_sprite_list_by_name("font-bouge_0")
        except:
            self.bg_parallax_0 = arcade.SpriteList()

        try:
            self.bg_parallax_1 = self.scene.get_sprite_list("font-bouge_1")
            self.scene.remove_sprite_list_by_name("font-bouge_1")
        except:
            self.bg_parallax_1 = arcade.SpriteList()

        for x, y in coords_pnj:
            # passer x y et joueur a pnj pour orientation
            un_pnj = PNJ(x, y, self.fleur) 
            self.tiroirs["pnj"].append(un_pnj)
        
        self.tiroirs["ennemis"] = arcade.SpriteList()
        self.tiroirs["attaques"] = arcade.SpriteList()
        self.tiroirs["projectiles_ennemis"] = arcade.SpriteList()   
        self.tiroirs["tirs_ennemis"] = arcade.SpriteList()

        # ajout a la scene pour dessin
        self.scene.add_sprite_list("Couche_Joueur")
        self.scene.add_sprite("Couche_Joueur", self.fleur)

        # 3 moteur physique en dernier
        # joueur et murs sont prets
        self.physique = arcade.PhysicsEnginePlatformer(
            self.fleur, 
            gravity_constant=0.5, 
            walls=self.tiroirs["murs"]
        )

        # musique et boss
        if not self.lecteur_musique:
            self.lecteur_musique = arcade.play_sound(self.musique_fond, volume=0.5, loop=True)
        
        self.boss_actif = False
        
        # gestion declencheur boss
        if "test" in self.scene:
            self.tiroirs["declencheurs"] = self.scene["test"]
        else:
            if "declencheurs" not in self.tiroirs:
                self.tiroirs["declencheurs"] = arcade.SpriteList()
        
        self.etat = "JEU"

    def on_text(self, text):
        """ fonction appelee par arcade pour clavier """
        # verifier chat actif sans entree ou t au hasard
        if self.chat.actif and text != '\r' and text.isprintable():
            self.chat.texte_saisie += text

    def on_key_press(self, key, modifiers):

        if key == arcade.key.ESCAPE:
            if self.etat == "JEU":
                self.etat = "PAUSE"
            elif self.etat == "PAUSE":
                self.etat = "JEU"
            return
        
        # gestion du chat
        if key == arcade.key.T and not self.chat.actif:
            self.chat.actif = True
            return 

        if self.chat.actif:
            if key == arcade.key.ENTER:
                if self.chat.texte_saisie.strip():
                    self.chat.ajouter_message(f"Moi: {self.chat.texte_saisie}")
                self.chat.actif = False
                self.chat.texte_saisie = ""
            elif key == arcade.key.BACKSPACE:
                self.chat.texte_saisie = self.chat.texte_saisie[:-1]
            return # bloquer mouvements pendant ecriture

        if (key == arcade.key.LSHIFT or key == arcade.key.RSHIFT):
        # verifier fin du cooldown
            if getattr(self.fleur, 'dash_cooldown', 0) <= 0:
                self.fleur.en_dash = True
                self.fleur.dash_cooldown = 5.0 # temps de recharge
                self.fleur.dash_duree = 0      # temps du mouvement
                self.chat.ajouter_message("DASH !", arcade.color.GOLD)
            
        
        self.inputs.on_key_press(key)
        # saut simple uniquement au sol
        if key == arcade.key.SPACE and self.physique.can_jump():
            self.fleur.change_y = self.fleur.puissance_saut

        if key == arcade.key.SPACE or key == arcade.key.Z:
            if self.physique.can_jump():
                arcade.play_sound(self.son_saut, volume=0.3)

        if key == arcade.key.F3:
            self.show_debug = not self.show_debug

        if key == arcade.key.LSHIFT:
            # si appui sur dash
            if self.fleur.energie >= 100: 
                self.fleur.energie = 0
                self.fleur.en_dash = True # activer animation dash
                
                # appliquer vitesse dash selon direction
                direction = -1 if self.fleur.face_gauche else 1
                self.fleur.change_x = direction * self.fleur.vitesse_dash
                
                self.chat.ajouter_message("DASH !", arcade.color.GOLD)
            else:
                self.chat.ajouter_message("Énergie insuffisante...", arcade.color.GRAY)

        if key == arcade.key.F4 and self.mode_dev:
            self.interface_dev.ouvert = not self.interface_dev.ouvert
            return # bloquer autres inputs si besoin

        # logique double saut
        if key == arcade.key.SPACE:
            if self.physique.can_jump():
                self.fleur.change_y = self.fleur.puissance_saut
                self.fleur.double_saut_dispo = True
                arcade.play_sound(self.son_saut, volume=0.3)
            elif "2_saut.png" in self.fleur.inventaire_charmes and self.fleur.double_saut_dispo:
                # verifier charme et double saut dispo
                self.fleur.change_y = self.fleur.puissance_saut
                self.fleur.double_saut_dispo = False
                arcade.play_sound(self.son_saut, volume=0.3)

        # lacher objet
        if key == arcade.key.A and not self.fleur.etat_suppression:
            if self.fleur.inventaire_items[self.fleur.index_selection] is not None:
                self.fleur.etat_suppression = True
                
        # gerer pop up oui non
        if self.fleur.etat_suppression:
            if key == arcade.key.O or key == arcade.key.ENTER:
                self.fleur.inventaire_items[self.fleur.index_selection] = None
                self.fleur.etat_suppression = False
            elif key == arcade.key.N or key == arcade.key.ESCAPE:
                self.fleur.etat_suppression = False

        # utiliser objet selectionne
        if key == arcade.key.ENTER and not self.fleur.etat_suppression and not self.chat.actif:
            item = self.fleur.inventaire_items[self.fleur.index_selection]
            if item is not None:
                fichier = item["fichier"]
                utilise = False
                
                if fichier == "Heal1.png" and self.fleur.vie < self.fleur.vie_max:
                    self.fleur.vie = min(self.fleur.vie_max, self.fleur.vie + 20)
                    utilise = True
                elif fichier == "Heal2.png" and self.fleur.vie < self.fleur.vie_max:
                    self.fleur.vie = min(self.fleur.vie_max, self.fleur.vie + 50)
                    utilise = True
                elif fichier == "eau.1.png" and self.fleur.eau < 100:
                    self.fleur.eau = min(100, self.fleur.eau + 20)
                    utilise = True
                elif fichier == "eau.2.png" and self.fleur.eau < 100:
                    self.fleur.eau = min(100, self.fleur.eau + 40)
                    utilise = True
                elif fichier == "eau.3.png" and self.fleur.eau < 100:
                    self.fleur.eau = min(100, self.fleur.eau + 60)
                    utilise = True
                
                # reduire pile si consomme
                if utilise:
                    item["qte"] -= 1
                    if item["qte"] <= 0:
                        self.fleur.inventaire_items[self.fleur.index_selection] = None

    def on_key_release(self, key, modifiers):   
        self.inputs.on_key_release(key)
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        # changer slot avec molette
        if scroll_y > 0:
            self.fleur.index_selection = (self.fleur.index_selection - 1) % 3
        elif scroll_y < 0:
            self.fleur.index_selection = (self.fleur.index_selection + 1) % 3

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mode_dev:
            self.interface_dev.update_souris(x, y)
        
        self.mouse_world_x = x + self.camera_jeu.position.x
        self.mouse_world_y = y + self.camera_jeu.position.y

        # 1 ajustement par rapport a camera
        # utiliser bottom left x pour camera 2d dans arcade 3 0
        # utiliser position x pour ancienne camera
        world_x = x + self.camera_jeu.position.x
        world_y = y + self.camera_jeu.position.y
        self.shop.update_souris(x, y)

        # ajout effets survol boutons
        if self.etat == "PAUSE":
            self.btn_reprendre.scale = 0.6 if self.btn_reprendre.collides_with_point((x, y)) else 0.5
            self.btn_menu.scale = 0.6 if self.btn_menu.collides_with_point((x, y)) else 0.5
            self.btn_aide.scale = 0.6 if self.btn_aide.collides_with_point((x, y)) else 0.5
        elif self.etat == "MORT":
            print("Dommage ! Le jeu se ferme...")
            time.sleep(3)
            arcade.exit()


        try:
            mouse_x = x + self.camera_jeu.bottom_left.x
            mouse_y = y + self.camera_jeu.bottom_left.y
        except AttributeError:
            mouse_x = x + self.camera_jeu.position.x
            mouse_y = y + self.camera_jeu.position.y
        
        # 2 remettre tout a false
        for pnj in self.tiroirs.get("pnjs", []):
            pnj.est_survole = False
            
        # 3 detecter cible sous la souris
        pnjs_touches = arcade.get_sprites_at_point((mouse_x, mouse_y), self.tiroirs.get("pnjs", arcade.SpriteList()))
        for pnj in pnjs_touches:
            pnj.est_survole = True
        
        world_x = x + self.camera_jeu.position.x
        world_y = y + self.camera_jeu.position.y

        for pnj in self.tiroirs["pnjs"]:
            # verifier presence souris dans zone pnj
            if pnj.collides_with_point((world_x, world_y)):
                pnj.mouse_over = True
            else:
                pnj.mouse_over = False

    def on_mouse_press(self, x, y, button, modifiers):

        # clic dans aide ramene ecran precedent
        if self.etat == "AIDE":
            self.etat = self.etat_precedent
            return
            
        if self.etat == "MORT":
            if self.btn_rejouer.collides_with_point((x, y)):
                self.setup() # relancer partie de zero
            elif self.btn_menu.collides_with_point((x, y)):
                # creer nouvelle instance menu pour tout reinitialiser
                menu_view = MenuPrincipalView()
                self.window.show_view(menu_view)
            return
            
        if self.etat == "PAUSE":
            if self.btn_reprendre.collides_with_point((x, y)):
                self.etat = "JEU"
            elif self.btn_menu.collides_with_point((x, y)):
                # creer nouvelle instance menu pour tout reinitialiser
                menu_view = MenuPrincipalView()
                self.window.show_view(menu_view)

            elif self.btn_aide.collides_with_point((x, y)):
                self.etat_precedent = "PAUSE"
                self.etat = "AIDE"
            return

        if self.etat == "JEU":
            # clic bouton pause en haut a droite
            if self.btn_pause_jeu.collides_with_point((x, y)):
                self.etat = "PAUSE"
                return

        if self.mode_dev and self.interface_dev.ouvert:
            self.interface_dev.on_mouse_press(x, y, self.fleur)
            return # bloquer attaque si clic dans menu
        
        # verifier clic droit
        if button == arcade.MOUSE_BUTTON_RIGHT:
            # verifier si joueur tient fusil
            # nom fichier doit etre exact dans inventaire
            item_actuel = self.fleur.inventaire_items[self.fleur.index_selection]
            if item_actuel is not None and item_actuel.get("fichier") == "piou.png":
                
                # transformer coordonnees souris
                # en coordonnees monde pour cibler sur map
                vx = x + self.camera_jeu.position.x
                vy = y + self.camera_jeu.position.y
                
                # creation de la balle
                balle = ProjectileJoueur(self.fleur.center_x, self.fleur.center_y, vx, vy)
                
                # ajouter au tiroir pour afficher
                if "projectiles_joueur" in self.tiroirs:
                    self.tiroirs["projectiles_joueur"].append(balle)
                        

        # a si shop deja ouvert
        if self.shop.ouvert:
            res = self.shop.on_mouse_press(x, y)
            
            if res == "FERMER":
                self.shop.ouvert = False
                self.cooldown_shop = 2.0 # attendre 2s
            
            elif isinstance(res, dict) and not res.get("achete", False): 
                if self.fleur.monnaie >= res["prix"]:
                    if res["type"] == "charme":
                        if len(self.fleur.inventaire_charmes) < 4:
                            self.fleur.monnaie -= res["prix"]
                            self.fleur.inventaire_charmes.append(res["fichier"])
                            res["achete"] = True # disparaitre de boutique
                            self.chat.ajouter_message(f"Charme {res['nom']} équipé !", arcade.color.PURPLE)
                            
                            # appliquer effet direct pour charme de vie
                            if res["fichier"] == "coeurs+5.png":
                                self.fleur.vie_max = 150
                                self.fleur.vie += 50
                        else:
                            self.chat.ajouter_message("Barre de charmes pleine !", arcade.color.RED)
                    else:
                        # consommable ou arme empilable
                        trouve = False
                        for item in self.fleur.inventaire_items:
                            if item is not None and item["fichier"] == res["fichier"]:
                                item["qte"] += 1
                                trouve = True
                                break
                        
                        if not trouve: # chercher case vide si absent du stack
                            for i in range(1):
                                if self.fleur.inventaire_items[i] is None:
                                    self.fleur.inventaire_items[i] = {
                                        "nom": res["nom"], "fichier": res["fichier"], 
                                        "qte": 1, "tex": res["icon"]
                                    }
                                    trouve = True
                                    break
                                    
                        if trouve:
                            self.fleur.monnaie -= res["prix"]
                            self.chat.ajouter_message(f"Achat : {res['nom']}", arcade.color.GREEN)
                        else:
                            self.chat.ajouter_message("Inventaire plein !", arcade.color.RED)
                else:
                    self.chat.ajouter_message("Pas assez d'argent !", arcade.color.RED)
            return

        # b si shop ferme detection pnj
        if button == arcade.MOUSE_BUTTON_RIGHT:
            # conversion coordonnees ecran monde
            world_x = x + self.camera_jeu.position.x
            world_y = y + self.camera_jeu.position.y
            
            # parcourir les pnjs
            if "pnjs" in self.tiroirs:
                for pnj in self.tiroirs["pnjs"]:
                    # verifier clic sur pnj
                    if pnj.collides_with_point((world_x, world_y)):
                        if pnj.est_marchand:
                            self.shop.ouvert = True
                            print(f"Shop ouvert via {pnj.nom}")
                            return

        # clic gauche attaque
        elif button == arcade.MOUSE_BUTTON_LEFT:
            if "attaques" not in self.tiroirs:
                self.tiroirs["attaques"] = arcade.SpriteList()
            
            # verifier import dossier attaques
            nouvelle_attaque = EffetAttaque(self.fleur, DOSSIER_ATTAQUES)
            self.tiroirs["attaques"].append(nouvelle_attaque)

    def on_update(self, delta_time):

        if self.etat != "JEU":
            return
            
        # detection mort joueur
        if self.fleur.vie <= 0:
            self.etat = "MORT"
            return

        # faire defiler frames de attaque
        if "attaques" in self.tiroirs:
            self.tiroirs["attaques"].update() # appeler update de effet attaque
            self.tiroirs["attaques"].update_animation(delta_time)

        self.chat.update(delta_time)

        # 1 calcul fps pour menu f3
        if delta_time > 0:
            self.fps = 1 / delta_time

        # 2 centrage camera
        # calculer position camera pour centrer joueur
        target_x = self.fleur.center_x - LARGEUR / 2
        target_y = self.fleur.center_y - HAUTEUR / 2
        
        # recuperer taille map pour cacher le vide
        map_width = self.tile_map.width * self.tile_map.tile_width
        map_height = self.tile_map.height * self.tile_map.tile_height
        
        # bloquer camera aux bords de la map
        target_x = max(0, min(target_x, map_width - LARGEUR))
        target_y = max(0, min(target_y, map_height - HAUTEUR))
        
        # appliquer position a camera jeu
        self.camera_sprites.position = (target_x, target_y)
        
        # mise a jour cameras parallax axe x uniquement
        # fond bouge vite si chiffre proche de 1 0
        # fond lent si chiffre proche de 0
        # mise a jour cameras parallax
        vitesse_fond_proche = 0.85  # fond qui bouge 0
        vitesse_fond_loin = 0.60    # fond qui bouge 1

        # changer x pour vitesse et forcer y a suivre camera jeu
        self.camera_bg0.position = (self.camera_jeu.position.x * vitesse_fond_proche, self.camera_jeu.position.y)
        self.camera_bg1.position = (self.camera_jeu.position.x * vitesse_fond_loin, self.camera_jeu.position.y)

        # utiliser calque murs pour eviter blocage
        murs = self.scene.get_sprite_list("murs")
        do_separation = False  # changer nom pour eviter conflit
        if "murs" in self.scene:
            murs = self.scene["murs"]
            do_separation = True

        

        # regeneration fontaine
        # logique des fontaines
        # verifier collision a chaque frame
        fontaines_touchees = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["fontaines"])

        if fontaines_touchees:
            # regeneration eau
            if self.fleur.eau < self.fleur.eau_max:
                self.fleur.eau += 20 * delta_time  # ajuster vitesse 20 par seconde
                if self.fleur.eau > self.fleur.eau_max:
                    self.fleur.eau = self.fleur.eau_max

            # regeneration vie
            if self.fleur.vie < self.fleur.vie_max:
                self.fleur.vie += 5 * delta_time   # ajuster vitesse 5 par seconde
                if self.fleur.vie > self.fleur.vie_max:
                    self.fleur.vie = self.fleur.vie_max


        est_en_train_de_dasher = self.fleur.timer_dash > 6.8 
        self.fleur.en_dash = est_en_train_de_dasher

        # 3 calcul des mouvements
        vitesse = self.fleur.vitesse
        direction_horizontale = self.inputs.droite - self.inputs.gauche
        direction_verticale = self.inputs.haut - self.inputs.bas
        
        if self.fleur.noclip:
            # mode vol noclip
            self.fleur.change_x = direction_horizontale * vitesse * 2 # plus rapide en vol
            self.fleur.change_y = direction_verticale * vitesse * 2
            self.fleur.center_x += self.fleur.change_x
            self.fleur.center_y += self.fleur.change_y
            # ignorer update physique et escalade normale
        else:

            # declenchement dash
            if self.inputs.shift and self.fleur.timer_dash <= 0 and self.fleur.eau >= 10:
                self.fleur.eau -= 10
                self.fleur.timer_dash = 7.0
                self.fleur.change_y = 0 

            if est_en_train_de_dasher:
                vitesse = VITESSE_DASH
                self.fleur.change_y = 0 
                if direction_horizontale == 0:
                    direction_horizontale = -1 if self.fleur.flipped_horizontally else 1
            
            self.fleur.change_x = direction_horizontale * vitesse

            # 4 gestion sens du sprite flip
            if self.fleur.change_x < 0:
                self.fleur.flipped_horizontally = True
            elif self.fleur.change_x > 0:
                self.fleur.flipped_horizontally = False

            # 5 physique et escalade
            if est_en_train_de_dasher:
                # mode dash mouvement simple a travers murs
                self.fleur.center_x += self.fleur.change_x
                if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"]):
                    self.fleur.center_x -= self.fleur.change_x
            else:
                # systeme escalade simplifie
                self.fleur.en_escalade = False 
                if direction_horizontale != 0:
                    # tester presence mur a 2 pixels
                    self.fleur.center_x += (direction_horizontale * 2)
                    contact_mur = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"])
                    self.fleur.center_x -= (direction_horizontale * 2) # remettre joueur en place
                    
                    if contact_mur:
                        self.fleur.en_escalade = True

                # application de la physique
                if self.fleur.en_escalade:
                    self.fleur.change_x = 0
                    self.fleur.change_y = VITESSE_MARCHE
                    self.fleur.center_y += self.fleur.change_y
                    if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"]):
                        self.fleur.center_y -= self.fleur.change_y # annuler le mouvement
                        self.fleur.en_escalade = False
                else:
                    # gravite et sauts normaux si pas escalade
                    self.physique.update()

        # 6 animations et camera
        self.fleur.update_animation(delta_time)
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)
        self.camera_jeu.position = self.fleur.position

        # 7 logique de jeu collisions pluie ennemis
        gerer_collisions(self.tiroirs) 

        # 8 sons de pas
        if abs(self.fleur.change_x) > 0.1 and self.physique.can_jump() and not est_en_train_de_dasher:
            if not self.lecteur_pas:
                self.lecteur_pas = arcade.play_sound(self.son_pas, volume=0.1, loop=True)
        else:
            if self.lecteur_pas:
                arcade.stop_sound(self.lecteur_pas)
                self.lecteur_pas = None

        self.tiroirs["ennemis"].update_animation(delta_time)

        # gestion des degats
        self.timer_degats += delta_time
        
        # recuperer liste ennemis touchant fleur
        ennemis_proches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["ennemis"])

        # mise a jour ennemis et logiques
        # creer liste projectiles si inexistante
        if "projectiles_ennemis" not in self.tiroirs:
            self.tiroirs["projectiles_ennemis"] = arcade.SpriteList()

        for ennemi in self.tiroirs["ennemis"]:
            # mobs terrestres
            if hasattr(ennemi, "logique_sol"):
                ennemi.logique_sol(self.tiroirs["murs"])
            # mobs volants
            elif hasattr(ennemi, "logique_air"):
                ennemi.logique_air(self.fleur, self.tiroirs["projectiles_ennemis"])
            
            ennemi.orienter_vers_joueur(self.fleur)
            ennemi.update_animation(delta_time)

        # mise a jour listes secondaires
        if "projectiles_ennemis" in self.tiroirs:
            self.tiroirs["projectiles_ennemis"].update()

        if "attaques" in self.tiroirs:
            self.tiroirs["attaques"].update()
            for attaque in self.tiroirs["attaques"]:
                if hasattr(attaque, "update_animation"):
                    attaque.update_animation(delta_time)

        if self.fleur.vie <= 0:
            print("Game Over")
            self.setup() # recommencer le niveau
        
        if "pnj" in self.tiroirs:
            # animations
            # appeler update animation sur chaque pnj
            self.tiroirs["pnj"].update_animation(delta_time)

            # ouverture du shop
            # verifier si joueur touche pnj
            pnj_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["pnj"])
            
            if pnj_touches:
                # ouvrir shop si pnj touche
                self.shop.ouvert = True
                # figer joueur pour eviter fuite
                # bloquer deplacement joueur

        # logique des mobs
        mobs_sol = sum(1 for e in self.tiroirs["ennemis"] if hasattr(e, "volant") and not e.volant)
        mobs_air = sum(1 for e in self.tiroirs["ennemis"] if hasattr(e, "volant") and e.volant)

        self.timer_spawn_air += delta_time
        self.timer_spawn_sol += delta_time

        px = self.fleur.center_x
        py = self.fleur.center_y

        
        # dessiner barres de vie au dessus chaque mob
        for ennemi in self.tiroirs["ennemis"]:
            # 1 appliquer gravite et patrouille
            ennemi.logique_sol(self.tiroirs["murs"])
    
            # 2 tourner mob vers plante
            ennemi.orienter_vers_joueur(self.fleur)
    
            # 3 mettre a jour animation marche
            ennemi.update_animation(delta_time)
        
            if hasattr(ennemi, "logique_ia"):
                ennemi.logique_ia(self.fleur, self.tiroirs["tirs_ennemis"])
        
            # collision corps a corps degats joueur
            if hasattr(ennemi, "degats_contact") and ennemi.degats_contact > 0:
                if arcade.check_for_collision(self.fleur, ennemi):
                    if self.fleur.invulnerable_timer <= 0: # utiliser invulnerabilite si presente
                        self.fleur.vie -= ennemi.degats_contact
                        self.fleur.invulnerable_timer = 1.0
                
            # appliquer le mouvement
            if not getattr(ennemi, "volant", False):
                ennemi.change_y -= GRAVITE # mobs sol subissent gravite
            ennemi.center_x += ennemi.change_x
            ennemi.center_y += ennemi.change_y
            ennemi.update_animation(delta_time)

        # mise a jour projectiles ennemis
        self.tiroirs["tirs_ennemis"].update()
        for tir in self.tiroirs["tirs_ennemis"]:
            if arcade.check_for_collision(tir, self.fleur):
                if getattr(self.fleur, "invulnerable_timer", 0) <= 0:
                    self.fleur.vie -= tir.degats
                    self.fleur.invulnerable_timer = 1.0 # 1 seconde de pause avant prochain coup
                tir.remove_from_sprite_lists()

                self.fleur.dernier_coup_timer += delta_time

        
        # separateur
        # logique boss ver de terre
        # separateur

        if "trigger_ver" in self.tiroirs and not self.boss_ver_spawne:
            if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["trigger_ver"]):
                self.boss_ver_spawne = True
                # spawn a 24492 en x et 1850 en y plus haut
                boss_ver = BossVerDeTerre(24492, 1970, self.fleur) 
                
                if "boss" not in self.tiroirs:
                    self.tiroirs["boss"] = arcade.SpriteList()
                self.tiroirs["boss"].append(boss_ver)
                self.chat.ajouter_message("UN VER GÉANT SORT DE TERRE !", arcade.color.GOLD)

            if "boss" in self.tiroirs:
                for boss in self.tiroirs["boss"]:
                    if hasattr(boss, "vie") and boss.vie <= 0:
                        boss.remove_from_sprite_lists()

        # separateur
        # logique boss robot
        # separateur
        if "trigger_robot" in self.tiroirs and not self.boss_robot_spawne:
            if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["trigger_robot"]):
                self.boss_robot_spawne = True
                boss_robot = BossRobot(9000, 1800, self.fleur) 
                
                if "boss" not in self.tiroirs:
                    self.tiroirs["boss"] = arcade.SpriteList()
                self.tiroirs["boss"].append(boss_robot)
                self.chat.ajouter_message("LE BOSS ROBOT DESCEND DU CIEL !", arcade.color.RED)

        # mise a jour attaques de zones
        if "attaques_boss" in self.tiroirs:
            self.tiroirs["attaques_boss"].update(delta_time)
            
            # gestion carres rouges devenant attaques
            for effet in self.tiroirs["attaques_boss"]:
                if isinstance(effet, ZoneRougeAvertissement):
                    if effet.timer <= 0:
                        # remplacer par vraie attaque a la fin du timer
                        vraie_attaque = AttaqueDeZoneBoss(effet.center_x, effet.center_y, effet.type_attaque, self.fleur)
                        self.tiroirs["attaques_boss"].append(vraie_attaque)
                        effet.remove_from_sprite_lists()

        # separateur
        # logique boss tron
        # separateur
        
        # 1 declenchement boss
        if "tron" in self.tiroirs and self.etat_boss_tron == 0:
            if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["tron"]):
                self.etat_boss_tron = 1
                # spawn aux coordonnees demandees
                boss_p1 = BossArbreP1(4000, 2800, self.fleur) 
                if "boss" not in self.tiroirs: self.tiroirs["boss"] = arcade.SpriteList()
                self.tiroirs["boss"].append(boss_p1)
                

        if "boss" in self.tiroirs:
            for boss in self.tiroirs["boss"]:
                # envoyer temps au boss
                boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], self.tiroirs["murs"])

        # 2 gestion pendant le combat
        elif self.etat_boss_tron == 1:
            
            # mise a jour entites boss
            for boss in self.tiroirs["boss"]:
                # mettre a jour logique boss gravite tir saut
                boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], self.tiroirs["murs"])
                
                # degats de contact pour p2 et p3
                if hasattr(boss, "degats") and arcade.check_for_collision(self.fleur, boss):
                    self.fleur.vie -= boss.degats
                    # recul du joueur
                    self.fleur.center_x += 40 if self.fleur.center_x > boss.center_x else -40

            # utiliser sprite fleur plutot que spritelist
            projectiles_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["projectiles_ennemis"])
        
            for p in projectiles_touches:
                self.fleur.vie -= 1  # faire perdre vie au joueur
                p.remove_from_sprite_lists() # faire disparaitre le baton

            # attaque du joueur sur le boss
            if "attaques" in self.tiroirs:
                for attaque in self.tiroirs["attaques"]:
                    boss_touches = arcade.check_for_collision_with_list(attaque, self.tiroirs["boss"])
                    for boss in boss_touches:
                        # gerer degats attaque joueur
                        boss.vie -= 1 
                        
                        # action si le boss meurt
                        if boss.vie <= 0:
                            # charger phase suivante si existante
                            if hasattr(boss, "au_deces"):
                                nouveaux_mobs = boss.au_deces()
                                for mob in nouveaux_mobs:
                                    self.tiroirs["boss"].append(mob)
                            boss.remove_from_sprite_lists()

            # fin du combat
            if len(self.tiroirs["boss"]) == 0:
                print("Le Boss Tron est totalement détruit !")
                self.etat_boss_tron = 2
                self.tiroirs["projectiles_ennemis"].clear()

        if "projectiles_ennemis" in self.tiroirs:
            self.tiroirs["projectiles_ennemis"].update()
        
        # gestion du shop cooldown et collision
        if self.cooldown_shop > 0:
            self.cooldown_shop -= delta_time

        # verifier shop ferme et hors cooldown
        if not self.shop.ouvert and self.cooldown_shop <= 0:
            # verifier collision joueur pnj
            pnjs_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs.get("pnjs", arcade.SpriteList()))
            for pnj in pnjs_touches:
                if getattr(pnj, "est_marchand", False):
                    self.shop.ouvert = True
                    break # arreter boucle apres ouverture shop

        self.camera_sprites.position = (self.fleur.center_x, self.fleur.center_y)

        self.timer_general += delta_time
        
        # mettre a jour balles
        if "projectiles_joueur" in self.tiroirs:
            
            for proj in self.tiroirs["projectiles_joueur"]:
                proj.update_proj(delta_time)
                # degats aux ennemis et boss
                listes_cibles = [self.tiroirs.get("ennemis", []), self.tiroirs.get("boss", [])]
                pour_supprimer = False
                for liste in listes_cibles:
                    touches = arcade.check_for_collision_with_list(proj, liste)
                    for cible in touches:
                        if hasattr(cible, "vie"): cible.vie -= proj.degats
                        elif hasattr(cible, "points_de_vie"): cible.points_de_vie -= proj.degats
                        pour_supprimer = True
                if pour_supprimer:
                    proj.remove_from_sprite_lists()

        # 1 orientation ennemis vers joueur
        for ennemi in self.tiroirs["ennemis"]:
            if hasattr(ennemi, "orienter_vers_joueur"):
                ennemi.orienter_vers_joueur(self.fleur)
            
            # appeler logique deplacement pour mobsol
            if hasattr(ennemi, "logique_sol"):
                ennemi.logique_sol(self.tiroirs["murs"])
        
        # 2 gestion separation ennemis
        from logic import gerer_separation_mobs
        gerer_separation_mobs(self.tiroirs["ennemis"], self.tiroirs["murs"])

        # 1 mise a jour projectiles ennemis
        for proj in self.projectiles_ennemis:
            proj.update_proj(delta_time)
            # gerer collision avec joueur
            if arcade.check_for_collision(proj, self.fleur):
                self.fleur.vie -= proj.degats
                proj.remove_from_sprite_lists()

        # 2 mise a jour nouveaux mobs
        murs = self.scene["hit-box"] # utiliser le bon nom de calque
        for mob in self.ennemis:
            if hasattr(mob, "update_mob"):
                mob.update_mob(delta_time, murs)
                # gerer collision physique avec joueur
                if isinstance(mob, MobSol) and arcade.check_for_collision(mob, self.fleur):
                    # utiliser invul timer pour eviter one shot
                    self.fleur.vie -= mob.degats

        
        
        # a gestion des timers
        if self.timer_spawn_mobs > 0:
            self.timer_spawn_mobs -= delta_time
            
        if self.fleur.invul_timer > 0:
            self.fleur.invul_timer -= delta_time
            self.fleur.alpha = 150 # effet visuel degats
        else:
            self.fleur.alpha = 255

        # b mise a jour mobs et collisions
        murs = self.scene.get_sprite_list("hit-box") if "hit-box" in self.scene else None
        
        for mob in self.ennemis:
            if hasattr(mob, "update_mob"):
                mob.update_mob(delta_time, murs)
            
            # gestion des degats sur joueur
            if arcade.check_for_collision(mob, self.fleur):
                # verifier attribut mob
                if getattr(mob, "touche_joueur", 0) == 0:
                    self.fleur.vie -= 10  # perdre 10 pv
                    mob.touche_joueur = 1 # marquer mob comme ayant touche
                    mob.timer_touche_joueur = 1.0 # delai de 1s avant prochaine attaque mob

                    # appliquer recul au joueur
                    direction = 1 if self.fleur.center_x > mob.center_x else -1
                    self.fleur.center_x += direction * 50
                    
                    # destruction si mobsol
                    if isinstance(mob, MobSol):
                        mob.remove_from_sprite_lists()

        # c mise a jour projectiles
        for proj in self.projectiles_ennemis:
            proj.update_proj(delta_time)
            # verifier collision boule joueur
            if arcade.check_for_collision(proj, self.fleur):
                if self.fleur.invul_timer <= 0:
                    self.fleur.vie -= 10 # perdre 10 pv
                    self.fleur.invul_timer = 1.0 # 1 seconde de securite
                proj.remove_from_sprite_lists()

        # d systeme de spawn par zone
        if "mobs" in self.scene and self.timer_spawn_mobs <= 0:
            touches_spawn = arcade.check_for_collision_with_list(self.fleur, self.scene["mobs"])
            
            if touches_spawn:
                px = self.fleur.center_x
                py = self.fleur.center_y
                spawn_possible = True
                
                # choix donnees selon axe x
                if 0 <= px <= 16960: # zone foret
                    s_sol = {"vie": 2, "degats": 10, "drop_hit": 1, "drop_death": 2}
                    t_sol = [os.path.join(DOSSIER_DATA, "mobs", "foret", "sol", f"spi{i}.png") for i in range(2)]
                    s_air = {"vie": 2, "degats": 10, "drop_hit": 1, "drop_death": 2}
                    t_air = [os.path.join(DOSSIER_DATA, "mobs", "foret", "air", f"libu{i}.png") for i in range(4)]
                    c_boule = os.path.join(DOSSIER_DATA, "mobs", "foret", "air", "boule_bleue.png")
                
                elif 16961 <= px <= 27136: # zone desert
                    s_sol = {"vie": 2, "degats": 10, "drop_hit": 2, "drop_death": 4}
                    t_sol = [os.path.join(DOSSIER_DATA, "mobs", "desert", "sol", f"sable{i}.png") for i in range(2)]
                    s_air = {"vie": 2, "degats": 10, "drop_hit": 2, "drop_death": 3}
                    t_air = [os.path.join(DOSSIER_DATA, "mobs", "desert", "air", f"puce{i}.png") for i in range(2)]
                    c_boule = os.path.join(DOSSIER_DATA, "mobs", "desert", "air", "boule_bleue.png")
                    
                elif 27137 <= px <= 38320: # zone ville
                    s_sol = {"vie": 2, "degats": 10, "drop_hit": 4, "drop_death": 6}
                    t_sol = [os.path.join(DOSSIER_DATA, "mobs", "ville", "sol", f"mob_sol.{i}.png") for i in range(1, 6)]
                    s_air = {"vie": 2, "degats": 10, "drop_hit": 4, "drop_death": 3}
                    t_air = [os.path.join(DOSSIER_DATA, "mobs", "ville", "air", f"drone{i}.png") for i in range(2)]
                    c_boule = os.path.join(DOSSIER_DATA, "mobs", "ville", "air", "boule_bleue.png")
                else:
                    spawn_possible = False

                if spawn_possible:
                    self.timer_spawn_mobs = 30.0 # bloquer spawn pendant 30s
                    
                    # apparaitre exactement 2 mobs air et 2 sol
                    for _ in range(2):
                        # apparaitre mobs a 300px minimum
                        cote = random.choice([-1, 1])
                        dist_x = random.randint(300, 600)
                        
                        # apparition mob sol
                        m_sol = MobSol(px + (cote * dist_x), py + 100, self.fleur, s_sol, t_sol)
                        self.ennemis.append(m_sol)
                        
                        # apparition mob air
                        m_air = MobAir(px + (cote * dist_x), py + 300, self.fleur, s_air, t_air, c_boule, self.projectiles_ennemis)
                        self.ennemis.append(m_air)

        # e logique combat et collisions
        gerer_collisions(self.tiroirs)
        # mise a jour des ennemis
        murs = self.scene.get_sprite_list("murs") # nom calque collision
        for ennemi in self.tiroirs["ennemis"]:
            ennemi.update_mob(delta_time, murs)

        # reperes divers
        if do_separation:
            separer_mobs(self.tiroirs["ennemis"], murs) # appel fonction importee

        # 2 gestion du dash
        if self.fleur.timer_dash > 0:
            self.fleur.timer_dash -= delta_time

        # empecher superposition des mobs
        separer_mobs(self.tiroirs["ennemis"], murs)
    
        if "boss" in self.tiroirs:
            for boss in self.tiroirs["boss"]:
                # mise a jour standard
                boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], self.tiroirs["murs"])
                
                # recuperer attaques de zones bossrobot
                if hasattr(boss, "nouvelles_zones") and boss.nouvelles_zones:
                    for zone in boss.nouvelles_zones:
                        self.tiroirs["attaques_boss"].append(zone)
                    boss.nouvelles_zones.clear() # vider liste attente

        # 1 spawn boss fin
        if not self.boss_fin_spawned:
            try:
                if arcade.check_for_collision_with_list(self.fleur, self.scene.get_sprite_list("boss fin")):
                    if "boss" not in self.tiroirs: self.tiroirs["boss"] = arcade.SpriteList()
                    self.tiroirs["boss"].append(BossFin(36391, 2957, self.fleur))
                    self.boss_fin_spawned = True
            except (KeyError, AttributeError): pass

        # 2 spawn boss dvd
        if not self.boss_dvd_spawned:
            try:
                if arcade.check_for_collision_with_list(self.fleur, self.scene.get_sprite_list("dvd")):
                    if "boss" not in self.tiroirs: self.tiroirs["boss"] = arcade.SpriteList()
                    self.tiroirs["boss"].append(BossDVD(33652, 2983, self.fleur))
                    self.boss_dvd_spawned = True
            except (KeyError, AttributeError): pass

        # 3 fin du jeu
        try:
            if arcade.check_for_collision_with_list(self.fleur, self.scene.get_sprite_list("ending")):
                self.window.show_view(OutroView())
        except (KeyError, AttributeError): pass

        # 4 rebond boss dvd sur hit box
        try:
            calque_hitbox = self.scene.get_sprite_list("hit-box")
            if "boss" in self.tiroirs:
                for boss in self.tiroirs["boss"]:
                    if isinstance(boss, BossDVD):
                        if arcade.check_for_collision_with_list(boss, calque_hitbox):
                            # inversion direction pour rebond
                            boss.recul_x = -boss.change_x * 15 
                            boss.recul_y = -boss.change_y * 15
                            boss.recul_timer = 30 
        except (KeyError, AttributeError): pass

    def on_draw(self):
        # 1 nettoyer ecran
        self.clear()
        
        # 1 dessin parallax arriere plan
        # dessiner le plus loin en premier
        self.camera_bg1.use()
        self.bg_parallax_1.draw()
        
        self.camera_bg0.use()
        self.bg_parallax_0.draw()

        # 2 couche monde du jeu
        self.camera_jeu.use()
        self.scene.draw()
        
        # dessiner la map
        if self.scene:
            self.scene.draw()

        # dessiner entites
        # dessin des pnj
        if "pnj" in self.tiroirs:
            self.tiroirs["pnj"].draw()

        if "ennemis" in self.tiroirs: 
            self.tiroirs["ennemis"].draw()
        
        if "boss" in self.tiroirs:
            self.tiroirs["boss"].draw()

        self.ennemis.draw() 
        self.projectiles_ennemis.draw()

        if "boss" in self.tiroirs:
            self.tiroirs["boss"].draw()
            for b in self.tiroirs["boss"]:
                b.dessiner_barre_vie()
        
        if "projectiles_ennemis" in self.tiroirs: self.tiroirs["projectiles_ennemis"].draw()
        if "attaques" in self.tiroirs: self.tiroirs["attaques"].draw()
        if "attaques_boss" in self.tiroirs: self.tiroirs["attaques_boss"].draw()

        if "projectiles_joueur" in self.tiroirs:
            self.tiroirs["projectiles_joueur"].draw()

        # important joueur a dessiner ici
        # permettre deplacement sur carte
        if "joueur" in self.tiroirs:
            self.tiroirs["joueur"].draw()


        # b couche interface fixe sur ecran
        # activer camera gui coordonnees 0 0
        self.camera_gui.use()
        
        # dessiner ui
        self.hud.dessiner(self.fleur)
        self.hud.dessiner_inventaire_et_monnaie(self.fleur)
        self.chat.dessiner()
        
        # shop dans gui pour centrage
        if self.shop.ouvert:
            self.shop.dessiner()

        # c debug dans gui
        if self.show_debug:
            debug_txt = f"X: {int(self.fleur.center_x)} Y: {int(self.fleur.center_y)}\nFPS: {int(arcade.get_fps())}"
            arcade.draw_text(debug_txt, 20, HAUTEUR - 60, arcade.color.GREEN, 12, multiline=True, width=400)

        if self.mode_dev and self.interface_dev.ouvert:
            self.interface_dev.dessiner(self.fleur)

        # dessin barres vie mobs
        # camera sprites pour lier barres aux mobs
        for ennemi in self.tiroirs.get("ennemis", []):
            if hasattr(ennemi, "vie") and hasattr(ennemi, "vie_max"):
                pourcentage = max(0, ennemi.vie / ennemi.vie_max)
                largeur_barre = 40
                hauteur_barre = 6
                y_barre = ennemi.top + 10 # 10 pixels au dessus de sa tete
                
                # fond rouge pour vie perdue
                arcade.draw_rectangle_filled(
                    ennemi.center_x, y_barre, 
                    largeur_barre, hauteur_barre, 
                    arcade.color.RED
                )
                
                # premier plan vert pour vie restante
                if pourcentage > 0:
                    largeur_verte = largeur_barre * pourcentage
                    # decaler rectangle vert pour alignement gauche
                    decalage_x = ennemi.center_x - (largeur_barre - largeur_verte) / 2
                    arcade.draw_rectangle_filled(
                        decalage_x, y_barre, 
                        largeur_verte, hauteur_barre, 
                        arcade.color.GREEN
                    )

        # dessin barres vie ennemis
        for ennemi in self.ennemis:
            if hasattr(ennemi, "vie") and hasattr(ennemi, "vie_max") and ennemi.vie > 0:
                pourcentage = max(0, ennemi.vie / ennemi.vie_max)
                largeur_barre = 40
                hauteur_barre = 6
                y_barre = ennemi.top + 10 # au dessus de sa tete
                
                # fond rouge
                arcade.draw_rect_filled(
                    arcade.rect.XYWH(ennemi.center_x, y_barre, largeur_barre, hauteur_barre),
                    arcade.color.RED
                )
                
                # jauge verte
                if pourcentage > 0:
                    largeur_verte = largeur_barre * pourcentage
                    decalage_x = ennemi.center_x - (largeur_barre - largeur_verte) / 2
                    arcade.draw_rect_filled(
                        arcade.rect.XYWH(decalage_x, y_barre, largeur_verte, hauteur_barre),
                        arcade.color.GREEN
                    )
        
        # afficher uniquement quand jeu charge
        if self.etat in ["JEU", "PAUSE", "MORT", "AIDE"]:
            
            # overlay interface
            if self.etat == "JEU":
                arcade.draw_sprite(self.btn_pause_jeu)

            elif self.etat == "PAUSE":
                # filtre noir transparent
                arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, LARGEUR, HAUTEUR), (0, 0, 0, 150))
                arcade.draw_sprite(self.btn_reprendre)
                arcade.draw_sprite(self.btn_menu)
                arcade.draw_sprite(self.btn_aide)
                
            elif self.etat == "MORT":
                # filtre rouge transparent
                arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR // 2, HAUTEUR // 2, LARGEUR, HAUTEUR), (255, 0, 0, 150))
                arcade.draw_text("VOUS ETES MORT", LARGEUR // 2, HAUTEUR // 2 + 150, arcade.color.WHITE, 60, anchor_x="center", bold=True)
                arcade.draw_sprite(self.btn_rejouer)
                arcade.draw_sprite(self.btn_menu)

            elif self.etat == "AIDE":
                # filtre noir semi transparent
                arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, LARGEUR, HAUTEUR), (0, 0, 0, 220))
                texte_aide = (
                    "--- COMMANDES DU JEU ---\n\n"
                    "Mouvement : Flèches ou ZQSD\n"
                    "Sauter : Espace\n"
                    "Attaquer : Clic Gauche\n"
                    "Dash : Majuscule (Shift)\n"
                    "Boutique : Clic Droit sur un PNJ\n"
                    "Chat : Touche T\n\n"
                    "Cliquez n'importe où pour retourner."
                )
                arcade.draw_text("AIDE", LARGEUR//2, HAUTEUR - 100, arcade.color.WHITE, 40, bold=True, anchor_x="center")
                arcade.draw_text(texte_aide, LARGEUR//2, HAUTEUR//2, arcade.color.WHITE, 16, anchor_x="center", anchor_y="center", align="center", multiline=True, width=600)

class OutroView(arcade.View):
    def __init__(self):
        super().__init__()
        self.phase = 1
        self.frame = 0
        self.timer = 0
        self.quitter_timer = 0
        self.credit_y = 0
        self.textures = {}
        
        chemin_outro = os.path.join(CHEMIN_BASE, "data", "outro")
        # charger toutes phases de 1 a 6
        limites = {1: 1, 2: 1, 3: 1, 4: 3, 5: 1, 6: 19}
        for p, max_f in limites.items():
            self.textures[p] = []
            for f in range(max_f + 1):
                try:
                    self.textures[p].append(arcade.load_texture(os.path.join(chemin_outro, f"{p}.{f}.png")))
                except: pass

    def on_update(self, delta_time):
        self.timer += delta_time
        
        # phases 1 2 3 5 en boucle
        if self.phase in [0, 1, 2, 3]:
            if self.timer > 0.5:
                self.frame = (self.frame + 1) % len(self.textures.get(self.phase, [None]))
                self.timer = 0
                
        elif self.phase == 4:
            # arret a 4 3 index 3
            if self.frame < 3 and self.timer > 0.5:
                self.frame += 1
                self.timer = 0
                
        elif self.phase == 5:
            # defilement credits de haut en bas
            self.credit_y -= 50 * delta_time 
            if self.timer > 0.5:
                self.frame = (self.frame + 1) % len(self.textures.get(self.phase, [None]))
                self.timer = 0
                
        elif self.phase == 6:
            # animation jusqu a 6 19
            if self.frame < 19 and self.timer > 0.1:
                self.frame += 1
                self.timer = 0
            elif self.frame >= 19:
                self.quitter_timer += delta_time
                if self.quitter_timer >= 10:
                    arcade.exit() # fermeture apres 10s

    def on_draw(self):
        self.clear()
        if self.phase in self.textures and len(self.textures[self.phase]) > self.frame:
            tex = self.textures[self.phase][self.frame]
            # appliquer decalage y pour credits
            y_pos = HAUTEUR // 2 + self.credit_y if self.phase == 5 else HAUTEUR // 2
            arcade.draw_texture_rect(tex, arcade.rect.XYWH(LARGEUR//2, y_pos, LARGEUR, HAUTEUR))

    def on_key_press(self, key, modifiers):
        # appui entree pour phase suivante
        if key == arcade.key.ENTER:
            if self.phase < 6:
                self.phase += 1
                self.frame = 0
                self.timer = 0
                self.credit_y = 0
                
def main():
    window = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    # lancement menu principal au lieu cinematique
    menu_principal = MenuPrincipalView()
    window.show_view(menu_principal)
    arcade.run()

if __name__ == "__main__":
    main()