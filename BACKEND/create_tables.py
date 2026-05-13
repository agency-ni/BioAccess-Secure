#!/usr/bin/env python3
"""
Script Python pour créer les tables PostgreSQL de BioAccess-Secure
Utilise psycopg2 pour se connecter directement à la base de données

NOTE: Ce script est legacy. Préférez `BACKEND/init-postgres-fixed.sql` pour l'installation de la base de données.
"""

import psycopg2
from psycopg2 import sql
import sys
import os

def create_tables():
    """Créer toutes les tables PostgreSQL avec les clés étrangères"""

    # Configuration de la base de données
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'bioaccess',
        'user': 'bioaccess_user',
        'password': 'secure_password'
    }

    try:
        print("🔄 Connexion à PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        print("✅ Connexion réussie!")

        # Création des tables
        tables_sql = [
            # Table 1: users
            """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                prenom VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                departement VARCHAR(50),
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                employee_id VARCHAR(12) UNIQUE,
                employee_id_created_at TIMESTAMP,
                last_employee_id VARCHAR(12),
                password_hash VARCHAR(256) NOT NULL,
                role VARCHAR(20) DEFAULT 'employe',
                is_active BOOLEAN DEFAULT TRUE,
                email_verified BOOLEAN DEFAULT FALSE,
                twofa_enabled BOOLEAN DEFAULT FALSE,
                twofa_secret VARCHAR(32),
                last_login_at TIMESTAMP,
                last_login_ip VARCHAR(45),
                login_count INT DEFAULT 0,
                failed_login_count INT DEFAULT 0,
                locked_until TIMESTAMP
            );
            """,

            # Table 2: admins
            """
            CREATE TABLE IF NOT EXISTS admins (
                id VARCHAR(36) PRIMARY KEY,
                niveau_habilitation VARCHAR(50) DEFAULT 'standard',
                date_derniere_connexion TIMESTAMP,
                FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 3: employes
            """
            CREATE TABLE IF NOT EXISTS employes (
                id VARCHAR(36) PRIMARY KEY,
                date_embauche DATE,
                poste_occupe VARCHAR(100),
                manager_id VARCHAR(36),
                FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (manager_id) REFERENCES employes(id) ON DELETE SET NULL
            );
            """,

            # Table 4: templates_biometriques
            """
            CREATE TABLE IF NOT EXISTS templates_biometriques (
                id VARCHAR(36) PRIMARY KEY,
                type VARCHAR(20) NOT NULL CHECK (type IN ('facial', 'vocal')),
                donnees BYTEA NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                utilisateur_id VARCHAR(36) NOT NULL,
                quality_score FLOAT DEFAULT 0.0,
                version INT DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 5: phrases_aleatoires
            """
            CREATE TABLE IF NOT EXISTS phrases_aleatoires (
                id VARCHAR(36) PRIMARY KEY,
                texte VARCHAR(255) NOT NULL,
                langue VARCHAR(10) DEFAULT 'fr',
                utilisateur_id VARCHAR(36) NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_count INT DEFAULT 0,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 6: tentatives_auth
            """
            CREATE TABLE IF NOT EXISTS tentatives_auth (
                id VARCHAR(36) PRIMARY KEY,
                date_heure TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                etape VARCHAR(50),
                resultat VARCHAR(20) NOT NULL CHECK (resultat IN ('succes', 'echec')),
                raison_echec VARCHAR(255),
                adresse_ip VARCHAR(45),
                utilisateur_id VARCHAR(36) NOT NULL,
                template_id VARCHAR(36),
                phrase_id VARCHAR(36),
                score_similarite FLOAT,
                temps_traitement_ms INT,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (template_id) REFERENCES templates_biometriques(id) ON DELETE SET NULL,
                FOREIGN KEY (phrase_id) REFERENCES phrases_aleatoires(id) ON DELETE SET NULL
            );
            """,

            # Table 7: authentication_attempts
            """
            CREATE TABLE IF NOT EXISTS authentication_attempts (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                user_id VARCHAR(36),
                success BOOLEAN DEFAULT FALSE,
                reason VARCHAR(100) NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                method VARCHAR(50) DEFAULT 'password',
                ip_address VARCHAR(45),
                user_agent VARCHAR(256),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 8: postes_travail
            """
            CREATE TABLE IF NOT EXISTS postes_travail (
                id VARCHAR(36) PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                adresse_ip VARCHAR(45) UNIQUE NOT NULL,
                systeme VARCHAR(50) DEFAULT 'Windows',
                statut VARCHAR(20) DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'verrouille')),
                employe_id VARCHAR(36) UNIQUE,
                localisation VARCHAR(100),
                mac_address VARCHAR(17) UNIQUE,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                os_version VARCHAR(50),
                FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE SET NULL
            );
            """,

            # Table 9: portes
            """
            CREATE TABLE IF NOT EXISTS portes (
                id VARCHAR(36) PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                localisation VARCHAR(100) NOT NULL,
                statut VARCHAR(20) DEFAULT 'fermee' CHECK (statut IN ('ouverte', 'fermee')),
                type_acces VARCHAR(20) DEFAULT 'biometrique',
                departements_autorises JSONB,
                horaires_autorises JSONB,
                timeout_ouverture INT DEFAULT 5,
                phrase_id VARCHAR(36),
                FOREIGN KEY (phrase_id) REFERENCES phrases_aleatoires(id) ON DELETE SET NULL
            );
            """,

            # Table 10: configurations
            """
            CREATE TABLE IF NOT EXISTS configurations (
                id VARCHAR(36) PRIMARY KEY,
                cle VARCHAR(100) UNIQUE NOT NULL,
                valeur TEXT NOT NULL,
                description VARCHAR(255),
                admin_id VARCHAR(36) NOT NULL,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type_donnee VARCHAR(20) DEFAULT 'string',
                FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
            );
            """,

            # Table 11: logs_acces
            """
            CREATE TABLE IF NOT EXISTS logs_acces (
                id VARCHAR(36) PRIMARY KEY,
                date_heure TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                type_acces VARCHAR(20) NOT NULL CHECK (type_acces IN ('poste', 'porte', 'auth', 'config')),
                statut VARCHAR(20) NOT NULL CHECK (statut IN ('succes', 'echec')),
                raison_echec VARCHAR(500),
                adresse_ip VARCHAR(45) NOT NULL,
                utilisateur_id VARCHAR(36),
                details JSONB,
                user_agent VARCHAR(256),
                resource VARCHAR(100),
                source_type VARCHAR(10) DEFAULT 'DESKTOP',
                hash_precedent VARCHAR(64),
                hash_actuel VARCHAR(64) UNIQUE NOT NULL,
                signature VARCHAR(256),
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 12: alertes
            """
            CREATE TABLE IF NOT EXISTS alertes (
                id VARCHAR(36) PRIMARY KEY,
                type VARCHAR(20) NOT NULL CHECK (type IN ('securite', 'systeme', 'tentative')),
                gravite VARCHAR(20) NOT NULL CHECK (gravite IN ('basse', 'moyenne', 'haute')),
                message VARCHAR(500) NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                traitee BOOLEAN DEFAULT FALSE,
                allow_access BOOLEAN DEFAULT FALSE,
                access_modified_by VARCHAR(36),
                access_modified_at TIMESTAMP,
                titre VARCHAR(255),
                description VARCHAR(1000),
                statut VARCHAR(50) DEFAULT 'Non traitée',
                priorite VARCHAR(20) DEFAULT 'Moyenne',
                resource VARCHAR(100) DEFAULT 'general',
                utilisateur_id VARCHAR(36),
                log_id VARCHAR(36),
                assignee_id VARCHAR(36),
                date_traitement TIMESTAMP,
                commentaire TEXT,
                admin_action VARCHAR(50),
                admin_notes VARCHAR(500),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (log_id) REFERENCES logs_acces(id) ON DELETE SET NULL,
                FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (access_modified_by) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 13: user_sessions
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                session_token VARCHAR(512) UNIQUE NOT NULL,
                refresh_token VARCHAR(512) UNIQUE,
                ip_address VARCHAR(45) NOT NULL,
                user_agent VARCHAR(256),
                device_fingerprint VARCHAR(128),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 14: login_logs
            """
            CREATE TABLE IF NOT EXISTS login_logs (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(120) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                user_agent VARCHAR(256),
                success BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR(36),
                failure_reason VARCHAR(255),
                method VARCHAR(50) DEFAULT 'password',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 15: rapports
            """
            CREATE TABLE IF NOT EXISTS rapports (
                id VARCHAR(36) PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                periode_debut DATE NOT NULL,
                periode_fin DATE NOT NULL,
                donnees JSONB NOT NULL,
                format VARCHAR(20) DEFAULT 'pdf' CHECK (format IN ('pdf', 'excel', 'csv')),
                titre VARCHAR(200) NOT NULL,
                date_generation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generateur_id VARCHAR(36) NOT NULL,
                taille_fichier INT,
                chemin_fichier VARCHAR(500),
                nom VARCHAR(100),
                prenom VARCHAR(100),
                FOREIGN KEY (generateur_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table d'association: rapport_logs
            """
            CREATE TABLE IF NOT EXISTS rapport_logs (
                rapport_id VARCHAR(36) NOT NULL,
                log_id VARCHAR(36) NOT NULL,
                PRIMARY KEY (rapport_id, log_id),
                FOREIGN KEY (rapport_id) REFERENCES rapports(id) ON DELETE CASCADE,
                FOREIGN KEY (log_id) REFERENCES logs_acces(id) ON DELETE CASCADE
            );
            """
        ]

        print("🏗️  Création des tables...")

        for i, table_sql in enumerate(tables_sql, 1):
            try:
                cursor.execute(table_sql)
                print(f"   ✅ Table {i}/15 créée")
            except Exception as e:
                print(f"   ❌ Erreur table {i}: {e}")
                continue

        # Création des indexes
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
            "CREATE INDEX IF NOT EXISTS idx_employes_manager_id ON employes(manager_id);",
            "CREATE INDEX IF NOT EXISTS idx_templates_utilisateur_id ON templates_biometriques(utilisateur_id);",
            "CREATE INDEX IF NOT EXISTS idx_templates_type ON templates_biometriques(type);",
            "CREATE INDEX IF NOT EXISTS idx_phrases_utilisateur_id ON phrases_aleatoires(utilisateur_id);",
            "CREATE INDEX IF NOT EXISTS idx_tentatives_utilisateur_id ON tentatives_auth(utilisateur_id);",
            "CREATE INDEX IF NOT EXISTS idx_tentatives_date_heure ON tentatives_auth(date_heure);",
            "CREATE INDEX IF NOT EXISTS idx_tentatives_resultat ON tentatives_auth(resultat);",
            "CREATE INDEX IF NOT EXISTS idx_auth_attempts_email ON authentication_attempts(email);",
            "CREATE INDEX IF NOT EXISTS idx_auth_attempts_user_id ON authentication_attempts(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_auth_attempts_success ON authentication_attempts(success);",
            "CREATE INDEX IF NOT EXISTS idx_auth_attempts_timestamp ON authentication_attempts(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_postes_adresse_ip ON postes_travail(adresse_ip);",
            "CREATE INDEX IF NOT EXISTS idx_postes_statut ON postes_travail(statut);",
            "CREATE INDEX IF NOT EXISTS idx_postes_employe_id ON postes_travail(employe_id);",
            "CREATE INDEX IF NOT EXISTS idx_portes_statut ON portes(statut);",
            "CREATE INDEX IF NOT EXISTS idx_portes_localisation ON portes(localisation);",
            "CREATE INDEX IF NOT EXISTS idx_configurations_cle ON configurations(cle);",
            "CREATE INDEX IF NOT EXISTS idx_configurations_admin_id ON configurations(admin_id);",
            "CREATE INDEX IF NOT EXISTS idx_logs_date_heure ON logs_acces(date_heure);",
            "CREATE INDEX IF NOT EXISTS idx_logs_type_acces ON logs_acces(type_acces);",
            "CREATE INDEX IF NOT EXISTS idx_logs_statut ON logs_acces(statut);",
            "CREATE INDEX IF NOT EXISTS idx_logs_utilisateur_id ON logs_acces(utilisateur_id);",
            "CREATE INDEX IF NOT EXISTS idx_logs_hash_actuel ON logs_acces(hash_actuel);",
            "CREATE INDEX IF NOT EXISTS idx_logs_source_type ON logs_acces(source_type);",
            "CREATE INDEX IF NOT EXISTS idx_alertes_type ON alertes(type);",
            "CREATE INDEX IF NOT EXISTS idx_alertes_gravite ON alertes(gravite);",
            "CREATE INDEX IF NOT EXISTS idx_alertes_traitee ON alertes(traitee);",
            "CREATE INDEX IF NOT EXISTS idx_alertes_utilisateur_id ON alertes(utilisateur_id);",
            "CREATE INDEX IF NOT EXISTS idx_alertes_date_creation ON alertes(date_creation);",
            "CREATE INDEX IF NOT EXISTS idx_alertes_priorite ON alertes(priorite);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_session_token ON user_sessions(session_token);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);",
            "CREATE INDEX IF NOT EXISTS idx_sessions_is_active ON user_sessions(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_login_logs_email ON login_logs(email);",
            "CREATE INDEX IF NOT EXISTS idx_login_logs_user_id ON login_logs(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_login_logs_success ON login_logs(success);",
            "CREATE INDEX IF NOT EXISTS idx_login_logs_timestamp ON login_logs(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_login_logs_method ON login_logs(method);",
            "CREATE INDEX IF NOT EXISTS idx_rapports_type ON rapports(type);",
            "CREATE INDEX IF NOT EXISTS idx_rapports_date_generation ON rapports(date_generation);",
            "CREATE INDEX IF NOT EXISTS idx_rapports_generateur_id ON rapports(generateur_id);",
            "CREATE INDEX IF NOT EXISTS idx_rapports_nom ON rapports(nom);",
            "CREATE INDEX IF NOT EXISTS idx_rapports_prenom ON rapports(prenom);",
            "CREATE INDEX IF NOT EXISTS idx_rapport_logs_rapport_id ON rapport_logs(rapport_id);",
            "CREATE INDEX IF NOT EXISTS idx_rapport_logs_log_id ON rapport_logs(log_id);"
        ]

        print("🔍 Création des indexes...")
        for index_sql in indexes_sql:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"   ⚠️  Index error: {e}")

        # Insertion d'un utilisateur admin de test
        print("👤 Insertion d'un utilisateur admin de test...")
        try:
            cursor.execute("""
                INSERT INTO users (id, nom, prenom, email, password_hash, role, is_active, email_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, (
                'admin-uuid-12345',
                'Admin',
                'System',
                'admin@bioaccess.secure',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYQmLxE8Ue',  # password: admin123
                'super_admin',
                True,
                True
            ))

            cursor.execute("""
                INSERT INTO admins (id, niveau_habilitation)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING;
            """, ('admin-uuid-12345', 'super'))

            print("   ✅ Utilisateur admin créé: admin@bioaccess.secure / admin123")

        except Exception as e:
            print(f"   ⚠️  Erreur création admin: {e}")

        # Vérification finale
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
        table_count = cursor.fetchone()[0]

        print(f"\n🎉 SUCCÈS! {table_count} tables créées dans la base 'bioaccess'")
        print("📋 Liste des tables créées:")

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        for table in tables:
            print(f"   • {table[0]}")

        cursor.close()
        conn.close()

        print("\n✅ Base de données PostgreSQL initialisée avec succès!")
        return True

    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initialisation de la base de données BioAccess-Secure PostgreSQL")
    print("=" * 60)

    success = create_tables()

    if success:
        print("\n✅ Toutes les tables ont été créées avec succès!")
        print("🔗 Vous pouvez maintenant utiliser l'application avec la base de données.")
    else:
        print("\n❌ Échec de l'initialisation de la base de données.")
        print("🔍 Vérifiez la configuration PostgreSQL et les permissions.")
        sys.exit(1)