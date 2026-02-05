"""Écran de connexion"""
import customtkinter as ctk
import logging
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from app.services.auth.authentication_service import AuthenticationService
from ui.screens.admin.admin_dashboard import AdminDashboard

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTk):
    """Écran de connexion principal"""
    
    def __init__(self):
        super().__init__()
        
        self.translator = Translator("FR")
        self.theme = ThemeManager("light")
        self.auth_service = AuthenticationService()
        
        self.title("U.O.R - Système de Contrôle d'Accès")
        self._set_window_size()
        self._create_ui()
    
    def _set_window_size(self):
        """Configure la taille de la fenêtre"""
        self.geometry("500x600")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _create_ui(self):
        """Crée l'interface de connexion"""
        bg_color = self.theme.get_color("background")
        self.configure(fg_color=bg_color)
        
        # Conteneur principal
        main_frame = ctk.CTkFrame(self, fg_color=bg_color)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=40, pady=(60, 40))
        
        ctk.CTkLabel(
            header_frame,
            text="U.O.R",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.theme.get_color("primary")
        ).pack()
        
        ctk.CTkLabel(
            header_frame,
            text="Plateforme d'Accès aux Examens",
            font=ctk.CTkFont(size=14),
            text_color=self.theme.get_color("text_secondary")
        ).pack()
        
        # Formulaire
        form_frame = ctk.CTkFrame(main_frame, fg_color=self.theme.get_color("surface"), corner_radius=14)
        form_frame.grid(row=1, column=0, sticky="ew", padx=40, pady=(0, 40))
        form_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            form_frame,
            text=self.translator.get("login").upper(),
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=30, pady=(30, 20), sticky="w")
        
        # Username input
        ctk.CTkLabel(form_frame, text=self.translator.get("username")).grid(row=1, column=0, padx=30, sticky="w")
        self.entry_username = ctk.CTkEntry(
            form_frame,
            placeholder_text=self.translator.get("username"),
            height=40,
            corner_radius=8
        )
        self.entry_username.grid(row=2, column=0, padx=30, pady=(8, 15), sticky="ew")
        
        # Password input
        ctk.CTkLabel(form_frame, text=self.translator.get("password")).grid(row=3, column=0, padx=30, sticky="w")
        self.entry_password = ctk.CTkEntry(
            form_frame,
            placeholder_text=self.translator.get("password"),
            height=40,
            show="*",
            corner_radius=8
        )
        self.entry_password.grid(row=4, column=0, padx=30, pady=(8, 25), sticky="ew")
        
        # Remember me
        self.checkbox_remember = ctk.CTkCheckBox(
            form_frame,
            text=self.translator.get("remember_me"),
            checkbox_height=20,
            checkbox_width=20
        )
        self.checkbox_remember.grid(row=5, column=0, padx=30, pady=(0, 25), sticky="w")
        
        # Login button
        self.btn_login = ctk.CTkButton(
            form_frame,
            text=self.translator.get("login").upper(),
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.theme.get_color("primary"),
            hover_color=self.theme.get_color("primary_dark"),
            command=self._handle_login
        )
        self.btn_login.grid(row=6, column=0, padx=30, pady=(0, 30), sticky="ew")
        
        # Status label
        self.label_status = ctk.CTkLabel(
            form_frame,
            text="",
            text_color=self.theme.get_color("danger")
        )
        self.label_status.grid(row=7, column=0, padx=30, pady=(0, 20), sticky="ew")
    
    def _handle_login(self):
        """Gère la tentative de connexion"""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        
        if not username or not password:
            self.label_status.configure(text="Veuillez remplir tous les champs")
            return
        
        # Temporaire: test avec admin/admin123
        if username == "admin" and password == "admin123":
            self.label_status.configure(text="Connexion réussie...", text_color=self.theme.get_color("success"))
            self.after(800, self._open_admin_dashboard)
        else:
            self.label_status.configure(text="Identifiants invalides", text_color=self.theme.get_color("danger"))
    
    def _open_admin_dashboard(self):
        """Ouvre le tableau de bord administrateur"""
        self.destroy()
        dashboard = AdminDashboard()
        dashboard.mainloop()
