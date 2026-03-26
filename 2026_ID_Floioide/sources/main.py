
import arcade
import random
import os
from constantes import *
from inputs import InputHandler
from logic import gerer_collisions
from entities import Joueur, MobAir, MobSol, MobDesertSol, MobForetSol, MobVilleSol, PNJ, EffetAttaque, BossArbreP1, BossArbreP2, BossArbreP3, BossVerDeTerre
from interface import HUD, Chat, InterfaceShop, InterfaceDev
import math
from arcade.hitbox import HitBox


class ProjectileJoueur(arcade.Sprite):
    def __init__(self, x, y, dest_x, dest_y):
        chemin = os.path.join(DOSSIER_DATA, "mobs", "PNJ", "items", "balle.png")
        try: 
            tex = arcade.load_texture(chemin)
        except: 
            tex = arcade.make_soft_square_texture(10, arcade.color.YELLOW)
        
        super().__init__(tex, scale=0.8)
        self.center_x, self.center_y = x, y
        self.degats = 2
        self.timer_vie = 0  # Chronomètre de vie
        
        # Calcul de l'angle vers le curseur
        angle_rad = math.atan2(dest_y - y, dest_x - x)
        
        # Vitesse basée sur la constante (448 px/s)
        self.change_x = math.cos(angle_rad) * VITESSE_TIR
        self.change_y = math.sin(angle_rad) * VITESSE_TIR
        
        # Orientation de la texture (Arcade utilise les degrés)
        # Comme ta balle pointe vers la droite par défaut, l'angle 0 est parfait
        self.angle = math.degrees(angle_rad)

    def update_proj(self, delta_time):
        # Déplacement simple
        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time
        
        # Gestion de la durée de vie (5 secondes)
        self.timer_vie += delta_time
        if self.timer_vie >= 5.0:
            self.remove_from_sprite_lists()

