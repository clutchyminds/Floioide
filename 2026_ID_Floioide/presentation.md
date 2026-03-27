Commandes :
- Déplacements : Z (Saut), Q (Gauche), S (Bas), D (Droite)

- Dash : Maj (Shift)

- Attaque : Clic Gauche

- Interaction Shop : touche les PNJ marchands.

Structure du Projet
sources/ : Code source (Logique, Entités, Interface).

data/ : Assets graphiques et cartes (Tiled).

requirements.txt : Liste des dépendances.

floioide.bat / floioide.sh : Scripts de déploiement.

# Présentation du projet : FLOIOIDE

## Présentation globale
- Naissance de l’idée : Créer un jeu style métroidevanilla avec une thématique florale où la survie dépend de la gestion de ressources vitales (eau/énergie).
- Problématique : Comment structurer un moteur de jeu modulaire en Python capable de gérer des comportements d'IA complexes et une boutique dynamique ?
- Objectifs : Proposer un gameplay nerveux (dash, tirs paraboliques) et une architecture de code robuste.

## Présentation de l'équipe
- Membre 1 : Gestion du moteur physique, des caméras et de la boucle de rendu (`main.py`, `constantes.py`).
- Membre 2 : Développement des entités (Joueur, Mobs) et du système de phases du Boss Arbre (`entities.py`).
- Membre 3 : Interface utilisateur (HUD), système d'inventaire à 4 slots et gestion des collisions (`interface.py`, `logic.py`).

## Étapes du projet
1.  Architecture : Mise en place du système de "tiroirs" (dictionnaires de SpriteLists) pour optimiser le rendu.
2.  Gameplay : Implémentation du moteur de mouvement et du combat 
3.  Contenu : Création des 3 biomes et du système de shop pour les "charmes".
4.  Déploiement : Création des scripts `.bat` et `.sh` pour garantir la portabilité.

## Validation de l’opérationnalité
- État d’avancement : Le jeu est complet, du menu principal au combat contre les Boss.
- Débogage : Utilisation d'une classe `InterfaceDev` permettant de modifier en temps réel la vitesse, le saut et l'échelle (scale) du joueur pour tester les limites du moteur.
- Difficulté résolue : Gestion des collisions multiples évitée grâce à un set `deja_touche` dans `logic.py`, empêchant un projectile d'infliger des dégâts plusieurs fois par seconde.

## Ouverture
- Analyse critique : L'utilisation de la POO a permis une grande flexibilité. Une amélioration possible serait l'ajout d'une sauvegarde de la progression en format JSON.
- Compétences développées : Maîtrise de la POO, gestion de projet collaborative, et automatisation système (Shell/Batch).