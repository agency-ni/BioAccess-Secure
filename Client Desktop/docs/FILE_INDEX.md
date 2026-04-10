# 📑 INDEX - Tous les Fichiers et Ressources

## 📂 Structure Complète

```
BioAccess-Secure/
│
├── 📁 Client Desktop/
│   ├── 🔍 device_diagnostic.py              <-- LANCER CECI EN PREMIER
│   ├── ⚙️  device_setup.py                   <-- PUIS CECI
│   ├── 🔐 permissions_manager.py
│   ├── ✔️  validate_installation.py          <-- Valider l'installation
│   ├── 📦 install_dependencies.py
│   ├── 🪟 install_permissions.bat           <-- Windows auto
│   ├── 🐧 install_permissions.sh            <-- Linux auto
│   ├── 📖 DEVICE_SETUP_GUIDE.md             <-- Lire pour la config
│   ├── 📋 CONFIGURATION_EXAMPLE.md          <-- Exemples
│   ├── logs/                                <-- Les rapports générés ici
│   └── ... (autres fichiers existants)
│
├── 📁 BACKEND/
│   ├── core/
│   │   └── biometric_permissions.py         <-- Permissions backend
│   ├── api/v1/
│   │   └── biometric.py                     <-- Routes API
│   └── ... (autres fichiers)
│
├── 📄 QUICK_START.txt                      <-- Commencer par lire CECI
├── 📄 README_SOLUTION.md                    <-- Vue d'ensemble
├── 📄 DEVELOPER_GUIDE.md                    <-- Pour développeurs
├── 📄 PERMISSIONS_AND_DEVICES_SETUP.md     <-- Spécifications
├── 📄 README_PERMISSIONS.md                <-- Permissions
└── ... (autres fichiers)
```

---

## 🗂️ Guide de Navigation

### 👤 JE SUIS UN UTILISATEUR

**Étape 1: Lire**
```
👉 QUICK_START.txt
```

**Étape 2: Installer**
```
Windows:  install_permissions.bat
Linux:    ./install_permissions.sh
macOS:    python device_setup.py
```

**Étape 3: Configurer**
```
python device_setup.py
```

**Besoin d'aide?**
```
→ Client Desktop/DEVICE_SETUP_GUIDE.md (guide complet par OS)
```

---

### 👨‍💼 JE SUIS UN ADMINISTRATEUR

**Comprendre la solution**
```
1. Lire: README_SOLUTION.md
2. Lire: PERMISSIONS_AND_DEVICES_SETUP.md
3. Lire: DEVELOPER_GUIDE.md
```

**Gérer les permissions**
```python
# Backend API
GET /api/biometric/permissions/<user_id>
GET /api/biometric/access-log
POST /api/biometric/permissions/<user_id>/grant
POST /api/biometric/permissions/<user_id>/revoke
```

**Dépanner**
```
→ Consulter logs/device_diagnostic.log
→ Consulter logs/device_*.json
```

---

### 👨‍💻 JE SUIS UN DÉVELOPPEUR

**Comprendre l'architecture**
```
1. Lire: DEVELOPER_GUIDE.md
2. Examiner: BACKEND/core/biometric_permissions.py
3. Examiner: BACKEND/api/v1/biometric.py
```

**Intégrer le client**
```python
# Importer les modules
from device_diagnostic import DeviceDiagnostic
from permissions_manager import PermissionsManager
from device_setup import DeviceSetup
```

**Intégrer le backend**
```python
# Permissions
from core.biometric_permissions import biometric_permissions, BiometricPermission

# Routes
from api.v1.biometric import register_biometric_routes
register_biometric_routes(app)
```

**Tester**
```
python validate_installation.py
```

---

## 📚 Fichiers par Catégorie

### 🎯 SCRIPTS EXÉCUTABLES (Client Desktop)

| Fichier | Type | Quand l'utiliser |
|---------|------|-----------------|
| `install_permissions.bat` | Batch | Installation auto (Windows) |
| `install_permissions.sh` | Shell | Installation auto (Linux) |
| `install_dependencies.py` | Python | Installation des modules |
| `device_diagnostic.py` | Python | Diagnostic des périphériques |
| `validate_installation.py` | Python | Valider l'installation |
| `device_setup.py` | Python | Configuration interactive |
| `permissions_manager.py` | Python | Gestion permissions système |

### 📖 GUIDES UTILISATEUR

| Fichier | Contenu | Pour qui |
|---------|---------|----------|
| `QUICK_START.txt` | Démarrage rapide | Tous |
| `DEVICE_SETUP_GUIDE.md` | Guide complet par OS | Utilisateurs |
| `CONFIGURATION_EXAMPLE.md` | Exemples de config | Utilisateurs |
| `README_SOLUTION.md` | Vue d'ensemble | Administrateurs |
| `PERMISSIONS_AND_DEVICES_SETUP.md` | Spécifications | Administrateurs |
| `README_PERMISSIONS.md` | Permissions | Administrateurs |

### 👨‍💻 GUIDES DÉVELOPPEURS

