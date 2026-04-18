# 🚀 Installation BioAccess Secure - Client Desktop

**Pour les utilisateurs non-techniciens**

---

## ⚠️ Prérequis: Python

Vous devez d'abord installer **Python 3.10 ou plus récent**.

### Sur Windows:
1. Visitez: https://www.python.org/downloads/
2. Cliquez sur le gros bouton jaune "Download Python"
3. **IMPORTANT**: Lors de l'installation, cochez la case **"Add Python to PATH"** (en bas)
4. Cliquez "Install Now"

### Sur macOS:
1. Ouvrez Terminal (Applications > Utilitaires > Terminal)
2. Collez cette commande:
   ```
   brew install python3
   ```

### Sur Linux:
1. Ouvrez Terminal
2. Collez cette commande:
   ```
   sudo apt-get install python3 python3-pip
   ```

---

## ✅ Installation du Client BioAccess

Une fois Python installé, c'est facile:

### Sur Windows:
1. Double-cliquez sur **`install.bat`** (ce dossier)
2. Attendez que tout s'installe (2-3 minutes)
3. Le script fermera automatiquement

### Sur macOS / Linux:
1. Ouvrez Terminal dans ce dossier
2. Tapez: `bash install.sh`
3. Appuyez sur Entrée
4. Attendez que tout s'installe (2-3 minutes)

---

## 🎯 Démarrer l'Application

Une fois l'installation terminée:

### Option 1: Depuis la ligne de commande
- **Windows**: Ouvrez un Terminal dans ce dossier et tapez:
  ```
  python -m biometric.examples_quickstart
  ```

- **macOS/Linux**: Ouvrez Terminal dans ce dossier et tapez:
  ```
  python3 -m biometric.examples_quickstart
  ```

### Option 2: Raccourci (si créé)
- Double-cliquez sur l'icône BioAccess (si disponible sur le bureau)

---

## 🔧 Configuration (Optionnel)

Un fichier `.env` est créé automatiquement avec la configuration par défaut.

Si vous devez modifier l'adresse du serveur:
1. Ouvrez le fichier `.env` avec un éditeur texte
2. Modifiez `API_SERVER=http://localhost:5000` avec votre adresse
3. Sauvegardez

Exemple:
```
API_SERVER=http://192.168.1.100:5000
API_PREFIX=/api/v1
DEBUG=false
```

---

## 📱 Utilisation

1. L'application demande votre **Employee ID** (ex: 1002218AAKH)
2. Scannez votre **visage** avec la webcam
3. Dites un **mot-clé** (enregistré lors de l'inscription)
4. Accès autorisé ✅ ou ❌

---

## ❌ Problèmes Courants

**Erreur: "Python n'est pas installé"**
- ➜ Installez Python (voir section Prérequis)
- ➜ Redémarrez votre ordinateur

**Erreur: "Webcam pas trouvée"**
- ➜ Vérifiez que votre webcam est connectée
- ➜ Allez dans Paramètres > Périphériques > Caméra
- ➜ Accordez les permissions à l'application

**Erreur: "Micro pas trouvé"**
- ➜ Connectez un microphone
- ➜ Testez le micro dans Paramètres audio

**L'application crash ou ralentit**
- ➜ Fermez les autres applications
- ➜ Vérifiez votre connexion Internet

---

## 📞 Support

Contactez: **support@bioaccess.secure**

Joignez à votre message:
- Le message d'erreur exact
- Votre système d'exploitation (Windows/Mac/Linux)
- Votre configuration (webcam, micro)

---

**Besoin d'aide?** Appelez le support au: **+33 1 XX XX XX XX**
