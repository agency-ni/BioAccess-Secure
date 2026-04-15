"""
Exemples d'utilisation de l'API BioAccess Secure
Déploiement: http://localhost:5000/api/docs (Swagger UI)
"""

# ============================================================
# AUTHENTIFICATION
# ============================================================

"""
1. LOGIN - Obtenir les tokens
"""
LOGIN_EXAMPLE = """
curl -X POST http://localhost:5000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "admin@bioaccess.secure",
    "password": "SecurePassword123!",
    "remember": true
  }'

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Authentification réussie",
  "data": {
    "access_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@bioaccess.secure",
      "first_name": "Admin",
      "last_name": "User",
      "role": "admin",
      "is_active": true
    }
  }
}
"""

"""
2. REFRESH TOKEN - Renouveler les credentials
"""
REFRESH_EXAMPLE = """
curl -X POST http://localhost:5000/api/v1/auth/refresh \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." \\
  -d '{
    "refresh_token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."
  }'
"""

"""
3. GET PROFILE - Récupérer le profil utilisateur actuel
"""
GET_PROFILE_EXAMPLE = """
curl -X GET http://localhost:5000/api/v1/auth/me \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Profil utilisateur",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@bioaccess.secure",
    "first_name": "Admin",
    "last_name": "User",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-06-01T12:00:00Z",
    "last_login_at": "2026-04-13T10:15:30Z"
  }
}
"""

"""
4. LOGOUT - Déconnecter l'utilisateur
"""
LOGOUT_EXAMPLE = """
curl -X POST http://localhost:5000/api/v1/auth/logout \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Déconnexion réussie"
}
"""

# ============================================================
# BIOMÉTRIE
# ============================================================

"""
5. VERIFY BIOMETRIC - Vérifier une donnée biométrique
"""
VERIFY_BIOMETRIC_EXAMPLE = """
# Vérification faciale
curl -X POST http://localhost:5000/api/v1/biometric/verify \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." \\
  -F "biometric_type=face" \\
  -F "file=@/path/to/face_image.jpg"

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Vérification biométrique réussie",
  "data": {
    "match": true,
    "confidence": 0.9847,
    "biometric_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
"""

"""
6. ENROLL BIOMETRIC - Enrôler une nouvelle donnée biométrique
"""
ENROLL_BIOMETRIC_EXAMPLE = """
# Enrôler une nouvelle face
curl -X POST http://localhost:5000/api/v1/biometric/enroll \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." \\
  -F "biometric_type=face" \\
  -F "file=@/path/to/face_image.jpg"

Response:
{
  "status": "success",
  "code": 201,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Données biométriques enrôlées avec succès",
  "data": {
    "biometric_id": "550e8400-e29b-41d4-a716-446655440002",
    "type": "face",
    "template_size": 512,
    "enrolled_at": "2026-04-13T10:30:45Z"
  }
}
"""

# ============================================================
# ACCÈS & AUDIT
# ============================================================

"""
7. GET ACCESS LOGS - Récupérer les logs d'accès
"""
ACCESS_LOGS_EXAMPLE = """
curl -X GET "http://localhost:5000/api/v1/access/logs?limit=50&offset=0&user_id=550e8400-e29b-41d4-a716-446655440000" \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Logs d'accès récupérés",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "access_point": "main_entrance",
      "biometric_type": "face",
      "success": true,
      "timestamp": "2026-04-13T10:15:30Z",
      "ip_address": "192.168.1.100"
    }
  ],
  "meta": {
    "total": 1250,
    "limit": 50,
    "offset": 0
  }
}
"""

"""
8. GET DASHBOARD STATS - Statistiques du dashboard
"""
DASHBOARD_EXAMPLE = """
curl -X GET http://localhost:5000/api/v1/dashboard/stats \\
  -H "Authorization: Bearer eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..."

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Statistiques du dashboard",
  "data": {
    "total_accesses": 15420,
    "successful_accesses": 15287,
    "failed_accesses": 133,
    "success_rate": 0.9914,
    "active_users": 127,
    "total_biometric_templates": 3540,
    "access_points": [
      {
        "name": "main_entrance",
        "total_accesses": 5200,
        "success_accesses": 5180
      }
    ]
  }
}
"""

# ============================================================
# HEALTH & MONITORING
# ============================================================

