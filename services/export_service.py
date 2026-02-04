import json

class ExportService:
    """Prépare le transfert des données académiques vers d'autres universités."""

    def generer_dossier_transfert(self, etudiant_id):
        """Compile tout le dossier pour exportation mondiale."""
        # Récupération des données structurées
        donnees = self.dao.recuperer_dossier_complet(etudiant_id)
        
        dossier = {
            "institution_origine": "Université Officielle de Ruwenzori (U.O.R)",
            "identite": donnees['identite'],
            "cursus": donnees['structure_academique'], # Faculté/Dépt/Prom
            "resultats": donnees['points'], # Points envoyés partout dans le monde 
            "documents": donnees['ouvrages'] # Ouvrages et documents 
        }
        
        return json.dumps(dossier, indent=4)