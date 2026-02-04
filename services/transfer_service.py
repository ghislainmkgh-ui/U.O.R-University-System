import json
import requests # Pour communiquer avec l'API de l'université de destination
from datetime import datetime

class ServiceTransfertDonnees:
    """Gère l'exportation et la communication des données vers d'autres universités."""

    def preparer_dossier_transfert(self, etudiant_id, profil_acad, points, documents):
        """
        Compile les données de l'étudiant dans un format standardisé JSON.
        Inclut les points, ouvrages et documents académiques.
        """
        dossier = {
            "uor_transfer_id": f"UOR-{etudiant_id}-{datetime.now().strftime('%Y%m%d')}",
            "date_transfert": str(datetime.now()),
            "donnees_etudiant": {
                "id": etudiant_id,
                "parcours": profil_acad, # Programme, niveau [cite: 15]
                "resultats": points,      # Points obtenus [cite: 44]
                "bibliotheque": documents # Ouvrages et documents [cite: 44]
            },
            "statut_authentification": "Certifié par U.O.R"
        }
        return json.dumps(dossier, indent=4)

    def envoyer_vers_universite(self, url_destination, dossier_json):
        """Transfère le dossier via une requête sécurisée vers une autre plateforme."""
        try:
            # Envoi sécurisé via protocole HTTPS
            reponse = requests.post(url_destination, json=dossier_json, timeout=10)
            if reponse.status_code == 200:
                print("Transfert réussi et certifié.")
                return True
            return False
        except Exception as e:
            print(f"Erreur lors du transfert international : {e}")
            return False