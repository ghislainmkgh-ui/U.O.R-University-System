"""Écran de connexion moderne et compact"""
import customtkinter as ctk
import logging
import threading
from tkinter import messagebox
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from app.services.auth.authentication_service import AuthenticationService
from ui.screens.admin.admin_dashboard import AdminDashboard
from ui.components.modern_loading import ProgressTracker

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTkFrame):
    """Écran de connexion moderne et simple"""

    def __init__(self, parent_app=None, parent=None):
        if parent_app:
            super().__init__(parent_app)
            self.parent_app = parent_app
            self.is_standalone = False
            self.pack(fill="both", expand=True)
            logger.info("LoginScreen created as child of AppWrapper")
        else:
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
        self.dashboard_open = False
        self.progress_tracker = ProgressTracker()

        self.card_outer = None
        self.card_inner = None
        self._last_window_size = None

        self._create_ui()
        self._set_window_size()

    def _set_window_size(self):
        """Configure la taille de la fenêtre (responsive)"""
        top = self.winfo_toplevel()
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()

        if screen_width < 900:
            window_width = min(int(screen_width * 0.9), 800)
            window_height = min(int(screen_height * 0.85), 700)
        elif screen_width < 1400:
            window_width = min(int(screen_width * 0.7), 900)
            window_height = min(int(screen_height * 0.8), 750)
        else:
            window_width = min(int(screen_width * 0.6), 1000)
            window_height = min(int(screen_height * 0.75), 800)

        window_width = max(520, window_width)
        window_height = max(520, window_height)

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        top.resizable(True, True)
        self._last_window_size = (window_width, window_height)
        self._update_card_size(window_width, window_height)
        self.after(50, self._sync_card_size)

    def _create_ui(self):
        """Crée l'interface SIMPLE à 100% pack()"""
        # ===== MAIN CONTAINER =====
        main = ctk.CTkFrame(self, fg_color="#59c2cf")
        main.pack(fill="both", expand=True)

        # ===== TOP BAR =====
        topbar = ctk.CTkFrame(main, fg_color="transparent", height=44)
        topbar.pack(fill="x", padx=20, pady=(8, 4))
        topbar.pack_propagate(False)

        spacer = ctk.CTkFrame(topbar, fg_color="transparent")
        spacer.pack(side="left", expand=True)

        ctk.CTkLabel(topbar, text="🌐", font=ctk.CTkFont(size=12), text_color="#0b3d4f").pack(
            side="right", padx=(0, 8)
        )

        self.lang_switch = ctk.CTkSegmentedButton(
            topbar,
            values=["FR", "EN"],
            command=self._on_language_change,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#8ed6df",
            selected_color="#0b3d4f",
            text_color="#0b3d4f",
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.pack(side="right")

        # ===== CENTER CONTAINER =====
        center = ctk.CTkFrame(main, fg_color="transparent")
        center.pack(fill="both", expand=True, padx=24, pady=24)

        # ===== CARD OUTER =====
        card_outer = ctk.CTkFrame(
            center, fg_color="#3f7f90", corner_radius=12, border_width=2, border_color="#a6dbe1"
        )
        card_outer.pack(anchor="center")
        card_outer.pack_propagate(False)
        self.card_outer = card_outer

        # ===== CARD INNER =====
        card_inner = ctk.CTkFrame(
            card_outer, fg_color="#2c5f6f", corner_radius=10, border_width=1, border_color="#6fb3bf"
        )
        card_inner.pack(padx=10, pady=10, fill="both", expand=True)
        self.card_inner = card_inner

        # ===== CARD CONTENT =====
        content = ctk.CTkFrame(card_inner, fg_color="transparent")
        content.pack(padx=16, pady=12, fill="both", expand=False)

        # Icon
        icon_frame = ctk.CTkFrame(
            content, fg_color="#2c5f6f", corner_radius=28, border_width=2, border_color="#8ed6df",
            width=56, height=56
        )
        icon_frame.pack(pady=(0, 8))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="📷", font=ctk.CTkFont(size=20), text_color="#8ed6df").pack()

        # Title
        ctk.CTkLabel(
            content, text="USER LOGIN", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cfeff2"
        ).pack(pady=(0, 4))

        # Subtitle
        ctk.CTkLabel(
            content, text="U.O.R Access Control System", font=ctk.CTkFont(size=9), text_color="#a6dbe1"
        ).pack(pady=(0, 12))

        # Email label
        ctk.CTkLabel(content, text="Email ID", font=ctk.CTkFont(size=10), text_color="#bde3ea").pack(anchor="w")

        # Email input
        self.entry_username = ctk.CTkEntry(
            content,
            placeholder_text="",
            height=28,
            corner_radius=4,
            border_width=1,
            bg_color="#2c5f6f",
            fg_color="#1a3a47",
            border_color="#6fb3bf",
            text_color="#e8f7f9",
            font=ctk.CTkFont(size=10),
        )
        self.entry_username.pack(fill="x", pady=(2, 10))
        self.entry_username.insert(0, "admin")

        # Password label
        ctk.CTkLabel(content, text="Password", font=ctk.CTkFont(size=10), text_color="#bde3ea").pack(anchor="w")

        # Password input
        self.entry_password = ctk.CTkEntry(
            content,
            placeholder_text="",
            height=28,
            show="•",
            corner_radius=4,
            border_width=1,
            bg_color="#2c5f6f",
            fg_color="#1a3a47",
            border_color="#6fb3bf",
            text_color="#e8f7f9",
            font=ctk.CTkFont(size=10),
        )
        self.entry_password.pack(fill="x", pady=(2, 10))
        self.entry_password.insert(0, "admin123")

        # Options row
        opts = ctk.CTkFrame(content, fg_color="transparent")
        opts.pack(fill="x", pady=(4, 8))

        ctk.CTkCheckBox(
            opts,
            text="Remember me",
            checkbox_height=12,
            checkbox_width=12,
            font=ctk.CTkFont(size=8),
            text_color="#bde3ea",
            fg_color="#8ed6df",
            hover_color="#7ccad6",
            border_color="#8ed6df",
        ).pack(side="left")

        ctk.CTkLabel(
            opts,
            text="Forgot Password?",
            font=ctk.CTkFont(size=8, weight="bold"),
            text_color="#cfeff2",
            cursor="hand2",
        ).pack(side="right")

        # Status label
        self.status_label = ctk.CTkLabel(
            content, text="", font=ctk.CTkFont(size=9, weight="bold"), text_color="#ffb4b4"
        )
        self.status_label.pack(fill="x", pady=(0, 6))

        # LOGIN BUTTON
        self.login_btn = ctk.CTkButton(
            content,
            text="LOGIN",
            height=32,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0a2230",
            hover_color="#071923",
            text_color="#e8f7f9",
            corner_radius=4,
            command=self._on_login,
        )
        self.login_btn.pack(fill="x", pady=(4, 0))

    def _update_card_size(self, window_width: int, window_height: int):
        """Ajuste la taille de la card pour éviter un rendu trop large."""
        try:
            card_width = max(360, min(460, int(window_width * 0.55)))
            card_height = max(360, min(460, int(window_height * 0.6)))
            if self.card_outer is not None:
                self.card_outer.configure(width=card_width, height=card_height)
                self.card_outer.pack_propagate(False)
        except Exception:
            pass

    def _sync_card_size(self):
        """Ajuste la card pour qu'elle contienne toujours le bouton LOGIN."""
        if self.card_outer is None or self.card_inner is None:
            return
        try:
            self.update_idletasks()
            desired_width = self.card_inner.winfo_reqwidth() + 20
            desired_height = self.card_inner.winfo_reqheight() + 20

            if self._last_window_size:
                window_width, window_height = self._last_window_size
            else:
                window_width = self.winfo_width()
                window_height = self.winfo_height()

            max_width = int(window_width * 0.7)
            max_height = int(window_height * 0.8)

            card_width = max(360, min(max_width, desired_width))
            card_height = max(360, min(max_height, desired_height))

            self.card_outer.configure(width=card_width, height=card_height)
            self.card_outer.pack_propagate(False)
        except Exception:
            pass

    def _on_language_change(self, value):
        """Change la langue"""
        if value == self.selected_language:
            return
        if self.dashboard_open:
            return

        self.selected_language = value
        self.translator = Translator(value)
        logger.info(f"Language changed to: {value}")

    def _on_login(self):
        """Gère la connexion avec loading moderne intégré"""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.status_label.configure(text="Please enter credentials")
            return

        # Désactiver le bouton login
        login_btn = getattr(self, 'login_btn', None)
        if login_btn:
            login_btn.configure(state="disabled")

        try:
            self.dashboard_open = True
            user, error = self.auth_service.authenticate(username, password)

            if error:
                self.status_label.configure(text=error)
                self.dashboard_open = False
                if login_btn:
                    login_btn.configure(state="normal")
                return

            if user:
                logger.info(f"User {user.get('email')} logged in successfully")
                
                # Créer l'overlay de loading sur la même page
                parent_frame = self.winfo_toplevel()
                progress = self.progress_tracker.create_overlay(parent_frame)
                progress.set_progress(10, "Authentification validée...")
                
                # Charger le dashboard en arrière-plan
                def load_dashboard():
                    try:
                        progress.set_progress(30, "Initialisation interface...")
                        
                        dashboard = AdminDashboard(
                            parent=parent_frame,
                            language=self.selected_language,
                            theme=self.theme
                        )
                        
                        progress.set_progress(70, "Chargement données...")
                        
                        # Attendre que le dashboard soit rendu
                        parent_frame.update_idletasks()
                        
                        progress.set_progress(90, "Finalisation...")
                        
                        # Passer le dashboard à l'app parent
                        if self.parent_app:
                            self.parent_app.dashboard = dashboard
                        
                        # Cacher le login
                        self.pack_forget()
                        
                        # Terminer le loading
                        progress.complete()
                        
                        self.dashboard_open = False
                    except Exception as e:
                        logger.error(f"Dashboard init error: {e}")
                        progress.place_forget()
                        self.dashboard_open = False
                        if login_btn:
                            login_btn.configure(state="normal")
                        self.status_label.configure(text=f"Erreur: {str(e)}")
                
                # Lancer en thread séparé pour ne pas bloquer l'UI
                thread = threading.Thread(target=load_dashboard, daemon=True)
                thread.start()
            else:
                self.status_label.configure(text="Login failed")
                self.dashboard_open = False
                if login_btn:
                    login_btn.configure(state="normal")
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.status_label.configure(text=f"Error: {str(e)}")
            self.dashboard_open = False
            if login_btn:
                login_btn.configure(state="normal")
