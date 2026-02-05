"""Service de notification par email et WhatsApp"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config.settings import EMAIL_SERVICE, EMAIL_ADDRESS, EMAIL_PASSWORD, WHATSAPP_ACCOUNT_SID, WHATSAPP_AUTH_TOKEN, WHATSAPP_FROM

logger = logging.getLogger(__name__)


class NotificationService:
    """Service pour envoyer des notifications"""
    
    def __init__(self):
        self.email_address = EMAIL_ADDRESS
        self.email_password = EMAIL_PASSWORD
        self.whatsapp_sid = WHATSAPP_ACCOUNT_SID
        self.whatsapp_token = WHATSAPP_AUTH_TOKEN
        self.whatsapp_from = WHATSAPP_FROM
    
    def send_payment_notification(self, student_email: str, student_name: str,
                                 amount_paid: float, remaining_amount: float,
                                 threshold: float) -> bool:
        """Envoie une notification de paiement par email"""
        try:
            subject = "Notification de Paiement - U.O.R"
            body = f"""
Bonjour {student_name},

Votre paiement a été reçu avec succès.

Montant payé: {amount_paid:,.0f} FC
Seuil requis: {threshold:,.0f} FC
Montant restant: {remaining_amount:,.0f} FC

Cordialement,
U.O.R - Système de Contrôle d'Accès
            """.strip()
            
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
            """.strip()
            
            return self._send_email(student_email, subject, body)
            
        except Exception as e:
            logger.error(f"Error preparing access denied notification: {e}")
            return False

    def send_access_code_notification(self, student_email: str, student_phone: str,
                                      student_name: str, access_code: str,
                                      code_type: str, expires_at: str) -> bool:
        """Envoie le code d'accès au étudiant par email et WhatsApp"""
        try:
            validity_msg = ""
            if code_type == 'full':
                validity_msg = "Ce code est valable durant toutes les périodes d'examens de l'année académique."
            else:
                validity_msg = f"Ce code est valable jusqu'au {expires_at}."
            
            subject = "Votre code d'accès - U.O.R"
            body = f"""
Bonjour {student_name},

Félicitations! Votre code d'accès a été généré avec succès.

Code d'accès: {access_code}
{validity_msg}

Utilisez ce code pour accéder à la salle d'examen.

Cordialement,
U.O.R - Système de Contrôle d'Accès
            """.strip()
            
            whatsapp_msg = f"Bonjour {student_name}, votre code d'accès: {access_code}. {validity_msg}"
            
            email_ok = self._send_email(student_email, subject, body)
            whatsapp_ok = self._send_whatsapp(student_phone, whatsapp_msg)
            
            logger.info(f"Access code notification sent to {student_name} - Email: {email_ok}, WhatsApp: {whatsapp_ok}")
            return email_ok or whatsapp_ok
            
        except Exception as e:
            logger.error(f"Error preparing access code notification: {e}")
            return False

    def send_threshold_change_notification(self, student_email: str, student_phone: str,
                                          student_name: str, old_threshold: float, 
                                          new_threshold: float) -> bool:
        """Notifie l'étudiant du changement de seuil financier"""
        try:
            subject = "Mise à jour du seuil financier - Action requise - U.O.R"
            body = f"""
Bonjour {student_name},

Le seuil financier pour l'accès aux examens a été mis à jour.

Ancien seuil: {old_threshold:,.0f} FC
Nouveau seuil: {new_threshold:,.0f} FC

IMPORTANT: Si vous aviez un code d'accès temporaire (paiement partiel), celui-ci a été invalidé. 
Veuillez effectuer un nouveau paiement pour atteindre le nouveau seuil et obtenir un code valide.

Les étudiants ayant payé intégralement conservent leur code valable toute l'année.

Cordialement,
U.O.R - Système de Contrôle d'Accès
            """.strip()
            
            whatsapp_msg = f"Bonjour {student_name}, le seuil financier a changé de {old_threshold:,.0f} FC à {new_threshold:,.0f} FC. Votre code temporaire a été invalidé si applicable."
            
            email_ok = self._send_email(student_email, subject, body)
            whatsapp_ok = self._send_whatsapp(student_phone, whatsapp_msg)
            
            logger.info(f"Threshold change notification sent to {student_name} - Email: {email_ok}, WhatsApp: {whatsapp_ok}")
            return email_ok or whatsapp_ok
            
        except Exception as e:
            logger.error(f"Error preparing threshold change notification: {e}")
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

    def _send_whatsapp(self, student_phone: str, message: str) -> bool:
        """Envoie un message WhatsApp via Twilio"""
        try:
            if not student_phone:
                logger.warning("No phone number provided")
                return False
                
            if not self.whatsapp_sid or not self.whatsapp_token or not self.whatsapp_from:
                logger.warning("WhatsApp service not configured")
                return False

            try:
                from twilio.rest import Client
            except ImportError:
                logger.warning("Twilio library not installed. Install with: pip install twilio")
                return False

            client = Client(self.whatsapp_sid, self.whatsapp_token)
            
            # Send message using standard API (not content templates)
            msg = client.messages.create(
                body=message,
                from_=f"whatsapp:{self.whatsapp_from}",
                to=f"whatsapp:{student_phone}"
            )
            
            logger.info(f"WhatsApp sent successfully to {student_phone} (SID: {msg.sid})")
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp: {e}")
            return False

    def send_whatsapp_with_template(self, student_phone: str, template_sid: str, 
                                   template_variables: list = None) -> bool:
        """Envoie un message WhatsApp via template Twilio (pour messages pré-approuvés)"""
        try:
            if not student_phone or not template_sid:
                logger.warning("Phone or template_sid missing")
                return False
                
            if not self.whatsapp_sid or not self.whatsapp_token or not self.whatsapp_from:
                logger.warning("WhatsApp service not configured")
                return False

            try:
                from twilio.rest import Client
            except ImportError:
                logger.warning("Twilio library not installed")
                return False

            client = Client(self.whatsapp_sid, self.whatsapp_token)
            
            # Format variables as JSON string if provided
            import json
            variables_json = ""
            if template_variables:
                # Convert list to Twilio format: {"1": "var1", "2": "var2", ...}
                variables_json = json.dumps({str(i+1): str(v) for i, v in enumerate(template_variables)})
            
            msg = client.messages.create(
                from_=f"whatsapp:{self.whatsapp_from}",
                content_sid=template_sid,
                content_variables=variables_json if variables_json else None,
                to=f"whatsapp:{student_phone}"
            )
            
            logger.info(f"WhatsApp template sent to {student_phone} (SID: {msg.sid})")
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp template: {e}")
            return False
