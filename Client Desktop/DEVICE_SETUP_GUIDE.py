#!/usr/bin/env python3
"""
BioAccess Secure - Guide de configuration des périphériques

Ce fichier contient les instructions pour configurer et tester
l'accès à la caméra et au microphone pour l'application.

Fichiers créés:
1. device_diagnostic.py - Script de diagnostic complet
2. permissions_manager.py - Gestionnaire des permissions Windows/Linux/macOS
3. device_setup.py - Interface de configuration interactive
4. DEVICE_SETUP_GUIDE.md - Ce guide
"""

import subprocess
import sys
import os
import platform


def guide_windows():
    """Guide complet pour Windows"""
    guide = """
╔════════════════════════════════════════════════════════════════════════════━╗
║      GUIDE DE CONFIGURATION - BIOACCESS SECURE (Windows 10/11)            ║
╚════════════════════════════════════════════════════════════════════════════━╝

1. DÉMARRER LA CONFIGURATION
════════════════════════════════════════════════════════════════════════════

Exécutez l'une de ces commandes:

    python device_setup.py              (Recommandé - Configuration interactive)
    python device_diagnostic.py         (Diagnostic uniquement)
    python permissions_manager.py       (Gestionnaire de permissions)


2. CONFIGURATION ÉTAPE PAR ÉTAPE
════════════════════════════════════════════════════════════════════════════

A) CAMÉRA
─────────────────────────────────────────────────────────────────────────────

Problème: "Aucune caméra détectée" ou "Impossible d'accéder à la caméra"

Solution 1 - Vérifier les permissions:
  1. Ouvrez: Paramètres > Confidentialité et sécurité > Caméra
  2. Activez "Accès à la caméra"
  3. Activez "Autoriser les applications à accéder à votre caméra"
  4. Vérifiez que BioAccess Secure est autorisée
  5. Redémarrez l'application

Solution 2 - Vérifier le matériel:
  1. Allez à: Paramètres > Applications > Applications et fonctionnalités > Caméra
  2. Assurez-vous que la caméra apparaît dans "Gestionnaire de périphériques"
  3. Cliquez sur caméra > Propriétés > Pilote
  4. Vérifiez que le pilote est à jour
  5. Sinon, cliquez "Mettre à jour le pilote"

Solution 3 - Redémarrer le service:
  1. Appuyez sur: Windows + R
  2. Tapez: devmgmt.msc
  3. Trouvez votre caméra (Caméras > [Votre caméra])
  4. Cliquez droit > Désactiver l'appareil
  5. Cliquez droit > Activer l'appareil
  6. Attendez 30 secondes et réessayez


B) MICROPHONE
─────────────────────────────────────────────────────────────────────────────

Problème: "Aucun microphone détecté" ou "Permission refusée"

Solution 1 - Vérifier les permissions:
  1. Ouvrez: Paramètres > Confidentialité et sécurité > Microphone
  2. Activez "Accès au microphone"
  3. Activez "Autoriser les applications à accéder à votre microphone"
  4. Vérifiez que BioAccess Secure est autorisée
  5. Redémarrez l'application

Solution 2 - Vérifier le niveau du microphone:
  1. Clic droit sur Icône de volume (coin bas droit)
  2. Sélectionnez "Paramètres de volume avancés"
  3. Trouvez votre microphone > Vérifiez le niveau d'entrée
  4. Augmentez le volume s'il est trop bas
  5. Testez avec un enregistreur de bruit (Accessoires > Enregistreur de bruit)

Solution 3 - Redémarrer le service audio:
  1. Appuyez sur: Windows + R
  2. Tapez: services.msc
  3. Trouvez "Windows Audio"
  4. Clic droit > Redémarrer
  5. Attendez 10 secondes et réessayez


3. SCRIPTS UTILES
════════════════════════════════════════════════════════════════════════════

Script                          Commande                      Description
─────────────────────────────────────────────────────────────────────────────
Setup complet      python device_setup.py          Configuration interactive
Diagnostic        python device_diagnostic.py       Diagnostic détaillé
Permissions       python permissions_manager.py    Gestionnaire permissions
─────────────────────────────────────────────────────────────────────────────


4. IMAGES DE TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════

Test caméra uniquement:
  python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print('✓ Caméra OK' if ret else '✗ Erreur caméra')
cap.release()
"

Test microphone uniquement:
  python -c "
import sounddevice as sd
import numpy as np
audio = sd.rec(int(1 * 44100), samplerate=44100, channels=1, dtype=np.float32)
sd.wait()
level = np.sqrt(np.mean(audio**2))
print(f'✓ Microphone OK (niveau: {level:.4f})' if level > 0.01 else '✗ Microphone silencieux')
"


5. RÉSUMÉ DES SOLUTIONS PAR ERREUR
════════════════════════════════════════════════════════════════════════════

┌─ Erreur: "Aucune caméra détectée" ────────────────────────────────────────┐
│                                                                             │
│ 1. Vérifier la connexion physique de la caméra                             │
│ 2. Activer la permission dans Paramètres > Confidentialité > Caméra       │
│ 3. Mettre à jour les pilotes                                              │
│ 4. Redémarrer l'application                                               │
│ 5. Redémarrer l'ordinateur                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Erreur: Permission refusée (caméra/micro) ──────────────────────────────┐
│                                                                             │
│ 1. Vérifier Paramètres > Confidentialité > Caméra/Microphone             │
│ 2. S'assurer que l'app est dans la liste blanche                          │
│ 3. Actualiser la permission: Désactiver > Réactiver                       │
│ 4. Redémarrer Windows                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Erreur: Son très faible ou absent ───────────────────────────────────────┐
│                                                                             │
│ 1. Augmenter le niveau du microphone                                       │
│ 2. Vérifier le volume système (zone système Windows)                      │
│ 3. Tester avec "Enregistreur de bruit" (Accessoires)                      │
│ 4. Vérifier les câbles de connexion                                       │
│ 5. Mettre à jour les pilotes audio                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─ Erreur: Application plante lors de l'accès caméra/micro ────────────────┐
│                                                                             │
│ 1. Vérifier les logs: logs/device_diagnostic_results.json                │
│ 2. Exécuter: python device_setup.py                                       │
│ 3. Vérifier les permissions                                               │
│ 4. Réinstaller OpenCV: pip install --upgrade opencv-python               │
│ 5. Réinstaller sounddevice: pip install --upgrade sounddevice             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘


6. LOGS ET DIAGNOSTICS
════════════════════════════════════════════════════════════════════════════

Les logs sont sauvegardés dans le dossier 'logs/':

- device_diagnostic_results.json : Résultats du diagnostic complet
- setup_YYYYMMDD_HHMMSS.json    : Log de configuration
- device_setup.log              : Log détaillé des opérations


7. CONTACT ET SUPPORT
════════════════════════════════════════════════════════════════════════════

Si vous continuez à avoir des problèmes:

1. Collectez le log de diagnostic:
   python device_diagnostic.py
   (Envoyer le fichier logs/device_diagnostic_results.json)

2. Exécutez la configuration complète:
   python device_setup.py
   (Envoyer le fichier logs/setup_*.json)

3. Consultez la documentation:
   - ARCHITECTURE.md
   - DEBUG.md
   - README.md
"""
    return guide


