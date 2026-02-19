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
        """Configure la taille de la fenêtre"""
        # Obtenir les dimensions de l'écran
        top = self.winfo_toplevel()
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()
        
        # Taille fixe (ne jamais dépasser ce format)
        window_width = 860
        window_height = 760
        
        # Centrer la fenêtre
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        top.resizable(True, True)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _create_ui(self):
        """Crée l'interface de connexion modernisée (style carte centrée)"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="#59c2cf")
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Language selector (top right)
        lang_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        lang_frame.place(relx=1, rely=0, x=-24, y=18, anchor="ne")

        self.lang_switch = ctk.CTkSegmentedButton(
            lang_frame,
            values=["FR", "EN"],
            command=self._on_language_change,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#8ed6df",
            selected_color="#0b3d4f",
            selected_hover_color="#0a3342",
            text_color="#0b3d4f"
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.pack(side="left")

        # Center card
        card_outer = ctk.CTkFrame(
            main_frame,
            fg_color="#3f7f90",
            corner_radius=8,
            border_width=2,
            border_color="#a6dbe1"
        )
        card_outer.place(relx=0.5, rely=0.5, anchor="center")

        card_inner = ctk.CTkFrame(
            card_outer,
            fg_color="#2c5f6f",
            corner_radius=6,
            border_width=1,
            border_color="#6fb3bf"
        )
        card_inner.pack(padx=18, pady=18)

        card_content = ctk.CTkFrame(card_inner, fg_color="transparent")
        card_content.pack(padx=28, pady=26)

        # Icon circle
        icon_ring = ctk.CTkFrame(card_content, fg_color="#2c5f6f", corner_radius=36, border_width=2, border_color="#8ed6df")
        icon_ring.pack(pady=(0, 12))
        ctk.CTkLabel(icon_ring, text="📷", font=ctk.CTkFont(size=22), text_color="#8ed6df").pack(padx=14, pady=10)

        # Title
        ctk.CTkLabel(
            card_content,
            text="USER LOGIN",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#cfeff2"
        ).pack(pady=(0, 16))

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
            height=34,
            corner_radius=2,
            border_width=0,
            fg_color="#2c5f6f",
            text_color="#e8f7f9",
            font=ctk.CTkFont(size=12)
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
            height=34,
            show="•",
            corner_radius=2,
            border_width=0,
            fg_color="#2c5f6f",
            text_color="#e8f7f9",
            font=ctk.CTkFont(size=12)
        )
        self.entry_password.pack(fill="x", pady=(2, 12))
        self.entry_password.insert(0, "admin123")

        # Remember me + Forgot password
        checkbox_frame = ctk.CTkFrame(card_content, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(2, 14))

        ctk.CTkCheckBox(
            checkbox_frame,
            text="Remember me",
            checkbox_height=14,
            checkbox_width=14,
            font=ctk.CTkFont(size=10),
            text_color="#bde3ea",
            fg_color="#8ed6df",
            hover_color="#7ccad6",
            border_color="#8ed6df"
        ).pack(side="left")

        ctk.CTkLabel(
            checkbox_frame,
            text="Forgot Password?",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#cfeff2",
            cursor="hand2"
        ).pack(side="right")

        # Status label
        self.status_label = ctk.CTkLabel(
            card_content,
            text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#ffb4b4"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # Login button
        self.login_btn = ctk.CTkButton(
            card_content,
            text="LOGIN",
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0a2230",
            hover_color="#071923",
            text_color="#e8f7f9",
            corner_radius=2,
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
