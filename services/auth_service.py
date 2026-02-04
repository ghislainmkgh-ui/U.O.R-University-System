import hashlib

class ServiceAuthentification:
    """Gère la sécurité des accès et l'intégrité des mots de passe."""
    
    @staticmethod
    def hacher_mot_de_passe(password: str) -> str:
        """Transforme le mot de passe en empreinte numérique non réversible."""
        return hashlib.sha256(password.encode()).hexdigest()

    def valider_format_password(self, password: str) -> bool:
        """Vérifie si le mot de passe respecte les critères de sécurité."""
        # Doit être composé de chiffres uniquement et avoir au moins 6 caractères 
        return password.isdigit() and len(password) >= 6

    def verifier_unicite(self, password: str, liste_existante: list) -> bool:
        """S'assure que le même mot de passe n'est pas utilisé par deux étudiants[cite: 52]."""
        return password not in liste_existante