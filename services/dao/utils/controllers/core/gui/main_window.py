import customtkinter as ctk
from services.dao.utils.controllers.core.gui.components.sidebar import SidebarNavigation

class DashboardPrincipal(ctk.CTk):
    def __init__(self, controleur_admin):
        super().__init__()
        self.ctrl = controleur_admin
        
        # Configuration de la fenêtre
        self.title("U.O.R - Plateforme de Contrôle d'Accès")
        self.geometry("1100x600")
        
        # Configuration du Layout (Grille)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Barre latérale
        self.sidebar = SidebarNavigation(self, self.get_nav_callbacks())
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Zone de contenu principal (Dashboard)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.creer_widgets_stats()

    def creer_widgets_stats(self):
        """Crée les cartes de statistiques (Éligibles, Non-payés, Fraudes)."""
        # Carte Seuil Atteint
        self.card_eligible = ctk.CTkFrame(self.main_frame, width=250, height=100, fg_color="#1cc88a")
        self.card_eligible.grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(self.card_eligible, text="ÉTUDIANTS ÉLIGIBLES", text_color="white").pack(pady=10)
        
        # Carte Seuil Non Atteint
        self.card_pending = ctk.CTkFrame(self.main_frame, width=250, height=100, fg_color="#f6c23e")
        self.card_pending.grid(row=0, column=1, padx=10, pady=10)
        ctk.CTkLabel(self.card_pending, text="SEUIL NON ATTEINT", text_color="white").pack(pady=10)

    def get_nav_callbacks(self):
        return {
            'dashboard': lambda: print("Affichage Dashboard"),
            'etudiants': lambda: print("Gestion Faculté => Promotion"),
            'langue': lambda l: print(f"Changement vers {l}")
        }