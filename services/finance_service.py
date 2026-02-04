from decimal import Decimal

class ServiceFinancier:
    """Gère la logique métier liée aux paiements et aux seuils."""

    def verifier_eligibilite(self, montant_paye: Decimal, seuil_requis: Decimal) -> bool:
        """Détermine si l'étudiant peut entrer en salle d'examen[cite: 10, 21]."""
        return montant_paye >= seuil_requis

    def calculer_restant(self, montant_paye: Decimal, seuil_requis: Decimal) -> Decimal:
        """Calcule le montant manquant pour atteindre le seuil[cite: 20]."""
        restant = seuil_requis - montant_paye
        return max(Decimal(0), restant)