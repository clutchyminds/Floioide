# Présentation du projet : FLOIOIDE

## 1. Présentation globale

**Naissance de l'idée** : Nous voulions créer un jeu vidéo 2D de type Metroidvania avec une thématique originale autour de la nature. L'idée était d'incarner une fleur qui explore un monde, affronte des ennemis et gère ses ressources vitales (eau, énergie).

**Problématique initiale** : Comment concevoir un jeu de plateforme complet en Python, avec un moteur physique, des animations, un système de combat et une boutique, en utilisant uniquement les compétences acquises en NSI ?

**Objectifs** :
- Proposer un gameplay fluide avec des mécaniques variées (dash, escalade, double saut, combat)
- Créer plusieurs biomes avec des ennemis spécifiques et un boss multi-phases
- Développer une interface utilisateur complète (HUD, boutique, inventaire, chat)

## 2. Organisation du travail

### Présentation de l'équipe

- **Laure** : Conception des entités (joueur, ennemis, PNJ), système d'inventaire et de charmes (`entities.py`, `interface.py`)
- **Thomas** : Moteur physique, gestion de la caméra, boucle de jeu principale (`main.py`, `constantes.py`)
- **Corentin** : Système de combat, gestion des collisions, projectiles (`logic.py`, `main.py`)
- **Victor** : Interface graphique (HUD, boutique, menu développeur), sons et cinématique d'intro (`interface.py`, `inputs.py`)

### Répartition des tâches

Chaque membre a contribué à la fois au code et à la documentation. Les tâches ont été réparties pour que chacun touche à un aspect technique du projet. La communication s'est faite via Discord avec des notifications automatiques à chaque push sur la forge.

### Temps passé sur le projet

Le projet a été développé sur plusieurs mois durant l'année scolaire 2025-2026, avec des séances en classe et du travail personnel.

## 3. Étapes du projet

1. **Conception** : Choix du thème (nature/fleur), découverte de la bibliothèque Arcade 3.0, création de la carte avec l'éditeur Tiled.
2. **Architecture** : Mise en place du système de "tiroirs" (dictionnaires de SpriteLists) pour organiser les objets du jeu (murs, ennemis, joueur, PNJ).
3. **Gameplay de base** : Implémentation des déplacements (ZQSD), du saut, du dash et de la gravité via le moteur physique d'Arcade.
4. **Combat et ennemis** : Création des mobs (forêt, désert, ville), du système d'attaque avec animation et du boss multi-phases (Boss Arbre, Ver de Terre).
5. **Interface et boutique** : Développement du HUD (coeurs, eau, énergie), de la boutique PNJ avec items consommables et charmes passifs.
6. **Cinématique et sons** : Création de l'intro narrative en 12 scènes avec texte défilant et musique de fond.
7. **Tests et débogage** : Utilisation du menu développeur secret (code Konami) pour modifier les statistiques en temps réel et tester les limites du jeu.

## 4. Validation de l'opérationnalité

**État d'avancement** : Le jeu est fonctionnel du menu principal jusqu'au combat contre le boss. Le joueur peut explorer la carte, combattre des ennemis, acheter des objets et utiliser des charmes.

**Vérification de l'absence de bugs** :
- Utilisation d'une classe `InterfaceDev` permettant de modifier en temps réel la vitesse, le saut, la taille et la vie du joueur
- Le système de collision utilise un ensemble `deja_touche` dans `logic.py` pour empêcher un projectile d'infliger des dégâts plusieurs fois par image
- Les scripts de lancement (`floioide.sh` et `floioide.bat`) créent automatiquement l'environnement virtuel et installent les dépendances

**Difficultés rencontrées et solutions** :
- La migration vers Arcade 3.0 a nécessité de réécrire le système de hitbox (passage à la classe `HitBox`)
- La gestion du miroir horizontal (flip) du joueur provoquait des retournements involontaires : résolu en séparant l'orientation de l'animation
- Le dash traversait les murs : résolu en ajoutant une vérification de collision après le déplacement

## 5. Ouverture

**Idées d'amélioration** :
- Ajouter un système de sauvegarde de la progression en format JSON
- Créer de nouveaux biomes et ennemis
- Ajouter un système de succès et de statistiques de fin de partie

**Analyse critique** :
- L'utilisation de la programmation orientée objet a permis une grande modularité (classes séparées pour le joueur, les ennemis, le boss, l'interface)
- Le système de "tiroirs" (dictionnaires de SpriteLists) est une solution élégante pour organiser les entités du jeu
- Le code pourrait être amélioré en séparant davantage la logique de jeu de l'affichage

**Compétences personnelles développées** :
- Maîtrise de la programmation orientée objet en Python
- Utilisation d'une bibliothèque graphique (Arcade 3.0)
- Travail collaboratif avec Git et la Forge
- Création de cartes avec l'éditeur Tiled
- Gestion de projet et répartition des tâches en équipe

**Démarche d'inclusion** : L'équipe est mixte (1 fille, 3 garçons). Chaque membre a eu un rôle technique concret dans le développement du jeu.

---

## Nature du code et usage de l'IA

### Degré de création originale

Le projet est une **création originale**. Le code du jeu a été écrit intégralement par les élèves. L'architecture du programme (système de tiroirs, classes d'entités, gestion des collisions) a été conçue par l'équipe.

### Sources externes citées

- **Arcade** (licence MIT) : bibliothèque Python pour le développement de jeux 2D
- **Tiled** (licence GPL) : éditeur de cartes utilisé pour créer les niveaux (format TMJ)
- Les assets graphiques (sprites, tuiles) ont été créés ou adaptés par l'équipe

### Utilisation de l'Intelligence Artificielle

L'IA (Claude Code) a été utilisée ponctuellement comme assistant de développement, sous la supervision de l'enseignant :

- Aide au débogage lors de la migration vers Arcade 3.0 (changements d'API)
- Conseils sur l'organisation du code en classes
- Aide à la rédaction de la documentation

L'utilisation a été **limitée et encadrée** : chaque suggestion a été relue, comprise et testée par les élèves avant d'être intégrée. Le code a été compris et expliqué par chaque membre de l'équipe.
