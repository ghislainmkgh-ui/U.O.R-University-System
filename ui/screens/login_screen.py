"""Écran de connexion avec sélection de langue"""
import customtkinter as ctk
import logging
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from app.services.auth.authentication_service import AuthenticationService
from ui.screens.admin.admin_dashboard import AdminDashboard

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTk):
    """Écran de connexion principal avec support multilingue"""
    
    def __init__(self):
        super().__init__()
        
        self.selected_language = "FR"
        self.translator = Translator(self.selected_language)
        self.theme = ThemeManager("light")
        self.auth_service = AuthenticationService()
        
        self.title("U.O.R - Système de Contrôle d'Accès")
        self._set_window_size()
        self._create_ui()
    
    def _set_window_size(self):
        """Configure la taille de la fenêtre"""
        self.geometry("520x700")
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
        
        # Sélecteur de langue (en haut à droite)
        lang_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=0, sticky="e", padx=30, pady=15)
        
        ctk.CTkLabel(
            lang_frame,
            text=self.translator.get("language"),
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=10)
        
        self.lang_switch = ctk.CTkSegmentedButton(
            lang_frame,
            values=["FR", "EN"],
            command=self._on_language_change,
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lang_switch.set("FR")
        self.lang_switch.pack(side="left", padx=5)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=1, column=0, sticky="ew", padx=40, pady=(30, 50))
        header_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header_frame,
            text="U.O.R",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.theme.get_color("primary")
        ).pack()
        
        ctk.CTkLabel(
            header_frame,
            text=self.translator.get("exam_access_platform"),
            font=ctk.CTkFont(size=13),
            text_color=self.theme.get_color("text_secondary")
        ).pack(pady=(5, 0))
        
        # Formulaire
        form_frame = ctk.CTkFrame(main_frame, fg_color=self.theme.get_color("surface"), corner_radius=15)
        form_frame.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 40))
        form_frame.grid_columnconfigure(0, weight=1)
        
        # Titre du formulaire
        ctk.CTkLabel(
            form_frame,
            text=self.translator.get("login").upper(),
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=30, pady=(30, 25), sticky="w")
        
        # Username
        ctk.CTkLabel(
            form_frame,
            text=self.translator.get("username"),
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=1, column=0, padx=30, sticky="w")
        
        self.entry_username = ctk.CTkEntry(
            form_frame,
            placeholder_text=self.translator.get("username"),
            height=42,
            corner_radius=8,
            border_width=1
        )
        self.entry_username.grid(row=2, column=0, padx=30, pady=(8, 18), sticky="ew")
        self.entry_username.insert(0, "admin")
        
        # Password
        ctk.CTkLabel(
            form_frame,
            text=self.translator.get("password"),
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=3, column=0, padx=30, sticky="w")
        
        self.entry_password = ctk.CTkEntry(
            form_frame,
            placeholder_text=self.translator.get("password"),
            height=42,
            show="•",
            corner_radius=8,
            border_width=1
        )
        self.entry_password.grid(row=4, column=0, padx=30, pady=(8, 18), sticky="ew")
        self.entry_password.insert(0, "admin123")
        
        # Remember me
        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            form_frame,
            text=self.translator.get("remember_me"),
            variable=self.remember_var,
            checkbox_height=18,
            checkbox_width=18,
            font=ctk.CTkFont(size=11)
        ).grid(row=5, column=0, padx=30, sticky="w", pady=(0, 20))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.theme.get_color("danger")
        )
        self.status_label.grid(row=6, column=0, padx=30, pady=(0, 15), sticky="ew")
        
        # Login button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text=self.translator.get("login").upper(),
            height=48,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.theme.get_color("primary"),
            command=self._on_login
        )
        self.login_btn.grid(row=7, column=0, padx=30, pady=(0, 30), sticky="ew")
    
    def _on_language_change(self, value):
        """Change la langue de l'interface"""
        self.selected_language = value
        self.translator = Translator(value)
        
        # Recréer l'interface avec la nouvelle langue
        for widget in self.winfo_children():
            widget.destroy()
        
        self._create_ui()
        logger.info(f"Langue changée à: {value}")
    
    def _on_login(self):
        """Gère la connexion"""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()
        
        if not username or not password:
            self.status_label.configure(
                text="❌ " + self.translator.get("invalid_input"),
                text_color=self.theme.get_color("danger")
            )
            return
        
        # Authentification admin (pour l'instant)
        if username == "admin" and password == "admin123":
            # Afficher le message de succès
            self.status_label.configure(
                text="✅ " + self.translator.get("success") + " - " + self.translator.get("welcome") + "!",
                text_color=self.theme.get_color("success")
            )
            
            # Désactiver les champs et le bouton
            self.entry_username.configure(state="disabled")
            self.entry_password.configure(state="disabled")
            self.login_btn.configure(state="disabled")
            
            logger.info("Connexion réussie - Ouverture du dashboard")
            
            # Attendre 1.5 secondes puis ouvrir le dashboard
            self.after(1500, self._open_dashboard)
        else:
            self.status_label.configure(
                text="❌ " + self.translator.get("error") + " - " + self.translator.get("invalid_input"),
                text_color=self.theme.get_color("danger")
            )
            logger.warning(f"Tentative de connexion échouée: {username}")
            
            # Effacer le mot de passe en cas d'erreur
            self.entry_password.delete(0, "end")
    
    def _open_dashboard(self):
        """Ouvre le tableau de bord"""
        try:
            # Créer et afficher le dashboard
            dashboard = AdminDashboard(parent=self, language=self.selected_language, theme=self.theme)
            
            # Gérer la fermeture du dashboard
            def on_dashboard_close():
                dashboard.destroy()
                # Réinitialiser l'écran de connexion
                self.entry_password.delete(0, "end")
                self.entry_username.delete(0, "end")
                self.entry_username.insert(0, "admin")
                self.entry_password.insert(0, "admin123")
                self.status_label.configure(text="")
                self.entry_username.configure(state="normal")
                self.entry_password.configure(state="normal")
                self.login_btn.configure(state="normal")
                # Réafficher la fenêtre de login
                self.deiconify()
            
            dashboard.protocol("WM_DELETE_WINDOW", on_dashboard_close)
            
            # Masquer la fenêtre de connexion
            self.withdraw()
            
            # Forcer l'affichage du dashboard
            dashboard.deiconify()
            dashboard.focus()
            
        except Exception as e:
            logger.error(f"Erreur ouverture dashboard: {e}")
            self.status_label.configure(
                text="❌ Erreur: " + str(e),
                text_color=self.theme.get_color("danger")
            )
            # Réactiver les champs
            self.entry_username.configure(state="normal")
            self.entry_password.configure(state="normal")
            self.login_btn.configure(state="normal")
