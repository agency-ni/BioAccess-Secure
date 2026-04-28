"""
Service biométrique - Reconnaissance faciale et vocale
"""

import numpy as np
import cv2
#import face_recognition
import pickle
import io
from models.biometric import TemplateBiometrique, TentativeAuth, PhraseAleatoire
from core.database import db
from core.security import SecurityManager
from core.errors import ValidationError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BiometricService:
    """Service pour la biométrie"""
    
    # Seuils de reconnaissance
    FACE_THRESHOLD = 0.6
    VOICE_THRESHOLD = 0.7
    
    @staticmethod
    def process_face_image(image_data, user_id):
        """
        Traite une image faciale et génère un template
        """
        try:
            # Convertir l'image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                raise ValidationError("Image invalide")
            
            # Convertir en RGB
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(rgb_img)
            if not face_locations:
                raise ValidationError("Aucun visage détecté")
            
            # Encoder le visage
            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
            if not face_encodings:
                raise ValidationError("Impossible d'encoder le visage")
            
            # Sérialiser l'encodage
            encoding_bytes = pickle.dumps(face_encodings[0])
            
            # Calculer la qualité (simplifié)
            quality = BiometricService._estimate_face_quality(img)
            
            # Créer le template
            template = TemplateBiometrique(
                type='facial',
                donnees=encoding_bytes,
                utilisateur_id=user_id,
                quality_score=quality
            )
            
            db.session.add(template)
            db.session.commit()
            
            return template
        except Exception as e:
            logger.error(f"Erreur traitement facial: {e}")
            raise ValidationError(f"Erreur traitement facial: {str(e)}")
    
    @staticmethod
    def extract_voice_features(audio_file, phrase_text=None):
        """
        Extrait les caractéristiques vocales d'un fichier audio
        Retourne un embedding 128-dimensionnel
        
        Args:
            audio_file: BytesIO object avec données WAV/MP3
            phrase_text: Texte de la phrase prononcée (ignoré pour version simplifiée)
            
        Returns:
            np.array de shape (128,) - embedding vocal
        """
        try:
            import hashlib
            import numpy as np
            from io import BytesIO
            
            # Lire les données audio
            if isinstance(audio_file, BytesIO):
                audio_data = audio_file.getvalue()
            else:
                audio_data = audio_file.read() if hasattr(audio_file, 'read') else audio_file
            
            # En production: utiliser librosa ou audio features extraction
            # Pour maintenant: générer deterministic embedding basé sur audio hash
            audio_hash = hashlib.sha256(audio_data).digest()
            
            # Seed numpy avec le hash pour deterministic embedding
            np.random.seed(int.from_bytes(audio_hash[:4], 'little'))
            
            # Générer embedding 128-dimensionnel (simulé, en prod: vrai MFCC/spectrogramme)
            voice_encoding = np.random.rand(128).astype(np.float32)
            
            # Ajouter du "bruit" basé sur audio length pour plus de variation
            voice_encoding = voice_encoding + (len(audio_data) % 256) / 1000.0
            
            # Normaliser entre 0 et 1
            voice_encoding = np.clip(voice_encoding, 0, 1).astype(np.float32)
            
            logger.info(f"Voice features extracted: shape={voice_encoding.shape}, audio_size={len(audio_data)}")
            return voice_encoding
            
        except Exception as e:
            logger.error(f"Erreur extraction features vocales: {e}")
            return None
    
    @staticmethod
    def process_voice_sample(audio_data, user_id, phrase_text=None):
        """
        Traite un échantillon vocal (DEPRECATED - utiliser extract_voice_features)
        """
        try:
            import hashlib
            import numpy as np
            
            # Créer un hash de l'audio comme template (simplifié)
            audio_hash = hashlib.sha256(audio_data).digest()
            
            # Convertir en vecteur (simulé)
            np.random.seed(int.from_bytes(audio_hash[:4], 'little'))
            voice_vector = np.random.rand(128).astype(np.float32)
            
            encoding_bytes = pickle.dumps(voice_vector)
            
            # Créer le template
            template = TemplateBiometrique(
                type='vocal',
                donnees=encoding_bytes,
                utilisateur_id=user_id,
                quality_score=0.85  # Simulé
            )
            
            db.session.add(template)
            db.session.commit()
            
            return template
        except Exception as e:
            logger.error(f"Erreur traitement vocal: {e}")
            raise ValidationError(f"Erreur traitement vocal: {str(e)}")
    
    @staticmethod
    def verify_face(template_id, image_data):
        """
        Vérifie un visage contre un template
        """
        template = TemplateBiometrique.query.get(template_id)
        if not template or template.type != 'facial':
            return False, 0.0, "Template invalide"
        
        try:
            # Charger le template
            known_encoding = pickle.loads(template.donnees)
            
            # Traiter la nouvelle image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Détecter le visage
            face_locations = face_recognition.face_locations(rgb_img)
            if not face_locations:
                return False, 0.0, "Aucun visage détecté"
            
            # Encoder
            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
            if not face_encodings:
                return False, 0.0, "Impossible d'encoder"
            
            # Comparer
            distance = face_recognition.face_distance([known_encoding], face_encodings[0])[0]
            similarity = 1 - distance
            
            is_match = distance < BiometricService.FACE_THRESHOLD
            
            return is_match, float(similarity), None
        except Exception as e:
            logger.error(f"Erreur vérification faciale: {e}")
            return False, 0.0, str(e)
    
    @staticmethod
    def verify_voice(template_id, audio_data, expected_phrase=None):
        """
        Vérifie un échantillon vocal
        """
        template = TemplateBiometrique.query.get(template_id)
        if not template or template.type != 'vocal':
            return False, 0.0, "Template invalide"
        
        try:
            # Version simplifiée
            # En production, utiliser un vrai modèle de vérification vocale
            
            # Simuler une vérification
            import hashlib
            import numpy as np
            
            # Calculer un hash de l'audio
            audio_hash = hashlib.sha256(audio_data).hexdigest()
            
            # Simuler un score basé sur le hash
            np.random.seed(int(audio_hash[:4], 16))
            similarity = np.random.uniform(0.5, 0.95)
            
            is_match = similarity > BiometricService.VOICE_THRESHOLD
            
            return is_match, float(similarity), None
        except Exception as e:
            logger.error(f"Erreur vérification vocale: {e}")
            return False, 0.0, str(e)
    
    @staticmethod
    def verify_liveness(frames):
        """
        Détection de vivant (anti-spoofing)
        Vérifie les clignements, micro-mouvements
        """
        if len(frames) < 10:
            return False, "Pas assez d'images"
        
        try:
            # Version simplifiée
            # En production, utiliser un vrai modèle de détection de vivant
            
            # Simuler la détection de clignement
            import random
            has_blink = random.random() > 0.3
            
            return has_blink, None
        except Exception as e:
            logger.error(f"Erreur détection vivant: {e}")
            return False, str(e)
    
    @staticmethod
    def authenticate(user_id, face_image=None, voice_audio=None, phrase=None, ip_address=None):
        """
        Authentification complète (poste de travail)
        """
        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur inconnu"
        
        # Récupérer les templates
        templates = TemplateBiometrique.query.filter_by(
            utilisateur_id=user_id,
            is_active=True
        ).all()
        
        facial_template = next((t for t in templates if t.type == 'facial'), None)
        vocal_template = next((t for t in templates if t.type == 'vocal'), None)
        
        start_time = datetime.utcnow()
        face_ok = False
        voice_ok = False
        raison = None
        face_score = 0
        voice_score = 0
        
        # Mode adaptatif
        if face_image and facial_template:
            face_ok, face_score, err = BiometricService.verify_face(
                facial_template.id, face_image
            )
            if err:
                raison = err
        
        if voice_audio and vocal_template and phrase:
            voice_ok, voice_score, err = BiometricService.verify_voice(
                vocal_template.id, voice_audio, phrase
            )
            if err:
                raison = err
        
        # Décision
        final_status = False
        if face_image and facial_template:
            final_status = face_ok
        elif voice_audio and vocal_template:
            final_status = voice_ok
        else:
            raison = "Mode d'authentification non supporté"
        
        # Calculer le temps
        end_time = datetime.utcnow()
        temps_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Journaliser la tentative
        tentative = TentativeAuth(
            date_heure=start_time,
            etape='combine' if (face_image and voice_audio) else 'simple',
            resultat='succes' if final_status else 'echec',
            raison_echec=raison if not final_status else None,
            adresse_ip=ip_address,
            utilisateur_id=user_id,
            template_id=facial_template.id if facial_template else None,
            phrase_id=phrase.id if isinstance(phrase, PhraseAleatoire) else None,
            score_similarite=max(face_score, voice_score),
            temps_traitement_ms=temps_ms
        )
        tentative.journaliser()
        
        return final_status, raison
    
    @staticmethod
    def _estimate_face_quality(image):
        """Estime la qualité d'une image faciale"""
        # Version simplifiée
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Variance de Laplacien (neteté)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Normaliser
        quality = min(laplacian_var / 500, 1.0)
        
        return round(quality, 2)