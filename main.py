# Importations de composants
from app.core.preferences import Preferences
from app.core.game_path import GamePath_Manager
from app.i18n.manager import LanguageManager
from app.ui.app import App
# Importations tierces
from app.utils.helpers import resource_path
# import pprint

# Définition de la langue par défaut
DEFAULT_LANG = "en-GB"

# Boucle principale de l'application
if __name__ == "__main__":

    # On initialise le contrôleur des préférences
    prefs = Preferences()

    # On initialise le contrôleur des langues
    lang_manager = LanguageManager(
        locales_path=resource_path("app/i18n/locales"),
        default_lang=DEFAULT_LANG
    )

    # On récupère la langue enregistrée dans les préférences
    saved_lang = prefs.get("language")

    # Si la langue enregistrée dans les préférences existe bien en tant que fichier xx-YY.json
    # dans le dossier i18n/locales, alors on en fait la langue à utiliser. Sinon, on utilise la
    # langue par défaut (prise en charge d'une potentielle faille : non-existence d'un fichier de langue).
    if saved_lang in lang_manager.available_languages():
        lang_manager.set_language(saved_lang)
    else:
        lang_manager.set_language(DEFAULT_LANG)

    # On initialise le contrôleur du chemin du jeu
    game_path_manager = GamePath_Manager(prefs)

    # On lance l'application en boucle
    app = App(lang_manager, prefs, game_path_manager)
    app.mainloop()
