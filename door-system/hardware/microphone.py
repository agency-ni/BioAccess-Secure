"""
Service de capture vocale par microphone
Enregistrement WAV, encodage base64, et envoi au backend
"""

import sounddevice
import wave
import io
import base64
import logging
import numpy as np
from typing import Optional
from config import (
    VOICE_CAPTURE_DURATION, SAMPLE_RATE, AUDIO_CHANNELS,
    MICROPHONE_INDEX, LOG_LEVEL
)

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

class MicrophoneService:
    """
    Service de capture vocale avec sounddevice
    Enregistre WAV et encode en base64
    """
    
    CHUNK = 1024  # Taille frame sounddevice
    FORMAT = sounddevice.paInt16  # Format audio 16-bit
    
    def __init__(self, duration=VOICE_CAPTURE_DURATION, sample_rate=SAMPLE_RATE,
                 channels=AUDIO_CHANNELS, microphone_index=MICROPHONE_INDEX):
        """
        Initialise le service de capture vocale
        
        Args:
            duration: Durée d'enregistrement en secondes
            sample_rate: Taux d'échantillonnage (Hz)
            channels: Nombre de canaux (1=mono, 2=stéréo)
            microphone_index: Index du microphone (-1 = défaut)
        """
        self.duration = duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.microphone_index = microphone_index
        self.audio_interface = None
        self.audio_frames = []
        
        logger.info(f"MicrophoneService initialisé - durée: {duration}s, SR: {sample_rate}Hz")
    
    def list_audio_devices(self):
        """
        Liste tous les périphériques audio disponibles
        Utile pour trouver l'index du microphone
        
        Returns:
            dict: Liste des périphériques avec index et noms
        """
        try:
            audio = sounddevice.sounddevice()
            devices = {}
            
            for i in range(audio.get_device_count()):
                device_info = audio.get_device_info_by_index(i)
                devices[i] = {
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'sample_rate': int(device_info['defaultSampleRate'])
                }
            
            audio.terminate()
            return devices
        except Exception as e:
            logger.error(f"Erreur listage périphériques: {e}")
            return {}
    
    def capture_voice(self) -> Optional[str]:
        """
        Enregistre la voix pendant VOICE_CAPTURE_DURATION secondes
        Retourne l'audio encodé en base64
        
        Returns:
            str: Données audio base64 ou None en cas d'erreur
        """
        try:
            self.audio_interface = sounddevice.sounddevice()
            
            # Ouvrir stream audio
            stream = self.audio_interface.open(
                format=self.FORMAT,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=None if self.microphone_index == -1 else self.microphone_index,
                frames_per_buffer=self.CHUNK
            )
            
            logger.info(f"Enregistrement vocal ({self.duration}s)...")
            
            self.audio_frames = []
            frames_to_record = int(self.sample_rate / self.CHUNK * self.duration)
            
            for _ in range(frames_to_record):
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.audio_frames.append(data)
                except Exception as e:
                    logger.warning(f"Erreur lecture frame audio: {e}")
                    continue
            
            logger.info(f"Enregistrement terminé ({len(self.audio_frames)} frames)")
            
            # Fermer stream
            stream.stop_stream()
            stream.close()
            self.audio_interface.terminate()
            
            # Encoder en WAV puis base64
            audio_base64 = self._encode_to_base64()
            return audio_base64
        
        except Exception as e:
            logger.error(f"Erreur capture vocale: {e}")
            return None
    
    def _encode_to_base64(self) -> Optional[str]:
        """
        Encode les frames audio en WAV format base64
        
        Returns:
            str: Audio base64 ou None
        """
        try:
            if not self.audio_frames:
                logger.error("Aucune frame audio à encoder")
                return None
            
            # Créer fichier WAV en mémoire
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio_interface.get_sample_size(self.FORMAT))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(b''.join(self.audio_frames))
            
            # Encoder base64
            wav_buffer.seek(0)
            audio_data = wav_buffer.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            logger.info(f"Audio encodé base64 ({len(audio_base64)} caractères)")
            return audio_base64
        
        except Exception as e:
            logger.error(f"Erreur encodage audio: {e}")
            return None
    
    def get_audio_level(self) -> float:
        """
        Mesure le niveau sonore actuel (décibels RMS)
        Utile pour vérifier la présence de bruit
        
        Returns:
            float: Niveau en décibels RMS
        """
        try:
            if not self.audio_frames:
                return 0.0
            
            # Convertir frames en array numpy
            audio_data = np.frombuffer(
                b''.join(self.audio_frames),
                dtype=np.int16
            )
            
            # Calculer RMS
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Convertir en décibels
            if rms > 0:
                db = 20 * np.log10(rms)
            else:
                db = 0
            
            return round(db, 2)
        
        except Exception as e:
            logger.error(f"Erreur mesure niveau audio: {e}")
            return 0.0
    
    def cleanup(self):
        """
        Nettoie les ressources audio
        """
        try:
            if self.audio_interface:
                self.audio_interface.terminate()
                self.audio_interface = None
            
            self.audio_frames = []
            logger.info("Ressources audio nettoyées")
        except Exception as e:
            logger.error(f"Erreur cleanup audio: {e}")
