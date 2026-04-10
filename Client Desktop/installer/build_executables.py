#!/usr/bin/env python3
"""
Compiler BioAccess Secure avec PyInstaller
Crée un exécutable unique et autonome sans dépendances Python
[Version Client Desktop/installer - Chemins adaptés]
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_banner():
    """Affiche l'en-tête"""
    print("\n" + "="*70)
    print("  🔨 COMPILATION - BioAccess Secure")
    print("  Création d'exécutables autonomes avec PyInstaller")
    print("="*70 + "\n")


def check_pyinstaller():
    """Vérifie que PyInstaller est installé"""
    print("1️⃣  Vérification de PyInstaller...")
    
    try:
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'show', 'pyinstaller'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("   ✅ PyInstaller installé\n")
        return True
    except subprocess.CalledProcessError:
        print("   ⚠️  PyInstaller non installé")
        print("\n   Installation:")
        print(f"   {sys.executable} -m pip install pyinstaller\n")
        
        response = input("   Installer maintenant? (oui/non): ").lower()
        if response in ['oui', 'o', 'yes', 'y']:
            print("\n   Installation de PyInstaller...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
                print("   ✅ PyInstaller installé\n")
                return True
            except subprocess.CalledProcessError:
                print("   ❌ Erreur lors de l'installation\n")
                return False
        else:
            print("   ❌ PyInstaller nécessaire\n")
            return False


def compile_setup():
    """Compile setup.py en exécutable"""
    print("\n2️⃣  Compilation de setup.py...")
    
    os.system = os.system or print
    
    # Commande PyInstaller - Chemins adaptés pour Client Desktop/installer/
    cmd = [
        sys.executable, '-m', 'pyinstaller',
        '--onefile',                    # Un seul fichier
        '--windowed',                   # Pas de console (optionnel)
        '--name', 'BioAccessSetup',     # Nom de l'exécutable
        '--icon', 'ICON.ico',           # Icon (si existe)
        '--add-data', f'../../logs:logs',  # CHEMIN ADAPTÉ
        '../../setup.py'                # CHEMIN ADAPTÉ
    ]
    
    try:
        subprocess.check_call(cmd)
        print("   ✅ Compilation réussie!\n")
        
        # Localiser l'exécutable
        dist_dir = Path('dist')
        if dist_dir.exists():
            exe_files = list(dist_dir.glob('BioAccessSetup*'))
            if exe_files:
                exe_path = exe_files[0]
                print(f"   📁 Exécutable créé: {exe_path}\n")
                return True
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Erreur: {e}\n")
        return False


def compile_diagnostic():
    """Compile device_diagnostic.py en exécutable"""
    print("3️⃣  Compilation de device_diagnostic.py...")
    
    cmd = [
        sys.executable, '-m', 'pyinstaller',
        '--onefile',
        '--name', 'BioAccessDiagnostic',
        '--add-data', f'../../logs:logs',  # CHEMIN ADAPTÉ
        '../device_diagnostic.py'         # CHEMIN ADAPTÉ
    ]
    
    try:
        subprocess.check_call(cmd)
        print("   ✅ Compilation réussie!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Erreur (non-bloquant): {e}\n")
        return False


def compile_setup_interactive():
    """Compile device_setup.py en exécutable"""
    print("4️⃣  Compilation de device_setup.py...")
    
    cmd = [
        sys.executable, '-m', 'pyinstaller',
        '--onefile',
        '--name', 'BioAccessConfig',
        '--add-data', f'../../logs:logs',  # CHEMIN ADAPTÉ
        '../device_setup.py'              # CHEMIN ADAPTÉ
    ]
    
    try:
        subprocess.check_call(cmd)
        print("   ✅ Compilation réussie!\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️  Erreur (non-bloquant): {e}\n")
        return False


def cleanup():
    """Nettoie les fichiers temporaires"""
    print("5️⃣  Nettoyage...")
    
    dirs_to_remove = [
        'build',
        '__pycache__',
        '.pytest_cache'
    ]
    
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            import shutil
            shutil.rmtree(dir_path)
            print(f"   ✅ Supprimé: {dir_name}")
    
    print()


def print_summary():
    """Affiche le résumé"""
    print("="*70)
    print("  ✅ COMPILATION TERMINÉE!")
    print("="*70)
    
    dist_dir = Path('dist')
    if dist_dir.exists():
        exe_files = list(dist_dir.glob('*'))
        if exe_files:
            print(f"\n  📁 Exécutables créés dans: {dist_dir}\n")
            for exe in exe_files:
                print(f"     • {exe.name}")
                
                # Afficher la taille
                try:
                    size_mb = exe.stat().st_size / (1024 * 1024)
                    print(f"       Taille: {size_mb:.1f} MB")
                except:
                    pass
    
    print("\n  📋 Ces exécutables sont AUTONOMES!")
    print("     Aucune installation Python nécessaire.\n")
    
    print("  Distribution:")
    print("     1. Copier les exécutables du dossier 'dist'")
    print("     2. Les donner aux utilisateurs")
    print("     3. Ils peuvent les lancer directement!\n")
    
    print("="*70 + "\n")


def main():
    """Point d'entrée principal"""
    try:
        print_banner()
        
        # Vérifier PyInstaller
        if not check_pyinstaller():
            return 1
        
        # Compiler
        compile_setup()
        compile_diagnostic()
        compile_setup_interactive()
        
        # Nettoyer
        cleanup()
        
        # Résumé
        print_summary()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n❌ Compilation annulée")
        return 1
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    
    if platform.system() != 'Windows':
        print("Appuyez sur Entrée pour terminer...")
        input()
    
    sys.exit(exit_code)
