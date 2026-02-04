from services.dao.DatabaseConnection import DatabaseConnection
from typing import Any

class EtudiantDAO:
    def __init__(self):
        self.db = DatabaseConnection().connect()

    def creer_etudiant(self, etudiant: Any):
        """Insère un nouvel étudiant avec son mot de passe haché[cite: 51, 60]."""
        cursor = self.db.cursor()
        query = """
            INSERT INTO Etudiant (numero_etudiant, promotion_id, nom, prenom, email, 
                                 mot_de_passe_hash, langue_preferee, theme_prefere, date_inscription)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        valeurs = (etudiant.numero_etudiant, etudiant.promotion_id, etudiant.nom, 
                   etudiant.prenom, etudiant.email, etudiant.mot_de_pass_hash, 
                   etudiant.langue_preferee, etudiant.theme_prefere)
        try:
            cursor.execute(query, valeurs)
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            self.db.rollback()
            raise e

    def recuperer_par_identifiant_unique(self, code_etudiant: str):
        """Récupère le profil complet pour la validation à l'entrée[cite: 26, 28]."""
        cursor = self.db.cursor(dictionary=True)
        query = """
            SELECT e.*, pf.montant_paye, pf.seuil_requis, pf.seuil_atteint 
            FROM Etudiant e
            JOIN ProfilFinancier pf ON e.etudiant_id = pf.etudiant_id
            WHERE e.numero_etudiant = %s
        """
        cursor.execute(query, (code_etudiant,))
        return cursor.fetchone()