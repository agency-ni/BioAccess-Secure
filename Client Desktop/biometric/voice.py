"""
Module d'enregistrement et traitement audio
Utilise sounddevice pour l'enregistrement
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy import signal
import base64
import io
import logging
from typing import Optional, Tuple, Dict, List
from config import AUDIO_DURATION, AUDIO_SAMPLE_RATE

logger = logging.getLogger(__name__)


class MicrophoneAccessError(Exception):
    """Exception levée quand l'accès au microphone est refusé"""
    pass


class VoiceRecorder:
    """Gestionnaire d'enregistrement audio"""

    def __init__(self, sample_rate: int = AUDIO_SAMPLE_RATE, duration: int = AUDIO_DURATION):
        """
        Initialiser le recorder
        
        Args:
            sample_rate: Fréquence d'échantillonnage (Hz)
            duration: Durée par défaut (secondes)
        """
        self.sample_rate = sample_rate
        self.duration = duration
        self.audio_data = None
        self.selected_device = None
        
        # Vérifier la disponibilité des périphériques
        try:
            devices = sd.query_devices()
            logger.info(f"✓ Périphériques audio détectés: {len(devices)}")
            self._list_input_devices()
        except Exception as e:
            logger.error(f"Erreur lors de la détection des périphériques: {e}")
            raise MicrophoneAccessError(f"Impossible de détecter les périphériques audio: {e}")
    
    def _list_input_devices(self):
        """Lister les périphériques d'entrée disponibles"""
        try:
            devices = sd.query_devices()
            logger.info("Périphériques d'entrée audio disponibles:")
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    logger.info(f"  {i}: {device['name']} "
                              f"({device['max_input_channels']} canaux)")
        except Exception as e:
            logger.warning(f"Impossible de lister les périphériques: {e}")

    def is_available(self) -> bool:
        """Vérifier si l'enregistrement audio est disponible"""
        try:
            devices = sd.query_devices()
            # Vérifier s'il y a au moins un périphérique d'entrée
            for device in devices:
                if device['max_input_channels'] > 0:
                    return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            return False
    
    def get_input_devices(self) -> List[Dict]:
        """
        Obtenir la liste des périphériques d'entrée
        
        Returns:
            List de dicts avec les informations des périphériques
        """
        devices_list = []
        try:
            devices = sd.query_devices()
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    devices_list.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des périphériques: {e}")
        
        return devices_list
    
    def set_device(self, device_id: int) -> bool:
        """
        Sélectionner un périphérique d'entrée
        
        Args:
            device_id: ID du périphérique
            
        Returns:
            True si succès
        """
        try:
            device = sd.query_devices(device_id)
            if device['max_input_channels'] > 0:
                self.selected_device = device_id
                logger.info(f"✓ Périphérique sélectionné: {device['name']}")
                return True
            else:
                logger.error(f"Périphérique {device_id} n'a pas d'entrée audio")
                return False
        except Exception as e:
            logger.error(f"Erreur lors de la sélection du périphérique: {e}")
            return False

    def is_available(self) -> bool:
        """Vérifier si l'enregistrement audio est disponible"""
        try:
            sd.query_devices()
            return True
        except:
            return False

    def record_audio(self, duration: Optional[int] = None, channels: int = 1, 
                     device_id: Optional[int] = None) -> Optional[np.ndarray]:
        """
        Enregistrer de l'audio
        
        Args:
            duration: Durée en secondes (None = utiliser la valeur par défaut)
            channels: Nombre de canaux (1=mono, 2=stéréo)
            device_id: ID du périphérique (None = utiliser le défaut)
            
        Returns:
            Audio data (numpy array) ou None si erreur
            
        Raises:
            MicrophoneAccessError: Si le microphone n'est pas accessible
        """
        duration = duration or self.duration
        
        if duration <= 0 or duration > 60:
            logger.error(f"Durée invalide: {duration}s")
            raise ValueError(f"Durée doit être entre 0 et 60 secondes, reçu: {duration}")
        
        try:
            logger.info(f"Enregistrement en cours ({duration}s)...")
            
            # Enregistrer l'audio
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=channels,
                dtype=np.float32,
                blocksize=2048,
                device=device_id if device_id is not None else self.selected_device
            )
            
            # Attendre la fin de l'enregistrement
            sd.wait()
            
            # Normaliser
            self.audio_data = audio
            
            logger.info(f"✓ Enregistrement terminé ({len(audio)} samples)")
            return audio
        
        except PermissionError as e:
            logger.error(f"Permission refusée: {e}")
            raise MicrophoneAccessError(f"Accès au microphone refusé: {e}")
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement: {e}")
            raise MicrophoneAccessError(f"Erreur d'enregistrement: {e}")
    
    def try_alternative_devices(self, duration: int = 2) -> Optional[np.ndarray]:
        """
        Essayer différents microphones
        
        Args:
            duration: Durée de test en secondes
            
        Returns:
            Audio si succès
        """
        logger.info("Recherche de microphone alternatif...")
        
        devices = self.get_input_devices()
        
        if not devices:
            logger.error("Aucun périphérique d'entrée trouvé")
            return None
        
        for device in devices:
            try:
                logger.info(f"Test du périphérique: {device['name']}")
                audio = self.record_audio(duration=duration, device_id=device['id'])
                if audio is not None and len(audio) > 0:
                    logger.info(f"✓ Microphone trouvé: {device['name']}")
                    self.selected_device = device['id']
                    return audio
            except Exception as e:
                logger.warning(f"Échec avec {device['name']}: {e}")
                continue
        
        logger.error("Aucun microphone alternatif fonctionnel trouvé")
        return None

    @staticmethod
    def record_with_callback(duration: int = AUDIO_DURATION, 
                            sample_rate: int = AUDIO_SAMPLE_RATE,
                            progress_callback=None) -> Optional[np.ndarray]:
        """
        Enregistrement avec callback de progression
        
        Args:
            duration: Durée (secondes)
            sample_rate: Fréquence d'échantillonnage
            progress_callback: Fonction appelée avec (frames_recorded, total_frames)
            
        Returns:
            Audio data ou None
        """
        try:
            total_frames = int(duration * sample_rate)
            audio_list = []
            chunk_size = sample_rate // 10  # Chunks de 0.1s
            
            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Status audio: {status}")
                audio_list.extend(indata[:, 0].copy())
                
                if progress_callback and len(audio_list) % chunk_size == 0:
                    progress_callback(len(audio_list), total_frames)
            
            logger.info(f"Enregistrement avec callback ({duration}s)...")
            
            with sd.InputStream(
                channels=1,
                samplerate=sample_rate,
                blocksize=chunk_size,
                callback=audio_callback
            ):
                sd.sleep(int(duration * 1000))  # Attendre en ms
            
            audio_data = np.array(audio_list, dtype=np.float32)
            logger.info(f"✓ Enregistrement terminé")
            return audio_data
        
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement: {e}")
            return None

    @staticmethod
    def audio_to_wav_base64(audio: np.ndarray, sample_rate: int = AUDIO_SAMPLE_RATE) -> str:
        """
        Convertir audio en WAV et encoder en base64
        
        Args:
            audio: Audio data (numpy array)
            sample_rate: Fréquence d'échantillonnage
            
        Returns:
            Chaîne base64
        """
        try:
            # Créer un buffer en mémoire
            buffer = io.BytesIO()
            
            # Écrire en WAV
            sf.write(buffer, audio, sample_rate, format='WAV')
            
            # Convertir en base64
            buffer.seek(0)
            wav_data = buffer.read()
            audio_base64 = base64.b64encode(wav_data).decode('utf-8')
            
            logger.info(f"✓ Audio converti en base64 ({len(audio_base64)} chars)")
            return audio_base64
        
        except Exception as e:
            logger.error(f"Erreur lors de la conversion: {e}")
            return ""

    @staticmethod
    def wav_base64_to_audio(data: str, sample_rate: int = AUDIO_SAMPLE_RATE) -> Optional[np.ndarray]:
        """
        Décoder audio depuis base64
        
        Args:
            data: Chaîne base64
            sample_rate: Fréquence d'échantillonnage attendue
            
        Returns:
            Audio data ou None
        """
        try:
            # Décoder depuis base64
            wav_data = base64.b64decode(data)
            
            # Créer un buffer et lire
            buffer = io.BytesIO(wav_data)
            audio, sr = sf.read(buffer)
            
            # Rééchantillonner si nécessaire
            if sr != sample_rate:
                num_samples = int(len(audio) * sample_rate / sr)
                audio = signal.resample(audio, num_samples)
            
            return audio.astype(np.float32)
        
        except Exception as e:
            logger.error(f"Erreur lors du décodage: {e}")
            return None

    @staticmethod
    def extract_features(audio: np.ndarray, sample_rate: int = AUDIO_SAMPLE_RATE) -> dict:
        """
        Extraire les caractéristiques audio (zéro-crossing, énergie, etc.)
        
        Args:
            audio: Audio data
            sample_rate: Fréquence d'échantillonnage
            
        Returns:
            Dictionnaire de caractéristiques
        """
        try:
            features = {}
            
            # RMS Energy
            features['energy'] = float(np.sqrt(np.mean(audio ** 2)))
            
            # Zero crossing rate
            zero_crossings = np.sum(np.abs(np.diff(np.sign(audio)))) / 2
            features['zcr'] = float(zero_crossings / len(audio))
            
            # Spectral centroid (approximé)
            fft = np.abs(np.fft.fft(audio))
            freqs = np.fft.fftfreq(len(audio), 1 / sample_rate)
            features['spectral_centroid'] = float(np.average(freqs[:len(freqs)//2], 
                                                            weights=fft[:len(fft)//2]))
            
            # MFCC (simplifié - moyenne des énergies par bande de fréquence)
            n_mfcc = 13
            mel_freqs = np.linspace(0, sample_rate // 2, n_mfcc)
            features['mfcc_mean'] = float(np.mean(fft[:n_mfcc]))
            
            # Durée
            features['duration'] = float(len(audio) / sample_rate)
            
            return features
        
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction: {e}")
            return {}

    @staticmethod
    def get_available_devices() -> list:
        """
        Lister les périphériques audio disponibles
        
        Returns:
            Liste de tuples (id, name)
        """
        try:
            devices = sd.query_devices()
            available = []
            
            for i, device in enumerate(devices):
                if device.get('max_input_channels', 0) > 0:
                    available.append((i, device.get('name', f'Device {i}')))
            
            return available
        
        except:
            return []

    @staticmethod
    def play_audio(audio: np.ndarray, sample_rate: int = AUDIO_SAMPLE_RATE):
        """
        Jouer un audio (utile pour les tests)
        
        Args:
            audio: Audio data
            sample_rate: Fréquence d'échantillonnage
        """
        try:
            sd.play(audio, sample_rate)
            sd.wait()
            logger.info("✓ Audio joué")
        except Exception as e:
            logger.error(f"Erreur lors de la lecture: {e}")


# Instance globale
voice_recorder = VoiceRecorder()
