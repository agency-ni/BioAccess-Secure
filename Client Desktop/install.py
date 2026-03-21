#!/usr/bin/env python3
"""
Script d'installation automatique pour BioAccess Secure Client
Crée l'environnement virtuel et installe les dépendances
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    """Afficher l'en-tête"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     🔐 BioAccess Secure - Installation Wizard          ║
    ║     Client Desktop v1.0                                ║
    ╚════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Vérifier la version de Python"""
    print("🔍 Vérification de Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ requis (vous avez {version.major}.{version.minor})")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def create_venv():
    """Créer l'environnement virtuel"""
    print("\n📦 Création de l'environnement virtuel...")
    
    venv_path = Path('venv')
    
    if venv_path.exists():
        print("   ⚠️  Environnement virtuel existant détecté")
        response = input("   Réinitialiser? (y/n) [n]: ").strip().lower()
        if response != 'y':
            print("   ✓ Utilisation de l'environnement existant")
            return True
        import shutil
        shutil.rmtree(venv_path)
    
    try:
        subprocess.check_call([sys.executable, '-m', 'venv', 'venv'])
        print("✅ Environnement virtuel créé")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def get_pip_command():
    """Déterminer la commande pip appropriée"""
    is_windows = platform.system() == 'Windows'
    
    if is_windows:
        venv_bin = Path('venv/Scripts')
        pip_cmd = str(venv_bin / 'pip')
        python_cmd = str(venv_bin / 'python')
    else:
        venv_bin = Path('venv/bin')
        pip_cmd = str(venv_bin / 'pip')
        python_cmd = str(venv_bin / 'python')
    
    return pip_cmd, python_cmd

def install_requirements():
    """Installer les dépendances"""
    print("\n📚 Installation des dépendances...")
    print("   (cela peut prendre 2-3 minutes...)\n")
    
    pip_cmd, _ = get_pip_command()
    
    try:
        # Mettre à jour pip
        print("   • Mise à jour de pip...", end=" ", flush=True)
        subprocess.check_call([pip_cmd, 'install', '--upgrade', 'pip'], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        print("✓")
        
        # Installer les requierements
        print("   • Installation des paquets...", end=" ", flush=True)
        subprocess.check_call([pip_cmd, 'install', '-r', 'requirements.txt'],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
        print("✓")
        
        print("✅ Dépendances installées avec succès")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de l'installation: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False

def create_env_file():
    """Créer le fichier .env"""
    print("\n⚙️  Configuration...")
    
    env_file = Path('.env')
    example_file = Path('.env.example')
    
    if env_file.exists():
        print("   ⚠️  Fichier .env existant détecté")
        response = input("   Réinitialiser? (y/n) [n]: ").strip().lower()
        if response != 'y':
            print("   ✓ Utilisation du fichier existant")
            return True
    
    if example_file.exists():
        try:
            with open(example_file, 'r') as f:
                content = f.read()
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ Fichier .env créé")
            print(f"   📝 Éditer .env pour configurer l'API")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    else:
        print("⚠️  Fichier .env.example non trouvé")
        return False

def create_logs_dir():
    """Créer le répertoire des logs"""
    print("\n📂 Création des répertoires...")
    
    logs_dir = Path('logs')
    temp_dir = Path('temp')
    
    try:
        logs_dir.mkdir(exist_ok=True)
        temp_dir.mkdir(exist_ok=True)
        print("✅ Répertoires créés")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_installation():
    """Tester l'installation"""
    print("\n🧪 Test de l'installation...")
    
    _, python_cmd = get_pip_command()
    
    # Test imports
    try:
        result = subprocess.run(
            [python_cmd, '-c', 
             'import cv2, sounddevice, requests, PIL; print("OK")'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and 'OK' in result.stdout:
            print("✅ Tous les modules importés avec succès")
            return True
        else:
            print(f"⚠️  Certains modules pourraient avoir un problème")
            print(f"   Output: {result.stderr}")
            return True  # Ne pas bloquer, car les dépendances optionnelles peuvent manquer
    
    except Exception as e:
        print(f"⚠️  Erreur lors du test: {e}")
        return True

def print_next_steps():
    """Afficher les prochaines étapes"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║                 ✅ Installation réussie!               ║
    ╚════════════════════════════════════════════════════════╝
    
    📝 Prochaines étapes:
    
    1️⃣  Éditer la configuration:
        • Ouvrir .env
        • Modifier API_BASE_URL si nécessaire
        • Vérifier les autres paramètres
    
    2️⃣  Démarrer le serveur backend (dans un autre terminal):
        cd BACKEND
        python run.py
    
    3️⃣  Lancer l'application:
        python main.py
    
    💡 Commandes utiles:
    
    • Tester l'API:
        python test_api.py
    
    • Voir les logs:
        tail -f logs/app.log  (Linux/Mac)
        Get-Content -Path logs/app.log -Wait  (PowerShell)
    
    📖 Documentation:
        • README.md - Documentation complète
        • QUICKSTART.md - Guide rapide
        • .env.example - Tous les paramètres disponibles
    
    🚀 C'est prêt! Bon test!
    """)

def main():
    """Fonction principale"""
    print_header()
    
    # Vérifier Python
    if not check_python_version():
        return 1
    
    # Créer venv
    if not create_venv():
        return 1
    
    # Installer dépendances
    if not install_requirements():
        print("\n⚠️  Erreur lors de l'installation des dépendances")
        print("   Réessayez avec: pip install -r requirements.txt")
        return 1
    
    # Créer fichier .env
    if not create_env_file():
        print("⚠️  Impossible de créer .env")
        print("   Vous pouvez le créer manuellement depuis .env.example")
    
    # Créer répertoires
    if not create_logs_dir():
        return 1
    
    # Tester
    test_installation()
    
    # Prochaines étapes
    print_next_steps()
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Installation annulée par l'utilisateur")
        sys.exit(1)
