from math import dist
import random 
import os
import arcade
from sources.constantes import DOSSIER_DATA, VITESSE_MARCHE

class EntiteAnimee(arcade.Sprite):
    def __init__(self, x, y, taille=1.0):
        super().__init__()
        self.en_escalade = False
        self.center_x = x
        self.center_y = y
        self.en_escalade = False
        self.scale = taille
        self.textures = []
        self.frame_actuelle = 0
        self.temps_ecoule = 0
        self.vitesse_animation = 0.15
        self.timer_dash = 0  # Temps restant avant le prochain dash

    def update_animation(self, delta_time=1/60):
        if not self.textures:
            return
            
        self.temps_ecoule += delta_time
        if self.temps_ecoule > self.vitesse_animation:
            self.temps_ecoule = 0
            self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures)
            
            # 1. On récupère la texture normale
            nouvelle_texture = self.textures[self.frame_actuelle]
            
            # 2. On applique le flip si nécessaire
            # hasattr vérifie si la variable existe pour éviter les bugs avec PetitMob
            if hasattr(self, "flipped_horizontally") and self.flipped_horizontally:
                self.texture = nouvelle_texture.flip_left_right()
            else:
                self.texture = nouvelle_texture

class Joueur(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=0.4)
        self.en_attaque = False
        self.cote_attaque = 1  # 1 pour droite, -1 pour gauche

        self.monnaie = 100
        self.eau = 100       # De 0 à 100
        self.energie = 0     # Commence à 0, monte à 100
        self.timer_energie = 0

        self.en_escalade = False
        self.en_dash = False

        self.vie_max = 20
        self.vie = 20
        
        self.inventaire = [None] * 5  # 5 slots vides

        # 1. Chargement de l'image de base (Idle)
        # Chemin selon l'image : data/player/player.png
        self.tex_idle = arcade.load_texture(os.path.join(DOSSIER_DATA, "player", "player.png"))        
        # 2. Chargement des animations (Toutes dans data/player/mouvements)
        # Définir le chemin vers ton dossier regroupé
        chemin_mouvements = os.path.join(DOSSIER_DATA, "player", "mouvements")

        # Lister tous les fichiers présents dans ce dossier
        tous_les_fichiers = sorted(os.listdir(chemin_mouvements))

        # Fonction pour extraire les images selon le début de leur nom
        def charger_liste(prefixe):
            liste = []
            for f in tous_les_fichiers:
                if f.startswith(prefixe) and f.endswith(".png"):
                    liste.append(arcade.load_texture(os.path.join(chemin_mouvements, f)))
            return liste

        # Assigner les animations en fonction des noms visibles sur ta capture
        self.anims_marche = charger_liste("avancer")   # Charge avancer (1).png, etc.
        self.anims_dash = charger_liste("Dash")        # Charge Dash.png
        self.anims_escalade = charger_liste("grimper") # Charge grimper (1).png, etc.

        self.texture = self.tex_idle

        self.etat = "IDLE"
        self.textures_attaque = []
        # --- CHARGEMENT DES ATTAQUES ---
        self.textures_attaque = []
        chemin_attaque = os.path.join(DOSSIER_DATA, "player", "attaque")
        
        # Remplace "1, 6" selon le nombre de frames que tu as. 
        # (Ici ça chargera attaque1.png jusqu'à attaque5.png)
        for i in range(1, 13): 
            nom_fichier = f"attaque{i}.png" # <-- Mets le bon nom ici
            tex = arcade.load_texture(os.path.join(chemin_attaque, nom_fichier))
            self.textures_attaque.append(tex)

    def update_animation(self, delta_time=1/60):
        # --- 1. SÉCURITÉ : Si aucune texture n'est chargée, on arrête ---
        if self.etat == "ATTAQUE":
            textures_a_utiliser = self.textures_attaque
        elif self.en_dash:
            textures_a_utiliser = self.anims_dash
        elif self.en_escalade:
            textures_a_utiliser = self.anims_escalade
        elif abs(self.change_x) > 0.1:
            textures_a_utiliser = self.anims_marche
        else:
            # On utilise une liste contenant juste l'image IDLE
            textures_a_utiliser = [self.tex_idle]

        if not textures_a_utiliser:
            return

        # --- 2. GESTION DU TIMER ---
        self.temps_ecoule += delta_time
        vitesse = 0.05 if self.etat == "ATTAQUE" else self.vitesse_animation

        if self.temps_ecoule > vitesse:
            self.temps_ecoule = 0
            self.frame_actuelle += 1

            # --- 3. LOGIQUE SELON L'ÉTAT ---
            if self.etat == "ATTAQUE":
                if self.frame_actuelle >= len(self.textures_attaque):
                    self.frame_actuelle = 0
                    self.etat = "IDLE"  # On repasse en mode normal
                else:
                    self.texture = self.textures_attaque[self.frame_actuelle]
            else:
                # Animation normale (IDLE/MARCHE)
                self.frame_actuelle %= len(textures_a_utiliser)
                self.texture = textures_a_utiliser[self.frame_actuelle]

        # --- 4. ORIENTATION (Flip / Rotation) ---
        if self.etat == "ATTAQUE" and self.direction_attaque == "HAUT":
            self.angle = 90
        else:
            self.angle = 0
            if hasattr(self, "flipped_horizontally"):
                if self.flipped_horizontally:
                    self.width = -abs(self.width)
                else:
                    self.width = abs(self.width)
        if self.en_attaque:
            # On utilise tes images d'attaque (ex: attaque1, attaque2...)
            # Assure-toi d'avoir une liste self.textures_attaque chargée
            self.texture = self.textures_attaque[self.frame_actuelle % len(self.textures_attaque)]
        
        # Gestion du miroir (Flip) selon la souris
        if self.cote_attaque == -1:
            self.texture = self.texture.flip_left_right()

    def escalader(self, liste_murs, direction_x):
        # On vérifie s'il y a un mur juste à côté de nous dans la direction où on avance
        mur_touche = arcade.check_for_collision_with_list(self, liste_murs)
        
        if mur_touche and direction_x != 0:
            self.en_escalade = True
            self.change_y = VITESSE_MARCHE # On monte à la même vitesse qu'on marche
        else:
            self.en_escalade = False


