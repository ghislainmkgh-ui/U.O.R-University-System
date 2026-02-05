"""Traductions français/anglais"""

TRANSLATIONS = {
    "FR": {
        # Navigation
        "dashboard": "Tableau de Bord",
        "students": "Étudiants",
        "finance": "Finances",
        "access_logs": "Logs d'Accès",
        "settings": "Paramètres",
        
        # Authentification
        "login": "Connexion",
        "logout": "Déconnexion",
        "username": "Nom d'utilisateur",
        "password": "Mot de passe",
        "remember_me": "Se souvenir de moi",
        "welcome": "Bienvenue",
        "access_granted": "Accès Autorisé",
        "access_denied": "Accès Refusé",
        
        # Étudiants
        "student_number": "Numéro d'Étudiant",
        "firstname": "Prénom",
        "lastname": "Nom",
        "email": "Email",
        "promotion": "Promotion",
        "eligible": "Éligible",
        "not_eligible": "Non Éligible",
        
        # Finances
        "amount_paid": "Montant Payé",
        "threshold": "Seuil",
        "remaining": "Restant",
        "payment": "Paiement",
        "eligible_students": "Étudiants Éligibles",
        "non_eligible_students": "Étudiants Non Éligibles",
        
        # Boutons
        "add": "Ajouter",
        "edit": "Modifier",
        "delete": "Supprimer",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "submit": "Soumettre",
        "view": "Voir",
        "search": "Rechercher",
        
        # Messages
        "loading": "Chargement...",
        "success": "Succès",
        "error": "Erreur",
        "warning": "Avertissement",
        "no_data": "Aucune donnée",
        "invalid_input": "Entrée invalide",
    },
    "EN": {
        # Navigation
        "dashboard": "Dashboard",
        "students": "Students",
        "finance": "Finance",
        "access_logs": "Access Logs",
        "settings": "Settings",
        
        # Authentication
        "login": "Login",
        "logout": "Logout",
        "username": "Username",
        "password": "Password",
        "remember_me": "Remember me",
        "welcome": "Welcome",
        "access_granted": "Access Granted",
        "access_denied": "Access Denied",
        
        # Students
        "student_number": "Student Number",
        "firstname": "First Name",
        "lastname": "Last Name",
        "email": "Email",
        "promotion": "Promotion",
        "eligible": "Eligible",
        "not_eligible": "Not Eligible",
        
        # Finance
        "amount_paid": "Amount Paid",
        "threshold": "Threshold",
        "remaining": "Remaining",
        "payment": "Payment",
        "eligible_students": "Eligible Students",
        "non_eligible_students": "Non-Eligible Students",
        
        # Buttons
        "add": "Add",
        "edit": "Edit",
        "delete": "Delete",
        "save": "Save",
        "cancel": "Cancel",
        "submit": "Submit",
        "view": "View",
        "search": "Search",
        
        # Messages
        "loading": "Loading...",
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "no_data": "No data",
        "invalid_input": "Invalid input",
    }
}


class Translator:
    """Service de traduction"""
    
    def __init__(self, language: str = "FR"):
        self.language = language if language in TRANSLATIONS else "FR"
    
    def set_language(self, language: str):
        """Change la langue"""
        if language in TRANSLATIONS:
            self.language = language
            return True
        return False
    
    def get(self, key: str, default: str = None) -> str:
        """Récupère une traduction"""
        text = TRANSLATIONS[self.language].get(key, None)
        return text if text else (default or key)
    
    def _(self, key: str) -> str:
        """Alias pour get()"""
        return self.get(key)
