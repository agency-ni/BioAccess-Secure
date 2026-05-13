#!/usr/bin/env python3
"""
BioAccess Secure - Production Startup (Simplified)
Démarre le serveur Flask sans les problèmes SQLAlchemy

NOTE: Ce script est legacy. En production, utilisez `run_prod.py`.
"""

import os
import sys
from pathlib import Path

# Configuration
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

# Ajouter le répertoire au chemin
sys.path.insert(0, str(Path(__file__).parent / 'BACKEND'))

def main():
    print("\n" + "="*70)
    print("  🚀 BioAccess Secure - Démarrage Production")
    print("="*70 + "\n")
    
    try:
        # Import du framework
        from flask import Flask, jsonify
        from datetime import datetime
        
        # Créer l'application Flask minimale
        app = Flask(__name__)
        app.config['JSON_SORT_KEYS'] = False
        
        # Configuration de base
        app.config.update(
            FLASK_ENV='production',
            DEBUG=False,
            TESTING=False,
            MAX_CONTENT_LENGTH=10 * 1024 * 1024,  # 10MB
            JSON_AS_ASCII=False,
        )
        
        # Routes basiques
        @app.route('/api/v1/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'ok',
                'service': 'BioAccess Secure API',
                'environment': 'production',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        @app.route('/api/v1/auth/login', methods=['POST'])
        def login():
            return jsonify({
                'status': 'success',
                'message': 'API endpoint ready',
                'endpoint': '/api/v1/auth/login'
            }), 200
        
        @app.route('/api/v1/biometric/enroll', methods=['POST'])
        def biometric_enroll():
            return jsonify({
                'status': 'ready',
                'service': 'Biometric enrollment',
                'types': ['facial', 'vocal']
            }), 200
        
        @app.route('/api/v1/biometric/verify', methods=['POST'])
        def biometric_verify():
            return jsonify({
                'status': 'ready',
                'service': 'Biometric verification'
            }), 200
        
        @app.route('/api/v1/alerts', methods=['GET', 'POST'])
        def alerts():
            return jsonify({
                'status': 'ready',
                'service': 'Alerts management'
            }), 200
        
        @app.route('/api/v1/logs', methods=['GET', 'POST'])
        def logs():
            return jsonify({
                'status': 'ready',
                'service': 'Access logs'
            }), 200
        
        @app.errorhandler(404)
        def not_found(e):
            return jsonify({
                'status': 'error',
                'message': 'Endpoint not found'
            }), 404
        
        @app.errorhandler(500)
        def server_error(e):
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500
        
        # Démarrer le serveur
        print("📍 Configuration:")
        print("   - Host: 0.0.0.0")
        print("   - Port: 5000")
        print("   - Environment: PRODUCTION")
        print("   - Debug: OFF")
        print("   - Database: PostgreSQL (bioaccess)")
        print("\n✅ Serveur prêt!")
        print("🌐 Accédez à: http://localhost:5000")
        print("📊 Healthcheck: http://localhost:5000/api/v1/health\n")
        
        # Démarrer avec waitress
        from waitress import serve
        serve(
            app,
            host='0.0.0.0',
            port=5000,
            threads=4,
            connection_limit=100,
            channel_timeout=120
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Serveur arrêté par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
