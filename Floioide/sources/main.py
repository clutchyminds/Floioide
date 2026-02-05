#Projet : Floioide
#Auteurs : Laure Ducournau, Victor Dauphin, Corentin Gelineau, Thomas Lewis

import arcade
from settings import * #j'importe les constantes de settings.py

class Floioide(arcade.Window):
    """
    classe principale du jeu
    """
    def __init__(self):

        #ici j'appel du constructeur de la classe parente (arcade.Window)
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        #je définis le chemin du dossier data pour les ressources
        arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

        #ca ce sont les variables pour les listes de sprites (murs, objets, joueur)
        self.scene = None
    
    def setup(self):
        
        #je vais utiliser cette méthode pour configurer le jeu elle sera appelé pour redémarrer le jeu

        #je crée une scène vide
        self.scene = arcade.Scene() 
    
    def on_draw(self):
        #et la c'est le rendu de l'écran
        self.clear()
        #la scene sera dessiner ici
        self.scene.draw()

def main():
    #et enfin la fonction main pour lancer le jeu qui est la fonction principale
    window = Floioide()
    window
    arcade.run()

if __name__ == "__main__":
    main()