# 🚀 Guide de démarrage rapide

## ⚡ Installation en 5 minutes

### 1. Cloner et accéder au dossier

```bash
cd "Client Desktop"
```

### 2. Créer l'environnement virtuel

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

**Durée estimée:** 2-3 minutes (selon la connexion)

### 4. Configurer l'API

Copier et éditer le fichier `.env`:

```bash
cp .env.example .env
```

**Éditer `.env` et modifier:**
```env
# Adapter l'URL du serveur
API_BASE_URL=http://localhost:5000/api/v1
```

### 5. Lancer l'application

```bash
python main.py
```

💡 **Vous devriez voir:**
- ✅ Vérification des dépendances
- ✅ Vérification de la connexion API
- 🪟 Ouverture de la fenêtre principale

## 📱 Utilisation basique

### Authentification par visage

1. Cliquer sur **📸 Scanner Visage**
2. Se placer devant la caméra
3. Attendre la capture automatique
4. Résultat affiché

**Durée:** ~3-5 secondes

### Authentification par voix

1. Cliquer sur **🎤 Utiliser la Voix**
2. Parler normalement
3. Enregistrement de 5 secondes
4. Résultat affiché

**Durée:** ~5 secondes

## ⚙️ Configuration rapide

Tous les paramètres sont dans le fichier `.env`:

| Paramètre | Valeur | Exemple |
|-----------|--------|---------|
| `API_BASE_URL` | URL du serveur | `http://localhost:5000/api/v1` |
| `CAMERA_ID` | ID caméra | `0` (caméra par défaut) |
| `AUDIO_DURATION` | Durée voix | `5` secondes |
| `MAX_ATTEMPTS` | Tentatives | `3` |

## 🧪 Tester la connexion API

```bash
python test_api.py
```

Devrait afficher:
```
✅ API ACCESSIBLE
```

## 🐛 Problèmes courants

### "Module not found: cv2"

```bash
pip install opencv-python
```

### "Cannot access camera"

- Vérifier que la caméra est connectée
- Modifier `CAMERA_ID=0` dans `.env`

### "No audio device found"

- Vérifier que le microphone fonctionne
- Sur Linux: `sudo usermod -a -G audio $USER`

## 📝 Fichiers importants

```
Client Desktop/
├── main.py              ← Lance l'app
├── config.py            ← Configuration centralisée
├── .env                 ← ✏️ Éditer ceci pour configurer
├── requirements.txt     ← Dépendances
├── test_api.py          ← Vérifier l'API
│
├── ui/
│   └── login_screen.py  ← Interface visuelle
├── biometric/
│   ├── face.py          ← Caméra & visage
│   └── voice.py         ← Microphone & voix
├── services/
│   └── api_client.py    ← Communication API
└── logs/
    └── app.log          ← Logs (pour déboguer)
```

## 🔗 Démarrer le serveur backend

**Dans un autre terminal:**

```bash
cd BACKEND
python run.py
```

L'API devrait être accessible sur `http://localhost:5000`

## ✅ Checklist de démarrage

- [ ] Python 3.8+ installé
- [ ] Caméra connectée et testée
- [ ] Microphone connecté et testé
- [ ] Dépendances installées: `pip install -r requirements.txt`
- [ ] Fichier `.env` créé et configuré
- [ ] Serveur backend lancé: `python run.py` (dans BACKEND/)
- [ ] `test_api.py` affiche ✅
- [ ] Application lancée: `python main.py`

## 🎯 Flux complet de test

```bash
# Terminal 1: Serveur backend
cd BACKEND
python run.py
# -> API court sur http://localhost:5000

# Terminal 2: On attend 2-3s, puis tester l'API
cd "Client Desktop"
python test_api.py
# -> ✅ API ACCESSIBLE

# Terminal 2: Lancer le client
python main.py
# -> Interface Tkinter s'ouvre
```

## 💡 Astuces

### Voir les logs en direct
```bash
tail -f logs/app.log
```

### Relancer après changement config
```bash
python main.py
```

### Vider les logs
```bash
> logs/app.log  # Windows
# ou
rm logs/app.log  # Linux/Mac
```

## 📞 Support rapide

**L'app refuse de démarrer?**
→ Vérifier les erreurs dans la console et dans `logs/app.log`

**API non accessible?**
→ Vérifier que le serveur backend est lancé: `python run.py` (BACKEND/)

**Caméra ne marche pas?**
→ Tester avec OpenCV directement:
```python
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

---

**C'est prêt! 🚀 Bon test!**
