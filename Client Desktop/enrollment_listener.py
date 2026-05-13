#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enrollment Listener — BioAccess Secure Desktop
Tourne en arrière-plan et attend qu'un admin déclenche l'enrôlement biométrique.

Flux :
  1. Le listener lit employee_id depuis device.id (ou demande une config)
  2. Il poll GET /api/v1/desktop/enrollment/poll?employee_id=<id> toutes les 5 s
  3. Quand pending=True → ouvre une fenêtre Tkinter de capture
  4. Capture 5 frames faciales + EAR liveness + 5 s de voix
  5. Envoie POST /api/v1/desktop/enrollment/submit avec les données
  6. Stocke le device_id retourné dans device.id
"""

import os
import sys
import json
import time
import base64
import logging
import threading
import platform
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("enrollment_listener")

SCRIPT_DIR = Path(__file__).parent.absolute()
DEVICE_FILE = SCRIPT_DIR / "device.id"
SERVER_URL = "http://localhost:5000"
POLL_INTERVAL = 5  # secondes

# ── Dépendances optionnelles ──────────────────────────────────────────────────
try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    logger.error("requests non installé — enrollment_listener désactivé")

try:
    import cv2
    import numpy as np
    OPENCV_OK = True
except ImportError:
    OPENCV_OK = False

try:
    import face_recognition
    FACE_REC_OK = True
except ImportError:
    FACE_REC_OK = False

try:
    import sounddevice as sd
    AUDIO_OK = True
except ImportError:
    AUDIO_OK = False

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    TK_OK = True
except ImportError:
    TK_OK = False


# ═════════════════════════════════════════════════════════════════════════════
# Persistance locale — device.id
# ═════════════════════════════════════════════════════════════════════════════

def load_device_info() -> dict:
    """Lit device.id et retourne {'employee_id', 'device_id', 'mac_address'}."""
    if DEVICE_FILE.exists():
        try:
            return json.loads(DEVICE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def save_device_info(info: dict):
    try:
        DEVICE_FILE.write_text(json.dumps(info, indent=2), encoding='utf-8')
    except Exception as e:
        logger.error(f"Impossible d'écrire device.id : {e}")


def get_mac_address() -> str:
    """Retourne l'adresse MAC principale de la machine (format XX:XX:XX:XX:XX:XX)."""
    try:
        import uuid as _uuid
        mac = ':'.join(
            ['{:02X}'.format(((_uuid.getnode() >> i) & 0xFF))
             for i in range(0, 48, 8)][::-1]
        )
        return mac
    except Exception:
        return 'UNKNOWN'


def announce_to_server(mac: str, hostname: str) -> dict:
    """Annonce ce poste au serveur backend, retourne la réponse JSON."""
    try:
        r = requests.post(
            f"{SERVER_URL}/api/v1/desktop/announce",
            json={
                'mac_address': mac,
                'hostname': hostname,
                'systeme': platform.system(),
                'os_version': platform.version()[:50],
            },
            timeout=5,
        )
        return r.json() if r.ok else {}
    except Exception as e:
        logger.debug(f"announce: {e}")
        return {}


# ═════════════════════════════════════════════════════════════════════════════
# Calcul EAR (Eye Aspect Ratio) pour liveness
# ═════════════════════════════════════════════════════════════════════════════

def _dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def compute_ear(eye_landmarks) -> float:
    """
    eye_landmarks: liste de 6 (x, y) tuples (face_recognition.face_landmarks order)
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    """
    if len(eye_landmarks) < 6:
        return 1.0
    p1, p2, p3, p4, p5, p6 = eye_landmarks[:6]
    return (_dist(p2, p6) + _dist(p3, p5)) / (2.0 * max(_dist(p1, p4), 1e-6))


# ═════════════════════════════════════════════════════════════════════════════
# Fenêtre d'enrôlement Tkinter
# ═════════════════════════════════════════════════════════════════════════════

