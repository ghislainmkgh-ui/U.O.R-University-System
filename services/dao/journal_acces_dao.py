class JournalAccesDAO:
    def __init__(self):
        self.db = DatabaseConnection().connect()

    def log_tentative_acces(self, etudiant_id, examen_id, autorise, raison_echec=None):
        """Archive l'historique des accès pour l'administration[cite: 55, 62]."""
        cursor = self.db.cursor()
        query = """
            INSERT INTO JournalAcces (etudiant_id, examen_id, heure_acces, acces_autorise, raison_echec)
            VALUES (%s, %s, NOW(), %s, %s)
        """
        cursor.execute(query, (etudiant_id, examen_id, autorise, raison_echec))
        self.db.commit()