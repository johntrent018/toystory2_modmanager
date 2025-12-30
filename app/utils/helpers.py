## Importations de base
import sys, os

def resource_path(relative_path):

    # Obtient le chemin absolu d'une ressource, fonctionne en dev et dans l'exe
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller crée un dossier temporaire et stocke le chemin dans _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)