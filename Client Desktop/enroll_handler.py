import json
import os
import queue
import random
import sys
import time
import threading
import tkinter as tk
from difflib import SequenceMatcher
from tkinter import messagebox

try:
    import sounddevice as sd
    import vosk
except ImportError:
    sd = None
    vosk = None

VOICE_PHRASES = [
    'Bonjour je confirme mon identité',
    'Je déclare ma présence au poste',
    'J autorise l accès sécurisé',
    'Phrase de vérification vocale en français',
    'Contrôle biométrique par voix activé',
    'Je parle pour activer mon profil',
    'Sécurité vocale validée maintenant',
    'Ma voix authentifie l accès',
    'BioAccess sécurise cet enregistrement',
    'Enregistrement vocal confirmé',
]


def _normalize(value: str) -> str:
    return ' '.join(
        ''.join(c.lower() if c.isalnum() or c.isspace() else ' ' for c in (value or '')).split()
    )


def _similarity(a: str, b: str) -> float:
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if not a_norm or not b_norm:
        return 0.0
    return SequenceMatcher(None, a_norm, b_norm).ratio()


class VoiceEnrollmentDialog(tk.Toplevel):
    def __init__(self, parent, model_path: str):
        super().__init__(parent)
        self.title('Enrôlement vocal')
        self.geometry('520x320')
        self.resizable(False, False)
        self.transcript = ''
        self.result = {'success': False, 'message': 'Annulé', 'transcript': ''}
        self.model_path = model_path
        self._recording = False
        self._audio_queue = queue.Queue()
        self._stop_event = threading.Event()
        self.protocol('WM_DELETE_WINDOW', self._on_close)
        self._build_ui()
        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        self.configure(bg='#f8fafc')
        header = tk.Frame(self, bg='#f8fafc')
        header.pack(fill='x', padx=16, pady=(16, 8))
        tk.Label(header, text='Phrase vocale aléatoire', bg='#f8fafc', fg='#111827',
                 font=('Inter', 12, 'bold')).pack(anchor='w')

        self.phrase_box = tk.Frame(self, bg='#fde68a', bd=1, relief='solid')
        self.phrase_box.pack(fill='x', padx=16, pady=(0, 4))
        # Choisir UNE seule phrase aléatoire à l'ouverture
        self._chosen_phrase = random.choice(VOICE_PHRASES)
        self.phrase_label = tk.Label(self.phrase_box, text=f'« {self._chosen_phrase} »',
                                     bg='#fde68a', fg='#111827',
                                     font=('Inter', 13, 'bold'), wraplength=480, justify='left')
        self.phrase_label.pack(padx=12, pady=12)

        # Bouton pour changer de phrase sans recommencer
        tk.Button(self, text='↻ Nouvelle phrase', command=self._new_phrase,
                  bg='#f8fafc', fg='#4b5563', font=('Inter', 9),
                  bd=1, relief='solid', cursor='hand2').pack(pady=(0, 8))

        self.record_btn = tk.Button(self, text='⏺ Enregistrer', command=self._on_record,
                                    bg='#111827', fg='white', activebackground='#374151',
                                    font=('Inter', 11, 'bold'), bd=0, padx=16, pady=10, cursor='hand2')
        self.record_btn.pack(pady=(0, 12))

        tk.Label(self, text='Transcription en temps réel', bg='#f8fafc', fg='#4b5563',
                 font=('Inter', 10, 'bold')).pack(anchor='w', padx=16)
        self.transcript_box = tk.Text(self, height=4, bg='white', fg='#111827',
                                      font=('Inter', 11), wrap='word', state='disabled', bd=1,
                                      relief='solid')
        self.transcript_box.pack(fill='x', padx=16, pady=(4, 8))
        self.status_label = tk.Label(self, text='Cliquez sur Enregistrer pour commencer.',
                                     bg='#f8fafc', fg='#4b5563', font=('Inter', 10))
        self.status_label.pack(anchor='w', padx=16)

    def _new_phrase(self):
        """Remplace la phrase par une autre aléatoire sans relancer l'enregistrement."""
        self._chosen_phrase = random.choice([p for p in VOICE_PHRASES if p != self._chosen_phrase] or VOICE_PHRASES)
        self.phrase_label.config(text=f'« {self._chosen_phrase} »')

    def _update_transcript(self, value: str):
        self.transcript = value or ''
        self.transcript_box.configure(state='normal')
        self.transcript_box.delete('1.0', 'end')
        self.transcript_box.insert('1.0', self.transcript)
        self.transcript_box.configure(state='disabled')

    def _set_status(self, message: str, error: bool = False):
        self.status_label.configure(text=message, fg='#dc2626' if error else '#4b5563')

    def _on_record(self):
        if self._recording:
            return
        if vosk is None or sd is None:
            self._set_status('Vosk ou sounddevice introuvable.', True)
            return
        self.record_btn.configure(state='disabled', text='Enregistrement...')
        self._set_status('Enregistrement en cours. Parlez clairement.', False)
        self._recording = True
        threading.Thread(target=self._record_thread, daemon=True).start()

    def _on_close(self):
        self._stop_event.set()
        self.destroy()

    def _record_thread(self):
        try:
            if not os.path.exists(self.model_path):
                self.after(0, lambda: self._set_status('Modèle Vosk introuvable.', True))
                self._finish(False, 'Modèle Vosk introuvable')
                return
            model = vosk.Model(self.model_path)
            rec = vosk.KaldiRecognizer(model, 16000)

            def callback(indata, frames, time_info, status):
                if status:
                    print(status, file=sys.stderr)
                self._audio_queue.put(bytes(indata))

            with sd.RawInputStream(samplerate=16000, blocksize=8192,
                                   dtype='int16', channels=1, callback=callback):
                deadline = time.time() + 8
                partial_text = ''
                while time.time() < deadline and not self._stop_event.is_set():
                    try:
                        data = self._audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        partial_text = result.get('text', '')
                        self.after(0, lambda text=partial_text: self._update_transcript(text))
                        break
                    else:
                        partial = json.loads(rec.PartialResult()).get('partial', '')
                        if partial:
                            self.after(0, lambda text=partial: self._update_transcript(text))
                if not self.transcript:
                    final = json.loads(rec.FinalResult())
                    self.transcript = final.get('text', '')
                    self.after(0, lambda text=self.transcript: self._update_transcript(text))
        except Exception as exc:
            self.after(0, lambda: self._set_status(f'Erreur micro : {exc}', True))
            self._finish(False, f'Erreur audio : {exc}')
            return

        phrase = getattr(self, '_chosen_phrase', self.phrase_label.cget('text').strip('«» ').strip())
        similarity = _similarity(self.transcript, phrase)
        if similarity >= 0.9:
            self.after(0, lambda: self._set_status('Phrase reconnue avec succès.', False))
            self._finish(True, 'Enregistrement valide')
        else:
            self.after(0, lambda: self._set_status(
                f'Phrase incorrecte ({int(similarity * 100)}% de similarité). Réessayez.', True))
            self._finish(False, 'Phrase incorrecte', self.transcript)

    def _finish(self, success: bool, message: str, transcript: str = None):
        self.result = {
            'success': success,
            'message': message,
            'transcript': transcript if transcript is not None else self.transcript,
        }
        self.after(1200, self._on_close)

    def show(self):
        self.wait_window(self)
        return self.result
