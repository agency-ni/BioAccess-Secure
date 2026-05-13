#!/usr/bin/env python3
"""
Script de création des tables SQLite pour BioAccess-Secure
Utilise SQLite comme base de données temporaire pour permettre les tests

NOTE: Ce script est legacy et n'est pas destiné à la production PostgreSQL.
"""

import sqlite3
import os
import sys

def create_sqlite_tables():
    """Créer toutes les tables SQLite avec les clés étrangères"""

    db_path = os.path.join(os.path.dirname(__file__), 'bioaccess.db')

    try:
        print("🔄 Connexion à SQLite...")
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")  # Activer les clés étrangères
        cursor = conn.cursor()

        print("✅ Connexion SQLite réussie!")

        # Création des tables
        tables_sql = [
            # Table 1: users
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                departement TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                employee_id TEXT UNIQUE,
                employee_id_created_at TIMESTAMP,
                last_employee_id TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'employe',
                is_active INTEGER DEFAULT 1,
                email_verified INTEGER DEFAULT 0,
                twofa_enabled INTEGER DEFAULT 0,
                twofa_secret TEXT,
                last_login_at TIMESTAMP,
                last_login_ip TEXT,
                login_count INTEGER DEFAULT 0,
                failed_login_count INTEGER DEFAULT 0,
                locked_until TIMESTAMP
            );
            """,

            # Table 2: admins
            """
            CREATE TABLE IF NOT EXISTS admins (
                id TEXT PRIMARY KEY,
                niveau_habilitation TEXT DEFAULT 'standard',
                date_derniere_connexion TIMESTAMP,
                FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 3: employes
            """
            CREATE TABLE IF NOT EXISTS employes (
                id TEXT PRIMARY KEY,
                date_embauche DATE,
                poste_occupe TEXT,
                manager_id TEXT,
                FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (manager_id) REFERENCES employes(id) ON DELETE SET NULL
            );
            """,

            # Table 4: templates_biometriques
            """
            CREATE TABLE IF NOT EXISTS templates_biometriques (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL CHECK (type IN ('facial', 'vocal')),
                donnees BLOB NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                utilisateur_id TEXT NOT NULL,
                quality_score REAL DEFAULT 0.0,
                version INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 5: phrases_aleatoires
            """
            CREATE TABLE IF NOT EXISTS phrases_aleatoires (
                id TEXT PRIMARY KEY,
                texte TEXT NOT NULL,
                langue TEXT DEFAULT 'fr',
                utilisateur_id TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_count INTEGER DEFAULT 0,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 6: tentatives_auth
            """
            CREATE TABLE IF NOT EXISTS tentatives_auth (
                id TEXT PRIMARY KEY,
                date_heure TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                etape TEXT,
                resultat TEXT NOT NULL CHECK (resultat IN ('succes', 'echec')),
                raison_echec TEXT,
                adresse_ip TEXT,
                utilisateur_id TEXT NOT NULL,
                template_id TEXT,
                phrase_id TEXT,
                score_similarite REAL,
                temps_traitement_ms INTEGER,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (template_id) REFERENCES templates_biometriques(id) ON DELETE SET NULL,
                FOREIGN KEY (phrase_id) REFERENCES phrases_aleatoires(id) ON DELETE SET NULL
            );
            """,

            # Table 7: authentication_attempts
            """
            CREATE TABLE IF NOT EXISTS authentication_attempts (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                user_id TEXT,
                success INTEGER DEFAULT 0,
                reason TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                method TEXT DEFAULT 'password',
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 8: postes_travail
            """
            CREATE TABLE IF NOT EXISTS postes_travail (
                id TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                adresse_ip TEXT UNIQUE NOT NULL,
                systeme TEXT DEFAULT 'Windows',
                statut TEXT DEFAULT 'actif' CHECK (statut IN ('actif', 'inactif', 'verrouille')),
                employe_id TEXT UNIQUE,
                localisation TEXT,
                mac_address TEXT UNIQUE,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                os_version TEXT,
                FOREIGN KEY (employe_id) REFERENCES employes(id) ON DELETE SET NULL
            );
            """,

            # Table 9: portes
            """
            CREATE TABLE IF NOT EXISTS portes (
                id TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                localisation TEXT NOT NULL,
                statut TEXT DEFAULT 'fermee' CHECK (statut IN ('ouverte', 'fermee')),
                type_acces TEXT DEFAULT 'biometrique',
                departements_autorises TEXT,  -- JSON string
                horaires_autorises TEXT,      -- JSON string
                timeout_ouverture INTEGER DEFAULT 5,
                phrase_id TEXT,
                FOREIGN KEY (phrase_id) REFERENCES phrases_aleatoires(id) ON DELETE SET NULL
            );
            """,

            # Table 10: configurations
            """
            CREATE TABLE IF NOT EXISTS configurations (
                id TEXT PRIMARY KEY,
                cle TEXT UNIQUE NOT NULL,
                valeur TEXT NOT NULL,
                description TEXT,
                admin_id TEXT NOT NULL,
                date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                type_donnee TEXT DEFAULT 'string',
                FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE
            );
            """,

            # Table 11: logs_acces
            """
            CREATE TABLE IF NOT EXISTS logs_acces (
                id TEXT PRIMARY KEY,
                date_heure TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                type_acces TEXT NOT NULL CHECK (type_acces IN ('poste', 'porte', 'auth', 'config')),
                statut TEXT NOT NULL CHECK (statut IN ('succes', 'echec')),
                raison_echec TEXT,
                adresse_ip TEXT NOT NULL,
                utilisateur_id TEXT,
                details TEXT,  -- JSON string
                user_agent TEXT,
                resource TEXT,
                source_type TEXT DEFAULT 'DESKTOP',
                hash_precedent TEXT,
                hash_actuel TEXT UNIQUE NOT NULL,
                signature TEXT,
                FOREIGN KEY (utilisateur_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 12: alertes
            """
            CREATE TABLE IF NOT EXISTS alertes (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL CHECK (type IN ('securite', 'systeme', 'tentative')),
                gravite TEXT NOT NULL CHECK (gravite IN ('basse', 'moyenne', 'haute')),
                message TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                traitee INTEGER DEFAULT 0,
                allow_access INTEGER DEFAULT 0,
                access_modified_by TEXT,
                access_modified_at TIMESTAMP,
                titre TEXT,
                description TEXT,
                statut TEXT DEFAULT 'Non traitée',
                priorite TEXT DEFAULT 'Moyenne',
                resource TEXT DEFAULT 'general',
                utilisateur_id TEXT,
                log_id TEXT,
                assignee_id TEXT,
                date_traitement TIMESTAMP,
                commentaire TEXT,
                admin_action TEXT,
                admin_notes TEXT,
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
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                refresh_token TEXT UNIQUE,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                device_fingerprint TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table 14: login_logs
            """
            CREATE TABLE IF NOT EXISTS login_logs (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT,
                success INTEGER DEFAULT 0,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                failure_reason TEXT,
                method TEXT DEFAULT 'password',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            """,

            # Table 15: rapports
            """
            CREATE TABLE IF NOT EXISTS rapports (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                periode_debut DATE NOT NULL,
                periode_fin DATE NOT NULL,
                donnees TEXT NOT NULL,  -- JSON string
                format TEXT DEFAULT 'pdf' CHECK (format IN ('pdf', 'excel', 'csv')),
                titre TEXT NOT NULL,
                date_generation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                generateur_id TEXT NOT NULL,
                taille_fichier INTEGER,
                chemin_fichier TEXT,
                nom TEXT,
                prenom TEXT,
                FOREIGN KEY (generateur_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """,

            # Table d'association: rapport_logs
            """
            CREATE TABLE IF NOT EXISTS rapport_logs (
                rapport_id TEXT NOT NULL,
                log_id TEXT NOT NULL,
                PRIMARY KEY (rapport_id, log_id),
                FOREIGN KEY (rapport_id) REFERENCES rapports(id) ON DELETE CASCADE,
                FOREIGN KEY (log_id) REFERENCES logs_acces(id) ON DELETE CASCADE
            );
            """
        ]

        print("🏗️  Création des tables SQLite...")

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
                INSERT OR IGNORE INTO users (id, nom, prenom, email, password_hash, role, is_active, email_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                'admin-uuid-12345',
                'Admin',
                'System',
                'admin@bioaccess.secure',
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPjYQmLxE8Ue',  # password: admin123
                'super_admin',
                1,
                1
            ))

            cursor.execute("""
                INSERT OR IGNORE INTO admins (id, niveau_habilitation)
                VALUES (?, ?);
            """, ('admin-uuid-12345', 'super'))

            print("   ✅ Utilisateur admin créé: admin@bioaccess.secure / admin123")

        except Exception as e:
            print(f"   ⚠️  Erreur création admin: {e}")

        conn.commit()

        # Vérification finale
        cursor.execute("SELECT COUNT(name) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]

        print(f"\n🎉 SUCCÈS! {table_count} tables créées dans SQLite")
        print("📋 Liste des tables créées:")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        for table in tables:
            print(f"   • {table[0]}")

        cursor.close()
        conn.close()

        print(f"\n✅ Base de données SQLite créée: {db_path}")
        return True

    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Initialisation de la base de données BioAccess-Secure SQLite")
    print("=" * 60)

    success = create_sqlite_tables()

    if success:
        print("\n✅ Toutes les tables ont été créées avec succès!")
        print("🔗 Vous pouvez maintenant utiliser l'application avec SQLite.")
        print("📝 Note: Pour PostgreSQL, exécutez plus tard:")
        print("   python create_tables_postgres.py")
    else:
        print("\n❌ Échec de l'initialisation de la base de données.")
        sys.exit(1)