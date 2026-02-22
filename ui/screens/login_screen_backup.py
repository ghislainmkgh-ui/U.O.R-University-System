"""Écran de connexion moderne avec design two-column"""
import customtkinter as ctk
import logging
import os
from PIL import Image
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
            logger.info("LoginScreen created as standalone window")
        
        self.selected_language = "FR"
        self.translator = Translator(self.selected_language)
        self.theme = ThemeManager("light")
        self.auth_service = AuthenticationService()
        self.dashboard_open = False  # Flag pour éviter les ouvertures multiples
        
        self._create_ui()
        self._set_window_size()
    
    def _set_window_size(self):
        """Configure la taille de la fenêtre (responsive)"""
        # Obtenir les dimensions de l'écran
        top = self.winfo_toplevel()
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        
        # Responsive: adapte la taille selon l'écran
        if screen_width < 900:
            # Petit écran: prendre 90% du width
            window_width = min(int(screen_width * 0.9), 800)
            window_height = min(int(screen_height * 0.85), 700)
        elif screen_width < 1400:
            # Moyen écran: 70% du width
            window_width = min(int(screen_width * 0.7), 900)
            window_height = min(int(screen_height * 0.8), 750)
        else:
            # Grand écran: 60% du width
            window_width = min(int(screen_width * 0.6), 1000)
            window_height = min(int(screen_height * 0.75), 800)
        
        # S'assurer que c'est minimum acceptable
        window_width = max(500, window_width)
        window_height = max(550, window_height)
        
        # Centrer la fenêtre
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        top.resizable(True, True)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _create_ui(self):
        """Crée l'interface de connexion (responsive, sans place())"""
        # Main container avec background graduel
        main_frame = ctk.CTkFrame(self, fg_color="#59c2cf")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Centering container (grid pour centrer)
        center_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        center_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        center_container.grid_columnconfigure(0, weight=1)
        center_container.grid_rowconfigure(1, weight=1)

        # === TOP BAR: Language selector ===
        topbar = ctk.CTkFrame(center_container, fg_color="transparent")
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        topbar.grid_columnconfigure(0, weight=1)
        
        spacer = ctk.CTkFrame(topbar, fg_color="transparent")
        spacer.grid(row=0, column=0, sticky="w")

        lang_label = ctk.CTkLabel(
            topbar,
            text="🌐",
            font=ctk.CTkFont(size=12),
            text_color="#0b3d4f"
        )
        lang_label.grid(row=0, column=1, sticky="e", padx=(0, 8))

        self.lang_switch = ctk.CTkSegmentedButton(
            topbar,
            values=["FR", "EN"],
            command=self._on_language_change,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#8ed6df",
            selected_color="#0b3d4f",
            selected_hover_color="#0a3342",
            text_color="#0b3d4f"
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.grid(row=0, column=2, sticky="e")

        # === CENTER: Login card ===
        spacer_frame = ctk.CTkFrame(center_container, fg_color="transparent")
        spacer_frame.grid(row=1, column=0, sticky="nsew")
        spacer_frame.grid_columnconfigure(0, weight=1)
        spacer_frame.grid_rowconfigure(0, weight=1)

        card_outer = ctk.CTkFrame(
            spacer_frame,
            fg_color="#3f7f90",
            corner_radius=12,
            border_width=2,
            border_color="#a6dbe1"
        )
        card_outer.grid(row=0, column=0, sticky="nsew")

        card_inner = ctk.CTkFrame(
            card_outer,
            fg_color="#2c5f6f",
            corner_radius=10,
            border_width=1,
            border_color="#6fb3bf"
        )
        card_inner.pack(padx=16, pady=16)

        card_content = ctk.CTkFrame(card_inner, fg_color="transparent")
        card_content.pack(padx=24, pady=20)

        # Icon circle
        icon_ring = ctk.CTkFrame(
            card_content,
            fg_color="#2c5f6f",
            corner_radius=36,
            border_width=2,
            border_color="#8ed6df",
            width=72,
            height=72
        )
        icon_ring.pack(pady=(0, 14))
        icon_ring.pack_propagate(False)
        ctk.CTkLabel(
            icon_ring,
            text="📷",
            font=ctk.CTkFont(size=28),
            text_color="#8ed6df"
        ).pack()

        # Title
        ctk.CTkLabel(
            card_content,
            text="USER LOGIN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#cfeff2"
        ).pack(pady=(0, 16))

        # Description (responsive)
        ctk.CTkLabel(
            card_content,
            text="U.O.R Access Control System",
            font=ctk.CTkFont(size=10),
            text_color="#a6dbe1"
        ).pack(pady=(0, 18))

        # Email field
        ctk.CTkLabel(
            card_content,
            text="Email ID",
            font=ctk.CTkFont(size=11),
            text_color="#bde3ea"
        ).pack(anchor="w")

        self.entry_username = ctk.CTkEntry(
            card_content,
            placeholder_text="",
            height=36,
            corner_radius=4,
            border_width=1,
            bg_color="#2c5f6f",
            fg_color="#1a3a47",
            border_color="#6fb3bf",
            text_color="#e8f7f9",
            font=ctk.CTkFont(size=11)
        )
        self.entry_username.pack(fill="x", pady=(2, 12))
        self.entry_username.insert(0, "admin")

        # Password field
        ctk.CTkLabel(
            card_content,
            text="Password",
            font=ctk.CTkFont(size=11),
            text_color="#bde3ea"
        ).pack(anchor="w")

        self.entry_password = ctk.CTkEntry(
            card_content,
            placeholder_text="",
            height=36,
            show="•",
            corner_radius=4,
            border_width=1,
            bg_color="#2c5f6f",
            fg_color="#1a3a47",
            border_color="#6fb3bf",
            text_color="#e8f7f9",
            font=ctk.CTkFont(size=11)
        )
        self.entry_password.pack(fill="x", pady=(2, 12))
        self.entry_password.insert(0, "admin123")

        # Checkbox and forgot password
        options_frame = ctk.CTkFrame(card_content, fg_color="transparent")
        options_frame.pack(fill="x", pady=(2, 14))
        options_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkCheckBox(
            options_frame,
            text="Remember me",
            checkbox_height=14,
            checkbox_width=14,
            font=ctk.CTkFont(size=9),
            text_color="#bde3ea",
            fg_color="#8ed6df",
            hover_color="#7ccad6",
            border_color="#8ed6df"
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            options_frame,
            text="Forgot Password?",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#cfeff2",
            cursor="hand2"
        ).grid(row=0, column=1, sticky="e")

        # Status label  
        self.status_label = ctk.CTkLabel(
            card_content,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ffb4b4",
            wraplength=250
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # Login button
        self.login_btn = ctk.CTkButton(
            card_content,
            text="LOGIN",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0a2230",
            hover_color="#071923",
            text_color="#e8f7f9",
            corner_radius=4,
            command=self._on_login
        )
        self.login_btn.pack(fill="x")
    
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
