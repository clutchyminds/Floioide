# PROJET : Floioide
# AUTEURS : Thomas, Victor, Laure, Corentin

import arcade
import os

# --- LES RÉGLAGES DU JEU ---
LARGEUR = 1280
HAUTEUR = 720
TITRE = "Floioide"

class MonJeu(arcade.Window):
    def __init__(self):
        # On crée la fenêtre du jeu
        super().__init__(LARGEUR, HAUTEUR, TITRE)
        
        # On force l'ordinateur à chercher les images dans le bon dossier
        # C'est obligatoire pour que le jeu marche sur tous les PC (Règlement Art 2.2.3)
        chemin_du_fichier = os.path.dirname(os.path.abspath(__file__))
        os.chdir(chemin_du_fichier)

        # On crée les "tiroirs" pour ranger nos objets
        self.liste_joueur = None  # Pour ranger la fleur
        self.liste_murs = None    # Pour ranger le sol et les murs
        
        # La variable qui contiendra notre personnage
        self.fleur = None
        
        # On crée deux caméras
        self.camera_jeu = None    # Celle qui suit la fleur (Thomas)
        self.camera_hud = None    # Celle qui reste fixe pour le score (Laure)

        # Le moteur qui gère la gravité et les chocs
        self.moteur_physique = None

    def setup(self):
        """ Cette partie prépare le jeu au début """
        
        # On initialise nos tiroirs (Listes de Sprites)
        self.liste_joueur = arcade.SpriteList()
        self.liste_murs = arcade.SpriteList()

        # On installe les caméras (Nouvelle version Arcade 3.0)
        self.camera_jeu = arcade.camera.Camera2D()
        self.camera_hud = arcade.camera.Camera2D()

        # --- CRÉATION DE LA FLEUR (Thomas) ---
        # On utilise une image de base fournie par Arcade pour tester
        self.fleur = arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png", 0.5)
        self.fleur.center_x = 100 # Position de départ à gauche
        self.fleur.center_y = 150 # Position de départ en hauteur
        self.liste_joueur.append(self.fleur)
        
        # --- CRÉATION DU SOL (Victor) ---
        # On crée une ligne de sol simple pour le moment
        for x in range(0, 2000, 64):
            mur = arcade.Sprite(":resources:images/tiles/grassMid.png", 0.5)
            mur.center_x = x
            mur.center_y = 32
            self.liste_murs.append(mur)

        # --- INSTALLATION DU MOTEUR (Thomas) ---
        # On dit au moteur : la fleur subit la gravité et s'arrête contre les murs
        self.moteur_physique = arcade.PhysicsEnginePlatformer(
            self.fleur, gravity_constant=0.5, walls=self.liste_murs
        )

    def on_draw(self):
        """ Cette partie dessine tout à l'écran (60 fois par seconde) """
        self.clear() # On efface l'écran avant de redessiner

        # 1. On active la caméra qui suit le joueur
        self.camera_jeu.use()
        self.liste_murs.draw()
        self.liste_joueur.draw()

        # 2. On active la caméra fixe pour dessiner l'interface (HUD)
        self.camera_hud.use()
        self.dessiner_interface()

    def dessiner_interface(self):
        """ La partie de Laure : l'affichage des textes """
        # On affiche un texte simple pour le moment
        arcade.draw_text("EAU : 100%", 20, 680, arcade.color.WHITE, 16)

    def on_update(self, delta_time):
        """ Cette partie gère la logique (mouvements, calculs) """
        
        # On fait bouger le moteur physique
        self.moteur_physique.update()

        # On dit à la caméra de se placer sur la fleur
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)

    def on_key_press(self, touche, modificateurs):
        """ Quand on appuie sur une touche """
        if touche == arcade.key.UP or touche == arcade.key.SPACE:
            # Si on peut sauter (qu'on touche le sol), on monte
            if self.moteur_physique.can_jump():
                self.fleur.change_y = 12
        elif touche == arcade.key.LEFT:
            self.fleur.change_x = -5 # On va à gauche
        elif touche == arcade.key.RIGHT:
            self.fleur.change_x = 5  # On va à droite

    def on_key_release(self, touche, modificateurs):
        """ Quand on relâche une touche """
        if touche == arcade.key.LEFT or touche == arcade.key.RIGHT:
            self.fleur.change_x = 0 # On s'arrête de marcher

def main():
    # Lancement du programme
    fenetre = MonJeu()
    fenetre.setup()
    arcade.run()

# Lancer le jeu
if __name__ == "__main__":
    main()