#!/usr/bin/env python3
"""
Script de démarrage production pour BioAccess Secure
Vérifie et initialise PostgreSQL, créé les tables, puis démarre l'API

NOTE: Ce script est désormais legacy. En production, utilisez `run_prod.py`.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Ajouter le répertoire BACKEND au chemin
sys.path.insert(0, str(Path(__file__).parent))

def print_header(msg):
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}\n")

def check_postgres():
    """Vérifier que PostgreSQL est accessible"""
    print_header("🔍 Vérification PostgreSQL")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres'  # À modifier si nécessaire
        )
        conn.close()
        print("✅ PostgreSQL est accessible")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL n'est pas accessible: {e}")
        print("💡 Assurez-vous que PostgreSQL est installé et en cours d'exécution")
        return False

def init_database():
    """Initialiser la base de données PostgreSQL"""
    print_header("🗄️  Initialisation de la base de données PostgreSQL")
    try:
        import psycopg2
        
        # Connexion au serveur PostgreSQL
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Créer l'utilisateur
        try:
            cur.execute("""
                CREATE ROLE bioaccess_user WITH LOGIN PASSWORD 'secure_password';
            """)
            print("✅ Utilisateur bioaccess_user créé")
        except psycopg2.Error:
            print("⚠️  Utilisateur bioaccess_user existe déjà")
        
        # Créer la base de données "bioaccess"
        try:
            cur.execute("""
                CREATE DATABASE bioaccess 
                    OWNER bioaccess_user 
                    ENCODING 'UTF8';
            """)
            print("✅ Base de données 'bioaccess' créée")
        except psycopg2.Error:
            print("⚠️  Base de données 'bioaccess' existe déjà")
        
        # Accorder les privilèges
        cur.execute("GRANT ALL PRIVILEGES ON DATABASE bioaccess TO bioaccess_user;")
        
        cur.close()
        conn.close()
        
        # Maintenant créer les tables
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='bioaccess',
            user='bioaccess_user',
            password='secure_password'
        )
        cur = conn.cursor()
        
        # Lire et exécuter le schéma SQL
        schema_file = Path(__file__).parent / 'migrations' / 'schema.sql'
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
                # Adapter le contenu pour PostgreSQL si nécessaire
                sql_content = sql_content.replace('DATETIME', 'TIMESTAMP')
                sql_content = sql_content.replace('LONGBLOB', 'BYTEA')
                sql_content = sql_content.replace('ENUM(', 'VARCHAR CHECK (')
                sql_content = sql_content.replace('CHECK (', '')
                sql_content = sql_content.replace(')', ' CHECK (')
                
                try:
                    cur.execute(sql_content)
                    conn.commit()
                    print("✅ Tables créées avec succès")
                except Exception as e:
                    print(f"⚠️  Tables existent probablement déjà: {e}")
        
        cur.close()
        conn.close()
        
        print("✅ Base de données initialisée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

def start_flask():
    """Démarrer l'application Flask"""
    print_header("🚀 Démarrage du serveur BioAccess Secure en PRODUCTION")
    try:
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = '0'
        
        # Importer et créer l'app
        from app import create_app
        
        app = create_app('production')
        
        from waitress import serve
        
        print("📍 Serveur lancé sur http://0.0.0.0:5000")
        print("✅ Base de données: PostgreSQL (bioaccess)")
        print("✅ Mode: PRODUCTION")
        print("✅ Debug: DÉSACTIVÉ\n")
        
        serve(
            app,
            host='0.0.0.0',
            port=5000,
            threads=4,
            connection_limit=100,
            channel_timeout=120
        )
        
    except Exception as e:
        print(f"❌ Erreur au démarrage: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print_header("BioAccess Secure - Démarrage Production")
    
    # Vérifier PostgreSQL
    if not check_postgres():
        print("\n❌ Impossible de démarrer sans PostgreSQL")
        sys.exit(1)
    
    # Initialiser la base de données
    if not init_database():
        print("\n❌ Impossible de démarrer sans base de données")
        sys.exit(1)
    
    # Démarrer Flask
    try:
        start_flask()
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt du serveur")
        sys.exit(0)

if __name__ == '__main__':
    main()
