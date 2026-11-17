<h1>
  <img src="/assets/ts2_manager.png" alt="Icône" width="32" height="32" style="vertical-align: middle; margin-right: 10px;">
  Toy Story 2 PC - Mod Manager
</h1>

<img src="https://img.shields.io/badge/Version-1.5.4-blue" height="25">
<img src="https://img.shields.io/badge/License-GNU GPL v3-c00002?logo=gplv3&logoColor=ffffff" height="25">
<br>
<img src="https://img.shields.io/badge/Special thanks-Toy Story 2 Speedrunning and Modding Community-5865f2?logo=discord&logoColor=fff" href="https://discord.gg/qfUHgT73FS" height="25">


## About

This mod manager is a simple Python Tkinter interface made to enable and disable easily and quickly mods for the video game "Toy Story 2 : Buzz Lightyear to the Rescue!". This mod manager works with any PC version of the game (standalone or installed on disc).

## ⚠️ Warning

As regards level mods, this app is not designed to create mods but to manage them easily. To create level mods (modified NGN files), you will first need to use the [ToyTwoToolbox app](https://github.com/EpicMinecartz/ToyTwoToolbox/releases). This app is therefore not intended to replace the ToyTwoToolbox app at this stage.

## Features

- Actually implemented :
  - Package mods as .zip archives to enable or disable them quickly in-game (the game automatically keeps a backup of the original files in the `mods/_vanilla` folder that it restores when you stop a mod);
  - Import and export packaged mods ;
  - Edit an existing mod ;
  - Reorder mods using drag and drop;
  - Search for a mod using filters such as its name (by default), its author (by typing “by:author-name”) or its version (by typing “version:1.0.0”);
  - Choose the interface language (instant refresh, see the [language section](#language) below) ;
  - Translate 
- Currently in development :
  - Smart conflict manager for mods: if two mods affect the same textures in the same places, choose which part of which mod to keep on each texture. At the moment, as I am still learning how to reverse-engineer level files and manipulate them in Python, the conflict manager does not yet support conflicts involving 3D models and area portals. These data will therefore be overwritten when a new mod is activated ;

## What can be modified without using ToyTwoToolbox?

- There are resources – other than the levels linked to NGN files – that can be modified very easily: music;
 sound effects (in .wav format) and cutscenes. Simply replace the original file (make a backup first) with the modified file, which must have the same name in order to replace it;
- As for cutscenes, these are simply MPG videos which – for some unknown reason, but probably to obfuscate things on the part of the game’s developers – have a .dll file extension; you simply need to rename this to .mpg to open the cutscene in any video player. So, in theory, placing an MPG video (with the same name as an in-game cutscene) with the file extension renamed to .dll will replace the cutscene;
- However, **you don’t need to bother with these technical steps**: the mod manager can do this for you automatically when you create or edit a mod. All you need to do is import the resources into the relevant sub-tab.

## Launch the app

#### Run (in development)
```
pip install -r requirements.txt
python main.py
```
Enter the game’s installation folder (the one containing `data`) in the ‘Settings’ tab.
No original game files need to be provided: the app saves them itself (see below).
The `mods` folder must remain alongside the application. If it does not exist, it will be created as soon as a mod is created or imported.

#### Build the executable
```
pyinstaller --onefile --windowed --name "ToyStory2_ModManager" --icon "assets/ts2_manager.ico" --add-data "app;app" --add-data "assets;assets" --add-data "lang;lang" main.py
```

This command allows you to generate a ready-to-use .exe application that contains all the necessary files and dependencies. In future, the executable application will be available to download from a ‘Releases’ page on GitHub.

The executable application will be generated in a `dist` folder, and the `preferences.json` file and the `mods` folder will be created alongside the application. This JSON file and this folder must remain at the same level as the executable application for it to work correctly. Although the folder in which these three items are located is not important (as the application’s settings tab asks you to specify the path to the game’s installation folder), I recommend placing them in a `modmanager` folder within the game’s installation folder, alongside the game files and folders.


## Language

#### Interface's language

You can switch the interface's language by going in the settings tab and choosing your language from the language option's dropdown list. The language shift is instant and doesn't need to restart the app. The supported language (for now 😉) are French and English. 

The language setting in this application is designed with one community objective in mind : make it as easy as possible to implement a new language. This means that the only required thing to get this app to be translated into a new language is a JSON copy of the "en_GB.json" file located in the "lang" folder and renamed as "**xx_YY.json**", according to the international norm [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166) (xx = language code ; YY = country code).

Then you only need to translated all the strings it contains. Really, that's all it takes because the whole application has a language manager that will go search the text strings directly from these languages JSON files.

#### Adding a language to your mods

If you’d like to make it easier for players who don’t speak your language to use your mod, you can translate your mod into another language (from those supported by the app) directly via the interface.

In the top right-hand corner of the ‘Create a mod’ tab (even when editing a mod), there is a drop-down list of the languages supported by the app. If you select a language, you will be able to enter the mod’s details as they will appear in that language.

The information that can be translated includes the mod’s name (compulsory), the description and the warning message (both optional).

If the mod creator has not provided a translation in the language you have selected in the settings, the mod will be displayed in English by default. However, if the mod does not have an English translation, it will be displayed in the language in which it was created.

## Format of a mod archive

```
<name>_<author>.zip                       (name = slug of the name in the default language)
├── mod.json                              Contains the mod’s data
├── i18n/fr_FR.json                       Mod data available in the language of the JSON file (here, French)
├── images/picture.jpg/.png/.gif/.webp    Images supplied with the mod (supported formats: JPG/PNG/GIF/WEBP)
├── images/_logo.png                      A special name reserved for the mod’s icon (optional) which appears next to its name.
└── levels/level11.ngn                    The modified levels folder and the associated levels it contains (in this case, the NGN file for level 11, ‘Al’s Penthouse’);
```

The display order of mods is specified in `mods/mod_order.json`, whilst the active mods are listed in `mods/active_mods.json`.