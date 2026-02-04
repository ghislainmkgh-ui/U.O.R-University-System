import customtkinter as ctk

class SidebarNavigation(ctk.CTkFrame):
    def __init__(self, master, callbacks):
        super().__init__(master, width=200, corner_radius=0)
        self.callbacks = callbacks
        
        # Logo U.O.R
        self.logo_label = ctk.CTkLabel(self, text="U.O.R ADMIN", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        # Boutons de navigation
        self.btn_dashboard = ctk.CTkButton(self, text="Dashboard", command=callbacks['dashboard'])
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)

        self.btn_etudiants = ctk.CTkButton(self, text="Gestion Étudiants", command=callbacks['etudiants'])
        self.btn_etudiants.grid(row=2, column=0, padx=20, pady=10)

        # Sélecteur de langue (Bilingue)
        self.lang_switch = ctk.CTkOptionMenu(self, values=["Français", "English"], command=callbacks['langue'])
        self.lang_switch.grid(row=10, column=0, padx=20, pady=20)