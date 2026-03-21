"""
BioAccess Secure - Client Desktop
Application d'authentification biométrique (visage + voix)

Point d'entrée de l'application
"""

import os
import sys
import logging
from pathlib import Path

# Ajouter le répertoire courant au PATH
sys.path.insert(0, str(Path(__file__).parent))

# Configuration du logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_dependencies():
    """Vérifier que toutes les dépendances sont installées"""
    required_packages = {
        'tkinter': 'tkinter',
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'requests': 'requests',
        'sounddevice': 'sounddevice',
        'soundfile': 'soundfile',
    }
    
    missing = []
    
    for import_name, pip_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pip_name)
    
    if missing:
        print("\n❌ Dépendances manquantes:")
        print(f"   {', '.join(missing)}")
        print("\nInstallation:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Fonction principale"""
    
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     🔐 BioAccess Secure - Client Desktop v1.0        ║
    ║     Authentification Biométrique (Visage + Voix)     ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Vérifier les dépendances
    print("🔍 Vérification des dépendances...")
    if not check_dependencies():
        return 1
    
    print("✅ Toutes les dépendances sont disponibles\n")
    
    # Importer et lancer l'application
    try:
        from ui.login_screen import LoginScreen
        import tkinter as tk
        
        logger.info("=" * 60)
        logger.info("Démarrage de BioAccess Secure Client")
        logger.info("=" * 60)
        
        print("🚀 Lancement de l'application...\n")
        
        root = tk.Tk()
        app = LoginScreen(root)
        
        logger.info("Interface lancée avec succès")
        
        root.mainloop()
        
        logger.info("Application fermée")
        return 0
    
    except Exception as e:
        logger.error(f"Erreur fatal: {str(e)}", exc_info=True)
        print(f"\n❌ Erreur: {str(e)}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
