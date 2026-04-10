"""
Service d'authentification biométrique avec logging admin
Gère authentification faciale + logs centralisant les erreurs pour l'admin

Architecture:
    - Authentification face recognition
    - Logging détaillé des tentatives
    - Alertes adminpour erreurs
    - Génération rapports
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import cv2
import base64
import io

from core.database import db
from core.errors import AuthenticationError, ValidationError
from models.user import User, UserSession, LoginLog
from models.biometric import TemplateBiometrique, AuthenticationAttempt, BiometricErrorLog
from services.biometric_service import BiometricService
from utils.encryption import EncryptionManager

logger = logging.getLogger(__name__)


@dataclass
class AuthenticationResult:
    """Résultat d'une authentification"""
    success: bool
    user_id: Optional[str] = None
    token: Optional[str] = None
    similarity_score: Optional[float] = None
    message: str = None
    error: str = None
    requires_mfa: bool = False
    timestamp: datetime = None


class BiometricAuthenticationService:
    """
    Service d'authentification biométrique
    Gère validation, logging et alertes admin
    """
    
    FACE_SIMILARITY_THRESHOLD = 0.6
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    
    def __init__(self):
        """Initialise le service d'authentification"""
        self.biometric_service = BiometricService()
        logger.info("BiometricAuthenticationService initialized")
    
    def authenticate_by_face(self,
                            email: str,
                            image_base64: str,
                            client_ip: str = None,
                            client_user_agent: str = None,
                            is_admin: bool = False) -> AuthenticationResult:
        """
        Authentifie un utilisateur par visage
        
        Args:
            email: Email utilisateur
            image_base64: Image captée en base64
            client_ip: Adresse IP client
            client_user_agent: User agent client
            is_admin: True si tentative admin
            
        Returns:
            AuthenticationResult avec token si succès
        """
        timestamp = datetime.now()
        
        try:
            # 1. Valider format image
            try:
                image_bytes = base64.b64decode(image_base64)
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if img is None:
                    raise ValueError("Image invalide")
            except Exception as e:
                logger.warning(f"Image invalide pour {email}: {e}")
                self._log_attempt(
                    email=email,
                    success=False,
                    reason="INVALID_IMAGE",
                    similarity=0,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin
                )
                return AuthenticationResult(
                    success=False,
                    error="Format image invalide",
                    timestamp=timestamp
                )
            
            # 2. Récupérer utilisateur
            user = User.query.filter_by(email=email).first()
            
            if not user:
                logger.warning(f"Tentative avec email inexistant: {email}")
                self._log_attempt(
                    email=email,
                    success=False,
                    reason="USER_NOT_FOUND",
                    similarity=0,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin
                )
                return AuthenticationResult(
                    success=False,
                    error="Utilisateur non trouvé",
                    timestamp=timestamp
                )
            
            # 3. Vérifier compte actif
            if not user.is_active:
                logger.warning(f"Tentative compte désactivé: {email}")
                self._log_attempt(
                    email=email,
                    user_id=user.id,
                    success=False,
                    reason="ACCOUNT_DISABLED",
                    similarity=0,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin
                )
                return AuthenticationResult(
                    success=False,
                    error="Compte désactivé",
                    timestamp=timestamp
                )
            
            # 4. Vérifier verrouillage
            if self._is_account_locked(user.id):
                logger.warning(f"Compte verrouillé après trop d'essais: {email}")
                self._log_attempt(
                    email=email,
                    user_id=user.id,
                    success=False,
                    reason="ACCOUNT_LOCKED",
                    similarity=0,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin
                )
                return AuthenticationResult(
                    success=False,
                    error="Compte temporairement verrouillé (trop d'essais)",
                    timestamp=timestamp
                )
            
            # 5. Extraire encoding de l'image
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            provided_encoding, quality, faces_count = self.biometric_service.extract_face_features(
                rgb_img
            )
            
            if provided_encoding is None:
                logger.warning(f"Aucun visage détecté pour {email}")
                self._log_attempt(
                    email=email,
                    user_id=user.id,
                    success=False,
                    reason="NO_FACE_DETECTED",
                    similarity=0,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin,
                    alert_admin=True,
                    alert_reason="Tentative sans visage valide"
                )
                return AuthenticationResult(
                    success=False,
                    error="Aucun visage détecté dans l'image",
                    timestamp=timestamp
                )
            
            # 6. Récupérer templates utilisateur
            templates = TemplateBiometrique.query.filter_by(
                user_id=user.id,
                type_biometrique='FACE'
            ).all()
            
            if not templates:
                logger.error(f"Aucun template pour utilisateur: {email}")
                self._log_attempt(
                    email=email,
                    user_id=user.id,
                    success=False,
                    reason="NO_ENROLLED_FACES",
                    similarity=0,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin
                )
                return AuthenticationResult(
                    success=False,
                    error="Utilisateur non enregistré pour authentification faciale",
                    timestamp=timestamp
                )
            
            # 7. Vérifier contre templates
            best_similarity = 0
            matched_template = None
            
            for template in templates:
                stored_encoding = np.array(template.template_data)
                distance = np.linalg.norm(stored_encoding - provided_encoding)
                
                # Convertir distance en similarité (0-1)
                similarity = max(0, 1 - (distance / 2))
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    if similarity > self.FACE_SIMILARITY_THRESHOLD:
                        matched_template = template
            
            # 8. Résultat matching
            if not matched_template or best_similarity <= self.FACE_SIMILARITY_THRESHOLD:
                logger.warning(
                    f"Reconnaissance faciale échouée pour {email}: "
                    f"similarité={best_similarity:.3f}"
                )
                self._log_attempt(
                    email=email,
                    user_id=user.id,
                    success=False,
                    reason="FACE_MISMATCH",
                    similarity=best_similarity,
                    ip_address=client_ip,
                    user_agent=client_user_agent,
                    is_admin=is_admin,
                    alert_admin=True,
                    alert_reason=f"Tentative reconnaissance échouée (similitude: {best_similarity:.1%})"
                )
                
                # Incrémenter compteur échecs
                self._increment_failed_attempts(user.id)
                
                return AuthenticationResult(
                    success=False,
                    error="Reconnaissance faciale échouée",
                    similarity_score=best_similarity,
                    timestamp=timestamp
                )
            
            # 9. Authentification réussie!
            logger.info(
                f"Authentification réussie par visage: {email} "
                f"(similarité: {best_similarity:.3f})"
            )
            
            # Mettre à jour template
            matched_template.date_derniere_utilisation = datetime.now()
            db.session.add(matched_template)
            
            # Créer session
            token = self._generate_session_token(user.id)
            session = UserSession(
                user_id=user.id,
                token_type='bearer',
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24),
                ip_address=client_ip,
                user_agent=client_user_agent,
                auth_method='FACE'
            )
            db.session.add(session)
            
            # Logger succès
            self._log_attempt(
                email=email,
                user_id=user.id,
                success=True,
                reason="MATCH_SUCCESS",
                similarity=best_similarity,
                ip_address=client_ip,
                user_agent=client_user_agent,
                is_admin=is_admin
            )
            
            # Réinitialiser compteur échecs
            self._reset_failed_attempts(user.id)
            
            db.session.commit()
            
            return AuthenticationResult(
                success=True,
                user_id=user.id,
                token=token,
                similarity_score=best_similarity,
                message=f"Authentification réussie (similarité: {best_similarity:.0%})",
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Erreur authentification: {e}", exc_info=True)
            db.session.rollback()
            
            self._log_attempt(
                email=email,
                success=False,
                reason="SYSTEM_ERROR",
                similarity=0,
                ip_address=client_ip,
                user_agent=client_user_agent,
                is_admin=is_admin,
                alert_admin=True,
                alert_reason=f"Erreur système: {str(e)}"
            )
            
            return AuthenticationResult(
                success=False,
                error="Erreur serveur",
                timestamp=timestamp
            )
    
    # ========== LOGGING & ALERTES ==========
    
    def _log_attempt(self,
                    email: str,
                    success: bool,
                    reason: str,
                    similarity: float = 0,
                    user_id: str = None,
                    ip_address: str = None,
                    user_agent: str = None,
                    is_admin: bool = False,
                    alert_admin: bool = False,
                    alert_reason: str = None):
        """
        Enregistre une tentative d'authentification
        
        Args:
            email: Email utilisateur
            success: Succès ou échec
            reason: Raison de l'authentification
            similarity: Score de similarité
            user_id: ID utilisateur
            ip_address: Adresse IP
            user_agent: User agent
            is_admin: Tentative admin
            alert_admin: Générer alerte admin
            alert_reason: Raison de l'alerte
        """
        try:
            attempt = AuthenticationAttempt(
                email=email,
                user_id=user_id,
                success=success,
                reason=reason,
                similarity_score=similarity,
                ip_address=ip_address,
                user_agent=user_agent,
                is_admin_attempt=is_admin,
                timestamp=datetime.now()
            )
            
            db.session.add(attempt)
            
            # Créer alerte admin si nécessaire
            if alert_admin:
                self._create_admin_alert(
                    user_email=email,
                    attempt_type="BIOMETRIC_AUTH_FAILED",
                    reason=alert_reason or reason,
                    details={
                        'email': email,
                        'user_id': user_id,
                        'reason': reason,
                        'similarity': similarity,
                        'ip_address': ip_address,
                        'is_admin': is_admin
                    }
                )
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Erreur logging attempt: {e}")
            db.session.rollback()
    
    def _create_admin_alert(self,
                           user_email: str,
                           attempt_type: str,
                           reason: str,
                           details: Dict = None):
        """
        Crée une alerte pour l'administrateur
        Enregistre aussi un log d'erreur biométrique
        
        Args:
            user_email: Email utilisateur impliqué
            attempt_type: Type d'alerte
            reason: Raison
            details: Détails additionnels
        """
        try:
            # Map attempt type to error type
            error_type_map = {
                'NO_FACE_DETECTED': 'NO_FACE_DETECTED',
                'FACE_MISMATCH': 'FACE_MISMATCH',
                'INVALID_IMAGE': 'INVALID_IMAGE',
                'USER_NOT_FOUND': 'USER_NOT_FOUND',
                'ACCOUNT_DISABLED': 'ACCOUNT_DISABLED',
                'ACCOUNT_LOCKED': 'ACCOUNT_LOCKED',
                'SYSTEM_ERROR': 'SYSTEM_ERROR'
            }
            
            error_type = error_type_map.get(attempt_type, 'BIOMETRIC_AUTH_ERROR')
            severity_map = {'CRITICAL': 9, 'ERROR': 7, 'WARNING': 5, 'INFO': 2}
            severity = severity_map.get(details.get('severity', 'ERROR') if details else 'ERROR', 5)
            
            # Créer log d'erreur biométrique
            error_log = BiometricErrorLog(
                error_type=error_type,
                error_message=reason,
                user_email=user_email,
                auth_type=details.get('auth_type', 'unknown') if details else 'unknown',
                client_info=details.get('client_info', {}) if details else {},
                severity=severity,
                resolved=False,
                timestamp=datetime.now()
            )
            
            db.session.add(error_log)
            
            # Optionally create alert for admin dashboard
            # (can implement as separate Alert model/table later)
            
            db.session.commit()
            
            logger.warning(f"Erreur biométrique enregistrée: {error_type} pour {user_email}")
            
        except Exception as e:
            logger.error(f"Erreur création alerte: {e}")
            db.session.rollback()
    
    # ========== GESTION VERROUILLAGE ==========
    
    def _is_account_locked(self, user_id: str) -> bool:
        """Vérifie si compte est verrouillé après trop d'échecs"""
        try:
            cutoff = datetime.now() - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            
            failed_count = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.user_id == user_id,
                AuthenticationAttempt.success == False,
                AuthenticationAttempt.timestamp > cutoff
            ).count()
            
            return failed_count >= self.MAX_FAILED_ATTEMPTS
            
        except Exception as e:
            logger.error(f"Erreur vérification verrouillage: {e}")
            return False
    
    def _increment_failed_attempts(self, user_id: str):
        """Incrémente compteur d'échecs"""
        try:
            # LoggerErreur supplémentaire après N échecs
            cutoff = datetime.now() - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            
            failed_count = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.user_id == user_id,
                AuthenticationAttempt.success == False,
                AuthenticationAttempt.timestamp > cutoff
            ).count()
            
            if failed_count == self.MAX_FAILED_ATTEMPTS:
                logger.warning(f"Compte verrouillé après {self.MAX_FAILED_ATTEMPTS} échecs: {user_id}")
                self._create_admin_alert(
                    user_email=User.query.get(user_id).email if user_id else "unknown",
                    attempt_type="ACCOUNT_LOCKED",
                    reason=f"Trop de tentatives échouées ({self.MAX_FAILED_ATTEMPTS})"
                )
        except Exception as e:
            logger.error(f"Erreur incrémentation attempts: {e}")
    
    def _reset_failed_attempts(self, user_id: str):
        """Réinitialise le compteur d'échecs après succès"""
        try:
            cutoff = datetime.now() - timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)
            
            # Supprimer anciennes tentatives échouées
            AuthenticationAttempt.query.filter(
                AuthenticationAttempt.user_id == user_id,
                AuthenticationAttempt.success == False,
                AuthenticationAttempt.timestamp > cutoff
            ).delete()
            
            db.session.commit()
        except Exception as e:
            logger.error(f"Erreur reset attempts: {e}")
            db.session.rollback()
    
    # ========== UTILITAIRES ==========
    
    def _generate_session_token(self, user_id: str) -> str:
        """Génère un token JWT pour la session"""
        import jwt
        from config import config_by_name
        import os
        
        config = config_by_name[os.getenv('FLASK_ENV', 'development')]
        
        payload = {
            'user_id': user_id,
            'iat': datetime.now(),
            'exp': datetime.now() + timedelta(hours=24),
            'type': 'access'
        }
        
        token = jwt.encode(
            payload,
            config.SECRET_KEY,
            algorithm='HS256'
        )
        
        return token
    
    def get_authentication_logs(self,
                               user_id: str = None,
                               limit: int = 50,
                               offset: int = 0) -> List[Dict]:
        """
        Récupère les logs d'authentification
        
        Args:
            user_id: Filtrer par utilisateur (optionnel)
            limit: Nombre de résultats
            offset: Pagination
            
        Returns:
            Liste logs formatés
        """
        try:
            query = AuthenticationAttempt.query
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            attempts = query.order_by(
                AuthenticationAttempt.timestamp.desc()
            ).limit(limit).offset(offset).all()
            
            return [
                {
                    'id': str(a.id),
                    'email': a.email,
                    'user_id': a.user_id,
                    'success': a.success,
                    'reason': a.reason,
                    'similarity': a.similarity_score,
                    'ip_address': a.ip_address,
                    'is_admin': a.is_admin_attempt,
                    'timestamp': a.timestamp.isoformat()
                }
                for a in attempts
            ]
        except Exception as e:
            logger.error(f"Erreur récupération logs: {e}")
            return []
    
    def get_admin_dashboard_stats(self) -> Dict:
        """
        Récupère statistiques pour dashboard admin
        
        Returns:
            Dict avec stats d'authentification
        """
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = datetime.combine(today, datetime.max.time())
            
            total_attempts = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.timestamp.between(start_of_day, end_of_day)
            ).count()
            
            successful = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.timestamp.between(start_of_day, end_of_day),
                AuthenticationAttempt.success == True
            ).count()
            
            failed = total_attempts - successful
            
            # Erreurs critiques
            critical_errors = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.timestamp.between(start_of_day, end_of_day),
                AuthenticationAttempt.reason.in(['NO_FACE_DETECTED', 'SYSTEM_ERROR'])
            ).count()
            
            return {
                'total_attempts': total_attempts,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total_attempts * 100) if total_attempts > 0 else 0,
                'critical_errors': critical_errors,
                'date': today.isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur stats dashboard: {e}")
            return {}
