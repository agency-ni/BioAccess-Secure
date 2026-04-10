#!/usr/bin/env python
"""
Script de diagnostic pour vérifier la configuration Google OAuth
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("DIAGNOSTIC - Configuration Google OAuth")
print("=" * 60)

# 1. Vérifier les imports
print("\n1. Vérification des imports...")
try:
    from google.oauth2 import id_token
    print("   ✓ google.oauth2.id_token importé")
except ImportError as e:
    print(f"   ✗ Erreur import google.oauth2: {e}")

try:
    from google.auth.transport import requests
    print("   ✓ google.auth.transport.requests importé")
except ImportError as e:
    print(f"   ✗ Erreur import google.auth.transport: {e}")

# 2. Vérifier les variables d'environnement
print("\n2. Vérification des variables d'environnement...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    google_client_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    
    if not google_client_id:
        print("   ⚠ GOOGLE_CLIENT_ID: Non défini")
    elif google_client_id.startswith('VOTRE'):
        print(f"   ⚠ GOOGLE_CLIENT_ID: Placeholder ({google_client_id})")
    else:
        print(f"   ✓ GOOGLE_CLIENT_ID défini: {google_client_id[:20]}...")
    
    if not google_client_secret:
        print("   ⚠ GOOGLE_CLIENT_SECRET: Non défini")
    else:
        print(f"   ✓ GOOGLE_CLIENT_SECRET défini: {google_client_secret[:10]}...")
        
except Exception as e:
    print(f"   ✗ Erreur chargement .env: {e}")

# 3. Vérifier la configuration Flask
print("\n3. Vérification de la configuration Flask...")
try:
    from config import Config
    flask_config = Config()
    
    print(f"   - GOOGLE_CLIENT_ID: {flask_config.GOOGLE_CLIENT_ID[:20] if flask_config.GOOGLE_CLIENT_ID else 'Non défini'}...")
    print(f"   - GOOGLE_CLIENT_SECRET: {'Oui' if flask_config.GOOGLE_CLIENT_SECRET else 'Non'}")
    print(f"   - GOOGLE_REDIRECT_URI: {flask_config.GOOGLE_REDIRECT_URI}")
except Exception as e:
    print(f"   ✗ Erreur chargement config: {e}")

# 4. Vérifier la base de données
print("\n4. Vérification de la base de données...")
try:
    from app import create_app
    from core.database import db
    
    app = create_app()
    with app.app_context():
        from models.user import User
        user_count = User.query.count()
        print(f"   ✓ Base de données connectée ({user_count} utilisateurs)")
except Exception as e:
    print(f"   ✗ Erreur BD: {e}")

# 5. Test de l'endpoint
print("\n5. Vérification de l'endpoint /api/v1/auth/google...")
try:
    from app import create_app
    app = create_app()
    
    # Lister les routes
    auth_routes = [str(rule) for rule in app.url_map.iter_rules() if 'auth' in str(rule)]
    
    if '/api/v1/auth/google' in [str(rule).split(' ')[0] for rule in app.url_map.iter_rules()]:
        print("   ✓ Endpoint /api/v1/auth/google enregistré")
    else:
        print("   ✗ Endpoint /api/v1/auth/google non trouvé")
        print("   Routes auth disponibles:")
        for route in auth_routes:
            print(f"      - {route}")
except Exception as e:
    print(f"   ✗ Erreur vérification endpoint: {e}")

print("\n" + "=" * 60)
print("FIN DIAGNOSTIC")
print("=" * 60)
print("\n📝 Prochaines étapes:")
print("1. Configurer GOOGLE_CLIENT_ID dans .env")
print("2. Configurer GOOGLE_CLIENT_SECRET dans .env")
print("3. Installer: pip install google-auth google-auth-oauthlib")
print("4. Redémarrer le backend")
print("=" * 60)