| Fichier | Contenu |
|---------|---------|
| `DEVELOPER_GUIDE.md` | Guide d'intégration complet |
| `BACKEND/core/biometric_permissions.py` | Implémentation permissions |
| `BACKEND/api/v1/biometric.py` | Routes API REST |

### 📊 FICHIERS GÉNÉRÉS (Automatiques)

Créés dans `logs/`:
- `device_diagnostic_YYYYMMDD_HHMMSS.json` - Rapport diagnostic
- `device_config.json` - Configuration sauvegardée
- `device_diagnostic.log` - Logs détaillés
- `device_setup.log` - Logs du setup
- `test_audio.wav` - Enregistrement test (optionnel)

---

## 🚀 WORKFLOWS COURANTS

### Workflow 1: Première Installation (Utilisateur)

```
1. Lire: QUICK_START.txt
2. Exécuter: install_permissions.bat (ou .sh)
3. Exécuter: validate_installation.py
4. Exécuter: device_setup.py
5. Suivre le menu:
   → Choisir "1. Configuration complète"
6. Redémarrer l'application
```

### Workflow 2: Diagnostic Uniquement

```
1. Exécuter: device_diagnostic.py
2. Consulter: logs/device_diagnostic_*.json
3. Lire les recommandations
```

### Workflow 3: Dépannage (Admin)

```
1. Exécuter: device_diagnostic.py
2. Consulter: logs/device_diagnostic.log
3. Consulter: README_SOLUTION.md → Troubleshooting
4. Consulter: DEVICE_SETUP_GUIDE.md → Dépannage par OS
```

### Workflow 4: Intégration Backend (Développeur)

```
1. Lire: DEVELOPER_GUIDE.md
2. Intégrer BiometricPermissionsManager
3. Ajouter routes API
4. Ajouter décorateurs aux routes sensibles
5. Tester avec pytest
```

---

## 🔑 FICHIERS CLÉS À MODIFIER

Si vous devez personnaliser:

### Client Desktop - Modifier les indices de périphériques

Éditer: `logs/device_config.json`
```json
{
  "primary_camera": 0,      <-- Changer ici
  "primary_microphone": 0    <-- Ou ici
}
```

### Backend - Modifier les permissions par rôle

Éditer: `BACKEND/core/biometric_permissions.py`
```python
ROLE_PERMISSIONS = {
    'super_admin': { ... },
    'admin': { ... },
    ...
}
```

### Backend - Modifier les endpoints

Éditer: `BACKEND/api/v1/biometric.py`
```python
@app.route('/api/biometric/...')
def your_endpoint():
    ...
```

---

## ✅ CHECKLIST DE VALIDATION

**Installation:**
- [ ] Python 3.7+ installé
- [ ] Modules installés (voir `validate_installation.py`)
- [ ] Dossier logs créé
- [ ] Validation réussie

**Configuration:**
- [ ] Diagnostic exécuté
- [ ] Caméras détectées
- [ ] Microphones détectées
- [ ] Permissions configurées par OS
- [ ] Config sauvegardée

**Fonctionnalité:**
- [ ] device_setup.py compile
- [ ] device_diagnostic.py compile
- [ ] Test caméra réussi
- [ ] Test microphone réussi
- [ ] API backend accessible

---

## 📞 SUPPORT RAPIDE

**Problème** → **Solution**

| Problème | Solution |
|----------|----------|
| "Modules non installés" | Lancer `install_permissions.bat/sh` |
| "Aucune caméra détectée" | Lancer diagnostic, voir recommandations |
| "Permissions refusées" | Relire guide OS dans `DEVICE_SETUP_GUIDE.md` |
| "Validation échouée" | Consulter `validate_installation.py` output |
| "Comment intégrer?" | Lire `DEVELOPER_GUIDE.md` |

---

## 🎯 RÉSUMÉ RAPIDE

```
Pour commencer rapidement:

$ QUICK_START.txt                    ← Lire d'abord
$ cd "Client Desktop"
$ install_permissions.bat             ← Installation (Windows)
$ python validate_installation.py    ← Vérifier
$ python device_setup.py             ← Configurer
```

**Voilà! Vous êtes prêt!** ✅

---

## 📌 NOTES IMPORTANTES

1. **Dépendances requises:**
   - Python 3.7+
   - opencv-python
   - sounddevice
   - soundfile
   - scipy
   - numpy

2. **Sessions utilisateur:**
   - Linux: Se reconnecter après modification des groupes
   - Windows: Redémarrer l'app après changement de permissions
   - macOS: Relancer l'app après autorisation

3. **Permissions Linux:**
   ```bash
   sudo usermod -a -G video $USER
   sudo usermod -a -G audio $USER
   newgrp video && newgrp audio
   ```

4. **Permissions Windows:**
   - Paramètres > Confidentialité > Caméra/Microphone
   - Autoriser l'application

5. **Permissions macOS:**
   - Sécurité & Confidentialité > Caméra/Microphone
   - Ou via boîte de dialogue système

---

**Créé:** Mars 2026  
**Version:** 1.0  
**Support:** BioAccess Secure Team
