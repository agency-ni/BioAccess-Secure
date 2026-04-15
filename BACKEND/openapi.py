"""
Spécification OpenAPI 3.0 pour BioAccess Secure API
Génère la documentation Swagger UI
"""

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "BioAccess Secure API",
        "description": """
        Système complet d'authentification biométrique multi-modale avec reconnaissance faciale et vocale.
        
        **Caractéristiques principales:**
        - Authentification biométrique (face, voix, fingerprint)
        - Gestion des accès granulaires
        - Audit et monitoring en temps réel
        - Alertes de sécurité intelligentes
        - Support OAuth 2.0 / OpenID Connect
        
        **Authentification:**
        - Bearer Token (JWT) dans l'en-tête `Authorization: Bearer <token>`
        - API Key dans l'en-tête `X-API-Key` pour les intégrations
        
        **Formats de réponse:**
        Toutes les réponses utilisent le format APIResponse normalisé:
        ```json
        {
            "status": "success|error",
            "code": 200,
            "timestamp": "2026-04-13T10:30:45Z",
            "message": "Message de la réponse",
            "data": {...},
            "meta": {...}
        }
        ```
        """,
        "version": "2.0.0",
        "contact": {
            "name": "BioAccess Support",
            "email": "support@bioaccess.secure",
            "url": "https://bioaccess.secure/support"
        },
        "license": {
            "name": "Proprietary",
            "url": "https://bioaccess.secure/license"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Development Server"
        },
        {
            "url": "https://api.bioaccess.secure",
            "description": "Production Server"
        }
    ],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT Token obtenu via /auth/login"
            },
            "apiKey": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Clé API pour les intégrations"
            }
        },
        "schemas": {
            "APIResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "error"],
                        "description": "Statut de la réponse"
                    },
                    "code": {
                        "type": "integer",
                        "description": "Code HTTP",
                        "example": 200
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Timestamp ISO 8601 UTC"
                    },
                    "message": {
                        "type": "string",
                        "description": "Message descriptif"
                    },
                    "data": {
                        "type": "object",
                        "description": "Données de la réponse"
                    },
                    "meta": {
                        "type": "object",
                        "description": "Métadonnées (pagination, etc.)"
                    }
                },
                "required": ["status", "code", "timestamp", "message"]
            },
            "LoginRequest": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "Adresse email"
                    },
                    "password": {
                        "type": "string",
                        "format": "password",
                        "description": "Mot de passe"
                    },
                    "remember": {
                        "type": "boolean",
                        "description": "Générer refresh token (30 jours)",
                        "default": False
                    }
                },
                "required": ["email", "password"]
            },
            "LoginResponse": {
                "allOf": [
                    {"$ref": "#/components/schemas/APIResponse"},
                    {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "properties": {
                                    "access_token": {
                                        "type": "string",
                                        "description": "JWT Token (1h expiration)"
                                    },
                                    "refresh_token": {
                                        "type": "string",
                                        "description": "Refresh Token (30j expiration) - si remember=true"
                                    },
                                    "user": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "email": {"type": "string"},
                                            "first_name": {"type": "string"},
                                            "last_name": {"type": "string"},
                                            "role": {"type": "string", "enum": ["admin", "operator", "viewer"]},
                                            "is_active": {"type": "boolean"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                ]
            },
            "BiometricData": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["face", "voice", "fingerprint"],
                        "description": "Type de donnée biométrique"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Score de confiance (0-1)"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Timestamp de la capture"
                    }
                }
            },
            "AccessLog": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "user_id": {"type": "string"},
                    "access_point": {"type": "string"},
                    "biometric_type": {"type": "string"},
                    "success": {"type": "boolean"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "ip_address": {"type": "string"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["error"]
                    },
                    "code": {
                        "type": "integer",
                        "example": 400
                    },
                    "message": {
                        "type": "string"
                    },
                    "details": {
                        "type": "object",
                        "description": "Détails supplémentaires de l'erreur"
                    }
                }
            }
        }
    },
    "paths": {
        "/api/v1/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Authentifier un utilisateur",
                "description": "Retourne un JWT token valide 1 heure et optionnellement un refresh token",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/LoginRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Authentification réussie",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginResponse"}
                            }
                        }
                    },
                    "401": {
                        "description": "Credentials invalides",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    },
                    "429": {
                        "description": "Rate limit dépassé (5 tentatives/5 min)"
                    }
                }
            }
        },
        "/api/v1/auth/refresh": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Renouveler le token",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "refresh_token": {"type": "string"}
                                },
                                "required": ["refresh_token"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Token renouvelé",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginResponse"}
                            }
                        }
                    },
                    "401": {
                        "description": "Refresh token expiré ou invalide"
                    }
                }
            }
        },
        "/api/v1/auth/logout": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Déconnecter l'utilisateur",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Déconnexion réussie"
                    }
                }
            }
        },
        "/api/v1/auth/me": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Obtenir le profil utilisateur actuel",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Profil utilisateur",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/APIResponse"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "string"},
                                                        "email": {"type": "string"},
                                                        "first_name": {"type": "string"},
                                                        "last_name": {"type": "string"},
                                                        "role": {"type": "string"},
                                                        "is_active": {"type": "boolean"},
                                                        "created_at": {"type": "string", "format": "date-time"}
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "401": {
                        "description": "Non authentifié"
                    }
                }
            }
        },
        "/api/v1/biometric/verify": {
            "post": {
                "tags": ["Biometric"],
                "summary": "Vérification biométrique",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "biometric_type": {
                                        "type": "string",
                                        "enum": ["face", "voice", "fingerprint"]
                                    },
                                    "file": {
                                        "type": "string",
                                        "format": "binary",
                                        "description": "Image ou audio"
                                    }
                                },
                                "required": ["biometric_type", "file"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Vérification réussie",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/APIResponse"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "type": "object",
                                                    "properties": {
                                                        "match": {"type": "boolean"},
                                                        "confidence": {
                                                            "type": "number",
                                                            "minimum": 0,
                                                            "maximum": 1
                                                        },
                                                        "biometric_id": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Type biométrique invalide ou fichier manquant"
                    }
                }
            }
        },
        "/api/v1/biometric/enroll": {
            "post": {
                "tags": ["Biometric"],
                "summary": "Enrôler une nouvelle donnée biométrique",
                "security": [{"bearerAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "biometric_type": {
                                        "type": "string",
                                        "enum": ["face", "voice", "fingerprint"]
                                    },
                                    "file": {
                                        "type": "string",
                                        "format": "binary"
                                    }
                                },
                                "required": ["biometric_type", "file"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Enrôlement réussi"
                    }
                }
            }
        },
        "/api/v1/access/logs": {
            "get": {
                "tags": ["Access Control"],
                "summary": "Lister les logs d'accès",
                "security": [{"bearerAuth": []}],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 50}
                    },
                    {
                        "name": "offset",
                        "in": "query",
                        "schema": {"type": "integer", "default": 0}
                    },
                    {
                        "name": "user_id",
                        "in": "query",
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Liste des logs d'accès",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "allOf": [
                                        {"$ref": "#/components/schemas/APIResponse"},
                                        {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "type": "array",
                                                    "items": {"$ref": "#/components/schemas/AccessLog"}
                                                },
                                                "meta": {
                                                    "type": "object",
                                                    "properties": {
                                                        "total": {"type": "integer"},
                                                        "limit": {"type": "integer"},
                                                        "offset": {"type": "integer"}
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dashboard/stats": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Statistiques du dashboard",
                "security": [{"bearerAuth": []}],
                "responses": {
                    "200": {
                        "description": "Statistiques"
                    }
                }
            }
        },
        "/api/v1/health": {
            "get": {
                "tags": ["Health"],
                "summary": "Health check du service",
                "responses": {
                    "200": {
                        "description": "Service operationnel"
                    },
                    "503": {
                        "description": "Service indisponible"
                    }
                }
            }
        },
        "/api/v1/ready": {
            "get": {
                "tags": ["Health"],
                "summary": "Readiness probe for Kubernetes",
                "responses": {
                    "200": {
                        "description": "Service ready"
                    },
                    "503": {
                        "description": "Service not ready"
                    }
                }
            }
        }
    },
    "security": [
        {"bearerAuth": []}
    ],
    "tags": [
        {
            "name": "Authentication",
            "description": "Endpoints d'authentification et gestion de session"
        },
        {
            "name": "Biometric",
            "description": "Endpoints de traitement biométrique"
        },
        {
            "name": "Access Control",
            "description": "Gestion des logs d'accès et audit"
        },
        {
            "name": "Dashboard",
            "description": "Données et statistiques du dashboard"
        },
        {
            "name": "Health",
            "description": "Health et readiness checks"
        }
    ]
}
