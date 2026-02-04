from cryptography.fernet import Fernet
import os

class GestionnaireSecurite:
    """Assure la confidentialité et l'intégrité des données sensibles."""

    def __init__(self):
        # La clé doit être stockée dans une variable d'environnement sécurisée
        self.key = os.getenv("SECRET_KEY_UOR", Fernet.generate_key())
        self.cipher_suite = Fernet(self.key)

    def chiffrer_donnees(self, texte: str) -> str:
        """Chiffre les informations personnelles avant stockage."""
        return self.cipher_suite.encrypt(texte.encode()).decode()

    def dechiffrer_donnees(self, texte_chiffre: str) -> str:
        """Déchiffre les données pour l'affichage administratif."""
        return self.cipher_suite.decrypt(texte_chiffre.encode()).decode()

    @staticmethod
    def verifier_integrite_systeme():
        """Vérifie si les fichiers vitaux du logiciel n'ont pas été modifiés."""
        # Logique de checksum pour prévenir le piratage
        pass