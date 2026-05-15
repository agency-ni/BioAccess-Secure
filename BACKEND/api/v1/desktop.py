"""
API Desktop — Enrôlement biométrique déclenché depuis le dashboard admin
Routes:
  POST /api/v1/desktop/announce               — Desktop s'annonce (mac, ip, hostname)
  GET  /api/v1/desktop/machines               — Admin: liste des machines connues
  POST /api/v1/desktop/link                   — Admin: lie machine ↔ employé
  POST /api/v1/desktop/enrollment/trigger     — Admin déclenche un enrôlement
  GET  /api/v1/desktop/enrollment/poll        — Desktop poll: session en attente ?
  POST /api/v1/desktop/enrollment/submit      — Desktop envoie face frames + voix
  GET  /api/v1/desktop/enrollment/status      — Admin consulte le statut d'une session
"""

import uuid
import threading
import logging
import base64 as _b64
from datetime import datetime, timedelta
from core.lazy_import import lazy_module

# Chargés à la première soumission d'enrôlement, pas au démarrage
np  = lazy_module('numpy')
cv2 = lazy_module('cv2')
from flask import Blueprint, request, jsonify, g

from core.database import db
from api.middlewares.auth_middleware import token_required, admin_required
from models.access_point import PosteTravail
from models.user import User

logger = logging.getLogger(__name__)

desktop_bp = Blueprint('desktop', __name__, url_prefix='/desktop')

# ── Enrollment sessions en mémoire (dict TTL) ─────────────────────────────────
# Clé : session_key (UUID str)
# Valeur : {employee_id, employee_name, status, created_at, expires_at,
#            triggered_by, device_id}
_sessions: dict = {}
_lock = threading.Lock()
SESSION_TTL = 10  # minutes


def _purge_expired():
    now = datetime.utcnow()
    with _lock:
        for k in [k for k, s in _sessions.items() if s['expires_at'] < now]:
            del _sessions[k]


