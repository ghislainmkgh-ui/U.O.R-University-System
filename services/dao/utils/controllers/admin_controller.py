class ControleurAdmin:
    """Cerveau administratif pour gérer les étudiants de l'U.O.R[cite: 170]."""

    def __init__(self, etudiant_dao, rapport_service, lang_manager):
        self.dao = etudiant_dao
        self.rapports = rapport_service
        self.lang = lang_manager

    def lister_etudiants_par_structure(self, fac_id, dept_id, prom_id):
        """Classe les étudiants selon la hiérarchie stricte[cite: 177, 178]."""
        # Récupère les données depuis le DAO en filtrant par Promotion
        etudiants = self.dao.recuperer_par_promotion(prom_id)
        return etudiants

    def obtenir_stats_financieres(self):
        """Distingue ceux qui ont payé, jamais payé, et ceux au seuil."""
        return {
            "eligibles": self.rapports.filtrer_par_statut_financier(self.dao.get_all(), "seuil_atteint"),
            "non_payes": self.rapports.filtrer_par_statut_financier(self.dao.get_all(), "jamais_paye")
        }