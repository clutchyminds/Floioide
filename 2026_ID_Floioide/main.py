import arcade
import random
import os
from sources.constantes import *
from sources.inputs import InputHandler
from sources.logic import gerer_collisions
from sources.entities import Joueur, Boss, MobDesertAir, MobDesertSol, MobDesertSol, MobForetAir, MobForetSol, MobVilleAir, MobVilleSol, PNJ, EffetAttaque
from sources.interface import HUD, Chat, InterfaceShop

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
        
        # 1. Organisation des listes d'objets (SpriteLists)
        self.tiroirs = {
            "murs": arcade.SpriteList(),      # Sera ton "hit-box"
            "front": arcade.SpriteList(),
            "background": arcade.SpriteList(),
            "boss_test": arcade.SpriteList(),
            "ennemis": arcade.SpriteList(),
            "tirs": arcade.SpriteList(),
            "joueur": arcade.SpriteList(),
            "pnjs": arcade.SpriteList()
        }
        
        # 2. Initialisation des outils
        self.fleur = None
        self.physique = None
        self.inputs = InputHandler()
        self.hud = HUD()
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        self.temps_depuis_dernier_mob = 0

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
    def setup(self):
        """ Configuration initiale du niveau et du spawn """
        
        # 1. Chargement de la Map Tiled
        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            # IMPORTANT : On stocke dans self.tile_map pour que tout le monde y ait accès
            self.tile_map = arcade.tilemap.load_tilemap(m_path, scaling=2.0)
            
            # --- RÉCUPÉRATION DES CALQUES ---
            # Calque Physique
            self.tiroirs["murs"] = self.tile_map.sprite_lists.get("hit-box", arcade.SpriteList())
            
            # Calque Premier plan
            self.tiroirs["front"] = self.tile_map.sprite_lists.get("front", arcade.SpriteList())
            
            # Calque Arrière-plan
            self.tiroirs["background"] = self.tile_map.sprite_lists.get("back-ground", arcade.SpriteList())
            
            # Calque test (Visuel seulement)
            self.tiroirs["test"] = self.tile_map.sprite_lists.get("boss-test", arcade.SpriteList())

            self.tiroirs["pnjs"] = arcade.SpriteList()
            mon_pnj = PNJ(x=790, y=2550)
            self.tiroirs["pnjs"].append(mon_pnj)

            self.tiroirs["tirs_ennemis"] = arcade.SpriteList()
            self.timer_spawn_air = 0
            self.timer_spawn_sol = 0

            self.tiroirs["attaques"] = arcade.SpriteList()

            # --- Logique de Spawn ---
            spawn_x, spawn_y = 2026, 1700
            if "Positions" in self.tile_map.object_lists:
                for obj in self.tile_map.object_lists["Positions"]:
                    if obj.name == "spawn_plante":
                        spawn_x = obj.shape[0] * 2
                        spawn_y = obj.shape[1] * 2
                        break
            
            self.fleur = Joueur(spawn_x, spawn_y)
            
        except Exception as e:
            print(f"Erreur chargement map : {e}")
            self.fleur = Joueur(500, 500)
            # On crée une map vide pour éviter que le reste du code plante
            self.tile_map = arcade.TileMap() 

        self.tiroirs["joueur"].append(self.fleur)
        self.tiroirs["fontaines"] = self.tile_map.sprite_lists.get("fontaine", arcade.SpriteList())

        # 2. Moteur Physique
        self.physique = arcade.PhysicsEnginePlatformer(
            self.fleur, 
            gravity_constant=0.5, 
            walls=self.tiroirs["murs"]
        )

        if not self.lecteur_musique:
            self.lecteur_musique = arcade.play_sound(self.musique_fond, volume=0.5, loop=True)

        # 3. GESTION DU BOSS ET DÉCLENCHEUR
        self.boss_apparu = False
        
        # On récupère le calque "test" qui sert de zone de déclenchement
        # .get() permet d'éviter un plantage si le calque n'existe pas dans Tiled
        self.tiroirs["declencheurs"] = self.tile_map.sprite_lists.get("test", arcade.SpriteList())

        
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
        # On ajuste les coordonnées avec la caméra
        poids_souris_x = x + self.camera_jeu.position.x
        poids_souris_y = y + self.camera_jeu.position.y

        if button == arcade.MOUSE_BUTTON_LEFT:
            # 1. On vérifie le timer (1.0 seconde)
            if self.fleur.dernier_coup_timer >= 1.0:
            
                # 2. On s'assure que la liste des attaques existe
                if "attaques" not in self.tiroirs:
                    self.tiroirs["attaques"] = arcade.SpriteList()

                # 3. On crée et on ajoute l'attaque
                nouvelle_attaque = EffetAttaque(self.fleur, dossier_attaques)
                self.tiroirs["attaques"].append(nouvelle_attaque)
            
                # 4. On RESET le timer
                self.fleur.dernier_coup_timer = 0
            else:
                print(f"Recharge... encore {1.0 - self.fleur.dernier_coup_timer:.1f}s")

        elif button == arcade.MOUSE_BUTTON_RIGHT:
            pnjs_touches = arcade.get_sprites_at_point(
                (poids_souris_x, poids_souris_y), 
                self.tiroirs["pnjs"]
            )
            if pnjs_touches:
                self.shop.afficher(pnjs_touches[0])

    def on_update(self, delta_time):
        # Ajouter ceci pour faire défiler les frames de l'attaque
        if "attaques" in self.tiroirs:
            for attaque in self.tiroirs["attaques"]:
                attaque.update_animation(delta_time)
                # Optionnel : si tu veux que l'attaque suive le joueur pendant qu'il bouge
                # attaque.center_x += self.fleur.change_x 
                # attaque.center_y += self.fleur.change_y

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

        # --- LOGIQUE DÉCLENCHEMENT BOSS ---
        # On ne vérifie la collision QUE si le boss n'est pas déjà apparu
        if not self.boss_apparu:
            zones_touchees = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["declencheurs"])
            if zones_touchees:
                # On crée UN SEUL boss aux coordonnées souhaitées
                le_boss = Boss(502, 2700) 
                le_boss.cible = self.fleur
                self.tiroirs["ennemis"].append(le_boss)
                
                # On verrouille pour ne plus jamais rentrer ici
                self.boss_apparu = True
                
                # On supprime les tuiles de déclenchement pour gagner en performance
                for z in zones_touchees:
                    z.remove_from_sprite_lists()

        # --- GESTION DES DÉGÂTS ---
        self.timer_degats += delta_time
        
        # On récupère la liste des ennemis qui touchent la fleur
        ennemis_proches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["ennemis"])

        if ennemis_proches:
            # Si 1 seconde (ou plus) s'est écoulée
            if self.timer_degats >= 1.0:
                self.fleur.vie -= 1    # -1 PV = -0.5 coeur
                print(f"DEBUG: Vie actuelle = {self.fleur.vie}/20") # <--- AJOUTE ÇA
                self.timer_degats = 0  # On reset le timer à ZERO
                
                # Feedback visuel : flash rouge
                self.fleur.color = arcade.color.RED
        else:
            # Si on ne touche rien, on remet la couleur normale
            # et on fait grimper le timer pour que le prochain coup soit instantané
            self.fleur.color = arcade.color.WHITE
            if self.timer_degats < 1.0:
                self.timer_degats += delta_time

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

        # Spawn Air (toutes les 30s)
        if self.timer_spawn_air > 30.0 and mobs_air < 5:
            offset_x = random.choice([-400, 400])
            if 0 <= px <= 8600:
                self.tiroirs["ennemis"].append(MobForetAir(px + offset_x, py + 200))
            elif 8600 < px <= 14000:
                self.tiroirs["ennemis"].append(MobDesertAir(px + offset_x, py + 200))
            else:
                self.tiroirs["ennemis"].append(MobVilleAir(px + offset_x, py + 200))
            self.timer_spawn_air = 0

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

        # Mise à jour des entités ennemies
        for ennemi in self.tiroirs["ennemis"]:
            if hasattr(ennemi, "verifier_despawn"):
                ennemi.verifier_despawn(delta_time)
        
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

    def on_draw(self):
        self.clear()
        
        if "tirs_ennemis" in self.tiroirs:
            self.tiroirs["tirs_ennemis"].draw()

        # Dessiner les barres de vie au-dessus de chaque mob
        for ennemi in self.tiroirs["ennemis"]:
            if hasattr(ennemi, "dessiner_barre_vie"):
                ennemi.dessiner_barre_vie()

        # 1. On active la caméra du jeu
        self.camera_jeu.use()
        
        
        # 2. On dessine les calques dans l'ordre (Arrière vers Avant)
        # 4ème plan
        if "boss_test" in self.tiroirs:
            self.tiroirs["boss_test"].draw()
            
        # 3ème plan
        if "background" in self.tiroirs:
            self.tiroirs["background"].draw()
            
        # 2ème plan (Le sol / hit-box)
        self.tiroirs["murs"].draw()
        
        if "fontaines" in self.tiroirs:
            self.tiroirs["fontaines"].draw()
            
        # Les entités
        self.tiroirs["ennemis"].draw()

        if "attaques" in self.tiroirs:
            self.tiroirs["attaques"].draw()

        self.tiroirs["tirs"].draw()
        
        self.hud.dessiner_inventaire_et_monnaie(self.fleur)
        self.shop.dessiner()
        
        self.tiroirs["ennemis"].draw_hit_boxes()
        self.tiroirs["joueur"].draw_hit_boxes()
        # 1er plan (Devant tout le monde)
        if "front" in self.tiroirs:
            self.tiroirs["front"].draw()

        
        
        # On dessine la liste des PNJs
        if "pnjs" in self.tiroirs:
            self.tiroirs["pnjs"].draw()
            
            # On rajoute les contours par-dessus si survolé
            for pnj in self.tiroirs["pnjs"]:
                if pnj.est_survole:
                    arcade.draw_rect_outline(
                        rect=pnj.rect,
                        color=arcade.color.WHITE,
                        border_width=3
                    )

        self.tiroirs["joueur"].draw() # Dessine la plante via la liste (plus fiable)


        if "attaques" in self.tiroirs:
            self.tiroirs["attaques"].draw()

        # 3. On active la caméra de l'interface (HUD)
        self.camera_gui.use()
        self.hud.dessiner(self.fleur)

        if self.show_debug:
            # Petit fond semi-transparent pour la lisibilité
            arcade.draw_rect_filled(
                arcade.LBWH(10, HAUTEUR - 110, 300, 100),
                (0, 0, 0, 150)
            )
            
            # Texte des coordonnées et FPS
            debug_text = (
                f"FPS: {int(self.fps)}\n"
                f"X: {int(self.fleur.center_x)} px\n"
                f"Y: {int(self.fleur.center_y)} px"
            )
            
            arcade.draw_text(
                debug_text,
                20, HAUTEUR - 100,
                arcade.color.GREEN,
                12,
                multiline=True,
                width=300
            )
        self.shop.dessiner()

        self.camera_gui.use()
        self.hud.dessiner(self.fleur)
        self.chat.dessiner() # On dessine le chat par dessus tout
        self.shop.dessiner()

        
def main():
    window = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    intro = CinematiqueView()
    window.show_view(intro)
    arcade.run()

if __name__ == "__main__":
    main()