"""
9. HEALTH CHECK - Vérifier si le service est opérationnel
"""
HEALTH_CHECK_EXAMPLE = """
curl -X GET http://localhost:5000/api/v1/health

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Service opérationnel",
  "data": {
    "service": "bioaccess-api",
    "database": "connected",
    "cache": "connected",
    "queue": "connected"
  }
}
"""

"""
10. READINESS PROBE - Kubernetes readiness check
"""
READINESS_EXAMPLE = """
curl -X GET http://localhost:5000/api/v1/ready

Response:
{
  "status": "success",
  "code": 200,
  "timestamp": "2026-04-13T10:30:45Z",
  "message": "Service prêt"
}
"""

# ============================================================
# POSTMAN COLLECTION
# ============================================================

POSTMAN_COLLECTION = {
    "info": {
        "name": "BioAccess Secure API",
        "description": "Collection complète des endpoints API",
        "version": "2.0.0"
    },
    "variable": [
        {
            "key": "base_url",
            "value": "http://localhost:5000/api/v1",
            "type": "string"
        },
        {
            "key": "access_token",
            "value": "",
            "type": "string"
        },
        {
            "key": "refresh_token",
            "value": "",
            "type": "string"
        }
    ],
    "auth": {
        "type": "bearer",
        "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}]
    },
    "item": [
        {
            "name": "Authentication",
            "item": [
                {
                    "name": "Login",
                    "request": {
                        "method": "POST",
                        "header": [{"key": "Content-Type", "value": "application/json"}],
                        "body": {
                            "mode": "raw",
                            "raw": '{\n  "email": "admin@bioaccess.secure",\n  "password": "SecurePassword123!",\n  "remember": true\n}'
                        },
                        "url": {"raw": "{{base_url}}/auth/login"}
                    }
                },
                {
                    "name": "Get Profile",
                    "request": {
                        "method": "GET",
                        "url": {"raw": "{{base_url}}/auth/me"}
                    }
                },
                {
                    "name": "Logout",
                    "request": {
                        "method": "POST",
                        "url": {"raw": "{{base_url}}/auth/logout"}
                    }
                }
            ]
        },
        {
            "name": "Biometric",
            "item": [
                {
                    "name": "Verify",
                    "request": {
                        "method": "POST",
                        "url": {"raw": "{{base_url}}/biometric/verify"}
                    }
                },
                {
                    "name": "Enroll",
                    "request": {
                        "method": "POST",
                        "url": {"raw": "{{base_url}}/biometric/enroll"}
                    }
                }
            ]
        }
    ]
}

# ============================================================
# COMMANDES BASH UTILES
# ============================================================

BASH_UTILITIES = """
#!/bin/bash

# Variables
API_URL="http://localhost:5000/api/v1"
EMAIL="admin@bioaccess.secure"
PASSWORD="SecurePassword123!"

# 1. Login et extraire les tokens
LOGIN_RESPONSE=$(curl -s -X POST $API_URL/auth/login \\
  -H "Content-Type: application/json" \\
  -d "{\\"email\\":\\"$EMAIL\\",\\"password\\":\\"$PASSWORD\\"}")

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.refresh_token')

echo "Access Token: $ACCESS_TOKEN"
echo "Refresh Token: $REFRESH_TOKEN"

# 2. Utiliser le token
curl -X GET $API_URL/auth/me \\
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 3. Vérifier la santé
curl -X GET $API_URL/health

# 4. Récupérer les logs d'accès avec pagination
curl -X GET "$API_URL/access/logs?limit=10&offset=0" \\
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq '.'
"""

# ============================================================
# PATTERNS D'ERREUR COURANTS
# ============================================================

ERROR_PATTERNS = """
1. 401 Unauthorized
{
  "status": "error",
  "code": 401,
  "message": "Token invalide ou expiré",
  "timestamp": "2026-04-13T10:30:45Z"
}

2. 429 Rate Limited
{
  "status": "error",
  "code": 429,
  "message": "Trop de requêtes. Réessayez dans 5 minutes",
  "timestamp": "2026-04-13T10:30:45Z"
}

3. 422 Validation Error
{
  "status": "error",
  "code": 422,
  "message": "Données de requête invalides",
  "details": {
    "email": ["Format email invalide"],
    "password": ["Minimum 12 caractères requis"]
  },
  "timestamp": "2026-04-13T10:30:45Z"
}

4. 500 Internal Server Error
{
  "status": "error",
  "code": 500,
  "message": "Erreur interne du serveur",
  "timestamp": "2026-04-13T10:30:45Z"
}
"""
