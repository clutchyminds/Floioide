import arcade
import os
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
        self.eau = 100
        self.en_escalade = False
        self.en_dash = False

        self.vie_max = 20
        self.vie = 20
        
        self.monnaie = 0
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
        chemin_attaque = os.path.join(DOSSIER_DATA, "player", "attaque")
        
        for i in range(16):
            nom_fichier = f"frame_{i:02d}_delay-0.1s.png"
            full_path = os.path.join(chemin_attaque, nom_fichier)
            if os.path.exists(full_path):
                self.textures_attaque.append(arcade.load_texture(full_path))
            else:
                print(f"Attention : fichier manquant {full_path}")

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

class PetitMob(EntiteAnimee):
    def __init__(self, x, y):
        super().__init__(x, y, taille=0.5)
        self.vitesse = 2
        # Utilise un carré rouge temporaire ou une image de mobtest
        self.texture = arcade.make_soft_square_texture(40, (255, 0, 0))

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