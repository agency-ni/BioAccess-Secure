"""
Service d'envoi d'emails
"""

from flask import current_app, render_template
from core.queue import celery_app
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Service d'envoi d'emails"""
    
    SMTP_HOST = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USER = 'noreply@bioaccess.com'
    SMTP_PASSWORD = 'password'
    
    @staticmethod
    def send(recipient, subject, body, html=None):
        """Envoie un email de manière asynchrone"""
        from services.tasks import send_email_async
        send_email_async.delay(recipient, subject, body, html)
    
    @staticmethod
    def send_sync(recipient, subject, body, html=None):
        """Envoie un email de manière synchrone"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = EmailService.SMTP_USER
            msg['To'] = recipient
            
            # Version texte
            msg.attach(MIMEText(body, 'plain'))
            
            # Version HTML
            if html:
                msg.attach(MIMEText(html, 'html'))
            
            # Envoyer
            server = smtplib.SMTP(EmailService.SMTP_HOST, EmailService.SMTP_PORT)
            server.starttls()
            server.login(EmailService.SMTP_USER, EmailService.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email envoyé à {recipient}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur envoi email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(user):
        """Envoie un email de bienvenue"""
        subject = "Bienvenue sur BioAccess Secure"
        body = f"""
        Bonjour {user.prenom},
        
        Votre compte BioAccess Secure a été créé avec succès.
        
        Vous pouvez vous connecter à l'adresse: https://app.bioaccess.com
        Votre email: {user.email}
        
        Cordialement,
        L'équipe BioAccess Secure
        """
        EmailService.send(user.email, subject, body)
    
    @staticmethod
    def send_password_reset(user, token):
        """Envoie un email de réinitialisation de mot de passe"""
        subject = "Réinitialisation de votre mot de passe"
        reset_link = f"https://app.bioaccess.com/reset-password?token={token}"
        
        body = f"""
        Bonjour {user.prenom},
        
        Vous avez demandé la réinitialisation de votre mot de passe.
        
        Cliquez sur le lien suivant (valable 1 heure):
        {reset_link}
        
        Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.
        
        Cordialement,
        L'équipe BioAccess Secure
        """
        
        html = f"""
        <h2>Réinitialisation de mot de passe</h2>
        <p>Bonjour {user.prenom},</p>
        <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
        <p><a href="{reset_link}">Cliquez ici pour réinitialiser</a></p>
        <p>Ce lien est valable 1 heure.</p>
        <p>Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
        """
        
        EmailService.send(user.email, subject, body, html)
    
    @staticmethod
    def send_alert_email(alert, user):
        """Envoie une alerte par email"""
        subject = f"[{alert.gravite.upper()}] Alerte BioAccess Secure"
        
        body = f"""
        Une nouvelle alerte a été générée:
        
        Type: {alert.type}
        Gravité: {alert.gravite}
        Message: {alert.message}
        Date: {alert.date_creation}
        
        Connectez-vous pour plus de détails.
        """
        
        EmailService.send(user.email, subject, body)
    
    @staticmethod
    def send_report_email(report, recipient):
        """Envoie un rapport par email"""
        subject = f"Rapport BioAccess Secure - {report.type}"
        
        body = f"""
        Votre rapport {report.type} pour la période
        du {report.periode_debut} au {report.periode_fin} est disponible.
        
        Connectez-vous pour le télécharger.
        """
        
        EmailService.send(recipient, subject, body)