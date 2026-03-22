"""
Interface de connexion - Écran principal Tkinter
Gère la reconnaissance faciale et vocale
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import cv2
import numpy as np

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, THEME_COLOR, ACCENT_COLOR, ERROR_COLOR,
    MAX_ATTEMPTS, ATTEMPT_TIMEOUT, FACE_SCAN_TIMEOUT, AUDIO_DURATION,
    FACE_CONFIDENCE_THRESHOLD, VOICE_CONFIDENCE_THRESHOLD
)
from services.api_client import api_client
from biometric.face import face_recognizer
from biometric.voice import voice_recorder

logger = logging.getLogger(__name__)


class LoginScreen:
    """Interface de connexion avec reconnaissance biométrique"""

    def __init__(self, root: tk.Tk):
        """
        Initialiser l'interface
        
        Args:
            root: Fenêtre Tkinter principale
        """
        self.root = root
        self.root.title("🔐 BioAccess Secure - Authentification")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=THEME_COLOR)
        
        # État de l'application
        self.camera = None
        self.is_camera_running = False
        self.is_recording = False
        self.authenticated = False
        self.current_user = None
        self.attempts_remaining = MAX_ATTEMPTS
        self.attempt_timeout_end = None
        
        # Variables threading
        self.camera_thread = None
        self.processing_thread = None
        
        # Construire l'interface
        self._build_ui()
        
        # Vérifier l'API
        self._check_api_connection()
        
        logger.info("✓ Interface initialisée")

    def _build_ui(self):
        """Construire l'interface graphique"""
        
        # ============ HEADER ============
        header = tk.Frame(self.root, bg=ACCENT_COLOR, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title = tk.Label(header, text="🔐 BioAccess Secure", 
                        font=("Arial", 28, "bold"), 
                        bg=ACCENT_COLOR, fg="white")
        title.pack(pady=20)
        
        # ============ MAIN CONTENT ============
        main_frame = tk.Frame(self.root, bg=THEME_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configuration du grid
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # --- ZONE GAUCHE: CAMÉRA ---
        left_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.SUNKEN, bd=2)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        left_frame.grid_propagate(False)
        left_frame.configure(width=350, height=400)
        
        camera_label = tk.Label(left_frame, text="📷 Caméra", 
                               font=("Arial", 14, "bold"),
                               bg="#34495E", fg=ACCENT_COLOR)
        camera_label.pack(pady=(10, 0))
        
        # Canvas pour afficher la caméra
        self.camera_canvas = tk.Canvas(left_frame, bg="black", 
                                       width=320, height=240)
        self.camera_canvas.pack(pady=10)
        
        # État caméra
        self.camera_status_label = tk.Label(left_frame, text="⚙️ Initialisation...",
                                           font=("Arial", 10),
                                           bg="#34495E", fg="white")
        self.camera_status_label.pack(pady=5)
        
        # Boutons caméra
        button_frame_camera = tk.Frame(left_frame, bg="#34495E")
        button_frame_camera.pack(pady=10)
        
        self.btn_face = tk.Button(button_frame_camera, text="📸 Scanner Visage",
                                 command=self._on_face_scan,
                                 font=("Arial", 11, "bold"),
                                 bg=ACCENT_COLOR, fg="white",
                                 padx=15, pady=10, relief=tk.RAISED, bd=2,
                                 cursor="hand2")
        self.btn_face.pack(pady=5)
        
        self.btn_voice = tk.Button(button_frame_camera, text="🎤 Utiliser la Voix",
                                  command=self._on_voice_record,
                                  font=("Arial", 11, "bold"),
                                  bg="#3498DB", fg="white",
                                  padx=15, pady=10, relief=tk.RAISED, bd=2,
                                  cursor="hand2")
        self.btn_voice.pack(pady=5)
        
        # --- ZONE DROITE: STATUT ET MESSAGES ---
        right_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.SUNKEN, bd=2)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        status_label = tk.Label(right_frame, text="📊 Statut", 
                               font=("Arial", 14, "bold"),
                               bg="#34495E", fg=ACCENT_COLOR)
        status_label.pack(pady=(10, 5), padx=10)
        
        # Cadre pour la zone messages
        msg_inner_frame = tk.Frame(right_frame, bg="#2C3E50", relief=tk.SUNKEN, bd=1)
        msg_inner_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Zone messages
        self.message_text = tk.Text(msg_inner_frame, 
                                   font=("Courier", 10),
                                   bg="#1C2833", fg="#ECF0F1",
                                   height=15, width=35,
                                   relief=tk.FLAT, bd=0)
        self.message_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.message_text.config(state=tk.DISABLED)
        
        # Scrollbar pour les messages
        scrollbar = tk.Scrollbar(msg_inner_frame, command=self.message_text.yview)
        self.message_text.config(yscrollcommand=scrollbar.set)
        
        # --- INFOS UTILISATEUR ---
        info_frame = tk.Frame(main_frame, bg="#34495E", relief=tk.SUNKEN, bd=2)
        info_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        info_title = tk.Label(info_frame, text="👤 Informations", 
                             font=("Arial", 12, "bold"),
                             bg="#34495E", fg=ACCENT_COLOR)
        info_title.pack(pady=(10, 5), padx=10, anchor="w")
        
        info_details_frame = tk.Frame(info_frame, bg="#2C3E50")
        info_details_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.user_label = tk.Label(info_details_frame, text="Utilisateur: Non connecté",
                                  font=("Arial", 10),
                                  bg="#2C3E50", fg="white", justify="left")
        self.user_label.pack(anchor="w", pady=2)
        
        self.confidence_label = tk.Label(info_details_frame, 
                                        text="Confiance: --",
                                        font=("Arial", 10),
                                        bg="#2C3E50", fg="white", justify="left")
        self.confidence_label.pack(anchor="w", pady=2)
        
        self.attempts_label = tk.Label(info_details_frame,
                                      text=f"Tentatives: {self.attempts_remaining}/{MAX_ATTEMPTS}",
                                      font=("Arial", 10),
                                      bg="#2C3E50", fg="white", justify="left")
        self.attempts_label.pack(anchor="w", pady=2)
        
        # --- FOOTER ---
        footer = tk.Frame(self.root, bg="#2C3E50", height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        
        footer_text = tk.Label(footer, 
                              text="🔒 Système de biométrie sécurisé | v1.0",
                              font=("Arial", 9),
                              bg="#2C3E50", fg="#BDC3C7")
        footer_text.pack(pady=15)
        
        # Bouton Quitter
        btn_quit = tk.Button(footer, text="❌ Quitter",
                            command=self._on_quit,
                            font=("Arial", 10),
                            bg=ERROR_COLOR, fg="white",
                            padx=10, pady=5, relief=tk.RAISED, bd=1,
                            cursor="hand2")
        btn_quit.pack(side=tk.RIGHT, padx=10)

    def _check_api_connection(self):
        """Vérifier la connexion à l'API"""
        self._log("🔍 Vérification de la connexion API...")
        
        def check():
            try:
                success, data = api_client.health_check()
                if success:
                    self._log("✅ API accessible")
                else:
                    self._log("❌ API non accessible")
                    self._disable_buttons()
            except Exception as e:
                self._log(f"❌ Erreur API: {str(e)}")
                self._disable_buttons()
        
        threading.Thread(target=check, daemon=True).start()

    def _log(self, message: str, level: str = "info"):
        """
        Ajouter un message au log
        
        Args:
            message: Message à afficher
            level: Type de message (info, success, error)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Colorer selon le type
        tag = level
        
        self.message_text.config(state=tk.NORMAL)
        self.message_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)
        
        # Configurer les tags de couleur
        if level == "success":
            self.message_text.tag_config(tag, foreground="#27AE60")
        elif level == "error":
            self.message_text.tag_config(tag, foreground="#E74C3C")
        else:
            self.message_text.tag_config(tag, foreground="#3498DB")
        
        logger.info(message)

    def _disable_buttons(self):
        """Désactiver les boutons de scan"""
        self.btn_face.config(state=tk.DISABLED)
        self.btn_voice.config(state=tk.DISABLED)

    def _enable_buttons(self):
        """Activer les boutons de scan"""
        self.btn_face.config(state=tk.NORMAL)
        self.btn_voice.config(state=tk.NORMAL)

    def _on_face_scan(self):
        """Handler pour le scan facial"""
        if self.is_recording:
            messagebox.showwarning("Attention", "Enregistrement en cours...")
            return
        
        if self.attempt_timeout_end and datetime.now() < self.attempt_timeout_end:
            remaining = (self.attempt_timeout_end - datetime.now()).seconds
            messagebox.showwarning("Bloqué", f"Trop de tentatives. Réessayez dans {remaining}s")
            return
        
        self._log("📸 Lancement du scan facial...", "info")
        self.btn_face.config(state=tk.DISABLED)
        
        def scan_face_thread():
            try:
                # Démarrer la caméra
                if not self.camera or not self.camera.isOpened():
                    self.camera = face_recognizer.start_camera()
                    if not self.camera:
                        self._log("❌ Impossible d'accéder à la caméra", "error")
                        self.btn_face.config(state=tk.NORMAL)
                        return
                
                # Afficher la caméra en direct
                self.is_camera_running = True
                self._display_camera_feed()
                
                # Capturer un visage
                self._log("📷 Veuillez vous positionner devant la caméra...", "info")
                face_image = face_recognizer.capture_face(self.camera, max_attempts=FACE_SCAN_TIMEOUT)
                
                self.is_camera_running = False
                
                if face_image is None:
                    self._log("❌ Aucun visage détecté", "error")
                    self.attempts_remaining -= 1
                    self._update_attempts()
                else:
                    # Convertir en base64
                    face_b64 = face_recognizer.image_to_base64(face_image)
                    
                    if not face_b64:
                        self._log("❌ Erreur d'encodage", "error")
                        self.attempts_remaining -= 1
                        self._update_attempts()
                        return
                    
                    # Envoyer à l'API
                    self._log("📤 Envoi au serveur...", "info")
                    success, response = api_client.authenticate_face(face_b64)
                    
                    if success and response.get('status') == 'success':
                        user_name = response.get('user', 'Utilisateur')
                        confidence = response.get('confidence', 0)
                        self._on_auth_success(user_name, confidence, 'facial')
                    else:
                        error_msg = response.get('message', response.get('error', 'Authentification échouée'))
                        self._log(f"❌ {error_msg}", "error")
                        self.attempts_remaining -= 1
                        self._update_attempts()
                        
                        if self.attempts_remaining > 0:
                            self._log(f"💡 Veuillez essayer la reconnaissance vocale", "info")
            
            except Exception as e:
                self._log(f"❌ Erreur: {str(e)}", "error")
                self.attempts_remaining -= 1
                self._update_attempts()
            
            finally:
                self.is_camera_running = False
                self.btn_face.config(state=tk.NORMAL)
        
        self.processing_thread = threading.Thread(target=scan_face_thread, daemon=True)
        self.processing_thread.start()

    def _on_voice_record(self):
        """Handler pour l'enregistrement vocal"""
        if self.is_recording:
            messagebox.showwarning("Attention", "Enregistrement déjà en cours")
            return
        
        if self.attempt_timeout_end and datetime.now() < self.attempt_timeout_end:
            remaining = (self.attempt_timeout_end - datetime.now()).seconds
            messagebox.showwarning("Bloqué", f"Trop de tentatives. Réessayez dans {remaining}s")
            return
        
        if not voice_recorder.is_available():
            messagebox.showerror("Erreur", "Aucun périphérique audio disponible")
            return
        
        self._log("🎤 Lancement enregistrement vocal...", "info")
        self.btn_voice.config(state=tk.DISABLED)
        self.is_recording = True
        
        def record_voice_thread():
            try:
                self._log(f"🎙️ Enregistrement en cours ({AUDIO_DURATION}s)...", "info")
                
                # Enregistrer l'audio
                audio = voice_recorder.record_audio(duration=AUDIO_DURATION)
                
                if audio is None:
                    self._log("❌ Erreur lors de l'enregistrement", "error")
                    self.attempts_remaining -= 1
                    self._update_attempts()
                    return
                
                # Convertir en base64
                audio_b64 = voice_recorder.audio_to_wav_base64(audio)
                
                if not audio_b64:
                    self._log("❌ Erreur d'encodage audio", "error")
                    self.attempts_remaining -= 1
                    self._update_attempts()
                    return
                
                # Envoyer à l'API
                self._log("📤 Envoi au serveur...", "info")
                success, response = api_client.authenticate_voice(audio_b64)
                
                if success and response.get('status') == 'success':
                    user_name = response.get('user', 'Utilisateur')
                    confidence = response.get('confidence', 0)
                    self._on_auth_success(user_name, confidence, 'vocal')
                else:
                    error_msg = response.get('message', response.get('error', 'Authentification échouée'))
                    self._log(f"❌ {error_msg}", "error")
                    self.attempts_remaining -= 1
                    self._update_attempts()
            
            except Exception as e:
                self._log(f"❌ Erreur: {str(e)}", "error")
                self.attempts_remaining -= 1
                self._update_attempts()
            
            finally:
                self.is_recording = False
                self.btn_voice.config(state=tk.NORMAL)
        
        self.processing_thread = threading.Thread(target=record_voice_thread, daemon=True)
        self.processing_thread.start()

    def _on_auth_success(self, user_name: str, confidence: float, mode: str):
        """Authentification réussie"""
        self._log(f"✅ Authentification réussie!", "success")
        self._log(f"👤 Utilisateur: {user_name}", "success")
        self._log(f"🎯 Confiance: {confidence:.1%}", "success")
        self._log(f"🔍 Mode: {'Reconnaissance faciale' if mode == 'facial' else 'Reconnaissance vocale'}", "success")
        
        self.user_label.config(text=f"Utilisateur: {user_name} ✅")
        self.confidence_label.config(text=f"Confiance: {confidence:.1%}")
        self.current_user = user_name
        self.authenticated = True
        self.attempts_remaining = MAX_ATTEMPTS
        
        # Désactiver les boutons
        self.btn_face.config(state=tk.DISABLED)
        self.btn_voice.config(state=tk.DISABLED)
        
        # Afficher un message de succès
        messagebox.showinfo("✅ Succès", f"Bienvenue {user_name}!\n\nAuthentification réussie.")

    def _update_attempts(self):
        """Mettre à jour l'affichage des tentatives"""
        self.attempts_label.config(
            text=f"Tentatives: {self.attempts_remaining}/{MAX_ATTEMPTS}"
        )
        
        if self.attempts_remaining <= 0:
            self._log("⛔ Nombre maximum de tentatives atteint", "error")
            self.attempt_timeout_end = datetime.now() + timedelta(seconds=ATTEMPT_TIMEOUT)
            self._disable_buttons()
            messagebox.showerror("Bloqué", f"Trop de tentatives. Réessayez dans {ATTEMPT_TIMEOUT}s")

    def _display_camera_feed(self):
        """Afficher le flux caméra en temps réel"""
        if not self.is_camera_running or not self.camera or not self.camera.isOpened():
            return
        
        frame = face_recognizer.read_frame(self.camera)
        
        if frame is not None:
            # Redimensionner et ajouter détection
            frame = face_recognizer.resize_frame(frame, 320, 240)
            frame_with_boxes = face_recognizer.frame_with_detection(frame)
            
            # Convertir en RGB et PIL
            frame_rgb = cv2.cvtColor(frame_with_boxes, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Afficher
            self.camera_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.camera_canvas.image = photo  # Garder une référence
            
            self.camera_status_label.config(
                text=f"📹 En direct ({frame.shape[1]}x{frame.shape[0]})"
            )
        
        # Continuer à rafraîchir
        if self.is_camera_running:
            self.root.after(33, self._display_camera_feed)  # ~30 FPS

    def _on_quit(self):
        """Quitter l'application"""
        if messagebox.askyesno("Confirmer", "Êtes-vous sûr de vouloir quitter?"):
            self._cleanup()
            self.root.quit()

    def _cleanup(self):
        """Nettoyer les ressources"""
        self.is_camera_running = False
        if self.camera:
            face_recognizer.stop_camera(self.camera)
        
        logger.info("Application fermée")


def main():
    """Point d'entrée"""
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/client.log'),
            logging.StreamHandler()
        ]
    )
    
    root = tk.Tk()
    app = LoginScreen(root)
    root.mainloop()


if __name__ == "__main__":
    main()