class Boss(EntiteAnimee):
    def __init__(self, x, y):
        # On définit la taille désirée une seule fois ici (ex: 4.0)
        self.taille_fixe = 4.0 
        super().__init__(x, y, taille=self.taille_fixe)
        
        self.textures_attaque = []
        self.textures_pause = []
        
        d = os.path.join(DOSSIER_DATA, "boss", "test")
        
        if os.path.exists(d):
            fichiers = sorted(os.listdir(d))
            for f in fichiers:
                if f.startswith("attaque") and f.endswith(".png"):
                    self.textures_attaque.append(arcade.load_texture(os.path.join(d, f)))
                elif f.startswith("pause") and f.endswith(".png"):
                    self.textures_pause.append(arcade.load_texture(os.path.join(d, f)))

        self.etat = "ATTAQUE"
        self.vitesse_animation = 0.12
        self.timer_pause = 0
        self.frame_actuelle = 0
        self.cible = None 
        self.vie = 50  # Modifie selon la résistance voulue

        if self.textures_attaque:
            self.texture = self.textures_attaque[0]

    def update_animation(self, delta_time=1/60):
        self.temps_ecoule += delta_time
        
        # --- Gestion des textures ---
        if self.etat == "ATTAQUE" and self.textures_attaque:
            if self.temps_ecoule > self.vitesse_animation:
                self.temps_ecoule = 0
                self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_attaque)
                self.texture = self.textures_attaque[self.frame_actuelle]
                if self.frame_actuelle == 0:
                    self.etat = "PAUSE"
                    self.timer_pause = 0
        
        elif self.etat == "PAUSE" and self.textures_pause:
            self.timer_pause += delta_time
            if self.temps_ecoule > 0.3:
                self.temps_ecoule = 0
                self.frame_actuelle = (self.frame_actuelle + 1) % len(self.textures_pause)
                self.texture = self.textures_pause[self.frame_actuelle]
            if self.timer_pause >= 5.0:
                self.etat = "ATTAQUE"

        # --- GESTION DU REGARD (SANS TÊTE EN BAS) ---
        if self.cible:
            # On utilise self.taille_fixe pour rester cohérent
            if self.cible.center_x < self.center_x:
                # Si tes images regardent à GAUCHE par défaut :
                self.width = abs(self.width)  # Largeur normale
            else:
                # On force la largeur en négatif pour le miroir horizontal uniquement
                self.width = -abs(self.width) 
            
            # Note : On ne touche JAMAIS à self.height ou self.scale ici 
            # pour éviter que le boss ne se retrouve la tête en bas.

        def logique_ia(self, joueur):
            pass
