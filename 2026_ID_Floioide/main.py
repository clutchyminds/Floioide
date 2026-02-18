# PROJET FLOÏOÏDE
# Equipe : Thomas, Victor, Laure et Corentin

import arcade
import os

# REGLAGES DE LA FENETRE
FENETRE_LARGEUR = 1280
FENETRE_HAUTEUR = 720
NOM_DU_JEU = "FLOÏOÏDE"

# GESTION DES CHEMINS
CHEMIN_BASE = os.path.dirname(os.path.abspath(__file__))
DOSSIER_MAPS = os.path.join(CHEMIN_BASE, "data", "maps")

# ==========================================
# CLASSE DES PETITS ENNEMIS (Corentin)
# ==========================================
class EnnemiAnime(arcade.Sprite):
    def __init__(self, images, x, y):
        super().__init__()
        # SECURITÉ : Si la liste est vide (erreur chargement), on met un carré rouge
        if not images:
            self.texture = arcade.make_soft_square_texture(64, arcade.color.RED)
        else:
            self.textures = images
            self.texture = self.textures[0]
            
        self.center_x = x
        self.center_y = y
        self.frame_actuelle = 0
        self.temps_ecoule = 0

    def update_animation(self, delta_time):
        # On n'anime que si on a des textures
        if hasattr(self, 'textures') and self.textures:
            self.temps_ecoule += delta_time
            if self.temps_ecoule > 0.15:
                self.temps_ecoule = 0
                self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures)
                self.texture = self.textures[self.frame_actuelle]

# ==========================================
# CLASSE DU BOSS (Unique et plus gros)
# ==========================================
class LeBoss(arcade.Sprite):
    def __init__(self, images, x, y):
        super().__init__()
        # SECURITÉ : Bloc rouge foncé pour le Boss s'il n'y a pas d'image
        if not images:
            self.texture = arcade.make_soft_square_texture(120, arcade.color.DARK_RED)
        else:
            self.textures = images
            self.texture = self.textures[0]
            
        self.scale = 2.5
        self.center_x = x
        self.center_y = y
        self.vie = 500

# SECTION 1 : L ECRAN DE MENU (Inchangé)
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
        self.tiroir_fleur = None
        self.tiroir_murs = None
        self.tiroir_arriere = None
        self.tiroir_devant = None
        self.tiroir_boss = None
        self.tiroir_petits = None 
        
        self.fleur_perso = None
        self.oeil_qui_suit = arcade.camera.Camera2D()
        self.oeil_fixe = arcade.camera.Camera2D()
        
        self.vie = 100
        self.eau = 100 
        self.vitesse_dash = 0
        self.moteur_physique = None

    def setup(self):
        # 1. On prepare les tiroirs
        self.tiroir_fleur = arcade.SpriteList()
        self.tiroir_petits = arcade.SpriteList()
        self.tiroir_boss = arcade.SpriteList() # On initialise aussi le tiroir boss

        # 2. Perso
        self.fleur_perso = arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png", 0.5)
        self.fleur_perso.center_x = 200
        self.fleur_perso.center_y = 300
        self.tiroir_fleur.append(self.fleur_perso)

        # 3. Chargement Map (Inchangé)
        chemin_ma_map = os.path.join(DOSSIER_MAPS, "map.tmj")
        try:
            ma_map_tiled = arcade.load_tilemap(chemin_ma_map, scaling=2)
            self.tiroir_murs = ma_map_tiled.sprite_lists.get("hit-box")
            self.tiroir_arriere = ma_map_tiled.sprite_lists.get("base")
        except Exception as e:
            print(f"Erreur de chargement Map : {e}")

        # 4. Physique
        if self.tiroir_murs:
            self.moteur_physique = arcade.PhysicsEnginePlatformer(self.fleur_perso, gravity_constant=0.5, walls=self.tiroir_murs)

        # 5. SPAWN DU MOB ET DU BOSS (Haut à droite du joueur)
        x_haut_droite = self.fleur_perso.center_x + 150
        y_haut_droite = self.fleur_perso.center_y + 150
        
        dossier_mob = os.path.join(CHEMIN_BASE, "data", "maps", "mobtest")
        
        # --- TEST TEXTURES MOB ---
        textures_mob = []
        try:
            textures_mob = [
                arcade.load_texture(os.path.join(dossier_mob, "avancer (1).png")),
                arcade.load_texture(os.path.join(dossier_mob, "avancer (2).png"))
            ]
        except Exception as e:
            print(f"MOB: Images non trouvées ({e}). Bloc rouge activé.")

        # --- TEST TEXTURES BOSS ---
        textures_boss = []
        # Ici tu pourras ajouter le chemin vers les images du boss plus tard
        
        # Création
        mon_mob_test = EnnemiAnime(textures_mob, x_haut_droite, y_haut_droite)
        mon_boss_test = LeBoss(textures_boss, x_haut_droite + 200, y_haut_droite) # Un peu plus à droite
        
        self.tiroir_petits.append(mon_mob_test)
        self.tiroir_boss.append(mon_boss_test)

    def on_draw(self):
        self.clear()
        self.oeil_qui_suit.use()
        
        if self.tiroir_arriere: self.tiroir_arriere.draw()
        if self.tiroir_murs: self.tiroir_murs.draw()
        if self.tiroir_petits: self.tiroir_petits.draw()
        if self.tiroir_boss: self.tiroir_boss.draw() # On dessine le boss
        self.tiroir_fleur.draw()

        self.oeil_fixe.use()
        self.dessiner_hud()

    def dessiner_hud(self):
        arcade.draw_lrbt_rectangle_filled(20, 220, 680, 700, arcade.color.GRAY)
        arcade.draw_lrbt_rectangle_filled(20, 20 + (self.vie/100)*200, 680, 700, arcade.color.RED)
        arcade.draw_lrbt_rectangle_filled(20, 220, 650, 670, arcade.color.GRAY)
        arcade.draw_lrbt_rectangle_filled(20, 20 + (self.eau/100)*200, 650, 670, arcade.color.BLUE)

    def on_update(self, delta_time):
        if self.moteur_physique:
            self.moteur_physique.update()
        
        for ennemi in self.tiroir_petits:
            ennemi.update_animation(delta_time)

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