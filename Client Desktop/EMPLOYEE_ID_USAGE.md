"""
Module Desktop Client - Authentification avec Employee ID

Format de l'Employee ID:
- Format: XXXXXXXAAAA (12 caractères)
  - 7 chiffres (séquentiel) ex: 1002218
  - 4 lettres aléatoires (A-Z) ex: AAKH
  - Exemple complet: 1002218AAKH

Utilisation du Desktop Client:
1. L'administrateur crée un nouvel utilisateur via le backend
2. Le backend génère automatiquement un employee_id unique
3. L'administrateur communique cet ID à l'utilisateur
4. L'utilisateur configure son Desktop Client avec cet employee_id
5. Le Desktop Client utilise cet employee_id comme clé d'authentification

Sécurité:
- L'employee_id est UNIQUE dans la base de données
- Impossible d'avoir deux utilisateurs avec le même employee_id
- Si un utilisateur réinstalle l'application et utilise un ancien employee_id:
  → Le système détecte que c'est un ancien ID
  → Une alerte est envoyée à l'admin
  → L'accès peut être refusé (selon politiques)

Configuration Desktop Client (config.py):
-----------
EMPLOYEE_ID = "1002218AAKH"  # Clé unique fournie par l'admin
API_URL = "http://localhost:5000/api"
SOURCE = "DESKTOP"
-----------

Endpoint d'authentification Desktop:
POST /api/v1/auth/face/verify
{
    "employee_id": "1002218AAKH",  # REMPLACE user_id pour Desktop
    "image_b64": "...",
    "source": "DESKTOP"
}

Réponse:
{
    "status": "success",
    "message": "Authentification réussie",
    "data": {
        "user_id": "uuid-...",
        "employee_id": "1002218AAKH",
        "nom": "Dupont",
        "prenom": "Jean",
        "role": "employe",
        "access_granted": true,
        "timestamp": "2024-01-01T..."
    }
}

Gestion des Erreurs Desktop:
- 401: Employee ID invalide ou non trouvé
- 403: Utilisateur désactivé ou ancien ID détecté
- 400: Données biométriques invalides

"""

# ============================================================
# EXEMPLE D'UTILISATION - DESKTOP CLIENT UPDATE
# ============================================================

import requests
from datetime import datetime


class DesktopAuthenticationClient:
    """
    Client d'authentification pour Desktop
    Utilise l'employee_id au lieu de user_id
    """
    
    def __init__(self, employee_id: str, api_url: str = "http://localhost:5000/api"):
        """
        Initialiser le client avec Employee ID
        
        Args:
            employee_id: ID unique de l'employé (ex: 1002218AAKH)
            api_url: URL de base du backend
        """
        self.employee_id = employee_id
        self.api_url = api_url
        self.timeout = 5
    
    def authenticate_face(self, image_base64: str) -> dict:
        """
        Authentifier avec reconnaissance faciale
        
        Args:
            image_base64: Image du visage encodée en base64
            
        Returns:
            Réponse du backend avec détails d'authentification
        """
        try:
            response = requests.post(
                f"{self.api_url}/v1/auth/face/verify",
                json={
                    "employee_id": self.employee_id,
                    "image_b64": image_base64,
                    "source": "DESKTOP"
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "❌ Employee ID invalide",
                    "details": response.json()
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "❌ Accès refusé - Ancien ID détecté ou utilisateur désactivé",
                    "details": response.json(),
                    "alert_admin": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Erreur serveur: {response.status_code}"
                }
                
        except requests.Timeout:
            return {
                "success": False,
                "error": "❌ Timeout - Impossible de contacter le serveur",
                "retry": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur: {str(e)}"
            }
    
    def authenticate_voice(self, audio_base64: str) -> dict:
        """
        Authentifier avec reconnaissance vocale
        
        Args:
            audio_base64: Audio encodé en base64
            
        Returns:
            Réponse du backend avec détails d'authentification
        """
        try:
            response = requests.post(
                f"{self.api_url}/v1/auth/voice/verify",
                json={
                    "employee_id": self.employee_id,
                    "audio_b64": audio_base64,
                    "source": "DESKTOP"
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get('message', 'Authentification échouée')
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur: {str(e)}"
            }


# ============================================================
# UTILISATION
# ============================================================

if __name__ == "__main__":
    # Configuration
    EMPLOYEE_ID = "1002218AAKH"  # Fourni par l'admin
    
    # Créer le client
    client = DesktopAuthenticationClient(
        employee_id=EMPLOYEE_ID,
        api_url="http://localhost:5000/api"
    )
    
    # Authentifier avec visage
    print("🔐 Authentification faciale...")
    # result = client.authenticate_face(image_base64_data)
    # print(result)
    
    print("✅ Client prêt pour authentification")
