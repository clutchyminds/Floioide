#Projet : Floioide
#Auteurs : Laure Ducournau, Victor Dauphin, Corentin Gelineau, Thomas Lewis

import os 


#si quelqu'un ne comprend pas le code (comme toi corentin)
#je fais éxpres de laisser des commentaires (et éxcusez moi pour les fautes d'orthographe)


#ici je vais crée les détails de la fenètre
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Floioide"

#ici sont les constantes pour les sprites
CHARACTER_SCALING = 1
TILE_SCALING = 0.5

'''
comme vue das le règlement il ne faut pas utiliser des chemins absolus ou relatifs
présent de base dans python car le code ne pourrait pas marche d'une machine a l'autre
alors on vas utiliser la bibliothèque os
'''
#chemins :

ASSETS_PATH = os.path.join("..", "data")
MAP_PATH = os.path.join(ASSETS_PATH, "maps", "map.tmj")