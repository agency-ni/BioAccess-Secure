#!/usr/bin/env python3
"""
🚀 SCRIPT D'INSTALLATION UNIVERSEL - BioAccess Secure
Détecte automatiquement l'OS et installe tout ce qui est nécessaire
Compatible: Windows, Linux, macOS
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path


class UniversalInstaller:
    """Installateur universel cross-platform"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.python_cmd = sys.executable
        self.project_root = Path(__file__).parent.absolute()
        self.logs_dir = self.project_root / 'logs'
    
    def print_banner(self):
        """Affiche l'en-tête"""
        print("\n" + "="*70)
        print("  🚀 INSTALLATION - BioAccess Secure")
        print("  Gestion des Permissions et Diagnostic des Périphériques")
        print("="*70)
        print()
        print(f"  🖥️  Système detected: {self.os_type}")
        print(f"  🐍 Python: {platform.python_version()}")
        print(f"  📁 Dossier installation: {self.project_root}")
        print()
    
    def create_logs_directory(self):
        """Crée le répertoire logs s'il n'existe pas"""
        try:
            self.logs_dir.mkdir(exist_ok=True)
            print("✅ Répertoire 'logs' créé/vérifié")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def update_pip(self):
        """Met à jour pip"""
        print("\n📦 Mise à jour de pip...")
        try:
            subprocess.check_call(
                [self.python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✅ pip mis à jour")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  Impossible de mettre à jour pip (continuant...)")
            return True  # Non-bloquant
    
    def install_packages(self):
        """Installe les packages Python nécessaires"""
        packages = [
            ('opencv-python', 'OpenCV'),
            ('sounddevice', 'sounddevice'),
            ('soundfile', 'soundfile'),
            ('scipy', 'scipy'),
            ('numpy', 'numpy'),
        ]
        
        print("\n📦 Installation des modules Python...")
        
        total = len(packages)
        for i, (package_name, display_name) in enumerate(packages, 1):
            print(f"\n[{i}/{total}] Installation de {display_name}...", end=' ')
            
            try:
                subprocess.check_call(
                    [self.python_cmd, '-m', 'pip', 'install', package_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print("✅")
            except subprocess.CalledProcessError as e:
                print(f"❌")
                print(f"    Erreur: {e}")
                return False
        
        return True
    
    def setup_linux_permissions(self):
        """Configure les permissions Linux"""
        print("\n🔐 Configuration des permissions Linux...")
        
        username = os.environ.get('USER', 'unknown')
        print(f"   Utilisateur: {username}")
        
        try:
            # Vérifier si on est root
            if os.geteuid() != 0:
                print("\n   ⚠️  Cette étape nécessite les droits administrateur")
                print(f"   Directives:\n")
                print(f"   1. Ouvrir un terminal")
                print(f"   2. Exécuter:")
                print(f"      sudo usermod -a -G video {username}")
                print(f"      sudo usermod -a -G audio {username}")
                print(f"   3. Se reconnecter à la session")
                
                response = input("\n   ✓ Avez-vous exécuté les commandes? (oui/non): ").lower()
                return response in ['oui', 'o', 'yes', 'y']
            else:
                # Si on est root, le faire automatiquement
                subprocess.check_call(['usermod', '-a', '-G', 'video', username])
                subprocess.check_call(['usermod', '-a', '-G', 'audio', username])
                print("✅ Groupes configurés")
                return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def setup_windows_permissions(self):
        """Instructions pour Windows"""
        print("\n🔐 Configuration des permissions Windows...")
        print("\n   Instructions manuelles (les paramètres sont fermés):\n")
        print("   1. Appuyez sur WIN + I pour ouvrir Paramètres")
        print("   2. Allez à: Confidentialité et sécurité > Caméra")
        print("   3. S'assurer que 'Accès à la caméra' est ACTIVÉ")
        print("   4. Vérifier que l'application est autorisée")
        print("   5. Répéter pour: Confidentialité... > Microphone\n")
        
        response = input("   ✓ Avez-vous configuré les permissions? (oui/non): ").lower()
        return response in ['oui', 'o', 'yes', 'y']
    
    def setup_macos_permissions(self):
        """Instructions pour macOS"""
        print("\n🔐 Configuration des permissions macOS...")
        print("\n   Instructions:\n")
        print("   1. L'application demandera accès à la caméra/microphone")
        print("   2. Cliquez sur 'Autoriser' ou 'OK'")
        print("   3. Si ne demande pas, allez à:")
        print("      Sécurité & Confidentialité > Caméra/Microphone\n")
        
        response = input("   ✓ Compris? (oui/non): ").lower()
        return response in ['oui', 'o', 'yes', 'y']
    
    def verify_installation(self):
        """Vérifie que l'installation est correcte"""
        print("\n✔️  Vérification de l'installation...")
        
        modules_ok = True
        try:
            import cv2
            print(f"   ✅ OpenCV {cv2.__version__}")
        except ImportError:
            print("   ❌ OpenCV not found")
            modules_ok = False
        
        try:
            import sounddevice
            print(f"   ✅ sounddevice")
        except ImportError:
            print("   ❌ sounddevice not found")
            modules_ok = False
        
        try:
            import numpy
            print(f"   ✅ numpy")
        except ImportError:
            print("   ❌ numpy not found")
            modules_ok = False
        
        return modules_ok
    
    def run_setup(self):
        """Affiche le menu de setup"""
        print("\n" + "="*70)
        print("  ⚙️  CONFIGURATION DES PÉRIPHÉRIQUES")
        print("="*70)
        print("\n  Les étapes suivantes sont optionnelles:")
        print("  Vous pouvez les exécuter maintenant ou plus tard\n")
        
        response = input("  → Lancer la configuration maintenant? (oui/non): ").lower()
        
        if response not in ['oui', 'o', 'yes', 'y']:
            return True
        
        # Lancer device_setup.py
        device_setup = self.project_root / 'device_setup.py'
        if not device_setup.exists():
            device_setup = Path.cwd() / 'device_setup.py'
        
        if device_setup.exists():
            try:
                subprocess.call([self.python_cmd, str(device_setup)])
                return True
            except Exception as e:
                print(f"Erreur: {e}")
                return False
        else:
            print(f"⚠️  device_setup.py non trouvé")
            return False
    
    def print_next_steps(self):
        """Affiche les prochaines étapes"""
        print("\n" + "="*70)
        print("  ✅ INSTALLATION TERMINÉE!")
        print("="*70)
        
        print("\n  📋 Prochaines étapes:\n")
        print("  1. Diagnostic des périphériques:")
        print(f"     {self.python_cmd} device_diagnostic.py\n")
        print("  2. Configuration interactive:")
        print(f"     {self.python_cmd} device_setup.py\n")
        print("  3. Tester votre caméra/microphone")
        print("     dans l'interface de configuration\n")
        
        print("  📖 Documentation:")
        print("     - QUICK_START.txt (démarrage rapide)")
        print("     - DEVICE_SETUP_GUIDE.md (guide complet)")
        print("     - README_SOLUTION.md (vue d'ensemble)\n")
        
        print("="*70)
        print("  Bonne chance! 🚀")
        print("="*70 + "\n")
    
    def install(self):
        """Lance l'installation complète"""
        self.print_banner()
        
        # Étape 1: Créer le dossier logs
        if not self.create_logs_directory():
            return False
        
        # Étape 2: Mettre à jour pip
        if not self.update_pip():
            return False
        
        # Étape 3: Installer les packages Python
        if not self.install_packages():
            print("\n❌ Erreur lors de l'installation des modules")
            return False
        
        # Étape 4: Vérifier l'installation
        if not self.verify_installation():
            print("\n⚠️  Certains modules n'ont pas pu être vérifiés")
            return False
        
        # Étape 5: Configuration spécifique à l'OS
        if self.os_type == 'Linux':
            if not self.setup_linux_permissions():
                print("\n⚠️  Permissions non configurées")
        elif self.os_type == 'Windows':
            self.setup_windows_permissions()
        elif self.os_type == 'Darwin':
            self.setup_macos_permissions()
        
        # Étape 6: Optionnel - Lancer le setup
        self.run_setup()
        
        # Afficher les prochaines étapes
        self.print_next_steps()
        
        return True


def main():
    """Point d'entrée principal"""
    try:
        installer = UniversalInstaller()
        success = installer.install()
        
        if success:
            print("\n✅ Installation réussie!")
            return 0
        else:
            print("\n❌ Installation incomplète")
            return 1
    
    except KeyboardInterrupt:
        print("\n\n❌ Installation annulée par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    
    if sys.platform != 'win32':
        print("\nAppuyez sur Entrée pour terminer...")
        input()
    
    sys.exit(exit_code)
