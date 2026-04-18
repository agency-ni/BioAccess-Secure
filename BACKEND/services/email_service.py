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
    
    @staticmethod
    def send_employee_id_email(user):
        """
        Envoie l'Employee ID à l'utilisateur pour l'authentification Desktop
        
        Format: XXXXXXXAAAA (ex: 1002218AAKH)
        L'utilisateur peut utiliser cet ID pour configurer son Desktop Client
        """
        subject = "🔐 Votre clé d'authentification BioAccess - Employee ID"
        
        body = f"""
Bonjour {user.prenom} {user.nom},

Votre clé d'authentification BioAccess Secure a été créée avec succès.

📌 VOTRE EMPLOYEE ID: {user.employee_id}

Cette clé vous permettra d'utiliser l'application Desktop BioAccess Secure.

COMMENT L'UTILISER:
1. Téléchargez l'application Desktop BioAccess depuis le portail
2. Lancez l'application et sélectionnez "Configuration"
3. Entrez votre Employee ID: {user.employee_id}
4. Enregistrez vos données biométriques (visage et/ou voix)
5. Vous pourrez alors vous authentifier via reconnaissance biométrique

SÉCURITÉ:
- Gardez votre Employee ID confidentiel
- Ne le partagez qu'avec votre administrateur système
- Si vous réinstallez l'application, contactez votre admin

BESOIN D'AIDE?
Contactez votre administrateur système ou l'équipe d'assistance.

Cordialement,
L'équipe BioAccess Secure
"""
        
        html = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4f46e5; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        .content {{ background: #f3f4f6; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .employee-id {{ 
            background: white; 
            border: 2px solid #4f46e5; 
            padding: 20px; 
            margin: 20px 0; 
            border-radius: 5px; 
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            color: #4f46e5;
        }}
        .steps {{ list-style: none; padding: 0; }}
        .steps li {{ 
            padding: 10px; 
            margin: 10px 0; 
            background: white; 
            border-left: 4px solid #4f46e5;
            padding-left: 15px;
        }}
        .security {{ background: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ color: #666; font-size: 12px; text-align: center; margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Votre clé d'authentification BioAccess</h1>
        </div>
        
        <p>Bonjour <strong>{user.prenom} {user.nom}</strong>,</p>
        
        <p>Votre clé d'authentification BioAccess Secure a été créée avec succès.</p>
        
        <div class="employee-id">
            {user.employee_id}
        </div>
        
        <p style="text-align: center; color: #666; font-size: 12px;">
            Cette clé vous permettra d'utiliser l'application Desktop BioAccess Secure
        </p>
        
        <div class="content">
            <h2>📱 Comment l'utiliser</h2>
            <ol class="steps">
                <li><strong>Étape 1:</strong> Téléchargez l'application Desktop BioAccess</li>
                <li><strong>Étape 2:</strong> Lancez l'application et allez à "Configuration"</li>
                <li><strong>Étape 3:</strong> Entrez votre Employee ID: <code style="background: #e5e7eb; padding: 5px;">{user.employee_id}</code></li>
                <li><strong>Étape 4:</strong> Enregistrez vos données biométriques (visage et/ou voix)</li>
                <li><strong>Étape 5:</strong> Authentifiez-vous via reconnaissance biométrique</li>
            </ol>
        </div>
        
        <div class="security">
            <h3>🔒 Sécurité</h3>
            <ul>
                <li>Gardez votre Employee ID confidentiel</li>
                <li>Ne le partagez qu'avec votre administrateur système</li>
                <li>Si vous réinstallez l'application, contactez votre admin</li>
            </ul>
        </div>
        
        <p><strong>Besoin d'aide?</strong><br>
        Contactez votre administrateur système ou l'équipe d'assistance.</p>
        
        <div class="footer">
            <p>© 2024 BioAccess Secure - Tous les droits réservés</p>
            <p>Cet email contient des informations confidentielles.</p>
        </div>
    </div>
</body>
</html>
"""
        
        EmailService.send(user.email, subject, body, html)