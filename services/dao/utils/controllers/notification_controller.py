from abc import ABC, abstractmethod

class NotificationController:
    """Orchestre l'envoi des alertes financières après chaque transaction."""

    def __init__(self, mail_service, whatsapp_service, lang_manager):
        self.mail_service = mail_service
        self.whatsapp_service = whatsapp_service
        self.lang = lang_manager

    def notifier_paiement(self, etudiant_data, montant_paye_instantane):
        """
        Calcule les soldes et envoie les notifications bilingues.
        Calcul : Montant déjà payé et Montant restant pour le seuil.
        """
        nom_complet = f"{etudiant_data['nom']} {etudiant_data['prenom']}"
        solde_actuel = etudiant_data['montant_paye']
        seuil = etudiant_data['seuil_requis']
        restant = max(0, seuil - solde_actuel)

        # Construction du message selon la langue de l'étudiant
        sujet = self.lang.get_texte("payment_conf")
        corps = (f"Cher(e) {nom_complet},\n"
                 f"Paiement reçu : {montant_paye_instantane} USD.\n"
                 f"Total payé : {solde_actuel} USD.\n"
                 f"Reste pour atteindre le seuil : {restant} USD.")

        # Envoi multicanal
        self.mail_service.send(etudiant_data['email'], sujet, corps)
        self.whatsapp_service.send(etudiant_data['telephone'], corps)

        # Si le seuil est atteint, envoyer une félicitation d'éligibilité
        if solde_actuel >= seuil:
            self.notifier_eligibilite(etudiant_data)

    def notifier_eligibilite(self, etudiant_data):
        msg = "Félicitations ! Vous avez atteint le seuil financier. Vous êtes désormais éligible pour les examens."
        self.whatsapp_service.send(etudiant_data['telephone'], msg)