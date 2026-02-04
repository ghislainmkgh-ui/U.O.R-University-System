class PaiementDAO:
    def __init__(self):
        self.db = DatabaseConnection().connect()

    def enregistrer_paiement(self, etudiant_id, montant, methode):
        """Enregistre la transaction et met à jour le profil financier[cite: 17, 32]."""
        cursor = self.db.cursor()
        try:
            # 1. Insérer le paiement
            cursor.execute("INSERT INTO Paiement (etudiant_id, montant, methode_paiement, date_paiement) VALUES (%s, %s, %s, NOW())", 
                           (etudiant_id, montant, methode))
            
            # 2. Mettre à jour le solde dans ProfilFinancier
            cursor.execute("""
                UPDATE ProfilFinancier 
                SET montant_paye = montant_paye + %s,
                    date_dernier_paiement = NOW()
                WHERE etudiant_id = %s
            """, (montant, etudiant_id))
            
            # 3. Vérifier et marquer l'éligibilité automatique [cite: 10, 22]
            cursor.execute("""
                UPDATE ProfilFinancier 
                SET seuil_atteint = TRUE 
                WHERE etudiant_id = %s AND montant_paye >= seuil_requis
            """, (etudiant_id,))
            
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return False