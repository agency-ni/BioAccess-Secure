"""
Système de gestion des Employee ID - Détection de réinstallation

SCÉNARIO 1: Employee ID valide et encore actif
├─ Authentification → SUCCÈS
└─ Accès accordé immédiatement

SCÉNARIO 2: Employee ID obsolète (ancien, après réinstallation)
├─ L'utilisateur réinstalle l'application
├─ Utilise le vieil employee_id stocké localement
├─ Système détecte: last_employee_id != employee_id 
└─ Actions:
   ├─ ⚠️ Refuser l'accès
   ├─ 📧 Alerter l'admin: "Tentative avec ancien ID"
   ├─ 📋 Logger l'incident
   └─ Proposer à l'utilisateur de demander nouveau ID à l'admin

SCÉNARIO 3: Employee ID fictif (jamais généré)
├─ Utilisateur entre un ID invalide
├─ Système vérifie l'unicité
└─ Actions:
   ├─ ❌ Refuser l'accès
   └─ 📋 Logger la tentative suspecte

BASE DE DONNÉES:

users table:
├─ id (UUID) - clé primaire
├─ employee_id (VARCHAR 12) - unique, clé d'authentification ACTIVE
├─ employee_id_created_at (DATETIME) - quand créé
├─ last_employee_id (VARCHAR 12) - ancien ID en cas de réinstallation
└─ ...

Exemple:
┌─────┬──────────────────┬─────────────────┬──────────────────┐
│ ID  │ employee_id      │ created_at      │ last_employee_id │
├─────┼──────────────────┼─────────────────┼──────────────────┤
│ u1  │ 1002218AAKH      │ 2024-01-01      │ NULL             │
│ u2  │ 1002219MXYO      │ 2024-01-02      │ 1002219QWER      │ ← ancien ID détecté
└─────┴──────────────────┴─────────────────┴──────────────────┘
"""

# ============================================================
# BACKEND - GESTION DES EMPLOYEE ID
# ============================================================

from datetime import datetime
from core.database import db
from models.user import User
import logging

logger = logging.getLogger(__name__)


class EmployeeIDManager:
    """
    Gère les Employee ID et détecte les réinstallations
    """
    
    @staticmethod
    def verify_employee_id(employee_id: str) -> tuple[bool, dict]:
        """
        Vérifier si un employee_id est valide et actif
        
        Returns:
            (is_valid, details_dict)
        """
        if not employee_id or len(employee_id) != 12:
            return False, {"error": "Employee ID invalide (format)"}
        
        # Chercher l'utilisateur avec cet employee_id actif
        user = User.query.filter_by(employee_id=employee_id).first()
        
        if not user:
            # Vérifier si c'est un ancien ID
            old_user = User.query.filter_by(last_employee_id=employee_id).first()
            if old_user:
                logger.warning(f"Tentative avec ANCIEN employee_id: {employee_id} par {old_user.email}")
                
                # Créer alerte pour l'admin
                EmployeeIDManager._create_admin_alert(
                    user_id=old_user.id,
                    alert_type="OLD_EMPLOYEE_ID",
                    message=f"Tentative d'authentification avec ancien employee_id: {employee_id}",
                    details={
                        "old_id": employee_id,
                        "new_id": old_user.employee_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                return False, {
                    "error": "ANCIEN_ID_DETECTED",
                    "message": "Cet ID a été remplacé. Contactez l'admin pour obtenir votre nouvel ID.",
                    "alert_sent": true
                }
            
            return False, {"error": "Employee ID non trouvé"}
        
        # Vérifier que l'utilisateur est actif
        if not user.is_active:
            return False, {"error": "Utilisateur désactivé"}
        
        return True, {
            "user_id": user.id,
            "employee_id": user.employee_id,
            "nom": user.nom,
            "prenom": user.prenom,
            "email": user.email,
            "role": user.role
        }
    
    @staticmethod
    def rotate_employee_id(user_id: str) -> dict:
        """
        Remplacer l'employee_id d'un utilisateur (réinstallation)
        L'ancien ID est sauvegardé dans last_employee_id
        
        Returns:
            {success, new_employee_id, old_employee_id, alert_sent}
        """
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return {"success": False, "error": "Utilisateur non trouvé"}
        
        old_id = user.employee_id
        
        # Générer nouvel ID
        new_id = User.generate_employee_id()
        
        # Sauvegarder ancien ID
        user.last_employee_id = old_id
        
        # Assigner nouvel ID
        user.employee_id = new_id
        user.employee_id_created_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Rotation employee_id pour {user.email}: {old_id} → {new_id}")
        
        # Créer alerte pour l'admin
        EmployeeIDManager._create_admin_alert(
            user_id=user_id,
            alert_type="EMPLOYEE_ID_ROTATED",
            message=f"Employee ID remplacé (probablement réinstallation)",
            details={
                "old_id": old_id,
                "new_id": new_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "old_employee_id": old_id,
            "new_employee_id": new_id,
            "alert_sent": True
        }
    
    @staticmethod
    def _create_admin_alert(user_id: str, alert_type: str, message: str, details: dict = None) -> bool:
        """
        Créer une alerte pour les admins en cas d'anomalie
        """
        try:
            from models.alert import Alerte
            
            alert = Alerte(
                user_id=user_id,
                type_alerte=alert_type,
                message=message,
                details=details or {},
                date_alerte=datetime.utcnow(),
                lue=False
            )
            db.session.add(alert)
            db.session.commit()
            
            logger.info(f"Alerte créée: {alert_type} pour user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur création alerte: {e}")
            return False


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

def example_verify_employee_id():
    """
    Exemple: Vérifier un employee_id lors de l'authentification
    """
    employee_id = "1002218AAKH"
    
    is_valid, details = EmployeeIDManager.verify_employee_id(employee_id)
    
    if is_valid:
        print(f"✅ Valid: {details['nom']} {details['prenom']}")
        # Procéder à l'authentification biométrique
    else:
        if details.get('error') == 'ANCIEN_ID_DETECTED':
            print(f"⚠️ Ancien ID détecté - Admin notifié")
            print(f"Message: {details.get('message')}")
        else:
            print(f"❌ Erreur: {details.get('error')}")


def example_rotate_employee_id():
    """
    Exemple: Remplacer l'employee_id (réinstallation)
    """
    result = EmployeeIDManager.rotate_employee_id(user_id="uuid-123")
    
    if result['success']:
        print(f"Ancien ID: {result['old_employee_id']}")
        print(f"Nouvel ID: {result['new_employee_id']}")
        print(f"Admin alerte: {result['alert_sent']}")
    else:
        print(f"Erreur: {result['error']}")
