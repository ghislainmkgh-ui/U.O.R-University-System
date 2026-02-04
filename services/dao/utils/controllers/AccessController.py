class AccessController:
    def traiter_entree(self, mdp_recu):
        # 1. Vérification du Mot de Passe
        etudiant = self.db.verifier_mot_de_passe(mdp_recu)
        if not etudiant:
            self.envoyer_a_arduino("ERR_AUTH")
            return

        # 2. Si MDP valide, demander visage sur le LCD
        self.envoyer_a_arduino("SCAN_VISAGE")
        
        # 3. Lancement de la reconnaissance faciale
        success_face = self.vision.analyser_flux_porte()
        if not success_face:
            self.envoyer_a_arduino("ERR_FACE")
            return

        # 4. Vérification financière
        if etudiant['solde'] < etudiant['seuil']:
            self.envoyer_a_arduino("ERR_FINANCE")
            self.notification.alerte_refus(etudiant) # Alerte WhatsApp
            return

        # 5. Tout est OK
        self.envoyer_a_arduino("ACCES_OK")
        self.journal.enregistrer_entree(etudiant['id'])