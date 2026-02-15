"""Écran de connexion moderne avec design two-column"""
import customtkinter as ctk
import logging
from tkinter import messagebox
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from app.services.auth.authentication_service import AuthenticationService
from ui.screens.admin.admin_dashboard import AdminDashboard

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTkFrame):
    """Écran de connexion moderne"""
    
    def __init__(self, parent_app=None, parent=None):
        # Si parent_app est fourni, c'est le wrapper, sinon on crée une fenêtre standalone
        if parent_app:
            super().__init__(parent_app)
            self.parent_app = parent_app
            self.is_standalone = False
            self.pack(fill="both", expand=True)
            logger.info("LoginScreen created as child of AppWrapper")
        else:
            # Mode legacy - créer sa propre fenêtre
            root = ctk.CTk()
            super().__init__(root)
            self.parent_app = None
            self.is_standalone = True
            self.pack(fill="both", expand=True)
            root.title("U.O.R - Système de Contrôle d'Accès")
            root.geometry("1000x680")
            logger.info("LoginScreen created as standalone window")
        
        self.selected_language = "FR"
        self.translator = Translator(self.selected_language)
        self.theme = ThemeManager("light")
        self.auth_service = AuthenticationService()
        self.dashboard_open = False  # Flag pour éviter les ouvertures multiples
        
        self._create_ui()
    
    def _set_window_size(self):
        """Configure la taille de la fenêtre"""
        # Obtenir les dimensions de l'écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Taille optimale (max 90% de l'écran)
        window_width = min(1000, int(screen_width * 0.9))
        window_height = min(680, int(screen_height * 0.85))
        
        # Centrer la fenêtre
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(600, 500)  # Taille minimale pour garder l'interface utilisable
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _create_ui(self):
        """Crée l'interface de connexion avec design two-column"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # LEFT COLUMN - Form
        left_frame = ctk.CTkFrame(main_frame, fg_color="white")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=0)
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_rowconfigure(2, weight=0)
        
        # Language selector (top right)
        lang_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        lang_frame.grid(row=0, column=0, sticky="ne", padx=30, pady=20)
        
        self.lang_switch = ctk.CTkSegmentedButton(
            lang_frame,
            values=["FR", "EN"],
            command=self._on_language_change,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#e5e5e5",
            selected_color="#FF4444",
            selected_hover_color="#E63333",
            text_color="#333333"
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.pack(side="left")
        
        # Form container (centered vertically)
        form_container = ctk.CTkFrame(left_frame, fg_color="transparent")
        form_container.grid(row=1, column=0, sticky="nsew", padx=50)
        form_container.grid_columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            form_container,
            text="Log in",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#1a1a1a"
        ).pack(anchor="w", pady=(0, 30))
        
        # Username/Email field
        ctk.CTkLabel(
            form_container,
            text="Username or Email",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#333333"
        ).pack(anchor="w", pady=(0, 8))
        
        self.entry_username = ctk.CTkEntry(
            form_container,
            placeholder_text="Enter your username or email",
            height=45,
            corner_radius=6,
            border_width=1,
            border_color="#e0e0e0",
            fg_color="white",
            text_color="#1a1a1a",
            font=ctk.CTkFont(size=12)
        )
        self.entry_username.pack(fill="x", pady=(0, 20))
        self.entry_username.insert(0, "admin")
        
        # Password field
        ctk.CTkLabel(
            form_container,
            text="Password",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#333333"
        ).pack(anchor="w", pady=(0, 8))
        
        self.entry_password = ctk.CTkEntry(
            form_container,
            placeholder_text="Enter your password",
            height=45,
            show="•",
            corner_radius=6,
            border_width=1,
            border_color="#e0e0e0",
            fg_color="white",
            text_color="#1a1a1a",
            font=ctk.CTkFont(size=12)
        )
        self.entry_password.pack(fill="x", pady=(0, 15))
        self.entry_password.insert(0, "admin123")
        
        # Remember me + Forgot password
        checkbox_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(0, 25))
        
        ctk.CTkCheckBox(
            checkbox_frame,
            text="Remember me",
            checkbox_height=16,
            checkbox_width=16,
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        ).pack(side="left")
        
        ctk.CTkLabel(
            checkbox_frame,
            text="Forgot Password?",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF4444",
            cursor="hand2"
        ).pack(side="right")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            form_container,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF4444"
        )
        self.status_label.pack(fill="x", pady=(0, 15))
        
        # Login button
        self.login_btn = ctk.CTkButton(
            form_container,
            text="Sign In",
            height=50,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#FF4444",
            hover_color="#E63333",
            text_color="white",
            corner_radius=6,
            command=self._on_login
        )
        self.login_btn.pack(fill="x", pady=(0, 20))
        
        # Sign up link
        signup_frame = ctk.CTkFrame(form_container, fg_color="transparent")
        signup_frame.pack(fill="x")
        
        ctk.CTkLabel(
            signup_frame,
            text="Don't have an account? ",
            font=ctk.CTkFont(size=11),
            text_color="#666666"
        ).pack(side="left")
        
        ctk.CTkLabel(
            signup_frame,
            text="Sign Up",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FF4444",
            cursor="hand2"
        ).pack(side="left")
        
        # RIGHT COLUMN - Banner
        right_frame = ctk.CTkFrame(main_frame, fg_color="#3a2551")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)
        
        # Banner content
        content_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_rowconfigure(1, weight=0)
        
        # Welcome text
        ctk.CTkLabel(
            content_frame,
            text="Welcome To\nU.O.R Platform",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="white",
            justify="center"
        ).grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Subtitle
        ctk.CTkLabel(
            content_frame,
            text="Exam Access & Management System",
            font=ctk.CTkFont(size=14),
            text_color="#cccccc"
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(20, 0))
    
    def _on_language_change(self, value):
        """Change la langue de l'interface"""
        # Ne rien faire si la langue est déjà sélectionnée
        if value == self.selected_language:
            logger.debug(f"Langue déjà sélectionnée: {value}")
            return
        
        # Ne pas changer la langue si le dashboard est en train de s'ouvrir
        if self.dashboard_open:
            logger.warning("Cannot change language while dashboard is opening")
            return
        
        logger.info(f"Changing language from {self.selected_language} to {value}")
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
                text="❌ Please enter both username and password",
                text_color="#FF4444"
            )
            return
        
        # Authentification admin (pour l'instant)
        if username == "admin" and password == "admin123":
            # Réinitialiser le flag avant ouverture
            self.dashboard_open = False
            
            # Afficher le message de succès
            self.status_label.configure(
                text="✅ Login successful!",
                text_color="#00BB00"
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
                text="❌ Invalid username or password",
                text_color="#FF4444"
            )
            logger.warning(f"Tentative de connexion échouée: {username}")
            
            # Effacer le mot de passe en cas d'erreur
            self.entry_password.delete(0, "end")
    
    def _open_dashboard(self):
        """Ouvre le tableau de bord"""
        logger.info(f"_open_dashboard called, current dashboard_open flag: {self.dashboard_open}")
        
        # Éviter d'ouvrir plusieurs fois le dashboard
        if self.dashboard_open:
            logger.warning("Dashboard déjà ouvert, ignoring duplicate call")
            return
        
        self.dashboard_open = True
        logger.info("Opening dashboard...")
        
        try:
            # Si nous sommes dans le wrapper, appeler sa méthode
            if self.parent_app:
                logger.info("Calling parent_app._show_dashboard()")
                self.parent_app._show_dashboard(language=self.selected_language)
            else:
                # Mode standalone (legacy) - créer le dashboard comme avant
                logger.info("Creating AdminDashboard in standalone mode")
                from ui.screens.admin.admin_dashboard import AdminDashboard
                dashboard = AdminDashboard(parent=self.master, language=self.selected_language, theme=self.theme)
                
                def on_dashboard_close():
                    logger.info("Dashboard closed by user - Restarting login")
                    dashboard.destroy()
                    self.dashboard_open = False
                    self.entry_password.delete(0, "end")
                    self.entry_username.delete(0, "end")
                    self.entry_username.insert(0, "admin")
                    self.entry_password.insert(0, "admin123")
                    self.status_label.configure(text="")
                    self.entry_username.configure(state="normal")
                    self.entry_password.configure(state="normal")
                    self.login_btn.configure(state="normal")
                
                dashboard.protocol("WM_DELETE_WINDOW", on_dashboard_close)
                dashboard.deiconify()
                dashboard.lift()
                dashboard.focus_set()
                
        except Exception as e:
            self.dashboard_open = False
            logger.error(f"Erreur ouverture dashboard: {e}", exc_info=True)
            self.status_label.configure(
                text="❌ Error: " + str(e)[:50],
                text_color="#FF4444"
            )
            self.entry_username.configure(state="normal")
            self.entry_password.configure(state="normal")
            self.login_btn.configure(state="normal")
            # Réactiver les champs
            self.entry_username.configure(state="normal")
            self.entry_password.configure(state="normal")
            self.login_btn.configure(state="normal")