class EnrollmentWindow:
    """Fenêtre Tkinter qui guide l'employé pendant la capture biométrique."""

    EAR_BLINK_THRESH = 0.22  # en dessous = clignement détecté
    FRAMES_NEEDED = 5
    AUDIO_SECONDS = 5
    AUDIO_SAMPLERATE = 16000

    def __init__(self, session_key: str, employee_name: str, on_done):
        self.session_key = session_key
        self.employee_name = employee_name
        self.on_done = on_done  # callback(success: bool)

        self._face_frames_b64 = []  # liste de str base64
        self._ear_values = []
        self._audio_bytes = None
        self._cap = None
        self._running = False

        self._root = None

    def run(self):
        """Ouvre la fenêtre (bloquant — appeler depuis le thread Tkinter)."""
        self._root = tk.Tk()
        self._root.title("BioAccess Secure — Enrôlement biométrique")
        self._root.geometry("560x460")
        self._root.resizable(False, False)
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self._root, bg="#4f46e5", height=60)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Enrôlement biométrique", fg="white",
                 bg="#4f46e5", font=("Helvetica", 14, "bold")).pack(pady=16)

        # ── Statut ──────────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value=f"Bonjour {self.employee_name} — préparation…")
        tk.Label(self._root, textvariable=self._status_var, font=("Helvetica", 11),
                 wraplength=520, justify="center").pack(pady=8)

        # ── Canvas caméra ────────────────────────────────────────────────────
        self._canvas = tk.Canvas(self._root, width=320, height=240, bg="black")
        self._canvas.pack()

        # ── Barre de progression ─────────────────────────────────────────────
        self._progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(self._root, variable=self._progress_var,
                        maximum=100, length=400).pack(pady=8)

        # ── Bouton démarrage ──────────────────────────────────────────────────
        self._start_btn = tk.Button(self._root, text="Commencer la capture",
                                    bg="#4f46e5", fg="white", font=("Helvetica", 11),
                                    padx=16, pady=8, relief="flat",
                                    command=self._start_capture)
        self._start_btn.pack(pady=8)

        self._root.mainloop()

    def _on_close(self):
        self._running = False
        if self._cap:
            self._cap.release()
        self._root.destroy()
        self.on_done(False)

    def _set_status(self, msg: str):
        if self._root:
            self._root.after(0, lambda: self._status_var.set(msg))

    def _set_progress(self, pct: float):
        if self._root:
            self._root.after(0, lambda: self._progress_var.set(pct))

    # ── Capture en thread séparé ─────────────────────────────────────────────
    def _start_capture(self):
        self._start_btn.config(state="disabled")
        threading.Thread(target=self._capture_thread, daemon=True).start()

    def _capture_thread(self):
        try:
            self._capture_face()
            if not self._face_frames_b64:
                self._set_status("Aucun visage capturé — réessayez.")
                self._start_btn.config(state="normal")
                return

            if AUDIO_OK:
                self._capture_voice()
            else:
                self._set_status("Microphone non disponible — enrôlement facial uniquement.")
                time.sleep(1)

            self._set_status("Envoi des données au serveur…")
            self._set_progress(90)
            self._send_to_backend()
        except Exception as e:
            logger.error(f"_capture_thread: {e}", exc_info=True)
            self._set_status(f"Erreur : {e}")
            if self._root:
                self._root.after(3000, self._root.destroy)
            self.on_done(False)

    # ── Capture faciale ──────────────────────────────────────────────────────
    def _capture_face(self):
        self._set_status("Regardez la caméra — clignez des yeux lentement.")
        if not OPENCV_OK:
            self._set_status("OpenCV non disponible — capture impossible.")
            return

        self._cap = cv2.VideoCapture(0)
        if not self._cap.isOpened():
            self._set_status("Caméra inaccessible.")
            return

        self._running = True
        blink_detected = False
        frames_ok = 0

        try:
            from PIL import Image, ImageTk
            PIL_OK = True
        except ImportError:
            PIL_OK = False

        while self._running and frames_ok < self.FRAMES_NEEDED:
            ret, frame = self._cap.read()
            if not ret:
                break

            # Afficher dans le canvas
            if PIL_OK and self._root:
                try:
                    rgb_preview = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img_pil = Image.fromarray(rgb_preview).resize((320, 240))
                    img_tk = ImageTk.PhotoImage(img_pil)
                    self._root.after(0, lambda i=img_tk: self._canvas.create_image(0, 0, anchor="nw", image=i))
                    # Garder une référence pour éviter le garbage-collect
                    self._canvas._img_ref = img_tk
                except Exception:
                    pass

            # Extraire features faciales
            if FACE_REC_OK:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locs = face_recognition.face_locations(rgb, model='hog')
                if locs:
                    landmarks_list = face_recognition.face_landmarks(rgb, locs)
                    if landmarks_list:
                        lm = landmarks_list[0]
                        left_eye = lm.get('left_eye', [])
                        right_eye = lm.get('right_eye', [])
                        if left_eye and right_eye:
                            ear = (compute_ear(left_eye) + compute_ear(right_eye)) / 2.0
                            self._ear_values.append(ear)
                            if ear < self.EAR_BLINK_THRESH:
                                blink_detected = True

                    # Encoder ce frame
                    encs = face_recognition.face_encodings(rgb, locs)
                    if encs:
                        _, img_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                        b64 = base64.b64encode(img_buf.tobytes()).decode('utf-8')
                        self._face_frames_b64.append(b64)
                        frames_ok += 1
                        self._set_progress(frames_ok / self.FRAMES_NEEDED * 40)
                        self._set_status(f"Visage capturé {frames_ok}/{self.FRAMES_NEEDED}…"
                                         + (" Clignement détecté !" if blink_detected else " Clignez des yeux."))
            else:
                # Sans face_recognition : capturer les frames brutes
                _, img_buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                b64 = base64.b64encode(img_buf.tobytes()).decode('utf-8')
                self._face_frames_b64.append(b64)
                frames_ok += 1
                self._set_progress(frames_ok / self.FRAMES_NEEDED * 40)

            time.sleep(0.3)

        self._cap.release()
        self._cap = None
        self._set_status("Capture faciale terminée." if self._face_frames_b64 else "Aucun visage détecté.")

    # ── Capture vocale ───────────────────────────────────────────────────────
    def _capture_voice(self):
        self._set_status("Parlez maintenant : prononcez votre nom et département…")
        self._set_progress(50)

        try:
            import io as _io
            import wave

            frames_audio = []
            q = __import__('queue').Queue()

            def callback(indata, frames, t, status):
                q.put(bytes(indata))

            with sd.RawInputStream(samplerate=self.AUDIO_SAMPLERATE, channels=1,
                                   dtype='int16', callback=callback):
                deadline = time.time() + self.AUDIO_SECONDS
                while time.time() < deadline:
                    remaining = deadline - time.time()
                    self._set_status(f"Parlez… {remaining:.0f}s restantes")
                    self._set_progress(50 + (1 - remaining / self.AUDIO_SECONDS) * 35)
                    try:
                        frames_audio.append(q.get(timeout=0.1))
                    except Exception:
                        pass

            # Assembler en WAV
            buf = _io.BytesIO()
            with wave.open(buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.AUDIO_SAMPLERATE)
                wf.writeframes(b''.join(frames_audio))
            self._audio_bytes = buf.getvalue()
            self._set_status("Enregistrement vocal terminé.")
        except Exception as e:
            logger.warning(f"Capture voix: {e}")
            self._set_status("Microphone inaccessible — enrôlement facial uniquement.")

    # ── Envoi au backend ─────────────────────────────────────────────────────
    def _send_to_backend(self):
        liveness = bool(self._ear_values and min(self._ear_values) < self.EAR_BLINK_THRESH)
        payload = {
            'session_key': self.session_key,
            'mac_address': get_mac_address(),
            'face_frames': self._face_frames_b64,
            'voice_base64': base64.b64encode(self._audio_bytes).decode('utf-8') if self._audio_bytes else None,
            'liveness_confirmed': liveness,
            'ear_min': min(self._ear_values) if self._ear_values else None,
        }

        try:
            r = requests.post(
                f"{SERVER_URL}/api/v1/desktop/enrollment/submit",
                json=payload,
                timeout=30,
            )
            result = r.json()
            if result.get('success'):
                device_id = result.get('device_id')
                if device_id:
                    info = load_device_info()
                    info['device_id'] = device_id
                    save_device_info(info)
                self._set_status(f"Enrôlement réussi ! {result.get('message', '')}")
                self._set_progress(100)
                if self._root:
                    self._root.after(3000, lambda: (self._root.destroy(), self.on_done(True)))
            else:
                err = result.get('error', 'Erreur inconnue')
                self._set_status(f"Erreur serveur : {err}")
                if self._root:
                    self._root.after(4000, self._root.destroy)
                self.on_done(False)
        except Exception as e:
            logger.error(f"Erreur envoi: {e}", exc_info=True)
            self._set_status(f"Erreur réseau : {e}")
            if self._root:
                self._root.after(3000, self._root.destroy)
            self.on_done(False)


