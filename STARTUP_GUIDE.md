# 🚀 BioAccess Secure - Guide de Démarrage Production

## ✅ Vérifications préalables

Avant de démarrer le système, vérifiez que tout est configuré:

```bash
python verify_system.py
```

## 📋 Prérequis

1. **Python 3.11 ou 3.12** (NOT 3.14 - SQLAlchemy issues)
   ```bash
   python --version
   ```

2. **PostgreSQL 15+** installé et en cours d'exécution
   - Server: localhost:5432
   - Admin user: postgres / postgres
   - Database: bioaccess (créé automatiquement)
   - User: bioaccess_user / secure_password

3. **Redis 7+** (optionnel mais recommandé)
   - Server: localhost:6379

4. **Dependencies Python** installées
   ```bash
   pip install -r BACKEND/requirements.txt
   ```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BIOACCESS SECURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌──────────────────────────┐    │
│  │  Frontend (Web)  │      │  Client Desktop (Win)    │    │
│  │  Port: 5500      │      │  Reconnaissance facial   │    │
│  │  (HTML/JS/CSS)   │      │  Enrollment biométrique  │    │
│  └────────┬─────────┘      └──────────────┬───────────┘    │
│           │                               │                │
│           └───────────────────┬───────────┘                │
│                               │                            │
│                        HTTP:5000                           │
│                               │                            │
│  ┌────────────────────────────▼──────────────────────────┐ │
│  │         Backend Flask API (Production)                 │ │
│  │  - Authentification (JWT)                              │ │
│  │  - Biométrie (Facial, Vocal)                           │ │
│  │  - Gestion accès                                       │ │
│  │  - Logs & Alertes                                      │ │
│  └──────────┬─────────────────────────────┬──────────────┘ │
│             │                             │                │
│    ┌────────▼──────────┐      ┌──────────▼────────────┐   │
│    │  PostgreSQL DB    │      │  Door System API       │   │
│    │  (bioaccess)      │      │  (Raspberry Pi)       │   │
│    │  14 tables        │      │  Reconnaissance vocale│   │
│    │  + Foreign Keys   │      │  Contrôle portes       │   │
│    └───────────────────┘      └───────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 Mode Production vs Développement

### Configuration actuelle: PRODUCTION

**Fichier**: `.env`
```
FLASK_ENV=production
FLASK_DEBUG=0
DATABASE_URL=postgresql://bioaccess_user:secure_password@localhost:5432/bioaccess
REDIS_ENABLED=True
SESSION_COOKIE_SECURE=True
```

### Bases de données

- **Dev**: SQLite (bioaccess.db)
- **Prod**: PostgreSQL (bioaccess) ✅ ACTUELLEMENT CONFIGURÉ

## 📊 Tables créées automatiquement

| Table | Colonnes | Foreign Keys |
|-------|----------|--------------|
| users | 21 | - |
| admins | 3 | users(id) |
| employes | 4 | users(id), employes(manager_id) |
| templates_biometriques | 7 | users(id) |
| phrases_aleatoires | 6 | users(id) |
| tentatives_auth | 10 | users, templates, phrases |
| authentication_attempts | 9 | users(id) |
| postes_travail | 10 | employes(id) |
| portes | 8 | phrases(id) |
| configurations | 7 | admins(id) |
| logs_acces | 13 | users(id) |
| alertes | 20 | users, logs |
| user_sessions | 10 | users(id) |
| login_logs | 10 | users(id) |

## 🔒 Sécurité en Production

✅ Activé:
- HTTPS (SESSION_COOKIE_SECURE=True)
- CSRF Protection
- Rate Limiting
- JWT avec HS512
- Chiffrement des templates biométriques
- Audit logs immuables
- Validation pydantic

## 🚀 Démarrage du système

### Option 1: Script automatique (Recommandé)

```bash
cd BACKEND
python run_production.py
```

Ce script:
1. ✅ Vérifie PostgreSQL
2. ✅ Crée l'utilisateur et la base de données
3. ✅ Crée toutes les tables avec FK
4. ✅ Démarre le serveur Flask

### Option 2: Manuel

```bash
# Terminal 1 - PostgreSQL (doit tourner)
psql -U postgres
\i BACKEND/init-postgres.sql

# Terminal 2 - Backend
cd BACKEND
python run_production.py

# Terminal 3 - Client Desktop (optionnel)
cd "Client Desktop"
python maindesktop.py

# Terminal 4 - Door System (optionnel)
cd door-system
python main.py
```

## 📡 Endpoints API disponibles

### Authentification
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/logout` - Déconnexion
- `GET /api/v1/auth/me` - Profil utilisateur
- `POST /api/v1/auth/refresh` - Renouveler token

### Biométrie
- `POST /api/v1/biometric/enroll` - Enregistrer empreinte
- `POST /api/v1/biometric/verify` - Vérifier biométrie
- `GET /api/v1/biometric/templates` - Récupérer templates

### Alertes
- `POST /api/v1/alerts` - Créer alerte
- `GET /api/v1/alerts` - Lister alertes
- `PUT /api/v1/alerts/{id}` - Traiter alerte

### Logs d'accès
- `GET /api/v1/logs` - Consulter logs
- `POST /api/v1/logs` - Enregistrer log

### Accès portes
- `GET /api/v1/access/check/{user_id}` - Vérifier accès
- `POST /api/v1/access/log` - Log accès

## 🔧 Dépannage

### PostgreSQL n'est pas accessible
```bash
# Windows
pg_ctl -D "C:\Program Files\PostgreSQL\15\data" start

# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql
```

### Port 5000 déjà utilisé
```bash
# Modifier dans run_production.py
serve(app, port=5001, ...)
```

### Erreur SQLAlchemy avec Python 3.14
```bash
# Utiliser Python 3.12 à la place
python3.12 run_production.py
```

### Réinitialiser la base de données
```bash
# Supprimer et recréer
psql -U postgres
DROP DATABASE bioaccess;
DROP ROLE bioaccess_user;
# Puis relancer run_production.py
```

## 📝 Logs & Monitoring

- **Application logs**: `BACKEND/logs/bioaccess.log`
- **Audit logs**: `BACKEND/logs/audit.log`
- **Debug**: Voir console du terminal

## 🧪 Tests

```bash
# Vérifier système avant démarrage
python verify_system.py

# Tester l'API (après démarrage)
curl http://localhost:5000/api/v1/health

# Test reconnaissance faciale
curl -X POST http://localhost:5000/api/v1/biometric/verify \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test-user", "image":"base64-data"}'
```

## 🎯 Fonctionnalités disponibles

### Frontend Web (port 5500)
✅ Dashboard
✅ Gestion utilisateurs
✅ Enrollment biométrique (facial & vocal)
✅ Consultation alertes
✅ Logs d'accès
✅ Configuration système

### Client Desktop
✅ Reconnaissance faciale (OpenCV)
✅ Reconnaissance vocale (Vosk)
✅ Enrollment biométrique
✅ Logs applicatifs

### Door System (Raspberry Pi)
✅ Reconnaissance faciale
✅ Reconnaissance vocale
✅ Contrôle servo porte
✅ LED & buzzer

## 📞 Support

Pour les erreurs:
1. Consulter les logs: `tail -f BACKEND/logs/bioaccess.log`
2. Vérifier PostgreSQL: `psql -U postgres -d bioaccess`
3. Tester API: `curl http://localhost:5000/api/v1/health`

---

**Status**: ✅ PRODUCTION READY
**Database**: PostgreSQL (bioaccess)
**Mode**: Secure, Scalable, Audited
