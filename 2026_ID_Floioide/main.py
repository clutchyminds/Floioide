import arcade
import random
import os
from sources.constantes import *
from sources.inputs import InputHandler
from sources.logic import gerer_collisions
from sources.entities import Joueur, Boss, MobDesertSol, MobForetSol, MobVilleSol, PNJ, EffetAttaque, BossArbreP1, BossArbreP2, BossArbreP3
from sources.interface import HUD, Chat, InterfaceShop
import math
from arcade.hitbox import HitBox

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
        arcade.draw_rect_filled(
            arcade.LBWH(0, 0, LARGEUR, 150),
            arcade.color.BLACK_BEAN
        )
        
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
                # Arrêter la musique de l'intro
                arcade.stop_sound(self.lecteur_musique)
                
                # Lancer le jeu
                game_view = MonJeu()
                game_view.setup()
                self.window.show_view(game_view)



class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()

        self.scene = None
        
        self.camera_sprites = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()

        self.tiroirs = {}
        self.lecteur_musique = None

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
            "boss": arcade.SpriteList(),               # <-- AJOUTE POUR LE BOSS
            "projectiles_ennemis": arcade.SpriteList(), # <-- AJOUTE POUR LES PROJECTILES DES ENNEMIS
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
        charger_calque("boss-test", "declencheurs")
        charger_calque("front", "front")
        charger_calque("back-ground", "background")

        # --- INITIALISATION DES LISTES D'ENTITÉS ---
        self.tiroirs["joueur"] = arcade.SpriteList()
        self.tiroirs["joueur"].append(self.fleur)
        
        self.tiroirs["pnjs"] = arcade.SpriteList()
        self.tiroirs["pnjs"].append(PNJ(790, 2550))
        
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
        
            
        
        self.inputs.on_key_press(key)
        # Saut simple (uniquement si au sol)
        if key == arcade.key.SPACE and self.physique.can_jump():
            self.fleur.change_y = VITESSE_SAUT
        if key == arcade.key.SPACE or key == arcade.key.Z:
            if self.physique.can_jump():
                arcade.play_sound(self.son_saut, volume=0.3)
        if key == arcade.key.F3:
            self.show_debug = not self.show_debug

        if key == arcade.key.LSHIFT: # Si on appuie sur Dash
            if self.fleur.energie >= 100: # On ne dash que si la barre est pleine
                self.fleur.energie = 0   # On vide la barre
                # Lancer ton code de Dash ici (vitesse_boost, etc.)
                self.chat.ajouter_message("DASH !", arcade.color.GOLD)
            else:
                self.chat.ajouter_message("Énergie insuffisante...", arcade.color.GRAY)

    def on_key_release(self, key, modifiers):
        self.inputs.on_key_release(key)

    def on_mouse_motion(self, x, y, dx, dy):
        # 1. Ajustement par rapport à la caméra
        # Si tu utilises Camera2D dans Arcade 3.0, c'est bottom_left.x !
        # Si tu utilises l'ancienne Camera, c'est position.x
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

    def on_mouse_press(self, x, y, button, modifiers):
        # --- CLIC DROIT : INTERACTION PNJ ---
        if button == arcade.MOUSE_BUTTON_RIGHT:
            # On convertit les coordonnées de l'écran en coordonnées du "monde"
            x_monde = x + self.camera_jeu.position[0]
            y_monde = y + self.camera_jeu.position[1]
            
            if "pnjs" in self.tiroirs:
                pnj_clique = arcade.get_sprites_at_point((x_monde, y_monde), self.tiroirs["pnjs"])
                if pnj_clique:
                    distance = math.dist((self.fleur.center_x, self.fleur.center_y),
                                         (pnj_clique[0].center_x, pnj_clique[0].center_y))
                    if distance < 150:
                        self.shop.actif = not self.shop.actif
                    else:
                        self.chat.ajouter_message("Le PNJ est trop loin !", couleur=arcade.color.RED)

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

        # Dans main.py, méthode on_update
        # --- LOGIQUE FONTAINE (EAU + VIE) ---
        if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["fontaines"]):
            # 1. Recharge d'eau (5% par seconde)
            self.fleur.eau = min(100, self.fleur.eau + (5 * delta_time))
    
            # 2. Recharge de vie (1 PV toutes les 3 secondes)
            self.timer_soin_fontaine += delta_time
            if self.timer_soin_fontaine >= 3.0:
                if self.fleur.vie < self.fleur.vie_max:
                    self.fleur.vie += 1
                    print(f"Soin ! Vie : {self.fleur.vie}")
                self.timer_soin_fontaine = 0 # Reset du chrono
        else:
            # Si on sort de la fontaine, on peut reset le timer 
            # pour ne pas "stocker" du temps de soin à l'extérieur
            self.timer_soin_fontaine = 0


        est_en_train_de_dasher = self.fleur.timer_dash > 6.8 
        self.fleur.en_dash = est_en_train_de_dasher

        # 3. CALCUL DES MOUVEMENTS
        vitesse = VITESSE_MARCHE
        direction_horizontale = self.inputs.droite - self.inputs.gauche
        
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
            else:
                # Gravité et sauts normaux (seulement si on n'escalade pas)
                self.physique.update()

        # 6. ANIMATIONS ET CAMÉRA
        self.fleur.update_animation(delta_time)
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)

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
        collision_tron = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["tron"])
        # --- LOGIQUE DÉCLENCHEMENT BOSS ---
        # On ne vérifie la collision QUE si le boss n'est pas déjà apparu
        if collision_tron and not self.boss_actif:
            # Sécurité supplémentaire : on vérifie si la liste est VRAIMENT vide
            if len(self.tiroirs["boss"]) == 0:
                print("SPAWN DU BOSS UNIQUE")
                self.boss_actif = True  # ON LE PASSE À TRUE IMMÉDIATEMENT
                
                nouveau_boss = BossArbreP1(2000, 1800, self.fleur)
                self.tiroirs["boss"].append(nouveau_boss)
        
                # IMPORTANT : On recrée le moteur physique pour que "tron" devienne solide
                self.moteur_physique = arcade.PhysicsEnginePlatformer(
                    self.fleur,
                    platforms=self.scene["tron"], # On ajoute le calque aux murs
                    gravity_constant=GRAVITE,
                    walls=self.tiroirs["murs"]
                )

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
        # Anime les PNJ
        for pnj in self.tiroirs["pnjs"]:
            pnj.update_animation(delta_time)

        # --- GESTION DES DÉGÂTS SUR LE BOSS ET MONNAIE ---
        # (Remplace ton appel à gerer_collisions pour les boss par ceci)
        for tir in self.tiroirs["tirs"]:
            ennemis_touches = arcade.check_for_collision_with_list(tir, self.tiroirs["ennemis"])
            if ennemis_touches:
                tir.remove_from_sprite_lists()
                for ennemi in ennemis_touches:
                    if isinstance(ennemi, Boss):
                        ennemi.vie -= 10
                        self.fleur.monnaie += 1  # +1 par tap
                        if ennemi.vie <= 0:
                            ennemi.remove_from_sprite_lists()
                            self.fleur.monnaie += 10 # +10 au kill
                    else:
                        ennemi.remove_from_sprite_lists() # Les petits mobs meurent direct
        if self.fleur.energie < 100:
            self.fleur.timer_energie += delta_time
            if self.fleur.timer_energie >= 2.0: # Toutes les 2 secondes
                self.fleur.energie += 25
                self.fleur.timer_energie = 0
                if self.fleur.energie > 100:
                    self.fleur.energie = 100

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

        # --- gestion du boss arbre ---
        
        if not self.boss_actif and "tron" in self.scene:
            hit_list = arcade.check_for_collision_with_list(self.fleur, self.scene["tron"])
    
            if len(hit_list) > 0:
                self.boss_actif = True
                print("Boss activé !")
        
                # 1. Créer le boss
                nouveau_boss = BossArbreP1(4094, 2669, self.fleur)
                self.tiroirs["boss"].append(nouveau_boss)
        
                # 2. RENDRE LE TRON SOLIDE
                murs_complets = arcade.SpriteList()
                murs_complets.extend(self.tiroirs["murs"])
                murs_complets.extend(self.scene["tron"])
                    
                # 3. On met à jour le moteur physique avec les vrais murs
                self.moteur_physique = arcade.PhysicsEnginePlatformer(
                    self.fleur,
                    walls=murs_complets, # utilise walls ici
                    gravity_constant=GRAVITE
                )
        
        for boss in self.tiroirs["boss"]:
            # On lui donne la liste des collisions de la map pour qu'il ne traverse pas le sol
            boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], self.tiroirs["murs"])

        # --- MISE A JOUR DES ENTITES DU BOSS ---
        if self.boss_actif and "boss" in self.tiroirs:
            
            # 1. creation des murs pour le boss
            murs_pour_boss = arcade.SpriteList()
            murs_pour_boss.extend(self.tiroirs["murs"])
            if "tron" in self.scene:
                murs_pour_boss.extend(self.scene["tron"])

            # 2. update des sprites boss
            for boss in self.tiroirs["boss"]:
                # le boss recoit les murs pour ne plus passer a travers le sol
                boss.update_boss(delta_time, self.tiroirs["projectiles_ennemis"], murs_pour_boss)
                
                # si le boss touche le joueur au corps a corps
                if arcade.check_for_collision(self.fleur, boss):
                    self.fleur.vie -= boss.degats
                    self.fleur.center_x += 30 if self.fleur.center_x > boss.center_x else -30

            # 3. update des projectiles (le baton)
            self.tiroirs["projectiles_ennemis"].update()
            for proj in self.tiroirs["projectiles_ennemis"]:
                if arcade.check_for_collision(self.fleur, proj):
                    self.fleur.vie -= proj.degats
                    proj.remove_from_sprite_lists()

            # 4. si le boss est totalement vaincu
            if len(self.tiroirs["boss"]) == 0:
                self.boss_actif = False
                self.tiroirs["projectiles_ennemis"].clear()
                # le calque tron redevient traversable
                self.moteur_physique = arcade.PhysicsEnginePlatformer(
                    self.fleur,
                    walls=self.tiroirs["murs"],
                    gravity_constant=GRAVITE
                )

            # 3. le joueur tape le boss
            if "attaques" in self.tiroirs and self.tiroirs["attaques"]:
                for attaque in self.tiroirs["attaques"]:
                    if not hasattr(attaque, "deja_touche_boss"):
                        attaque.deja_touche_boss = set()

                    boss_touches = arcade.check_for_collision_with_list(attaque, self.liste_boss)
                    for boss in boss_touches:
                        if boss not in attaque.deja_touche_boss:
                            boss.pv -= 1 # 1 de degat inflige par ton attaque
                            attaque.deja_touche_boss.add(boss)

                            # si le boss ou son entite meurt
                            if boss.pv <= 0:
                                # on regarde s il a une phase suivante (au_deces)
                                if hasattr(boss, "au_deces"):
                                    nouvelles_entites = boss.au_deces()
                                    for entite in nouvelles_entites:
                                        self.liste_boss.append(entite)
                                boss.remove_from_sprite_lists()

            # 4. verification de la fin totale du boss
            if len(self.liste_boss) == 0:
                self.boss_actif = False
                self.liste_projectiles_boss.clear()
                
                # le boss est mort, le calque tron redevient non solide
                self.moteur_physique = arcade.PhysicsEnginePlatformer(
                    self.fleur,
                    gravity_constant=GRAVITE,
                    walls=[self.tiroirs["murs"]]
                )
        self.camera_sprites.position = (self.fleur.center_x, self.fleur.center_y)

    def on_draw(self):
        # 1. On nettoie l'écran (très important pour ne pas avoir d'images fantômes)
        self.clear()
        
        # --- A. COUCHE "MONDE" (Tout ce qui bouge avec le joueur) ---
        self.camera_sprites.use() 
        self.camera_jeu.use()
        
        if self.scene:
            self.scene.draw()

        # On dessine les entités par-dessus
        if "pnjs" in self.tiroirs: self.tiroirs["pnjs"].draw()
        if "ennemis" in self.tiroirs: self.tiroirs["ennemis"].draw()
        if "boss" in self.tiroirs:
            self.tiroirs["boss"].draw()
            for b in self.tiroirs["boss"]:
                b.dessiner_barre_vie()
        
        if "projectiles_ennemis" in self.tiroirs: self.tiroirs["projectiles_ennemis"].draw()
        if "attaques" in self.tiroirs: self.tiroirs["attaques"].draw()

        # --- B. COUCHE "INTERFACE" (Tout ce qui reste fixe sur l'écran) ---
        self.camera_gui.use()
        
        # ON NE DESSINE JAMAIS LA SCENE ICI !
        self.hud.dessiner(self.fleur)
        self.hud.dessiner_inventaire_et_monnaie(self.fleur)
        self.chat.dessiner()
        self.shop.dessiner()
        # 3. ON DESSINE LE JOUEUR EN DERNIER (pour qu'il soit devant tout le monde)
        if "joueur" in self.tiroirs:
            self.tiroirs["joueur"].draw()
        # --- C. DEBUG ---
        if self.show_debug:
            debug_txt = f"X: {int(self.fleur.center_x)} Y: {int(self.fleur.center_y)}\nFPS: {int(arcade.get_fps())}"
            arcade.draw_text(debug_txt, 20, HAUTEUR - 60, arcade.color.GREEN, 12, multiline=True, width=400)
            
def main():
    window = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    intro = CinematiqueView()
    window.show_view(intro)
    arcade.run()

if __name__ == "__main__":
    main()