def guide_linux():
    """Guide pour Linux"""
    guide = """
╔════════════════════════════════════════════════════════════════════════════╗
║      GUIDE DE CONFIGURATION - BIOACCESS SECURE (Linux)                    ║
╚════════════════════════════════════════════════════════════════════════════╝

1. DÉMARRER LA CONFIGURATION
════════════════════════════════════════════════════════════════════════════

    python device_setup.py              (Configuration interactive)
    python device_diagnostic.py         (Diagnostic)
    python permissions_manager.py       (Gestionnaire permissions)


2. AJOUTER LES PERMISSIONS UTILISATEUR
════════════════════════════════════════════════════════════════════════════

Pour accéder à la caméra et au microphone sur Linux, votre utilisateur
doit faire partie de groupes spécifiques.

Caméra:
  sudo usermod -a -G video $USER

Microphone:
  sudo usermod -a -G audio $USER

Appliquez les changements:
  # Option 1: Déconnectez-vous puis reconnectez-vous

  # Option 2: Exécutez dans le terminal courant
  newgrp video && newgrp audio


3. VÉRIFIER LES PERMISSIONS
════════════════════════════════════════════════════════════════════════════

Vérifier l'appartenance aux groupes:
  groups

Vous devriez voir 'video' et 'audio' dans la liste.


4. TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════

Erreur: "Permission denied" pour caméra
  → Vérifier: groups | grep video
  → Exécuter: sudo usermod -a -G video $USER
  → Redémarrer: déconnectez-vous ou redémarrez

Erreur: "No sound input"
  → Vérifier: groups | grep audio
  → Exécuter: sudo usermod -a -G audio $USER
  → Vérifier PulseAudio: pulseaudio --version
  → Liste des entrées: pactl list short sources

Caméra USB non détectée:
  → Lister: ls /dev/video*
  → Vérifier la permission: ls -l /dev/video*
  → Essayer: v4l2-ctl --list-devices


5. DÉPENDANCES
════════════════════════════════════════════════════════════════════════════

Installer les dépendances:

Ubuntu/Debian:
  sudo apt-get install python3-opencv python3-sounddevice
  sudo apt-get install libopencv-dev
  sudo apt-get install pulseaudio pavucontrol

Fedora/RHEL:
  sudo dnf install python3-opencv python3-sounddevice
  sudo dnf install opencv-devel

Arch:
  sudo pacman -S opencv python-sounddevice
"""
    return guide


