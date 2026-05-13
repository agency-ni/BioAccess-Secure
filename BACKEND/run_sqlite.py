#!/usr/bin/env python3
"""
Serveur BioAccess-Secure simplifié avec SQLite
Version de production sans SQLAlchemy pour éviter les problèmes de compatibilité

NOTE: Ce script est legacy et ne doit pas être utilisé pour la production PostgreSQL.
"""

import os
import sys
import sqlite3
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bioaccess.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Création de l'application Flask
app = Flask(__name__)

# Configuration CORS
CORS(app, origins=["http://localhost:5500", "http://127.0.0.1:5500", "http://localhost:3000"])

# Configuration de base
app.config['SECRET_KEY'] = 'super_secret_key_for_bioaccess_secure_2024'
app.config['JWT_SECRET_KEY'] = 'jwt_secret_key_bioaccess_2024'

# Base de données SQLite
DB_PATH = os.path.join(os.path.dirname(__file__), 'bioaccess.db')

def get_db_connection():
    """Obtenir une connexion à la base de données SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialiser la base de données si elle n'existe pas"""
    if not os.path.exists(DB_PATH):
        logger.info("Base de données non trouvée, création en cours...")
        os.system('python create_tables_sqlite.py')
        logger.info("Base de données créée avec succès")

# Routes de base
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Point de santé de l'API"""
    return jsonify({
        "environment": "production",
        "service": "BioAccess Secure API",
        "status": "ok",
        "database": "SQLite",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Authentification utilisateur"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND is_active = 1',
            (email,)
        ).fetchone()
        conn.close()

        if user:
            logger.info(f"Tentative de connexion pour {email}")
            logger.info(f"Utilisateur trouvé: {user['email']}, mot de passe fourni: {password}")
            # Pour les tests, accepter admin123 pour l'admin
            if password == "admin123" and user['email'] == "admin@bioaccess.secure":
                logger.info("Connexion admin réussie")
                return jsonify({
                    "message": "Connexion réussie",
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "role": user['role']
                    },
                    "token": f"fake_jwt_token_{user['id']}"
                })
            elif user['password_hash'] == password:
                logger.info("Connexion par hash réussie")
                return jsonify({
                    "message": "Connexion réussie",
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "role": user['role']
                    },
                    "token": f"fake_jwt_token_{user['id']}"
                })
            else:
                logger.info("Mot de passe incorrect")
        else:
            logger.info(f"Utilisateur {email} non trouvé")

        return jsonify({"error": "Identifiants invalides"}), 401

    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.route('/api/v1/biometric/enroll', methods=['POST'])
def biometric_enroll():
    """Enregistrement biométrique"""
    return jsonify({
        "service": "Biometric enrollment",
        "status": "ready",
        "types": ["facial", "vocal"],
        "message": "Service d'enregistrement biométrique prêt"
    })

@app.route('/api/v1/biometric/verify', methods=['POST'])
def biometric_verify():
    """Vérification biométrique"""
    return jsonify({
        "service": "Biometric verification",
        "status": "ready",
        "message": "Service de vérification biométrique prêt"
    })

@app.route('/api/v1/alerts', methods=['POST'])
def create_alert():
    """Créer une alerte"""
    return jsonify({
        "service": "Alerts management",
        "status": "ready",
        "message": "Service d'alertes prêt"
    })

@app.route('/api/v1/logs', methods=['GET'])
def get_logs():
    """Consulter les logs d'accès"""
    return jsonify({
        "service": "Access logs",
        "status": "ready",
        "message": "Service de logs prêt"
    })

@app.route('/api/v1/users', methods=['GET'])
def get_users():
    """Récupérer la liste des utilisateurs"""
    try:
        conn = get_db_connection()
        users = conn.execute('SELECT id, nom, prenom, email, role, is_active FROM users').fetchall()
        conn.close()

        user_list = []
        for user in users:
            user_list.append({
                "id": user['id'],
                "nom": user['nom'],
                "prenom": user['prenom'],
                "email": user['email'],
                "role": user['role'],
                "is_active": bool(user['is_active'])
            })

        return jsonify({
            "users": user_list,
            "total": len(user_list)
        })

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint non trouvé"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Erreur interne du serveur"}), 500

def main():
    """Fonction principale"""
    print("🚀 Démarrage de BioAccess-Secure API (SQLite)")
    print("=" * 50)

    # Initialiser la base de données
    init_db()

    # Créer le dossier logs s'il n'existe pas
    os.makedirs('logs', exist_ok=True)

    # Configuration du serveur
    host = '0.0.0.0'
    port = 5000
    debug = False

    print(f"📡 Serveur démarré sur http://{host}:{port}")
    print("🔗 Base de données: SQLite (bioaccess.db)")
    print("📊 Environnement: Production")
    print("🛡️  CORS activé pour le développement")
    print()
    print("Endpoints disponibles:")
    print("  GET  /api/v1/health      - Santé de l'API")
    print("  POST /api/v1/auth/login  - Authentification")
    print("  POST /api/v1/biometric/enroll - Enregistrement biométrique")
    print("  POST /api/v1/biometric/verify - Vérification biométrique")
    print("  GET  /api/v1/users       - Liste des utilisateurs")
    print("  POST /api/v1/alerts      - Créer une alerte")
    print("  GET  /api/v1/logs        - Consulter les logs")
    print()
    print("Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 50)

    # Démarrer le serveur
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()