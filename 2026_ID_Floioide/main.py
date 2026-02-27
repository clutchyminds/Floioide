import arcade
import os
from sources.constantes import *
from sources.entities import Ennemi, LeBoss

# reglages de deplacement
VITESSE_MARCHE = 5
VITESSE_SAUT = 12

class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        self.tiroir_fleur = arcade.SpriteList()
        self.tiroir_ennemis = arcade.SpriteList()
        self.tiroir_murs = arcade.SpriteList()
        self.tiroir_decor = arcade.SpriteList()
        self.fleur = None
        self.physique = None
        self.cam = arcade.camera.Camera2D()

    def setup(self):
        # 1. joueur
        p_path = os.path.join(DOSSIER_DATA, "player", "player.png")
        try:
            self.fleur = arcade.Sprite(p_path, 0.4)
        except:
            self.fleur = arcade.Sprite(":resources:images/items/star.png", 0.5)
        
        # SPAWN PLUS HAUT (y=1500)
        self.fleur.center_x = 1200 
        self.fleur.center_y = 1500
        self.tiroir_fleur.append(self.fleur)

        # 2. map
        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            ma_map = arcade.tilemap.load_tilemap(m_path, scaling=2)
            self.tiroir_murs = ma_map.sprite_lists.get("hit-box", arcade.SpriteList())
            self.tiroir_decor = ma_map.sprite_lists.get("back-ground", arcade.SpriteList())
            print("map chargee")
        except Exception as e:
            print(f"erreur map : {e}")

        # 3. physique
        self.physique = arcade.PhysicsEnginePlatformer(self.fleur, gravity_constant=0.5, walls=self.tiroir_murs)

        # 4. ennemis
        self.tiroir_ennemis.append(Ennemi(self.fleur.center_x + 200, self.fleur.center_y))
        self.tiroir_ennemis.append(LeBoss(self.fleur.center_x + 500, self.fleur.center_y + 100))

    def on_key_press(self, key, modifiers):
        # controles thomas
        if key == arcade.key.LEFT:
            self.fleur.change_x = -VITESSE_MARCHE
        elif key == arcade.key.RIGHT:
            self.fleur.change_x = VITESSE_MARCHE
        elif key == arcade.key.SPACE:
            if self.physique.can_jump():
                self.fleur.change_y = VITESSE_SAUT

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.fleur.change_x = 0

    def on_draw(self):
        self.clear()
        self.cam.use()
        if self.tiroir_decor: self.tiroir_decor.draw()
        if self.tiroir_murs: self.tiroir_murs.draw()
        self.tiroir_ennemis.draw()
        self.tiroir_fleur.draw()

    def on_update(self, delta_time):
        if self.physique:
            self.physique.update()
        for e in self.tiroir_ennemis:
            e.update_animation(delta_time)
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