import arcade
import os
from sources.constantes import *
from sources.entities import Ennemi, LeBoss

class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        self.tiroir_fleur = arcade.SpriteList()
        self.tiroir_ennemis = arcade.SpriteList()
        self.tiroir_murs = arcade.SpriteList()
        self.tiroir_arriere = arcade.SpriteList()
        self.fleur = None
        self.physique = None
        self.cam = arcade.camera.Camera2D()

    def setup(self):
        # 1. Joueur (data/player/player.png)
        p_path = os.path.join(DOSSIER_DATA, "player", "player.png")
        try:
            self.fleur = arcade.Sprite(p_path, 0.4)
        except:
            print("Image player.png introuvable")
            self.fleur = arcade.Sprite(":resources:images/items/star.png", 0.5)
        
        self.fleur.center_x = 200
        self.fleur.center_y = 300
        self.tiroir_fleur.append(self.fleur)

        # 2. Map (On force le passage malgre l erreur de tuile 310)
        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            # On charge la map normalement
            ma_map = arcade.tilemap.load_tilemap(m_path, scaling=2)
            self.tiroir_murs = ma_map.sprite_lists.get("hit-box", arcade.SpriteList())
            self.tiroir_arriere = ma_map.sprite_lists.get("base", arcade.SpriteList())
            print("Map chargee")
        except Exception as e:
            print(f"Erreur map : {e}")
            print("Conseil : Ouvre Tiled et supprime la tuile a la position (23, 84)")

        # 3. Physique
        self.physique = arcade.PhysicsEnginePlatformer(self.fleur, gravity_constant=0.5, walls=self.tiroir_murs)

        # 4. Ennemis (Spawn a cote du joueur)
        self.tiroir_ennemis.append(Ennemi(self.fleur.center_x + 300, self.fleur.center_y + 100))
        self.tiroir_ennemis.append(LeBoss(self.fleur.center_x + 600, self.fleur.center_y + 150))

    def on_draw(self):
        self.clear()
        self.cam.use()
        if self.tiroir_arriere: self.tiroir_arriere.draw()
        if self.tiroir_murs: self.tiroir_murs.draw()
        self.tiroir_ennemis.draw()
        self.tiroir_fleur.draw()

    def on_update(self, delta_time):
        if self.physique: self.physique.update()
        for e in self.tiroir_ennemis: e.update_animation(delta_time)
        self.cam.position = (self.fleur.center_x, self.fleur.center_y)

class Menu(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("FLOIOIDE - ENTREE", LARGEUR/2, HAUTEUR/2, arcade.color.WHITE, 20, anchor_x="center")
    def on_key_press(self, key, mod):
        if key == arcade.key.ENTER:
            v = MonJeu(); v.setup()
            self.window.show_view(v)

def main():
    win = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    win.show_view(Menu())
    arcade.run()

if __name__ == "__main__":
    main()