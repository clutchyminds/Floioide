import arcade
import os
from sources.constantes import *
from sources.entities import Ennemi, LeBoss, Joueur, Projectile

class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        self.tiroir_fleur = arcade.SpriteList()
        self.tiroir_ennemis = arcade.SpriteList()
        self.tiroir_murs = arcade.SpriteList()
        self.tiroir_decor = arcade.SpriteList()
        self.tiroir_tirs = arcade.SpriteList()
        
        self.fleur = None
        self.physique = None
        
        # --- NOUVEAU SYSTEME DE CAMERA ---
        self.camera_jeu = arcade.camera.Camera2D()
        
        self.gauche_pressee = False
        self.droite_pressee = False
        self.z_presse = False

    def setup(self):
        self.fleur = Joueur(1200, 1500)
        self.tiroir_fleur.append(self.fleur)

        m_path = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            ma_map = arcade.tilemap.load_tilemap(m_path, scaling=2)
            self.tiroir_murs = ma_map.sprite_lists.get("hit-box", arcade.SpriteList())
            self.tiroir_decor = ma_map.sprite_lists.get("back-ground", arcade.SpriteList())
        except Exception as e: print(f"Erreur map: {e}")

        # Moteur physique standard pour le saut et la gravite
        self.physique = arcade.PhysicsEnginePlatformer(self.fleur, gravity_constant=0.5, walls=self.tiroir_murs)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Q: self.gauche_pressee = True
        elif key == arcade.key.D: self.droite_pressee = True
        elif key == arcade.key.Z: self.z_presse = True
        elif key == arcade.key.LSHIFT: self.fleur.en_dash = True
        elif key == arcade.key.SPACE:
            # On ne peut sauter que si on n'est pas en train de grimper
            if self.physique.can_jump() and not self.fleur.en_escalade:
                self.fleur.change_y = 12

    def on_key_release(self, key, modifiers):
        if key == arcade.key.Q: self.gauche_pressee = False
        elif key == arcade.key.D: self.droite_pressee = False
        elif key == arcade.key.Z: self.z_presse = False
        elif key == arcade.key.LSHIFT: self.fleur.en_dash = False

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Correction : on utilise unproject au lieu de map_screen_to_world
            pos_monde = self.camera_jeu.unproject((x, y))
            
            un_tir = Projectile(self.fleur.center_x, self.fleur.center_y, pos_monde[0], pos_monde[1], 10)
            self.tiroir_tirs.append(un_tir)

    def on_update(self, delta_time):
        # 1. Deplacement horizontal
        v = 10 if self.fleur.en_dash else 5
        self.fleur.change_x = (self.droite_pressee - self.gauche_pressee) * v

        # 2. Logique Grimpe vs Physique
        hit_list = arcade.check_for_collision_with_list(self.fleur, self.tiroir_murs)
        if hit_list and self.z_presse:
            self.fleur.en_escalade = True
            self.fleur.change_y = 4 
            # On deplace manuellement pour ignorer la gravite pendant la grimpe
            self.fleur.center_y += self.fleur.change_y
        else:
            self.fleur.en_escalade = False
            self.physique.update()

        # 3. Animations et tirs
        self.fleur.update_animation(delta_time)
        for t in self.tiroir_tirs: 
            t.update()
            t.update_animation(delta_time)

        # 4. CAMERA : Centrage sur le joueur (Methode stable 3.0)
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)

    def on_draw(self):
        self.clear()
        # On utilise la camera avant de dessiner
        self.camera_jeu.use()
        
        self.tiroir_decor.draw()
        self.tiroir_murs.draw()
        self.tiroir_ennemis.draw()
        self.tiroir_tirs.draw()
        self.tiroir_fleur.draw()

class Menu(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("FLOIOIDE - ENTREE (ZQSD + ESPACE)", LARGEUR/2, HAUTEUR/2, arcade.color.WHITE, 20, anchor_x="center")
    def on_key_press(self, key, mod):
        if key == arcade.key.ENTER:
            v = MonJeu(); v.setup(); self.window.show_view(v)

def main():
    win = arcade.Window(LARGEUR, HAUTEUR, TITRE)
    win.show_view(Menu())
    arcade.run()

if __name__ == "__main__": main()