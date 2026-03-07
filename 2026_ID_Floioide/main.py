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

    def on_key_release(self, key, modifiers):
        self.inputs.on_key_release(key)

    def on_update(self, delta_time):
        # 1. CALCUL DE LA VITESSE ET DASH
        vitesse = VITESSE_MARCHE
        if self.inputs.shift and self.fleur.eau > 0:
            vitesse = VITESSE_DASH
            self.fleur.en_dash = True
            self.fleur.eau = max(0, self.fleur.eau - 0.3)
        else:
            self.fleur.en_dash = False
        
        # On définit la direction voulue
        self.fleur.change_x = (self.inputs.droite - self.inputs.gauche) * vitesse

        # 2. MISE À JOUR DE L'ORIENTATION (Indispensable AVANT la physique)
        # On appelle l'animation ici pour qu'elle lise le change_x qu'on vient de définir
        self.fleur.update_animation(delta_time)

        # 3. LOGIQUE D'ESCALADE SIMPLE
        murs_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"])
        if murs_touches and (self.inputs.droite or self.inputs.gauche):
            self.fleur.en_escalade = True
            self.fleur.change_y = 4 
        else:
            self.fleur.en_escalade = False
            # On n'applique la physique (gravité) que si on ne grimpe pas
            self.physique.update()

        # 4. CAMÉRA ET COMBAT
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)
        gerer_collisions(self.tiroirs["tirs"], self.tiroirs["ennemis"])
        
        # 5. APPARITION ENNEMIS
        self.temps_depuis_dernier_mob += delta_time
        if self.temps_depuis_dernier_mob > 5.0:
            offset = 400 if random.random() > 0.5 else -400
            ennemi = PetitMob(self.fleur.center_x + offset, self.fleur.center_y + 100)
            self.tiroirs["ennemis"].append(ennemi)
            self.temps_depuis_dernier_mob = 0

        # --- SYSTÈME DE PLUIE ALÉATOIRE ---
        # 1% de chance qu'une goutte apparaisse à chaque frame
        if random.random() < 0.1: 
            # Apparaît au dessus du joueur, mais avec un décalage horizontal aléatoire
            x = self.fleur.center_x + random.randint(-600, 600)
            y = self.fleur.center_y + 500
            goutte = Goutte(x, y)
            self.tiroirs["pluie"].append(goutte)

        # Mise à jour de la position des gouttes
        self.tiroirs["pluie"].update()

        # 2. COLLISIONS : La plante boit les gouttes
        gouttes_bues = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["pluie"])
        for g in gouttes_bues:
            self.fleur.eau = min(100, self.fleur.eau + 0.5) # +5% d'eau par goutte
            g.remove_from_sprite_lists()

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