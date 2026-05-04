#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         BioAccess Secure — Client Desktop Principal                  ║
║                                                                              ║
║  Architecture de sécurité :                                                 ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │  DÉMARRAGE → Fenêtre normale                                        │    ║
║  │      ↓ Saisie User_ID → Verrou plein écran (ALT+F4 bloqué)         │    ║
║  │      ↓ Vérif admin (API alerts.html)                                │    ║
║  │      ↓ Auth biométrique (face OpenCV ou voix Vosk)                  │    ║
║  │      ↓ Succès → Poste déverrouillé                                  │    ║
║  └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  Intégrité (intégré) :                                                      ║
║    • SHA-256 de l'exe + sceau HMAC au démarrage                            ║
║    • Compromis → alerte automatique via POST /api/v1/alerts                ║
║    • Compatible avec alerts.html (même format JSON)                        ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import cv2
import time
import math
import random
import hashlib
import platform
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from enum import Enum, auto
from typing import Optional, Tuple

import tkinter as tk
from tkinter import ttk, messagebox

# ── Chemins ───────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / "biometric"))

def resource_path(relative_path):
    """ Gestion des chemins pour PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # Mode compilé : PyInstaller stocke les fichiers ici
        return os.path.join(sys._MEIPASS, relative_path)
    # Mode développement : on utilise le répertoire du script
    return str(SCRIPT_DIR / relative_path)

# Charge ton détecteur comme ça :
FACE_XML = resource_path("haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(FACE_XML)
    
# ── Modules optionnels ────────────────────────────────────────────────────────
try:
    from biometric import BiometricAPI, get_capture_service, MUSE_AVAILABLE
    BIOMETRIC_AVAILABLE = True
except Exception:
    BIOMETRIC_AVAILABLE = False
    MUSE_AVAILABLE = False

# CRITIQUE: NumPy MUST be imported before cv2
try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False
    print("[ERREUR CRITIQUE] NumPy n'est pas installé.", file=sys.stderr)
    print("Exécutez : fix_deps.bat", file=sys.stderr)

try:
    import cv2
    OPENCV_OK = NUMPY_OK  # OpenCV OK seulement si NumPy OK
except ImportError as e:
    OPENCV_OK = False
    print(f"[AVERT] OpenCV non disponible : {e}", file=sys.stderr)

try:
    import cv2
    import numpy as np
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False

try:
    import vosk
    import sounddevice as sd
    import queue
    VOSK_OK = True
except ImportError:
    VOSK_OK = False

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False


# ── Vérification des dépendances critiques ────────────────────────────────────
CRITICAL_OK = NUMPY_OK and REQUESTS_OK
if not CRITICAL_OK:
    root = tk.Tk()
    root.withdraw()
    error_msg = "Dépendances critiques manquantes :\n\n"
    if not NUMPY_OK:
        error_msg += "✗ NumPy\n"
    if not REQUESTS_OK:
        error_msg += "✗ Requests\n"
    error_msg += "\n" + "Veuillez exécuter : fix_deps.bat"
    messagebox.showerror("Erreur Démarrage", error_msg)
    sys.exit(1)

# ╔══════════════════════════════════════════════════════════════════════
# ╔══════════════════════════════════════════════════════════════════════
# ║  MODULE PERMISSIONS BIOMETRIQUES -- integre directement            ║
# ║  Windows registre + macOS TCC/AVFoundation + Linux v4l2/ALSA       ║
# ╚══════════════════════════════════════════════════════════════════════
import os
import sys
import platform
import subprocess
import threading
import logging
from enum import Enum, auto
from typing import Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field

log = logging.getLogger("bioaccess.permissions")


# ═════════════════════════════════════════════════════════════════════════════
# TYPES
# ═════════════════════════════════════════════════════════════════════════════

class DevicePermission(Enum):
    CAMERA     = auto()
    MICROPHONE = auto()


class PermissionState(Enum):
    GRANTED       = auto()  # Accordée
    DENIED        = auto()  # Refusée explicitement
    NOT_DETERMINED= auto()  # Jamais demandée (macOS / Windows 11)
    RESTRICTED    = auto()  # Politique d'entreprise (MDM/GPO)
    UNAVAILABLE   = auto()  # Périphérique absent
    UNKNOWN       = auto()  # Impossible à déterminer


@dataclass
class PermissionResult:
    device:    DevicePermission
    state:     PermissionState
    os_name:   str
    message:   str                       # Message court (pour l'UI)
    detail:    str = ""                  # Détail technique
    fix_steps: list = field(default_factory=list)  # Étapes correctives
    can_request: bool = False            # True si on peut demander l'accès

    @property
    def granted(self) -> bool:
        return self.state == PermissionState.GRANTED

    @property
    def actionable(self) -> bool:
        """True si l'utilisateur peut faire quelque chose."""
        return self.state in (
            PermissionState.DENIED,
            PermissionState.NOT_DETERMINED,
        )


# ═════════════════════════════════════════════════════════════════════════════
# GESTIONNAIRE PRINCIPAL
# ═════════════════════════════════════════════════════════════════════════════

class PermissionManager:
    """
    Vérifie et demande les permissions biométriques.
    Windows uniquement (Windows 10+ v1903, Windows 11).
    """

    def __init__(self):
        self.os = platform.system()   # "Windows" | "Darwin" | "Linux"

    # ── Point d'entrée public ─────────────────────────────────────────────────
    def check_and_request(
        self,
        device: DevicePermission,
        on_result: Optional[Callable[[PermissionResult], None]] = None
    ) -> PermissionResult:
        """
        Vérifie la permission, la demande si possible, retourne le résultat.
        Si on_result est fourni, l'appel est fait en thread séparé.
        """
        if on_result:
            threading.Thread(
                target=lambda: on_result(self._dispatch(device)),
                daemon=True).start()
            # Retourne un état temporaire pendant la vérification
            return PermissionResult(
                device=device,
                state=PermissionState.UNKNOWN,
                os_name=self.os,
                message="Vérification en cours…"
            )
        return self._dispatch(device)

    def check_all(self) -> Tuple[PermissionResult, PermissionResult]:
        """Vérifie caméra ET microphone. Retourne (camera_result, mic_result)."""
        cam = self._dispatch(DevicePermission.CAMERA)
        mic = self._dispatch(DevicePermission.MICROPHONE)
        return cam, mic

    def _dispatch(self, device: DevicePermission) -> PermissionResult:
        try:
            if self.os == "Windows": 
                return self._check_windows(device)
            else:
                return PermissionResult(
                    device=device,
                    state=PermissionState.UNKNOWN,
                    os_name=self.os,
                    message=f"⚠ BioAccess Secure est configuré pour Windows uniquement.",
                    detail=f"OS détecté : {self.os}",
                    fix_steps=[f"Cette application n'est compatible qu'avec Windows 10+ (v1903 ou supérieur)."]
                )
        except Exception as e:
            log.warning(f"Permission check error ({device.name}): {e}")
            return PermissionResult(
                device=device,
                state=PermissionState.UNKNOWN,
                os_name=self.os,
                message=f"Impossible de vérifier la permission : {e}",
                fix_steps=["Vérifiez manuellement les paramètres de confidentialité Windows."]
            )

    # ═══════════════════════════════════════════════════════════════════════
    # WINDOWS
    # ═══════════════════════════════════════════════════════════════════════

    def _check_windows(self, device: DevicePermission) -> PermissionResult:
        r"""
        Verifie via le registre Windows :
        HKCU\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\
        ConsentStore\{webcam|microphone}
        Value : 'Allow' | 'Deny'

        Windows 10 v1903+ / Windows 11.
        """
        device_key = "webcam" if device == DevicePermission.CAMERA else "microphone"
        device_name = "Caméra" if device == DevicePermission.CAMERA else "Microphone"
        settings_page = (
            "ms-settings:privacy-webcam"
            if device == DevicePermission.CAMERA
            else "ms-settings:privacy-microphone"
        )

        try:
            import winreg
            key_path = rf"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\{device_key}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "Value")

            if value == "Allow":
                # Vérification supplémentaire : tester l'accès réel
                ok, err = self._test_device_access(device)
                if ok:
                    return PermissionResult(
                        device=device, state=PermissionState.GRANTED,
                        os_name="Windows",
                        message=f"✓ {device_name} autorisée",
                        detail=f"Registre : Allow | Test accès : OK"
                    )
                else:
                    return PermissionResult(
                        device=device, state=PermissionState.UNAVAILABLE,
                        os_name="Windows",
                        message=f"✗ {device_name} autorisée mais inaccessible",
                        detail=f"Registre : Allow | Test accès : {err}",
                        fix_steps=[
                            f"Vérifiez qu'un {device_name.lower()} est connecté.",
                            "Vérifiez que le pilote est installé (Gestionnaire de périphériques).",
                            "Essayez de déconnecter/reconnecter le périphérique.",
                        ]
                    )
            elif value == "Deny":
                return PermissionResult(
                    device=device, state=PermissionState.DENIED,
                    os_name="Windows",
                    message=f"✗ {device_name} refusée par Windows",
                    detail=f"Registre : Deny",
                    can_request=True,
                    fix_steps=[
                        f"Ouvrez : Paramètres → Confidentialité → {device_name}",
                        f"Activez l'accès à la {device_name.lower()} pour les applications de bureau.",
                        "Ou cliquez sur 'Ouvrir les Paramètres' ci-dessous.",
                    ]
                )
            else:
                return PermissionResult(
                    device=device, state=PermissionState.UNKNOWN,
                    os_name="Windows",
                    message=f"? {device_name} — état inconnu ({value})",
                    detail=f"Registre : valeur inattendue = {value}",
                    fix_steps=[
                        f"Ouvrez : Paramètres → Confidentialité → {device_name}",
                    ]
                )

        except FileNotFoundError:
            # Clé absente = permission jamais demandée
            # → Demander la permission de manière native
            device_name = "Caméra" if device == DevicePermission.CAMERA else "Microphone"
            log.info(f"Clé registre {device_key} absente — Demande de permission native pour {device_name}")
            
            granted = self._request_permission_native(device)
            if granted:
                # Vérifier l'accès après demande
                ok, err = self._test_device_access(device)
                return PermissionResult(
                    device=device, state=PermissionState.GRANTED,
                    os_name="Windows",
                    message=f"✓ {device_name} autorisée",
                    detail="Permission accordée via demande native"
                )
            else:
                return PermissionResult(
                    device=device, state=PermissionState.DENIED,
                    os_name="Windows",
                    message=f"✗ Permission {device_name.lower()} refusée",
                    detail="L'utilisateur a refusé l'accès",
                    can_request=True,
                    fix_steps=[
                        f"Ouvrez : Paramètres → Confidentialité → {device_name}",
                        f"Activez l'accès à la {device_name.lower()} pour les applications de bureau.",
                        "Relancez l'application.",
                    ]
                )
        except OSError as e:
            # Accès registre refusé (GPO)
            return PermissionResult(
                device=device, state=PermissionState.RESTRICTED,
                os_name="Windows",
                message=f"⊘ {device_name} bloquée par politique d'entreprise",
                detail=str(e),
                fix_steps=[
                    "Contactez votre administrateur informatique.",
                    "La politique GPO de votre organisation restreint l'accès au registre.",
                ]
            )

    def _open_windows_settings(self, device: DevicePermission):
        """Ouvre les paramètres de confidentialité Windows."""
        page = (
            "ms-settings:privacy-webcam"
            if device == DevicePermission.CAMERA
            else "ms-settings:privacy-microphone"
        )
        try:
            subprocess.Popen(f"start {page}", shell=True)
        except Exception as e:
            log.warning(f"Impossible d'ouvrir les paramètres Windows : {e}")

    def _request_permission_native(self, device: DevicePermission) -> bool:
        """
        Demande la permission de manière native.
        Affiche la boîte de dialogue système de Windows pour la caméra ou le microphone.
        Retourne True si permission accordée, False sinon.
        """
        device_name = "Caméra" if device == DevicePermission.CAMERA else "Microphone"
        
        # Accès direct au périphérique (déclenche la boîte de dialogue native de Windows)
        log.info(f"Utilisation de l'accès direct au périphérique pour demander permission {device_name.lower()}")
        if device == DevicePermission.CAMERA:
            try:
                import cv2
                # Tenter d'ouvrir la caméra - cela déclenche la boîte de dialogue native si nécessaire
                cap = cv2.VideoCapture(0)
                if cap.isOpened():
                    cap.release()
                    log.info("Permission caméra accordée (accès direct)")
                    return True
                else:
                    log.info("Permission caméra refusée ou périphérique indisponible")
                    return False
            except Exception as e:
                log.warning(f"Erreur lors de la demande de permission caméra : {e}")
                return False
        else:  # MICROPHONE
            try:
                import sounddevice as sd
                # Tenter d'ouvrir un stream microphone - cela peut déclencher la boîte de dialogue native
                stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                         channels=1)
                stream.start()
                stream.stop()
                stream.close()
                log.info("Permission microphone accordée (accès direct)")
                return True
            except Exception as e:
                log.warning(f"Erreur lors de la demande de permission microphone : {e}")
                return False


    @staticmethod
    def _test_device_access(device: DevicePermission) -> Tuple[bool, str]:
        """
        Teste l'accès réel au périphérique en ouvrant brièvement la caméra
        ou le microphone. Retourne (success, error_message).
        Windows uniquement.
        """
        if device == DevicePermission.CAMERA:
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    cap.release()
                    return False, "cv2.VideoCapture(0) : isOpened() == False"
                ret, _ = cap.read()
                cap.release()
                if not ret:
                    return False, "Caméra ouverte mais aucune frame capturée"
                return True, ""
            except Exception as e:
                return False, str(e)

        else:  # MICROPHONE
            try:
                import sounddevice as sd
                # Tester les périphériques d'entrée disponibles
                devices = sd.query_devices()
                if devices is None or len(devices) == 0:
                    return False, "Aucun périphérique audio détecté par sounddevice"
                
                # Chercher un périphérique d'entrée valide
                found_input = False
                for i, device_info in enumerate(devices):
                    if device_info.get("max_input_channels", 0) > 0:
                        found_input = True
                        break
                
                if not found_input:
                    return False, "Aucun périphérique d'entrée (microphone) détecté"
                
                # Essai d'ouverture du stream
                stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                                         channels=1)
                stream.start()
                stream.stop()
                stream.close()
                return True, ""
            except OSError as e:
                err = str(e).lower()
                if "permission" in err or "access" in err or "denied" in err:
                    return False, f"Permission refusée : {e}"
                elif "no default" in err or "invalid" in err:
                    return False, f"Périphérique introuvable : {e}"
                return False, str(e)
            except Exception as e:
                return False, str(e)

    # ── Utilitaire : ouvrir les paramètres Windows ────────────────────────────
    def open_settings(self, device: DevicePermission):
        """Ouvre les paramètres de permissions Windows."""
        if self.os == "Windows": 
            self._open_windows_settings(device)
        else:
            log.warning(f"Configuration de permissions non supportée sur {self.os}")

    # ── Rapport global ────────────────────────────────────────────────────────
    def full_report(self) -> dict:
        cam, mic = self.check_all()
        return {
            "os":        self.os,
            "camera": {
                "state":     cam.state.name,
                "granted":   cam.granted,
                "message":   cam.message,
                "fix_steps": cam.fix_steps,
            },
            "microphone": {
                "state":     mic.state.name,
                "granted":   mic.granted,
                "message":   mic.message,
                "fix_steps": mic.fix_steps,
            }
        }