def _get_or_create_poste(mac: str, ip: str, hostname: str,
                         systeme: str, os_version: str) -> PosteTravail:
    poste = PosteTravail.query.filter_by(mac_address=mac).first()
    if not poste:
        poste = PosteTravail(
            nom=hostname or 'Desktop',
            adresse_ip=ip or None,
            systeme=systeme or 'Windows',
            mac_address=mac,
            os_version=os_version,
            last_seen=datetime.utcnow(),
            statut='actif',
        )
        db.session.add(poste)
    else:
        poste.adresse_ip = ip or poste.adresse_ip
        poste.last_seen = datetime.utcnow()
        poste.statut = 'actif'
        if os_version:
            poste.os_version = os_version
    db.session.commit()
    return poste


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/desktop/announce
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/announce', methods=['POST'])
def announce():
    """
    Le client Desktop s'annonce à chaque démarrage.
    Body: {mac_address, hostname, ip?, systeme?, os_version?}
    Returns: {machine_id, employee_id, device_id, linked}
    """
    try:
        data = request.get_json(silent=True) or {}
        mac = (data.get('mac_address') or '').upper().replace('-', ':').strip()
        if not mac:
            return jsonify({'success': False, 'error': 'mac_address requis'}), 400

        ip = data.get('ip') or request.remote_addr
        hostname = data.get('hostname', 'Desktop')
        systeme = data.get('systeme', 'Windows')
        os_version = data.get('os_version', '')

        poste = _get_or_create_poste(mac, ip, hostname, systeme, os_version)

        # Récupérer la clé desk de l'employé si lié
        emp = db.session.get(User, poste.employe_id) if poste.employe_id else None
        return jsonify({
            'success':       True,
            'machine_id':    poste.id,
            'device_id':     poste.id,
            'employee_uuid': poste.employe_id,           # UUID interne
            'employee_id':   emp.employee_id if emp else None,  # clé auth desktop (ex: 2421434JTKO)
            'employee_name': f"{emp.prenom} {emp.nom}" if emp else None,
            'linked':        poste.employe_id is not None,
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur announce: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/desktop/machines    (admin)
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/machines', methods=['GET'])
@admin_required
def list_machines():
    """Liste toutes les machines connues, avec l'employé lié (si existant)."""
    try:
        postes = PosteTravail.query.order_by(PosteTravail.last_seen.desc()).all()
        result = []
        for p in postes:
            emp = db.session.get(User, p.employe_id) if p.employe_id else None
            result.append({
                'machine_id': p.id,
                'nom': p.nom,
                'ip': p.adresse_ip,
                'mac': p.mac_address,
                'systeme': p.systeme,
                'os_version': p.os_version,
                'statut': p.statut,
                'last_seen': p.last_seen.isoformat() if p.last_seen else None,
                'employee_id': p.employe_id,
                'employee_name': f"{emp.prenom} {emp.nom}" if emp else None,
                'employee_email': emp.email if emp else None,
            })
        return jsonify({'success': True, 'machines': result, 'count': len(result)})
    except Exception as e:
        logger.error(f"Erreur list_machines: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/desktop/link    (admin)
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/link', methods=['POST'])
@admin_required
def link_machine():
    """
    Lie une machine à un employé.
    Body: {machine_id, employee_id}
    """
    try:
        data = request.get_json(silent=True) or {}
        machine_id = data.get('machine_id')
        employee_id = data.get('employee_id')
        if not machine_id or not employee_id:
            return jsonify({'success': False, 'error': 'machine_id et employee_id requis'}), 400

        poste = db.session.get(PosteTravail, machine_id)
        if not poste:
            return jsonify({'success': False, 'error': 'Machine introuvable'}), 404

        user = db.session.get(User, employee_id)
        if not user:
            return jsonify({'success': False, 'error': 'Employé introuvable'}), 404

        poste.employe_id = employee_id
        db.session.commit()
        logger.info(f"Machine {machine_id} liée à l'employé {employee_id} ({user.email})")
        return jsonify({
            'success': True,
            'message': f"Machine liée à {user.prenom} {user.nom}",
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur link_machine: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/desktop/enrollment/trigger    (admin)
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/enrollment/trigger', methods=['POST'])
@admin_required
def trigger_enrollment():
    """
    L'admin déclenche l'enrôlement biométrique pour un employé.
    Body: {employee_id}
    Returns: {session_key, expires_at, employee_name}
    """
    try:
        data = request.get_json(silent=True) or {}
        employee_id = data.get('employee_id')
        if not employee_id:
            return jsonify({'success': False, 'error': 'employee_id requis'}), 400

        user = db.session.get(User, employee_id)
        if not user:
            return jsonify({'success': False, 'error': 'Employé introuvable'}), 404

        # emp_desk_key = clé auth desktop (ex: 2421434JTKO), utilisée par le poll du client
        emp_desk_key = user.employee_id or employee_id

        _purge_expired()

        # Retourner la session déjà active si elle existe
        with _lock:
            for key, sess in _sessions.items():
                if sess['employee_id'] == emp_desk_key and sess['status'] == 'pending':
                    return jsonify({
                        'success': True,
                        'session_key': key,
                        'expires_at': sess['expires_at'].isoformat(),
                        'employee_name': sess['employee_name'],
                        'message': 'Session déjà en attente',
                    })

        session_key = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=SESSION_TTL)
        with _lock:
            _sessions[session_key] = {
                'employee_id':   emp_desk_key,  # clé poll desktop (ex: 2421434JTKO)
                'employee_uuid': employee_id,   # UUID pour opérations BDD
                'employee_name': f"{user.prenom} {user.nom}",
                'status': 'pending',
                'created_at': datetime.utcnow(),
                'expires_at': expires_at,
                'triggered_by': g.user_id,
                'device_id': None,
            }

        logger.info(f"Enrôlement déclenché pour {employee_id} — session {session_key}")
        return jsonify({
            'success': True,
            'session_key': session_key,
            'expires_at': expires_at.isoformat(),
            'employee_name': f"{user.prenom} {user.nom}",
            'message': 'Enrôlement déclenché — le client desktop va démarrer',
        })
    except Exception as e:
        logger.error(f"Erreur trigger_enrollment: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/desktop/enrollment/poll?employee_id=<id>
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/enrollment/poll', methods=['GET'])
def poll_enrollment():
    """
    Le client Desktop vérifie s'il y a un enrôlement en attente pour cet employé.
    Query: employee_id
    Returns: {pending, session_key?, employee_name?, expires_at?}
    """
    try:
        employee_id = request.args.get('employee_id')
        if not employee_id:
            return jsonify({'success': False, 'error': 'employee_id requis'}), 400

        _purge_expired()

        with _lock:
            for key, sess in _sessions.items():
                if sess['employee_id'] == employee_id and sess['status'] == 'pending':
                    return jsonify({
                        'success': True,
                        'pending': True,
                        'session_key': key,
                        'employee_name': sess['employee_name'],
                        'expires_at': sess['expires_at'].isoformat(),
                    })

        return jsonify({'success': True, 'pending': False})
    except Exception as e:
        logger.error(f"Erreur poll_enrollment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/desktop/enrollment/submit
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/enrollment/submit', methods=['POST'])
def submit_enrollment():
    """
    Le client Desktop envoie les données biométriques captées.
    Body: {
        session_key:         str,
        mac_address:         str,
        face_frames:         [base64_str, ...],   # 1–5 frames JPEG/PNG
        voice_base64:        str | null,           # audio WAV en base64
        liveness_confirmed:  bool,
        ear_min:             float | null
    }
    Returns: {device_id, employee_id, face_ok, voice_ok, face_enrolled, message}
    """
    session_key = None
    try:
        data = request.get_json(silent=True) or {}
        session_key = data.get('session_key')
        mac = (data.get('mac_address') or '').upper().replace('-', ':').strip()
        face_frames: list = data.get('face_frames') or []
        voice_b64: str | None = data.get('voice_base64')
        liveness_confirmed = bool(data.get('liveness_confirmed', False))

        if not session_key:
            return jsonify({'success': False, 'error': 'session_key requis'}), 400

        # ── Valider la session ────────────────────────────────────────────
        with _lock:
            sess = _sessions.get(session_key)
            if not sess:
                return jsonify({'success': False, 'error': 'Session introuvable ou expirée'}), 404
            if sess['status'] != 'pending':
                return jsonify({'success': False,
                                'error': f"Session déjà en statut '{sess['status']}'"}), 409
            if sess['expires_at'] < datetime.utcnow():
                return jsonify({'success': False, 'error': 'Session expirée'}), 410
            sess['status'] = 'processing'

        employee_id   = sess['employee_id']          # clé desk (ex: 2421434JTKO)
        employee_uuid = sess.get('employee_uuid', employee_id)  # UUID BDD
        face_ok = False
        voice_ok = False
        face_enrolled = 0
        errors = []

        # ── Traitement face frames ────────────────────────────────────────
        if face_frames:
            from services.biometric_service import BiometricService
            from models.biometric import TemplateBiometrique

            for i, frame_b64 in enumerate(face_frames[:5]):
                try:
                    raw = frame_b64
                    if ',' in raw:
                        raw = raw.split(',', 1)[1]
                    img_bytes = _b64.b64decode(raw)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        errors.append(f"Frame {i+1}: image invalide")
                        continue
                    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    encoding, quality, _ = BiometricService.extract_face_features(rgb)
                    if encoding is None:
                        errors.append(f"Frame {i+1}: aucun visage détecté")
                        continue
                    tpl = TemplateBiometrique(
                        type_biometrique='FACE',
                        template_data=encoding.tolist(),
                        user_id=employee_uuid,
                        quality_score=quality,
                        label=f"Desktop frame {i+1} — {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}",
                        is_active=True,
                    )
                    db.session.add(tpl)
                    face_enrolled += 1
                except Exception as ex:
                    errors.append(f"Frame {i+1}: {ex}")

            if face_enrolled > 0:
                db.session.commit()
                face_ok = True

        # ── Traitement voix ───────────────────────────────────────────────
        if voice_b64:
            try:
                raw_v = voice_b64
                if ',' in raw_v:
                    raw_v = raw_v.split(',', 1)[1]
                audio_bytes = _b64.b64decode(raw_v)
                from services.biometric_service import BiometricService
                tpl = BiometricService.process_voice_sample(audio_bytes, employee_uuid)
                if tpl:
                    voice_ok = True
            except Exception as ex:
                errors.append(f"Voix: {ex}")
                logger.warning(f"Erreur traitement voix: {ex}")

        # ── Mettre à jour / créer PosteTravail ────────────────────────────
        device_id = None
        if mac:
            try:
                poste = PosteTravail.query.filter_by(mac_address=mac).first()
                if not poste:
                    poste = PosteTravail(
                        nom='Desktop employé',
                        adresse_ip=request.remote_addr,
                        mac_address=mac,
                        employe_id=employee_uuid,
                        last_seen=datetime.utcnow(),
                        statut='actif',
                    )
                    db.session.add(poste)
                    db.session.commit()
                else:
                    if poste.employe_id != employee_uuid:
                        poste.employe_id = employee_uuid
                    poste.last_seen = datetime.utcnow()
                    db.session.commit()
                device_id = poste.id
            except Exception as ex:
                logger.warning(f"Erreur mise à jour PosteTravail: {ex}")
                db.session.rollback()

        # ── Finaliser la session ──────────────────────────────────────────
        overall_ok = face_ok or voice_ok
        with _lock:
            if session_key in _sessions:
                _sessions[session_key]['status'] = 'done' if overall_ok else 'error'
                _sessions[session_key]['device_id'] = device_id

        if not overall_ok:
            return jsonify({
                'success': False,
                'error': 'Aucun template biométrique enregistré',
                'errors': errors,
            }), 422

        logger.info(f"Enrôlement desktop réussi — employé {employee_id}, "
                    f"visages={face_enrolled}, voix={voice_ok}, device_id={device_id}")
        return jsonify({
            'success': True,
            'device_id': device_id,
            'employee_id': employee_id,
            'face_ok': face_ok,
            'face_enrolled': face_enrolled,
            'voice_ok': voice_ok,
            'liveness_confirmed': liveness_confirmed,
            'errors': errors,
            'message': (f"Enrôlement réussi — {face_enrolled} visage(s)"
                        f"{', voix enregistrée' if voice_ok else ''}"),
        })

    except Exception as e:
        db.session.rollback()
        if session_key:
            with _lock:
                if session_key in _sessions:
                    _sessions[session_key]['status'] = 'error'
        logger.error(f"Erreur submit_enrollment: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/desktop/enrollment/status?session_key=<key>    (token)
# ─────────────────────────────────────────────────────────────────────────────
@desktop_bp.route('/enrollment/status', methods=['GET'])
@token_required
def enrollment_status():
    """Permet à l'admin de suivre le statut d'une session d'enrôlement."""
    try:
        session_key = request.args.get('session_key')
        if not session_key:
            return jsonify({'success': False, 'error': 'session_key requis'}), 400

        with _lock:
            sess = _sessions.get(session_key)

        if not sess:
            return jsonify({'success': False, 'error': 'Session introuvable'}), 404

        return jsonify({
            'success': True,
            'session_key': session_key,
            'status': sess['status'],
            'employee_id': sess['employee_id'],
            'employee_name': sess['employee_name'],
            'device_id': sess.get('device_id'),
            'created_at': sess['created_at'].isoformat(),
            'expires_at': sess['expires_at'].isoformat(),
        })
    except Exception as e:
        logger.error(f"Erreur enrollment_status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
