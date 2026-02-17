# =================================================================
# PROJET : FLOÏOÏDE
# ÉQUIPE : Thomas (Moteur), Victor (Map), Laure (Interface), Corentin (Ennemis)
# =================================================================

import arcade
import os

# --- LES RÉGLAGES (Les Constantes) ---
# On utilise des majuscules pour les variables qui ne changent jamais.
# Cela permet de modifier la taille de la fenêtre partout d'un seul coup.
LARGEUR = 1280
HAUTEUR = 720
TITRE_JEU = "FLOÏOÏDE - Projet NSI 2026"

# =================================================================
# 1. L'ÉCRAN DE MENU (Laure)
# =================================================================
class MenuDepart(arcade.View):
    """ 
    Objet de type 'View' (Vue). 
    C'est une classe qui représente un écran spécifique du jeu.
    Ici, c'est l'écran d'accueil avant que le jeu ne commence.
    """
    
    def on_show_view(self):
        """ 
        'def' signifie 'définition'. C'est une fonction (ici une méthode).
        'on_show_view' s'exécute UNE SEULE FOIS au moment où l'écran s'affiche.
        On l'utilise pour régler la couleur de fond par exemple.
        """
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self):
        """ 
        'on_draw' s'exécute en boucle (60 fois par seconde).
        C'est ici qu'on met tout ce qui doit être dessiné à l'écran.
        """
        self.clear() # On efface l'image d'avant pour ne pas avoir de traces.
        
        # Le titre du jeu (Le nom du jeu)
        # anchor_x="center" permet de centrer le texte sur le point donné.
        arcade.draw_text(TITRE_JEU, LARGEUR/2, HAUTEUR*0.7, arcade.color.GREEN, 60, anchor_x="center")
        
        # Les instructions pour le joueur
        arcade.draw_text("Appuyez sur ENTRÉE pour Lancer", LARGEUR/2, HAUTEUR*0.5, arcade.color.WHITE, 20, anchor_x="center")
        arcade.draw_text("Appuyez sur H pour l'Aide", LARGEUR/2, HAUTEUR*0.4, arcade.color.WHITE, 20, anchor_x="center")

    def on_key_press(self, key, modifiers):
        """ 
        Cette méthode surveille le clavier. 
        'key' contient le code de la touche sur laquelle on a appuyé.
        """
        if key == arcade.key.ENTER:
            # On crée un nouvel OBJET de la classe MonJeu
            vue_jeu = MonJeu()
            # On lance sa configuration
            vue_jeu.setup()
            # On dit à la fenêtre de quitter le menu pour afficher le jeu
            self.window.show_view(vue_jeu)

# =================================================================
# 2. L'ÉCRAN DE JEU (Le Moteur principal)
# =================================================================
class MonJeu(arcade.View):
    """
    C'est le coeur du projet. Cette classe gère la physique de Thomas, 
    la map de Victor et les barres de Laure.
    """
    
    def __init__(self):
        """ 
        '__init__' est le CONSTRUCTEUR de la classe.
        Il prépare les variables (les attributs) dont le jeu aura besoin.
        On les met à 'None' (vide) au début.
        """
        super().__init__()
        self.liste_joueur = None # Tiroir pour ranger la fleur
        self.fleur = None        # L'objet qui représente le joueur
        
        # Les Caméras (Essentiel en NSI pour la gestion de l'affichage)
        self.camera_jeu = arcade.camera.Camera2D() # Bouge avec Thomas
        self.camera_hud = arcade.camera.Camera2D() # Reste fixe pour Laure
        
        # --- STATS DE LA FLEUR (Attributs de Laure) ---
        self.vie = 100
        self.eau = 100 # Sert aussi de barre d'énergie (stamina)

    def setup(self):
        """
        Prépare tous les éléments du niveau. 
        C'est ici que Victor chargera sa grande map TMX.
        """
        # SpriteList est une liste optimisée par Arcade pour dessiner vite.
        self.liste_joueur = arcade.SpriteList()
        
        # On crée le Sprite de la fleur (le personnage)
        # On utilise une image temporaire fournie par Arcade.
        self.fleur = arcade.Sprite(":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png", 0.5)
        self.fleur.center_x = 100
        self.fleur.center_y = 150
        self.liste_joueur.append(self.fleur) # On range la fleur dans son tiroir

    def on_draw(self):
        """ Dessine le monde et l'interface """
        self.clear()
        
        # 1. On utilise la caméra de jeu (Thomas)
        # Tout ce qui est dessiné après ici suivra le joueur.
        self.camera_jeu.use()
        self.liste_joueur.draw()

        # 2. On utilise la caméra HUD (Laure)
        # Tout ce qui est dessiné ici sera "collé" à l'écran.
        self.camera_hud.use()
        self.dessiner_hud()

    def dessiner_hud(self):
        """ 
        Méthode créée pour Laure pour organiser son code.
        Elle dessine les jauges de survie.
        """
        # --- LA BARRE DE VIE (ROUGE) ---
        # Un rectangle gris pour le fond de la barre
        arcade.draw_lrtb_rectangle_filled(20, 220, 700, 680, arcade.color.GRAY)
        # Calcul de la largeur : on fait un produit en croix.
        # (vie / 100) donne un nombre entre 0 et 1. On multiplie par 200 (largeur max).
        largeur_vie = (self.vie / 100) * 200
        arcade.draw_lrtb_rectangle_filled(20, 20 + largeur_vie, 700, 680, arcade.color.RED)
        arcade.draw_text("VIE", 230, 685, arcade.color.WHITE, 12)

        # --- LA BARRE D'EAU / ÉNERGIE (BLEUE) ---
        arcade.draw_lrtb_rectangle_filled(20, 220, 670, 650, arcade.color.GRAY)
        largeur_eau = (self.eau / 100) * 200
        arcade.draw_lrtb_rectangle_filled(20, 20 + largeur_eau, 670, 650, arcade.color.BLUE)
        arcade.draw_text("EAU", 230, 655, arcade.color.WHITE, 12)

    def on_update(self, delta_time):
        """ 
        'on_update' gère la logique (la réflexion du jeu).
        delta_time est le temps écoulé depuis la dernière image (environ 1/60e de sec).
        """
        # La caméra de jeu suit toujours les coordonnées X et Y de la fleur.
        self.camera_jeu.position = (self.fleur.center_x, self.fleur.center_y)
        
        # EXEMPLE DE LOGIQUE : L'eau baisse avec le temps
        if self.eau > 0:
            self.eau -= 0.05 # On retire un tout petit peu d'eau à chaque mise à jour

# =================================================================
# 3. LE LANCEMENT DU PROGRAMME
# =================================================================
def main():
    """ 
    C'est la fonction principale. C'est le point d'entrée du code.
    """
    # On crée l'objet 'Fenêtre'
    window = arcade.Window(LARGEUR, HAUTEUR, TITRE_JEU)
    
    # On crée l'objet 'Menu'
    menu = MenuDepart()
    
    # On dit à la fenêtre d'afficher le menu en premier
    window.show_view(menu)
    
    # On lance la boucle infinie du jeu
    arcade.run()

# Cette ligne vérifie si on a cliqué sur 'Play' dans l'éditeur de code.
if __name__ == "__main__":
    main()