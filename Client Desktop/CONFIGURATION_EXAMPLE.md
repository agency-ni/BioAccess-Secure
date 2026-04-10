# Configuration des Périphériques - BioAccess Secure

## 📱 Périphériques Détectés

### 📷 Caméras

```json
{
  "primary_camera": 0,
  "cameras": [
    {
      "index": 0,
      "resolution": "1920x1080",
      "fps": 30,
      "status": "OK"
    }
  ]
}
```

### 🎤 Microphones

```json
{
  "primary_microphone": 0,
  "microphones": [
    {
      "index": 0,
      "name": "Microphone (Microphone Array)",
      "channels": 2,
      "sample_rate": 44100,
      "status": "OK"
    }
  ]
}
```

## 🔐 Configuration des Permissions

### Windows

- Ouvrir Paramètres (`Win + I`)
- Aller à: **Confidentialité et sécurité**
- **Caméra**: Activer et autoriser l'application
- **Microphone**: Activer et autoriser l'application
- Redémarrer l'application

### Linux

```bash
# Vérifier les groupes
groups

# Ajouter aux groupes
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER

# Appliquer les changements
newgrp video && newgrp audio
```

### macOS

- Autoriser via la boîte de dialogue du système
- Ou: **Préférences Système > Sécurité & Confidentialité**

## 📊 Résultats du Diagnostic

Le diagnostic génère un fichier JSON avec toutes les informations:

```json
{
  "timestamp": "2026-03-25T10:30:00.123456",
  "os": "Windows",
  "python_version": "3.10.5",
  "cameras": [
    {
      "index": 0,
      "resolution": "1920x1080",
      "fps": 30,
      "accessible": true,
      "capture_test": "Réussi"
    }
  ],
  "microphones": [
    {
      "index": 0,
      "name": "Microphone",
      "channels": 2,
      "sample_rate": 44100,
      "accessible": true
    }
  ],
  "permissions": {
    "os": "Windows",
    "camera": "À vérifier dans Paramètres",
    "microphone": "À vérifier dans Paramètres"
  },
  "recommendations": []
}
```

## ✅ Vérification

Pour vérifier que tout est configuré:

1. **Diagnostic:**
   ```bash
   python device_diagnostic.py
   ```

2. **Setup interactif:**
   ```bash
   python device_setup.py
   ```

3. **Test:**
   ```bash
   python device_setup.py
   # Choisir: 4. Test des périphériques
   ```

## 🔄 Redémarrer la Configuration

Si vous avez besoin de recommencer:

```bash
# Supprimer la configuration précédente
rm logs/device_config.json
rm logs/device_diagnostic_*.json

# Relancer le diagnostic
python device_diagnostic.py

# Relancer la configuration
python device_setup.py
```

## 📖 Voir aussi

- [DEVICE_SETUP_GUIDE.md](DEVICE_SETUP_GUIDE.md) - Guide complet par OS
- [README_SOLUTION.md](../README_SOLUTION.md) - Vue d'ensemble de la solution
- [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md) - Guide pour développeurs
