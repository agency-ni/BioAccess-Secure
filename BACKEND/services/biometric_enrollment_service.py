"""
Service d'enregistrement biométrique - Deux modes (upload + live)
Gère l'enregistrement des utilisateurs avec photo upload ou capture live

Architecture:
    - Mode upload: photo depuis fichier
    - Mode live: capture directe depuis caméra
    - Validation faciale + qualité
    - Stockage persistant BD
"""

import base64
import os
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import cv2
from PIL import Image

from core.database import db
from core.errors import ValidationError, AuthenticationError, ConflictError
from models.biometric import TemplateBiometrique
from models.user import User
from services.biometric_service import BiometricService

logger = logging.getLogger(__name__)


@dataclass
class EnrollmentResult:
    """Résultat d'un enregistrement"""
    success: bool
    template_id: Optional[str] = None
    user_id: Optional[str] = None
    quality_score: Optional[float] = None
    templates_count: Optional[int] = None
    message: str = None
    error: str = None


class BiometricEnrollmentService:
    """
    Service d'enregistrement biométrique
    Supporte deux modes: upload et live
    """
    
    MIN_FACES_REQUIRED = 1  # Minimum de visages pour enregistrement complet
    MAX_FACES_PER_USER = 10  # Maximum de templates par utilisateur
    FACE_THRESHOLD = 0.6  # Seuil de similarité
    MIN_QUALITY_SCORE = 0.4  # Score qualité minimum
    
    def __init__(self):
        """Initialise le service d'enregistrement"""
        self.biometric_service = BiometricService()
        logger.info("BiometricEnrollmentService initialized")
    
    # ========== MODE UPLOAD ==========
    
    def enroll_face_from_upload(self,
                                user_id: str,
                                image_data: bytes,
                                label: str = None,
                                check_duplicate: bool = True) -> EnrollmentResult:
        """
        Enregistre un visage à partir d'une image upload
        
        Args:
            user_id: ID utilisateur
            image_data: Données image brutes (bytes)
            label: Label optionnel
            check_duplicate: Vérifier si autre utilisateur n'a pas ce visage
            
        Returns:
            EnrollmentResult
        """
        try:
            # Valider utilisateur
            user = User.query.get(user_id)
            if not user:
                return EnrollmentResult(
                    success=False,
                    error="Utilisateur non trouvé",
                    user_id=user_id
                )
            
            # Vérifier limite
            existing_count = TemplateBiometrique.query.filter_by(
                user_id=user_id,
                type_biometrique='FACE'
            ).count()
            
            if existing_count >= self.MAX_FACES_PER_USER:
                return EnrollmentResult(
                    success=False,
                    error=f"Limite d'enregistrement atteinte ({self.MAX_FACES_PER_USER} visages max)",
                    user_id=user_id
                )
            
            # Convertir image
            try:
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    return EnrollmentResult(
                        success=False,
                        error="Format image invalide",
                        user_id=user_id
                    )
            except Exception as e:
                logger.error(f"Erreur conversion image: {e}")
                return EnrollmentResult(
                    success=False,
                    error="Erreur traitement image",
                    user_id=user_id
                )
            
            # Traiter et encoder
            result = self._process_face_image(
                img,
                user_id,
                label or f"Visage {existing_count + 1}",
                check_duplicate
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur enregistrement upload: {e}")
            return EnrollmentResult(
                success=False,
                error=str(e),
                user_id=user_id
            )
    
    def enroll_face_from_base64(self,
                                user_id: str,
                                image_base64: str,
                                label: str = None,
                                check_duplicate: bool = True) -> EnrollmentResult:
        """
        Enregistre à partir d'image base64
        
        Args:
            user_id: ID utilisateur
            image_base64: Image en base64
            label: Label optionnel
            check_duplicate: Vérifier duplicatas
            
        Returns:
            EnrollmentResult
        """
        try:
            # Décoder base64
            image_data = base64.b64decode(image_base64)
            return self.enroll_face_from_upload(
                user_id,
                image_data,
                label,
                check_duplicate
            )
        except Exception as e:
            logger.error(f"Erreur décodage base64: {e}")
            return EnrollmentResult(
                success=False,
                error="Base64 invalide",
                user_id=user_id
            )
    
    # ========== MODE LIVE ==========
    
    def enroll_face_from_live(self,
                              user_id: str,
                              image_base64: str,
                              label: str = None) -> EnrollmentResult:
        """
        Enregistre à partir d'une capture live
        (Même traitement qu'upload)
        
        Args:
            user_id: ID utilisateur
            image_base64: Image capturée
            label: Label optionnel
            
        Returns:
            EnrollmentResult
        """
        return self.enroll_face_from_base64(
            user_id,
            image_base64,
            label or "Capture live",
            check_duplicate=True
        )
    
    # ========== MULTI-ENREGISTREMENT ==========
    
    def enroll_multiple_faces(self,
                             user_id: str,
                             images: List[bytes],
                             labels: List[str] = None) -> Dict:
        """
        Enregistre plusieurs visages d'un coup
        
        Args:
            user_id: ID utilisateur
            images: Liste images (bytes)
            labels: Labels optionnels
            
        Returns:
            Dict avec résultats + statistiques
        """
        results = []
        successful = 0
        
        for i, image_data in enumerate(images):
            label = labels[i] if labels and i < len(labels) else f"Visage {i+1}"
            
            result = self.enroll_face_from_upload(
                user_id,
                image_data,
                label,
                check_duplicate=True
            )
            
            results.append({
                'index': i,
                'label': label,
                'success': result.success,
                'quality_score': result.quality_score,
                'error': result.error,
                'template_id': result.template_id
            })
            
            if result.success:
                successful += 1
        
        return {
            'user_id': user_id,
            'total_submitted': len(images),
            'successful': successful,
            'failed': len(images) - successful,
            'results': results,
            'overall_success': successful >= self.MIN_FACES_REQUIRED
        }
    
    # ========== UTILITAIRES INTERNES ==========
    
    def _process_face_image(self,
                            img: np.ndarray,
                            user_id: str,
                            label: str,
                            check_duplicate: bool = True) -> EnrollmentResult:
        """
        Traitement interne d'image faciale
        
        Args:
            img: Image OpenCV
            user_id: ID utilisateur
            label: Label du template
            check_duplicate: Vérifier sur BD
            
        Returns:
            EnrollmentResult
        """
        try:
            # Convertir BGR → RGB
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Utiliser service biométrique existant
            encoding, quality, faces_count = self.biometric_service.extract_face_features(
                rgb_img
            )
            
            if encoding is None:
                return EnrollmentResult(
                    success=False,
                    error="Aucun visage détecté dans l'image",
                    user_id=user_id
                )
            
            # Vérifier qualité
            if quality < self.MIN_QUALITY_SCORE:
                return EnrollmentResult(
                    success=False,
                    error=f"Qualité insuffisante ({quality:.1%}). Minimum: {self.MIN_QUALITY_SCORE:.1%}",
                    user_id=user_id,
                    quality_score=quality
                )
            
            # Vérifier duplicate si demandé
            if check_duplicate:
                duplicate_user = self._check_duplicate_face(encoding)
                if duplicate_user and duplicate_user != user_id:
                    # Log tentative d'enregistrement doublon
                    logger.warning(
                        f"Tentative enregistrement visage dupliqué: "
                        f"user={user_id}, existing_user={duplicate_user}"
                    )
                    return EnrollmentResult(
                        success=False,
                        error="Ce visage est déjà enregistré pour un autre utilisateur",
                        user_id=user_id
                    )
            
            # Créer template BD
            template = TemplateBiometrique(
                user_id=user_id,
                type_biometrique='FACE',
                template_data=encoding.tolist(),
                label=label,
                quality_score=quality,
                date_creation=datetime.now(),
                date_derniere_utilisation=datetime.now()
            )
            
            db.session.add(template)
            db.session.commit()
            
            # Compter total templates
            total_templates = TemplateBiometrique.query.filter_by(
                user_id=user_id,
                type_biometrique='FACE'
            ).count()
            
            logger.info(
                f"Enregistrement facial réussi: user={user_id}, "
                f"quality={quality:.2%}, total_templates={total_templates}"
            )
            
            return EnrollmentResult(
                success=True,
                template_id=str(template.id),
                user_id=user_id,
                quality_score=quality,
                templates_count=total_templates,
                message=f"Visage enregistré avec succès (qualité: {quality:.0%})"
            )
            
        except Exception as e:
            logger.error(f"Erreur traitement facial: {e}")
            db.session.rollback()
            return EnrollmentResult(
                success=False,
                error=f"Erreur traitement: {str(e)}",
                user_id=user_id
            )
    
    def _check_duplicate_face(self, encoding: np.ndarray) -> Optional[str]:
        """
        Vérifie si ce visage existe déjà en BD
        
        Returns:
            user_id si duplicate trouvé, None sinon
        """
        try:
            # Récupérer tous les templates
            templates = TemplateBiometrique.query.filter_by(
                type_biometrique='FACE'
            ).all()
            
            for template in templates:
                stored_encoding = np.array(template.template_data)
                distance = np.linalg.norm(stored_encoding - encoding)
                
                if distance <= self.FACE_THRESHOLD:
                    return template.user_id
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur vérification duplicate: {e}")
            return None
    
    def get_user_templates(self, user_id: str) -> List[Dict]:
        """
        Récupère les templates d'un utilisateur
        
        Args:
            user_id: ID utilisateur
            
        Returns:
            Liste templates avec métadonnées
        """
        try:
            templates = TemplateBiometrique.query.filter_by(
                user_id=user_id,
                type_biometrique='FACE'
            ).all()
            
            return [
                {
                    'id': str(t.id),
                    'label': t.label,
                    'quality_score': t.quality_score,
                    'created': t.date_creation.isoformat(),
                    'last_used': t.date_derniere_utilisation.isoformat() if t.date_derniere_utilisation else None
                }
                for t in templates
            ]
        except Exception as e:
            logger.error(f"Erreur récupération templates: {e}")
            return []
    
    def delete_template(self, user_id: str, template_id: str) -> bool:
        """
        Supprime un template d'un utilisateur
        
        Args:
            user_id: ID utilisateur
            template_id: ID template à supprimer
            
        Returns:
            bool: Success
        """
        try:
            template = TemplateBiometrique.query.filter_by(
                id=template_id,
                user_id=user_id,
                type_biometrique='FACE'
            ).first()
            
            if not template:
                logger.warning(f"Template non trouvé: {template_id}")
                return False
            
            db.session.delete(template)
            db.session.commit()
            
            logger.info(f"Template supprimé: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression template: {e}")
            db.session.rollback()
            return False
    
    def cleanup_old_templates(self, days_old: int = 90) -> int:
        """
        Nettoie les anciens templates non utilisés
        
        Args:
            days_old: Nombre de jours avant suppression
            
        Returns:
            Nombre templates supprimés
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            deleted = TemplateBiometrique.query.filter(
                TemplateBiometrique.type_biometrique == 'FACE',
                TemplateBiometrique.date_derniere_utilisation < cutoff_date
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Nettoyage: {deleted} templates supprimés")
            return deleted
            
        except Exception as e:
            logger.error(f"Erreur nettoyage templates: {e}")
            db.session.rollback()
            return 0
