import random
import string
from core.vision_engine import VisionEngine
from services.auth_service import ServiceAuthentification

class EnrollmentManager:
    """Gère l'enregistrement professionnel et sécurisé des nouveaux étudiants."""

    def __init__(self, etudiant_dao, vision_engine):
        self.dao = etudiant_dao
        self.vision = vision_engine
        self.auth = ServiceAuthentification()

    def generer_mot_de_passe_unique(self):
        """Génère un code de 6 chiffres qui n'existe pas encore dans le système."""
        while True:
            # Génération d'un code aléatoire de 6 chiffres [cite: 51]
            nouveau_mdp = ''.join(random.choices(string.digits, k=6))
            
            # Vérification de l'unicité stricte 
            if not self.dao.verifier_existence_mot_de_passe(nouveau_mdp):
                return nouveau_mdp

    def inscrire_etudiant(self, infos_perso, chemin_photo, seuil_exige):
        """
        Orchestre l'inscription complète :
        1. Capture et encodage facial.
        2. Génération du mot de passe unique[cite: 51].
        3. Création des profils académique et financier.
        """
        # Traitement du visage
        encodage = self.vision.encoder_visage(chemin_photo)
        if encodage is None:
            return False, "Erreur : Visage non détecté sur la photo."

        # Sécurité : Mot de passe
        mdp_clair = self.generer_mot_de_passe_unique()
        mdp_hache = self.auth.hacher_mot_de_passe(mdp_clair)

        # Structuration des données (Faculté => Département => Promotion) 
        try:
            etudiant_id = self.dao.creer_etudiant_complet(
                infos_perso, 
                mdp_hache, 
                encodage, 
                seuil_exige
            )
            
            # Retourne le mot de passe clair à l'administrateur pour remise à l'étudiant
            return True, {"id": etudiant_id, "mdp_a_remettre": mdp_clair}
        except Exception as e:
            return False, f"Erreur base de données : {str(e)}"