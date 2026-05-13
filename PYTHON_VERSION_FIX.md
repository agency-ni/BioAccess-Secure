# 🔧 CONFIGURATION PYTHON REQUISE

## ⚠️ PROBLÈME CONNU: Python 3.14 + SQLAlchemy

Le système est actuellement configuré avec Python 3.14, mais SQLAlchemy 2.0.30 
n'est pas compatible avec Python 3.14 (problèmes de typing).

## ✅ SOLUTION: Installer Python 3.12

### Option 1: Windows (Recommandé)

Téléchargez Python 3.12.x depuis https://www.python.org/downloads/

Ou utilisez le Microsoft Store:
```powershell
winget install Python.Python.3.12
```

### Option 2: Utiliser uv (Gestionnaire Python)

```bash
# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Créer un environnement avec Python 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\activate   # Windows
```

### Option 3: Installer via pyenv (Linux/Mac)

```bash
brew install pyenv
pyenv install 3.12.1
pyenv global 3.12.1
```

## 📝 Après Installation de Python 3.12

Réinstallez les dépendances:

```bash
cd BACKEND
pip install --user -r requirements.txt

# Redémarrez le système
python start_production.py
```

## 🚀 Alternative: Utiliser le serveur Flask minimaliste

Si vous ne pouvez pas installer Python 3.12, utilisez le serveur simplifié:

```bash
cd BACKEND
python start_production.py
```

Ce serveur:
- ✅ Démarre sur port 5000
- ✅ N'utilise pas SQLAlchemy (évite le problème Python 3.14)
- ✅ Fournit les endpoints API de base
- ✅ Prêt pour l'intégration avec PostgreSQL

Les endpoints disponibles:
- GET  /api/v1/health
- POST /api/v1/auth/login
- POST /api/v1/biometric/enroll
- POST /api/v1/biometric/verify
- GET/POST /api/v1/alerts
- GET/POST /api/v1/logs

## 📊 Compatibilité

| Python | SQLAlchemy | Status |
|--------|-----------|--------|
| 3.9    | 2.0.x     | ✅ OK |
| 3.10   | 2.0.x     | ✅ OK |
| 3.11   | 2.0.x     | ✅ OK |
| 3.12   | 2.0.x     | ✅ OK ← Recommandé |
| 3.13   | 2.0.x     | ⚠️ Problèmes |
| 3.14   | 2.0.x     | ❌ Incompatible |

## 🎯 Recommandation

1. Installez Python 3.12.x
2. Recréez l'environnement avec pip
3. Utilisez `python run_production.py` (version complète avec DB)

OU

Utilisez `python start_production.py` pour une version minimale qui fonctionne maintenant.
