"""
Module de vérification d'accès pour Client Desktop
Vérifie après authentification si l'utilisateur a le droit d'accéder
(en fonction des alertes de sécurité)

Intégration avec alerts.py du backend
Endpoints:
  - GET /api/v1/alerts/access/check/{user_id}
  - GET /api/v1/alerts/access/status/{user_id}
"""

import logging
import requests
from typing import Dict, Tuple, Optional
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class AccessVerifier:
    """
    Vérifie l'accès d'un utilisateur après authentification biométrique
    Appelle le backend pour vérifier les alertes de sécurité actives
    """
    
    def __init__(self, api_client):
        """
        Initialise le vérificateur d'accès
        
        Args:
            api_client: Instance de BioAccessAPIClient
        """
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
    
    def check_access(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Vérifie si un utilisateur peut accéder
        APPEL CRITIQUE après authentification biométrique réussie
        
        Args:
            user_id: UUID ou employee_id de l'utilisateur
        
        Returns:
            Tuple (allowed: bool, reason: str, alert_details: dict|None)
            - allowed: True = accès autorisé, False = accès bloqué
            - reason: Message d'explication
            - alert_details: Détails de l'alerte si bloquée
        
        Exemple:
            allowed, reason, alert = verifier.check_access(user_id)
            if not allowed:
                show_error_dialog(reason, alert['alert_title'])
                return
        """
        try:
            # Construire l'URL
            endpoint = f"/alerts/access/check/{user_id}"
            url = urljoin(self.api_client.api_base, endpoint)
            
            # Appeler le backend (pas de token requis pour ce endpoint)
            response = requests.get(
                url,
                headers=self.api_client.session.headers,
                timeout=self.api_client.timeout,
                verify=self.api_client.verify_ssl
            )
            
            if response.status_code != 200:
                logger.error(f"Erreur vérification accès {user_id}: {response.status_code}")
                # Fail-closed: en cas d'erreur, bloquer par défaut
                return False, "Erreur vérification accès - accès bloqué par défaut", None
            
            data = response.json()
            
            if data.get('success') is False:
                logger.warning(f"API returned success=false for user {user_id}")
                return False, data.get('message', 'Erreur serveur'), None
            
            api_data = data.get('data', {})
            
            # Extraire les informations
            allowed = api_data.get('allowed', False)
            reason = api_data.get('reason', '')
            
            if allowed:
                logger.info(f"Accès AUTORISÉ pour {user_id}")
                return True, reason, None
            else:
                # Accès BLOQUÉ - construire les détails de l'alerte
                alert_details = {
                    'alert_id': api_data.get('alert_id'),
                    'alert_title': api_data.get('alert_title', 'Alerte de sécurité'),
                    'resource_blocked': api_data.get('resource_blocked', 'poste'),
                    'timestamp': api_data.get('timestamp')
                }
                logger.warning(f"Accès BLOQUÉ pour {user_id}: {reason}")
                return False, reason, alert_details
        
        except requests.Timeout:
            logger.error(f"Timeout vérification accès {user_id}")
            return False, "Timeout serveur - accès bloqué par défaut", None
        except requests.ConnectionError:
            logger.error(f"Erreur connexion vérification accès {user_id}")
            return False, "Erreur connexion - accès bloqué par défaut", None
        except Exception as e:
            logger.error(f"Exception vérification accès {user_id}: {e}")
            return False, f"Erreur système: {str(e)}", None
    
    def get_access_status(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Alias pour check_access - même fonctionnalité
        """
        return self.check_access(user_id)
    
    def format_alert_message(self, reason: str, alert_details: Optional[Dict]) -> str:
        """
        Formate un message d'alerte pour affichage à l'utilisateur
        
        Args:
            reason: Raison du blocage (from API)
            alert_details: Détails de l'alerte
        
        Returns:
            Message formaté pour affichage
        """
        if not alert_details:
            return f"❌ Accès refusé\n\n{reason}"
        
        msg = f"❌ ACCÈS BLOQUÉ\n\n"
        msg += f"Raison: {reason}\n"
        msg += f"Alerte: {alert_details.get('alert_title', 'Alerte de sécurité')}\n"
        msg += f"Ressource: {alert_details.get('resource_blocked', 'inconnue')}\n"
        
        if alert_details.get('timestamp'):
            msg += f"Date: {alert_details['timestamp']}\n"
        
        msg += f"\nVeuillez contacter votre administrateur système."
        
        return msg
