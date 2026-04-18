"""
Exemple d'intégration: Authentification + Vérification d'accès
Montre le flux complet pour le client desktop

Flux:
  1. Authentification faciale (verify_face)
  2. Authentification vocale (verify_voice)
  3. Vérification d'accès (check_access) ← NOUVEAU
  4. Si accès bloqué -> afficher alerte et bloquer
  5. Si accès autorisé -> déverrouiller le poste
"""

import logging
from typing import Optional
from access_verification import AccessVerifier

logger = logging.getLogger(__name__)


class BiometricAuthenticationWithAccessControl:
    """
    Classe d'authentification biométrique avec vérification d'accès
    Intègre le client API et la vérification des alertes de sécurité
    """
    
    def __init__(self, api_client, tkinter_app=None):
        """
        Initialise l'authentification avec contrôle d'accès
        
        Args:
            api_client: Instance BioAccessAPIClient
            tkinter_app: Instance de l'application Tkinter (optionnel)
        """
        self.api_client = api_client
        self.access_verifier = AccessVerifier(api_client)
        self.app = tkinter_app
        self.logger = logging.getLogger(__name__)
    
    def authenticate_with_access_check(self, 
                                       employee_id: str,
                                       facial_image_b64: str,
                                       voice_audio_b64: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Authentifie l'utilisateur et vérifie l'accès
        C'est le flux COMPLET appelé après capture faciale et vocale
        
        Args:
            employee_id: ID employé (ex: "1002218AAKH")
            facial_image_b64: Image faciale en base64
            voice_audio_b64: Audio vocal en base64
        
        Returns:
            Tuple (success: bool, message: str, result: dict)
            result contient:
              - user_id: UUID utilisateur
              - facial_confidence: Score similarité facial
              - voice_confidence: Score similarité vocal
              - access_allowed: True/False après vérification alerte
              - alert_details: Détails si accès bloqué
        """
        try:
            self.logger.info(f"Démarrage authentification pour {employee_id}")
            
            # ÉTAPE 1: Authentification faciale
            self.logger.info("1/3 - Vérification faciale en cours...")
            face_result = self.api_client.verify_face(
                employee_id=employee_id,
                image_b64=facial_image_b64,
                source='DESKTOP'  # Identifier source DESKTOP vs DOOR
            )
            
            if not face_result.success or not face_result.data.get('matched'):
                return False, f"Authentification faciale échouée: {face_result.error_message}", None
            
            face_confidence = face_result.data.get('similarity', 0.0)
            self.logger.info(f"Facial OK (conf: {face_confidence:.2%})")
            
            # ÉTAPE 2: Authentification vocale
            self.logger.info("2/3 - Vérification vocale en cours...")
            voice_result = self.api_client.verify_voice(
                employee_id=employee_id,
                audio_b64=voice_audio_b64,
                source='DESKTOP'
            )
            
            if not voice_result.success or not voice_result.data.get('matched'):
                return False, f"Authentification vocale échouée: {voice_result.error_message}", None
            
            voice_confidence = voice_result.data.get('similarity', 0.0)
            self.logger.info(f"Vocal OK (conf: {voice_confidence:.2%})")
            
            # À ce stade: authentification biométrique = SUCCÈS
            user_id = face_result.data.get('user_id')
            
            # ÉTAPE 3: VÉRIFICATION D'ACCÈS (NOUVEAU - CRITIQUE)
            self.logger.info("3/3 - Vérification d'accès (alertes de sécurité)...")
            access_allowed, access_reason, alert_details = self.access_verifier.check_access(user_id)
            
            if not access_allowed:
                # Accès BLOQUÉ par une alerte de sécurité
                self.logger.warning(f"Accès BLOQUÉ pour {user_id}: {access_reason}")
                
                alert_msg = self.access_verifier.format_alert_message(access_reason, alert_details)
                
                # Afficher l'alerte à l'utilisateur (UI)
                if self.app:
                    self.app.show_error_dialog("Accès Refusé", alert_msg)
                
                return False, alert_msg, {
                    'user_id': user_id,
                    'facial_confidence': face_confidence,
                    'voice_confidence': voice_confidence,
                    'access_allowed': False,
                    'alert_details': alert_details
                }
            
            # Accès AUTORISÉ
            self.logger.info(f"Accès AUTORISÉ pour {user_id}")
            success_msg = f"Authentification réussie\n{access_reason}"
            
            return True, success_msg, {
                'user_id': user_id,
                'facial_confidence': face_confidence,
                'voice_confidence': voice_confidence,
                'access_allowed': True,
                'alert_details': None,
                'auth_token': face_result.data.get('token')  # JWT token pour session
            }
        
        except Exception as e:
            self.logger.error(f"Erreur authentification: {e}")
            error_msg = f"Erreur système: {str(e)}"
            
            if self.app:
                self.app.show_error_dialog("Erreur", error_msg)
            
            return False, error_msg, None


# ============================================================
# EXEMPLE D'UTILISATION DANS L'APPLICATION TKINTER
# ============================================================

def example_tkinter_integration():
    """
    Exemple d'intégration dans une application Tkinter
    Montre comment appeler l'authentification avec vérification d'accès
    """
    from biometric_api_client import BioAccessAPIClient
    
    # Initialiser le client API
    api_client = BioAccessAPIClient(
        api_base="http://192.168.1.100:5000/api/v1",
        timeout=10
    )
    
    # Initialiser le système d'authentification avec contrôle d'accès
    auth_system = BiometricAuthenticationWithAccessControl(
        api_client=api_client,
        tkinter_app=None  # Remplacer par l'instance Tkinter réelle
    )
    
    # Exemple: après avoir capturé le visage et la voix
    employee_id = "1002218AAKH"
    facial_image_b64 = "iVBORw0KGgoAAAANS..."  # Image capturée
    voice_audio_b64 = "//NExAAL..."  # Audio capturé
    
    # Appeler l'authentification COMPLÈTE avec vérification d'accès
    success, message, result = auth_system.authenticate_with_access_check(
        employee_id=employee_id,
        facial_image_b64=facial_image_b64,
        voice_audio_b64=voice_audio_b64
    )
    
    if success:
        print(f"✅ Authentification et accès AUTORISÉS")
        print(f"   Utilisateur: {result['user_id']}")
        print(f"   Confiance faciale: {result['facial_confidence']:.2%}")
        print(f"   Confiance vocale: {result['voice_confidence']:.2%}")
        print(f"   Token: {result.get('auth_token', 'N/A')[:20]}...")
        
        # À ce stade: déverrouiller le poste
        # unlock_workstation()
    
    else:
        print(f"❌ Authentification ou accès REFUSÉ")
        print(f"   Raison: {message}")
        
        if result and result.get('alert_details'):
            alert = result['alert_details']
            print(f"   Alerte: {alert.get('alert_title')}")
            print(f"   Ressource bloquée: {alert.get('resource_blocked')}")


# ============================================================
# INTÉGRATION AVEC BOUCLE PRINCIPALE CLIENT DESKTOP
# ============================================================

def on_biometric_captured(event):
    """
    Callback appelé quand facial + vocal ont été capturés
    Déclenche l'authentification complète avec vérification d'accès
    """
    # event contient:
    #   - facial_image_b64
    #   - voice_audio_b64
    #   - employee_id
    
    auth_result = authenticate_with_access_check(
        employee_id=event.get('employee_id'),
        facial_image_b64=event.get('facial_image_b64'),
        voice_audio_b64=event.get('voice_audio_b64')
    )
    
    if auth_result['success']:
        # ✅ DÉVERROUILLER
        unlock_desktop()
        start_user_session(auth_result['result']['user_id'])
    else:
        # ❌ BLOQUER
        show_locked_screen(auth_result['message'])
        log_failed_attempt(auth_result)
