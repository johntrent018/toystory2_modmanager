# Gestionnaire de mods – Toy Story 2 PC (prototype)

## Lancer
```
pip install -r requirements.txt
python main.py
```
Renseigner le dossier d'installation du jeu (celui qui contient `data`) dans l'onglet « Paramètres ».
Aucun fichier d'origine du jeu n'est à fournir : l'appli les sauvegarde elle-même (voir ci-dessous).
Le dossier `mods` doit rester à côté de l'application.

## Structure (MVC + Observer)
```
main.py                      assemblage des composants
app/event_bus.py             Observer/pubsub (+ noms des événements)
app/game_path_manager.py     GamePath_Manager
app/language_manager.py      LanguageManager (clés en dot-notation)
app/preferences.py           Preferences
app/app_paths.py             resource_path / dossier de l'appli
app/models/                  logique métier (aucun import Tkinter)
app/controllers/             un contrôleur par onglet
app/views/                   widgets Tkinter uniquement (icons.py : icônes dessinées avec Pillow)
assets/cursors/              curseurs main ouverte / poing fermé (.cur)
lang/<code>.json              traductions de l'interface (fr_FR.json, en_UK.json)
```

## Langues
- Langues fournies pour l'instant : `fr_FR` et `en_GB` (les autres seront ajoutées en une fois quand l'appli sera terminée).
- **Ajouter une langue** : déposer `lang/<code>.json` (copie traduite de `en_GB.json`, avec
  `"_meta": {"language_name": "…"}`). Elle apparaît seule dans Paramètres et dans « Créer un mod ».
  Une clé manquante retombe sur l'anglais (en_GB).
- Codes : langue ISO 639 + pays ISO 3166 (`fr_FR`, `en_GB`) ou région UN M.49 (`es_419`). Ancien code `en_UK` accepté (lu comme `en_GB`).
- Langue par défaut avant tout choix : anglais. Le changement dans Paramètres est appliqué immédiatement ;
  c'est aussi la langue par défaut des nouveaux mods.
- Affichage d'un mod : langue de l'interface → autres variantes de la même langue → anglais → langue par défaut du mod
  (champ par champ).

## Ressources du jeu et sauvegardes (`mods/_vanilla`)
- `assets/game_resources.json` relie chaque nom de l'interface (niveau 3, musique du menu…) au fichier du jeu à
  remplacer. Les objets imbriqués forment les dossiers ; les textes sont les chemins (relatifs à la racine du jeu).
  Version 1.5.4 : l'interface gère les catégories `levels` (Niveaux) et `screens` (Écrans) ; les autres onglets de
  « Ressources modifiées » (Musiques, Effets sonores, Cinématiques) sont des emplacements « bientôt disponible ».
  Le fichier d'un mod doit avoir l'extension du fichier du jeu remplacé (.ngn, mais .bmp pour `intro_choose_resolution`).
- **Activation** d'un mod : l'original du fichier remplacé est copié dans `mods/_vanilla/<catégories>/<clé>.<ext>`
  (ex. `levels/3.ngn`, `bgm/others/menus.wav`), sauf si cette sauvegarde existe déjà (elle n'est jamais écrasée).
  **Désactivation** : la sauvegarde est recopiée dans le jeu ; elle est conservée pour la prochaine activation.
- Les copies se font en deux temps (fichiers temporaires puis renommage) et en flux : un échec en cours de route
  laisse le jeu intact, et la mémoire reste faible même pour de gros fichiers.
- Anciennes versions : les NGN à plat `mods/_vanilla/levelN.ngn` sont rangés automatiquement dans `levels/N.ngn`.

## Icône de l'application
Déposer `assets/ts2_manager.ico` (Windows ; plusieurs tailles dans le fichier) et/ou `assets/ts2_manager.png`.
Absente ou illisible : la plume Tk par défaut est conservée. Pour l'icône du .exe : `pyinstaller … --icon assets/ts2_manager.ico`.

## À personnaliser
- `app/app_info.py` : nom de l'auteur, pseudo, dépôt GitHub, invitation Discord (onglet « À propos »).
- `lang/*.json`, clés `help.*` : contenu de l'onglet « Aide ».

## Format d'une archive de mod
```
<nom>_<auteur>.zip            (nom = slug du nom dans la langue par défaut)
├── mod.json                  schema_version, default_language, author, version?, images[] (ordre d'affichage), logo?, levels{"N": "levels/levelN.ngn"}
├── i18n/fr_FR.json           {"name", "description", "warning"} dans chaque langue renseignée
├── i18n/en_GB.json
├── images/<noms d'origine>   ordre = celui de mod.json ; collision de nom → "nom (1).png"
├── images/_logo.png          icône carrée 256x256 (facultative) ; une image nommée _logo.png devient "_logo (1).png"
├── levels/level<N>.ngn
└── screens/<clé>.ngn|.bmp    (et plus tard bgm/…, sfx/…, cutscenes/… ; listés dans "resources" de mod.json)
```
Les anciens mods (v1 sans `i18n`, ou images `01.png`…) restent lisibles et passent au nouveau format à leur première modification.

L'ordre d'affichage des mods (glisser-déposer) est dans `mods/mod_order.json`, les mods actifs dans `mods/active_mods.json`.

## Compilation PyInstaller
```
pyinstaller --noconsole --onefile --add-data "lang;lang" --add-data "assets;assets" main.py
```
(`;` est le séparateur Windows). `assets/` contient les curseurs « main ouverte / poing fermé » (`.cur`, Windows).
Si les curseurs « main » ne se chargent pas, la raison est écrite dans la console (curseur de secours : rose des vents).
`mods/` et `preferences.json` sont créés à côté de l'exe.
