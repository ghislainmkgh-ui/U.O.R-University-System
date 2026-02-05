"""Service de notification par email et WhatsApp"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import EMAIL_SERVICE, EMAIL_ADDRESS, EMAIL_PASSWORD

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour envoyer des notifications"""
    
    def __init__(self):
        self.email_address = EMAIL_ADDRESS
        self.email_password = EMAIL_PASSWORD
    
    def send_payment_notification(self, student_email: str, student_name: str,
                                 amount_paid: float, remaining_amount: float,
                                 threshold: float) -> bool:
        """
        Envoie une notification de paiement par email
        
        Args:
            student_email: Email de l'étudiant
            student_name: Nom complet de l'étudiant
            amount_paid: Montant déjà payé
            remaining_amount: Montant restant
            threshold: Seuil requis
            
        Returns:
            True si l'email est envoyé avec succès
        """
        try:
            subject = "Notification de Paiement - U.O.R"
            body = f"""
            Bonjour {student_name},
            
            Votre paiement a été reçu avec succès.
            
            Montant payé: {amount_paid}
            Seuil requis: {threshold}
            Montant restant: {remaining_amount}
            
            Cordialement,
            U.O.R - Système de Contrôle d'Accès
            """
            
            return self._send_email(student_email, subject, body)
            
        except Exception as e:
            logger.error(f"Error preparing payment notification: {e}")
            return False
    
    def send_access_denied_notification(self, student_email: str, student_name: str,
                                       reason: str) -> bool:
        """Envoie une notification d'accès refusé"""
        try:
            subject = "Accès Refusé - U.O.R"
            body = f"""
            Bonjour {student_name},
            
            Votre tentative d'accès à la salle d'examen a été refusée.
            Raison: {reason}
            
            Veuillez contacter l'administration pour plus d'informations.
            
            Cordialement,
            U.O.R - Système de Contrôle d'Accès
            """
            
            return self._send_email(student_email, subject, body)
            
        except Exception as e:
            logger.error(f"Error preparing access denied notification: {e}")
            return False
    
    def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Envoie un email"""
        try:
            if not self.email_address or not self.email_password:
                logger.warning("Email service not configured")
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Configurer le serveur SMTP
            smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
            smtp_server.starttls()
            smtp_server.login(self.email_address, self.email_password)
            
            smtp_server.send_message(msg)
            smtp_server.quit()
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
