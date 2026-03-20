"""
Constantes de l'application
"""

# Rôles utilisateurs
ROLES = {
    'SUPER_ADMIN': 'super_admin',
    'ADMIN': 'admin',
    'EMPLOYE': 'employe',
    'AUDITEUR': 'auditeur'
}

# Types d'accès
ACCESS_TYPES = {
    'POSTE': 'poste',
    'PORTE': 'porte',
    'AUTH': 'auth',
    'CONFIG': 'config'
}

# Types d'alertes
ALERT_TYPES = {
    'SECURITE': 'securite',
    'SYSTEME': 'systeme',
    'TENTATIVE': 'tentative'
}

# Gravités d'alerte
ALERT_GRAVITY = {
    'BASSE': 'basse',
    'MOYENNE': 'moyenne',
    'HAUTE': 'haute'
}

# Règles d'alerte
ALERT_RULES = {
    'three_failures': {
        'type': 'tentative',
        'gravite': 'haute',
        'message': "3 échecs consécutifs pour {user}"
    },
    'unauthorized_access': {
        'type': 'securite',
        'gravite': 'haute',
        'message': "Tentative accès non autorisé: {reason}"
    },
    'off_hours': {
        'type': 'securite',
        'gravite': 'moyenne',
        'message': "Accès hors horaire à {heure}h"
    },
    'suspicious_activity': {
        'type': 'securite',
        'gravite': 'moyenne',
        'message': "Activité suspecte: {count} échecs en {minutes} min"
    },
    'server_down': {
        'type': 'systeme',
        'gravite': 'haute',
        'message': "Serveur {component} inaccessible"
    }
}

# Types de logs
LOG_TYPES = ACCESS_TYPES

# Statuts
STATUS = {
    'SUCCESS': 'succes',
    'FAILED': 'echec'
}

# Formats de rapport
REPORT_FORMATS = {
    'PDF': 'pdf',
    'EXCEL': 'excel',
    'CSV': 'csv'
}

# Types de rapport
REPORT_TYPES = {
    'DAILY': 'journalier',
    'WEEKLY': 'hebdomadaire',
    'MONTHLY': 'mensuel',
    'CUSTOM': 'personnalise'
}

# Paramètres par défaut
DEFAULT_CONFIG = {
    'face_threshold': 0.6,
    'voice_threshold': 0.7,
    'max_login_attempts': 5,
    'lockout_duration': 15,  # minutes
    'session_timeout': 480,  # minutes (8h)
    'log_retention_days': 90,
    'door_timeout': 5,  # secondes
    'allowed_departments': ['informatique', 'direction']
}

# Types de fichiers autorisés
ALLOWED_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp',  # Images
    'wav', 'mp3', 'ogg', 'm4a',            # Audio
    'pdf', 'xlsx', 'csv'                    # Documents
}

# Taille maximale des fichiers (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024