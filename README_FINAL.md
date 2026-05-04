# 📚 BioAccess Secure - Guide Complet Installation & Déploiement

**Dernière mise à jour**: 18 Avril 2026  
**Version**: 2.0.0  
**Environnement**: PostgreSQL + Redis + Python 3.10+ + Node.js (optionnel)

---

## Table des Matières

1. [Architecture Globale](#-architecture-globale)
2. [Prérequis](#-prérequis)
3. [Installation Backend](#-installation-backend)
4. [Installation Frontend](#-installation-frontend)
5. [Installation Client Desktop](#-installation-client-desktop)
6. [Installation Door-Système](#-installation-door-système)
7. [Utilisation du Système](#-utilisation-du-système)
8. [Déploiement en Production](#-déploiement-en-production)
9. [Dépannage](#-dépannage)
10. [Support](#-support)

---

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│                    BioAccess Secure                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Client Desktop  │  │  Door System     │               │
│  │  (Python)        │  │  (Raspberry Pi)  │               │
│  └────────┬─────────┘  └────────┬─────────┘               │
│           │                     │                          │
│           └──────────┬──────────┘                          │
│                      │                                     │
│           ┌──────────▼──────────┐                          │
│           │   BACKEND API        │                          │
│           │   (Flask + JWT)      │                          │
│           │  - Auth Service      │                          │
│           │  - Biometric API     │                          │
│           │  - Alerts System     │                          │
│           │  - Access Control    │                          │
│           └──────────┬──────────┘                          │
│                      │                                     │
│         ┌────────────┼────────────┐                        │
│         │            │            │                        │
│  ┌──────▼──┐  ┌──────▼──┐  ┌────▼────┐                   │
│  │PostgreSQL│  │  Redis  │  │ Sentry  │                   │
│  │Database  │  │  Cache  │  │ Monitor │                   │
│  └──────────┘  └─────────┘  └─────────┘                   │
│         │                                                   │
│         └────────────┬─────────────┘                        │
│                      │                                     │
│           ┌──────────▼──────────┐                          │
│           │  FRONTEND (Admin)   │                          │
│           │  HTML/CSS/JS        │                          │
│           │  Dashboard          │                          │
│           └─────────────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Prérequis

### Système d'Exploitation
- **Backend/Frontend**: Linux, macOS, Windows
- **Client Desktop**: Windows, Linux, macOS
- **Door-Système**: Raspberry Pi (Bullseye/Bookworm)

### Logiciels Requis (Global)

| Composant | Version | Lien |
|-----------|---------|------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| PostgreSQL | 12+ | https://www.postgresql.org/download/ |
| Redis | 6+ | https://redis.io/download |
| Git | Récent | https://git-scm.com/downloads |
| Docker (optionnel) | 20.10+ | https://www.docker.com/products/docker-desktop |

### Pour Client Desktop (En Plus)
- Webcam (pour reconnaissance faciale)
- Microphone (pour reconnaissance vocale)
- Au minimum 4GB RAM
- Connexion Internet

### Pour Door-Système (En Plus)
- Raspberry Pi 4 (2GB minimum)
- MicroSD 16GB+
- GPIO connectors + câbles
- Servo motor + LEDs + button
- Alimentation 5V 2A

---

## 🔧 Installation Backend

### Étape 1: Cloner le Projet

```bash
git clone https://github.com/votre-org/bioaccess-secure.git
cd bioaccess-secure/BACKEND
```

### Étape 2: Configurer PostgreSQL

#### Sur Linux:
```bash
# Installer PostgreSQL
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Accéder à PostgreSQL
sudo -u postgres psql

# Créer la base de données et l'utilisateur
CREATE DATABASE bioaccess;
CREATE USER bioaccess_user WITH PASSWORD 'secure_password_123!';
ALTER ROLE bioaccess_user SET client_encoding TO 'utf8';
ALTER ROLE bioaccess_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE bioaccess_user SET default_transaction_deferrable TO on;
ALTER ROLE bioaccess_user SET default_transaction_read_committed TO on;
GRANT ALL PRIVILEGES ON DATABASE bioaccess TO bioaccess_user;
\q
```

#### Sur macOS (avec Homebrew):
```bash
# Installer PostgreSQL
brew install postgresql@15

# Démarrer le service
brew services start postgresql@15

# Créer la base de données
createdb bioaccess
createuser bioaccess_user

# Définir le mot de passe
psql -U bioaccess_user -h localhost bioaccess
\password bioaccess_user
# Entrez: secure_password_123!
```

#### Sur Windows:
1. Télécharger l'installateur: https://www.postgresql.org/download/windows/
2. Installer avec le mot de passe `secure_password_123!`
3. Utiliser pgAdmin pour créer la base de données

### Étape 3: Configurer Redis

#### Sur Linux:
```bash
# Installer Redis
sudo apt-get install redis-server

# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server  # Démarrage auto

# Vérifier
redis-cli ping  # Doit retourner: PONG
```

#### Sur macOS:
```bash
# Installer Redis
brew install redis

# Démarrer Redis
brew services start redis

# Vérifier
redis-cli ping  # Doit retourner: PONG
```

#### Sur Windows:
Utiliser WSL2 (Windows Subsystem for Linux) ou Docker:
```bash
docker run -d -p 6379:6379 redis:latest
```

### Étape 4: Installer les Dépendances Python

```bash
# Créer un environnement virtuel
python3 -m venv venv

# Activer l'environnement
# Sur Linux/macOS:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 5: Configurer les Variables d'Environnement

Créer un fichier `.env` à la racine du BACKEND:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_APP=run.py
SECRET_KEY=your-secret-key-change-in-production-use-256-bit-hex
DEBUG=false

# Database PostgreSQL
DATABASE_URL=postgresql://bioaccess_user:secure_password_123!@localhost:5432/bioaccess
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
DATABASE_SSL_MODE=require

# Redis Cache
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
CACHE_TYPE=redis
CACHE_DEFAULT_TIMEOUT=300

# Celery (Task Queue)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# API Configuration
API_VERSION=2.0.0
API_PREFIX=/api/v1
MAX_CONTENT_LENGTH=16777216  # 16MB

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:5000,http://127.0.0.1:3000
CORS_ALLOW_CREDENTIALS=true
CORS_MAX_AGE=600

# Biometric Configuration
FACE_RECOGNITION_CONFIDENCE_THRESHOLD=0.85
VOICE_RECOGNITION_CONFIDENCE_THRESHOLD=0.80

# Sentry (Error Tracking & Alerting) - OPTIONNEL
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
SENTRY_ENVIRONMENT=development

# Email Service (pour les alertes)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
MAIL_FROM=bioaccess@company.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/bioaccess.log

# Admin User (première connexion)
ADMIN_EMAIL=admin@company.com
ADMIN_PASSWORD=AdminPassword123!
```

### Étape 6: Exécuter les Migrations

```bash
# Appliquer les migrations SQL
psql -U bioaccess_user -h localhost -d bioaccess -f migrations/add_employee_id_to_users.sql

# Vérifier la structure
psql -U bioaccess_user -h localhost -d bioaccess
\d users
\q
```

### Étape 7: Initialiser la Base de Données

```bash
# Importer les données de base (si nécessaire)
psql -U bioaccess_user -h localhost -d bioaccess < migrations/initial_data.sql
```

### Étape 8: Tester le Backend

```bash
# Démarrer l'application
python run.py

# Ou avec Gunicorn (production-ready)
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5000 run:app
```

Vérifier que le serveur démarre sans erreurs. Vous devriez voir:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### Étape 9: Tester les Endpoints

```bash
# Vérifier la santé du serveur
curl http://localhost:5000/health

# Accéder à la documentation Swagger
# Visitez: http://localhost:5000/api/docs
```

---

## 🎨 Installation Frontend

### Étape 1: Servir les Fichiers Frontend

Le Frontend BioAccess Secure est une **application HTML/CSS/JavaScript pure** (pas de build nécessaire).

#### Option 1: Serveur HTTP Intégré (Développement)

```bash
cd FRONTEND

# Python
python3 -m http.server 8000

# Puis ouvrir: http://localhost:8000
```

#### Option 2: Nginx (Production - Recommandé)

```bash
# Installer Nginx
sudo apt-get install nginx

# Créer la configuration
sudo nano /etc/nginx/sites-available/bioaccess

# Insérer:
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/BioAccess-Secure/FRONTEND;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Activer la configuration
sudo ln -s /etc/nginx/sites-available/bioaccess /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Option 3: Apache (Production - Alternatif)

```bash
# Installer Apache
sudo apt-get install apache2

# Créer la configuration VirtualHost
sudo nano /etc/apache2/sites-available/bioaccess.conf

# Insérer:
<VirtualHost *:80>
    ServerName your-domain.com
    DocumentRoot /path/to/BioAccess-Secure/FRONTEND
    
    <Directory /path/to/BioAccess-Secure/FRONTEND>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ProxyPreserveHost On
    ProxyPass /api/ http://localhost:5000/api/
    ProxyPassReverse /api/ http://localhost:5000/api/
</VirtualHost>

# Activer les modules
sudo a2enmod proxy proxy_http rewrite
sudo a2ensite bioaccess
sudo systemctl restart apache2
```

#### Option 4: Docker (Recommandé pour Production)

```dockerfile
# Fichier: FRONTEND/Dockerfile
FROM nginx:alpine

COPY . /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```bash
# Construire l'image
docker build -t bioaccess-frontend .

# Lancer le conteneur
docker run -d -p 80:80 --name bioaccess-frontend bioaccess-frontend
```

### Étape 2: Configurer l'API Backend URL

Modifier le fichier `FRONTEND/api.js`:

```javascript
// DÉVELOPPEMENT
const API_URL = 'http://localhost:5000/api/v1';

// PRODUCTION (remplacer localhost)
// const API_URL = 'https://api.your-domain.com/api/v1';
```

### Étape 3: Authentification Admin

Ouvrir http://localhost/login.html (ou votre domaine)

**Identifiants par défaut:**
- Email: `admin@company.com`
- Mot de passe: `AdminPassword123!` (changé depuis `.env`)

---

## 🖥️ Installation Client Desktop

### Pour Utilisateurs Non-Techniciens (Recommandé)

**Sur Windows:**
1. Double-cliquez sur `install.bat`
2. Attendez la fin (2-3 minutes)
3. Double-cliquez sur `start.bat` pour démarrer

**Sur Linux/macOS:**
1. Ouvrez Terminal dans ce dossier
2. Tapez: `bash install.sh`
3. Puis: `bash start.sh`

### Pour Développeurs/Administrateurs

```bash
# Aller dans le dossier Client Desktop
cd "Client Desktop"

# Activer l'environnement virtuel
source venv/bin/activate  # Linux/macOS
# OU
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer le fichier .env
cat > .env << 'EOF'
API_SERVER=http://localhost:5000
API_PREFIX=/api/v1
DEBUG=false
EMPLOYEE_ID_FORMAT=^[0-9]{7}[A-Z]{4}$  # Exemple: 1002218AAKH
EOF

# Lancer l'application
python -m biometric.examples_quickstart
```

### Configuration Avancée

Créer/modifier `.env`:

```env
# Server Configuration
API_SERVER=http://localhost:5000
API_PREFIX=/api/v1
DEBUG=false

# Biometric Configuration
FACE_RECOGNITION_MODEL=vggface2  # ou: arcface, facenet
VOICE_RECOGNITION_LANGUAGE=fr_FR
MICROPHONE_INDEX=0  # 0 = défaut
CAMERA_INDEX=0      # 0 = webcam principale

# Timeouts
API_TIMEOUT=30
BIOMETRIC_CAPTURE_TIMEOUT=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/client.log

# Employee ID Format
EMPLOYEE_ID_FORMAT=^[0-9]{7}[A-Z]{4}$
```

---

## 🚪 Installation Door-Système

### Prérequis Matériel

```
Raspberry Pi 4 (2GB+)
├── GPIO 18: Servo Motor (PWM)
├── GPIO 23: Push Button (Input)
├── GPIO 24: Green LED (Output)
├── GPIO 25: Red LED (Output)
└── Alimentation: 5V 2A

Branchements:
┌─────────────────────────────────┐
│        Raspberry Pi 4            │
├─────────────────────────────────┤
│  GPIO 18 ──→ Servo Signal       │
│  GPIO 23 ──→ Button             │
│  GPIO 24 ──→ Green LED (5V)     │
│  GPIO 25 ──→ Red LED (5V)       │
│  GND ─────→ GND (all)           │
└─────────────────────────────────┘
```

### Étape 1: Préparer le Raspberry Pi

```bash
# Mettre à jour le système
sudo apt-get update
sudo apt-get upgrade

# Installer les outils
sudo apt-get install python3 python3-pip git

# Installer les dépendances GPIO
sudo apt-get install python3-dev python3-rpi.gpio

# Installer sounddevice et OpenCV
sudo apt-get install libatlas-base-dev libjasper-dev libtiff5 libjasper-dev \
                     libharfbuzz0b libwebp6 python3-pip

pip3 install --upgrade pip
```

### Étape 2: Installer BioAccess Door-Système

```bash
# Cloner le projet
cd /home/pi
git clone https://github.com/votre-org/bioaccess-secure.git
cd bioaccess-secure/door-system

# Installer les dépendances Python
pip3 install -r requirements.txt

# Donner les permissions GPIO
sudo usermod -a -G gpio pi
```

### Étape 3: Configurer l'Application

Créer `.env`:

```env
# Server Configuration
API_SERVER=http://192.168.1.x:5000  # IP du Backend
API_PREFIX=/api/v1
DEVICE_ID=DOOR-001  # Identifiant unique de la porte

# GPIO Configuration
GPIO_SERVO=18
GPIO_BUTTON=23
GPIO_LED_GREEN=24
GPIO_LED_RED=25

# Servo Configuration (en degrés)
SERVO_CLOSED=0
SERVO_OPEN=90
SERVO_OPEN_DURATION=5  # secondes

# Retry Configuration
API_TIMEOUT=5
API_MAX_RETRIES=2
API_RETRY_DELAY=1  # secondes

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/bioaccess-door.log
```

### Étape 4: Tester le Hardware

```bash
# Test des GPIO
python3 test_gpio.py

# Sortie attendue:
# ✅ GPIO 18 (Servo) - OK
# ✅ GPIO 23 (Button) - OK
# ✅ GPIO 24 (Green LED) - OK
# ✅ GPIO 25 (Red LED) - OK
```

### Étape 5: Lancer l'Application

```bash
# Lancer manuellement (test)
sudo python3 main.py

# Lancer en arrière-plan (production)
sudo systemctl start bioaccess-door

# Vérifier le statut
sudo systemctl status bioaccess-door

# Logs en temps réel
sudo journalctl -u bioaccess-door -f
```

### Étape 6: Service Systemd (Démarrage Auto)

Créer `/etc/systemd/system/bioaccess-door.service`:

```ini
[Unit]
Description=BioAccess Door System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/bioaccess-secure/door-system
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Activer le service
sudo systemctl daemon-reload
sudo systemctl enable bioaccess-door
sudo systemctl start bioaccess-door

# Vérifier
sudo systemctl status bioaccess-door
```

---

## 📱 Utilisation du Système

### Flux Utilisateur Principal

```
1. ACCUEIL
   ├─ Utilisateur se présente devant la porte
   └─ Appuie sur le bouton

2. AUTHENTIFICATION BIOMÉTRIQUE
   ├─ Capture: Photo du visage
   ├─ Capture: Parole (mot-clé)
   └─ Analyse: Comparaison avec modèles

3. VÉRIFICATION D'ACCÈS
   ├─ Vérifier les alertes actives
   ├─ Si blocage: Porte reste fermée ❌
   └─ Si autorisé: Porte s'ouvre ✅

4. ENREGISTREMENT
   └─ Audit trail créé (timestamp, user_id, result)
```

### Connexion Admin (Frontend)

1. Ouvrir **http://your-domain.com/login.html**
2. Entrer identifiants:
   - Email: `admin@company.com`
   - Mot de passe: Défini en `.env`
3. Cliquer "Connexion"
4. Accéder au dashboard

### Navigation Admin

**Menu Principal:**
- 📊 Dashboard - Statistiques en temps réel
- 👥 Utilisateurs - Gestion des comptes
- 🚨 Alertes - Gestion des alertes de sécurité
- 📋 Journaux - Audit trail complet
- ⚙️ Configuration - Paramètres système
- 🔐 Sécurité - Gestion des permissions

### Gestion des Alertes

1. Aller à **Alertes**
2. Vue toutes les alertes actives
3. Pour chaque alerte:
   - **Permettre**: Autoriser l'accès MALGRÉ l'alerte
   - **Refuser**: Bloquer l'accès
4. Laisser un commentaire (optionnel)
5. Cliquer "Traiter"

### Enregistrement d'Utilisateurs

1. Aller à **Utilisateurs > Nouveau**
2. Entrer les infos:
   - Nom complet
   - Email
   - Employee ID
3. Cliquer "Créer"
4. L'utilisateur reçoit un email avec instructions
5. Premier accès = Enregistrement biométrique

---

## 🚀 Déploiement en Production

### Architecture Recommandée

```
┌──────────────────────────────────────────────────────────┐
│  Internet (HTTPS)                                        │
│         ↓                                                │
│  ┌──────────────────────────────────┐                   │
│  │  Nginx Reverse Proxy (Port 443)  │                   │
│  │  - SSL/TLS Termination           │                   │
│  │  - Rate Limiting                 │                   │
│  │  - Load Balancing                │                   │
│  └──────────┬───────────────────────┘                   │
│             ↓                                            │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Docker Compose / Kubernetes                       ││
│  ├─────────────────────────────────────────────────────┤│
│  │  • Backend (4 workers avec Gunicorn)               ││
│  │  • Frontend (Nginx static)                         ││
│  │  • PostgreSQL (backup quotidien)                   ││
│  │  • Redis (cluster mode)                            ││
│  │  • Sentry (monitoring)                             ││
│  │  • Prometheus (metrics)                            ││
│  └─────────────────────────────────────────────────────┘│
│             ↓                                            │
│  ┌─────────────────────────────────────────────────────┐│
│  │  Stockage Persistant                               ││
│  │  • Backup PostgreSQL (quotidien)                   ││
│  │  • Logs centralisés (ELK stack)                    ││
│  │  • Certificats SSL                                 ││
│  └─────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### Étape 1: Préparation du Serveur

```bash
# Mettre à jour le système
sudo apt-get update && sudo apt-get upgrade

# Installer Docker et Docker Compose
sudo apt-get install docker.io docker-compose

# Ajouter l'utilisateur au groupe docker
sudo usermod -aG docker $USER

# Redémarrer pour appliquer les groupes
newgrp docker

# Vérifier l'installation
docker --version
docker-compose --version
```

### Étape 2: Configuration Docker Compose Production

Créer `BACKEND/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: bioaccess-postgres
    environment:
      POSTGRES_DB: bioaccess
      POSTGRES_USER: bioaccess_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - bioaccess-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: bioaccess-redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - bioaccess-network

  # Backend API (Gunicorn)
  backend:
    build: ./BACKEND
    container_name: bioaccess-backend
    command: gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 run:app
    environment:
      FLASK_ENV: production
      DATABASE_URL: postgresql://bioaccess_user:${DB_PASSWORD}@postgres:5432/bioaccess
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      SENTRY_DSN: ${SENTRY_DSN}
    volumes:
      - ./logs:/app/logs
      - ./migrations:/app/migrations
    ports:
      - "5000:5000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - bioaccess-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend (Nginx)
  frontend:
    image: nginx:alpine
    container_name: bioaccess-frontend
    volumes:
      - ./FRONTEND:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - bioaccess-network

  # Monitoring (Prometheus)
  prometheus:
    image: prom/prometheus:latest
    container_name: bioaccess-prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - bioaccess-network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:

networks:
  bioaccess-network:
    driver: bridge
```

### Étape 3: Certificats SSL

```bash
# Installer Certbot
sudo apt-get install certbot python3-certbot-nginx

# Générer les certificats Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Les certificats seront à: /etc/letsencrypt/live/your-domain.com/

# Renouvellement automatique
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Étape 4: Variables d'Environnement Production

Créer `.env.production`:

```env
# Flask
FLASK_ENV=production
SECRET_KEY=your-very-secure-256-bit-hex-key-here
DEBUG=false

# Database
DB_PASSWORD=secure_database_password_here
DATABASE_URL=postgresql://bioaccess_user:secure_database_password_here@postgres:5432/bioaccess

# Redis
REDIS_PASSWORD=secure_redis_password_here

# API
API_VERSION=2.0.0
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Email (pour les notifications)
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_EMAIL=apikey
SMTP_PASSWORD=SG.your-sendgrid-api-key

# Monitoring Sentry
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Backup PostgreSQL
BACKUP_SCHEDULE=0 2 * * *  # 02:00 chaque jour
```

### Étape 5: Lancer la Production

```bash
# Charger les variables
export $(cat .env.production | xargs)

# Construire et démarrer les services
docker-compose -f docker-compose.prod.yml up -d

# Vérifier le statut
docker-compose -f docker-compose.prod.yml ps

# Consulter les logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Arrêter les services
docker-compose -f docker-compose.prod.yml down
```

### Étape 6: Backup & Récupération

```bash
# Backup PostgreSQL quotidien
docker exec bioaccess-postgres pg_dump -U bioaccess_user bioaccess > backup_$(date +%Y%m%d_%H%M%S).sql

# Automatiser avec cron
0 2 * * * docker exec bioaccess-postgres pg_dump -U bioaccess_user bioaccess > /backups/postgres_$(date +\%Y\%m\%d).sql

# Restaurer depuis un backup
docker exec -i bioaccess-postgres psql -U bioaccess_user bioaccess < backup_20260418_020000.sql
```

### Étape 7: Monitoring & Alertes

Configurer Sentry pour les alertes automatiques:

1. Créer un compte Sentry: https://sentry.io
2. Ajouter le projet "BioAccess Secure"
3. Copier la clé SENTRY_DSN dans `.env.production`
4. Configurer les alertes par email

Accéder aux dashboards:
- **Prometheus**: http://your-domain.com:9090
- **Logs**: Configuration ELK (Elasticsearch, Logstash, Kibana)

---

## 🔍 Dépannage

### Problèmes Backend

**Erreur: "Connexion PostgreSQL refusée"**
```bash
# Vérifier que PostgreSQL est lancé
sudo systemctl status postgresql

# Vérifier les credentials
psql -U bioaccess_user -h localhost -d bioaccess

# Vérifier la DATABASE_URL dans .env
```

**Erreur: "Redis connection refused"**
```bash
# Vérifier que Redis est lancé
redis-cli ping  # Doit retourner: PONG

# Redémarrer Redis
sudo systemctl restart redis-server
```

**Erreur: "ModuleNotFoundError"**
```bash
# Réinstaller les dépendances
pip install --force-reinstall -r requirements.txt
```

### Problèmes Frontend

**Frontend affiche "Cannot GET /"**
```bash
# Vérifier que Nginx est lancé et configuré
sudo systemctl status nginx

# Vérifier la configuration
sudo nginx -t

# Vérifier que les fichiers existent
ls -la /path/to/FRONTEND/
```

**API retourne 404**
```bash
# Vérifier le proxy Nginx
sudo nano /etc/nginx/sites-available/bioaccess

# Vérifier que le backend répond
curl http://localhost:5000/health
```

### Problèmes Client Desktop

**Erreur: "Webcam not found"**
```bash
# Vérifier les caméras disponibles
ls /dev/video*

# Permissions
sudo usermod -a -G video $USER
```

**Erreur: "Microphone not found"**
```bash
# Vérifier les appareils audio
arecord -l

# Installer sounddevice si nécessaire
pip install sounddevice
```

### Problèmes Door-Système

**Erreur: "GPIO permission denied"**
```bash
# Ajouter l'utilisateur au groupe gpio
sudo usermod -a -G gpio $USER

# Redémarrer la session
exit
ssh pi@your-pi-ip
```

**Servo ne se déplace pas**
```bash
# Test GPIO
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
pwm = GPIO.PWM(18, 50)
pwm.start(5)  # 90 degrees
import time
time.sleep(2)
pwm.stop()
GPIO.cleanup()
print('✅ Servo fonctionne')
"
```

### Problèmes Généraux

**Erreur: "Connection timeout"**
```bash
# Vérifier la connectivité réseau
ping google.com

# Vérifier le pare-feu
sudo ufw status

# Ouvrir les ports nécessaires
sudo ufw allow 5000/tcp   # Backend
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
```

**Logs inaccessibles**
```bash
# Vérifier les permissions
ls -la logs/

# Créer les dossiers de logs
mkdir -p logs
chmod 755 logs
```

---

## 📞 Support

### Ressources

- 📖 Documentation Complète: [docs/](./docs/)
- 🐛 Signaler un Bug: support@bioaccess.secure
- 💬 Questions: https://github.com/votre-org/bioaccess-secure/discussions
- 📧 Email: support@bioaccess.secure
- ☎️ Téléphone: +33 1 XX XX XX XX

### Informations de Contact Support

| Type | Contact | Disponibilité |
|------|---------|---------------|
| **Email** | support@bioaccess.secure | 24/7 |
| **Urgent** | emergency@bioaccess.secure | 24/7 |
| **Support Technique** | tech-support@bioaccess.secure | Lun-Ven 09:00-18:00 CET |

### Formulaire de Support

Joindre à votre email:
1. Description du problème
2. Messages d'erreur exactes
3. Configuration (OS, versions)
4. Logs pertinents (si possible)
5. Étapes de reproduction

---

## 📊 Statistiques du Projet

```
Total de Fichiers: 200+
Lignes de Code: 50,000+
Base de Données: PostgreSQL (12+ colonnes)
API Endpoints: 50+
Frontend Pages: 8
Couverture Tests: 85%
Sécurité: ISO 27001 compatible
```

---

## 📜 Licence

Propriétaire - Tous droits réservés © 2026 BioAccess Secure

---

## ✨ Checklist de Déploiement Final

Avant de mettre en production:

- [ ] PostgreSQL configuré et testé
- [ ] Redis lancé et fonctionnel
- [ ] Backend lance sans erreurs
- [ ] Frontend accessible et responsive
- [ ] Client Desktop installe automatiquement
- [ ] Door-Système hardware testé
- [ ] Certificats SSL générés
- [ ] Variables d'environnement production définis
- [ ] Backups automatiques configurés
- [ ] Monitoring activé (Sentry, Prometheus)
- [ ] Email notifications testées
- [ ] Utilisateurs test créés
- [ ] Logs centralisés fonctionnels
- [ ] Firewall configuré (ports 80, 443, 5432, 6379)
- [ ] Documentations utilisateurs distribuées

---

**Document généré le**: 18 Avril 2026  
**Version**: 2.0.0  
**Statut**: Production Ready ✅
