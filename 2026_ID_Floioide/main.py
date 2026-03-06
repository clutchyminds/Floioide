import arcade
import random
import os
from sources.constantes import *
from sources.entities import Joueur, Boss, PetitMob
from sources.inputs import InputHandler
from sources.interface import HUD
from sources.logic import gerer_collisions

class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        
        # 1. Organisation des listes d'objets (SpriteLists)
        self.tiroirs = {
            "murs": arcade.SpriteList(),
            "decor": arcade.SpriteList(),
            "ennemis": arcade.SpriteList(),
            "tirs": arcade.SpriteList(),
            "joueur": arcade.SpriteList()
        }
        
        # 2. Initialisation des outils
        self.fleur = None
        self.physique = None
        self.inputs = InputHandler()
        self.hud = HUD()
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        
        self.temps_depuis_dernier_mob = 0

    def setup(self):
        """ Configuration initiale du niveau et du spawn """
        
        # 1. Chargement de la Map Tiled
        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            ma_map = arcade.tilemap.load_tilemap(m_path, scaling=2)
            self.tiroirs["murs"] = ma_map.sprite_lists.get("hit-box", arcade.SpriteList())
            self.tiroirs["decor"] = ma_map.sprite_lists.get("back-ground", arcade.SpriteList())
            
            # --- Logique de Spawn via Tiled ---
            spawn_x, spawn_y = 300, 300 # Valeurs de secours
            
            if "Positions" in ma_map.object_lists:
                for obj in ma_map.object_lists["Positions"]:
                    if obj.name == "spawn_plante":
                        spawn_x = obj.shape[0] * 2  # Multiplié par le scaling
                        spawn_y = obj.shape[1] * 2
                        print(f"Spawn chargé depuis Tiled : {spawn_x}, {spawn_y}")
                        break
            
            self.fleur = Joueur(spawn_x, spawn_y)
            
        except Exception as e:
            print(f"Erreur chargement map : {e}")
            self.fleur = Joueur(500, 500)

        self.tiroirs["joueur"].append(self.fleur)

        # 2. Moteur Physique (Platformer)
        self.physique = arcade.PhysicsEnginePlatformer(
            self.fleur, 
            gravity_constant=0.5, 
            walls=self.tiroirs["murs"]
        )

    def on_key_press(self, key, modifiers):
        self.inputs.on_key_press(key)
        # Saut simple (uniquement si au sol)
        if key == arcade.key.SPACE and self.physique.can_jump():
            self.fleur.change_y = VITESSE_SAUT

    def on_key_release(self, key, modifiers):
        self.inputs.on_key_release(key)

    def on_update(self, delta_time):
        # 1. Gestion du Dash et de la vitesse
        self.fleur.en_dash = False
        vitesse = VITESSE_MARCHE
        
        if self.inputs.shift and self.fleur.eau > 0:
            vitesse = VITESSE_DASH
            self.fleur.en_dash = True
            self.fleur.eau = max(0, self.fleur.eau - 0.3) # Consomme de l'eau
        
        self.fleur.change_x = (self.inputs.droite - self.inputs.gauche) * vitesse

        # 2. Escalade AUTOMATIQUE
        # On vérifie si la plante touche un mur
        murs_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"])
        
        # Si contact mur + appui vers le mur (Q ou D)
        if murs_touches and (self.inputs.droite or self.inputs.gauche):
            self.fleur.en_escalade = True
            self.fleur.change_y = 4      # Vitesse de montée
            self.fleur.center_y += 4    # Force le déplacement vers le haut
        else:
            self.fleur.en_escalade = False
            self.physique.update()      # Physique normale (gravité)

        # 3. Animations et Caméra
        self.fleur.update_animation(delta_time)
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)

        # 4. Collisions (Combat)
        gerer_collisions(self.tiroirs["tirs"], self.tiroirs["ennemis"])
        
        # 5. Apparition aléatoire d'ennemis
        self.temps_depuis_dernier_mob += delta_time
        if self.temps_depuis_dernier_mob > 5.0:
            offset = 400 if random.random() > 0.5 else -400
            ennemi = PetitMob(self.fleur.center_x + offset, self.fleur.center_y + 100)
            self.tiroirs["ennemis"].append(ennemi)
            self.temps_depuis_dernier_mob = 0

    def on_draw(self):
        self.clear()
        
        # Dessin du jeu (Caméra qui suit la plante)
        self.camera_jeu.use()
        for liste in self.tiroirs.values():
            liste.draw()
        
        # Dessin de l'interface (Caméra fixe)
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