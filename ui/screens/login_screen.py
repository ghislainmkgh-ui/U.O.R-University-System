"""Écran de connexion moderne et compact"""
import customtkinter as ctk
import logging
import threading
from tkinter import messagebox
from PIL import Image
import os
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
        self.content_frame = None
        self.icon_frame = None
        self.title_label = None
        
        # Widgets à ajuster pour responsive
        self.responsive_widgets = {}

        self._create_ui()
        self._set_window_size()
        
        # Bind resize event pour responsive
        self.bind("<Configure>", self._on_window_resize)

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
        """Crée l'interface exactement comme l'image de référence"""
        # ===== MAIN CONTAINER avec logo en arrière-plan =====
        main = ctk.CTkFrame(self, fg_color="#5DD3E0")
        main.pack(fill="both", expand=True)
        self.main_frame = main
        
        # Charger et afficher le logo UOR en arrière-plan (AVANT tout le reste)
        self.bg_logo_label = None
        try:
            logo_path = os.path.join("assets", "uor_logo.jpg")
            if os.path.exists(logo_path):
                # Charger l'image
                logo_img = Image.open(logo_path)
                
                # Convertir en RGBA pour supporter la transparence
                if logo_img.mode != 'RGBA':
                    logo_img = logo_img.convert('RGBA')
                
                # Redimensionner le logo pour l'arrière-plan (plus grand)
                logo_img = logo_img.resize((600, 600), Image.Resampling.LANCZOS)
                
                # Créer une version semi-transparente (plus visible)
                alpha = logo_img.split()[3]
                alpha = alpha.point(lambda p: int(p * 0.30))  # 30% d'opacité (plus visible)
                logo_img.putalpha(alpha)
                
                # Créer CTkImage pour CustomTkinter
                self.bg_logo_ctk = ctk.CTkImage(
                    light_image=logo_img,
                    dark_image=logo_img,
                    size=(600, 600)
                )
                
                # Créer un canvas pour le logo en arrière-plan
                logo_container = ctk.CTkFrame(main, fg_color="#5DD3E0")
                logo_container.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0, relheight=1.0)
                
                # Afficher le logo en arrière-plan avec CTkLabel
                logo_label = ctk.CTkLabel(
                    logo_container, 
                    image=self.bg_logo_ctk,
                    text=""
                )
                logo_label.place(relx=0.5, rely=0.5, anchor="center")
                self.bg_logo_label = logo_label
                
                # Mettre le logo en arrière-plan (lower dans le z-order)
                logo_container.lower()
                
                logger.info(f"UOR logo loaded successfully: {logo_path}")
            else:
                logger.warning(f"UOR logo not found at {logo_path}")
        except Exception as e:
            logger.error(f"Could not load UOR logo: {e}", exc_info=True)

        # ===== TOP BAR =====
        topbar = ctk.CTkFrame(main, fg_color="#5DD3E0", height=50)
        topbar.pack(fill="x", padx=20, pady=(10, 0))
        topbar.pack_propagate(False)

        spacer = ctk.CTkFrame(topbar, fg_color="#5DD3E0")
        spacer.pack(side="left", expand=True)

        ctk.CTkLabel(topbar, text="🌐", font=ctk.CTkFont(size=14), text_color="#2d6d7a").pack(
            side="right", padx=(0, 10)
        )

        self.lang_switch = ctk.CTkSegmentedButton(
            topbar, values=["FR", "EN"], command=self._on_language_change, 
            font=ctk.CTkFont(size=11, weight="bold"), 
            fg_color="#3EB8C8", 
            selected_color="#2d6d7a", 
            text_color="#1a4a54",
            selected_hover_color="#265d68"
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.pack(side="right")

        # ===== CENTER CONTAINER =====
        center = ctk.CTkFrame(main, fg_color="#5DD3E0")
        center.pack(fill="both", expand=True, padx=20, pady=20)

        # ===== LOGIN CARD (avec effet d'ombre via layers) =====
        # Shadow layer (légère)
        shadow_frame = ctk.CTkFrame(
            center, 
            fg_color="#3EB8C8", 
            corner_radius=15
        )
        shadow_frame.pack(anchor="center", padx=15, pady=15)
        shadow_frame.pack_propagate(False)
        
        # Main card
        card = ctk.CTkFrame(
            shadow_frame, 
            fg_color="#3E4F5A",  # Couleur exacte de l'image
            corner_radius=12
        )
        card.pack(padx=8, pady=8, fill="both", expand=True)
        self.card_outer = shadow_frame
        self.card_inner = card

        # ===== CARD CONTENT =====
        content = ctk.CTkFrame(card, fg_color="#3E4F5A")
        content.pack(padx=32, pady=32, fill="both", expand=False)
        self.content_frame = content

        # Icon circle avec camera
        icon_frame = ctk.CTkFrame(
            content, 
            fg_color="#547885",  # Couleur interne du cercle
            corner_radius=35, 
            width=70, 
            height=70
        )
        icon_frame.pack(pady=(0, 16))
        icon_frame.pack_propagate(False)
        self.icon_frame = icon_frame
        
        # Camera icon
        camera_icon = ctk.CTkLabel(
            icon_frame, 
            text="📷", 
            font=ctk.CTkFont(size=28), 
            text_color="#B8C5CB"
        )
        camera_icon.pack(expand=True)
        self.responsive_widgets['camera_icon'] = camera_icon

        # Title: USER LOGIN
        title_label = ctk.CTkLabel(
            content, 
            text="USER LOGIN", 
            font=ctk.CTkFont(size=16, weight="bold", family="Arial"), 
            text_color="#B8C5CB"
        )
        title_label.pack(pady=(0, 24))
        self.title_label = title_label
        self.responsive_widgets['title_label'] = title_label

        # Email ID
        email_label = ctk.CTkLabel(
            content, 
            text="📧  Email ID", 
            font=ctk.CTkFont(size=11), 
            text_color="#8A9CA5",
            anchor="w"
        )
        email_label.pack(anchor="w", pady=(0, 6))
        self.responsive_widgets['email_label'] = email_label

        self.entry_username = ctk.CTkEntry(
            content, 
            placeholder_text="", 
            height=36, 
            corner_radius=5, 
            border_width=1,
            fg_color="#2A3940", 
            border_color="#5A6B75", 
            text_color="#FFFFFF", 
            font=ctk.CTkFont(size=11)
        )
        self.entry_username.pack(fill="x", pady=(0, 18))
        self.entry_username.insert(0, "admin")

        # Password
        password_label = ctk.CTkLabel(
            content, 
            text="🔒  Password", 
            font=ctk.CTkFont(size=11), 
            text_color="#8A9CA5",
            anchor="w"
        )
        password_label.pack(anchor="w", pady=(0, 6))
        self.responsive_widgets['password_label'] = password_label

        self.entry_password = ctk.CTkEntry(
            content, 
            placeholder_text="", 
            height=36, 
            show="•", 
            corner_radius=5, 
            border_width=1,
            fg_color="#2A3940", 
            border_color="#5A6B75", 
            text_color="#FFFFFF", 
            font=ctk.CTkFont(size=11)
        )
        self.entry_password.pack(fill="x", pady=(0, 14))
        self.entry_password.insert(0, "admin123")

        # Options row: Remember me + Forgot Password
        opts = ctk.CTkFrame(content, fg_color="#3E4F5A")
        opts.pack(fill="x", pady=(0, 12))

        self.remember_me = ctk.CTkCheckBox(
            opts, 
            text="Remember me", 
            checkbox_height=16, 
            checkbox_width=16, 
            font=ctk.CTkFont(size=10), 
            text_color="#8A9CA5", 
            fg_color="#5DD3E0", 
            hover_color="#4DC2D0", 
            border_color="#5A6B75"
        )
        self.remember_me.pack(side="left")

        forgot_label = ctk.CTkLabel(
            opts, 
            text="Forgot Password?", 
            font=ctk.CTkFont(size=10), 
            text_color="#8A9CA5", 
            cursor="hand2"
        )
        forgot_label.pack(side="right")

        # Status label (pour les erreurs)
        self.status_label = ctk.CTkLabel(
            content, 
            text="", 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#FFB4B4"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # LOGIN BUTTON (noir comme dans l'image)
        self.login_btn = ctk.CTkButton(
            content, 
            text="LOGIN", 
            height=40, 
            font=ctk.CTkFont(size=12, weight="bold"), 
            fg_color="#1A1A1A",  # Noir pur
            hover_color="#000000", 
            text_color="#FFFFFF", 
            corner_radius=5, 
            command=self._on_login
        )
        self.login_btn.pack(fill="x", pady=(0, 0))

    def _update_card_size(self, window_width: int, window_height: int):
        """Ajuste la taille de la card de manière responsive."""
        try:
            # Calcul responsive de la taille de la card
            if window_height < 600:
                # Très petit écran
                card_height = min(window_height - 80, 450)
                card_width = min(window_width - 40, 340)
                padding = 16
                icon_size = 50
                title_font_size = 13
                label_font_size = 9
            elif window_height < 700:
                # Petit écran
                card_height = min(window_height - 100, 480)
                card_width = min(window_width - 60, 360)
                padding = 20
                icon_size = 60
                title_font_size = 14
                label_font_size = 10
            else:
                # Écran normal/grand
                card_height = 500
                card_width = 380
                padding = 32
                icon_size = 70
                title_font_size = 16
                label_font_size = 11
            
            if self.card_outer is not None:
                self.card_outer.configure(width=card_width, height=card_height)
                self.card_outer.pack_propagate(False)
            
            # Ajuster le padding du contenu
            if self.content_frame is not None:
                self.content_frame.pack_configure(padx=padding, pady=padding)
            
            # Ajuster la taille de l'icône
            if self.icon_frame is not None:
                self.icon_frame.configure(width=icon_size, height=icon_size)
                corner_radius = icon_size // 2
                self.icon_frame.configure(corner_radius=corner_radius)
            
            # Ajuster les tailles de police
            if 'camera_icon' in self.responsive_widgets:
                icon_font_size = int(icon_size * 0.4)
                self.responsive_widgets['camera_icon'].configure(
                    font=ctk.CTkFont(size=icon_font_size)
                )
            
            if 'title_label' in self.responsive_widgets:
                self.responsive_widgets['title_label'].configure(
                    font=ctk.CTkFont(size=title_font_size, weight="bold", family="Arial")
                )
            
            for widget_name in ['email_label', 'password_label']:
                if widget_name in self.responsive_widgets:
                    self.responsive_widgets[widget_name].configure(
                        font=ctk.CTkFont(size=label_font_size)
                    )
            
            # Ajuster la hauteur des inputs
            input_height = 36 if window_height >= 600 else 32
            if hasattr(self, 'entry_username'):
                self.entry_username.configure(height=input_height)
            if hasattr(self, 'entry_password'):
                self.entry_password.configure(height=input_height)
            
            # Ajuster la hauteur du bouton
            button_height = 40 if window_height >= 600 else 36
            if hasattr(self, 'login_btn'):
                self.login_btn.configure(height=button_height)
                
        except Exception as e:
            logger.error(f"Error updating card size: {e}")
            pass

    def _sync_card_size(self):
        """Ajuste la card de manière responsive."""
        if self.card_outer is None or self.card_inner is None:
            return
        try:
            self.update_idletasks()
            
            if self._last_window_size:
                window_width, window_height = self._last_window_size
            else:
                window_width = self.winfo_width()
                window_height = self.winfo_height()
            
            self._update_card_size(window_width, window_height)
        except Exception as e:
            logger.error(f"Error syncing card size: {e}")
            pass
    
    def _on_window_resize(self, event=None):
        """Gère le redimensionnement de la fenêtre pour responsive design."""
        try:
            # Éviter les appels trop fréquents
            if hasattr(self, '_resize_after_id'):
                self.after_cancel(self._resize_after_id)
            
            self._resize_after_id = self.after(100, self._apply_responsive_layout)
        except Exception:
            pass
    
    def _apply_responsive_layout(self):
        """Applique le layout responsive."""
        try:
            window_width = self.winfo_width()
            window_height = self.winfo_height()
            
            if window_width > 0 and window_height > 0:
                self._last_window_size = (window_width, window_height)
                self._update_card_size(window_width, window_height)
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
            self.status_label.configure(text="Veuillez entrer vos identifiants")
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
                        progress.set_progress(30, "Initialisation de l'interface...")
                        
                        dashboard = AdminDashboard(
                            parent=parent_frame, language=self.selected_language, theme=self.theme
                        )
                        
                        progress.set_progress(70, "Chargement des données...")
                        
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
                self.status_label.configure(text="Connexion échouée")
                self.dashboard_open = False
                if login_btn:
                    login_btn.configure(state="normal")
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.status_label.configure(text=f"Erreur: {str(e)}")
            self.dashboard_open = False
            if login_btn:
                login_btn.configure(state="normal")
