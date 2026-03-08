import arcade
import random
import os
from sources.constantes import *
from sources.entities import Joueur, Boss, PetitMob, Goutte
from sources.inputs import InputHandler
from sources.interface import HUD
from sources.logic import gerer_collisions

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
            "pluie": arcade.SpriteList()
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

    def setup(self):
        """ Configuration initiale du niveau et du spawn """
        
        # 1. Chargement de la Map Tiled
        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            # On charge la map une seule fois
            ma_map = arcade.tilemap.load_tilemap(m_path, scaling=2.0)
            
            # --- RÉCUPÉRATION DES CALQUES (Ordre de profondeur) ---
            # Calque 2 (Physique) : Le seul qui bloque le joueur
            self.tiroirs["murs"] = ma_map.sprite_lists.get("hit-box", arcade.SpriteList())
            
            # Calque 1 (Premier plan) : Devant tout le monde
            self.tiroirs["front"] = ma_map.sprite_lists.get("front", arcade.SpriteList())
            
            # Calque 3 (Arrière-plan) : Derrière le joueur
            self.tiroirs["background"] = ma_map.sprite_lists.get("back-ground", arcade.SpriteList())
            
            # Calque 4 (Très loin) : Derrière tout
            self.tiroirs["boss_test"] = ma_map.sprite_lists.get("boss-test", arcade.SpriteList())

            # --- Logique de Spawn ---
            spawn_x, spawn_y = 300, 3000  # Valeurs de secours
            if "Positions" in ma_map.object_lists:
                for obj in ma_map.object_lists["Positions"]:
                    if obj.name == "spawn_plante":
                        # Tiled utilise des coordonnées Y inversées par rapport à Arcade
                        spawn_x = obj.shape[0] * 2
                        spawn_y = obj.shape[1] * 2
                        break
            
            self.fleur = Joueur(spawn_x, spawn_y)
            
        except Exception as e:
            print(f"Erreur chargement map : {e}")
            self.fleur = Joueur(500, 500)

        self.tiroirs["joueur"].append(self.fleur)

        # 2. Moteur Physique (UNIQUEMENT avec le calque hit-box)
        # Comme on ne met pas "background" ou "front" ici, ils seront traversables
        self.physique = arcade.PhysicsEnginePlatformer(
            self.fleur, 
            gravity_constant=0.5, 
            walls=self.tiroirs["murs"]
        )

        if not self.lecteur_musique:
            self.lecteur_musique = arcade.play_sound(self.musique_fond, volume=0.5, loop=True)

    def on_key_press(self, key, modifiers):
        self.inputs.on_key_press(key)
        # Saut simple (uniquement si au sol)
        if key == arcade.key.SPACE and self.physique.can_jump():
            self.fleur.change_y = VITESSE_SAUT
        if key == arcade.key.SPACE or key == arcade.key.Z:
            if self.physique.can_jump():
                arcade.play_sound(self.son_saut, volume=0.3)

    def on_key_release(self, key, modifiers):
        self.inputs.on_key_release(key)

    def on_update(self, delta_time):
        # --- 1. GESTION DES TIMERS ET ÉTATS ---
        if self.fleur.timer_dash > 0:
            self.fleur.timer_dash -= delta_time
            
        # Le dash dure 0.2 seconde (entre 7.0 et 6.8)
        est_en_train_de_dasher = self.fleur.timer_dash > 6.8 
        self.fleur.en_dash = est_en_train_de_dasher

        # --- 2. CALCUL DE LA VITESSE ET DÉCLENCHEMENT ---
        vitesse = VITESSE_MARCHE
        
        # Déclenchement du dash
        if self.inputs.shift and self.fleur.timer_dash <= 0 and self.fleur.eau >= 10:
            self.fleur.eau -= 10
            self.fleur.timer_dash = 7.0
            self.fleur.change_y = 0 

        if est_en_train_de_dasher:
            vitesse = VITESSE_DASH
            self.fleur.change_y = 0 
        
        # Calcul de la direction horizontale
        direction = self.inputs.droite - self.inputs.gauche
        if direction == 0 and est_en_train_de_dasher:
            direction = 1 if not self.fleur.flipped_horizontally else -1
            
        self.fleur.change_x = direction * vitesse

        # --- 3. ANIMATION ET ORIENTATION ---
        # On le fait avant de déplacer le sprite pour que l'image soit la bonne
        self.fleur.update_animation(delta_time)

        # --- 4. PHYSIQUE ET COLLISIONS (Optimisée) ---
        if est_en_train_de_dasher:
            self.fleur.center_x += self.fleur.change_x
            if arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"]):
                self.fleur.center_x -= self.fleur.change_x
        else:
            # On détecte les murs autour du joueur
            murs_proches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"])
            direction_voulue = self.inputs.droite - self.inputs.gauche

            # GRIMPE : Si on touche un mur ET qu'on pousse vers lui
            if murs_proches and direction_voulue != 0:
                self.fleur.en_escalade = True
                self.fleur.change_x = 0  # On ne s'enfonce pas dans le mur
                self.fleur.change_y = VITESSE_MARCHE # On monte verticalement
                self.fleur.center_y += self.fleur.change_y
            else:
                # PHYSIQUE NORMALE
                self.fleur.en_escalade = False
                self.physique.update()

        # --- 5. CAMÉRA ET ÉVÉNEMENTS DU MONDE ---
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)
        gerer_collisions(self.tiroirs["tirs"], self.tiroirs["ennemis"])
        
        # Apparition ennemis
        self.temps_depuis_dernier_mob += delta_time
        if self.temps_depuis_dernier_mob > 5.0:
            offset = 400 if random.random() > 0.5 else -400
            ennemi = PetitMob(self.fleur.center_x + offset, self.fleur.center_y + 100)
            self.tiroirs["ennemis"].append(ennemi)
            self.temps_depuis_dernier_mob = 0

        # --- GESTION DES COLLISIONS AVEC LES GOUTTES ---
        gouttes_touchees = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["pluie"])
        for goutte in gouttes_touchees:
            goutte.remove_from_sprite_lists()
            # On augmente l'eau de la plante (par exemple +5 par goutte)
            self.fleur.eau = min(100, self.fleur.eau + 2)

        # --- 6. SYSTÈME DE PLUIE ---
        if random.random() < 0.1: 
            x = self.fleur.center_x + random.randint(-600, 600)
            y = self.fleur.center_y + 500
            goutte = Goutte(x, y)
            self.tiroirs["pluie"].append(goutte)

        self.tiroirs["pluie"].update()


        # NETTOYAGE : Supprimer ce qui est hors écran (très important contre le lag)
        for goutte in self.tiroirs["pluie"]:
            if goutte.top < -100:
                goutte.remove_from_sprite_lists()

        # --- 7. SONS DE PAS ---
        if abs(self.fleur.change_x) > 0.1 and self.physique.can_jump() and not est_en_train_de_dasher:
            if not self.lecteur_pas:
                self.lecteur_pas = arcade.play_sound(self.son_pas, volume=0.1, loop=True)
        else:
            if self.lecteur_pas:
                arcade.stop_sound(self.lecteur_pas)
                self.lecteur_pas = None
                
    def on_draw(self):
        self.clear()
        
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
        
        # Les entités
        self.tiroirs["ennemis"].draw()
        self.tiroirs["joueur"].draw() # Dessine la plante via la liste (plus fiable)
        self.tiroirs["pluie"].draw()
        self.tiroirs["tirs"].draw()
        
        # 1er plan (Devant tout le monde)
        if "front" in self.tiroirs:
            self.tiroirs["front"].draw()

        # 3. On active la caméra de l'interface (HUD)
        self.camera_gui.use()
        self.hud.dessiner(self.fleur)

def main():
    window = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    game = MonJeu()
    game.setup()
    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main()