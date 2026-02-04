class MessagingService(ABC):
    @abstractmethod
    def send(self, destinataire, sujet, message):
        pass

class WhatsAppService(MessagingService):
    def send(self, destinataire, sujet, message):
        # Ici on intégrerait l'API Twilio ou une passerelle WhatsApp
        print(f"Envoi WhatsApp vers {destinataire} : {message[:30]}...")

class EmailService(MessagingService):
    def send(self, destinataire, sujet, message):
        # Ici on intégrerait le protocole SMTP sécurisé
        print(f"Envoi Email vers {destinataire} : {sujet}")