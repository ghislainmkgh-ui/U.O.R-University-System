class GestionnaireLangue:
    """Gère le bilinguisme du logiciel (FR/EN)."""
    
    DICTIONNAIRES = {
        "FR": {
            "dashboard": "Tableau de Bord",
            "access_granted": "Accès Autorisé",
            "access_denied": "Accès Refusé",
            "financial_threshold": "Seuil Financier",
            "face_recognition": "Reconnaissance Faciale",
            "student_id": "Matricule Étudiant"
        },
        "EN": {
            "dashboard": "Dashboard",
            "access_granted": "Access Granted",
            "access_denied": "Access Denied",
            "financial_threshold": "Financial Threshold",
            "face_recognition": "Face Recognition",
            "student_id": "Student ID"
        }
    }

    def __init__(self, langue_par_defaut="FR"):
        self.langue_actuelle = langue_par_defaut

    def changer_langue(self, nouvelle_langue):
        if nouvelle_langue in self.DICTIONNAIRES:
            self.langue_actuelle = nouvelle_langue

    def get_texte(self, cle):
        """Récupère la traduction correspondante à la clé."""
        return self.DICTIONNAIRES[self.langue_actuelle].get(cle, cle)