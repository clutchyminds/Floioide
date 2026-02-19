# =================================================================
# PROJET : FLOÏOÏDE
# L'équipe : Thomas, Victor, Laure et Corentin
# =================================================================

import arcade
import os

# --- LES RÉGLAGES (Pour ne pas s'embêter plus tard) ---
FENETRE_LARGEUR = 1280
FENETRE_HAUTEUR = 720
NOM_DU_JEU = "FLOÏOÏDE"

# =================================================================
# 1. L'ÉCRAN D'ACCUEIL (La partie de Laure)
# =================================================================
class EcranMenu(arcade.View):
    """ 
    C'est comme la première diapo d'un exposé. 
    Elle sert juste à afficher le titre et attendre qu'on appuie sur Start.
    """
    
    def on_show_view(self):
        # On choisit une couleur de fond (ici un gris-bleu foncé)
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        # Cette fonction dessine ce qu'on voit à l'écran
        self.clear() # On nettoie l'écran
        
        # On écrit le titre au milieu
        arcade.draw_text(NOM_DU_JEU, FENETRE_LARGEUR/2, 500, arcade.color.GREEN, 80, anchor_x="center")
        
        # On écrit les instructions pour les joueurs
        arcade.draw_text("Appuie sur ENTRÉE pour jouer", FENETRE_LARGEUR/2, 350, arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text("Appuie sur H pour l'Aide", FENETRE_LARGEUR/2, 280, arcade.color.WHITE, 20, anchor_x="center")

    def on_key_press(self, touche, modificateurs):
        # Si le joueur appuie sur la touche ENTRÉE
        if touche == arcade.key.ENTER:
            # On prépare le "vrai" jeu
            le_jeu = MonJeu()
            le_jeu.setup() # On lance l'installation des objets
            # On change de "diapo" pour afficher le jeu
            self.window.show_view(le_jeu)

# =================================================================
# 2. LE COEUR DU JEU (Thomas, Laure, Victor, Corentin)
# =================================================================
class MonJeu(arcade.View):
    """
    C'est ici que tout se passe : les mouvements, les barres de vie, etc.
    """
    
    def __init__(self):
        # C'est la liste de préparation des ingrédients du jeu
        super().__init__()
        
        # On crée des "tiroirs" vides pour ranger nos trucs plus tard
        self.tiroir_fleur = None  # Pour ranger notre personnage
        self.fleur_perso = None   # Pour créer notre fleur
        
        # On crée deux caméras (comme des yeux)
        self.oeil_qui_suit = arcade.camera.Camera2D() # Suivra la fleur
        self.oeil_fixe = arcade.camera.Camera2D()     # Ne bougera jamais (pour Laure)
        
        # --- LES STATS (Pour Laure) ---
        self.vie = 100
        self.eau = 100 
        
        # --- LE DASH (Pour Thomas) ---
        self.vitesse_dash = 0  # Au début, on ne dashe pas

    def setup(self):
        """ Ici on installe les meubles dans la chambre (on crée les objets) """
        
        # On active nos tiroirs
        self.tiroir_fleur = arcade.SpriteList()
        
        # On crée la fleur (On prend une image de test pour l'instant)
        self.fleur_perso = arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png", 0.5)
        self.fleur_perso.center_x = 200 # Position de départ à gauche
        self.fleur_perso.center_y = 300 # Position de départ en hauteur
        
        # On range la fleur dans son tiroir
        self.tiroir_fleur.append(self.fleur_perso)

    def on_draw(self):
        """ On dessine tout ce qui se passe dans le jeu """
        self.clear() # On efface tout pour redessiner proprement
        
        # 1. On utilise l'oeil qui suit le joueur (Thomas)
        self.oeil_qui_suit.use()
        self.tiroir_fleur.draw() # On dessine tout ce qu'il y a dans le tiroir fleur

        # 2. On utilise l'oeil fixe pour l'interface (Laure)
        self.oeil_fixe.use()
        self.dessiner_barres_de_vie()

    def dessiner_barres_de_vie(self):
        """ La partie de Laure : dessiner les jauges en haut à gauche """
        
        # BARRE DE VIE (En rouge)
        # Un rectangle gris dessous (le fond vide)
        arcade.draw_lrtb_rectangle_filled(20, 220, 700, 680, arcade.color.GRAY)
        # La barre rouge qui change de taille selon la vie
        taille_rouge = (self.vie / 100) * 200
        arcade.draw_lrtb_rectangle_filled(20, 20 + taille_rouge, 700, 680, arcade.color.RED)
        
        # BARRE D'EAU (En bleu)
        # Un rectangle gris dessous
        arcade.draw_lrtb_rectangle_filled(20, 220, 670, 650, arcade.color.GRAY)
        # La barre bleue qui change de taille selon l'eau
        taille_bleue = (self.eau / 100) * 200
        arcade.draw_lrtb_rectangle_filled(20, 20 + taille_bleue, 670, 650, arcade.color.BLUE)

    def on_update(self, delta_time):
        """ C'est le cerveau du jeu. Il calcule tout 60 fois par seconde. """
        
        # On dit à l'oeil de toujours regarder la fleur
        self.oeil_qui_suit.position = (self.fleur_perso.center_x, self.fleur_perso.center_y)
        
        # --- LOGIQUE DU DASH (Thomas) ---
        # Si la vitesse de dash est active, on fait avancer la fleur super vite
        if self.vitesse_dash > 0:
            self.fleur_perso.center_x += self.vitesse_dash
            self.vitesse_dash -= 1 # On freine petit à petit pour que ça s'arrête
        
        # --- LOGIQUE DE L'EAU (Laure) ---
        if self.eau > 0:
            self.eau -= 0.05 # L'eau s'évapore tout doucement

    def on_key_press(self, touche, modificateurs):
        """ Quand on appuie sur une touche du clavier """
        
        # Marcher à gauche ou à droite
        if touche == arcade.key.LEFT:
            self.fleur_perso.change_x = -5
        elif touche == arcade.key.RIGHT:
            self.fleur_perso.change_x = 5
            
        # LE DASH (Thomas)
        # Si on appuie sur SHIFT (la flèche en haut au dessus de CTRL)
        if touche == arcade.key.LSHIFT:
            # On vérifie si on a assez d'eau (énergie) pour dasher
            if self.eau >= 20:
                self.vitesse_dash = 20 # On donne un gros coup de boost
                self.eau -= 20         # On consomme de l'eau (énergie)

    def on_key_release(self, touche, modificateurs):
        """ Quand on lâche la touche, on arrête de marcher """
        if touche == arcade.key.LEFT or touche == arcade.key.RIGHT:
            self.fleur_perso.change_x = 0

# =================================================================
# 3. LE BOUTON "ALLUMER"
# =================================================================
def main():
    # On crée la fenêtre de Windows
    fenetre_principale = arcade.Window(FENETRE_LARGEUR, FENETRE_HAUTEUR, NOM_DU_JEU)
    
    # On prépare le menu
    menu = EcranMenu()
    
    # On dit à la fenêtre : "Affiche le menu d'abord !"
    fenetre_principale.show_view(menu)
    
    # On lance la machine
    arcade.run()

# On lance le code
if __name__ == "__main__":
    main()