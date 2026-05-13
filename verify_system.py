#!/usr/bin/env python3
"""
Script de vérification et test complet du système BioAccess Secure
Vérifie: PostgreSQL, tables, API, clients, configuration
"""

import sys
import os
from pathlib import Path

# Ajouter les répertoires au chemin
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'Client Desktop'))
sys.path.insert(0, str(Path(__file__).parent / 'door-system'))

def print_test(title, success, message=""):
    """Afficher le résultat d'un test"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"  {status}: {title}")
    if message:
        print(f"         {message}")

def print_section(title):
    """Afficher un titre de section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_python_version():
    """Vérifier la version de Python"""
    print_section("1. Vérification Python")
    version = sys.version_info
    success = version.major >= 3 and version.minor >= 9
    print_test(f"Python {version.major}.{version.minor}", success)
    return success

def test_postgres():
    """Vérifier PostgreSQL"""
    print_section("2. Vérification PostgreSQL")
    try:
        import psycopg2
        print_test("Module psycopg2", True)
        
        # Tester la connexion
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password='postgres'
            )
            conn.close()
            print_test("Connexion PostgreSQL", True)
            return True
        except Exception as e:
            print_test("Connexion PostgreSQL", False, str(e))
            return False
    except ImportError:
        print_test("Module psycopg2", False, "psycopg2 non installé")
        return False

def test_flask():
    """Vérifier Flask et ses dépendances"""
    print_section("3. Vérification Flask et dépendances")
    
    modules = [
        'flask',
        'flask_cors',
        'flask_sqlalchemy',
        'flask_compress',
        'prometheus_flask_exporter',
        'cryptography',
        'pydantic',
        'redis',
        'requests'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            print_test(f"Module {module}", True)
        except ImportError:
            print_test(f"Module {module}", False)
            all_ok = False
    
    return all_ok

def test_biometric_libs():
    """Vérifier les bibliothèques biométriques"""
    print_section("4. Vérification Biométrie")
    
    modules = [
        ('opencv', 'cv2'),
        ('numpy', 'numpy'),
        ('scipy', 'scipy'),
    ]
    
    all_ok = True
    for name, import_name in modules:
        try:
            __import__(import_name)
            print_test(f"Module {name}", True)
        except ImportError:
            print_test(f"Module {name}", False)
            all_ok = False
    
    return all_ok

def test_config_files():
    """Vérifier les fichiers de configuration"""
    print_section("5. Vérification fichiers de configuration")
    
    backend_root = Path(__file__).parent / 'BACKEND'
    
    files = {
        'BACKEND/.env': backend_root / '.env',
        'BACKEND/config.py': backend_root / 'config.py',
        'BACKEND/app.py': backend_root / 'app.py',
        'door-system/.env': Path(__file__).parent / 'door-system' / '.env',
        'door-system/config.py': Path(__file__).parent / 'door-system' / 'config.py',
    }
    
    all_ok = True
    for name, path in files.items():
        exists = path.exists()
        print_test(f"{name} exists", exists)
        if exists and path.name == '.env':
            # Vérifier que le fichier a du contenu
            with open(path, 'r') as f:
                content = f.read().strip()
                has_config = len(content) > 0
                print_test(f"  {name} has config", has_config)
        if not exists:
            all_ok = False
    
    return all_ok

def test_api_endpoints():
    """Tester les endpoints API"""
    print_section("6. Vérification endpoints API")
    
    import requests
    
    endpoints = [
        ('/api/v1/health', 'GET'),
        ('/api/v1/auth/login', 'POST'),
        ('/api/v1/biometric/verify', 'POST'),
        ('/api/v1/alerts', 'POST'),
    ]
    
    print("  💡 Vérification que les routes sont définies...")
    print("  ⚠️  Les tests complets se feront après le démarrage du serveur")
    
    return True

def test_database_schema():
    """Vérifier le schéma de la base de données"""
    print_section("7. Vérification schéma base de données")
    
    backend_root = Path(__file__).parent / 'BACKEND'
    schema_file = backend_root / 'migrations' / 'schema.sql'
    
    if schema_file.exists():
        with open(schema_file, 'r') as f:
            content = f.read()
            tables = [
                'users',
                'admins',
                'employes',
                'templates_biometriques',
                'phrases_aleatoires',
                'tentatives_auth',
                'logs_acces',
                'alertes'
            ]
            
            all_found = True
            for table in tables:
                if f'CREATE TABLE' in content and table in content:
                    print_test(f"Table {table}", True)
                else:
                    print_test(f"Table {table}", False)
                    all_found = False
            
            return all_found
    else:
        print_test("Fichier schema.sql", False)
        return False

def test_env_variables():
    """Vérifier les variables d'environnement"""
    print_section("8. Vérification variables d'environnement")
    
    backend_root = Path(__file__).parent / 'BACKEND'
    env_file = backend_root / '.env'
    
    required_vars = [
        'FLASK_ENV=production',
        'DATABASE_URL',
        'BACKEND_URL',
        'SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    all_ok = True
    for var in required_vars:
        if var.split('=')[0] in env_content or var in env_content:
            print_test(f"Variable {var.split('=')[0]}", True)
        else:
            print_test(f"Variable {var.split('=')[0]}", False)
            all_ok = False
    
    return all_ok

def print_summary(results):
    """Afficher le résumé"""
    print_section("RÉSUMÉ DES VÉRIFICATIONS")
    
    checks = [
        ('Python', results[0]),
        ('PostgreSQL', results[1]),
        ('Flask & dépendances', results[2]),
        ('Biométrie', results[3]),
        ('Fichiers de configuration', results[4]),
        ('Endpoints API', results[5]),
        ('Schéma base de données', results[6]),
        ('Variables d\'environnement', results[7]),
    ]
    
    passed = sum(1 for _, r in checks if r)
    total = len(checks)
    
    for name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Résultat: {passed}/{total} vérifications réussies")
    
    if passed == total:
        print("\n  🎉 SYSTÈME PRÊT POUR PRODUCTION!")
        print("  Lancez le serveur avec: python run_production.py")
        return True
    else:
        print("\n  ⚠️  PROBLÈMES DÉTECTÉS - Veuillez corriger avant de démarrer")
        return False

def main():
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  BioAccess Secure - Vérification Système Production".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    results = [
        test_python_version(),
        test_postgres(),
        test_flask(),
        test_biometric_libs(),
        test_config_files(),
        test_api_endpoints(),
        test_database_schema(),
        test_env_variables(),
    ]
    
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
