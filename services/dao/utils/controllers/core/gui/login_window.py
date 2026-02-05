import customtkinter as ctk
from services.auth_service import ServiceAuthentification

class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_success = on_login_success
        self.auth = ServiceAuthentification()
        
        self.title("U.O.R - Connexion Sécurisée")
        self.geometry("400x500")
        
        # Design élégant
        self.label = ctk.CTkLabel(self, text="ADMINISTRATION U.O.R", font=("Arial", 20, "bold"))
        self.label.pack(pady=40)

        self.username = ctk.CTkEntry(self, placeholder_text="Nom d'utilisateur", width=250)
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(self, placeholder_text="Mot de passe", show="*", width=250)
        self.password.pack(pady=10)

        self.btn_login = ctk.CTkButton(self, text="Se Connecter", command=self.verifier_connexion, 
                                       fg_color="#4e73df", hover_color="#2e59d9")
        self.btn_login.pack(pady=30)

        self.status_label = ctk.CTkLabel(self, text="", text_color="#e74a3b")
        self.status_label.pack(pady=5)

    def verifier_connexion(self):
        # Ici, on compare avec la table 'Administrateur' du MLD
        user = self.username.get()
        pwd = self.password.get()
        
        # Logique de vérification (exemple simplifié)
        if user == "admin" and pwd == "admin123": # À lier avec AdminDAO
            self.status_label.configure(text="Accès autorisé : Connexion réussie.", text_color="#1cc88a")
            self.after(300, self._proceed_after_success)
        else:
            self.status_label.configure(text="Accès refusé : Identifiants invalides.", text_color="#e74a3b")

    def _proceed_after_success(self):
        self.destroy() # Ferme la fenêtre de login
        self.on_success() # Lance le Dashboard