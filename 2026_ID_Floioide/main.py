import arcade
import random
from sources.constantes import *
from sources.entities import Joueur, Boss, PetitMob
from sources.inputs import InputHandler
from sources.interface import HUD
from sources.logic import gerer_collisions

class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        self.tiroirs = {
            "murs": arcade.SpriteList(),
            "decor": arcade.SpriteList(),
            "ennemis": arcade.SpriteList(),
            "tirs": arcade.SpriteList(),
            "joueur": arcade.SpriteList()
        }
        self.fleur = None
        self.physique = None
        self.inputs = InputHandler()
        self.hud = HUD()
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_gui = arcade.camera.Camera2D()
        self.temps_depuis_dernier_mob = 0

    def setup(self):
        """ Configuration initiale avec lecture du spawn Tiled """
        # 1. Charger la map
        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            ma_map = arcade.tilemap.load_tilemap(m_path, scaling=2)
            self.tiroirs["murs"] = ma_map.sprite_lists.get("hit-box", arcade.SpriteList())
            self.tiroirs["decor"] = ma_map.sprite_lists.get("back-ground", arcade.SpriteList())
            
            # --- LOGIQUE DE SPAWN ---
            # Valeurs de secours si on ne trouve pas le point dans Tiled
            spawn_x, spawn_y = 300, 10000 
            
            # On vérifie si le calque d'objets existe
            if "Positions" in ma_map.object_lists:
                for obj in ma_map.object_lists["Positions"]:
                    if obj.name == "spawn_plante":
                        # On récupère les coordonnées de l'objet
                        # shape[0] c'est X, shape[1] c'est Y
                        spawn_x = obj.shape[0] * 2  # *2 car scaling=2
                        spawn_y = obj.shape[1] * 2
                        print(f"Spawn trouvé dans Tiled : {spawn_x}, {spawn_y}")
                        break
            
            # Création du joueur au bon endroit
            self.fleur = Joueur(spawn_x, spawn_y)
            
        except Exception as e:
            print(f"Erreur : {e}")
            self.fleur = Joueur(500, 500) # Spawn de secours ultime

        self.tiroirs["joueur"].append(self.fleur)
        self.physique = arcade.PhysicsEnginePlatformer(self.fleur, gravity_constant=0.5, walls=self.tiroirs["murs"])


    def on_key_press(self, key, modifiers):
        self.inputs.on_key_press(key)
        if key == arcade.key.SPACE and self.physique.can_jump():
            self.fleur.change_y = VITESSE_SAUT

    def on_key_release(self, key, modifiers):
        self.inputs.on_key_release(key)

    def on_update(self, delta_time):
        # 1. Gestion du Dash et de l'état
        self.fleur.en_dash = False # Par défaut
        v = VITESSE_MARCHE
        
        if self.inputs.shift and self.fleur.eau > 0:
            v = VITESSE_DASH
            self.fleur.en_dash = True # On active l'état dash pour l'anim
            self.fleur.eau = max(0, self.fleur.eau - 0.4)
        
        self.fleur.change_x = (self.inputs.droite - self.inputs.gauche) * v

        # 2. Escalade (L'état en_escalade est déjà géré par ton bloc de collision)
        murs_touches = arcade.check_for_collision_with_list(self.fleur, self.tiroirs["murs"])
        if murs_touches and (self.inputs.droite or self.inputs.gauche):
            self.fleur.en_escalade = True


        # 3. Animations et Caméra
        self.fleur.update_animation(delta_time)
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)
        gerer_collisions(self.tiroirs["tirs"], self.tiroirs["ennemis"])

    def on_draw(self):
        self.clear()
        self.camera_jeu.use()
        for liste in self.tiroirs.values(): liste.draw()
        
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