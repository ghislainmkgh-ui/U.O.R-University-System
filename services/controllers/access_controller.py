class ControlleurAcces:
    """Orchestre la validation finale pour autoriser l'accès[cite: 29, 33]."""

    def __init__(self, service_auth, service_face, service_finance):
        self.auth = service_auth
        self.face = service_face
        self.finance = service_finance

    def valider_entree(self, etudiant_data, mdp_saisi, image_camera) -> bool:
        """Vérifie simultanément les 3 conditions[cite: 28, 29]."""
        
        # 1. Vérification Mot de passe [cite: 30]
        if self.auth.hacher_mot_de_passe(mdp_saisi) != etudiant_data['mot_de_passe']:
            return False
            
        # 2. Vérification Reconnaissance Faciale [cite: 31]
        if not self.face.comparer_visages(etudiant_data['encodage'], image_camera):
            return False
            
        # 3. Vérification Seuil Financier [cite: 32]
        if not self.finance.verifier_eligibilite(etudiant_data['solde'], etudiant_data['seuil']):
            return False
            
        return True # Accès Autorisé [cite: 33]