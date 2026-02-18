# PROJET FLOÏOÏDE
# Equipe : Thomas, Victor, Laure et Corentin

import arcade
import os

# REGLAGES DE LA FENETRE
FENETRE_LARGEUR = 1280
FENETRE_HAUTEUR = 720
NOM_DU_JEU = "FLOÏOÏDE"

# GESTION DES CHEMINS
# On trouve ou est range ce fichier sur ton PC
CHEMIN_BASE = os.path.dirname(os.path.abspath(__file__))
# On pointe vers data/maps
DOSSIER_MAPS = os.path.join(CHEMIN_BASE, "data", "maps")

# SECTION 1 : L ECRAN DE MENU
class EcranMenu(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        self.clear()
        arcade.draw_text(NOM_DU_JEU, FENETRE_LARGEUR/2, 500, arcade.color.GREEN, 80, anchor_x="center")
        arcade.draw_text("Appuie sur ENTREE pour jouer", FENETRE_LARGEUR/2, 350, arcade.color.WHITE, 20, anchor_x="center")

    def on_key_press(self, touche, modificateurs):
        if touche == arcade.key.ENTER:
            le_jeu = MonJeu()
            le_jeu.setup()
            self.window.show_view(le_jeu)

# SECTION 2 : LE COEUR DU JEU
class MonJeu(arcade.View):
    def __init__(self):
        super().__init__()
        
        # Les tiroirs (SpriteLists) - On les met a None (vide) au debut
        self.tiroir_fleur = None
        self.tiroir_murs = None
        self.tiroir_arriere = None
        self.tiroir_devant = None
        self.tiroir_boss = None
        
        self.fleur_perso = None
        
        # Les cameras (les yeux du jeu)
        self.oeil_qui_suit = arcade.camera.Camera2D()
        self.oeil_fixe = arcade.camera.Camera2D()
        
        # Stats de Laure
        self.vie = 100
        self.eau = 100 
        
        # Variables de Thomas
        self.vitesse_dash = 0
        self.moteur_physique = None

    def setup(self):
        # 1. On prepare la fleur
        self.tiroir_fleur = arcade.SpriteList()
        self.fleur_perso = arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png", 0.5)
        self.fleur_perso.center_x = 200
        self.fleur_perso.center_y = 300
        self.tiroir_fleur.append(self.fleur_perso)

        # 2. On charge la map de Victor
        chemin_ma_map = os.path.join(DOSSIER_MAPS, "map.tmj")
        
        # On essaie de charger la map. Si le fichier n'existe pas, ca affichera une erreur plus claire.
        try:
            ma_map_tiled = arcade.load_tilemap(chemin_ma_map, scaling=2)
            
            # On remplit les tiroirs seulement si les calques existent dans Tiled
            # On utilise .get() pour eviter que le programme plante si le nom est mal ecrit
            self.tiroir_murs = ma_map_tiled.sprite_lists.get("hit-box")
            self.tiroir_arriere = ma_map_tiled.sprite_lists.get("base")
            # self.tiroir_devant = ma_map_tiled.sprite_lists.get("Decor_Devant")
            # self.tiroir_boss = ma_map_tiled.sprite_lists.get("Boss_Layer")
        except Exception as e:
            print(f"Erreur de chargement : {e}")

        # 3. On branche la physique (On verifie que le tiroir murs n'est pas vide)
        if self.tiroir_murs is not None:
            self.moteur_physique = arcade.PhysicsEnginePlatformer(
                self.fleur_perso, 
                gravity_constant=0.5, 
                walls=self.tiroir_murs
            )

    def on_draw(self):
        self.clear()
        self.oeil_qui_suit.use()
        
        # SECURITE : On dessine les tiroirs seulement s'ils ne sont pas vides (None)
        if self.tiroir_arriere:
            self.tiroir_arriere.draw()
            
        if self.tiroir_murs:
            self.tiroir_murs.draw()
            
        if self.tiroir_boss:
            self.tiroir_boss.draw()
            
        self.tiroir_fleur.draw()
        
        if self.tiroir_devant:
            self.tiroir_devant.draw()

        self.oeil_fixe.use()
        self.dessiner_hud()

    def dessiner_hud(self):
        # On dessine les barres de Laure
        arcade.draw_lrbt_rectangle_filled(20, 220, 680, 700, arcade.color.GRAY)
        largeur_vie = (self.vie / 100) * 200
        arcade.draw_lrbt_rectangle_filled(20, 20 + largeur_vie, 680, 700, arcade.color.RED)
        
        arcade.draw_lrbt_rectangle_filled(20, 220, 650, 670, arcade.color.GRAY)
        largeur_eau = (self.eau / 100) * 200
        arcade.draw_lrbt_rectangle_filled(20, 20 + largeur_eau, 650, 670, arcade.color.BLUE)

    def on_update(self, delta_time):
        if self.moteur_physique:
            self.moteur_physique.update()
        
        self.oeil_qui_suit.position = (self.fleur_perso.center_x, self.fleur_perso.center_y)
        
        if self.vitesse_dash > 0:
            self.fleur_perso.center_x += self.vitesse_dash
            self.vitesse_dash -= 1 
        
        if self.eau > 0:
            self.eau -= 0.05

    def on_key_press(self, touche, modificateurs):
        if touche == arcade.key.UP or touche == arcade.key.SPACE:
            if self.moteur_physique and self.moteur_physique.can_jump():
                self.fleur_perso.change_y = 12
        elif touche == arcade.key.LEFT:
            self.fleur_perso.change_x = -5
        elif touche == arcade.key.RIGHT:
            self.fleur_perso.change_x = 5
        elif touche == arcade.key.LSHIFT:
            if self.eau >= 20:
                self.vitesse_dash = 20
                self.eau -= 20

    def on_key_release(self, touche, modificateurs):
        if touche == arcade.key.LEFT or touche == arcade.key.RIGHT:
            self.fleur_perso.change_x = 0

def main():
    fenetre = arcade.Window(FENETRE_LARGEUR, FENETRE_HAUTEUR, NOM_DU_JEU)
    menu = EcranMenu()
    fenetre.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()