#!/usr/bin/env python3
"""
Package Distribution Builder pour BioAccess Secure
Crée des paquets prêts à distribuer sur tous les OS
[Version Client Desktop/installer - Chemins adaptés]
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class PackageBuilder:
    """Constructeur de paquets de distribution"""
    
    def __init__(self):
        # Déterminer le projet_root automatiquement
        script_dir = Path(__file__).parent.absolute()
        if (script_dir.parent.name == 'Client Desktop' or 
            script_dir.name == 'installer'):
            self.project_root = script_dir.parent.parent  # Racine du projet
        else:
            self.project_root = Path.cwd()
        
        self.dist_dir = self.project_root / 'dist'
        self.package_dir = self.project_root / 'release'
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.release_version = f'BioAccess-Secure-{self.timestamp}'
        self.release_path = self.package_dir / self.release_version
    
    def print_banner(self):
        """Affiche le banner"""
        print("\n" + "="*75)
        print("  📦 PACKAGE DISTRIBUTION BUILDER")
        print("  BioAccess Secure Distribution")
        print("="*75 + "\n")
    
    def check_executables(self) -> bool:
        """Vérifie que les exécutables existent"""
        print("1️⃣  Vérification des exécutables...")
        
        if not self.dist_dir.exists():
            print(f"   ❌ Dossier '{self.dist_dir}' non trouvé\n")
            print("   Vous devez d'abord compiler:")
            print("   python build_executables.py\n")
            return False
        
        exe_files = list(self.dist_dir.glob('*'))
        exe_files = [f for f in exe_files if f.is_file()]
        
        if not exe_files:
            print(f"   ❌ Aucun fichier exécutable trouvé\n")
            return False
        
        print(f"   ✅ {len(exe_files)} fichier(s) trouvé(s):\n")
        for exe in exe_files:
            size_mb = exe.stat().st_size / (1024 * 1024)
            print(f"      • {exe.name:<35} {size_mb:>6.1f} MB")
        
        return True
    
    def create_release_structure(self) -> bool:
        """Crée la structure du répertoire de release"""
        print("\n2️⃣  Création de la structure de release...")
        
        try:
            self.release_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Répertoire créé: {self.release_path}\n")
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")
            return False
    
    def copy_executables(self) -> bool:
        """Copie les exécutables dans le répertoire de release"""
        print("3️⃣  Copie des exécutables...")
        
        try:
            for exe_file in self.dist_dir.glob('*'):
                if exe_file.is_file():
                    dest = self.release_path / exe_file.name
                    import shutil
                    shutil.copy2(exe_file, dest)
                    print(f"   ✓ {exe_file.name}")
            
            print()
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")
            return False
    
    def create_readme(self) -> bool:
        """Crée le fichier README"""
        print("4️⃣  Création de la documentation...")
        
        readme_en = """# BioAccess Secure

## Installation

Double-click on **BioAccessSetup.exe** to begin.

## Contents

- **BioAccessSetup.exe** - Initial setup and configuration
- **BioAccessDiagnostic.exe** - Camera and microphone diagnostics
- **BioAccessConfig.exe** - Advanced permission configuration

## System Requirements

- Windows 7 or later (or Linux/macOS with corresponding executables)
- Compatible webcam
- Compatible microphone
- 500 MB free disk space

## Support

For any questions, refer to the included documentation.

