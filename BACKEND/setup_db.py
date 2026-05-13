#!/usr/bin/env python3
"""
Script de réinitialisation complète de la base de données BioAccess-Secure.

Usage:
    cd BACKEND
    python setup_db.py

Ce script :
  1. Supprime toutes les tables existantes (DROP ALL)
  2. Recrée toutes les tables depuis les modèles SQLAlchemy (CREATE ALL)
  3. Crée un utilisateur super_admin de test
  4. Seed les 20 phrases aléatoires vocales
"""

import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

# Assurer que le dossier BACKEND est dans le path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / '.env')

from app import create_app
from core.database import db

# ─────────────────────────────────────────────────────────
# Importer TOUS les modèles pour que SQLAlchemy les connaisse
# avant db.create_all()
# ─────────────────────────────────────────────────────────
from models.user import User, Admin, Employe, UserSession, LoginLog
from models.biometric import (
    TemplateBiometrique, PhraseAleatoire, TentativeAuth,
    AuthenticationAttempt, BiometricErrorLog
)
from models.log import LogAcces, Alerte
from models.access_point import PosteTravail, Porte, Configuration
from models.report import Rapport, rapport_logs


def reset_database(app):
    """Supprime et recrée toutes les tables via DROP CASCADE (sans privilèges superuser)."""
    with app.app_context():
        print("🗑️  Suppression des tables existantes (DROP CASCADE)...")

        # Tables dans l'ordre inverse des dépendances FK
        tables_ordered = [
            'rapport_logs', 'rapports',
            'alertes', 'logs_acces',
            'configurations', 'portes', 'postes_travail',
            'authentication_attempts', 'biometric_error_logs',
            'tentatives_auth', 'phrases_aleatoires', 'templates_biometriques',
            'login_logs', 'user_sessions',
            'employes', 'admins', 'users',
        ]

        try:
            with db.engine.connect() as conn:
                with conn.begin():
                    # Supprimer les index orphelins connus avant les tables
                    orphan_indexes = [
                        'ix_authentication_attempts_timestamp',
                        'idx_auth_user_timestamp',
                        'idx_auth_success_timestamp',
                        'idx_error_type_timestamp',
                        'idx_error_user_timestamp',
                        'idx_error_unresolved',
                    ]
                    for idx in orphan_indexes:
                        conn.execute(db.text(f'DROP INDEX IF EXISTS "{idx}"'))
                    # Supprimer les tables dans l'ordre inverse des FK
                    for table in tables_ordered:
                        conn.execute(db.text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
            print("   ✅ Tables et index supprimés")
        except Exception as e:
            print(f"   ⚠️  Erreur lors du drop: {e}")
            raise

        print("🏗️  Création des tables depuis les modèles SQLAlchemy...")
        db.create_all()
        print("   ✅ Tables créées avec toutes les FK correctes")


def seed_admin(app):
    """Crée un compte super_admin de test."""
    with app.app_context():
        print("👤 Création du compte super_admin...")

        existing = User.query.filter_by(email='admin@bioaccess.secure').first()
        if existing:
            print("   ℹ️  Admin déjà présent, on met à jour l'employee_id si absent...")
            if not existing.employee_id:
                existing.employee_id = User.generate_employee_id()
                existing.employee_id_created_at = datetime.utcnow()
                db.session.commit()
                print(f"   ✅ employee_id généré : {existing.employee_id}")
            return existing

        admin_user = User(
            id=str(uuid.uuid4()),
            nom='Admin',
            prenom='System',
            email='admin@bioaccess.secure',
            departement='Direction',
            role='super_admin',
            is_active=True,
            email_verified=True,
        )
        admin_user.set_password('Admin@2026!')
        admin_user.employee_id = User.generate_employee_id()
        admin_user.employee_id_created_at = datetime.utcnow()

        db.session.add(admin_user)
        db.session.flush()  # Obtenir l'id avant commit

        # Créer l'entrée dans la table admins
        admin_profile = Admin(
            id=admin_user.id,
            niveau_habilitation='super',
        )
        db.session.add(admin_profile)
        db.session.commit()

        print(f"   ✅ super_admin créé")
        print(f"   📧 Email    : admin@bioaccess.secure")
        print(f"   🔑 Password : Admin@2026!")
        print(f"   🪪 Employee ID : {admin_user.employee_id}")
        return admin_user


def seed_phrases(app):
    """Seed les 20 phrases de défi vocales."""
    with app.app_context():
        if PhraseAleatoire.query.count() > 0:
            print("ℹ️  Phrases déjà présentes en base")
            return

        print("📢 Ajout des phrases de défi vocales...")
        phrases = [
            "Bonjour, je suis une personne autorisée.",
            "Mon code d'accès est personnel et unique.",
            "Je reconnais les conditions d'utilisation.",
            "La sécurité biométrique est essentielle.",
            "Mon visage identifie qui je suis.",
            "Ma voix est un code de sécurité.",
            "J'accepte les politiques de confidentialité.",
            "Ces données biométriques sont protégées.",
            "L'authentification multifacteurs est forte.",
            "Mes empreintes digitales sont confidentielles.",
            "La reconnaissance faciale est précise.",
            "Je confirme mon authentification vocale.",
            "Aucun partage de données biométriques.",
            "La protection des données est prioritaire.",
            "Ces informations restent confidentielles.",
            "L'accès est contrôlé et sécurisé.",
            "Je valide cette tentative d'authentification.",
            "Mes identifiants biométriques sont uniques.",
            "La cryptographie protège mes données.",
            "L'audit trail enregistre tous les accès.",
        ]
        for texte in phrases:
            db.session.add(PhraseAleatoire(
                id=str(uuid.uuid4()),
                texte=texte,
                langue='fr',
                user_id=None,
            ))
        db.session.commit()
        print(f"   ✅ {len(phrases)} phrases ajoutées")


def verify_schema(app):
    """Vérifie que les tables et FK critiques sont bien en place."""
    with app.app_context():
        print("\n🔍 Vérification du schéma...")
        result = db.session.execute(db.text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result]
        print(f"   Tables créées ({len(tables)}) : {', '.join(tables)}")

        result = db.session.execute(db.text("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table,
                ccu.column_name AS foreign_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name;
        """))
        fks = result.fetchall()
        print(f"\n   Clés étrangères ({len(fks)}) :")
        for fk in fks:
            print(f"     {fk[1]}.{fk[2]} → {fk[3]}.{fk[4]}")


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 BioAccess-Secure — Réinitialisation de la base de données")
    print("=" * 60)

    app = create_app('development')

    reset_database(app)
    seed_admin(app)
    seed_phrases(app)
    verify_schema(app)

    print("\n" + "=" * 60)
    print("✅ Base de données prête pour les tests d'enrollment !")
    print("=" * 60)
    print("\nProchaines étapes :")
    print("  1. Démarrer le backend  : python run.py")
    print("  2. Ouvrir le dashboard  : FRONTEND/login.html")
    print("  3. Login admin          : admin@bioaccess.secure / Admin@2026!")
    print("  4. Créer un utilisateur → il reçoit son employee_id")
    print("  5. Entrer l'employee_id dans le Client Desktop")
    print("  6. Effectuer l'enrollment facial/vocal depuis le Desktop")
