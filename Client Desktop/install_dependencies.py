"""
Installation des dépendances pour BioAccess Secure - Client Desktop
Installe les modules Python nécessaires
"""

import subprocess
import sys
import platform


def install_dependencies():
    """Installe toutes les dépendances requises"""
    
    print("\n" + "="*60)
    print("  📦 Installation des dépendances")
    print("  BioAccess Secure - Device Configuration")
    print("="*60 + "\n")
    
    # Packages à installer
    packages = [
        'opencv-python',
        'sounddevice',
        'soundfile',
        'scipy',
        'numpy'
    ]
    
    # Déterminer la commande Python
    python_cmd = sys.executable
    
    print(f"Python: {python_cmd}")
    print(f"Version: {platform.python_version()}")
    print(f"OS: {platform.system()}\n")
    
    # Mettre à jour pip
    print("🔄 Mise à jour de pip...")
    try:
        subprocess.check_call([python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'])
        print("✅ pip mis à jour\n")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Erreur lors de la mise à jour de pip: {e}")
        print("   Continuant l'installation...\n")
    
    # Installer les packages
    total_packages = len(packages)
    for i, package in enumerate(packages, 1):
        print(f"\n[{i}/{total_packages}] 📦 Installation de {package}...")
        
        try:
            subprocess.check_call([python_cmd, '-m', 'pip', 'install', package])
            print(f"✅ {package} installé")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'installation de {package}: {e}")
            return False
    
    # Vérifier l'installation
    print("\n" + "-"*60)
    print("🔍 Vérification de l'installation...")
    print("-"*60 + "\n")
    
    verification_code = """
import sys
modules_ok = True

try:
    import cv2
    print(f"✅ OpenCV {cv2.__version__}")
except ImportError:
    print("❌ OpenCV non installé")
    modules_ok = False

try:
    import sounddevice as sd
    print(f"✅ sounddevice {sd.__version__}")
except ImportError:
    print("❌ sounddevice non installé")
    modules_ok = False

try:
    import soundfile as sf
    print(f"✅ soundfile {sf.__version__}")
except ImportError:
    print("❌ soundfile non installé")
    modules_ok = False

try:
    import scipy
    print(f"✅ scipy {scipy.__version__}")
except ImportError:
    print("❌ scipy non installé")
    modules_ok = False

try:
    import numpy as np
    print(f"✅ numpy {np.__version__}")
except ImportError:
    print("❌ numpy non installé")
    modules_ok = False

sys.exit(0 if modules_ok else 1)
"""
    
    try:
        subprocess.check_call([python_cmd, '-c', verification_code])
    except subprocess.CalledProcessError:
        print("\n⚠️  Certains modules n'ont pas pu être vérifiés")
        return False
    
    print("\n" + "="*60)
    print("  ✅ Installation complète!")
    print("="*60 + "\n")
    
    print("📚 Prochaines étapes:\n")
    print("1. Créer le dossier logs (s'il n'existe pas):")
    print("   mkdir logs")
    print("\n2. Exécuter le diagnostic:")
    print("   python device_diagnostic.py")
    print("\n3. Configurer les permissions:")
    print("   python device_setup.py")
    print("\n4. Suivre les instructions à l'écran")
    
    return True


if __name__ == '__main__':
    try:
        success = install_dependencies()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Installation annulée par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)