---
Build Date: {}
Version: 1.0.0
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        readme_fr = """# BioAccess Secure

## Installation

Double-cliquez sur **BioAccessSetup.exe** pour commencer.

## Contenu

- **BioAccessSetup.exe** - Assistanat d'installation et configuration
- **BioAccessDiagnostic.exe** - Diagnostic des caméras et microphones
- **BioAccessConfig.exe** - Configuration avancée des permissions

## Configuration Système

- Windows 7 ou supérieur (ou Linux/macOS avec exécutables correspondants)
- Une caméra web compatible
- Un microphone compatible
- Au minimum 500 MB d'espace disque libre

## Support

Pour toute question, consultez la documentation fournie.

---
Date de compilation: {}
Version: 1.0.0
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        try:
            (self.release_path / 'README.txt').write_text(readme_en, encoding='utf-8')
            print("   ✓ README.txt (English)")
            
            (self.release_path / 'LISEZMOI.txt').write_text(readme_fr, encoding='utf-8')
            print("   ✓ LISEZMOI.txt (Français)")
            
            print()
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")
            return False
    
    def create_version_info(self) -> bool:
        """Crée le fichier d'informations de version"""
        print("5️⃣  Création des informations de version...")
        
        version_info = f"""[VERSION]
Product=BioAccess-Secure
Version=1.0.0
BuildDate={datetime.now().isoformat()}
Platform={sys.platform}
Python={sys.version}

[FILES]
"""
        
        # Ajouter les informations des fichiers
        for exe_file in self.dist_dir.glob('*'):
            if exe_file.is_file():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                version_info += f"{exe_file.name}={size_mb:.1f}MB\n"
        
        try:
            (self.release_path / 'VERSION.txt').write_text(version_info)
            print("   ✓ VERSION.txt")
            print()
            return True
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")
            return False
    
    def create_zip_archive(self) -> Optional[Path]:
        """Crée une archive ZIP"""
        print("6️⃣  Création de l'archive ZIP...")
        
        archive_path = self.package_dir / f'{self.release_version}.zip'
        
        try:
            import zipfile
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in self.release_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.package_dir)
                        zipf.write(file_path, arcname)
            
            size_mb = archive_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ {archive_path.name} ({size_mb:.1f} MB)")
            print()
            return archive_path
        except Exception as e:
            print(f"   ⚠️  Erreur: {e}\n")
            return None
    
    def create_7z_archive(self) -> Optional[Path]:
        """Crée une archive 7-Zip (si disponible)"""
        print("7️⃣  Création de l'archive 7-Zip...")
        
        try:
            # Vérifier si 7-Zip est disponible
            subprocess.run(['7z'], capture_output=True, check=False, timeout=2)
        except:
            print("   ⚠️  7-Zip non disponible (installation optionnelle)\n")
            return None
        
        archive_path = self.package_dir / f'{self.release_version}.7z'
        
        try:
            cmd = ['7z', 'a', '-y', str(archive_path), str(self.release_path)]
            subprocess.run(cmd, capture_output=True, check=True)
            
            size_mb = archive_path.stat().st_size / (1024 * 1024)
            print(f"   ✓ {archive_path.name} ({size_mb:.1f} MB)")
            print()
            return archive_path
        except Exception as e:
            print(f"   ⚠️  Erreur: {e}\n")
            return None
    
    def print_summary(self, zip_archive: Optional[Path], 
                      archive_7z: Optional[Path]):
        """Affiche le résumé final"""
        print("="*75)
        print("  ✅ PACKAGING TERMINÉ")
        print("="*75)
        
        print(f"\n  📦 Release: {self.release_version}")
        print(f"  📁 Emplacement: {self.release_path}")
        
        # Lister les fichiers
        print("\n  📂 Fichiers du paquet:")
        for file_path in sorted(self.release_path.glob('*')):
            if file_path.is_file():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                print(f"     • {file_path.name:<35} {size_mb:>6.1f} MB")
        
        # Archives créées
        print("\n  📦 Archives:");
        
        if zip_archive:
            size_mb = zip_archive.stat().st_size / (1024 * 1024)
            print(f"     • {zip_archive.name:<35} {size_mb:>6.1f} MB")
        
        if archive_7z:
            size_mb = archive_7z.stat().st_size / (1024 * 1024)
            print(f"     • {archive_7z.name:<35} {size_mb:>6.1f} MB")
        
        print("\n  🚀 Distribution:")
        print("     1. Télécharger les archives du dossier 'release'")
        print("     2. Partager avec les utilisateurs")
        print("     3. Les utilisateurs lancent BioAccessSetup.exe")
        
        print("\n  ⚙️  Système d'exploitation:")
        print(f"     {sys.platform} - {os.name}")
        
        print("\n" + "="*75 + "\n")
    
    def build(self) -> int:
        """Lance le process complet"""
        try:
            self.print_banner()
            
            if not self.check_executables():
                return 1
            
            if not self.create_release_structure():
                return 1
            
            if not self.copy_executables():
                return 1
            
            if not self.create_readme():
                return 1
            
            if not self.create_version_info():
                return 1
            
            zip_archive = self.create_zip_archive()
            archive_7z = self.create_7z_archive()
            
            self.print_summary(zip_archive, archive_7z)
            
            return 0
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Packaging interrompu")
            return 1
        
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Point d'entrée"""
    builder = PackageBuilder()
    exit_code = builder.build()
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
