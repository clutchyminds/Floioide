# TODO - Corrections Floïoïde

Rédigé le 24/02/2026

## Bugs

- [ ] Corriger le chemin des sprites ennemis : `data/maps/mobtest/` -> `data/mobtest/` (main.py:126)
- [ ] Charger les textures du boss au lieu de laisser la liste vide (main.py:139-140)
- [ ] Corriger le chemin inexistant `data/images/fleur.png` dans entities.py:15 (chemin relatif + dossier absent)
- [ ] Corriger le dash pour qu'il aille dans la direction du joueur et pas toujours à droite (main.py:178)

## Nettoyage

- [ ] Supprimer ou intégrer `sources/interface.py` (doublon ancien de main.py)
- [ ] Supprimer ou compléter `sources/entities.py` et `sources/constantes.py` (jamais importés, code mort)
- [ ] Ajouter `__init__.py` dans `sources/` si le module doit être conservé
- [ ] Remplacer `draw_lrtb_rectangle_filled` par `draw_lrbt_rectangle_filled` dans interface.py (API dépréciée)
