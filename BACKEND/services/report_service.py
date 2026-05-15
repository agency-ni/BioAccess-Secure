"""
Service de génération de rapports
"""

from models.log import LogAcces
from models.user import User
from models.report import Rapport
from core.database import db
from datetime import datetime, timedelta
import json
import csv
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import logging

logger = logging.getLogger(__name__)

class ReportService:
    """Service de génération de rapports"""
    
    @staticmethod
    def generate_daily_reports():
        """Génère les rapports quotidiens pour tous les admins"""
        from models.user import User
        
        yesterday = datetime.utcnow().date() - timedelta(days=1)
        reports = []
        
        admins = User.query.filter(User.role.in_(['admin', 'super_admin'])).all()
        
        for admin in admins:
            report = ReportService.generate_report(
                'journalier',
                yesterday,
                yesterday,
                admin.id
            )
            if report:
                reports.append(report)
        
        return reports
    
    @staticmethod
    def generate_report(report_type, start_date, end_date, generator_id):
        """Génère un rapport"""
        # Récupérer les logs
        logs = LogAcces.query.filter(
            LogAcces.date_heure >= start_date,
            LogAcces.date_heure <= end_date + timedelta(days=1)
        ).all()
        
        # Calculer les statistiques
        total = len(logs)
        success = len([l for l in logs if l.statut == 'succes'])
        failed = total - success
        
        success_rate = 0
        if total > 0:
            success_rate = round(success / total * 100, 1)
        
        # Par type
        poste_logs = [l for l in logs if l.type_acces == 'poste']
        porte_logs = [l for l in logs if l.type_acces == 'porte']
        
        # Par département
        from collections import defaultdict
        dept_stats = defaultdict(lambda: {'total': 0, 'success': 0})
        
        for log in logs:
            if log.utilisateur_id:
                user = db.session.get(User, log.utilisateur_id)
                if user and user.departement:
                    dept = user.departement
                    dept_stats[dept]['total'] += 1
                    if log.statut == 'succes':
                        dept_stats[dept]['success'] += 1
        
        dept_data = []
        for dept, stats in dept_stats.items():
            rate = 0
            if stats['total'] > 0:
                rate = round(stats['success'] / stats['total'] * 100, 1)
            dept_data.append({
                'departement': dept,
                'total': stats['total'],
                'success': stats['success'],
                'rate': rate
            })
        
        # Données du rapport
        data = {
            'type': report_type,
            'periode': {
                'debut': start_date.isoformat(),
                'fin': end_date.isoformat()
            },
            'generation': datetime.utcnow().isoformat(),
            'stats': {
                'total': total,
                'success': success,
                'failed': failed,
                'success_rate': success_rate,
                'poste': len(poste_logs),
                'porte': len(porte_logs)
            },
            'departements': dept_data,
            'recommandations': ReportService._generate_recommendations(dept_data)
        }
        
        # Créer le rapport
        report = Rapport(
            type=report_type,
            periode_debut=start_date,
            periode_fin=end_date,
            donnees=data,
            generateur_id=generator_id,
            titre=f"Rapport {report_type} {start_date} - {end_date}"
        )
        
        db.session.add(report)
        db.session.commit()
        
        # Ajouter les logs
        for log in logs:
            report.logs.append(log)
        
        db.session.commit()
        
        return report
    
    @staticmethod
    def export_to_pdf(report):
        """Exporte un rapport au format PDF"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Titre
        elements.append(Paragraph(report.titre, styles['Title']))
        elements.append(Paragraph(f"Généré le {report.date_generation}", styles['Normal']))
        elements.append(Paragraph("<br/><br/>", styles['Normal']))
        
        # Statistiques
        data = report.donnees
        stats = data['stats']
        
        stats_data = [
            ['Métrique', 'Valeur'],
            ['Total tentatives', str(stats['total'])],
            ['Succès', str(stats['success'])],
            ['Échecs', str(stats['failed'])],
            ['Taux de succès', f"{stats['success_rate']}%"],
            ['Accès postes', str(stats['poste'])],
            ['Accès portes', str(stats['porte'])]
        ]
        
        table = Table(stats_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        
        # Recommandations
        if data.get('recommandations'):
            elements.append(Paragraph("<br/><br/>Recommandations:", styles['Heading2']))
            for rec in data['recommandations']:
                elements.append(Paragraph(f"• {rec}", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def export_to_csv(report):
        """Exporte un rapport au format CSV"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-tête
        writer.writerow(['Type', 'Période début', 'Période fin', 'Généré le'])
        writer.writerow([
            report.type,
            report.periode_debut,
            report.periode_fin,
            report.date_generation
        ])
        writer.writerow([])
        
        # Statistiques
        stats = report.donnees['stats']
        writer.writerow(['Métrique', 'Valeur'])
        for key, value in stats.items():
            writer.writerow([key, value])
        
        writer.writerow([])
        
        # Départements
        writer.writerow(['Département', 'Total', 'Succès', 'Taux'])
        for dept in report.donnees['departements']:
            writer.writerow([
                dept['departement'],
                dept['total'],
                dept['success'],
                f"{dept['rate']}%"
            ])
        
        output.seek(0)
        return output.getvalue().encode('utf-8')
    
    @staticmethod
    def _generate_recommendations(dept_data):
        """Génère des recommandations basées sur les données"""
        recs = []
        
        for dept in dept_data:
            if dept['rate'] < 85:
                recs.append(
                    f"Le département {dept['departement']} a un taux de succès "
                    f"de {dept['rate']}%. Envisager une formation."
                )
        
        return recs