# ═════════════════════════════════════════════════════════════════════════════
# TEST EN LIGNE DE COMMANDE
# ═════════════════════════════════════════════════════════════════════════════

PERM_MGR_OK = True  # Toujours disponible car integre ci-dessus

# ── Config ────────────────────────────────────────────────────────────────────
class Config:
    VERSION      = "2.0.0"
    APP_NAME     = "BioAccess Secure"
    API_BASE_URL = "http://localhost:5000"   # ← adapter à votre backend
    API_TOKEN    = ""                         # ← token JWT si nécessaire

# ── Stockage local ────────────────────────────────────────────────────────────
DATA_DIR   = Path.home() / ".bioaccess"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
FACES_DIR  = DATA_DIR / "faces"
FACES_DIR.mkdir(exist_ok=True)

def load_users() -> dict:
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(u: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(u, f, ensure_ascii=False, indent=2)

# ── Palette ───────────────────────────────────────────────────────────────────
C_BG      = "#0a0e1a"
C_SURFACE = "#111827"
C_PANEL   = "#1a2236"
C_BORDER  = "#2a3a5c"
C_ACCENT  = "#00d4ff"
C_ACCENT2 = "#7c3aed"
C_SUCCESS = "#10b981"
C_ERROR   = "#ef4444"
C_WARNING = "#f59e0b"
C_TEXT    = "#e2e8f0"
C_MUTED   = "#64748b"
C_LOCK    = "#dc2626"

# ── 250 phrases d'authentification vocale ────────────────────────────────────
PHRASES = [
    "le soleil brille sur la montagne",
    "j'aime les journées ensoleillées en automne",
    "les étoiles scintillent dans le ciel nocturne",
    "la rivière coule doucement vers la mer",
    "les oiseaux chantent au lever du soleil",
    "le vent souffle dans les arbres de la forêt",
    "la neige recouvre les sommets enneigés",
    "les fleurs s'épanouissent au printemps",
    "la pluie tombe doucement sur les toits",
    "le feu crépite dans la cheminée",
    "les nuages défilent dans le ciel bleu",
    "la lune éclaire la nuit silencieuse",
    "les vagues déferlent sur le rivage",
    "la forêt est pleine de vie et de couleurs",
    "les enfants jouent dans le jardin fleuri",
    "la montagne domine la vallée verdoyante",
    "le chat dort paisiblement sur le canapé",
    "les livres sont la fenêtre sur le monde",
    "la musique adoucit les mœurs humaines",
    "le café chaud réchauffe les matins froids",
    "les papillons volent parmi les fleurs",
    "la mer est calme et transparente aujourd'hui",
    "les éclairs illuminent le ciel orageux",
    "la fontaine murmure dans le parc fleuri",
    "les arbres perdent leurs feuilles en automne",
    "la brise marine rafraîchit la journée chaude",
    "les étoiles filantes traversent la nuit d'été",
    "la rosée du matin brille sur l'herbe verte",
    "les montagnes se reflètent dans le lac",
    "le crépuscule peint le ciel de rouge et d'or",
    "les cigales chantent sous la chaleur estivale",
    "la forêt de pins embaume l'air frais",
    "les hirondelles annoncent le retour du printemps",
    "la tempête approche depuis l'horizon sombre",
    "les champs de blé ondulent sous le vent",
    "la cascade tombe avec fracas dans la gorge",
    "les renards jouent dans la clairière au crépuscule",
    "la brume matinale enveloppe la vallée endormie",
    "les cerisiers sont en fleurs au Japon",
    "la mer déchaînée brise les digues de pierre",
    "les corbeaux croassent sur la branche morte",
    "la lumière du phare guide les marins perdus",
    "les moutons paissent dans la prairie verdoyante",
    "la rivière serpente entre les collines boisées",
    "les aurores boréales dansent dans le ciel arctique",
    "le volcan crache de la lave rouge et fumante",
    "les dauphins sautent hors des vagues bleues",
    "la cloche du village sonne à midi pile",
    "les lavandes embaument la Provence en été",
    "le vent du nord apporte la neige et le froid",
    "les cigognes nichent sur les toits des maisons",
    "la bruyère rose couvre les landes d'Écosse",
    "les tornades ravagent les plaines du Midwest",
    "la sève monte dans les arbres au printemps",
    "les méduses flottent dans les eaux translucides",
    "la foudre frappe le chêne centenaire",
    "les moissons dorées réchauffent le paysage",
    "la grotte abrite des stalactites millénaires",
    "les chevaux galopent dans la plaine immense",
    "la brume de mer enveloppe le port endormi",
    "les pieuvres se cachent dans les rochers sous-marins",
    "les manchots marchent en file sur la banquise",
    "la savane africaine s'étend à perte de vue",
    "les coraux colorent les fonds marins tropicaux",
    "les baleines migrent vers les eaux chaudes du sud",
    "le désert de sel scintille sous le soleil ardent",
    "les loups hurlent à la pleine lune d'hiver",
    "les flamants roses se dressent dans le lagon rose",
    "le geyser jaillit toutes les heures avec précision",
    "les abeilles butinent les fleurs du verger fleuri",
    "les chouettes chassent silencieusement la nuit",
    "les libellules virevoltent au-dessus de l'étang",
    "les pingouins plongent dans les eaux glaciales",
    "la banquise fond à une vitesse alarmante",
    "les séquoias géants dominent la forêt californienne",
    "les caribous migrent sur des milliers de kilomètres",
    "les termites construisent des cathédrales de terre rouge",
    "le brouillard londonien cache les toits victoriens",
    "les poulpes changent de couleur en un instant",
    "les hérons pêchent immobiles au bord de l'eau",
    "la forêt amazonienne est le poumon de la planète",
    "les macareux colorés nichent sur les falaises",
    "les épaulards chassent en meute dans l'océan Pacifique",
    "les éléphants creusent des puits en période de sécheresse",
    "les albatros planent pendant des mois sans se poser",
    "les lémuriens gambadent dans les forêts de Madagascar",
    "les pandas géants mangent presque exclusivement du bambou",
    "les tortues marines reviennent pondre sur leur plage natale",
    "les gorilles des montagnes vivent sous la brume volcanique",
    "les condors des Andes planent à cinq mille mètres d'altitude",
    "la reconnaissance faciale analyse les traits biométriques uniques",
    "le système de sécurité vérifie votre identité en temps réel",
    "l'authentification forte garantit un accès sécurisé au poste",
    "le chiffrement protège les données sensibles des utilisateurs",
    "la reconnaissance vocale transforme la parole en texte précis",
    "les algorithmes d'apprentissage améliorent la précision biométrique",
    "la vérification d'identité numérique est fiable et rapide",
    "le réseau neuronal reconnaît les patterns biométriques complexes",
    "l'intelligence artificielle sécurise les accès informatiques modernes",
    "les aigles royaux survolent les sommets alpins enneigés",
    "la steppe kazakhe est battue par les vents froids du nord",
    "les loutres de rivière jouent dans le courant vif et clair",
    "les grillons chantent toute la nuit dans la prairie",
    "les mustangs courent librement dans les plaines du Nevada",
    "les monarques migrent de six mille kilomètres chaque automne",
    "les grues japonaises dansent leur parade sur les plaines enneigées",
    "les fous de Bassan plongent de trente mètres dans la mer",
    "les grenouilles arboricoles collent aux feuilles humides",
    "le blizzard polaire réduit la visibilité à presque zéro",
    "les vautours fauves planent dans les thermiques montagnards",
    "la fonte des neiges alimente les rivières de montagne",
    "les bouquetins traversent les pentes verglacées avec aisance",
    "les puffins fouisseurs creusent des terriers dans les dunes",
    "la caravane de chameaux traverse l'erg sans boussole",
    "les bécasses sondent la terre molle de leur long bec",
    "le verglas recouvre les routes d'un film dangereux",
    "la dépression atlantique apporte des pluies abondantes",
    "les hérissons hibernent de novembre à mars en Europe",
    "les troglodytes mignons nichent dans les souches pourries",
    "les couleuvres vertes et jaunes chassent les lézards",
    "le froid polaire fige le mercure à moins quarante degrés",
    "les milans royaux virevoltent dans les courants ascendants",
    "les baleines grises frottent leur dos sur les rochers",
    "les lièvres variables blanchissent avec les premières neiges",
    "la tornade aspire les toits des maisons préfabriquées",
    "le cordon littoral protège la lagune des tempêtes",
    "les belettes traquent les campagnols sous la neige",
    "la vague de chaleur dépasse les quarante degrés en ville",
    "le kelp géant forme des forêts sous-marines en Californie",
    "le Gulf Stream distribue la chaleur tropicale vers l'Europe",
    "les crabes des cocotiers grimpent aux palmiers la nuit",
    "la tourbière séquestre le carbone depuis des millénaires",
    "le cyclone tropical s'intensifie sur les eaux chaudes",
    "la digue de mer du Nord protège les polders depuis des siècles",
    "les rapaces nocturnes chassent grâce à leur ouïe parfaite",
    "les pluviers dorés voyagent de l'Arctique à l'Afrique",
    "la déforestation expose les sols à l'érosion pluviale",
    "les grèbes huppés dansent leur parade nuptiale sur le lac",
    "les cygnes tuberculés défendent leur territoire avec ardeur",
    "le nuage de cendres arrête les vols aériens pendant des jours",
    "les lézards des murailles se chauffent sur les pierres chaudes",
    "les phoques se prélassent sur les rochers de Bretagne",
    "les merles chantent dès l'aube dans les jardins de la ville",
    "le brouillard givrant habille les arbres d'une robe blanche",
    "les renards urbains fouillent les poubelles la nuit",
    "la prairie fleurie attire les papillons au printemps",
    "les fourmis portent cent fois leur propre poids",
    "les lynx patrouillent les forêts boréales du Canada",
    "les otaries aboyantes peuplent les côtes chiliennes",
    "les baleines à bosse chantent des mélodies complexes",
    "les tapirs nagent dans les rivières d'Amérique du Sud",
    "les tritons crêtés hibernent dans la vase des étangs",
    "les vagues déferlent sur les récifs coralliens colorés",
    "les flamants roses filtrent la vase avec leur bec courbe",
    "les grands ducs chassent les lapins en plaine ouverte",
    "le mistral refroidit la Provence plusieurs jours de suite",
    "les porcs-épics hérissent leurs piquants face au prédateur",
    "la grêle hache les vignes en quelques minutes seulement",
    "les geais des chênes cachent des glands pour l'hiver",
    "les vanneaux huppés nichent dans les prairies humides",
    "les sangliers ravagent les cultures de maïs en forêt",
    "la suberaie produit le liège tous les neuf ans environ",
    "les éperviers fondent en piqué sur les moineaux",
    "les alouettes montent en spirale dans le ciel du matin",
    "les icebergs dérivent lentement depuis le Groenland",
    "les piranhas peuplent les rivières amazoniennes",
    "le sirocco apporte un air chaud et sec du Sahara",
    "les loutres de mer dorment enlacées dans les algues",
    "le permafrost dégèle et libère du méthane dans l'atmosphère",
    "les cigales stridulent sans relâche les nuits d'été",
    "les biches et leurs faons traversent la route en forêt",
    "les renards d'oreilles de fennec survivent dans le Sahara",
    "la pollution lumineuse perturbe la migration des oiseaux nocturnes",
    "les tritons alpestres se reproduisent dans les mares froides",
    "la vague scélérate surprend les marins en haute mer",
    "le chablis laisse des arbres déracinés après la tempête",
    "les geysers d'Islande alimentent les serres de tomates",
    "les canards colverts reviennent chaque hiver sur le lac",
    "la dorsale médio-atlantique s'étire sous l'océan profond",
    "la palmeraie verdoyante contraste avec le désert aride",
    "les pélicans plongent en piqué dans la mer bleue",
    "la sécheresse transforme les rivières en filets d'eau",
    "les dauphins jouent dans le sillage des bateaux",
    "le volcan en éruption illumine le ciel nocturne",
    "les manchots empereurs couvent leurs œufs dans le blizzard",
    "les loups gris chassent en meute dans la taïga",
    "la forêt tropicale abrite des millions d'espèces animales",
    "les cormorans étendent leurs ailes pour les sécher au soleil",
    "la marée basse révèle les rochers couverts d'algues vertes",
    "les grues cendrées forment de grands V dans le ciel d'automne",
    "le brouillard matinal se dissipe avec le soleil levant",
    "les fougères arborescentes peuplent les forêts néo-zélandaises",
    "la neige poudreuse recouvre silencieusement la forêt",
    "les albatros royaux planent sans effort sur les courants d'air",
    "la tempête de sable obscurcit le ciel du Sahara pendant des heures",
    "les pieuvres géantes habitent les fosses océaniques profondes",
    "le mistral balaie les lavandes de Haute-Provence",
    "les lynx ibériques chassent dans les forêts espagnoles",
    "la mousson transforme les plaines arides en marécages fertiles",
    "les oiseaux de paradis paradent dans la jungle papouasienne",
    "les orques coordonnent leurs attaques avec une précision remarquable",
    "la sargasse envahit les plages des Caraïbes chaque été",
    "les poulpes intelligents résolvent des énigmes complexes",
    "la banquise arctique atteint son minimum en septembre chaque année",
    "les guépards courent à cent dix kilomètres par heure",
    "les fourmis leafcutter découpent les feuilles en petits morceaux",
    "les murènes se cachent dans les crevasses coralliennes",
    "la forêt de bouleaux frémit sous la brise arctique légère",
    "les hippocampes mâles portent les petits dans leur poche ventrale",
    "le platane centenaire abrite des centaines d'oiseaux chanteurs",
    "les libellules chassent les moustiques avec une précision redoutable",
    "la cigogne blanche revient fidèlement chaque printemps au village",
    "les loutres géantes pêchent en famille dans l'Amazone",
    "le flamant rose doit sa couleur aux crevettes qu'il consomme",
    "les baleines franches migrent sur des milliers de kilomètres",
    "les caribous traversent les rivières gonflées par la fonte des neiges",
    "le martin-pêcheur plonge comme une flèche dans l'eau claire",
    "les renards jouent dans les champs couverts de givre",
    "la mouette rieuse survole les ports en quête de nourriture",
    "les hiboux grand-duc règnent sur les nuits de la garrigue",
    "les grenouilles rousses chantent dès les premières pluies de mars",
]


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  MODULE D'INTÉGRITÉ — INTÉGRÉ DIRECTEMENT DANS L'APPLICATION               ║
# ║  (synchronisé avec integrity_check.py — même logique, même API)            ║
# ╚══════════════════════════════════════════════════════════════════════════════

# ── Constantes sceau ──────────────────────────────────────────────────────────
_SEAL_DIR     = DATA_DIR / "seal"
_SEAL_DIR.mkdir(exist_ok=True)
_SEAL_FILE    = _SEAL_DIR / "install.seal"
_JOURNAL_FILE = _SEAL_DIR / "integrity.log"
_HMAC_KEY     = b"BioAccess-Secure-IntegrityKey-2025-v2"


class IntegrityStatus(Enum):
    OK            = auto()
    FIRST_INSTALL = auto()
    REINSTALLED   = auto()
    DATA_WIPED    = auto()
    TAMPERED      = auto()

    @property
    def is_critical(self) -> bool:
        return self in (IntegrityStatus.TAMPERED,
                        IntegrityStatus.REINSTALLED,
                        IntegrityStatus.DATA_WIPED)

    @property
    def severity(self) -> str:
        return {
            IntegrityStatus.TAMPERED:    "haute",
            IntegrityStatus.DATA_WIPED:  "haute",
            IntegrityStatus.REINSTALLED: "moyenne",
            IntegrityStatus.FIRST_INSTALL: "basse",
            IntegrityStatus.OK:          "basse",
        }[self]

    @property
    def ui_color(self) -> str:
        return {
            IntegrityStatus.TAMPERED:    C_LOCK,
            IntegrityStatus.DATA_WIPED:  C_ERROR,
            IntegrityStatus.REINSTALLED: C_WARNING,
            IntegrityStatus.FIRST_INSTALL: C_SUCCESS,
            IntegrityStatus.OK:          C_SUCCESS,
        }[self]

    @property
    def ui_label(self) -> str:
        return {
            IntegrityStatus.TAMPERED:    "🚨 INTÉGRITÉ COMPROMISE",
            IntegrityStatus.DATA_WIPED:  "⚠ Données effacées",
            IntegrityStatus.REINSTALLED: "⚠ Réinstallation détectée",
            IntegrityStatus.FIRST_INSTALL: "✓ Premier enregistrement",
            IntegrityStatus.OK:          "✓ Intégrité vérifiée",
        }[self]


class IntegrityGuard:
    """
    Moteur d'intégrité intégré à BioAccess Secure.
    Vérifie l'authenticité de l'exe, détecte les compromis,
    et envoie des alertes à l'administrateur via POST /api/v1/alerts.
    """

    def __init__(self):
        self.exe_path = (Path(sys.executable)
                         if getattr(sys, "frozen", False)
                         else Path(__file__).resolve())
        self.exe_hash: Optional[str] = None

    # ── Hash SHA-256 de l'exe ─────────────────────────────────────────────────
    def compute_exe_hash(self) -> str:
        sha = hashlib.sha256()
        try:
            with open(self.exe_path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    sha.update(chunk)
            return sha.hexdigest()
        except (PermissionError, OSError):
            return self._partial_hash()

    def _partial_hash(self) -> str:
        sha = hashlib.sha256()
        try:
            size = self.exe_path.stat().st_size
            with open(self.exe_path, "rb") as f:
                sha.update(f.read(min(524288, size)))
                if size > 524288:
                    f.seek(-524288, 2)
                    sha.update(f.read())
            return sha.hexdigest() + "-partial"
        except Exception:
            return "unknown"

    # ── Empreinte machine ─────────────────────────────────────────────────────
    @staticmethod
    def _machine_fp() -> str:
        parts = [platform.node(), platform.machine(),
                 platform.system(), str(Path.home())]
        if platform.system() == "Windows":
            try:
                r = subprocess.run(["wmic", "os", "get", "SerialNumber"],
                                   capture_output=True, text=True, timeout=3)
                parts.append(r.stdout.strip())
            except Exception:
                pass
        elif platform.system() == "Linux":
            try:
                parts.append(Path("/etc/machine-id").read_text().strip())
            except Exception:
                pass
        return hashlib.sha256("|".join(parts).encode()).hexdigest()[:32]

    # ── HMAC ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _sign(data: dict) -> str:
        return hmac.new(_HMAC_KEY,
                        json.dumps(data, sort_keys=True).encode(),
                        hashlib.sha256).hexdigest()

    @staticmethod
    def _verify(data: dict, sig: str) -> bool:
        return hmac.compare_digest(
            hmac.new(_HMAC_KEY,
                     json.dumps(data, sort_keys=True).encode(),
                     hashlib.sha256).hexdigest(),
            sig)

    # ── Sceau ─────────────────────────────────────────────────────────────────
    def _load_seal(self) -> Optional[dict]:
        if not _SEAL_FILE.exists():
            return None
        try:
            env  = json.loads(_SEAL_FILE.read_text(encoding="utf-8"))
            sig  = env.pop("__sig__", "")
            if not self._verify(env, sig):
                return None   # falsifié
            return env
        except Exception:
            return None

    def _save_seal(self, exe_hash: str, reason: str = "install"):
        old  = self._load_seal() or {}
        data = {
            "exe_hash":      exe_hash,
            "machine_fp":    self._machine_fp(),
            "install_date":  old.get("install_date", datetime.now().isoformat()),
            "last_verified": datetime.now().isoformat(),
            "app_version":   Config.VERSION,
            "reason":        reason,
            "install_count": old.get("install_count", 0) + 1,
            "hostname":      platform.node(),
            "platform":      platform.system(),
        }
        data["__sig__"] = self._sign(data)
        _SEAL_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                              encoding="utf-8")

    def _touch_seal(self, seal: dict):
        s = {k: v for k, v in seal.items() if k != "__sig__"}
        s["last_verified"] = datetime.now().isoformat()
        s["__sig__"] = self._sign(s)
        try:
            _SEAL_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False),
                                  encoding="utf-8")
        except Exception:
            pass

    # ── Journal ───────────────────────────────────────────────────────────────
    @staticmethod
    def _log(event: str, detail: str = ""):
        entry = {"ts": datetime.now().isoformat(), "event": event,
                 "detail": detail, "host": platform.node()}
        try:
            with open(_JOURNAL_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ── Alerte admin ──────────────────────────────────────────────────────────
    def _alert_admin(self, status: IntegrityStatus,
                     message: str, seal: Optional[dict] = None):
        """
        Envoie une alerte à l'administrateur via POST /api/v1/alerts.
        Format identique à celui attendu par alerts.html.
        Si le backend est hors ligne, l'alerte est mise en file locale.
        """
        if not REQUESTS_OK:
            self._log("ALERT_SKIP", "requests non disponible")
            return

        host    = platform.node()
        seal    = seal or {}
        payload = {
            "titre":       f"{status.ui_label} — {host}",
            "description": message,
            "gravite":     status.severity,
            "resource":    f"poste-{host}",
            "type":        "integrity_violation",
            "allow_access": False,
            "traitee":     False,
            "date_creation": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "metadata": {
                "exe_hash_nouveau":   self.exe_hash or "?",
                "exe_hash_precedent": seal.get("exe_hash", "inconnu"),
                "machine_fp":         seal.get("machine_fp", "?"),
                "install_count":      seal.get("install_count", 0),
                "platform":           platform.system(),
                "hostname":           host,
                "status_code":        status.name,
                "detected_at":        datetime.now().isoformat(),
            }
        }
        headers = {"Content-Type": "application/json"}
        if Config.API_TOKEN:
            headers["Authorization"] = f"Bearer {Config.API_TOKEN}"
        url = f"{Config.API_BASE_URL}/api/v1/alerts"

        def _post():
            try:
                r = requests.post(url, json=payload, headers=headers, timeout=5)
                if r.status_code in (200, 201):
                    self._log("ALERT_SENT", f"HTTP {r.status_code} status={status.name}")
                else:
                    self._log("ALERT_FAILED", f"HTTP {r.status_code}")
                    self._queue(payload)
            except requests.exceptions.ConnectionError:
                self._log("ALERT_QUEUED", "backend hors ligne")
                self._queue(payload)
            except Exception as e:
                self._log("ALERT_ERROR", str(e))

        threading.Thread(target=_post, daemon=True).start()

    def _queue(self, payload: dict):
        """File locale des alertes non envoyées (backend hors ligne)."""
        qf = _SEAL_DIR / "pending_alerts.json"
        try:
            q = json.loads(qf.read_text()) if qf.exists() else []
            q.append(payload)
            qf.write_text(json.dumps(q, indent=2, ensure_ascii=False))
        except Exception:
            pass

    def flush_pending(self):
        """Renvoie les alertes en attente. Appelé au prochain démarrage."""
        if not REQUESTS_OK:
            return
        qf = _SEAL_DIR / "pending_alerts.json"
        if not qf.exists():
            return

        def _flush():
            try:
                q = json.loads(qf.read_text())
                if not q:
                    return
                headers = {"Content-Type": "application/json"}
                if Config.API_TOKEN:
                    headers["Authorization"] = f"Bearer {Config.API_TOKEN}"
                sent = []
                for p in q:
                    try:
                        r = requests.post(f"{Config.API_BASE_URL}/api/v1/alerts",
                                          json=p, headers=headers, timeout=4)
                        if r.status_code in (200, 201):
                            sent.append(p)
                    except Exception:
                        break
                remaining = [p for p in q if p not in sent]
                qf.write_text(json.dumps(remaining, indent=2, ensure_ascii=False))
                if sent:
                    self._log("FLUSH", f"{len(sent)} alerte(s) en attente envoyée(s)")
            except Exception as e:
                self._log("FLUSH_ERR", str(e))

        threading.Thread(target=_flush, daemon=True).start()

    # ── Vérification principale ───────────────────────────────────────────────
    def verify(self) -> Tuple[IntegrityStatus, str]:
        """
        Appelé au démarrage de l'application.
        Retourne (IntegrityStatus, message_UI).
        Déclenche automatiquement une alerte admin si statut critique.
        """
        self.flush_pending()
        self.exe_hash = self.compute_exe_hash()
        seal          = self._load_seal()

        # ── Cas 1 : Premier lancement ─────────────────────────────────────────
        if not _SEAL_FILE.exists():
            self._save_seal(self.exe_hash, "first_install")
            self._log("FIRST_INSTALL", f"hash={self.exe_hash[:16]}")
            return (IntegrityStatus.FIRST_INSTALL,
                    f"Premier lancement sur {platform.node()}.\n"
                    f"Sceau de sécurité créé.")

        # ── Cas 2 : Sceau falsifié (HMAC invalide) ───────────────────────────
        if seal is None:
            self._log("TAMPERED", "HMAC invalide")
            msg = (f"COMPROMIS D'INTÉGRITÉ sur {platform.node()} :\n"
                   f"Le sceau de sécurité a été modifié ou corrompu.\n"
                   f"L'administrateur a été alerté immédiatement.")
            self._alert_admin(IntegrityStatus.TAMPERED, msg,
                              {"exe_hash": "tampered", "machine_fp": self._machine_fp()})
            return IntegrityStatus.TAMPERED, msg

        # ── Cas 3 : Hash identique → Tout va bien ────────────────────────────
        if seal.get("exe_hash") == self.exe_hash:
            self._touch_seal(seal)
            self._log("OK", f"hash={self.exe_hash[:16]}")
            return IntegrityStatus.OK, "Application authentique."

        # ── Cas 4 : Hash différent → Réinstallation ───────────────────────────
        uf          = DATA_DIR / "users.json"
        data_ok     = uf.exists() and uf.stat().st_size > 4
        faces_count = len(list(FACES_DIR.glob("*.yml"))) if FACES_DIR.exists() else 0
        inst        = seal.get("install_count", 1)
        old_hash    = seal.get("exe_hash", "?")

        self._save_seal(self.exe_hash, "reinstall")

        if data_ok:
            status = IntegrityStatus.REINSTALLED
            msg = (f"Réinstallation détectée sur {platform.node()} "
                   f"(installation n°{inst + 1}).\n"
                   f"Données préservées : {faces_count} profil(s).\n"
                   f"Hash précédent : {old_hash[:16]}...\n"
                   f"Hash actuel    : {self.exe_hash[:16]}...")
        else:
            status = IntegrityStatus.DATA_WIPED
            msg = (f"Réinstallation avec perte de données sur {platform.node()} "
                   f"(installation n°{inst + 1}).\n"
                   f"Aucune donnée biométrique trouvée.\n"
                   f"Les utilisateurs devront se réenregistrer.")

        self._log(status.name,
                  f"old={old_hash[:16]} new={self.exe_hash[:16]} "
                  f"data={'ok' if data_ok else 'wiped'} faces={faces_count}")
        # ── Alerte admin ──────────────────────────────────────────────────────
        self._alert_admin(status, msg, seal)
        return status, msg


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  CANVAS ANIMÉ                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════

def _mix(hex_color: str, alpha: float) -> str:
    hc = hex_color.lstrip("#")
    r, g, b   = int(hc[0:2], 16), int(hc[2:4], 16), int(hc[4:6], 16)
    br, bg, bb= int(C_BG[1:3], 16), int(C_BG[3:5], 16), int(C_BG[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r*alpha + br*(1-alpha)),
        int(g*alpha + bg*(1-alpha)),
        int(b*alpha + bb*(1-alpha)))


class AnimatedCanvas(tk.Canvas):
    def __init__(self, parent, mode: str = "face", **kwargs):
        super().__init__(parent, bg=C_BG, highlightthickness=0, **kwargs)
        self.mode      = mode
        self._running  = False
        self._angle    = 0
        self._pulse    = 0.0
        self._scan_y   = 0
        self._scan_dir = 1
        self._success  = False
        self._fail     = False
        self._frame_id = None

    def start(self):
        self._running = True
        self._success = self._fail = False
        self._animate()

    def stop(self):
        self._running = False
        if self._frame_id:
            self.after_cancel(self._frame_id)

    def show_success(self): self._success = True;  self._fail    = False
    def show_fail(self):    self._fail    = True;   self._success = False

    def _animate(self):
        if not self._running:
            return
        self.delete("all")
        w  = self.winfo_width()  or 320
        h  = self.winfo_height() or 320
        cx, cy = w // 2, h // 2

        # Particules étoiles
        for i in range(30):
            sx = (i*97 + int(self._angle*0.3)) % w
            sy = (i*53 + int(self._angle*0.2)) % h
            r  = 1 if i % 3 else 2
            self.create_oval(sx-r, sy-r, sx+r, sy+r,
                             fill=_mix(C_ACCENT, 0.3+0.2*math.sin(self._angle*0.05+i)),
                             outline="")

        if   self.mode == "face":  self._draw_face(cx, cy, w, h)
        elif self.mode == "voice": self._draw_voice(cx, cy, w, h)
        else:                      self._draw_lock(cx, cy, w, h)

        self._angle += 2
        self._pulse  = (self._pulse + 0.08) % (2*math.pi)
        size = int(min(w, h) * 0.55)
        self._scan_y += 2 * self._scan_dir
        if   self._scan_y >  size // 2: self._scan_dir = -1
        elif self._scan_y < -size // 2: self._scan_dir =  1
        self._frame_id = self.after(30, self._animate)

    def _draw_lock(self, cx, cy, w, h):
        c     = C_LOCK
        pulse = int(4 + 3*math.sin(self._pulse*2))
        for mult in [0.35, 0.48, 0.60]:
            r = int(min(w,h)*mult + pulse*math.sin(self._pulse+mult*4))
            self.create_oval(cx-r, cy-r, cx+r, cy+r,
                             outline=_mix(c, 0.18-mult*0.1), width=1)
        step = max(1, int(min(w,h)*0.1))
        for i in range(0, w, step):
            self.create_line(i, 0, i, h, fill=_mix(c, 0.04))
        for i in range(0, h, step):
            self.create_line(0, i, w, i, fill=_mix(c, 0.04))
        lw, lh = 64, 52
        lx, ly = cx-lw//2, cy-8
        self.create_rectangle(lx, ly, lx+lw, ly+lh,
                              fill=_mix(c, 0.28), outline=_mix(c, 0.9), width=3)
        self.create_arc(lx+10, cy-62, lx+lw-10, cy,
                        start=0, extent=180, outline=_mix(c, 0.9), style="arc", width=3)
        kr = 10
        self.create_oval(cx-kr, cy+10-kr, cx+kr, cy+10+kr,
                         fill=_mix(c, 0.5), outline=_mix(c, 0.9), width=2)
        self.create_rectangle(cx-5, cy+10, cx+5, ly+lh-10,
                              fill=_mix(c, 0.5), outline="")

    def _draw_face(self, cx, cy, w, h):
        size  = int(min(w,h)*0.55)
        x0,y0 = cx-size//2, cy-size//2
        x1,y1 = cx+size//2, cy+size//2
        color = C_SUCCESS if self._success else (C_ERROR if self._fail else C_ACCENT)
        pw    = int(4+2*math.sin(self._pulse))
        step  = size//8
        for i in range(0, size+1, step):
            c = _mix(color, 0.08)
            self.create_line(x0+i, y0, x0+i, y1, fill=c)
            self.create_line(x0, y0+i, x1, y0+i, fill=c)
        fc = int(size*0.35)
        self.create_oval(cx-fc, cy-fc-size//12, cx+fc, cy+fc-size//12,
                         outline=_mix(color,0.3), width=1, fill=_mix(color,0.12))
        ey,ex,ew = cy-size//10, int(fc*0.4), int(fc*0.18)
        for s in (-1,1):
            self.create_oval(cx+s*ex-ew, ey-ew//2, cx+s*ex+ew, ey+ew//2,
                             outline=_mix(color,0.5), width=1, fill="")
        corner = size//5
        for dx,dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:
            ox = x0 if dx<0 else x1; oy = y0 if dy<0 else y1
            self.create_line(ox, oy, ox+dx*corner, oy, fill=color, width=pw)
            self.create_line(ox, oy, ox, oy+dy*corner, fill=color, width=pw)
        if not self._success and not self._fail:
            sy  = cy+self._scan_y
            alp = 0.6+0.3*math.sin(self._pulse*2)
            if y0 < sy < y1:
                self.create_line(x0+4, sy, x1-4, sy, fill=_mix(color,alp), width=2)
                for off in range(1,6):
                    self.create_line(x0+4, sy-off, x1-4, sy-off,
                                     fill=_mix(color, max(0,alp-off*0.1)), width=1)
        radius = size//2+15
        for i in range(0,360,5):
            rad = math.radians(i+self._angle)
            x2  = cx+radius*math.cos(rad); y2 = cy+radius*math.sin(rad)
            self.create_oval(x2-1,y2-1,x2+1,y2+1,
                             fill=_mix(color,0.1+0.4*math.sin(math.radians(i))),
                             outline="")
        if   self._success: self.create_text(cx,y1+25,text="✓  ACCÈS AUTORISÉ", fill=C_SUCCESS,font=("Courier",12,"bold"))
        elif self._fail:    self.create_text(cx,y1+25,text="✗  ACCÈS REFUSÉ",   fill=C_ERROR,  font=("Courier",12,"bold"))
        else:               self.create_text(cx,y1+25,
                                text=f"SCAN EN COURS  {int(abs(self._scan_y/(size/2))*100)}%",
                                fill=_mix(color,0.8),font=("Courier",10))

    def _draw_voice(self, cx, cy, w, h):
        color = C_SUCCESS if self._success else (C_ERROR if self._fail else "#a855f7")
        bars  = 32; bw = w//(bars*2)
        for i in range(bars):
            x   = cx-bars//2*(bw*2)+i*bw*2
            amp = 4 if (self._success or self._fail) else max(4, int(
                h*0.25*abs(math.sin(math.radians(i*12+self._angle*3+self._pulse*30)))))
            self.create_rectangle(x,cy-amp,x+bw-1,cy+amp,
                                  fill=_mix(color,0.4+0.5*(i/bars)),outline="")
        for rm in [0.25,0.4,0.55]:
            r = int(min(w,h)*rm+5*math.sin(self._pulse+rm*5))
            self.create_oval(cx-r,cy-r,cx+r,cy+r,
                             outline=_mix(color,0.2-rm*0.1),width=1)
        mw,mh = 14,22
        self.create_rectangle(cx-mw//2,cy-mh//2-5,cx+mw//2,cy+mh//2-5,
                              fill=_mix(color,0.3),outline=_mix(color,0.8),width=2)
        self.create_arc(cx-mw,cy+mh//2-5,cx+mw,cy+mh*1.2-5,
                        start=0,extent=180,outline=_mix(color,0.8),style="arc",width=2)
        self.create_line(cx,cy+mh-5,cx,cy+mh*1.6-5,fill=_mix(color,0.8),width=2)
        if   self._success: self.create_text(cx,cy+80,text="✓  VOIX RECONNUE",     fill=C_SUCCESS,font=("Courier",12,"bold"))
        elif self._fail:    self.create_text(cx,cy+80,text="✗  VOIX NON RECONNUE", fill=C_ERROR,  font=("Courier",12,"bold"))
        else:               self.create_text(cx,cy+80,text="● ÉCOUTE EN COURS...", fill=_mix(color,0.9),font=("Courier",10,"bold"))


# ╔══════════════════════════════════════════════════════════════════════════════
# ║  APPLICATION PRINCIPALE                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════

class BioAccessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # ── État ──────────────────────────────────────────────────────────────
        self._locked            = False  # fenêtre normale au démarrage
        self._uid_submitted     = False  # verrou activé au 1er User_ID soumis
        self._admin_granted     = False
        self._auth_done         = False
        self._authenticated_uid = ""
        self._stop_event        = threading.Event()
        self._current_phrase    = ""
        self._integrity_guard   = IntegrityGuard()
        self._permissions_ok    = False  # Permissions requises pour l'auth biométrique
        self._permissions_checked = False

        self.title(f"BioAccess Secure v{Config.VERSION}")
        self.configure(bg=C_BG)
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1060x720+{(sw-1060)//2}+{(sh-720)//2}")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._screens = {}
        self._build_ui()
        self.show_screen("lock")

        # Intégrité + surveillance admin lancées après affichage
        self.after(400, self._run_integrity_check)
        # PRIORITAIRE : Vérification permissions périphériques biométriques AVANT l'auth
        self.after(300, self._run_permissions_check_mandatory)
        self._poll_admin()

    # ══════════════════════════════════════════════════════════════════════════
    # VERROU SYSTÈME
    # ══════════════════════════════════════════════════════════════════════════
    def _apply_lock(self):
        """
        Active le mode kiosque plein écran.
        ⚠ Appelé UNIQUEMENT à la première soumission du User_ID,
          jamais au démarrage.
        """
        self._locked = True
        self.overrideredirect(True)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        for seq in ("<Alt-F4>","<Alt-Tab>","<Super_L>","<Super_R>",
                    "<Control-Escape>","<Escape>","<F11>"):
            self.bind(seq, self._block)
        self.protocol("WM_DELETE_WINDOW", self._block)
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.user32.BlockInput(True)
            except Exception:
                pass

    def _unlock_window(self):
        """Restaure la fenêtre normale après auth réussie."""
        self._locked = False
        self.overrideredirect(False)
        self.attributes("-fullscreen", False)
        self.attributes("-topmost", False)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        for seq in ("<Alt-F4>","<Alt-Tab>","<Super_L>","<Super_R>",
                    "<Control-Escape>","<Escape>","<F11>"):
            self.unbind(seq)
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.user32.BlockInput(False)
            except Exception:
                pass
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"1060x720+{(sw-1060)//2}+{(sh-720)//2}")

    def _block(self, event=None):
        return "break"

    # ══════════════════════════════════════════════════════════════════════════
    # INTÉGRITÉ — vérification au démarrage + bandeau UI
    # ══════════════════════════════════════════════════════════════════════════
    def _run_integrity_check(self):
        """
        Vérifie l'intégrité en arrière-plan.
        • Si OK → silencieux
        • Si compromis → carte de notification dans le coin inférieur droit
          qui se déplace légèrement vers le milieu
        """
        def check():
            status, message = self._integrity_guard.verify()

            def show_notification(s: IntegrityStatus, m: str):
                if s == IntegrityStatus.OK:
                    return  # Aucune action visible

                color     = s.ui_color
                label     = s.ui_label
                fg_color  = "white" if color not in (C_WARNING,) else C_BG
                # Texte court pour la notification
                short_msg = m.split("\n")[0][:90]

                # Créer la carte de notification
                card = tk.Frame(self, bg=color, highlightthickness=2, 
                               highlightbackground=_mix(color, 0.7), relief="raised")
                card.configure(padx=12, pady=10)

                # Contenu de la carte
                content_frame = tk.Frame(card, bg=color)
                content_frame.pack(fill="both", expand=True)

                # Texte label + message
                text_frame = tk.Frame(content_frame, bg=color)
                text_frame.pack(side="left", fill="both", expand=True)
                
                tk.Label(text_frame,
                         text=f"{label}  —  {short_msg}",
                         bg=color, fg=fg_color,
                         font=("Courier", 9, "bold"),
                         anchor="w", justify="left", wraplength=280).pack(fill="x")

                # Boutons (verticalement à droite)
                buttons_frame = tk.Frame(content_frame, bg=color)
                buttons_frame.pack(side="right", padx=(8, 0))

                # Bouton "Détails"
                def show_detail():
                    messagebox.showwarning("Intégrité BioAccess", m, parent=self)

                tk.Button(buttons_frame, text="📋 Détails", bg=_mix(color, 0.9), 
                         fg=fg_color, font=("Courier", 8), bd=0, cursor="hand2",
                         padx=6, pady=2,
                         activebackground=_mix(color, 0.7),
                         command=show_detail).pack(pady=(0, 4))

                # Bouton fermer (sauf TAMPERED)
                if s != IntegrityStatus.TAMPERED:
                    tk.Button(buttons_frame, text="✕", bg=_mix(color, 0.9), 
                             fg=fg_color, font=("Courier", 10, "bold"), bd=0, 
                             cursor="hand2", padx=6, pady=2,
                             activebackground=_mix(color, 0.7),
                             command=card.destroy).pack()

                # Placer la carte dans le coin inférieur droit
                # Position initiale : coin inférieur droit
                card.place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-16)
                card.update_idletasks()
                
                # Animation : glisser vers le milieu droit avec ease-out
                card_width = card.winfo_width()
                card_height = card.winfo_height()
                screen_width = self.winfo_screenwidth()
                screen_height = self.winfo_screenheight()
                
                # Position finale : milieu de la partie droite
                # x final : 80% vers la droite
                # y final : centre vertical
                x_start = -16
                y_start = -16
                x_end = -(card_width + 16)  # Reste à droite mais plus proche du centre
                y_end = -card_height // 2   # Centre vertical par rapport au bas
                
                duration = 600  # ms
                start_time = time.time()
                
                def animate():
                    elapsed = (time.time() - start_time) * 1000
                    if elapsed >= duration:
                        # Position finale
                        card.place(relx=1.0, rely=1.0, anchor="se", 
                                  x=x_end, y=y_end)
                        return
                    
                    # Ease-out cubic
                    progress = elapsed / duration
                    eased = 1 - (1 - progress) ** 3
                    
                    x = x_start + (x_end - x_start) * eased
                    y = y_start + (y_end - y_start) * eased
                    
                    card.place(relx=1.0, rely=1.0, anchor="se", x=int(x), y=int(y))
                    self.after(16, animate)
                
                animate()

                # Auto-dismiss après 12 s (sauf TAMPERED)
                if s != IntegrityStatus.TAMPERED:
                    def auto_dismiss():
                        if card.winfo_exists():
                            card.destroy()
                    self.after(12000, auto_dismiss)

            self.after(0, lambda: show_notification(status, message))

        threading.Thread(target=check, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════════
    # PERMISSIONS BIOMÉTRIQUES — vérification OBLIGATOIRE au démarrage
    # ══════════════════════════════════════════════════════════════════════════
    def _run_permissions_check_mandatory(self):
        """
        Vérifie caméra + microphone AVANT de permettre l'authentification.
        BLOQUE l'interface jusqu'à ce que les permissions soient accordées.
        Affiche le statut COMPLET (accordées + refusées).
        """
        if not PERM_MGR_OK:
            self._permissions_ok = True
            self._permissions_checked = True
            return
        
        def check():
            mgr        = PermissionManager()
            cam_result = mgr.check_and_request(DevicePermission.CAMERA)
            mic_result = mgr.check_and_request(DevicePermission.MICROPHONE)
            
            # Vérifier si AU MOINS une permission est accordée
            # (on peut utiliser face OU voix)
            if cam_result.granted or mic_result.granted:
                self._permissions_ok = True
            else:
                self._permissions_ok = False
            
            self._permissions_checked = True
            
            # Afficher TOUJOURS le dialogue avec le statut COMPLET des permissions
            all_results = [
                ("Caméra", cam_result),
                ("Microphone", mic_result)
            ]
            
            self.after(0, lambda: self._show_permission_dialog_mandatory(all_results, mgr))
        
        threading.Thread(target=check, daemon=True).start()

    def _show_permission_dialog_mandatory(self, problems: list, mgr):
        """
        Dialogue BLOQUANT pour les permissions.
        Affiche l'état COMPLET des DEUX permissions (caméra + microphone).
        - Permissions ACCORDÉES : affichage vert avec checkmark
        - Permissions REFUSÉES : affichage rouge avec étapes correctives
        Permet de demander l'accès via Windows Paramètres nativement.
        """
        os_name = platform.system()
        os_lbl  = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}.get(os_name, os_name)

        dlg = tk.Toplevel(self)
        dlg.title("🔒 Permissions biométriques OBLIGATOIRES")
        dlg.configure(bg=C_BG)
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # Désactiver le X
        dlg.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        dlg.geometry(f"750x850+{(sw-750)//2}+{(sh-850)//2}")

        # En-tête : couleur adaptée selon statut global
        # Si AU MOINS une permission est accordée → EN-TÊTE MIXTE/POSITIF
        has_granted = any(result.granted for _, result in problems)
        header_bg = C_SUCCESS if has_granted and all(result.granted for _, result in problems) else C_ERROR
        header_text = "✓  PERMISSIONS BIOMÉTRIQUES  —  Status Complet" if has_granted else "🔒  PERMISSIONS REQUISES"
        
        hdr = tk.Frame(dlg, bg=header_bg, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,
                 text=f"  {header_text}  —  {os_lbl}",
                 bg=header_bg, fg="white" if header_bg == C_ERROR else C_BG,
                 font=("Courier", 12, "bold")).pack(side="left", padx=12, fill="y")

        body = tk.Frame(dlg, bg=C_BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        
        # Texte descriptif adapté au contexte
        if all(result.granted for _, result in problems):
            desc_text = "✓ Toutes les permissions biométriques sont ACCORDÉES !\nVous pouvez procéder à l'authentification."
            desc_color = C_SUCCESS
        elif any(result.granted for _, result in problems):
            desc_text = "⚠ Certaines permissions sont accordées, d'autres manquent.\nVeuillez corriger les permissions refusées."
            desc_color = C_WARNING
        else:
            desc_text = "L'authentification biométrique requiert l'accès aux périphériques suivants."
            desc_color = C_TEXT
        
        tk.Label(body,
                 text=desc_text,
                 bg=C_BG, fg=desc_color, font=("Courier", 9),
                 wraplength=700, justify="left").pack(anchor="w", pady=(0, 16))

        # Container pour les deux permissions (caméra + microphone)
        perm_frame = tk.Frame(body, bg=C_BG)
        perm_frame.pack(fill="both", expand=True, pady=(0, 12))

        # Afficher TOUTES les deux permissions (de problems)
        for device_name, result in problems:
            # Couleur et icône selon l'état
            if result.granted:
                card_bg = C_SURFACE
                card_border = C_SUCCESS
                status_color = C_SUCCESS
                status_icon = "✓"
                status_text = "ACCORDÉE"
            elif result.state == PermissionState.DENIED:
                card_bg = C_PANEL
                card_border = C_ERROR
                status_color = C_ERROR
                status_icon = "✗"
                status_text = "REFUSÉE"
            elif result.state == PermissionState.NOT_DETERMINED:
                card_bg = C_PANEL
                card_border = C_WARNING
                status_color = C_WARNING
                status_icon = "?"
                status_text = "NON DÉTERMINÉE"
            else:
                card_bg = C_PANEL
                card_border = C_MUTED
                status_color = C_MUTED
                status_icon = "⊘"
                status_text = result.state.name if hasattr(result.state, "name") else "INCONNUE"

            card = tk.Frame(perm_frame, bg=card_bg,
                            highlightthickness=2, highlightbackground=card_border)
            card.pack(fill="x", pady=8)
            
            # En-tête avec statut
            title_bar = tk.Frame(card, bg=card_border, height=40)
            title_bar.pack(fill="x"); title_bar.pack_propagate(False)
            
            icon = "📷" if "Caméra" in device_name else "🎤"
            tk.Label(title_bar,
                     text=f"  {icon}  {device_name}  —  {status_icon} {status_text}",
                     bg=card_border, fg="white",
                     font=("Courier", 10, "bold")).pack(side="left", padx=10, fill="y")

            # Contenu
            content = tk.Frame(card, bg=card_bg)
            content.pack(fill="both", expand=True, padx=12, pady=10)

            # Message principal
            if result.message:
                tk.Label(content, text=f"  {result.message}",
                         bg=card_bg, fg=status_color,
                         font=("Courier", 9), anchor="w").pack(fill="x", pady=(0, 6))

            # Détails techniques
            if result.detail:
                tk.Label(content, text=f"  💡 {result.detail}",
                         bg=card_bg, fg=C_MUTED,
                         font=("Courier", 8), anchor="w").pack(fill="x", pady=(0, 6))

            # Étapes correctives (si permission refusée/non-déterminée)
            if not result.granted and result.fix_steps:
                sf = tk.Frame(content, bg=C_BG)
                sf.pack(fill="x", padx=(0, 0), pady=(6, 0))
                tk.Label(sf, text="📝  COMMENT CORRIGER :",
                         bg=C_BG, fg=C_ACCENT, font=("Courier", 8, "bold")
                         ).pack(fill="x", anchor="w", pady=(0, 4))
                for i, step in enumerate(result.fix_steps[:5]):
                    prefix = f"  {i+1}." if not step.startswith(" ") else "    "
                    tk.Label(sf, text=f"{prefix} {step.strip()}",
                             bg=C_BG, fg=C_MUTED,
                             font=("Courier", 8), anchor="w",
                             justify="left", wraplength=680).pack(fill="x", anchor="w", pady=2)

            # Bouton pour ouvrir paramètres (si actionable ET non accordée)
            if not result.granted and (getattr(result, "actionable", False) or getattr(result, "can_request", False)) and PERM_MGR_OK:
                dev_enum = DevicePermission.CAMERA if "Caméra" in device_name else DevicePermission.MICROPHONE
                btn_frame = tk.Frame(content, bg=card_bg)
                btn_frame.pack(fill="x", pady=(8, 0))
                tk.Button(btn_frame,
                          text=f"  🔧  Ouvrir Paramètres {os_lbl}  →",
                          bg=C_ACCENT2, fg="white",
                          font=("Courier", 9, "bold"),
                          bd=0, cursor="hand2", pady=6, padx=10,
                          activebackground=C_ACCENT,
                          command=lambda d=dev_enum: self._open_permission_settings(d, os_name)
                          ).pack(fill="x")

        # Boutons d'action en bas
        bf = tk.Frame(dlg, bg=C_BG)
        bf.pack(fill="x", padx=20, pady=(0,14))
        
        # Logique : si AU MOINS une permission accordée → bouton "Continuer"
        has_at_least_one = any(result.granted for _, result in problems)
        
        if has_at_least_one:
            # Bouton "Continuer" en vert (principal)
            tk.Button(bf, text="✓  CONTINUER L'AUTHENTIFICATION",
                      bg=C_SUCCESS, fg="white",
                      font=("Courier", 10, "bold"),
                      bd=0, cursor="hand2", pady=10, padx=10,
                      activebackground=C_SUCCESS,
                      command=dlg.destroy
                      ).pack(fill="x", pady=(0, 8))
        
        # Bouton "Revérifier" actif en permanence
        tk.Button(bf, text="🔄  REVÉRIFIER LES PERMISSIONS",
                  bg=C_ACCENT2, fg="white",
                  font=("Courier", 10, "bold"),
                  bd=0, cursor="hand2", pady=10, padx=10,
                  activebackground=C_ACCENT,
                  command=lambda: [dlg.destroy(),
                                   self.after(800, self._run_permissions_check_mandatory)]
                  ).pack(fill="x", pady=(0, 8))
        
        tk.Button(bf, text="❌  QUITTER L'APPLICATION",
                  bg=C_ERROR, fg="white",
                  font=("Courier", 10, "bold"), bd=0, cursor="hand2", pady=10, padx=10,
                  activebackground=C_ERROR,
                  command=self.destroy
                  ).pack(fill="x")

    def _open_permission_settings(self, device: DevicePermission, os_name: str):
        """Ouvre les paramètres de permission natifs de l'OS."""
        try:
            if os_name == "Windows":
                # Windows 10+ : Paramètres de Confidentialité (direct)
                import subprocess
                if device == DevicePermission.CAMERA:
                    subprocess.Popen(["explorer", "ms-settings:privacy-webcam"])
                    messagebox.showinfo(
                        "Paramètres ouverture",
                        "✓ Les Paramètres de Confidentialité Windows s'ouvrent.\n\n"
                        "📷 CAMÉRA :\n"
                        "Vérifiez que l'accès est ACTIVÉ pour les applications de bureau."
                    )
                else:
                    subprocess.Popen(["explorer", "ms-settings:privacy-microphone"])
                    messagebox.showinfo(
                        "Paramètres ouverture",
                        "✓ Les Paramètres de Confidentialité Windows s'ouvrent.\n\n"
                        "🎤 MICROPHONE :\n"
                        "Vérifiez que l'accès est ACTIVÉ pour les applications de bureau."
                    )
            elif os_name == "Darwin":
                # macOS : Préférences Système
                import subprocess
                pref_url = (
                    "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera"
                    if device == DevicePermission.CAMERA
                    else "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
                )
                subprocess.Popen(["open", pref_url])
                messagebox.showinfo(
                    "Paramètres ouverture",
                    "✓ Les Préférences Système macOS s'ouvrent.\n\n"
                    "Vérifiez que BioAccess Secure est coché dans la liste."
                )
            elif os_name == "Linux":
                # Linux : dépend du DE (GNOME, KDE, etc.)
                messagebox.showinfo(
                    "Configuration Linux",
                    "Sous Linux, configurez l'accès aux périphériques via :\n\n"
                    "📷 CAMÉRA : groupe 'video'\n"
                    "   sudo usermod -aG video $USER\n\n"
                    "🎤 MICROPHONE : groupe 'audio'\n"
                    "   sudo usermod -aG audio $USER\n\n"
                    "Puis relancez votre session."
                )
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir les paramètres : {e}\n\n"
                "Ouvrez manuellement :\n"
                "Windows : Paramètres → Confidentialité\n"
                "macOS : Préférences Système → Confidentialité\n"
                "Linux : Gestionnaire de groupes"
            )

    def _run_permissions_check(self):
        """Vérifie caméra + microphone selon l'OS, affiche un dialogue si problème."""
        if not PERM_MGR_OK:
            return
        def check():
            mgr        = PermissionManager()
            cam_result = mgr.check_and_request(DevicePermission.CAMERA)
            mic_result = mgr.check_and_request(DevicePermission.MICROPHONE)
            problems   = []
            if not cam_result.granted: problems.append(("Caméra", cam_result))
            if not mic_result.granted: problems.append(("Microphone", mic_result))
            if problems:
                self.after(0, lambda: self._show_permission_dialog(problems, mgr))
        threading.Thread(target=check, daemon=True).start()

    def _show_permission_dialog(self, problems: list, mgr):
        """Dialogue non bloquant avec étapes correctives et bouton paramètres OS."""
        os_name = platform.system()
        os_lbl  = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}.get(os_name, os_name)

        dlg = tk.Toplevel(self)
        dlg.title("Permissions biométriques manquantes")
        dlg.configure(bg=C_BG)
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        dlg.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        dlg.geometry(f"600x540+{(sw-600)//2}+{(sh-540)//2}")

        # En-tête
        hdr = tk.Frame(dlg, bg=C_WARNING, height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,
                 text=f"  ⚠  Permissions biométriques manquantes  —  {os_lbl}",
                 bg=C_WARNING, fg=C_BG,
                 font=("Courier", 11, "bold")).pack(side="left", padx=12, fill="y")

        body = tk.Frame(dlg, bg=C_BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(body,
                 text="Les permissions ci-dessous sont nécessaires pour l'authentification biométrique.\n"
                      "Sans elles, la caméra ou le microphone seront inaccessibles.",
                 bg=C_BG, fg=C_MUTED, font=("Courier", 8),
                 wraplength=560, justify="left").pack(anchor="w", pady=(0, 12))

        for device_name, result in problems:
            card = tk.Frame(body, bg=C_PANEL,
                            highlightthickness=1, highlightbackground=C_ERROR)
            card.pack(fill="x", pady=5)
            title_bar = tk.Frame(card, bg=C_ERROR, height=30)
            title_bar.pack(fill="x"); title_bar.pack_propagate(False)
            icon       = "CAMERA" if "Caméra" in device_name else "MICRO"
            state_name = result.state.name if hasattr(result.state, "name") else str(result.state)
            tk.Label(title_bar,
                     text=f"  [{icon}]  {device_name}  —  {state_name}",
                     bg=C_ERROR, fg="white",
                     font=("Courier", 9, "bold")).pack(side="left", padx=8, fill="y")
            tk.Label(card, text=f"  {result.message}",
                     bg=C_PANEL, fg=C_TEXT,
                     font=("Courier", 9), anchor="w").pack(fill="x", padx=10, pady=(6,2))
            if result.fix_steps:
                sf = tk.Frame(card, bg=C_SURFACE)
                sf.pack(fill="x", padx=10, pady=4)
                for i, step in enumerate(result.fix_steps[:5]):
                    prefix = "  " if step.startswith(" ") else f"  {i+1}."
                    tk.Label(sf, text=f"{prefix} {step.strip()}",
                             bg=C_SURFACE, fg=C_MUTED,
                             font=("Courier", 8), anchor="w",
                             justify="left").pack(fill="x")
            actionable = getattr(result, "actionable", False) or getattr(result, "can_request", False)
            if actionable and PERM_MGR_OK:
                dev_enum = (DevicePermission.CAMERA
                            if "Caméra" in device_name else DevicePermission.MICROPHONE)
                tk.Button(card,
                          text=f"  Ouvrir les paramètres {os_lbl}  →",
                          bg=C_ACCENT2, fg="white",
                          font=("Courier", 8, "bold"),
                          bd=0, cursor="hand2", pady=5,
                          activebackground=C_ACCENT,
                          command=lambda d=dev_enum: mgr.open_settings(d)
                          ).pack(fill="x", padx=10, pady=(4,8))

        bf = tk.Frame(dlg, bg=C_BG)
        bf.pack(fill="x", padx=20, pady=(0,14))
        tk.Button(bf, text="↻  Revérifier",
                  bg=C_PANEL, fg=C_TEXT,
                  font=("Courier", 9, "bold"),
                  bd=0, cursor="hand2", pady=8,
                  activebackground=C_BORDER,
                  command=lambda: [dlg.destroy(),
                                   self.after(300, self._run_permissions_check)]
                  ).pack(side="left", fill="x", expand=True, padx=(0,6))
        tk.Button(bf, text="Continuer quand même",
                  bg=C_SURFACE, fg=C_MUTED,
                  font=("Courier", 9), bd=0, cursor="hand2", pady=8,
                  activebackground=C_BORDER,
                  command=dlg.destroy
                  ).pack(side="left", fill="x", expand=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SURVEILLANCE ADMIN (polling API toutes les 5 s)
    # ══════════════════════════════════════════════════════════════════════════
    def _check_admin_access(self, uid: str) -> Tuple[bool, str]:
        if not REQUESTS_OK:
            return True, "Mode local (requests non disponible)"
        try:
            headers = {}
            if Config.API_TOKEN:
                headers["Authorization"] = f"Bearer {Config.API_TOKEN}"
            r = requests.get(
                f"{Config.API_BASE_URL}/api/v1/alerts/access/check/{uid}",
                headers=headers, timeout=3)
            if r.status_code == 200:
                d = r.json()
                return d.get("allow_access", True), d.get("reason", "")
            elif r.status_code == 404:
                return True, "Non géré par l'administration"
            return False, f"Erreur API ({r.status_code})"
        except requests.exceptions.ConnectionError:
            return True, "Backend hors ligne — vérification locale"
        except Exception as e:
            return True, str(e)

    def _poll_admin(self):
        if self._auth_done and not self._locked and self._authenticated_uid:
            def check():
                allowed, reason = self._check_admin_access(self._authenticated_uid)
                if not allowed:
                    def revoke():
                        self._auth_done = self._admin_granted = False
                        self._locked    = True
                        self._apply_lock()
                        self.lock_uid_var.set("")
                        self.lock_uid_status.config(text="")
                        self.lock_admin_msg.config(
                            text=f"⚠ Accès révoqué : {reason}", fg=C_LOCK)
                        self.show_screen("lock")
                        self.status_var.set("Accès révoqué — poste re-verrouillé")
                    self.after(0, revoke)
            threading.Thread(target=check, daemon=True).start()
        self.after(5000, self._poll_admin)

    # ══════════════════════════════════════════════════════════════════════════
    # CONSTRUCTION UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Barre de titre
        tb = tk.Frame(self, bg=C_SURFACE, height=50)
        tb.pack(fill="x", side="top"); tb.pack_propagate(False)
        tk.Label(tb, text="⬡", bg=C_SURFACE, fg=C_ACCENT,
                 font=("Courier",18,"bold")).pack(side="left", padx=14, pady=8)
        tk.Label(tb, text="BioAccess Secure", bg=C_SURFACE, fg=C_TEXT,
                 font=("Courier",14,"bold")).pack(side="left", pady=8)
        tk.Label(tb, text=f"CLIENT DESKTOP v{Config.VERSION}",
                 bg=C_SURFACE, fg=C_MUTED,
                 font=("Courier",9)).pack(side="left", padx=16)

        # Barre de statut
        self.status_var = tk.StringVar(value="Prêt")
        sb = tk.Frame(self, bg=C_SURFACE, height=28)
        sb.pack(fill="x", side="bottom"); sb.pack_propagate(False)
        tk.Label(sb, textvariable=self.status_var,
                 bg=C_SURFACE, fg=C_MUTED, font=("Courier",8),
                 anchor="w").pack(side="left", padx=12, fill="y")
        self.lock_indicator = tk.Label(sb, text="🔓 OUVERT",
                                        bg=C_SURFACE, fg=C_SUCCESS,
                                        font=("Courier",8,"bold"))
        self.lock_indicator.pack(side="right", padx=12)

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill="x")

        self.main = tk.Frame(self, bg=C_BG)
        self.main.pack(fill="both", expand=True)

        self._build_lock_screen()
        self._build_blocked_screen()
        self._build_auth_screen()
        self._build_register_screen()
        self._build_home_screen()
        self._build_success_screen()

    # ══════════════════════════════════════════════════════════════════════════
    # ÉCRAN 1 — SAISIE USER_ID (fenêtre normale)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_lock_screen(self):
        f = tk.Frame(self.main, bg=C_BG)
        self._screens["lock"] = f

        self.lock_canvas = AnimatedCanvas(f, mode="lock")
        self.lock_canvas.pack(fill="both", expand=True)

        panel = tk.Frame(f, bg=C_PANEL,
                         highlightthickness=2, highlightbackground=C_LOCK)
        panel.place(relx=0.5, rely=0.73, anchor="center", width=460)

        tk.Label(panel,
                 text="⚠  POSTE SÉCURISÉ — IDENTIFICATION REQUISE",
                 bg=C_PANEL, fg=C_LOCK,
                 font=("Courier",10,"bold")).pack(pady=(18,4), padx=20)
        tk.Label(panel,
                 text="Saisissez votre User_ID pour demander l'accès.\n"
                      "Votre administrateur doit autoriser la connexion.",
                 bg=C_PANEL, fg=C_MUTED,
                 font=("Courier",8), wraplength=420,
                 justify="center").pack(pady=(0,12), padx=20)

        self.lock_uid_var = tk.StringVar()
        self.lock_uid_entry = tk.Entry(
            panel, textvariable=self.lock_uid_var,
            bg=C_SURFACE, fg=C_ACCENT,
            font=("Courier",15,"bold"),
            insertbackground=C_ACCENT,
            highlightthickness=2,
            highlightcolor=C_ACCENT,
            highlightbackground=C_LOCK,
            bd=0, justify="center")
        self.lock_uid_entry.pack(fill="x", padx=24, ipady=11)
        self.lock_uid_entry.bind("<Return>", lambda e: self._on_lock_submit())
        self.lock_uid_entry.focus_set()

        self.lock_uid_status = tk.Label(panel, text="",
                                         bg=C_PANEL, fg=C_MUTED,
                                         font=("Courier",8))
        self.lock_uid_status.pack(pady=(4,0))
        self.lock_uid_var.trace_add("write", self._on_lock_uid_change)

        self.lock_submit_btn = tk.Button(
            panel, text="  VALIDER MON USER_ID  →",
            bg=C_LOCK, fg="white",
            font=("Courier",11,"bold"),
            bd=0, cursor="hand2",
            activebackground="#b91c1c",
            pady=11, command=self._on_lock_submit)
        self.lock_submit_btn.pack(fill="x", padx=24, pady=(14,0))

        self.lock_admin_msg = tk.Label(panel, text="",
                                        bg=C_PANEL, fg=C_WARNING,
                                        font=("Courier",8),
                                        wraplength=420, justify="center")
        self.lock_admin_msg.pack(pady=(6,14), padx=20)

    def _on_lock_uid_change(self, *_):
        uid = self.lock_uid_var.get().strip()
        if not uid:
            self.lock_uid_status.config(text="", fg=C_MUTED)
        elif uid in load_users():
            self.lock_uid_status.config(
                text=f"✓  User_ID «{uid}» reconnu localement", fg=C_SUCCESS)
        else:
            self.lock_uid_status.config(
                text="✗  User_ID inconnu — enregistrez-vous d'abord", fg=C_ERROR)

    def _on_lock_submit(self):
        uid = self.lock_uid_var.get().strip()
        if not uid:
            self.lock_admin_msg.config(text="⚠ Entrez votre User_ID.", fg=C_WARNING)
            return
        if uid not in load_users():
            self.lock_admin_msg.config(
                text="✗ User_ID inconnu. Contactez votre administrateur.",
                fg=C_ERROR)
            return

        # ── VÉRIFICATION PERMISSIONS BIOMÉTRIQUES AVANT D'AUTORISER L'ACCÈS ──
        if PERM_MGR_OK and not self._permissions_ok:
            self.lock_admin_msg.config(
                text="✗ Permissions biométriques manquantes — impossible de continuer.",
                fg=C_ERROR)
            self.after(1500, lambda: messagebox.showerror(
                "Authentification impossible",
                "Les permissions d'accès aux périphériques biométriques (caméra/microphone)"
                " sont obligatoires.\n\n"
                "Configurez-les dans les paramètres du système et réessayez."
            ))
            return

        # ── ACTIVATION DU VERROU au 1er User_ID soumis ──────────────────────
        if not self._uid_submitted:
            self._uid_submitted = True
            self._apply_lock()

        self.lock_admin_msg.config(
            text="⏳ Vérification auprès de l'administrateur...", fg=C_WARNING)
        self.lock_submit_btn.config(state="disabled")
        self.status_var.set(f"Vérification accès pour {uid}...")

        def check():
            allowed, reason = self._check_admin_access(uid)
            def update():
                self.lock_submit_btn.config(state="normal")
                if allowed:
                    self._admin_granted = True
                    self.lock_admin_msg.config(
                        text="✓ Accès autorisé — authentification biométrique requise",
                        fg=C_SUCCESS)
                    self.after(800, lambda: self._go_to_auth(uid))
                else:
                    self.show_screen("blocked")
                    self.blocked_uid_label.config(text=f"User_ID : {uid}")
                    self.blocked_reason_label.config(
                        text=f"Raison : {reason or 'Accès bloqué par l\'administrateur'}")
                    self.status_var.set(f"Accès refusé pour {uid}")
            self.after(0, update)
        threading.Thread(target=check, daemon=True).start()

    def _go_to_auth(self, uid: str):
        self.auth_userid_var.set(uid)
        self._new_phrase()
        self.show_screen("auth")
        self.auth_canvas.start()
        self.status_var.set(f"Authentification biométrique requise — {uid}")

    # ══════════════════════════════════════════════════════════════════════════
    # ÉCRAN 2 — ACCÈS BLOQUÉ PAR L'ADMIN
    # ══════════════════════════════════════════════════════════════════════════
    def _build_blocked_screen(self):
        f = tk.Frame(self.main, bg=C_BG)
        self._screens["blocked"] = f
        center = tk.Frame(f, bg=C_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")

        ic = tk.Canvas(center, width=160, height=160,
                       bg=C_BG, highlightthickness=0)
        ic.pack(pady=(0,20))
        ic.create_oval(10,10,150,150, outline=C_LOCK, width=5,
                       fill=_mix(C_LOCK, 0.1))
        ic.create_line(38,38,122,122, fill=C_LOCK, width=6)
        ic.create_line(122,38,38,122, fill=C_LOCK, width=6)

        tk.Label(center, text="ACCÈS REFUSÉ", bg=C_BG, fg=C_LOCK,
                 font=("Courier",22,"bold")).pack(pady=4)
        tk.Label(center,
                 text="L'administrateur a bloqué l'accès à ce poste",
                 bg=C_BG, fg=C_TEXT, font=("Courier",10)).pack(pady=2)
        self.blocked_uid_label = tk.Label(center, text="",
                                           bg=C_BG, fg=C_ACCENT,
                                           font=("Courier",12,"bold"))
        self.blocked_uid_label.pack(pady=8)
        self.blocked_reason_label = tk.Label(center, text="",
                                              bg=C_BG, fg=C_WARNING,
                                              font=("Courier",10), wraplength=520)
        self.blocked_reason_label.pack(pady=4)
        tk.Label(center,
                 text="Contactez votre administrateur (interface alerts.html)\n"
                      "pour demander l'autorisation d'accès.",
                 bg=C_BG, fg=C_MUTED, font=("Courier",9),
                 wraplength=500, justify="center").pack(pady=16)
        tk.Button(center,
                  text="← Réessayer avec un autre User_ID",
                  bg=C_PANEL, fg=C_TEXT, font=("Courier",10),
                  bd=0, cursor="hand2", activebackground=C_BORDER,
                  pady=10, padx=20,
                  command=lambda: self.show_screen("lock")).pack(pady=4)

    # ══════════════════════════════════════════════════════════════════════════
    # ÉCRAN 3 — AUTHENTIFICATION BIOMÉTRIQUE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_auth_screen(self):
        f = tk.Frame(self.main, bg=C_BG)
        self._screens["auth"] = f

        header = tk.Frame(f, bg=C_SURFACE, height=56)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Frame(header, bg=C_BORDER, height=1).pack(side="bottom", fill="x")
        tk.Button(header, text="← User_ID",
                  bg=C_SURFACE, fg=C_MUTED,
                  font=("Courier",9), bd=0, cursor="hand2",
                  activebackground=C_SURFACE, activeforeground=C_ACCENT,
                  command=lambda: self.show_screen("lock")).pack(side="left", padx=16)
        tk.Label(header, text="AUTHENTIFICATION BIOMÉTRIQUE",
                 bg=C_SURFACE, fg=C_TEXT,
                 font=("Courier",13,"bold")).pack(side="left", padx=12)
        tk.Label(header, text="✓ Admin autorisé",
                 bg=C_SURFACE, fg=C_SUCCESS,
                 font=("Courier",9,"bold")).pack(side="right", padx=20)

        body = tk.Frame(f, bg=C_BG)
        body.pack(fill="both", expand=True)

        # ── Gauche ──────────────────────────────────────────────────────────
        left = tk.Frame(body, bg=C_PANEL, width=300)
        left.pack(side="left", fill="y", padx=1); left.pack_propagate(False)

        tk.Label(left, text="USER_ID", bg=C_PANEL, fg=C_MUTED,
                 font=("Courier",9,"bold")).pack(pady=(24,4), padx=20, anchor="w")
        self.auth_userid_var = tk.StringVar()
        tk.Entry(left, textvariable=self.auth_userid_var,
                 bg=C_SURFACE, fg=C_ACCENT,
                 font=("Courier",12,"bold"),
                 highlightthickness=1,
                 highlightcolor=C_SUCCESS,
                 highlightbackground=C_SUCCESS,
                 bd=0, state="readonly",
                 readonlybackground=C_SURFACE).pack(padx=16, fill="x", ipady=7)

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=16, pady=16)
        self.auth_method = tk.StringVar(value="face")
        tk.Label(left, text="MÉTHODE", bg=C_PANEL, fg=C_MUTED,
                 font=("Courier",9,"bold")).pack(pady=(0,8), padx=20, anchor="w")
        for val,label,icon in [("face","Reconnaissance faciale","👁"),
                                ("voice","Reconnaissance vocale","🎙")]:
            rf = tk.Frame(left, bg=C_PANEL); rf.pack(fill="x", padx=16, pady=3)
            tk.Radiobutton(rf, text=f"{icon}  {label}",
                           variable=self.auth_method, value=val,
                           bg=C_PANEL, fg=C_TEXT, selectcolor=C_SURFACE,
                           activebackground=C_PANEL, font=("Courier",10),
                           command=self._update_auth_view).pack(anchor="w")

        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=16, pady=16)
        self.phrase_frame = tk.Frame(left, bg=C_PANEL)
        tk.Label(self.phrase_frame, text="PHRASE À LIRE",
                 bg=C_PANEL, fg=C_MUTED,
                 font=("Courier",9,"bold")).pack(anchor="w", pady=(0,6))
        self.phrase_label = tk.Label(self.phrase_frame, text="",
                                     bg=C_SURFACE, fg=C_ACCENT,
                                     font=("Courier",9), wraplength=240,
                                     justify="center", padx=10, pady=10)
        self.phrase_label.pack(fill="x")
        self._btn(self.phrase_frame, "↻ Nouvelle phrase",
                  self._new_phrase, False, 200, small=True).pack(pady=6)

        tk.Frame(left, bg=C_SURFACE).pack(fill="both", expand=True)
        self.auth_btn = self._btn(left, "⚡  LANCER L'AUTH",
                                  self._start_auth, True, 240)
        self.auth_btn.pack(pady=16)
        self.stop_auth_btn = self._btn(left, "■  ARRÊTER",
                                       self._stop_auth, False, 240)
        self.stop_auth_btn.pack(pady=4); self.stop_auth_btn.config(state="disabled")

        # ── Droite ──────────────────────────────────────────────────────────
        right = tk.Frame(body, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)
        self.auth_canvas = AnimatedCanvas(right, mode="face")
        self.auth_canvas.pack(fill="both", expand=True, padx=20, pady=20)
        self.auth_result_var = tk.StringVar(value="")
        self.auth_result_label = tk.Label(right,
                                          textvariable=self.auth_result_var,
                                          bg=C_BG, fg=C_TEXT,
                                          font=("Courier",11,"bold"))
        self.auth_result_label.pack(pady=4)
        self.audio_phrase_label = tk.Label(right, text="",
                                           bg=C_BG, fg=C_ACCENT,
                                           font=("Courier",13,"bold"),
                                           wraplength=500, justify="center")
        self.audio_phrase_label.pack(pady=4)
        self.transcript_var = tk.StringVar(value="")
        tk.Label(right, textvariable=self.transcript_var,
                 bg=C_BG, fg=C_MUTED, font=("Courier",9),
                 wraplength=500).pack(pady=2)

    # ══════════════════════════════════════════════════════════════════════════
    # ÉCRAN 4 — ACCUEIL (poste déverrouillé)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_home_screen(self):
        f = tk.Frame(self.main, bg=C_BG)
        self._screens["home"] = f

        left = tk.Frame(f, bg=C_SURFACE, width=340)
        left.pack(side="left", fill="y"); left.pack_propagate(False)
        tk.Frame(left, bg=C_BORDER, width=1).pack(side="right", fill="y")

        logo_c = tk.Canvas(left, width=120, height=120,
                           bg=C_SURFACE, highlightthickness=0)
        logo_c.pack(pady=(40,16), padx=30)
        self._draw_logo(logo_c)
        tk.Label(left, text="BIOACCESS\nSECURE",
                 bg=C_SURFACE, fg=C_ACCENT,
                 font=("Courier",20,"bold"), justify="center").pack(pady=8)
        tk.Label(left, text="✓ Poste déverrouillé",
                 bg=C_SURFACE, fg=C_SUCCESS,
                 font=("Courier",10,"bold")).pack(pady=4)
        tk.Frame(left, bg=C_BORDER, height=1).pack(fill="x", padx=20, pady=16)
        self.home_user_info = tk.Label(left, text="",
                                        bg=C_SURFACE, fg=C_TEXT,
                                        font=("Courier",10))
        self.home_user_info.pack(pady=4)
        for cap, flag in [("Reconnaissance faciale", OPENCV_OK),
                           ("Reconnaissance vocale",  VOSK_OK)]:
            tk.Label(left,
                     text=("✓ " if flag else "✗ ") + cap,
                     bg=C_SURFACE,
                     fg=C_SUCCESS if flag else C_ERROR,
                     font=("Courier",9)).pack(pady=2)
        tk.Frame(left, bg=C_SURFACE).pack(fill="both", expand=True)
        self._btn(left, "👤  Gérer l'enregistrement",
                  lambda: self.show_screen("register"),
                  False, 240, small=True).pack(pady=8)
        tk.Button(left, text="🔒  Verrouiller le poste",
                  bg=C_LOCK, fg="white",
                  font=("Courier",10,"bold"),
                  bd=0, cursor="hand2", pady=10,
                  activebackground="#b91c1c",
                  command=self._manual_lock).pack(fill="x", padx=16, pady=12)

        right = tk.Frame(f, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)
        center = tk.Frame(right, bg=C_BG)
        center.place(relx=0.5, rely=0.45, anchor="center")
        self.home_welcome = tk.Label(center, text="BIENVENUE",
                                      bg=C_BG, fg=C_ACCENT,
                                      font=("Courier",28,"bold"))
        self.home_welcome.pack(pady=(0,8))
        tk.Label(center, text="Poste déverrouillé avec succès",
                 bg=C_BG, fg=C_SUCCESS, font=("Courier",11)).pack(pady=(0,30))
        tk.Label(center,
                 text="Vous pouvez maintenant réduire ou fermer cette fenêtre.",
                 bg=C_BG, fg=C_MUTED, font=("Courier",10),
                 justify="center").pack(pady=8)
        tk.Frame(center, bg=C_BORDER, height=1, width=320).pack(pady=20)
        tk.Label(center, text="Utilisateurs enregistrés :",
                 bg=C_BG, fg=C_MUTED, font=("Courier",9)).pack()
        lbf = tk.Frame(center, bg=C_PANEL,
                       highlightthickness=1, highlightbackground=C_BORDER)
        lbf.pack(pady=8, fill="x")
        self.home_users_lb = tk.Listbox(
            lbf, bg=C_PANEL, fg=C_TEXT, font=("Courier",10),
            selectbackground=C_BORDER, highlightthickness=0, bd=0, height=4)
        self.home_users_lb.pack(fill="both", padx=4, pady=4)
        self._btn(center, "🗑  Supprimer utilisateur",
                  self._delete_user, False, 220, small=True).pack(pady=4)

    def _manual_lock(self):
        self._auth_done = self._admin_granted = False
        self._uid_submitted = False
        self._locked = True
        self.lock_uid_var.set("")
        self.lock_uid_status.config(text="")
        self.lock_admin_msg.config(text="")
        self._apply_lock()
        self.show_screen("lock")
        self.status_var.set("Poste verrouillé manuellement")

    # ══════════════════════════════════════════════════════════════════════════
    # ÉCRAN 5 — ENREGISTREMENT
    # ══════════════════════════════════════════════════════════════════════════
    def _build_register_screen(self):
        f = tk.Frame(self.main, bg=C_BG)
        self._screens["register"] = f
        header = tk.Frame(f, bg=C_SURFACE, height=56)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Frame(header, bg=C_BORDER, height=1).pack(side="bottom", fill="x")
        tk.Button(header, text="← Retour",
                  bg=C_SURFACE, fg=C_ACCENT,
                  font=("Courier",10), bd=0, cursor="hand2",
                  activebackground=C_SURFACE, activeforeground=C_ACCENT,
                  command=lambda: self.show_screen("home")).pack(side="left", padx=16)
        tk.Label(header, text="ENREGISTREMENT BIOMÉTRIQUE",
                 bg=C_SURFACE, fg=C_TEXT,
                 font=("Courier",13,"bold")).pack(side="left", padx=20)

        body = tk.Frame(f, bg=C_BG); body.pack(fill="both", expand=True)
        center = tk.Frame(body, bg=C_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(center, text="NOUVEL UTILISATEUR",
                 bg=C_BG, fg=C_ACCENT,
                 font=("Courier",18,"bold")).pack(pady=(0,24))
        tk.Label(center, text="Votre User_ID :",
                 bg=C_BG, fg=C_TEXT, font=("Courier",11)).pack(anchor="w")
        self.reg_uid_var = tk.StringVar()
        tk.Entry(center, textvariable=self.reg_uid_var,
                 bg=C_PANEL, fg=C_ACCENT,
                 font=("Courier",13,"bold"),
                 insertbackground=C_ACCENT,
                 highlightthickness=1,
                 highlightcolor=C_ACCENT, highlightbackground=C_BORDER,
                 bd=0, width=30).pack(pady=6, ipady=9, padx=2)
        tk.Label(center, text="Lettres, chiffres, - _ autorisés",
                 bg=C_BG, fg=C_MUTED, font=("Courier",8)).pack()
        tk.Frame(center, bg=C_BORDER, height=1, width=360).pack(pady=16)
        tk.Label(center, text="Méthode :",
                 bg=C_BG, fg=C_TEXT, font=("Courier",11)).pack(anchor="w")
        self.reg_method = tk.StringVar(value="face")
        mf = tk.Frame(center, bg=C_BG); mf.pack(pady=8, anchor="w")
        for val,label,icon in [("face","Visage","👁"),
                                ("voice","Voix","🎙"),
                                ("both","Les deux","🔐")]:
            tk.Radiobutton(mf, text=f"{icon}  {label}",
                           variable=self.reg_method, value=val,
                           bg=C_BG, fg=C_TEXT, selectcolor=C_PANEL,
                           activebackground=C_BG,
                           font=("Courier",10)).pack(side="left", padx=12)
        tk.Frame(center, bg=C_BORDER, height=1, width=360).pack(pady=16)
        self.reg_status_var = tk.StringVar(value="")
        tk.Label(center, textvariable=self.reg_status_var,
                 bg=C_BG, fg=C_WARNING, font=("Courier",10),
                 wraplength=360).pack(pady=8)
        self.reg_btn = self._btn(center, "⚡  LANCER L'ENREGISTREMENT",
                                 self._start_register, True, 300)
        self.reg_btn.pack(pady=8)

    # ══════════════════════════════════════════════════════════════════════════
    # ÉCRAN 6 — SUCCÈS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_success_screen(self):
        f = tk.Frame(self.main, bg=C_BG)
        self._screens["success"] = f
        center = tk.Frame(f, bg=C_BG)
        center.place(relx=0.5, rely=0.5, anchor="center")
        cc = tk.Canvas(center, width=200, height=200,
                       bg=C_BG, highlightthickness=0)
        cc.pack()
        self._draw_success_check(cc)
        self.success_name = tk.Label(center, text="",
                                      bg=C_BG, fg=C_TEXT,
                                      font=("Courier",22,"bold"))
        self.success_name.pack(pady=8)
        tk.Label(center,
                 text="AUTHENTIFICATION RÉUSSIE — POSTE DÉVERROUILLÉ",
                 bg=C_BG, fg=C_SUCCESS,
                 font=("Courier",13,"bold")).pack(pady=4)
        self.success_method = tk.Label(center, text="",
                                        bg=C_BG, fg=C_MUTED,
                                        font=("Courier",10))
        self.success_method.pack(pady=4)
        self.success_time = tk.Label(center, text="",
                                      bg=C_BG, fg=C_MUTED,
                                      font=("Courier",9))
        self.success_time.pack(pady=4)
        self._btn(center, "→ Accéder à l'accueil",
                  lambda: self.show_screen("home"), True, 260).pack(pady=20)

    # ══════════════════════════════════════════════════════════════════════════
    # NAVIGATION
    # ══════════════════════════════════════════════════════════════════════════
    def show_screen(self, name: str):
        if name not in ("lock", "blocked"):
            self._stop_auth()
        for s in self._screens.values():
            s.pack_forget()
        self._screens[name].pack(fill="both", expand=True)

        if name == "lock":
            self.lock_canvas.start()
            self.lock_indicator.config(text="🔒 VERROUILLÉ" if self._uid_submitted else "🔓 OUVERT",
                                        fg=C_LOCK if self._uid_submitted else C_SUCCESS)
            self.status_var.set("Saisissez votre User_ID")
            self.lock_uid_entry.focus_set()
        else:
            self.lock_canvas.stop()

        if name == "home":
            self.lock_indicator.config(text="🔓 DÉVERROUILLÉ", fg=C_SUCCESS)
            self._refresh_home()
        elif name == "auth":
            self._update_auth_view()
            self.auth_canvas.start()
        elif name == "register":
            self.reg_status_var.set("")

    def _refresh_home(self):
        users = load_users()
        self.home_users_lb.delete(0, "end")
        for u in users:
            m = ("👁" if users[u].get("face") else "") + \
                (" 🎙" if users[u].get("voice") else "")
            self.home_users_lb.insert("end", f"  {m.strip()}  {u}")
        uid = self._authenticated_uid
        self.home_user_info.config(text=f"Connecté : {uid}")
        self.home_welcome.config(text=f"BIENVENUE, {uid.upper()}")

    # ══════════════════════════════════════════════════════════════════════════
    # LOGIQUE AUTH
    # ══════════════════════════════════════════════════════════════════════════
    def _update_auth_view(self):
        mode = self.auth_method.get()
        self.auth_canvas.mode = mode
        if mode == "voice": self.phrase_frame.pack(fill="x", padx=16)
        else:               self.phrase_frame.pack_forget()

    def _new_phrase(self):
        phrase = random.choice(PHRASES)
        self.phrase_label.config(text=f'« {phrase} »')
        self._current_phrase = phrase

    def _start_auth(self):
        uid = self.auth_userid_var.get().strip()
        if not uid or uid not in load_users():
            self._auth_fail("User_ID introuvable"); return
        self._stop_event.clear()
        self.auth_btn.config(state="disabled")
        self.stop_auth_btn.config(state="normal")
        self.auth_result_var.set(""); self.transcript_var.set("")
        self.audio_phrase_label.config(text="")
        self.auth_canvas._success = self.auth_canvas._fail = False
        method = self.auth_method.get()
        self.status_var.set(f"Auth [{method}] — {uid}")
        if method == "face":
            threading.Thread(target=self._face_thread,
                             args=(uid,), daemon=True).start()
        else:
            phrase = self._current_phrase
            self.audio_phrase_label.config(
                text=f'Lisez à voix haute :\n« {phrase} »')
            threading.Thread(target=self._voice_thread,
                             args=(uid, phrase), daemon=True).start()

    def _stop_auth(self):
        self._stop_event.set()
        if hasattr(self, "auth_btn"):      self.auth_btn.config(state="normal")
        if hasattr(self, "stop_auth_btn"): self.stop_auth_btn.config(state="disabled")
        if hasattr(self, "auth_canvas"):
            self.auth_canvas._success = self.auth_canvas._fail = False
        self.status_var.set("Prêt")

    def _auth_success(self, uid: str, method: str):
        self.auth_canvas.show_success()
        self.auth_result_var.set(f"✓ Bienvenue, {uid} !")
        self.auth_result_label.config(fg=C_SUCCESS)
        self.auth_btn.config(state="normal")
        self.stop_auth_btn.config(state="disabled")
        self._auth_done         = True
        self._authenticated_uid = uid
        self._unlock_window()
        def go():
            self.success_name.config(text=uid)
            self.success_method.config(
                text=f"Méthode : {'Faciale' if method=='face' else 'Vocale'}")
            self.success_time.config(
                text=datetime.now().strftime("Connecté le %d/%m/%Y à %H:%M:%S"))
            self.show_screen("success")
            self.status_var.set(f"🔓 Poste déverrouillé — {uid}")
            self.lock_indicator.config(text="🔓 DÉVERROUILLÉ", fg=C_SUCCESS)
        self.after(1200, go)

    def _auth_fail(self, reason: str = "Authentification échouée"):
        self.auth_canvas.show_fail()
        self.auth_result_var.set(f"✗ {reason}")
        self.auth_result_label.config(fg=C_ERROR)
        self.status_var.set(f"Échec : {reason}")
        self.auth_btn.config(state="normal")
        self.stop_auth_btn.config(state="disabled")

    # ── Thread faciale ─────────────────────────────────────────────────────────
    def _face_thread(self, uid: str):
        if not OPENCV_OK:
            self.after(0, lambda: self._auth_fail("OpenCV non installé")); return
        face_file = FACES_DIR / f"{uid}.yml"
        if not face_file.exists() or not load_users().get(uid, {}).get("face"):
            self.after(0, lambda: self._auth_fail("Aucun profil facial")); return
        # ── Vérification permission caméra selon l'OS ────────────────────────
        if PERM_MGR_OK:
            mgr    = PermissionManager()
            result = mgr.check_and_request(DevicePermission.CAMERA)
            if not result.granted:
                msg = f"Permission caméra refusée ({platform.system()})\n{result.message}"
                if result.fix_steps:
                    msg += "\n" + "\n".join(result.fix_steps[:2])
                self.after(0, lambda m=msg: self._auth_fail(m))
                # Afficher aussi le dialogue complet
                self.after(0, lambda: self._show_permission_dialog(
                    [("Caméra", result)], mgr))
                return
        try:
            rec = cv2.face.LBPHFaceRecognizer_create()
            rec.read(str(face_file))
        except Exception as e:
            self.after(0, lambda: self._auth_fail(f"Erreur modèle : {e}")); return
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.after(0, lambda: self._auth_fail("Caméra inaccessible")); return
        att = 0
        while not self._stop_event.is_set() and att < 60:
            ret, frame = cap.read()
            if not ret: break
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(100,100))
            for (x,y,w,h) in faces:
                roi = cv2.resize(gray[y:y+h, x:x+w], (200,200))
                _, conf = rec.predict(roi)
                if conf < 80:
                    cap.release()
                    self.after(0, lambda: self._auth_success(uid, "face")); return
            att += 1; time.sleep(0.1)
        cap.release()
        if not self._stop_event.is_set():
            self.after(0, lambda: self._auth_fail("Visage non reconnu"))

    # ── Thread vocal ───────────────────────────────────────────────────────────
    def _voice_thread(self, uid: str, phrase: str):
        if not VOSK_OK:
            self.after(0, lambda: self._auth_fail("Vosk non installé")); return
        mp = resource_path("vosk-model")
        if not os.path.exists(mp):
            self.after(0, lambda: self._auth_fail("Modèle Vosk introuvable")); return
        # ── Vérification permission microphone selon l'OS ────────────────────
        if PERM_MGR_OK:
            mgr    = PermissionManager()
            result = mgr.check_and_request(DevicePermission.MICROPHONE)
            if not result.granted:
                msg = f"Permission microphone refusée ({platform.system()})\n{result.message}"
                if result.fix_steps:
                    msg += "\n" + "\n".join(result.fix_steps[:2])
                self.after(0, lambda m=msg: self._auth_fail(m))
                self.after(0, lambda: self._show_permission_dialog(
                    [("Microphone", result)], mgr))
                return
        try:
            import sounddevice as sd
            import queue as queue_module
            
            model  = vosk.Model(mp)
            rec    = vosk.KaldiRecognizer(model, 16000)
            
            # File d'attente pour l'audio avec sounddevice
            audio_queue = queue_module.Queue()
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(status, file=sys.stderr)
                audio_queue.put(bytes(indata))
            
            stream = sd.RawInputStream(samplerate=16000, blocksize=8192, dtype='int16',
                                      channels=1, callback=audio_callback)
            stream.start()
        except Exception as e:
            self.after(0, lambda: self._auth_fail(f"Erreur audio : {e}")); return
        transcript = ""; deadline = time.time() + 10
        while not self._stop_event.is_set() and time.time() < deadline:
            try:
                data = audio_queue.get(timeout=0.1)
                if rec.AcceptWaveform(data):
                    transcript = json.loads(rec.Result()).get("text","").lower().strip()
                    self.after(0, lambda t=transcript:
                               self.transcript_var.set(f'Reconnu : « {t} »'))
                    break
            except queue_module.Empty:
                continue
        stream.stop(); stream.close()
        if self._stop_event.is_set(): return
        sim = self._sim(transcript, phrase.lower().strip())
        self.after(0, lambda t=transcript:
                   self.transcript_var.set(f'Reconnu : « {t} »'))
        if sim >= 0.6: self.after(0, lambda: self._auth_success(uid, "voice"))
        else:          self.after(0, lambda: self._auth_fail(
                                  f"Phrase incorrecte ({int(sim*100)}% de similarité)"))

    @staticmethod
    def _sim(a: str, b: str) -> float:
        if not a or not b: return 0.0
        wa, wb = set(a.split()), set(b.split())
        return len(wa & wb) / len(wb) if wb else 0.0

    # ── Enregistrement ─────────────────────────────────────────────────────────
    def _start_register(self):
        name = self.reg_uid_var.get().strip()
        if not name:
            self.reg_status_var.set("⚠ Entrez un User_ID."); return
        if not name.replace("_","").replace("-","").isalnum():
            self.reg_status_var.set("⚠ Caractères invalides"); return
        self.reg_btn.config(state="disabled")
        self.reg_status_var.set("Enregistrement en cours...")
        threading.Thread(target=self._reg_thread,
                         args=(name, self.reg_method.get()), daemon=True).start()

    def _reg_thread(self, name: str, method: str):
        users = load_users()
        if name not in users: users[name] = {}
        ok_f = ok_v = False
        if method in ("face","both"):
            ok, msg = self._reg_face(name)
            self.after(0, lambda m=msg: self.reg_status_var.set(m))
            if ok: users[name]["face"] = True; ok_f = True
        if method in ("voice","both") and (method=="voice" or ok_f):
            ok, msg = self._reg_voice(name)
            self.after(0, lambda m=msg: self.reg_status_var.set(m))
            if ok: users[name]["voice"] = True; ok_v = True
        save_users(users)
        def fin():
            self.reg_btn.config(state="normal")
            success = ((method=="face" and ok_f) or
                       (method=="voice" and ok_v) or
                       (method=="both" and (ok_f or ok_v)))
            if success:
                self.reg_status_var.set(f"✓ User_ID «{name}» enregistré !")
                self.after(1500, lambda: self.show_screen("home"))
            else:
                self.reg_status_var.set("✗ Enregistrement échoué. Réessayez.")
        self.after(0, fin)

    def _reg_face(self, name: str) -> Tuple[bool, str]:
        if not OPENCV_OK: return False, "✗ OpenCV non installé"
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): return False, "✗ Caméra inaccessible"
        self.after(0, lambda: self.reg_status_var.set(
            "📸 Regardez la caméra... (30 photos)"))
        samples, frames = [], 0
        while frames < 150 and len(samples) < 30:
            ret, frame = cap.read()
            if not ret: break
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(100,100))
            for (x,y,w,h) in faces:
                samples.append(cv2.resize(gray[y:y+h, x:x+w], (200,200)))
            frames += 1
            n = len(samples)
            if n > 0 and n % 5 == 0:
                self.after(0, lambda nn=n: self.reg_status_var.set(
                    f"📸 Capture... {nn}/30"))
            time.sleep(0.05)
        cap.release()
        if len(samples) < 10:
            return False, f"✗ Visage non détecté ({len(samples)} captures)"
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(samples, np.array([0]*len(samples)))
        recognizer.save(str(FACES_DIR / f"{name}.yml"))
        return True, f"✓ Visage enregistré ({len(samples)} captures)"

    def _reg_voice(self, name: str) -> Tuple[bool, str]:
        if not VOSK_OK: return False, "✗ Vosk non installé"
        mp = resource_path("vosk-model")
        if not os.path.exists(mp): return False, "✗ Modèle Vosk introuvable"
        self.after(0, lambda: self.reg_status_var.set("🎙 Dites votre phrase..."))
        try:
            import sounddevice as sd
            import queue as queue_module
            
            model  = vosk.Model(mp)
            rec    = vosk.KaldiRecognizer(model, 16000)
            
            # File d'attente pour l'audio avec sounddevice
            audio_queue = queue_module.Queue()
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(status, file=sys.stderr)
                audio_queue.put(bytes(indata))
            
            stream = sd.RawInputStream(samplerate=16000, blocksize=8192, dtype='int16',
                                      channels=1, callback=audio_callback)
            stream.start()
        except Exception as e:
            return False, f"✗ Erreur audio : {e}"
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                data = audio_queue.get(timeout=0.1)
                if rec.AcceptWaveform(data):
                    text = json.loads(rec.Result()).get("text","").strip()
                    if text:
                        stream.stop(); stream.close()
                        u = load_users()
                        if name not in u: u[name] = {}
                        u[name]["voice_phrase"] = text
                        save_users(u)
                        return True, "✓ Voix enregistrée"
            except queue_module.Empty:
                continue
        stream.stop(); stream.close()
        return False, "✗ Aucune voix détectée"

    # ── Helpers communs ────────────────────────────────────────────────────────
    def _delete_user(self):
        sel = self.home_users_lb.curselection()
        if not sel:
            messagebox.showwarning("Sélection", "Sélectionnez un utilisateur.")
            return
        name = self.home_users_lb.get(sel[0]).strip().split()[-1]
        if messagebox.askyesno("Supprimer", f"Supprimer «{name}» ?"):
            users = load_users()
            if name in users: del users[name]
            fp = FACES_DIR / f"{name}.yml"
            if fp.exists(): fp.unlink()
            save_users(users)
            self._refresh_home()

    def _btn(self, parent, text: str, cmd,
             primary: bool = True, width: int = 200, small: bool = False):
        bg = C_ACCENT if primary else C_PANEL
        fg = C_BG     if primary else C_TEXT
        b = tk.Button(parent, text=text, command=cmd,
                      bg=bg, fg=fg,
                      font=("Courier", 10 if small else 11, "bold"),
                      width=width//8, bd=0, cursor="hand2",
                      activebackground=C_ACCENT2 if primary else C_BORDER,
                      activeforeground=C_TEXT,
                      pady=5 if small else 8,
                      highlightthickness=1,
                      highlightbackground=C_ACCENT if primary else C_BORDER)
        b.bind("<Enter>", lambda e: b.config(
            bg=C_ACCENT2 if primary else C_BORDER))
        b.bind("<Leave>", lambda e: b.config(bg=bg))
        return b

    def _draw_logo(self, canvas: tk.Canvas):
        cx, cy = 60, 60
        for i in range(6):
            a  = math.radians(60*i-30); a2 = math.radians(60*(i+1)-30)
            canvas.create_line(cx+45*math.cos(a), cy+45*math.sin(a),
                               cx+45*math.cos(a2), cy+45*math.sin(a2),
                               fill=C_ACCENT, width=2)
        canvas.create_oval(cx-28, cy-28, cx+28, cy+28,
                           outline=C_ACCENT2, width=2, fill="")
        canvas.create_text(cx, cy, text="⬡",
                           fill=C_ACCENT, font=("Courier",24,"bold"))

    def _draw_success_check(self, canvas: tk.Canvas):
        cx, cy = 100, 100
        canvas.create_oval(cx-70, cy-70, cx+70, cy+70,
                           outline=C_SUCCESS, width=4, fill="")
        canvas.create_line(cx-30, cy, cx-5, cy+28, cx+40, cy-28,
                           fill=C_SUCCESS, width=5)


# ══════════════════════════════════════════════════════════════════════════════
def main():
    try:
        app = BioAccessApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()