class EcranChargementView(arcade.View):
    def __init__(self, vue_suivante_class):
        super().__init__()
        self.vue_suivante_class = vue_suivante_class
        self.timer = 0
        self.indice_chargement = 1
        self.temp_anim = 0
        
        # Correction du nom de la variable pour éviter le TypeError
        self.frames_chargement = [] 
        
        # Logo réduit d'office
        self.logo = arcade.load_texture(os.path.join(DOSSIER_DATA, "Logo_.png"))

        # On charge les 6 images dans la BONNE variable
        for i in range(1, 7):
            chemin = os.path.join(DOSSIER_DATA, "chargement", f"{i}.png")
            if os.path.exists(chemin):
                self.frames_chargement.append(arcade.load_texture(chemin))
            else:
                # Texture de secours si fichier manquant
                self.frames_chargement.append(arcade.make_soft_square_texture(50, arcade.color.WHITE))

    def on_update(self, delta_time):
        self.timer += delta_time
        self.temp_anim += delta_time
        if self.temp_anim > 0.1:
            self.indice_chargement += 1
            if self.indice_chargement > 6: self.indice_chargement = 1
            self.temp_anim = 0

        if self.timer > 2.5: # Temps de chargement
            vue = self.vue_suivante_class()
            if hasattr(vue, "setup"): vue.setup()
            self.window.show_view(vue)

    def on_draw(self):
        self.clear()
        arcade.draw_rect_filled(arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2, LARGEUR, HAUTEUR), arcade.color.BLACK)
        
        # LOGO : échelle 0.5 (plus petit) avec pulsation
        echelle = 0.5 + math.sin(self.timer * 3) * 0.05
        arcade.draw_texture_rect(self.logo, arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2 + 80, 
                                 self.logo.width * echelle, self.logo.height * echelle))
        
        # Animation du petit chargement
        tex = self.frames_chargement[self.indice_chargement - 1]
        arcade.draw_texture_rect(tex, arcade.rect.XYWH(LARGEUR//2, HAUTEUR//2 - 120, 64, 64))

class MenuAideView(arcade.View):
    def __init__(self):
        super().__init__()
        # TEXTE À MODIFIER COMME TU VEUX
        self.texte_aide = (
            "--- COMMANDES DU JEU ---\n\n"
            "Mouvement : Flèches directionnelles ou ZQSD\n"
            "Sauter : Espace\n"
            "Attaquer : Clic Gauche\n"
            "Dash : Touche Majuscule (Shift)\n"
            "Boutique : Clic Droit sur un PNJ\n"
            "Chat : Touche T\n\n"
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
        
        # Variables pour l'animation
        self.timer = 0
        self.mouse_x = 0
        self.mouse_y = 0

        # Chemins des images
        try:
            self.fond = arcade.load_texture(os.path.join(DOSSIER_DATA, "intro", "image 1.1.png"))
            self.logo = arcade.load_texture(os.path.join(DOSSIER_DATA, "Logo_.png"))
            self.btn_jouer = arcade.load_texture(os.path.join(DOSSIER_DATA, "jouer.png"))
            self.btn_aide = arcade.load_texture(os.path.join(DOSSIER_DATA, "aide.png"))
        except:
            # Sécurité si les images ne sont pas encore créées
            self.fond = arcade.make_soft_square_texture(LARGEUR, arcade.color.BLACK)
            self.logo = arcade.make_soft_square_texture(200, arcade.color.GOLD)
            self.btn_jouer = arcade.make_soft_square_texture(200, arcade.color.DARK_GREEN)
            self.btn_aide = arcade.make_soft_square_texture(200, arcade.color.DARK_BLUE)
            
        self.historique = []
        # Code 1 : h, h, b, b, g, d, g, d, a, b, s
        self.code_dev_1 = [arcade.key.H, arcade.key.H, arcade.key.B, arcade.key.B, arcade.key.G, arcade.key.D, arcade.key.G, arcade.key.D, arcade.key.A, arcade.key.B, arcade.key.S]
        # Code 2 : Haut, Haut, Bas, Bas, Gauche, Droite, Gauche, Droite, A, B, Entrée
        self.code_dev_2 = [arcade.key.UP, arcade.key.UP, arcade.key.DOWN, arcade.key.DOWN, arcade.key.LEFT, arcade.key.RIGHT, arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.B, arcade.key.ENTER]

        

    def on_update(self, delta_time):
        self.timer += delta_time

    def on_mouse_motion(self, x, y, dx, dy):
        # On garde en mémoire la position de la souris
        self.mouse_x = x
        self.mouse_y = y

    def on_draw(self):
        self.clear()
        # Fond
        arcade.draw_texture_rect(self.fond, arcade.LBWH(0, 0, LARGEUR, HAUTEUR))
        
        # Calcul de la pulsation de base (grossit/rétrécit)
        pulsation = math.sin(self.timer * 4) * 0.05
        
        # --- LOGO : Plus petit avec pulsation ---
        scale_logo = 0.5 + pulsation # Base 0.5 au lieu de 1.0
        arcade.draw_texture_rect(self.logo, arcade.rect.XYWH(LARGEUR//2, HAUTEUR - 150, self.logo.width * scale_logo, self.logo.height * scale_logo))
        
        # --- BOUTON JOUER : Détection du survol ---
        survol_jouer = abs(self.mouse_x - self.x_btn) < self.w_btn_base/2 and abs(self.mouse_y - self.y_jouer) < self.h_btn_base/2
        scale_jouer = 1.15 if survol_jouer else 1.0 + pulsation # Gros et fixe si survolé, sinon pulse
        
        w_jouer = self.w_btn_base * scale_jouer
        h_jouer = self.h_btn_base * scale_jouer
        arcade.draw_texture_rect(self.btn_jouer, arcade.rect.XYWH(self.x_btn, self.y_jouer, w_jouer, h_jouer))
        arcade.draw_text("", self.x_btn, self.y_jouer, arcade.color.WHITE, int(20 * scale_jouer), bold=True, anchor_x="center", anchor_y="center")
        
        # --- BOUTON AIDE : Détection du survol ---
        survol_aide = abs(self.mouse_x - self.x_btn) < self.w_btn_base/2 and abs(self.mouse_y - self.y_aide) < self.h_btn_base/2
        scale_aide = 1.15 if survol_aide else 1.0 + pulsation
        
        w_aide = self.w_btn_base * scale_aide
        h_aide = self.h_btn_base * scale_aide
        arcade.draw_texture_rect(self.btn_aide, arcade.rect.XYWH(self.x_btn, self.y_aide, w_aide, h_aide))
        arcade.draw_text("", self.x_btn, self.y_aide, arcade.color.WHITE, int(20 * scale_aide), bold=True, anchor_x="center", anchor_y="center")

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # On utilise les dimensions de base pour la zone de clic
            if abs(x - self.x_btn) < self.w_btn_base/2 and abs(y - self.y_jouer) < self.h_btn_base/2:
                self.window.show_view(EcranChargementView(CinematiqueView))
            elif abs(x - self.x_btn) < self.w_btn_base/2 and abs(y - self.y_aide) < self.h_btn_base/2:
                self.window.show_view(MenuAideView())

    def on_key_press(self, key, modifiers):
        self.historique.append(key)
        # On ne garde que les 11 dernières touches
        if len(self.historique) > 11:
            self.historique.pop(0)

        # Si l'un des deux codes est tapé, on lance MonJeu en dev mode !
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
        chemin_musique = os.path.join(DOSSIER_DATA, "sounds", "Popi.mp3")
        self.musique_fond = arcade.load_sound(chemin_musique)
        self.lecteur_musique = arcade.play_sound(self.musique_fond, volume=0.5, loop=True)

        

        #12 textes pour l'intro du jeu
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
        #construction des chemin des images en alternance (animé) 
        chemin = os.path.join(DOSSIER_DATA, "intro")
        nom1 = f"image {self.scene_actuelle}.1.PNG"
        nom2 = f"image {self.scene_actuelle}.2.PNG"
        
        self.img1 = arcade.load_texture(os.path.join(chemin, nom1))
        self.img2 = arcade.load_texture(os.path.join(chemin, nom2))
        self.texture_active = self.img1
        
        self.texte_affiche = ""
        self.index_lettre = 0

    def on_update(self, delta_time):
        #animation de l'alternance entre les images .1 et .2
        self.timer_animation += delta_time
        if self.timer_animation > 0.5:
            self.texture_active = self.img2 if self.texture_active == self.img1 else self.img1
            self.timer_animation = 0

        # Effet d'écriture automatique
        if self.index_lettre < len(self.textes[self.scene_actuelle - 1]):
            self.timer_texte += delta_time
            if self.timer_texte > 0.04:
                self.index_lettre += 1
                self.texte_affiche = self.textes[self.scene_actuelle - 1][:self.index_lettre]
                self.timer_texte = 0
        

    def on_draw(self):
        self.clear()
        
        # utilise draw_lrbt_rectangle_filled avec la texture si possible
        # sinon dessine la texture via les coordonnées simples
        
        # Dans Arcade 3.0, pour dessiner une texture sur tout l'écran sans créer d'objet Rect :
        arcade.draw_texture_rect(
            self.texture_active, 
            arcade.LBWH(0, 0, LARGEUR, HAUTEUR) # LBWH = Left, Bottom, Width, Height
        )
        
        # Bandeau de texte noir en bas
        # Ici on utilise directement LBWH qui est beaucoup plus simple que Rect
        rect = arcade.LBWH(0, 0, LARGEUR, 150)
        arcade.draw_rect_filled(rect, arcade.color.BROWN)
        
        # Affichage du texte
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
                # 1. Arrêter la musique de l'intro
                arcade.stop_sound(self.lecteur_musique)
                
                # 2. On lance l'écran de chargement en lui disant qu'après, c'est MonJeu
                # On ne fait SURTOUT PAS game_view.setup() ici
                chargement = EcranChargementView(MonJeu) 
                self.window.show_view(chargement)

class MonJeu(arcade.View):
    def __init__(self, mode_dev=False):
        super().__init__()

        self.scene = None
        
        self.timer_spawn_mobs = 0.0

        self.etat_boss_tron = 0

        
        self.mode_dev = mode_dev

        self.interface_dev = InterfaceDev()

        self.camera_sprites = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()

        self.tiroirs = {}
        self.lecteur_musique = None

        self.mouse_world_x = 0
        self.mouse_world_y = 0
        self.timer_general = 0 # Pour faire tourner les charmes
        # Dans le setup(), ajoute :
        self.tiroirs["projectiles_joueur"] = arcade.SpriteList()

        self.ennemis = arcade.SpriteList()
        self.projectiles_ennemis = arcade.SpriteList()
        self.tiroirs["ennemis"] = self.ennemis

        # 1. Organisation des listes d'objets (SpriteLists)
        self.tiroirs = {
            "murs": arcade.SpriteList(),      # Sera ton "hit-box"
            "front": arcade.SpriteList(),
            "background": arcade.SpriteList(),
            "boss_test": arcade.SpriteList(),
            "ennemis": arcade.SpriteList(),
            "tirs": arcade.SpriteList(),
            "joueur": arcade.SpriteList(),
            "pnjs": arcade.SpriteList(),
            "boss": arcade.SpriteList(),             
            "projectiles_ennemis": arcade.SpriteList(), 
            "projectiles_joueur": arcade.SpriteList()
        }
        
        # variables pour gerer le systeme de boss
        self.boss_actif = False
        self.liste_boss = arcade.SpriteList()
        self.liste_projectiles_boss = arcade.SpriteList()
        self.murs_boss = arcade.SpriteList() # va contenir les collisions + le calque declencheur
        self.scene = None
        # 2. Initialisation des outils
        self.fleur = None
        self.physique = None
        self.inputs = InputHandler()
        self.hud = HUD()
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        self.temps_depuis_dernier_mob = 0

        self.timer_spawn_sol = 0.0
        self.timer_spawn_air = 0.0
        # Si ton code utilise aussi un timer général :
        self.timer_spawn = 0.0
        
        chemin_musique = os.path.join(DOSSIER_DATA, "sounds", "Popi.mp3")
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

        self.camera_jeu = arcade.camera.Camera2D() # Pour le monde
        self.camera_gui = arcade.camera.Camera2D() # Pour l'interface

        self.window.ctx.default_filter = (arcade.gl.NEAREST, arcade.gl.NEAREST)

    def setup(self):    

        self.camera_sprites = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()

        # 1.0 est la vue normale.   
        # Si tu mets 0.5, tu vois 2x plus de choses (tu dézoomes).
        # Si tu mets 2.0, tu zoomes de très près.
        self.camera_sprites.zoom = 0.5

        """ Configuration initiale du niveau et du spawn """
        # 1. Chargement de la Map Tiled
        map_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        nom_murs = "hit-box" 
        
        layer_options = {nom_murs: {"use_spatial_hash": True}}
        self.tile_map = arcade.load_tilemap(map_path, scaling=2.0, layer_options=layer_options)
        
        # Crée la scène unique
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # 2. Création du Joueur (DOIT ÊTRE FAIT AVANT LE RESTE)
        self.fleur = Joueur(2026, 1800)
        self.fleur.scale = 0.5  # Maintenant self.fleur existe, on peut changer le scale
        self.fleur.hit_box = HitBox(self.fleur.texture.hit_box_points) # Assure la collision

        # --- RÉCUPÉRATION SÉCURISÉE DES CALQUES ---
        def charger_calque(nom_tiled, nom_tiroir):
            if nom_tiled in self.scene:
                self.tiroirs[nom_tiroir] = self.scene[nom_tiled]
            else:
                self.tiroirs[nom_tiroir] = arcade.SpriteList()

        
        # On remplit les tiroirs (Surtout les murs pour la physique !)
        charger_calque("hit-box", "murs")
        charger_calque("fontaine", "fontaines")
        charger_calque("tron", "tron")
        charger_calque("ver de terre", "trigger_ver")
        self.boss_ver_spawne = False # Pour empêcher de le spawn 2 fois
        charger_calque("boss-test", "declencheurs")
        charger_calque("front", "front")
        charger_calque("back-ground", "background")

        # --- INITIALISATION DES LISTES D'ENTITÉS ---
        self.tiroirs["joueur"] = arcade.SpriteList()
        self.tiroirs["joueur"].append(self.fleur)
        
        self.tiroirs["pnj"] = arcade.SpriteList()

        coords_pnj = [
            (2765, 2797), (5893, 877), (12373, 2989), 
            (15154, 3949), (18868, 2989), (29084, 2733)
        ]

        for x, y in coords_pnj:
            # On passe x, y et le joueur (fleur) car la classe PNJ en a besoin pour te regarder
            un_pnj = PNJ(x, y, self.fleur) 
            self.tiroirs["pnj"].append(un_pnj)
        
        self.tiroirs["ennemis"] = arcade.SpriteList()
        self.tiroirs["attaques"] = arcade.SpriteList()
        self.tiroirs["projectiles_ennemis"] = arcade.SpriteList()   
        self.tiroirs["tirs_ennemis"] = arcade.SpriteList()

        # Ajout à la scène pour le dessin
        self.scene.add_sprite_list("Couche_Joueur")
        self.scene.add_sprite("Couche_Joueur", self.fleur)

        # 3. MOTEUR PHYSIQUE (EN DERNIER)
        # Maintenant que self.fleur ET self.tiroirs["murs"] sont prêts
        self.physique = arcade.PhysicsEnginePlatformer(
            self.fleur, 
            gravity_constant=0.5, 
            walls=self.tiroirs["murs"]
        )

        # Musique et Boss
        if not self.lecteur_musique:
            self.lecteur_musique = arcade.play_sound(self.musique_fond, volume=0.5, loop=True)
        
        self.boss_actif = False
        
        # GESTION DU DÉCLENCHEUR BOSS
        if "test" in self.scene:
            self.tiroirs["declencheurs"] = self.scene["test"]
        else:
            if "declencheurs" not in self.tiroirs:
                self.tiroirs["declencheurs"] = arcade.SpriteList()
        
    def on_text(self, text):
        """Fonction appelée automatiquement par Arcade quand on tape au clavier"""
        # Si le chat est actif et qu'on ne tape pas 'Entrée' ou 'T' au hasard
        if self.chat.actif and text != '\r' and text.isprintable():
            self.chat.texte_saisie += text

    def on_key_press(self, key, modifiers):
        # --- GESTION DU CHAT ---
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
            return # Bloque les mouvements quand on écrit

        if (key == arcade.key.LSHIFT or key == arcade.key.RSHIFT):
        # On vérifie si le cooldown est fini (variable à créer dans Joueur)
            if getattr(self.fleur, 'dash_cooldown', 0) <= 0:
                self.fleur.en_dash = True
                self.fleur.dash_cooldown = 5.0 # Temps de recharge
                self.fleur.dash_duree = 0      # Temps du mouvement
                self.chat.ajouter_message("DASH !", arcade.color.GOLD)
            
        
        self.inputs.on_key_press(key)
        # Saut simple (uniquement si au sol)
        if key == arcade.key.SPACE and self.physique.can_jump():
            self.fleur.change_y = self.fleur.puissance_saut

        if key == arcade.key.SPACE or key == arcade.key.Z:
            if self.physique.can_jump():
                arcade.play_sound(self.son_saut, volume=0.3)

        if key == arcade.key.F3:
            self.show_debug = not self.show_debug

        if key == arcade.key.LSHIFT:
            # Si on appuie sur Dash
            if self.fleur.energie >= 100: 
                self.fleur.energie = 0
                self.fleur.en_dash = True # Active l'animation de dash
                
                # Appliquer la vitesse du dash selon la direction où regarde le joueur
                direction = -1 if self.fleur.face_gauche else 1
                self.fleur.change_x = direction * self.fleur.vitesse_dash
                
                self.chat.ajouter_message("DASH !", arcade.color.GOLD)
            else:
                self.chat.ajouter_message("Énergie insuffisante...", arcade.color.GRAY)

        if key == arcade.key.F4 and self.mode_dev:
            self.interface_dev.ouvert = not self.interface_dev.ouvert
            return # On bloque les autres inputs si on veut

        # Double Saut logic
        if key == arcade.key.SPACE:
            if self.physique.can_jump():
                self.fleur.change_y = self.fleur.puissance_saut
                self.fleur.double_saut_dispo = True
                arcade.play_sound(self.son_saut, volume=0.3)
            elif "2_saut.png" in self.fleur.inventaire_charmes and self.fleur.double_saut_dispo:
                # Si on a le charme et qu'on n'a pas encore double sauté
                self.fleur.change_y = self.fleur.puissance_saut
                self.fleur.double_saut_dispo = False
                arcade.play_sound(self.son_saut, volume=0.3)

        # Drop item
        if key == arcade.key.A and not self.fleur.etat_suppression:
            if self.fleur.inventaire_items[self.fleur.index_selection] is not None:
                self.fleur.etat_suppression = True
                
        # Handle Pop-up Oui/Non
        if self.fleur.etat_suppression:
            if key == arcade.key.O or key == arcade.key.ENTER:
                self.fleur.inventaire_items[self.fleur.index_selection] = None
                self.fleur.etat_suppression = False
            elif key == arcade.key.N or key == arcade.key.ESCAPE:
                self.fleur.etat_suppression = False

        # Utiliser l'objet sélectionné
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
                
                # Réduction du stack si consommé
                if utilise:
                    item["qte"] -= 1
                    if item["qte"] <= 0:
                        self.fleur.inventaire_items[self.fleur.index_selection] = None

    def on_key_release(self, key, modifiers):   
        self.inputs.on_key_release(key)
    
    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        # Changement de slot avec la molette
        if scroll_y > 0:
            self.fleur.index_selection = (self.fleur.index_selection - 1) % 3
        elif scroll_y < 0:
            self.fleur.index_selection = (self.fleur.index_selection + 1) % 3

    def on_mouse_motion(self, x, y, dx, dy):
        if self.mode_dev:
            self.interface_dev.update_souris(x, y)
        
        self.mouse_world_x = x + self.camera_jeu.position.x
        self.mouse_world_y = y + self.camera_jeu.position.y

        # 1. Ajustement par rapport à la caméra
        # Si tu utilises Camera2D dans Arcade 3.0, c'est bottom_left.x !
        # Si tu utilises l'ancienne Camera, c'est position.x
        world_x = x + self.camera_jeu.position.x
        world_y = y + self.camera_jeu.position.y
        self.shop.update_souris(x, y)

        try:
            mouse_x = x + self.camera_jeu.bottom_left.x
            mouse_y = y + self.camera_jeu.bottom_left.y
        except AttributeError:
            mouse_x = x + self.camera_jeu.position.x
            mouse_y = y + self.camera_jeu.position.y
        
        # 2. On remet tout le monde à False
        for pnj in self.tiroirs.get("pnjs", []):
            pnj.est_survole = False
            
        # 3. On détecte qui est sous la souris
        pnjs_touches = arcade.get_sprites_at_point((mouse_x, mouse_y), self.tiroirs.get("pnjs", arcade.SpriteList()))
        for pnj in pnjs_touches:
            pnj.est_survole = True
        
        world_x = x + self.camera_jeu.position.x
        world_y = y + self.camera_jeu.position.y

        for pnj in self.tiroirs["pnjs"]:
            # Si la souris est dans la zone du PNJ
            if pnj.collides_with_point((world_x, world_y)):
                pnj.mouse_over = True
            else:
                pnj.mouse_over = False

    def on_mouse_press(self, x, y, button, modifiers):
        if self.mode_dev and self.interface_dev.ouvert:
            self.interface_dev.on_mouse_press(x, y, self.fleur)
            return # On bloque l'attaque si on clique dans le menu
        
        # On vérifie si c'est le clic droit
        if button == arcade.MOUSE_BUTTON_RIGHT:
            # Vérifie que le joueur tient bien le fusil
            # Note : "piou.png" doit être le nom EXACT dans ton inventaire
            if self.fleur.item_tenu == "piou.png":
                
                # IMPORTANT : On transforme les coordonnées de la souris 
                # en coordonnées "monde" pour tirer au bon endroit sur la map
                vx = x + self.camera_jeu.position.x
                vy = y + self.camera_jeu.position.y
                
                # Création de la balle
                balle = ProjectileJoueur(self.fleur.center_x, self.fleur.center_y, vx, vy)
                
                # On l'ajoute au tiroir pour qu'elle s'affiche
                if "projectiles_joueur" in self.tiroirs:
                    self.tiroirs["projectiles_joueur"].append(balle)
                        

        # --- A. SI LE SHOP EST DÉJÀ OUVERT ---
        if self.shop.ouvert:
            res = self.shop.on_mouse_press(x, y)
            
            if res == "FERMER":
                self.shop.ouvert = False
                self.cooldown_shop = 2.0 # On attend 2s
            
            elif isinstance(res, dict) and not res.get("achete", False): 
                if self.fleur.monnaie >= res["prix"]:
                    if res["type"] == "charme":
                        if len(self.fleur.inventaire_charmes) < 4:
                            self.fleur.monnaie -= res["prix"]
                            self.fleur.inventaire_charmes.append(res["fichier"])
                            res["achete"] = True # Disparaît de la boutique
                            self.chat.ajouter_message(f"Charme {res['nom']} équipé !", arcade.color.PURPLE)
                            
                            # Si c'est le charme de vie, on applique l'effet direct
                            if res["fichier"] == "coeurs+5.png":
                                self.fleur.vie_max = 150
                                self.fleur.vie += 50
                        else:
                            self.chat.ajouter_message("Barre de charmes pleine !", arcade.color.RED)
                    else:
                        # Consommable ou Arme (Empilable)
                        trouve = False
                        for item in self.fleur.inventaire_items:
                            if item is not None and item["fichier"] == res["fichier"]:
                                item["qte"] += 1
                                trouve = True
                                break
                        
                        if not trouve: # Si pas trouvé dans le stack, on cherche une case vide
                            for i in range(3):
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

        # --- B. SI LE SHOP EST FERMÉ (Détection du PNJ) ---
        if button == arcade.MOUSE_BUTTON_RIGHT:
            # IMPORTANT : Conversion des coordonnées écran -> monde
            world_x = x + self.camera_jeu.position.x
            world_y = y + self.camera_jeu.position.y
            
            # On boucle sur les PNJs
            if "pnjs" in self.tiroirs:
                for pnj in self.tiroirs["pnjs"]:
                    # On vérifie si le clic est SUR le PNJ
                    if pnj.collides_with_point((world_x, world_y)):
                        if pnj.est_marchand:
                            self.shop.ouvert = True
                            print(f"Shop ouvert via {pnj.nom}")
                            return

        # --- CLIC GAUCHE : ATTAQUE ---
        elif button == arcade.MOUSE_BUTTON_LEFT:
            if "attaques" not in self.tiroirs:
                self.tiroirs["attaques"] = arcade.SpriteList()
            
            # Assure-toi que dossier_attaques est bien importé depuis constantes.py
            nouvelle_attaque = EffetAttaque(self.fleur, dossier_attaques)
            self.tiroirs["attaques"].append(nouvelle_attaque)

    def on_update(self, delta_time):
        # Ajouter ceci pour faire défiler les frames de l'attaque
        if "attaques" in self.tiroirs:
            self.tiroirs["attaques"].update() # Appelle le update de EffetAttaque
            self.tiroirs["attaques"].update_animation(delta_time)

        self.chat.update(delta_time)

        # 1. Calcul des FPS pour le menu F3
        if delta_time > 0:
            self.fps = 1 / delta_time

        # 2. GESTION DU DASH (Timers et États)
        if self.fleur.timer_dash > 0:
            self.fleur.timer_dash -= delta_time

        # --- RÉGÉNÉRATION FONTAINE ---
        # --- LOGIQUE DES FONTAINES (À mettre dans on_update) ---
        # On vérifie la collision à chaque frame, même si le joueur est immobile
        fontaines_touchees = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["fontaines"])

        if fontaines_touchees:
            # Régénération de l'EAU
            if self.fleur.eau < self.fleur.eau_max:
                self.fleur.eau += 20 * delta_time  # Ajustez la vitesse (ici +20 par seconde)
                if self.fleur.eau > self.fleur.eau_max:
                    self.fleur.eau = self.fleur.eau_max

            # Régénération de la VIE
            if self.fleur.vie < self.fleur.vie_max:
                self.fleur.vie += 5 * delta_time   # Ajustez la vitesse (ici +5 par seconde)
                if self.fleur.vie > self.fleur.vie_max:
                    self.fleur.vie = self.fleur.vie_max


        est_en_train_de_dasher = self.fleur.timer_dash > 6.8 
        self.fleur.en_dash = est_en_train_de_dasher

        # 3. CALCUL DES MOUVEMENTS
        vitesse = self.fleur.vitesse
        direction_horizontale = self.inputs.droite - self.inputs.gauche
        direction_verticale = self.inputs.haut - self.inputs.bas
        
        if self.fleur.noclip:
            # --- MODE VOL / NOCLIP ---
            self.fleur.change_x = direction_horizontale * vitesse * 2 # Plus rapide en vol
            self.fleur.change_y = direction_verticale * vitesse * 2
            self.fleur.center_x += self.fleur.change_x
            self.fleur.center_y += self.fleur.change_y
            # On ignore complètement l'update physique et l'escalade normale
        else:

            # Déclenchement du dash
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

            # 4. GESTION DU SENS DU SPRITE (Le "Flip")
            if self.fleur.change_x < 0:
                self.fleur.flipped_horizontally = True
            elif self.fleur.change_x > 0:
                self.fleur.flipped_horizontally = False

            # 5. PHYSIQUE ET ESCALADE
            if est_en_train_de_dasher:
                # Mode Dash : mouvement simple à travers/contre les murs
                self.fleur.center_x += self.fleur.change_x
                if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"]):
                    self.fleur.center_x -= self.fleur.change_x
            else:
                # Système d'escalade simplifié
                self.fleur.en_escalade = False 
                if direction_horizontale != 0:
                    # On teste si un mur est présent juste à côté (2 pixels)
                    self.fleur.center_x += (direction_horizontale * 2)
                    contact_mur = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"])
                    self.fleur.center_x -= (direction_horizontale * 2) # On remet le joueur en place
                    
                    if contact_mur:
                        self.fleur.en_escalade = True

                # Application de la physique
                if self.fleur.en_escalade:
                    self.fleur.change_x = 0
                    self.fleur.change_y = VITESSE_MARCHE
                    self.fleur.center_y += self.fleur.change_y
                    if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"]):
                        self.fleur.center_y -= self.fleur.change_y # Annule le mouvement
                        self.fleur.en_escalade = False
                else:
                    # Gravité et sauts normaux (seulement si on n'escalade pas)
                    self.physique.update()

        # 6. ANIMATIONS ET CAMÉRA
        self.fleur.update_animation(delta_time)
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)
        self.camera_jeu.position = self.fleur.position

        # 7. LOGIQUE DE JEU (Collisions, Pluie, Ennemis)
        gerer_collisions(self.tiroirs) 

        # 8. SONS DE PAS
        if abs(self.fleur.change_x) > 0.1 and self.physique.can_jump() and not est_en_train_de_dasher:
            if not self.lecteur_pas:
                self.lecteur_pas = arcade.play_sound(self.son_pas, volume=0.1, loop=True)
        else:
            if self.lecteur_pas:
                arcade.stop_sound(self.lecteur_pas)
                self.lecteur_pas = None

        self.tiroirs["ennemis"].update_animation(delta_time)

        # --- GESTION DES DÉGÂTS ---
        self.timer_degats += delta_time
        
        # On récupère la liste des ennemis qui touchent la fleur
        ennemis_proches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["ennemis"])

        # --- MISE A JOUR DES ENNEMIS ET DE LEURS LOGIQUES ---
        # Sécurité : créer la liste de projectiles si elle n'existe pas
        if "projectiles_ennemis" not in self.tiroirs:
            self.tiroirs["projectiles_ennemis"] = arcade.SpriteList()

        for ennemi in self.tiroirs["ennemis"]:
            # Les mobs terrestres
            if hasattr(ennemi, "logique_sol"):
                ennemi.logique_sol(self.tiroirs["murs"])
            # Les mobs volants (C'EST ÇA QUI MANQUAIT)
            elif hasattr(ennemi, "logique_air"):
                ennemi.logique_air(self.fleur, self.tiroirs["projectiles_ennemis"])
            
            ennemi.orienter_vers_joueur(self.fleur)
            ennemi.update_animation(delta_time)

        # --- MISE A JOUR DES LISTES SECONDAIRES ---
        if "projectiles_ennemis" in self.tiroirs:
            self.tiroirs["projectiles_ennemis"].update()

        if "attaques" in self.tiroirs:
            self.tiroirs["attaques"].update()
            for attaque in self.tiroirs["attaques"]:
                if hasattr(attaque, "update_animation"):
                    attaque.update_animation(delta_time)

        if self.fleur.vie <= 0:
            print("Game Over")
            self.setup() # Pour recommencer le niveau
        
        if "pnj" in self.tiroirs:
            # --- LES ANIMATIONS ---
            # Cette ligne appelle update_animation() sur chaque PNJ de la liste
            self.tiroirs["pnj"].update_animation(delta_time)

            # --- L'OUVERTURE DU SHOP ---
            # On vérifie si le joueur (self.fleur) touche un PNJ
            pnj_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["pnj"])
            
            if pnj_touches:
                # Si on en touche un, on ouvre le shop
                self.shop.ouvert = True
                # Optionnel : On peut aussi figer le joueur pour qu'il ne s'enfuie pas direct
                # self.fleur.change_x = 0

        # --- LOGIQUE DES MOBS ---
        mobs_sol = sum(1 for e in self.tiroirs["ennemis"] if hasattr(e, "volant") and not e.volant)
        mobs_air = sum(1 for e in self.tiroirs["ennemis"] if hasattr(e, "volant") and e.volant)

        self.timer_spawn_air += delta_time
        self.timer_spawn_sol += delta_time

        px = self.fleur.center_x
        py = self.fleur.center_y

        # Spawn Sol (toutes les 15s par exemple)
        if self.timer_spawn_sol > 15.0 and mobs_sol < 5:
            offset_x = random.choice([-500, 500])
            if 0 <= px <= 8600:
                self.tiroirs["ennemis"].append(MobForetSol(px + offset_x, py + 50))
            elif 8600 < px <= 14000:
                self.tiroirs["ennemis"].append(MobDesertSol(px + offset_x, py + 50))
            else:
                self.tiroirs["ennemis"].append(MobVilleSol(px + offset_x, py + 50))
            self.timer_spawn_sol = 0

        
        # Dessiner les barres de vie au-dessus de chaque mob
        for ennemi in self.tiroirs["ennemis"]:
            # 1. Appliquer la gravité et patrouille
            ennemi.logique_sol(self.tiroirs["murs"])
    
            # 2. Tourner le mob vers la plante (self.fleur)
            ennemi.orienter_vers_joueur(self.fleur)
    
            # 3. Mettre à jour l'animation (marche)
            ennemi.update_animation(delta_time)
        
            if hasattr(ennemi, "logique_ia"):
                ennemi.logique_ia(self.fleur, self.tiroirs["tirs_ennemis"])
        
            # Collision corps à corps (Dégâts au joueur)
            if hasattr(ennemi, "degats_contact") and ennemi.degats_contact > 0:
                if arcade.check_for_collision(self.fleur, ennemi):
                    if self.fleur.invulnerable_timer <= 0: # Si tu as implémenté une invulnérabilité
                        self.fleur.vie -= ennemi.degats_contact
                        self.fleur.invulnerable_timer = 1.0
                
            # On applique le mouvement
            if not getattr(ennemi, "volant", False):
                ennemi.change_y -= GRAVITE # Les mobs au sol subissent la gravité
            ennemi.center_x += ennemi.change_x
            ennemi.center_y += ennemi.change_y
            ennemi.update_animation(delta_time)

        # Mise à jour des projectiles ennemis
        self.tiroirs["tirs_ennemis"].update()
        for tir in self.tiroirs["tirs_ennemis"]:
            if arcade.check_for_collision(tir, self.fleur):
                if getattr(self.fleur, "invulnerable_timer", 0) <= 0:
                    self.fleur.vie -= tir.degats
                    self.fleur.invulnerable_timer = 1.0 # 1 seconde de pause avant le prochain coup
                tir.remove_from_sprite_lists()

                self.fleur.dernier_coup_timer += delta_time

        
        # =========================================================
        # --- LOGIQUE DU BOSS VER DE TERRE ---
        # =========================================================

        if "trigger_ver" in self.tiroirs and not self.boss_ver_spawne:
            if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["trigger_ver"]):
                self.boss_ver_spawne = True
                # Spawn à 24492 en X et 1850 en Y (plus haut qu'avant)
                boss_ver = BossVerDeTerre(24492, 1970, self.fleur) 
                
                if "boss" not in self.tiroirs:
                    self.tiroirs["boss"] = arcade.SpriteList()
                self.tiroirs["boss"].append(boss_ver)
                self.chat.ajouter_message("UN VER GÉANT SORT DE TERRE !", arcade.color.GOLD)

        # =========================================================
        # --- LOGIQUE DU BOSS TRON ---
        # =========================================================
        
        # 1. DÉCLENCHEMENT DU BOSS
        if "tron" in self.tiroirs and self.etat_boss_tron == 0:
            if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["tron"]):
                self.etat_boss_tron = 1
                # CHANGEMENT : Spawn aux coordonnées demandées
                boss_p1 = BossArbreP1(4000, 2800, self.fleur) 
                if "boss" not in self.tiroirs: self.tiroirs["boss"] = arcade.SpriteList()
                self.tiroirs["boss"].append(boss_p1)
                

        if "boss" in self.tiroirs:
            for boss in self.tiroirs["boss"]:
                # C'est cette ligne qui envoie le "temps" au boss
                boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], self.tiroirs["murs"])

        # 2. GESTION PENDANT LE COMBAT
        elif self.etat_boss_tron == 1:
            
            # --- Mise à jour des entités Boss ---
            for boss in self.tiroirs["boss"]:
                # On met à jour sa logique (gravité, tir, saut)
                boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], self.tiroirs["murs"])
                
                # Dégâts de contact (seulement pour P2 et P3 qui ont un attribut 'degats')
                if hasattr(boss, "degats") and arcade.check_for_collision(self.fleur, boss):
                    self.fleur.vie -= boss.degats
                    # Recul du joueur
                    self.fleur.center_x += 40 if self.fleur.center_x > boss.center_x else -40

            # On utilise self.fleur (le Sprite) au lieu de la SpriteList
            projectiles_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["projectiles_ennemis"])
        
            for p in projectiles_touches:
                self.fleur.vie -= 1  # Le joueur perd de la vie
                p.remove_from_sprite_lists() # Le bâton disparaît

            # --- Le Joueur attaque le Boss ---
            if "attaques" in self.tiroirs:
                for attaque in self.tiroirs["attaques"]:
                    boss_touches = arcade.check_for_collision_with_list(attaque, self.tiroirs["boss"])
                    for boss in boss_touches:
                        # Gérer les dégâts de l'attaque du joueur ici
                        boss.vie -= 1 
                        
                        # Si le boss meurt
                        if boss.vie <= 0:
                            # S'il a une phase suivante (au_deces retourne une liste)
                            if hasattr(boss, "au_deces"):
                                nouveaux_mobs = boss.au_deces()
                                for mob in nouveaux_mobs:
                                    self.tiroirs["boss"].append(mob)
                            boss.remove_from_sprite_lists()

            # --- Fin du combat ---
            if len(self.tiroirs["boss"]) == 0:
                print("Le Boss Tron est totalement détruit !")
                self.etat_boss_tron = 2
                self.tiroirs["projectiles_ennemis"].clear()

        if "projectiles_ennemis" in self.tiroirs:
            self.tiroirs["projectiles_ennemis"].update()
        
        # --- GESTION DU SHOP (Cooldown et Collision) ---
        if self.cooldown_shop > 0:
            self.cooldown_shop -= delta_time

        # Si le shop est fermé et qu'on n'est pas en cooldown
        if not self.shop.ouvert and self.cooldown_shop <= 0:
            # Si le joueur touche un PNJ
            pnjs_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs.get("pnjs", arcade.SpriteList()))
            for pnj in pnjs_touches:
                if getattr(pnj, "est_marchand", False):
                    self.shop.ouvert = True
                    break # On arrête la boucle, le shop est ouvert

        self.camera_sprites.position = (self.fleur.center_x, self.fleur.center_y)

        self.timer_general += delta_time
        
        # Update les balles de Piou
        if "projectiles_joueur" in self.tiroirs:
            
            for proj in self.tiroirs["projectiles_joueur"]:
                proj.update_proj(delta_time)
                # Dégâts aux ennemis / boss
                listes_cibles = [self.tiroirs.get("ennemis", []), self.tiroirs.get("boss", [])]
                pour_supprimer = False
                for liste in listes_cibles:
                    touches = arcade.check_for_collision_with_list(proj, liste)
                    for cible in touches:
                        if hasattr(cible, "pv"): cible.pv -= proj.degats
                        elif hasattr(cible, "points_de_vie"): cible.points_de_vie -= proj.degats
                        pour_supprimer = True
                if pour_supprimer:
                    proj.remove_from_sprite_lists()

        # 1. MISE A JOUR DES PROJECTILES ENNEMIS (Boules bleues)
        for proj in self.projectiles_ennemis:
            proj.update_proj(delta_time)
            # Collision avec le joueur (dégâts de la boule)
            if arcade.check_for_collision(proj, self.fleur):
                self.fleur.vie -= proj.degats
                proj.remove_from_sprite_lists()

        # 2. MISE A JOUR DES NOUVEAUX MOBS
        murs = self.scene["hit-box"] # Assure-toi que c'est bien le nom de ton calque
        for mob in self.ennemis:
            if hasattr(mob, "update_mob"):
                mob.update_mob(delta_time, murs)
                # Collision physique (Dégâts au contact du joueur pour les mobs sol uniquement)
                if isinstance(mob, MobSol) and arcade.check_for_collision(mob, self.fleur):
                    # Attention, il te faudra peut-être un invul_timer sur le joueur pour ne pas le one-shot
                    self.fleur.vie -= mob.degats

        
        # --- GESTION DU TIMER DE SPAWN ---
        if self.timer_spawn_mobs > 0:
            self.timer_spawn_mobs -= delta_time

        # --- SYSTÈME DE SPAWN VIA LE CALQUE "mobs" ---
        if "mobs" in self.scene and self.timer_spawn_mobs <= 0:
            touches_spawn = arcade.check_for_collision_with_list(self.fleur, self.scene["mobs"])
            
            if touches_spawn:
                px = self.fleur.center_x
                spawn_possible = True
                
                # Définition des zones (Foret, Desert, Ville)
                if 0 <= px <= 16960:
                    stats_sol = {"pv": 2, "degats": 2.0, "drop_hit": 1, "drop_death": 2}
                    tex_sol = [os.path.join(DOSSIER_DATA, "mobs", "foret", "sol", f"spi{i}.png") for i in range(2)]
                    stats_air = {"pv": 2, "degats": 0.5, "drop_hit": 1, "drop_death": 2}
                    tex_air = [os.path.join(DOSSIER_DATA, "mobs", "foret", "air", f"libu{i}.png") for i in range(4)]
                    chemin_boule = os.path.join(DOSSIER_DATA, "mobs", "foret", "air", "boule_bleue.png")
                
                elif 16961 <= px <= 27136:
                    stats_sol = {"pv": 3, "degats": 2.5, "drop_hit": 2, "drop_death": 4}
                    tex_sol = [os.path.join(DOSSIER_DATA, "mobs", "desert", "sol", f"sable{i}.png") for i in range(2)]
                    stats_air = {"pv": 3, "degats": 1.0, "drop_hit": 2, "drop_death": 3}
                    tex_air = [os.path.join(DOSSIER_DATA, "mobs", "desert", "air", f"puce{i}.png") for i in range(2)]
                    chemin_boule = os.path.join(DOSSIER_DATA, "mobs", "desert", "air", "boule_bleue.png")
                    
                elif 27137 <= px <= 38320:
                    stats_sol = {"pv": 4, "degats": 3.0, "drop_hit": 4, "drop_death": 6}
                    tex_sol = [os.path.join(DOSSIER_DATA, "mobs", "ville", "sol", f"mob_sol.{i}.png") for i in range(1, 6)]
                    stats_air = {"pv": 4, "degats": 1.0, "drop_hit": 4, "drop_death": 3}
                    tex_air = [os.path.join(DOSSIER_DATA, "mobs", "ville", "air", f"drone{i}.png") for i in range(2)]
                    chemin_boule = os.path.join(DOSSIER_DATA, "mobs", "ville", "air", "boule_bleue.png")
                else:
                    spawn_possible = False

                if spawn_possible:
                    # On lance le cooldown de 30 secondes
                    self.timer_spawn_mobs = 30.0
                    
                    for _ in range(3):
                        # Spawn Sol
                        rx = px + random.randint(-640, 640)
                        ry = self.fleur.center_y + 100
                        self.ennemis.append(MobSol(rx, ry, self.fleur, stats_sol, tex_sol))
                        # Spawn Air
                        rax = px + random.randint(-640, 640)
                        ray = self.fleur.center_y + 300
                        self.ennemis.append(MobAir(rax, ray, self.fleur, stats_air, tex_air, chemin_boule, self.projectiles_ennemis))
                     
    def on_draw(self):
        # 1. On nettoie l'écran
        self.clear()
        
        # --- A. COUCHE "MONDE" (Tout ce qui bouge quand le joueur marche) ---
        # On utilise la caméra du jeu (qui suit le joueur)
        self.camera_jeu.use()
        
        # On dessine la map
        if self.scene:
            self.scene.draw()

        # On dessine les entités (PNJ, Ennemis, Boss)
        # --- DESSIN DES PNJ (À ajouter ici) ---
        if "pnj" in self.tiroirs:
            self.tiroirs["pnj"].draw()

        if "ennemis" in self.tiroirs: self.tiroirs["ennemis"].draw()
        
        if "boss" in self.tiroirs:
            self.tiroirs["boss"].draw()

        if "boss" in self.tiroirs:
            self.tiroirs["boss"].draw()
            for b in self.tiroirs["boss"]:
                b.dessiner_barre_vie()
        
        if "projectiles_ennemis" in self.tiroirs: self.tiroirs["projectiles_ennemis"].draw()
        if "attaques" in self.tiroirs: self.tiroirs["attaques"].draw()

        if "projectiles_joueur" in self.tiroirs:
            self.tiroirs["projectiles_joueur"].draw()

        # --- IMPORTANT : LE JOUEUR DOIT ÊTRE ICI ---
        # Pour qu'il se déplace sur la carte et pas qu'il soit collé à l'écran
        if "joueur" in self.tiroirs:
            self.tiroirs["joueur"].draw()


        # --- B. COUCHE "INTERFACE" (Tout ce qui reste fixe sur l'écran) ---
        # On switch sur la caméra GUI (Coordonnées 0,0 en bas à gauche de l'écran)
        self.camera_gui.use()
        
        # On dessine les éléments de l'UI
        self.hud.dessiner(self.fleur)
        self.hud.dessiner_inventaire_et_monnaie(self.fleur)
        self.chat.dessiner()
        
        # Le shop doit être dans la GUI pour rester au centre de l'écran
        if self.shop.ouvert:
            self.shop.dessiner()

        # --- C. DEBUG (Aussi dans la GUI pour être lisible) ---
        if self.show_debug:
            debug_txt = f"X: {int(self.fleur.center_x)} Y: {int(self.fleur.center_y)}\nFPS: {int(arcade.get_fps())}"
            arcade.draw_text(debug_txt, 20, HAUTEUR - 60, arcade.color.GREEN, 12, multiline=True, width=400)

        if self.mode_dev and self.interface_dev.ouvert:
            self.interface_dev.dessiner(self.fleur)
              
def main():
    window = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    # --- MODIFICATION ICI : On lance le menu principal au lieu de la cinématique ---
    menu_principal = MenuPrincipalView()
    window.show_view(menu_principal)
    arcade.run()

if __name__ == "__main__":
    main()
