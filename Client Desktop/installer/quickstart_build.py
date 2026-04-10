#!/usr/bin/env python3
"""
Quick Start Builder - Compile et Package en une commande
Pour les utilisateurs qui veulent des exécutables prêts à distribuer
[Version Client Desktop/installer - Chemins adaptés]
"""

import os
import sys
import subprocess
from pathlib import Path


def print_banner():
    print("\n" + "="*80)
    print("  ⚡ QUICK START BUILDER - BioAccess Secure")
    print("  Compilation + Packaging en 1 commande")
    print("="*80 + "\n")


def run_build_executables():
    """Lance la compilation des exécutables"""
    print("1️⃣  Compilation des exécutables...\n")
    
    try:
        script_path = Path(__file__).parent / 'build_executables_advanced.py'
        result = subprocess.run(
            [sys.executable, str(script_path), '--verbose'],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de la compilation: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Le fichier 'build_executables_advanced.py' n'existe pas")
        print("   Assurez-vous d'être dans le bon répertoire")
        return False


def run_build_package():
    """Lance le packaging de distribution"""
    print("\n2️⃣  Création du paquet de distribution...\n")
    
    try:
        script_path = Path(__file__).parent / 'build_distribution_package.py'
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors du packaging: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ Le fichier 'build_distribution_package.py' n'existe pas")
        return False


def print_success_summary():
    """Affiche le résumé du succès"""
    print("\n" + "="*80)
    print("  ✅ QUICK START TERMINÉ")
    print("="*80)
    
    print("\n  📊 Ce qui a été créé:")
    print("     1. Exécutables compilés et optimisés")
    print("     2. Paquet de distribution")
    print("     3. Archives ZIP et 7-Zip")
    print("     4. Documentation complète")
    
    print("\n  📁 Emplacements:")
    print("     • Exécutables: ./dist/")
    print("     • Paquets: ./release/")
    print("     • Archives: ./release/")
    
    print("\n  🚀 Prochaines étapes:")
    print("     1. Vérifier les fichiers dans ./release/")
    print("     2. Télécharger les archives")
    print("     3. Distribuer aux utilisateurs")
    
    print("\n  💡 Commandes utiles:")
    print("     • Compiler seulement: python build_executables_advanced.py")
    print("     • Packager seulement: python build_distribution_package.py")
    
    print("\n" + "="*80 + "\n")


def main():
    """Flux principal"""
    try:
        print_banner()
        
        # Étape 1: Compilation
        if not run_build_executables():
            print("\n❌ La compilation a échoué")
            return 1
        
        # Étape 2: Packaging
        if not run_build_package():
            print("\n❌ Le packaging a échoué")
            print("   Vous pouvez toujours utiliser les exécutables du dossier 'dist/'")
            return 1
        
        # Résumé
        print_success_summary()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Opération interrompue par l'utilisateur")
        return 1
    
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = main()
    
    # Sur les systèmes non-Windows, demander à l'utilisateur de confirmer
    if sys.platform != 'win32' and exit_code == 0:
        input("\nAppuyez sur Entrée pour terminer...")
    
    sys.exit(exit_code)
