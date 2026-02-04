class ServiceSession:
    """Gère l'état de l'utilisateur admin actuel."""

    def __init__(self):
        self.admin_actuel = None
        self.langue = "FR"  # Par défaut 
        self.theme = "Clair" # Par défaut 

    def demarrer_session(self, admin_obj):
        self.admin_actuel = admin_obj
        self.langue = admin_obj.get('langue', "FR")
        self.theme = admin_obj.get('theme', "Clair")

    def fermer_session(self):
        self.admin_actuel = None