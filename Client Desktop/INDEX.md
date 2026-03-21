# 📚 Index - Guide de Navigation

Bienvenue dans la documentation de **BioAccess Secure - Client Desktop**. 

Utilisez ce guide pour naviguer rapidement dans tous les documents disponibles.

---

## 🚀 Démarrage rapide

### Je veux juste que ça marche maintenant!
1. **Lire:** [QUICKSTART.md](QUICKSTART.md) (5 min)
2. **Exécuter:** `python main.py`
3. **C'est fini!**

### J'ai une question spécifique
- Problème d'installation? → [QUICKSTART.md - Installation](QUICKSTART.md#installation-en-5-minutes)
- Ça ne marche pas? → [DEBUG.md](DEBUG.md)
- Comment ça fonctionne? → [ARCHITECTURE.md](ARCHITECTURE.md)
- Comment utiliser? → [README.md](README.md#utilisation)

---

## 📖 Documentation par sujet

### 📋 Vue d'ensemble

| Document | But | Temps |
|----------|-----|-------|
| [README.md](README.md) | Documentation complète | 15 min |
| [QUICKSTART.md](QUICKSTART.md) | Installation et démarrage | 5 min |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Comprendre le design | 10 min |
| [CHANGELOG.md](CHANGELOG.md) | Historique des versions | 5 min |

### 🔧 Développement

| Document | Contenu | Pour qui |
|----------|---------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md#architecture-en-couches) | Chaque module expliqué | Développeurs |
| [ARCHITECTURE.md](ARCHITECTURE.md#extension-points) | Comment étendre | Développeurs |
| [README.md](README.md#-api-de-développement) | API modules | Développeurs |

### 🐛 Problèmes

| Document | Erreur | Solution |
|----------|--------|----------|
| [DEBUG.md](DEBUG.md#installation) | ModuleNotFoundError | Voir DEBUG.md |
| [DEBUG.md](DEBUG.md#caméra) | Caméra ne marche pas | Voir DEBUG.md |
| [DEBUG.md](DEBUG.md#audio) | Pas de micro | Voir DEBUG.md |
| [DEBUG.md](DEBUG.md#api) | Serveur inaccessible | Voir DEBUG.md |

### ⚙️ Configuration

| Fichier | Usage | Comment |
|---------|-------|---------|
| [.env.example](.env.example.md) | Template config | Copier en `.env` |
| [config.py](config.py) | Config centralisée | Éditer `.env` |
| [README.md](README.md#-personnalisation) | Editer les paramètres | Voir README |

### 📱 Utilisation

| Sujet | Lien | Détails |
|-------|------|---------|
| Authentification faciale | [README.md](README.md#utilisation) | Cliquer bouton & scanner |
| Authentification vocale | [README.md](README.md#utilisation) | Cliquer bouton & parler |
| Gestion tentatives | [README.md](README.md#utilisation) | Max 3, puis cooldown |

---

## 🗂️ Structure des fichiers

```
Client Desktop/
│
├── 📖 Documentation (à lire)
│   ├── README.md              ← Lire en premier
│   ├── QUICKSTART.md          ← Installation & démarrage
│   ├── ARCHITECTURE.md        ← Comment ça marche
│   ├── DEBUG.md               ← Problèmes & solutions
│   ├── CHANGELOG.md           ← Historique versions
│   └── INDEX.md               ← CE FICHIER
│
├── 🚀 Lancer l'app
│   ├── main.py                ← Exécuter: python main.py
│   ├── test_api.py            ← Tester API: python test_api.py
│   └── install.* (bat/sh/py)  ← Installer dépendances
│
├── ⚙️ Configuration
│   ├── config.py              ← Tous les paramètres
│   ├── .env.example           ← Template variables d'env
│   └── .env                   ← Configuration (créer depuis .env.example)
│
├── 📦 Code source
│   ├── ui/login_screen.py     ← Interface Tkinter
│   ├── biometric/
│   │   ├── face.py            ← Reconnaissance faciale
│   │   └── voice.py           ← Reconnaissance vocale
│   └── services/
│       └── api_client.py      ← Client API
│
├── 📝 Dépendances
│   └── requirements.txt        ← Toutes les dépendances
│
└── 📂 Générés au runtime
    ├── logs/app.log           ← Fichier log
    ├── temp/                  ← Fichiers temporaires
    └── venv/                  ← Environnement virtuel
```

---

## 🎯 Scénarios courants

### Scénario 1: Installation première fois

```
1. Ouvrir QUICKSTART.md
2. Copier cli par cli
3. Répondre aux questions
4. python main.py
```

**Temps:** ~5 minutes

### Scénario 2: Application ne marche pas

```
1. Ouvrir DEBUG.md
2. Chercher le message d'erreur
3. Suivre la solution
4. Réessayer
```

**Temps:** ~2-10 minutes selon le problème

### Scénario 3: Je veux comprendre l'architecture

```
1. Lire README.md - Section "Architecture du projet"
2. Lire ARCHITECTURE.md - Sections "Vue d'ensemble"
3. Lire ARCHITECTURE.md - Section du module spécifique
4. Regarder le code source
```

**Temps:** ~20 minutes

### Scénario 4: Je veux ajouter une feature

```
1. Lire ARCHITECTURE.md - "Extension Points"
2. Lire le code du module related
3. Implémenter votre feature
4. Tester avec test_api.py
5. Vérifier logs/app.log
```

**Temps:** Dépend de la feature

### Scénario 5: Je veux déployer en production

```
1. Lire README.md - Section "Sécurité"
2. Éditer .env avec vrais paramètres
3. Vérifier API_KEY
4. Configurer HTTPS
5. Lancer main.py sur serveur
6. Configurer autostart (systemd/cron/Task Scheduler)
```

**Temps:** ~30 minutes

---

## 🔍 Recherche rapide

### Mots-clés importants

**Installation:**
- QUICKSTART.md
- install.bat / install.sh / install.py
- requirements.txt

**Caméra:**
- biometric/face.py
- DEBUG.md#caméra
- ARCHITECTURE.md#FaceRecognizer

**Audio:**
- biometric/voice.py
- DEBUG.md#audio
- ARCHITECTURE.md#VoiceRecorder

**API:**
- services/api_client.py
- DEBUG.md#api
- README.md#endpoints-api-attendus

**Configuration:**
- config.py
- .env.example
- README.md#personnalisation

**Logs:**
- logs/app.log
- README.md#logging
- DEBUG.md#problèmes-courants

---

## 📞 Questions fréquentes (FAQ)

### Q: Où sont mes logs?
**A:** `logs/app.log`
```bash
tail -f logs/app.log  # Voir en direct
```

### Q: Je dois configurer quoi?
**A:** Editer `.env`
```bash
cp .env.example .env
# Éditer .env - surtout API_BASE_URL
```

### Q: Comment installer les dépendances?
**A:** Suivre QUICKSTART.md ou exécuter install.bat/sh
```bash
pip install -r requirements.txt
```

### Q: Ça ne marche pas, qui appeler?
**A:** 
1. Consulter DEBUG.md
2. Vérifier logs/app.log
3. Relire ARCHITECTURE.md

### Q: Où trouver le code de la caméra?
**A:** `biometric/face.py`
Classe: `FaceRecognizer`

### Q: Où trouver le code de l'interface?
**A:** `ui/login_screen.py`
Classe: `LoginScreen`

### Q: Peut-on ajouter une autre biométrie (iris, empreinte)?
**A:** Oui! Voir ARCHITECTURE.md#extension-points

### Q: Ça marche offline?
**A:** Non, v1.0 nécessite l'API. Voir CHANGELOG.md#future-roadmap pour v2.0

---

## 🗺️ Map mentale des modules

```
LoginScreen (UI)
├─ appelle → FaceRecognizer
│           ├─ read_frame()
│           ├─ detect_faces()
│           ├─ capture_face()
│           └─ image_to_base64()
│
├─ appelle → VoiceRecorder
│           ├─ record_audio()
│           ├─ audio_to_wav_base64()
│           └─ extract_features()
│
└─ appelle → APIClient
            ├─ authenticate_face()
            ├─ authenticate_voice()
            ├─ health_check()
            └─ _make_request()
```

---

## 📚 Ressources externes

### Documentation Framework/Libraries

- **Tkinter**: https://docs.python.org/3/library/tkinter.html
- **OpenCV**: https://docs.opencv.org/
- **sounddevice**: https://python-sounddevice.readthedocs.io/
- **requests**: https://requests.readthedocs.io/

### Tutoriels

- Face detection avec OpenCV: https://docs.opencv.org/master/d7/d8b/tutorial_py_face_detection_haar_cascade.html
- Tkinter apps: https://tkdocs.com/tutorial/
- Audio processing Python: https://realpython.com/primer-on-python-decorators/

### Community

- Stack Overflow: [Rechercher "opencv face detection"]
- Reddit: r/Python, r/learnprogramming
- GitHub: Issues & discussions

---

## ✅ Checklist de vérification

Avant de déployer:

- [ ] Installation réussie (`pip install -r requirements.txt`)
- [ ] .env créé et configuré
- [ ] test_api.py répond ✅
- [ ] Caméra détectée
- [ ] Microphone détecté
- [ ] Interface s'affiche
- [ ] Scan facial fonctionne
- [ ] Enregistrement vocal fonctionne
- [ ] API répond correctement
- [ ] Logs générés dans logs/app.log
- [ ] Documentation lue (au moins QUICKSTART)

---

## 🎓 Ordre de lecture recommandé

Pour **Utilisateur finale** (juste utiliser):
1. QUICKSTART.md
2. README.md#utilisation

Pour **Développeur** (contribuer):
1. README.md (entièrement)
2. ARCHITECTURE.md (entièrement)
3. Code source (ui/ → biometric/ → services/)
4. DEBUG.md (pour références)

Pour **DevOps/Deployment**:
1. QUICKSTART.md#installation
2. README.md#sécurité
3. config.py
4. .env.example
5. DEBUG.md#performance

---

## 🔗 Liens importants

- **Documentation complète:** [README.md](README.md)
- **Installation rapide:** [QUICKSTART.md](QUICKSTART.md)
- **Architecture technique:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Dépannage:** [DEBUG.md](DEBUG.md)
- **Versions:** [CHANGELOG.md](CHANGELOG.md)

---

**Vous êtes prêt(e)! Commencez par [QUICKSTART.md](QUICKSTART.md) 🚀**

Dernière mise à jour: 21 Mars 2024
