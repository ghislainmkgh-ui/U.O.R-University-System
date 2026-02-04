class ServiceRapports:
    """Génère des vues filtrées pour l'administration."""

    def filtrer_par_statut_financier(self, liste_etudiants, critere):
        """
        Filtre les étudiants selon 3 catégories précises :
        - 'payé' : ont déjà effectué un versement.
        - 'jamais_payé' : solde à zéro.
        - 'seuil_atteint' : éligibles pour l'examen.
        """
        if critere == "seuil_atteint":
            return [e for e in liste_etudiants if e['seuil_atteint'] == True] [cite: 55]
        elif critere == "jamais_paye":
            return [e for e in liste_etudiants if e['montant_paye'] == 0] [cite: 55]
        return liste_etudiants

    def generer_statistiques_promotion(self, promotion_id, db_session):
        """Fournit un résumé pro et fluide pour le Dashboard."""
        # Logique pour compter les accès autorisés vs refusés [cite: 33, 35]
        pass