def guide_macos():
    """Guide pour macOS"""
    guide = """
╔════════════════════════════════════════════════════════════════════════════╗
║      GUIDE DE CONFIGURATION - BIOACCESS SECURE (macOS)                    ║
╚════════════════════════════════════════════════════════════════════════════╝

1. DÉMARRER LA CONFIGURATION
════════════════════════════════════════════════════════════════════════════

    python device_setup.py              (Configuration interactive)
    python device_diagnostic.py         (Diagnostic)
    python permissions_manager.py       (Gestionnaire permissions)


2. ACCORDER LES PERMISSIONS
════════════════════════════════════════════════════════════════════════════

Première utilisation - macOS demandera une permission

Caméra:
  → macOS vous demandera l'autorisation
  → Cliquez "Autoriser" dans la popup
  → Si refusé: Préférences Système > Sécurité et confidentialité > Caméra

Microphone:
  → macOS vous demandera l'autorisation
  → Cliquez "Autoriser" dans la popup
  → Si refusé: Préférences Système > Sécurité et confidentialité > Microphone


3. VÉRIFIER LES PERMISSIONS
════════════════════════════════════════════════════════════════════════════

Vérifier l'autorisations accordées:
  tccutil dump


4. TROUBLESHOOTING
════════════════════════════════════════════════════════════════════════════

Erreur: Permission refusée
  → Aller à: Préférences Système > Sécurité et confidentialité
  → Sélectionner Caméra ou Microphone
  → Retirer l'application et la rajouter

Réinitialiser les permissions:
  tccutil reset All

Erreur: Caméra non détectée
  → Vérifier que la caméra FaceTime est bien connectée
  → Redémarrer macOS


5. DÉPENDANCES
════════════════════════════════════════════════════════════════════════════

Installer via Homebrew:
  brew install opencv sounddevice
  
Ou via pip:
  pip install opencv-python sounddevice soundfile
"""
    return guide


def main():
    """Menu principal"""
    print("\n" + "=" * 70)
    print("  GUIDE DE CONFIGURATION - BIOACCESS SECURE")
    print("=" * 70)
    
    current_os = platform.system()
    
    print(f"\nSystème détecté: {current_os}")
    print("\nChoix:")
    print(f"  1. Guide pour {current_os} (recommandé)")
    print("  2. Guide pour Windows")
    print("  3. Guide pour Linux")
    print("  4. Guide pour macOS")
    print("  5. Lancer la configuration interactive")
    print("  6. Quitter\n")
    
    choice = input("Sélectionner (1-6): ").strip()
    
    if choice == '1':
        if current_os == 'Windows':
            print(guide_windows())
        elif current_os == 'Linux':
            print(guide_linux())
        elif current_os == 'Darwin':
            print(guide_macos())
    elif choice == '2':
        print(guide_windows())
    elif choice == '3':
        print(guide_linux())
    elif choice == '4':
        print(guide_macos())
    elif choice == '5':
        print("\nLancement de device_setup.py...")
        os.system(f"{sys.executable} device_setup.py")
    elif choice == '6':
        print("Au revoir!")
        return
    
    input("\nAppuyez sur Entrée pour quitter...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
        sys.exit(0)