class PetitMob(EntiteAnimee):
    def __init__(self, x, y):
        # On force la taille à 0.3 pour qu'ils ne soient pas géants
        super().__init__(x, y, taille=0.3)
        
        chemin_mobs = os.path.join(DOSSIER_DATA, "mobs", "sol")
        # Chargement des textures mob_sol.1.png à mob_sol.5.png
        for i in range(1, 6):
            tex = arcade.load_texture(os.path.join(chemin_mobs, f"mob_sol.{i}.png"))
            self.textures.append(tex)
        
        self.texture = self.textures[0]
        self.vitesse = 2
        self.points_de_vie = 3
        self.direction_balade = random.choice([-1, 1])
        self.timer_balade = 0

    def update_animation(self, delta_time=1/60):
        # Animation automatique des 5 frames
        super().update_animation(delta_time)

    def logique_ia(self, joueur):
        # On calcule la distance
        distance = arcade.get_distance_between_sprites(self, joueur)
        
        if distance < 400:
            if self.center_x < joueur.center_x:
                self.change_x = 2 # Marche à droite
            else:
                self.change_x = -2 # Marche à gauche
        else:
            self.change_x = 0 # S'arrête

class PNJ(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(center_x=x, center_y=y, scale=0.5)
        chemin_pnj = os.path.join(DOSSIER_DATA, "mobs", "PNJ")
        
        # Sécurité si les images n'existent pas encore
        try:
            self.tex1 = arcade.load_texture(os.path.join(chemin_pnj, "PNJ1.png"))
            self.tex2 = arcade.load_texture(os.path.join(chemin_pnj, "PNJ2.png"))
        except:
            self.tex1 = arcade.make_soft_square_texture(50, arcade.color.BLUE)
            self.tex2 = arcade.make_soft_square_texture(50, arcade.color.LIGHT_BLUE)

        self.texture = self.tex1
        self.timer_anim = 0
        self.est_survole = False

    def update_animation(self, delta_time=1/60):
        # 1. Animation (switch toutes les 0.5s)
        self.timer_anim += delta_time
        if self.timer_anim > 0.5:
            self.timer_anim = 0
            self.texture = self.tex2 if self.texture == self.tex1 else self.tex1

        # 2. Changement de couleur au survol
        if self.est_survole:
            self.color = arcade.color.YELLOW
        else:
            self.color = arcade.color.WHITE

    def draw(self, **kwargs):
        # 1. Dessiner le sprite normalement
        super().draw(**kwargs)
        
        # 2. Si survolé, on ajoute un contour blanc (Glow effect)
        if self.est_survole:
            # On dessine un rectangle vide autour du sprite
            # On utilise les dimensions du sprite
            arcade.draw_rect_outline(
                rect=self.rect,
                color=arcade.color.WHITE,
                border_width=3
            )

class EffetAttaque(arcade.Sprite):
    def __init__(self, x, y, direction, dossier_attaque):
        super().__init__()
        self.center_x = x + (40 * direction) # Décale l'attaque devant le joueur
        self.center_y = y
        self.scale = 1.0
        
        # Chargement des textures d'attaque
        self.textures = []
        for i in range(1, 6): # Suppose que tu as attaque1.png à attaque5.png
            try:
                tex = arcade.load_texture(os.path.join(dossier_attaque, f"attaque{i}.png"))
                if direction == -1:
                    tex = tex.flip_left_right()
                self.textures.append(tex)
            except:
                pass
        
        if self.textures:
            self.texture = self.textures[0]
        self.frame = 0
        self.timer = 0

    def update_animation(self, delta_time=1/60):
        self.timer += delta_time
        if self.timer > 0.05: # Vitesse de l'attaque
            self.timer = 0
            self.frame += 1
            if self.frame < len(self.textures):
                self.texture = self.textures[self.frame]
            else:
                self.remove_from_sprite_lists() # Détruit l'attaque quand l'anim est finie