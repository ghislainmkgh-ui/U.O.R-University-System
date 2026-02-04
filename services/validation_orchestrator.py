class ValidationOrchestrator:
    """Coordonne les trois piliers de la validation pour l'U.O.R."""

    def __init__(self, vision_engine, finance_service, auth_service):
        self.vision = vision_engine
        self.finance = finance_service
        self.auth = auth_service

    def processus_admission_salle(self, etudiant_id, mdp_saisi, image_porte):
        """
        Exécute la séquence stricte :
        1. Mot de passe [cite: 30]
        2. Reconnaissance faciale [cite: 31]
        3. Seuil financier [cite: 32]
        """
        # Récupération des données via DAO (simulé ici)
        donnees = self.get_student_full_data(etudiant_id)

        # Étape 1 : Mot de passe
        if not self.auth.verifier(mdp_saisi, donnees['mdp_hash']):
            return False, "Code erroné"

        # Étape 2 : Visage (appel au VisionEngine)
        is_identifie, msg = self.vision.verifier_identite(donnees['face_enc'], image_porte)
        if not is_identifie:
            return False, msg

        # Étape 3 : Seuil Financier
        if not self.finance.verifier_eligibilite(donnees['solde'], donnees['seuil']):
            return False, "Seuil non atteint"

        return True, "Accès Autorisé"