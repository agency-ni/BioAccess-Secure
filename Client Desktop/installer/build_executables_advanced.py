#!/usr/bin/env python3
"""
Compilateur avancé PyInstaller pour BioAccess Secure
- Support des fichiers .spec prédéfinis
- Options d'optimisation
- Gestion améliorée des erreurs
- Rapports détaillés
[Version Client Desktop/installer - Chemins adaptés automatiquement]
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Tuple, Optional


class PyInstallerBuilder:
    """Orchestrateur de compilation PyInstaller"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        
        # Déterminer le projet_root automatiquement
        # Si on est dans Client Desktop/installer, remonter à la racine
        current = Path.cwd()
        self.script_dir = Path(__file__).parent.absolute()
        
        # Si le script est dans Client Desktop/installer
        if (self.script_dir.parent.name == 'Client Desktop' or 
            self.script_dir.name == 'installer'):
            self.project_root = self.script_dir.parent.parent  # Remonter à racine
        else:
            self.project_root = current
        
        self.dist_dir = self.project_root / 'dist'
        self.build_dir = self.project_root / 'build'
        self.results = {
            'successful': [],
            'failed': [],
            'skipped': []
        }
    
    def print_banner(self):
        """Banner de démarrage"""
        print("\n" + "="*80)
        print("  🔨 COMPILATEUR AVANCÉ - BioAccess Secure")
        print("  PyInstaller - Création d'exécutables autonomes")
        print("="*80 + "\n")
        print(f"  📂 Répertoire racine: {self.project_root}")
        print(f"  📁 Répertoire dist: {self.dist_dir}")
        print(f"  🖥️  Système: {platform.system()}")
        print()
    
    def check_pyinstaller(self) -> bool:
        """Vérifie et installe PyInstaller si nécessaire"""
        print("1️⃣  Vérification de PyInstaller...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pyinstaller', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"   ✅ PyInstaller {result.stdout.strip()}\n")
            return True
        
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ⚠️  PyInstaller non installé")
            self._install_pyinstaller()
            return True
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}\n")
            return False
    
    def _install_pyinstaller(self):
        """Installe PyInstaller"""
        print("   Installation de PyInstaller...")
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', 'pyinstaller', '-q'],
                stdout=subprocess.DEVNULL
            )
            print("   ✅ PyInstaller installé\n")
        except Exception as e:
            print(f"   ❌ Erreur d'installation: {e}\n")
    
    def compile_with_spec(self, spec_file: str) -> bool:
        """Compile en utilisant un fichier .spec"""
        print(f"   📋 Utilisant spec: {spec_file}")
        
        cmd = [
            sys.executable, '-m', 'pyinstaller',
            '--clean',
            '--distpath', str(self.dist_dir),
            '--buildpath', str(self.build_dir),
            spec_file
        ]
        
        try:
            if self.verbose:
                subprocess.run(cmd, check=True, cwd=str(self.project_root))
            else:
                subprocess.run(cmd, capture_output=True, check=True, cwd=str(self.project_root))
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erreur: {e}")
            return False
    
    def compile_direct(
        self,
        source: str,
        name: str,
        console: bool = True,
        optimize: bool = True,
        strip: bool = True
    ) -> bool:
        """Compile directement sans .spec"""
        print(f"   📝 Compilation: {source} → {name}")
        
        cmd = [
            sys.executable, '-m', 'pyinstaller',
            '--clean',
            '--onefile',
            '--distpath', str(self.dist_dir),
            '--buildpath', str(self.build_dir),
        ]
        
        if not console:
            cmd.append('--windowed')
        
        if console:
            cmd.append('--console')
        
        # Options d'optimisation
        if optimize:
            cmd.extend(['-O2'])  # Optimisation O2
        
        if strip:
            cmd.append('--strip')
        
        # Collecte automatique des modules
        cmd.extend([
            '--collect-all', 'cv2',
            '--collect-all', 'sounddevice',
            '--collect-all', 'soundfile',
            '--collect-all', 'scipy',
            '--collect-all', 'numpy',
        ])
        
        # Ajouter les données
        logs_dir = self.project_root / 'logs'
        if logs_dir.exists():
            cmd.extend(['--add-data', f'{logs_dir}{os.pathsep}logs'])
        
        cmd.extend(['--name', name, source])
        
        try:
            if self.verbose:
                subprocess.run(cmd, check=True, cwd=str(self.project_root))
            else:
                subprocess.run(cmd, capture_output=True, check=True, cwd=str(self.project_root))
            
            return True
        except subprocess.CalledProcessError as e:
            if self.verbose:
                print(f"   ❌ Erreur: {e}")
            return False
    
    def compile_setup(self) -> bool:
        """Compil le fichier setup.py"""
        print("\n2️⃣  Compilation de setup.py")
        
        setup_py = self.project_root / 'setup.py'
        spec_file = self.project_root / 'setup_build.spec'
        
        if spec_file.exists():
            success = self.compile_with_spec(str(spec_file))
        else:
            success = self.compile_direct(
                str(setup_py),
                'BioAccessSetup',
                console=True,
                optimize=True,
                strip=True
            )
        
        if success:
            self.results['successful'].append('BioAccessSetup')
            print("   ✅ Succès\n")
        else:
            self.results['failed'].append('BioAccessSetup')
        
        return success
    
    def compile_diagnostic(self) -> bool:
        """Compile device_diagnostic.py"""
        print("\n3️⃣  Compilation de device_diagnostic.py")
        
        source = self.project_root / 'Client Desktop' / 'device_diagnostic.py'

        if not source.exists():
            print(f"   ⚠️  Fichier non trouvé: {source}\n")
            self.results['skipped'].append('BioAccessDiagnostic')
            return False
        
        success = self.compile_direct(
            str(source),
            'BioAccessDiagnostic',
            console=True,
            optimize=True,
            strip=True
        )
        
        if success:
            self.results['successful'].append('BioAccessDiagnostic')
            print("   ✅ Succès\n")
        else:
            self.results['failed'].append('BioAccessDiagnostic')
        
        return success
    
    def compile_config(self) -> bool:
        """Compile device_setup.py"""
        print("\n4️⃣  Compilation de device_setup.py")
        
        source = self.project_root / 'Client Desktop' / 'device_setup.py'
        
        if not source.exists():
            print(f"   ⚠️  Fichier non trouvé: {source}\n")
            self.results['skipped'].append('BioAccessConfig')
            return False
        
        success = self.compile_direct(
            str(source),
            'BioAccessConfig',
            console=True,
            optimize=True,
            strip=True
        )
        
        if success:
            self.results['successful'].append('BioAccessConfig')
            print("   ✅ Succès\n")
        else:
            self.results['failed'].append('BioAccessConfig')
        
        return success
    
    def cleanup(self, remove_spec=False):
        """Nettoie les fichiers temporaires"""
        print("\n5️⃣  Nettoyage des fichiers temporaires...")
        
        dirs_to_remove = ['build', '__pycache__', '.pytest_cache']
        
        for dir_name in dirs_to_remove:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                import shutil
                try:
                    shutil.rmtree(dir_path)
                    print(f"   ✅ Supprimé: {dir_name}")
                except Exception as e:
                    print(f"   ⚠️  Impossible de supprimer {dir_name}: {e}")
        
        # Supprimer les fichiers .spec compilés
        if remove_spec:
            for spec_file in self.project_root.glob('*.spec'):
                try:
                    spec_file.unlink()
                    print(f"   ✅ Supprimé: {spec_file.name}")
                except Exception as e:
                    print(f"   ⚠️  Impossible de supprimer {spec_file.name}: {e}")
        
        print()
    
    def print_summary(self):
        """Affiche le résumé final"""
        print("\n" + "="*80)
        print("  📊 RÉSUMÉ DE COMPILATION")
        print("="*80)
        
        # Statistiques
        print(f"\n  ✅ Réussis: {len(self.results['successful'])}")
        for name in self.results['successful']:
            print(f"     • {name}")
        
        if self.results['failed']:
            print(f"\n  ❌ Échoués: {len(self.results['failed'])}")
            for name in self.results['failed']:
                print(f"     • {name}")
        
        if self.results['skipped']:
            print(f"\n  ⏭️  Ignorés: {len(self.results['skipped'])}")
            for name in self.results['skipped']:
                print(f"     • {name}")
        
        # Détails des exécutables
        if self.dist_dir.exists():
            exe_files = list(self.dist_dir.glob('*'))
            if exe_files:
                print(f"\n  📁 Exécutables dans: {self.dist_dir}\n")
                total_size = 0
                for exe in sorted(exe_files):
                    if exe.is_file():
                        size_mb = exe.stat().st_size / (1024 * 1024)
                        total_size += exe.stat().st_size
                        print(f"     • {exe.name:<30} {size_mb:>8.1f} MB")
                
                print(f"\n  📊 Taille totale: {total_size / (1024 * 1024):.1f} MB")
        
        print("\n  💡 Ces exécutables sont COMPLÈTEMENT AUTONOMES!")
        print("     • Aucune installation Python nécessaire")
        print("     • Aucune dépendance externe")
        print("     • Peuvent être distribués directement")
        
        print("\n  📦 Distribution:")
        print("     1. Copier le contenu de 'dist/' sur un support")
        print("     2. Partager avec les utilisateurs")
        print("     3. Les utilisateurs lancent les .exe directement")
        
        print("\n  🔐 Sécurité (Windows):")
        print("     • Signer les exécutables pour éviter SmartScreen")
        print("     • Utiliser un certificat EV (Extended Validation)")
        
        print("\n" + "="*80 + "\n")
    
    def build_all(self, cleanup=True, remove_spec=False):
        """Lance la compilation complète"""
        try:
            self.print_banner()
            
            if not self.check_pyinstaller():
                return 1
            
            self.compile_setup()
            self.compile_diagnostic()
            self.compile_config()
            
            if cleanup:
                self.cleanup(remove_spec=remove_spec)
            
            self.print_summary()
            
            return 0 if len(self.results['failed']) == 0 else 1
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Compilation interrompue par l'utilisateur")
            return 1
        
        except Exception as e:
            print(f"\n❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compilateur PyInstaller pour BioAccess Secure'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Mode verbeux'
    )
    parser.add_argument(
        '-nc', '--no-cleanup',
        action='store_true',
        help='Ne pas nettoyer après compilation'
    )
    parser.add_argument(
        '-rs', '--remove-spec',
        action='store_true',
        help='Supprimer les fichiers .spec après compilation'
    )
    
    args = parser.parse_args()
    
    builder = PyInstallerBuilder(verbose=args.verbose)
    exit_code = builder.build_all(
        cleanup=not args.no_cleanup,
        remove_spec=args.remove_spec
    )
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
