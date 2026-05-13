"""
Service biométrique - Reconnaissance faciale et vocale
Utilise face_recognition (dlib) pour la faciale, librosa MFCC pour la voix.
"""

import numpy as np
import cv2
import face_recognition
import io
import pickle
import logging
from datetime import datetime

from models.biometric import TemplateBiometrique, TentativeAuth, PhraseAleatoire
from core.database import db
from core.security import SecurityManager
from core.errors import ValidationError

logger = logging.getLogger(__name__)


class BiometricService:
    """Service pour la biométrie — face_recognition + librosa MFCC"""

    # Seuils de reconnaissance
    FACE_THRESHOLD  = 0.55   # Distance face_recognition (< 0.55 = match)
    VOICE_THRESHOLD = 0.70   # Similarité cosinus MFCC (> 0.70 = match)

    # ──────────────────────────────────────────────────────────────
    # FACIAL
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def extract_face_features(rgb_img):
        """
        Détecte et encode le visage dominant d'une image RGB.

        Returns
        -------
        (encoding, quality, faces_count)
            encoding   : np.ndarray(128,) float64  ou  None si aucun visage
            quality    : float 0-1 (netteté Laplacien)
            faces_count: int
        """
        try:
            face_locations = face_recognition.face_locations(rgb_img, model='hog')
            if not face_locations:
                return None, 0.0, 0

            encodings = face_recognition.face_encodings(rgb_img, face_locations)
            if not encodings:
                return None, 0.0, len(face_locations)

            # Qualité sur l'image BGR
            bgr = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2BGR)
            quality = BiometricService._estimate_face_quality(bgr)

            return encodings[0], quality, len(face_locations)

        except Exception as e:
            logger.error(f"extract_face_features: {e}")
            return None, 0.0, 0

    @staticmethod
    def process_face_image(image_data, user_id):
        """
        Décode image_data (bytes JPEG/PNG), encode le visage,
        crée et persiste un TemplateBiometrique FACE.
        """
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValidationError("Image invalide ou format non reconnu")

            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encoding, quality, n_faces = BiometricService.extract_face_features(rgb_img)

            if encoding is None:
                raise ValidationError("Aucun visage détecté dans l'image")

            template = TemplateBiometrique(
                type_biometrique='FACE',
                template_data=encoding.tolist(),
                user_id=user_id,
                quality_score=quality,
                label=f"Enrôlement facial {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            db.session.add(template)
            db.session.commit()
            return template

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"process_face_image: {e}")
            db.session.rollback()
            raise ValidationError(f"Erreur traitement facial : {e}")

    @staticmethod
    def verify_face(template_id, image_data):
        """
        Compare image_data contre le template stocké.

        Returns (is_match: bool, similarity: float, error: str|None)
        """
        template = TemplateBiometrique.query.get(template_id)
        if not template or template.type_biometrique != 'FACE':
            return False, 0.0, "Template facial invalide"

        try:
            known_encoding = np.array(template.template_data)

            nparr   = np.frombuffer(image_data, np.uint8)
            img     = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_img, model='hog')
            if not face_locations:
                return False, 0.0, "Aucun visage détecté"

            encodings = face_recognition.face_encodings(rgb_img, face_locations)
            if not encodings:
                return False, 0.0, "Impossible d'encoder le visage"

            distance   = face_recognition.face_distance([known_encoding], encodings[0])[0]
            similarity = float(max(0.0, 1.0 - distance))
            is_match   = distance < BiometricService.FACE_THRESHOLD

            return is_match, similarity, None

        except Exception as e:
            logger.error(f"verify_face: {e}")
            return False, 0.0, str(e)

    # ──────────────────────────────────────────────────────────────
    # VOCAL
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def extract_voice_features(audio_file, phrase_text=None):
        """
        Extrait un embedding vocal MFCC 80-dim normalisé.

        Parameters
        ----------
        audio_file : BytesIO | bytes | file-like
            Audio brut (webm / ogg / wav / mp3 acceptés par librosa)

        Returns
        -------
        np.ndarray(80,) float32  ou  None si échec
        """
        try:
            import librosa

            # Lire les bytes
            if isinstance(audio_file, io.BytesIO):
                audio_bytes = audio_file.getvalue()
            elif hasattr(audio_file, 'read'):
                audio_bytes = audio_file.read()
            else:
                audio_bytes = bytes(audio_file)

            # Décodage — librosa accepte webm/ogg/wav/mp3 via soundfile/ffmpeg
            y, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)

            if len(y) < sr * 0.3:   # < 300 ms → trop court
                logger.warning("Audio trop court pour MFCC (< 300 ms)")
                return None

            # 40 MFCC coefficients — moyenne temporelle
            mfcc       = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
            mfcc_mean  = np.mean(mfcc, axis=1).astype(np.float32)

            # Delta MFCC — dynamique temporelle
            delta      = librosa.feature.delta(mfcc)
            delta_mean = np.mean(delta, axis=1).astype(np.float32)

            # Embedding 80-dim
            embedding = np.concatenate([mfcc_mean, delta_mean])

            # Normalisation L2
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm

            logger.info(f"MFCC extrait : shape={embedding.shape}, durée={len(y)/sr:.2f}s")
            return embedding

        except Exception as e:
            logger.error(f"extract_voice_features: {e}")
            return None

    @staticmethod
    def compute_voice_quality(y, sr):
        """
        Calcule un score qualité vocal [0, 1] basé sur SNR, VAD et clipping.
        """
        try:
            import librosa
            # VAD: ratio d'énergie active vs totale
            rms = librosa.feature.rms(y=y)[0]
            silence_threshold = np.percentile(rms, 20)
            active_ratio = float(np.mean(rms > silence_threshold))

            # SNR estimé: rapport énergie active / énergie silence
            active_energy = float(np.mean(rms[rms > silence_threshold] ** 2)) if np.any(rms > silence_threshold) else 1e-9
            noise_energy = float(np.mean(rms[rms <= silence_threshold] ** 2)) if np.any(rms <= silence_threshold) else 1e-9
            snr_ratio = min(active_energy / max(noise_energy, 1e-9), 100.0)
            snr_score = min(snr_ratio / 20.0, 1.0)  # normalise: SNR=20 → score=1.0

            # Clipping: proportion d'échantillons saturés (|amplitude| > 0.99)
            clip_ratio = float(np.mean(np.abs(y) > 0.99))
            clip_penalty = max(0.0, 1.0 - clip_ratio * 10)

            # Durée: score plein dès 1 seconde
            duration = len(y) / sr
            duration_score = min(duration, 1.0)

            quality = (0.35 * active_ratio + 0.35 * snr_score + 0.15 * clip_penalty + 0.15 * duration_score)
            return float(np.clip(quality, 0.0, 1.0))
        except Exception as e:
            logger.warning(f"compute_voice_quality: {e}")
            return 0.5

    @staticmethod
    def process_voice_sample(audio_data, user_id, phrase_text=None):
        """
        Encode l'audio, crée et persiste un TemplateBiometrique VOICE.
        Retourne le template ORM (déjà commité).
        """
        try:
            import librosa
            audio_bytes = bytes(audio_data)
            y, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)
            quality_score = BiometricService.compute_voice_quality(y, sr)

            embedding = BiometricService.extract_voice_features(
                io.BytesIO(audio_bytes), phrase_text
            )
            if embedding is None:
                raise ValidationError("Impossible d'extraire les caractéristiques vocales")

            template = TemplateBiometrique(
                type_biometrique='VOICE',
                template_data=embedding.tolist(),
                user_id=user_id,
                quality_score=quality_score,
                label=f"Enrôlement vocal {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            db.session.add(template)
            db.session.commit()
            return template

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"process_voice_sample: {e}")
            db.session.rollback()
            raise ValidationError(f"Erreur traitement vocal : {e}")

    @staticmethod
    def verify_voice(template_id, audio_data, expected_phrase=None):
        """
        Compare audio_data contre le template MFCC stocké.
        Utilise la similarité cosinus.

        Returns (is_match: bool, similarity: float, error: str|None)
        """
        template = TemplateBiometrique.query.get(template_id)
        if not template or template.type_biometrique != 'VOICE':
            return False, 0.0, "Template vocal invalide"

        try:
            stored  = np.array(template.template_data, dtype=np.float32)
            new_emb = BiometricService.extract_voice_features(io.BytesIO(audio_data))

            if new_emb is None:
                return False, 0.0, "Impossible d'extraire les features vocales"

            from scipy.spatial.distance import cosine
            similarity = float(1.0 - cosine(stored, new_emb))
            is_match   = similarity > BiometricService.VOICE_THRESHOLD

            return is_match, similarity, None

        except Exception as e:
            logger.error(f"verify_voice: {e}")
            return False, 0.0, str(e)

    # ──────────────────────────────────────────────────────────────
    # VIVANT (liveness)
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def verify_liveness(liveness_confirmed: bool, ear_min: float = None):
        """
        Valide la détection de vivant transmise par le frontend.

        Parameters
        ----------
        liveness_confirmed : bool
            True si le frontend a détecté un clignement (EAR < 0.22)
        ear_min : float | None
            Valeur minimale d'EAR mesurée pendant la capture

        Returns (is_alive: bool, reason: str|None)
        """
        if not liveness_confirmed:
            return False, "Aucun clignement détecté (liveness échoué)"

        # Si on a la valeur EAR, vérifier qu'elle est plausible
        if ear_min is not None:
            if ear_min > 0.22:
                return False, f"EAR minimum trop élevé ({ear_min:.3f}) — clignement non confirmé"
            if ear_min < 0.01:
                return False, f"EAR anormal ({ear_min:.3f}) — possible spoofing"

        return True, None

    # ──────────────────────────────────────────────────────────────
    # AUTHENTIFICATION COMPLÈTE
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def authenticate(user_id, face_image=None, voice_audio=None, phrase=None,
                     ip_address=None, liveness_confirmed=False, ear_min=None):
        """
        Authentification multimodale.
        """
        from models.user import User
        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur inconnu"

        templates = TemplateBiometrique.query.filter_by(
            user_id=user_id, is_active=True
        ).all()

        facial_template = next((t for t in templates if t.type_biometrique == 'FACE'), None)
        vocal_template  = next((t for t in templates if t.type_biometrique == 'VOICE'), None)

        start_time = datetime.utcnow()
        face_ok = voice_ok = False
        raison = None
        face_score = voice_score = 0.0

        # Vérification liveness avant tout
        if face_image:
            alive, liveness_err = BiometricService.verify_liveness(liveness_confirmed, ear_min)
            if not alive:
                raison = liveness_err
                BiometricService._log_tentative(
                    user_id, 'facial', 'echec', raison, ip_address,
                    facial_template.id if facial_template else None, 0.0,
                    int((datetime.utcnow() - start_time).total_seconds() * 1000)
                )
                return False, raison

        if face_image and facial_template:
            face_ok, face_score, err = BiometricService.verify_face(
                facial_template.id, face_image
            )
            if err:
                raison = err

        if voice_audio and vocal_template:
            voice_ok, voice_score, err = BiometricService.verify_voice(
                vocal_template.id, voice_audio,
                phrase.texte if isinstance(phrase, PhraseAleatoire) else phrase
            )
            if err:
                raison = err

        # Décision finale
        if face_image and facial_template and voice_audio and vocal_template:
            final_status = face_ok and voice_ok
        elif face_image and facial_template:
            final_status = face_ok
        elif voice_audio and vocal_template:
            final_status = voice_ok
        else:
            raison = "Aucun template enrôlé ou données manquantes"
            final_status = False

        temps_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        etape    = 'combine' if (face_image and voice_audio) else ('facial' if face_image else 'vocal')

        BiometricService._log_tentative(
            user_id, etape,
            'succes' if final_status else 'echec',
            None if final_status else raison,
            ip_address,
            facial_template.id if facial_template else None,
            max(face_score, voice_score),
            temps_ms,
            phrase.id if isinstance(phrase, PhraseAleatoire) else None
        )

        return final_status, raison

    # ──────────────────────────────────────────────────────────────
    # UTILITAIRES INTERNES
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _estimate_face_quality(bgr_image):
        """Score de netteté par variance du Laplacien (0-1)."""
        gray          = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(min(laplacian_var / 500.0, 1.0))

    @staticmethod
    def _log_tentative(user_id, etape, resultat, raison, ip, template_id,
                       score, temps_ms, phrase_id=None):
        """Journalise une tentative dans tentatives_auth."""
        try:
            tentative = TentativeAuth(
                etape=etape,
                resultat=resultat,
                raison_echec=raison,
                adresse_ip=ip,
                user_id=user_id,
                template_id=template_id,
                phrase_id=phrase_id,
                score_similarite=score,
                temps_traitement_ms=temps_ms
            )
            db.session.add(tentative)
            db.session.commit()
        except Exception as e:
            logger.error(f"_log_tentative: {e}")
            db.session.rollback()
