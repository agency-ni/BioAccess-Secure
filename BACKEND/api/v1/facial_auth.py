"""
Routes API pour l'authentification faciale et vocale
Endpoints complets pour reconnaissance faciale, vocale et détection de vivacité
Support employee_id pour Desktop Client et email pour autres clients
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from typing import Dict, Tuple
from datetime import datetime, timedelta
import base64
import io
import logging
import uuid
import numpy as np
import cv2
import face_recognition
from scipy.spatial.distance import cosine as cosine_distance

from core.database import db
from core.errors import AuthenticationError, ValidationError, NotFoundError
from core.logger import log_audit
from api.middlewares.auth_middleware import token_required, optional_token
from models.user import User, UserSession, LoginLog
from models.log import LogAcces
from services.biometric_service import BiometricService
from services.auth_service import AuthService
from services.employee_id_manager import EmployeeIDManager

logger = logging.getLogger(__name__)

# Blueprint pour l'authentification biométrique
facial_bp = Blueprint('facial_auth', __name__)

# Services
biometric_service = BiometricService()
auth_service = AuthService()
employee_id_manager = EmployeeIDManager()

# ============================================================
# AUTHENTIFICATION FACIALE
# ============================================================

@facial_bp.route('/face/register', methods=['POST'])
@token_required
def register_face() -> Tuple[Dict, int]:
    """
    Enregistrer un nouveau visage pour l'utilisateur connecté
    
    POST /api/v1/auth/face/register
    Header: Authorization: Bearer <token>
    Body:
        {
            "image_data": "base64_encoded_image",
            "label": "Face enregistrée le 2024"
        }
    
    Response:
        {
            "success": true,
            "template_id": "uuid",
            "encoding_vector": [...],
            "message": "Visage enregistré avec succès"
        }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            raise ValidationError("image_data (base64) requis")
        
        # Décoder l'image base64
        try:
            image_bytes = base64.b64decode(data['image_data'])
            
            # ✅ VALIDATION: Vérifier la taille de l'image
            # Max 5MB pour images biométriques (plus petit que le limit global 10MB)
            MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
            if len(image_bytes) > MAX_IMAGE_SIZE:
                raise ValidationError(
                    f"Image trop volumineux: {len(image_bytes) / 1024 / 1024:.1f}MB "
                    f"(max {MAX_IMAGE_SIZE / 1024 / 1024:.1f}MB)"
                )
            
            image_file = io.BytesIO(image_bytes)
        except base64.binascii.Error as e:
            raise ValidationError(f"Format base64 invalide: {e}")
        except Exception as e:
            raise ValidationError(f"Erreur décodage image: {e}")
        
        # Traiter l'image et générer le template
        encoding = biometric_service.process_face_image(image_file)
        
        if encoding is None:
            raise ValidationError("Aucun visage détecté dans l'image")
        
        # Sauvegarder le template en base de données
        template_id = str(uuid.uuid4())
        from models.biometric import TemplateBiometrique
        
        template = TemplateBiometrique(
            id=template_id,
            user_id=user_id,
            type_biometrique='FACE',
            template_data=encoding.tolist(),
            label=data.get('label', 'Visage enregistré'),
            date_creation=datetime.now(),
            date_derniere_utilisation=datetime.now()
        )
        
        db.session.add(template)
        db.session.commit()
        
        # Log audit
        log_audit(
            user_id=user_id,
            action='FACE_REGISTRATION',
            resource='biometric_template',
            resource_id=template_id,
            details={'type': 'FACE', 'label': data.get('label')},
            status='SUCCESS'
        )
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'encoding_vector': encoding.tolist()[:10],  # Premiers éléments seulement
            'message': 'Visage enregistré avec succès'
        }), 201
    
    except (ValidationError, AuthenticationError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Erreur enregistrement facial: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@facial_bp.route('/face/verify', methods=['POST'])
def verify_face() -> Tuple[Dict, int]:
    """
    Authentifier un utilisateur via reconnaissance faciale
    Supporte EMPLOYEE_ID (Desktop Client) ou EMAIL (autres clients)
    
    POST /api/v1/auth/face/verify
    Body:
        {
            "employee_id": "1002218AAKH",  ← Pour Desktop Client
            "image_data": "base64_encoded_image",
            "source": "DESKTOP"  ← Optionnel (DESKTOP ou DOOR)
        }
        OU
        {
            "email": "user@example.com",  ← Pour autres clients
            "image_data": "base64_encoded_image"
        }
    
    Response:
        {
            "success": true,
            "matched": true,
            "similarity": 0.95,
            "token": "jwt_token",
            "user": {...},
            "message": "Authentification réussie"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            raise ValidationError("image_data (base64) requis")
        
        # Déterminer la source (Desktop vs autre)
        source = data.get('source', 'DESKTOP').upper()
        if source not in ['DESKTOP', 'DOOR']:
            source = 'DESKTOP'
        
        # ========== IDENTIFICATION UTILISATEUR ==========
        user = None
        identifier = None  # user_id, email ou employee_id
        
        # Priorité 1: employee_id (Desktop Client)
        if 'employee_id' in data and data['employee_id']:
            employee_id = data['employee_id']
            is_valid, details = EmployeeIDManager.verify_employee_id(employee_id)
            
            if not is_valid:
                # Créer log d'échec
                login_log = LoginLog(
                    email='',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    success=False,
                    method='FACE'
                )
                db.session.add(login_log)
                
                # Créer alerte si ancien ID
                if details.get('error') == 'ANCIEN_ID_DETECTED':
                    log_entry = LogAcces(
                        type_acces='auth',
                        statut='echec',
                        raison_echec=f"Tentative avec ancien employee_id: {employee_id}",
                        adresse_ip=request.remote_addr,
                        source_type=source,
                        details={'employee_id': employee_id, 'reason': 'OLD_ID'}
                    )
                    log_entry.enregistrer()
                    db.session.add(login_log)
                    db.session.commit()
                    raise AuthenticationError(f"❌ {details.get('message', 'Employee ID invalide')}")
                
                db.session.commit()
                raise AuthenticationError("❌ Employee ID invalide")
            
            user = User.query.filter_by(id=details.get('user_id')).first()
            identifier = f"emp_id:{employee_id}"
        
        # Priorité 2: email (clients web/autre)
        elif 'email' in data and data['email']:
            email = data['email'].lower()
            user = User.query.filter_by(email=email).first()
            identifier = f"email:{email}"

        # Priorité 3: user_id UUID direct (Door-System)
        elif 'user_id' in data and data['user_id']:
            user = User.query.get(data['user_id'])
            identifier = f"user_id:{str(data['user_id'])[:8]}"

        else:
            raise ValidationError("employee_id, email ou user_id requis")

        # Log de tentative
        login_log = LoginLog(
            email=user.email if user else data.get('email', ''),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=False,
            method='FACE'
        )
        
        if not user:
            db.session.add(login_log)
            db.session.commit()
            raise AuthenticationError("Utilisateur non trouvé")
        
        if not user.is_active:
            db.session.add(login_log)
            db.session.commit()
            raise AuthenticationError("Compte désactivé")
        
        # ========== VÉRIFICATION BIOMÉTRIQUE ==========
        # Décoder et encoder l'image
        try:
            image_bytes = base64.b64decode(data['image_data'])
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValidationError("Image illisible")
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            provided_encoding, _quality, n_faces = BiometricService.extract_face_features(rgb_img)
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Erreur décodage image: {e}")

        if provided_encoding is None:
            db.session.add(login_log)
            db.session.commit()
            raise ValidationError("Aucun visage détecté dans l'image")
        
        # Récupérer les templates stockés
        from models.biometric import TemplateBiometrique
        templates = TemplateBiometrique.query.filter_by(
            user_id=user.id,
            type_biometrique='FACE'
        ).all()
        
        if not templates:
            db.session.add(login_log)
            db.session.commit()
            raise AuthenticationError("Aucun visage enregistré pour cet utilisateur")
        
        # Vérifier contre tous les templates
        best_similarity = 0
        matched = False
        
        for template in templates:
            known_enc = np.array(template.template_data)
            dist = face_recognition.face_distance([known_enc], provided_encoding)[0]
            similarity = float(max(0.0, 1.0 - dist))

            if similarity > best_similarity:
                best_similarity = similarity
                if dist < 0.55:  # seuil face_recognition (distance < 0.55 = match)
                    matched = True
                    template.date_derniere_utilisation = datetime.now()
        
        if not matched:
            db.session.add(login_log)
            db.session.commit()
            
            # Log d'échec
            log_entry = LogAcces(
                type_acces='auth',
                statut='echec',
                raison_echec=f"Reconnaissance faciale échouée (similarité: {best_similarity:.2f})",
                adresse_ip=request.remote_addr,
                utilisateur_id=user.id,
                source_type=source,
                details={'similarity': best_similarity, 'identifier': identifier}
            )
            log_entry.enregistrer()
            
            raise AuthenticationError("Reconnaissance faciale échouée")
        
        # ========== AUTHENTIFICATION RÉUSSIE ==========
        login_log.success = True
        db.session.add(login_log)
        
        # Créer la session
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_type='bearer',
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            auth_method='FACE'
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Log succès
        log_entry = LogAcces(
            type_acces='auth',
            statut='succes',
            adresse_ip=request.remote_addr,
            utilisateur_id=user.id,
            source_type=source,
            details={'similarity': best_similarity, 'identifier': identifier}
        )
        log_entry.enregistrer()
        
        # Log audit
        log_audit(
            user_id=user.id,
            action='AUTHENTICATION',
            resource='user_session',
            resource_id=session.id,
            details={'method': 'FACE', 'similarity': best_similarity, 'source': source},
            status='SUCCESS'
        )
        
        return jsonify({
            'success': True,
            'matched': True,
            'similarity': round(best_similarity, 4),
            'token': session.id,
            'user': {
                'id': user.id,
                'employee_id': user.employee_id,
                'email': user.email,
                'nom': user.nom,
                'prenom': user.prenom,
                'role': user.role
            },
            'message': 'Authentification par visage réussie ✅'
        }), 200
    
    except (ValidationError, AuthenticationError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401
    except Exception as e:
        logger.error(f"Erreur vérification faciale: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


# ============================================================
# AUTHENTIFICATION VOCALE
# ============================================================

@facial_bp.route('/voice/challenge', methods=['GET'])
def get_voice_challenge() -> Tuple[Dict, int]:
    """
    Obtenir une phrase aléatoire pour défi vocal
    Endpoint public (pas de token requis)
    
    GET /api/v1/auth/voice/challenge
    
    Response:
        {
            "success": true,
            "phrase_id": "uuid",
            "phrase": "Bonjour, je suis une personne autorisée.",
            "instruction": "Veuillez lire cette phrase à voix claire"
        }
    """
    try:
        from models.biometric import PhraseAleatoire
        
        # Obtenir une phrase aléatoire
        phrase = PhraseAleatoire.getRandom()
        
        if not phrase:
            return jsonify({
                'success': False,
                'error': 'Aucune phrase disponible'
            }), 500
        
        return jsonify({
            'success': True,
            'phrase_id': phrase.id,
            'phrase': phrase.texte,
            'instruction': 'Veuillez lire cette phrase à voix claire et naturelle'
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur récupération phrase défi: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@facial_bp.route('/voice/register', methods=['POST'])
@token_required
def register_voice() -> Tuple[Dict, int]:
    """
    Enregistrer un modèle vocal pour l'utilisateur connecté
    
    POST /api/v1/auth/voice/register
    Header: Authorization: Bearer <token>
    Body:
        {
            "audio_data": "base64_encoded_wav",
            "label": "Voix enregistrée"
        }
    
    Response:
        {
            "success": true,
            "template_id": "uuid",
            "message": "Voix enregistrée avec succès"
        }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data or 'audio_data' not in data:
            raise ValidationError("audio_data (base64) requis")
        
        # Décoder l'audio base64
        try:
            audio_bytes = base64.b64decode(data['audio_data'])
            audio_file = io.BytesIO(audio_bytes)
        except Exception as e:
            raise ValidationError(f"Erreur décodage audio: {e}")
        
        # Génerer le template vocal
        voice_encoding = biometric_service.extract_voice_features(audio_file)
        
        if voice_encoding is None:
            raise ValidationError("Impossible d'extraire les caractéristiques vocales")
        
        # Sauvegarder le template
        template_id = str(uuid.uuid4())
        from models.biometric import TemplateBiometrique
        
        template = TemplateBiometrique(
            id=template_id,
            user_id=user_id,
            type_biometrique='VOICE',
            template_data=voice_encoding if isinstance(voice_encoding, list) else [voice_encoding],
            label=data.get('label', 'Voix enregistrée'),
            date_creation=datetime.now(),
            date_derniere_utilisation=datetime.now()
        )
        
        db.session.add(template)
        db.session.commit()
        
        log_audit(
            user_id=user_id,
            action='VOICE_REGISTRATION',
            resource='biometric_template',
            resource_id=template_id,
            details={'type': 'VOICE'},
            status='SUCCESS'
        )
        
        return jsonify({
            'success': True,
            'template_id': template_id,
            'message': 'Voix enregistrée avec succès'
        }), 201
    
    except (ValidationError, AuthenticationError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Erreur enregistrement vocal: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@facial_bp.route('/voice/verify', methods=['POST'])
def verify_voice() -> Tuple[Dict, int]:
    """
    Authentifier un utilisateur via reconnaissance vocale
    Supporte EMPLOYEE_ID (Desktop Client) ou EMAIL (autres clients)
    Support phrases aléatoires pour anti-replay
    
    POST /api/v1/auth/voice/verify
    Body:
        {
            "employee_id": "1002218AAKH",  ← Pour Desktop Client
            "audio_data": "base64_encoded_wav",
            "phrase_id": "uuid",           ← Optionnel (ID phrase lue)
            "source": "DESKTOP"            ← Optionnel (DESKTOP ou DOOR)
        }
        OU
        {
            "email": "user@example.com",   ← Pour autres clients
            "audio_data": "base64_encoded_wav",
            "phrase_id": "uuid"            ← Optionnel
        }
    
    Response:
        {
            "success": true,
            "matched": true,
            "similarity": 0.85,
            "token": "jwt_token",
            "user": {...},
            "phrase_id": "uuid",
            "message": "Authentification réussie"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'audio_data' not in data:
            raise ValidationError("audio_data (base64) requis")
        
        # Phrase optionnelle (pour enregistrement vérification)
        phrase_id = data.get('phrase_id')
        
        # Déterminer la source (Desktop vs autre)
        source = data.get('source', 'DESKTOP').upper()
        if source not in ['DESKTOP', 'DOOR']:
            source = 'DESKTOP'
        
        # ========== IDENTIFICATION UTILISATEUR ==========
        user = None
        identifier = None  # user_id, email ou employee_id
        
        # Priorité 1: employee_id (Desktop Client)
        if 'employee_id' in data and data['employee_id']:
            employee_id = data['employee_id']
            is_valid, details = EmployeeIDManager.verify_employee_id(employee_id)
            
            if not is_valid:
                # Créer log d'échec
                login_log = LoginLog(
                    email='',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    success=False,
                    method='VOICE'
                )
                db.session.add(login_log)
                
                # Créer alerte si ancien ID
                if details.get('error') == 'ANCIEN_ID_DETECTED':
                    log_entry = LogAcces(
                        type_acces='auth',
                        statut='echec',
                        raison_echec=f"Tentative avec ancien employee_id: {employee_id}",
                        adresse_ip=request.remote_addr,
                        source_type=source,
                        details={'employee_id': employee_id, 'reason': 'OLD_ID', 'method': 'VOICE'}
                    )
                    log_entry.enregistrer()
                
                db.session.commit()
                raise AuthenticationError(f"❌ {details.get('message', 'Employee ID invalide')}")
            
            user = User.query.filter_by(id=details.get('user_id')).first()
            identifier = f"emp_id:{employee_id}"
        
        # Priorité 2: email (clients web/autre)
        elif 'email' in data and data['email']:
            email = data['email'].lower()
            user = User.query.filter_by(email=email).first()
            identifier = f"email:{email}"

        # Priorité 3: user_id UUID direct (Door-System)
        elif 'user_id' in data and data['user_id']:
            user = User.query.get(data['user_id'])
            identifier = f"user_id:{str(data['user_id'])[:8]}"

        else:
            raise ValidationError("employee_id, email ou user_id requis")

        # Log de tentative
        login_log = LoginLog(
            email=user.email if user else data.get('email', ''),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            success=False,
            method='VOICE'
        )
        
        if not user or not user.is_active:
            db.session.add(login_log)
            db.session.commit()
            raise AuthenticationError("Utilisateur non trouvé ou désactivé")
        
        # ========== VÉRIFICATION BIOMÉTRIQUE ==========
        # Décoder l'audio
        try:
            audio_bytes = base64.b64decode(data['audio_data'])
            audio_file = io.BytesIO(audio_bytes)
        except Exception as e:
            raise ValidationError(f"Erreur décodage audio: {e}")
        
        # Extraire les caractéristiques
        provided_encoding = biometric_service.extract_voice_features(audio_file)
        
        if provided_encoding is None:
            db.session.add(login_log)
            db.session.commit()
            raise ValidationError("Impossible d'extraire les caractéristiques vocales")
        
        # Récupérer les templates
        from models.biometric import TemplateBiometrique
        templates = TemplateBiometrique.query.filter_by(
            user_id=user.id,
            type_biometrique='VOICE'
        ).all()
        
        if not templates:
            db.session.add(login_log)
            db.session.commit()
            raise AuthenticationError("Aucune voix enregistrée")
        
        # Vérifier
        best_similarity = 0
        matched = False
        
        for template in templates:
            stored = np.array(template.template_data, dtype=np.float32)
            similarity = float(1.0 - cosine_distance(stored, provided_encoding))

            if similarity > best_similarity:
                best_similarity = similarity
                if similarity >= BiometricService.VOICE_THRESHOLD:
                    matched = True
                    template.date_derniere_utilisation = datetime.now()
        
        if not matched:
            db.session.add(login_log)
            db.session.commit()
            
            # Log d'échec
            log_entry = LogAcces(
                type_acces='auth',
                statut='echec',
                raison_echec=f"Reconnaissance vocale échouée (similarité: {best_similarity:.2f})",
                adresse_ip=request.remote_addr,
                utilisateur_id=user.id,
                source_type=source,
                details={'similarity': best_similarity, 'identifier': identifier, 'method': 'VOICE'}
            )
            log_entry.enregistrer()
            
            raise AuthenticationError("Reconnaissance vocale échouée")
        
        # ========== AUTHENTIFICATION RÉUSSIE ==========
        # Créer session
        login_log.success = True
        db.session.add(login_log)
        
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_type='bearer',
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            auth_method='VOICE'
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Log succès
        log_entry = LogAcces(
            type_acces='auth',
            statut='succes',
            adresse_ip=request.remote_addr,
            utilisateur_id=user.id,
            source_type=source,
            details={'similarity': best_similarity, 'identifier': identifier, 'method': 'VOICE', 'phrase_id': phrase_id}
        )
        log_entry.enregistrer()
        
        log_audit(
            user_id=user.id,
            action='AUTHENTICATION',
            resource='user_session',
            resource_id=session.id,
            details={'method': 'VOICE', 'similarity': best_similarity, 'source': source, 'phrase_id': phrase_id},
            status='SUCCESS'
        )
        
        return jsonify({
            'success': True,
            'matched': True,
            'similarity': round(best_similarity, 4),
            'token': session.id,
            'phrase_id': phrase_id,
            'user': {
                'id': user.id,
                'employee_id': user.employee_id,
                'email': user.email,
                'nom': user.nom,
                'prenom': user.prenom,
                'role': user.role
            },
            'message': 'Authentification par voix réussie ✅'
        }), 200
    
    except (ValidationError, AuthenticationError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401
    except Exception as e:
        logger.error(f"Erreur vérification vocale: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


# ============================================================
# DÉTECTION DE VIVACITÉ
# ============================================================

@facial_bp.route('/face/liveness', methods=['POST'])
def detect_liveness() -> Tuple[Dict, int]:
    """
    Détecter la vivacité (anti-spoofing) pour une image faciale
    
    POST /api/v1/auth/face/liveness
    Body:
        {
            "image_data": "base64_encoded_image",
            "email": "user@example.com"  # optionnel
        }
    
    Response:
        {
            "success": true,
            "is_live": true,
            "confidence": 0.98,
            "details": {
                "has_blink": true,
                "motion_detected": true,
                "spoof_score": 0.05
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'image_data' not in data:
            raise ValidationError("image_data requis")
        
        # Décoder l'image
        try:
            image_bytes = base64.b64decode(data['image_data'])
            image_file = io.BytesIO(image_bytes)
        except Exception as e:
            raise ValidationError(f"Erreur décodage image: {e}")
        
        # Détecter la vivacité
        liveness_result = biometric_service.detect_liveness(image_file)
        
        email = data.get('email', 'unknown')
        log_audit(
            user_id=email,
            action='LIVENESS_CHECK',
            resource='face_frame',
            details={
                'is_live': liveness_result.get('is_live'),
                'confidence': liveness_result.get('confidence'),
                'spoof_score': liveness_result.get('spoof_score')
            },
            status='SUCCESS'
        )
        
        return jsonify({
            'success': True,
            'is_live': liveness_result.get('is_live'),
            'confidence': round(liveness_result.get('confidence', 0), 4),
            'details': {
                'has_blink': liveness_result.get('has_blink'),
                'motion_detected': liveness_result.get('motion_detected'),
                'spoof_score': round(liveness_result.get('spoof_score', 0), 4)
            }
        }), 200
    
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Erreur détection vivacité: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


# ============================================================
# UTILITIES
# ============================================================

@facial_bp.route('/face/templates', methods=['GET'])
@token_required
def get_face_templates() -> Tuple[Dict, int]:
    """
    Récupérer les templates faciaux de l'utilisateur
    
    GET /api/v1/auth/face/templates
    Header: Authorization: Bearer <token>
    """
    try:
        user_id = g.user_id
        from models.biometric import TemplateBiometrique
        
        templates = TemplateBiometrique.query.filter_by(
            user_id=user_id,
            type_biometrique='FACE'
        ).all()
        
        return jsonify({
            'success': True,
            'count': len(templates),
            'templates': [{
                'id': t.id,
                'label': t.label,
                'created': t.date_creation.isoformat(),
                'last_used': t.date_derniere_utilisation.isoformat() if t.date_derniere_utilisation else None
            } for t in templates]
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur récupération templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@facial_bp.route('/face/templates/<template_id>', methods=['DELETE'])
@token_required
def delete_face_template(template_id: str) -> Tuple[Dict, int]:
    """
    Supprimer un template facial
    
    DELETE /api/v1/auth/face/templates/<template_id>
    """
    try:
        user_id = g.user_id
        from models.biometric import TemplateBiometrique
        
        template = TemplateBiometrique.query.filter_by(
            id=template_id,
            user_id=user_id,
            type_biometrique='FACE'
        ).first()
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Template non trouvé'
            }), 404
        
        db.session.delete(template)
        db.session.commit()
        
        log_audit(
            user_id=user_id,
            action='FACE_TEMPLATE_DELETED',
            resource='biometric_template',
            resource_id=template_id,
            status='SUCCESS'
        )
        
        return jsonify({
            'success': True,
            'message': 'Template supprimé'
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur suppression template: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


# ============================================================
# ENREGISTREMENT DU BLUEPRINT
# ============================================================
# À utiliser dans app.py:
# from api.v1.facial_auth import facial_bp
# app.register_blueprint(facial_bp)