# ═════════════════════════════════════════════════════════════════════════════
# Listener principal (thread de fond)
# ═════════════════════════════════════════════════════════════════════════════

class EnrollmentListener:
    """
    Thread daemon qui poll le serveur et déclenche l'UI d'enrôlement.
    Utilisation depuis maindesktop.py :
        listener = EnrollmentListener()
        listener.start()
    """

    def __init__(self):
        self._thread = threading.Thread(target=self._run, daemon=True, name="EnrollmentListener")
        self._stop_event = threading.Event()
        self._enrolling = threading.Event()  # empêche deux sessions simultanées

        # Charger les infos locales
        info = load_device_info()
        self._employee_id: str | None = info.get('employee_id')
        self._mac = get_mac_address()
        self._hostname = platform.node()

        # Annoncer ce poste au démarrage
        if REQUESTS_OK and self._employee_id:
            threading.Thread(target=self._announce, daemon=True).start()

    def _announce(self):
        result = announce_to_server(self._mac, self._hostname)
        if result.get('success'):
            eid = result.get('employee_id')
            if eid and eid != self._employee_id:
                self._employee_id = eid
                info = load_device_info()
                info['employee_id'] = eid
                info['device_id'] = result.get('device_id', info.get('device_id'))
                save_device_info(info)
            logger.info(f"Annoncé — employee_id={self._employee_id}")

    def set_employee_id(self, employee_id: str):
        """Peut être appelé depuis maindesktop quand l'utilisateur se connecte."""
        if self._employee_id == employee_id:
            return
        self._employee_id = employee_id
        info = load_device_info()
        info['employee_id'] = employee_id
        save_device_info(info)
        threading.Thread(target=self._announce, daemon=True).start()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        if not REQUESTS_OK:
            logger.warning("EnrollmentListener désactivé (requests manquant)")
            return

        logger.info("EnrollmentListener démarré")
        while not self._stop_event.is_set():
            try:
                if self._employee_id and not self._enrolling.is_set():
                    self._poll()
            except Exception as e:
                logger.debug(f"Poll erreur: {e}")
            self._stop_event.wait(POLL_INTERVAL)

    def _poll(self):
        try:
            r = requests.get(
                f"{SERVER_URL}/api/v1/desktop/enrollment/poll",
                params={'employee_id': self._employee_id},
                timeout=4,
            )
            if not r.ok:
                return
            data = r.json()
            if data.get('pending') and not self._enrolling.is_set():
                session_key = data['session_key']
                employee_name = data.get('employee_name', 'Employé')
                logger.info(f"Enrôlement en attente — session {session_key}")
                self._start_enrollment_ui(session_key, employee_name)
        except requests.exceptions.ConnectionError:
            pass  # backend pas encore démarré
        except Exception as e:
            logger.debug(f"_poll: {e}")

    def _start_enrollment_ui(self, session_key: str, employee_name: str):
        if not TK_OK:
            logger.warning("Tkinter non disponible — UI d'enrôlement impossible")
            return

        self._enrolling.set()

        def on_done(success: bool):
            self._enrolling.clear()
            if success:
                logger.info("Enrôlement terminé avec succès")
            else:
                logger.warning("Enrôlement annulé ou échoué")

        # Ouvrir dans un thread séparé (Tkinter doit tourner dans le thread principal
        # ou dans son propre thread — ici on utilise un thread dédié)
        def ui_thread():
            win = EnrollmentWindow(session_key, employee_name, on_done)
            win.run()

        t = threading.Thread(target=ui_thread, daemon=True, name="EnrollmentUI")
        t.start()


# ═════════════════════════════════════════════════════════════════════════════
# Utilisation autonome (test)
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(name)s] %(levelname)s %(message)s')

    info = load_device_info()
    if not info.get('employee_id'):
        employee_id = input("Entrez votre employee_id (UUID) : ").strip()
        if employee_id:
            info['employee_id'] = employee_id
            info['mac_address'] = get_mac_address()
            save_device_info(info)
    else:
        print(f"employee_id : {info['employee_id']}")

    listener = EnrollmentListener()
    listener.start()
    print("Listener démarré — Ctrl+C pour arrêter")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        print("Arrêté.")
