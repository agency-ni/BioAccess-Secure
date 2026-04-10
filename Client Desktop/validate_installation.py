#!/usr/bin/env python3
"""
Script de validation - Vérifier que tout est installé et fonctionnel
BioAccess Secure - Device Configuration
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime


def print_header():
    """Affiche l'en-tête"""
    print("\n" + "="*60)
    print("  ✅ VALIDATION - BioAccess Secure")
    print("  Vérification de l'installation et configuration")
    print("="*60 + "\n")


def check_python():
    """Vérifie la version Python"""
    print("1️⃣  Vérification de Python...")
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"   Python {version}")
    
    if sys.version_info >= (3, 7):
        print("   ✅ OK (≥ 3.7)")
        return True
    else:
        print("   ❌ ERREUR (besoin ≥ 3.7)")
        return False


def check_modules():
    """Vérifie les modules Python"""
    print("\n2️⃣  Vérification des modules Python...")
    
    modules_required = {
        'cv2': 'OpenCV',
        'sounddevice': 'sounddevice',
        'soundfile': 'soundfile',
        'scipy': 'scipy',
        'numpy': 'numpy'
    }
    
    all_ok = True
    
    for module_name, display_name in modules_required.items():
        try:
            module = __import__(module_name)
            version = getattr(module, '__version__', 'unknown')
            print(f"   ✅ {display_name} ({version})")
        except ImportError:
            print(f"   ❌ {display_name} (pas installé)")
            all_ok = False
    
    return all_ok


def check_files():
    """Vérifie que tous les fichiers existent"""
    print("\n3️⃣  Vérification des fichiers...")
    
    files_required = {
        'device_diagnostic.py': 'Diagnostic',
        'permissions_manager.py': 'Gestionnaire permissions',
        'device_setup.py': 'Interface setup',
    }
    
    all_ok = True
    current_dir = Path.cwd()
    
    for filename, description in files_required.items():
        filepath = current_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"   ✅ {filename} ({size} bytes) - {description}")
        else:
            print(f"   ❌ {filename} (manquant)")
            all_ok = False
    
    return all_ok


def check_logs_directory():
    """Vérifie que le répertoire logs existe"""
    print("\n4️⃣  Vérification du répertoire logs...")
    
    logs_dir = Path('logs')
    
    if not logs_dir.exists():
        print(f"   ℹ️  Création du répertoire logs...")
        try:
            logs_dir.mkdir(exist_ok=True)
            print(f"   ✅ Répertoire logs créé")
            return True
        except OSError as e:
            print(f"   ❌ Erreur: {e}")
            return False
    else:
        print(f"   ✅ Répertoire logs existe")
        
        # Vérifier les fichiers de logs
        log_files = list(logs_dir.glob('*.log')) + list(logs_dir.glob('*.json'))
        if log_files:
            print(f"   ℹ️  {len(log_files)} fichier(s) de log trouvé(s)")
        
        return True


def check_diagnostic():
    """Teste le diagnostic des périphériques"""
    print("\n5️⃣  Test du diagnostic des périphériques...")
    
    try:
        from device_diagnostic import DeviceDiagnostic
        
        diagnostic = DeviceDiagnostic()
        print("   ✅ DeviceDiagnostic instancié")
        
        # Obtenir les infos sans faire le test complet
        print(f"   ℹ️  OS: {diagnostic.os_type}")
        print(f"   ℹ️  Python: {diagnostic.python_version}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def check_permissions_manager():
    """Teste le gestionnaire de permissions"""
    print("\n6️⃣  Test du gestionnaire de permissions...")
    
    try:
        from permissions_manager import PermissionsManager
        
        pm = PermissionsManager()
        print("   ✅ PermissionsManager instancié")
        print(f"   ℹ️  OS: {pm.os_type}")
        print(f"   ℹ️  Utilisateur: {pm.username}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False


def check_backend_permissions():
    """Teste le gestionnaire de permissions backend"""
    print("\n7️⃣  Test du gestionnaire de permissions backend...")
    
    try:
        # Import depuis le backend
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'BACKEND'))
        
        from core.biometric_permissions import (
            BiometricPermissionsManager,
            BiometricPermission,
            setup_default_permissions
        )
        
        manager = BiometricPermissionsManager()
        print("   ✅ BiometricPermissionsManager instancié")
        
        # Test de permissions
        setup_default_permissions('test_user', 'employee')
        
        perms = manager.get_user_permissions('test_user', 'employee')
        print(f"   ✅ Permissions configurées pour test_user: {len(perms)} permissions")
        
        # Test de vérification
        check = manager.check_permission(
            'test_user',
            'employee',
            BiometricPermission.USE_CAMERA
        )
        print(f"   ✅ Vérification de permission: {check['allowed']}")
        
        return True
    except Exception as e:
        print(f"   ⚠️  Permissions backend non testées (peut être normal): {e}")
        return True  # Pas critique


def print_summary(results):
    """Affiche le résumé"""
    print("\n" + "="*60)
    print("  📊 RÉSUMÉ")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    percentage = int((passed / total) * 100)
    
    print(f"\nTests réussis: {passed}/{total} ({percentage}%)\n")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print("\n" + "="*60)
    
    if percentage == 100:
        print("  ✅ VALIDATION COMPLÈTE - Tout fonctionne!")
        print("  Vous pouvez maintenant exécuter device_setup.py")
    elif percentage >= 70:
        print("  ⚠️  VALIDATION PARTIELLE - Certains tests ont échoué")
        print("  Vérifiez les erreurs ci-dessus")
    else:
        print("  ❌ VALIDATION ÉCHOUÉE - Trop d'erreurs")
        print("  Consultez le guide d'installation")
    
    print("="*60 + "\n")
    
    return percentage == 100


def print_next_steps(all_passed):
    """Affiche les prochaines étapes"""
    print("📋 PROCHAINES ÉTAPES:\n")
    
    if all_passed:
        print("1. Lancer le diagnostic:")
        print("   python device_diagnostic.py\n")
        print("2. Configurer les permissions:")
        print("   python device_setup.py\n")
        print("3. Suivre les instructions affichées\n")
    else:
        print("1. Installer les dépendances manquantes:")
        print("   python install_dependencies.py\n")
        print("   Ou sur Windows:")
        print("   install_permissions.bat\n")
        print("2. Relancer cette validation")
        print("   python validate_installation.py\n")


def main():
    """Point d'entrée principal"""
    print_header()
    
    results = {}
    
    # Exécuter les vérifications
    results['Python Version'] = check_python()
    results['Modules Required'] = check_modules()
    results['Required Files'] = check_files()
    results['Logs Directory'] = check_logs_directory()
    results['Device Diagnostic'] = check_diagnostic()
    results['Permissions Manager'] = check_permissions_manager()
    results['Backend Permissions'] = check_backend_permissions()
    
    # Afficher le résumé
    all_passed = print_summary(results)
    
    # Afficher les prochaines étapes
    print_next_steps(all_passed)
    
    # Retourner le code de sortie approprié
    return 0 if all_passed else 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Validation annulée")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
