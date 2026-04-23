"""
Routes API pour les logs d'accès
GET    /api/v1/logs
GET    /api/v1/logs/<log_id>
GET    /api/v1/logs/user/<user_id>
"""

from flask import Blueprint, request, g
from datetime import datetime, timedelta
import logging

from core.database import db
from core.errors import ValidationError, NotFoundError
from api.middlewares.auth_middleware import token_required, admin_required
from api.response_handler import APIResponse

from models.log import LogAcces

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('', methods=['GET'])
@admin_required
def list_logs():
    """
    Lister les logs d'accès avec filtres
    
    GET /api/v1/logs?page=1&per_page=10&type_acces=poste&statut=succes&days=7
    Response: { status, code, timestamp, message, data: [logs...], meta: {...} }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        type_acces = request.args.get('type_acces')
        statut = request.args.get('statut')
        days = request.args.get('days', 30, type=int)
        user_id = request.args.get('user_id')
        
        # Limiter per_page
        per_page = min(per_page, 100)
        
        # Filtrer par date
        since = datetime.utcnow() - timedelta(days=days)
        query = LogAcces.query.filter(LogAcces.date_heure >= since)
        
        # Filtres additionnels
        if type_acces:
            query = query.filter_by(type_acces=type_acces)
        if statut:
            query = query.filter_by(statut=statut)
        if user_id:
            query = query.filter_by(utilisateur_id=user_id)
        
        # Trier par date décroissante
        query = query.order_by(LogAcces.date_heure.desc())
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page)
        
        logs_data = [log.to_dict() for log in paginated.items]
        
        return APIResponse.paginated(
            logs_data,
            paginated.total,
            page,
            per_page,
            "Logs récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur listage logs: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération des logs",
            error_code="LIST_LOGS_ERROR",
            status_code=500
        )


@logs_bp.route('/<log_id>', methods=['GET'])
@admin_required
def get_log(log_id):
    """
    Récupérer un log spécifique
    
    GET /api/v1/logs/<log_id>
    Response: { status, code, timestamp, message, data: {log...} }
    """
    try:
        log = LogAcces.query.get(log_id)
        if not log:
            return APIResponse.error(
                "Log non trouvé",
                error_code="LOG_NOT_FOUND",
                status_code=404
            )
        
        return APIResponse.success(
            log.to_dict(),
            "Log récupéré avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération log {log_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_LOG_ERROR",
            status_code=500
        )


@logs_bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_user_logs(user_id):
    """
    Récupérer les logs d'un utilisateur
    
    GET /api/v1/logs/user/<user_id>
    Response: { status, code, timestamp, message, data: [logs...], meta: {...} }
    """
    try:
        # Vérifier permissions (self ou admin)
        if g.user_id != user_id and g.user_role not in ['admin', 'super_admin']:
            return APIResponse.error(
                "Accès refusé",
                error_code="ACCESS_DENIED",
                status_code=403
            )
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        days = request.args.get('days', 30, type=int)
        
        per_page = min(per_page, 100)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = LogAcces.query.filter(
            LogAcces.utilisateur_id == user_id,
            LogAcces.date_heure >= since
        ).order_by(LogAcces.date_heure.desc())
        
        paginated = query.paginate(page=page, per_page=per_page)
        logs_data = [log.to_dict() for log in paginated.items]
        
        return APIResponse.paginated(
            logs_data,
            paginated.total,
            page,
            per_page,
            "Logs utilisateur récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération logs utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_USER_LOGS_ERROR",
            status_code=500
        )


@logs_bp.route('/stats', methods=['GET'])
@admin_required
def get_logs_stats():
    """
    Récupérer les statistiques sur les logs
    
    GET /api/v1/logs/stats?days=7
    Response: { status, code, timestamp, message, data: {stats...} }
    """
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        total_logs = LogAcces.query.filter(LogAcces.date_heure >= since).count()
        success_logs = LogAcces.query.filter(
            LogAcces.date_heure >= since,
            LogAcces.statut == 'succes'
        ).count()
        failure_logs = total_logs - success_logs
        success_rate = (success_logs / total_logs * 100) if total_logs > 0 else 0
        
        stats = {
            'total_logs': total_logs,
            'success_logs': success_logs,
            'failure_logs': failure_logs,
            'success_rate': round(success_rate, 2),
            'period_days': days,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(
            stats,
            "Statistiques des logs récupérées avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur statistiques logs: {e}")
        return APIResponse.error(
            "Erreur lors du calcul des statistiques",
            error_code="STATS_ERROR",
            status_code=500
        )


# ============================================================
# EXPORT LOGS - JSON/CSV/PDF
# ============================================================

@logs_bp.route('/export', methods=['POST'])
@admin_required
def export_logs():
    """
    Exporter les logs d'accès en JSON, CSV ou PDF
    
    POST /api/v1/logs/export
    Body: {
        "format": "json|csv|pdf",
        "days": 7,
        "type_acces": "poste|porte|auth|config" (optionnel),
        "statut": "succes|echec" (optionnel),
        "user_id": "uuid" (optionnel)
    }
    
    Response: Fichier téléchargeable
    """
    try:
        from flask import send_file
        import json
        import csv
        import io
        from datetime import date
        
        data = request.get_json() or {}
        
        # Validation des paramètres
        export_format = data.get('format', 'json').lower()
        if export_format not in ['json', 'csv', 'pdf']:
            return APIResponse.error(
                "Format invalide. Valeurs acceptées: json, csv, pdf",
                error_code="INVALID_FORMAT",
                status_code=400
            )
        
        days = data.get('days', 7)
        if not isinstance(days, int) or days < 1 or days > 365:
            return APIResponse.error(
                "days doit être entre 1 et 365",
                error_code="INVALID_DAYS",
                status_code=400
            )
        
        # Filtres de sécurité
        since = datetime.utcnow() - timedelta(days=days)
        query = LogAcces.query.filter(LogAcces.date_heure >= since)
        
        # Filtres optionnels
        type_acces = data.get('type_acces')
        if type_acces and type_acces in ['poste', 'porte', 'auth', 'config']:
            query = query.filter_by(type_acces=type_acces)
        
        statut = data.get('statut')
        if statut and statut in ['succes', 'echec']:
            query = query.filter_by(statut=statut)
        
        user_id = data.get('user_id')
        if user_id:
            query = query.filter_by(utilisateur_id=user_id)
        
        # Trier par date décroissante
        logs = query.order_by(LogAcces.date_heure.desc()).all()
        
        if not logs:
            return APIResponse.error(
                "Aucun log trouvé pour les critères spécifiés",
                error_code="NO_LOGS_FOUND",
                status_code=404
            )
        
        # Log d'audit (OWASP A09 - Logging & Monitoring)
        logger.info(f"Export {export_format.upper()} - {len(logs)} logs par admin {g.user_id}")
        
        # Génération selon format
        if export_format == 'json':
            logs_data = [log.to_dict() for log in logs]
            content = json.dumps(logs_data, indent=2, default=str)
            filename = f"logs_export_{date.today().isoformat()}.json"
            mimetype = 'application/json'
        
        elif export_format == 'csv':
            output = io.StringIO()
            
            if logs:
                fieldnames = logs[0].to_dict().keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for log in logs:
                    # Sanitize pour éviter les injections CSV (OWASP A03 - Injection)
                    row = log.to_dict()
                    row = {k: str(v).replace(',', ' ').replace('\n', ' ') for k, v in row.items()}
                    writer.writerow(row)
            
            content = output.getvalue()
            filename = f"logs_export_{date.today().isoformat()}.csv"
            mimetype = 'text/csv'
        
        elif export_format == 'pdf':
            # Génération PDF avec reportlab (sécurisé contre les injections)
            try:
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.units import inch
                from reportlab.lib import colors
                
                output = io.BytesIO()
                doc = SimpleDocTemplate(output, pagesize=A4, topMargin=0.5*inch)
                elements = []
                
                # Titre
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.HexColor('#4f46e5'),
                    spaceAfter=30,
                    alignment=1
                )
                
                elements.append(Paragraph("Rapport d'Accès - BioAccess Secure", title_style))
                elements.append(Spacer(1, 0.3*inch))
                
                # Informations du rapport
                info_style = ParagraphStyle(
                    'Info',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.grey
                )
                
                elements.append(Paragraph(
                    f"Généré le: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}", 
                    info_style
                ))
                elements.append(Paragraph(
                    f"Période: {since.strftime('%d/%m/%Y')} au {datetime.utcnow().strftime('%d/%m/%Y')}", 
                    info_style
                ))
                elements.append(Paragraph(
                    f"Total enregistrements: {len(logs)}", 
                    info_style
                ))
                elements.append(Spacer(1, 0.2*inch))
                
                # Tableau des logs (limiter à 50 premières lignes pour perf)
                table_data = [['Date', 'Type', 'Statut', 'Utilisateur', 'IP']]
                
                for log in logs[:50]:
                    log_dict = log.to_dict()
                    table_data.append([
                        log_dict.get('date_heure', '')[:19],
                        log_dict.get('type_acces', '')[:20],
                        log_dict.get('statut', '')[:10],
                        log_dict.get('utilisateur_id', '')[:12],
                        log_dict.get('adresse_ip', '')
                    ])
                
                # Ajouter note si données tronquées
                if len(logs) > 50:
                    table_data.append(['...', f'et {len(logs) - 50} autres', '...', '...', '...'])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                ]))
                
                elements.append(table)
                
                # Build PDF
                doc.build(elements)
                content = output.getvalue()
                filename = f"logs_export_{date.today().isoformat()}.pdf"
                mimetype = 'application/pdf'
            
            except ImportError:
                logger.warning("reportlab non installé pour export PDF")
                return APIResponse.error(
                    "Export PDF non disponible - reportlab manquant",
                    error_code="PDF_UNAVAILABLE",
                    status_code=501
                )
        
        # Envoyer le fichier avec headers de sécurité
        file_data = io.BytesIO(content.encode('utf-8')) if isinstance(content, str) else io.BytesIO(content)
        
        response = send_file(
            file_data,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
        # Headers de sécurité pour le téléchargement (OWASP A06 - Misconfiguration)
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        
        return response
    
    except Exception as e:
        logger.error(f"Erreur export logs: {e}", exc_info=True)
        return APIResponse.error(
            "Erreur lors de l'export des logs",
            error_code="EXPORT_ERROR",
            status_code=500
        )


@logs_bp.route('/verify', methods=['GET'])
@admin_required
def verify_logs_integrity():
    """
    Vérifier l'intégrité de la chaîne de hashes des logs (immutabilité)
    
    GET /api/v1/logs/verify?days=7
    Response: {
        "status": "ok|compromised",
        "verified_count": 1000,
        "compromised_count": 0,
        "details": {...}
    }
    """
    try:
        import hashlib
        
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        logs = LogAcces.query.filter(
            LogAcces.date_heure >= since
        ).order_by(LogAcces.date_heure.asc()).all()
        
        verified_count = 0
        compromised_count = 0
        compromised_logs = []
        
        # Vérifier la chaîne de hash (OWASP A08 - Software Integrity Failures)
        for i, log in enumerate(logs):
            if not log.hash_actuel:
                continue
            
            # Reconstituer le hash attendu
            log_str = f"{log.date_heure}|{log.type_acces}|{log.statut}|{log.utilisateur_id or ''}|{log.adresse_ip or ''}"
            
            if i > 0 and logs[i-1].hash_actuel:
                # Hash chaîné (hash actuel du log précédent + données actuelles)
                hash_input = f"{logs[i-1].hash_actuel}|{log_str}".encode('utf-8')
            else:
                # Premier log
                hash_input = log_str.encode('utf-8')
            
            expected_hash = hashlib.sha256(hash_input).hexdigest()
            
            if log.hash_actuel == expected_hash:
                verified_count += 1
            else:
                compromised_count += 1
                compromised_logs.append({
                    'log_id': log.id,
                    'date': log.date_heure.isoformat(),
                    'expected_hash': expected_hash[:16] + '...',
                    'actual_hash': log.hash_actuel[:16] + '...'
                })
        
        # Log d'audit en cas de compromis
        if compromised_count > 0:
            logger.error(f"⚠️ COMPROMIS DÉTECTÉ: {compromised_count} logs altérés par {g.user_id}")
        
        status = 'compromised' if compromised_count > 0 else 'ok'
        
        return APIResponse.success({
            'status': status,
            'verified_count': verified_count,
            'compromised_count': compromised_count,
            'period_days': days,
            'compromised_logs': compromised_logs[:10],  # Top 10 seulement
            'total_checked': len(logs),
            'integrity_score': round((verified_count / len(logs) * 100) if logs else 0, 2)
        }, f"Vérification intégrité terminée - {verified_count}/{len(logs)} logs valides")
    
    except Exception as e:
        logger.error(f"Erreur vérification intégrité: {e}", exc_info=True)
        return APIResponse.error(
            "Erreur lors de la vérification d'intégrité",
            error_code="INTEGRITY_CHECK_ERROR",
            status_code=500
        )

