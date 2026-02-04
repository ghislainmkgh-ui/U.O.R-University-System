class ServiceNotification:
    """Gère l'envoi des alertes automatiques."""

    def envoyer_alerte_paiement(self, email_etudiant: str, tel_etudiant: str, montant: float, restant: float):
        """Simule ou déclenche l'envoi via API (Email/WhatsApp)[cite: 18, 19, 20]."""
        message = f"Paiement reçu. Montant payé : {montant}. Il vous reste {restant} pour atteindre le seuil."
        
        # Logique d'envoi Email
        self._envoyer_email(email_etudiant, message)
        
        # Logique d'envoi WhatsApp
        self._envoyer_whatsapp(tel_etudiant, message)

    def _envoyer_email(self, destinataire, msg):
        print(f"Email envoyé à {destinataire}") # Intégration SMTP future

    def _envoyer_whatsapp(self, numero, msg):
        print(f"WhatsApp envoyé au {numero}") # Intégration API WhatsApp future