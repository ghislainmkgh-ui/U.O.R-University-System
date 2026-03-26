"""Écran de connexion moderne et compact"""
import customtkinter as ctk
import logging
import threading
from tkinter import messagebox
import tkinter as tk
from PIL import Image
import os
from time import perf_counter
from ui.i18n.translator import Translator, set_current_language
from ui.responsive import fit_dialog_to_viewport
from ui.theme.theme_manager import ThemeManager
from app.services.auth.authentication_service import AuthenticationService
from ui.components.modern_loading import ProgressTracker
import webbrowser

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTkFrame):
    """Écran de connexion moderne et simple"""

    def __init__(self, parent_app=None, parent=None):
        init_t0 = perf_counter()
        if parent_app:
            super().__init__(parent or parent_app)
            self.parent_app = parent_app
            self.is_standalone = False
            self.pack(fill="both", expand=True)
            logger.info("LoginScreen created as child of AppWrapper")
        elif parent is not None:
            super().__init__(parent)
            self.parent_app = None
            self.is_standalone = False
            self.pack(fill="both", expand=True)
            logger.info("LoginScreen created as embedded page")
        else:
            root = ctk.CTk()
            super().__init__(root)
            self.parent_app = None
            self.is_standalone = True
            self.pack(fill="both", expand=True)
            root.title("U.O.R - Système de Contrôle d'Accès")
            logger.info("LoginScreen created as standalone window")

        saved_state = {}
        if self.parent_app and hasattr(self.parent_app, "get_saved_login_state"):
            try:
                saved_state = self.parent_app.get_saved_login_state() or {}
            except Exception:
                saved_state = {}

        self.selected_language = saved_state.get("language", "FR") or "FR"
        self.translator = Translator(self.selected_language)
        set_current_language(self.selected_language)
        self.theme = ThemeManager(saved_state.get("theme", "light") or "light")
        self.auth_service = None
        self.dashboard_open = False
        self.progress_tracker = ProgressTracker()

        self.card_outer = None
        self.card_inner = None
        self._last_window_size = None
        self._last_applied_window_size = None
        self._last_layout_profile = None
        self._last_compact_mode = None
        self._resize_after_id = None
        self.content_frame = None
        self.icon_frame = None
        self.title_label = None
        self.social_icons = {}
        self.topbar = None
        self.topbar_globe_label = None
        self.hero_frame = None
        self.hero_badge = None
        self.hero_title = None
        self.hero_subtitle = None
        
        # Widgets à ajuster pour responsive
        self.responsive_widgets = {}
        # Widgets à mettre à jour lors d'un changement de langue
        self.translatable_widgets = {}

        self._create_ui()
        self._restore_saved_login_state(saved_state)
        self._set_window_size()
        
        # Bind resize event pour responsive
        self.bind("<Configure>", self._on_window_resize)
        self.winfo_toplevel().bind("<Configure>", self._on_window_resize, add="+")
        logger.info("LoginScreen initialized in %.1f ms", (perf_counter() - init_t0) * 1000)

    def _restore_saved_login_state(self, saved_state: dict):
        """Restaure remember-me uniquement (sans auto-login implicite)."""
        if not isinstance(saved_state, dict):
            return

        remember_me = bool(saved_state.get("remember_me"))
        saved_identifier = saved_state.get("saved_identifier", "") or ""
        saved_password = saved_state.get("saved_password", "") or ""

        try:
            if remember_me and hasattr(self, "remember_me"):
                self.remember_me.select()
            elif hasattr(self, "remember_me"):
                self.remember_me.deselect()
        except Exception:
            pass

        if remember_me and saved_identifier:
            try:
                self.entry_username.delete(0, "end")
                self.entry_username.insert(0, saved_identifier)
            except Exception:
                pass

        if remember_me and saved_password:
            try:
                self.entry_password.delete(0, "end")
                self.entry_password.insert(0, saved_password)
            except Exception:
                pass

        # Important: "Se souvenir de moi" ne déclenche jamais une connexion auto.
        # On conserve uniquement le pré-remplissage des identifiants.

    def _set_window_size(self):
        """Configure la taille de la fenêtre (responsive)"""
        top = self.winfo_toplevel()
        screen_width = top.winfo_screenwidth()
        screen_height = top.winfo_screenheight()

        if not self.is_standalone:
            current_width = top.winfo_width() or max(640, min(int(screen_width * 0.72), 1200))
            current_height = top.winfo_height() or max(680, min(int(screen_height * 0.80), 920))
            self._last_window_size = (current_width, current_height)
            self._update_card_size(current_width, current_height)
            self.after(50, self._sync_card_size)
            return

        if screen_width < 900:
            window_width = min(int(screen_width * 0.9), 800)
            window_height = min(int(screen_height * 0.92), 820)
        elif screen_width < 1400:
            window_width = min(int(screen_width * 0.7), 900)
            window_height = min(int(screen_height * 0.88), 860)
        else:
            window_width = min(int(screen_width * 0.6), 1000)
            window_height = min(int(screen_height * 0.85), 900)

        window_width = max(520, window_width)
        window_height = max(720, window_height)

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
        self.topbar = topbar

        spacer = ctk.CTkFrame(topbar, fg_color="#5DD3E0")
        spacer.pack(side="left", expand=True)

        globe_label = ctk.CTkLabel(topbar, text="🌐", font=ctk.CTkFont(size=14), text_color="#2d6d7a")
        globe_label.pack(
            side="right", padx=(0, 10)
        )
        self.topbar_globe_label = globe_label

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
        self.center_frame = center

        hero_frame = ctk.CTkFrame(center, fg_color="transparent")
        hero_frame.place(relx=0.5, rely=0.11, anchor="n")
        self.hero_frame = hero_frame

        hero_badge = ctk.CTkLabel(
            hero_frame,
            text="UNIVERSITY OF REDEMPTION",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#1f5f6b",
            fg_color="#A7E7EF",
            corner_radius=14,
            padx=14,
            pady=6,
        )
        hero_badge.pack(pady=(0, 12))
        self.hero_badge = hero_badge

        hero_title = ctk.CTkLabel(
            hero_frame,
            text="Bienvenue dans votre espace d'administration",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#134955",
        )
        hero_title.pack()
        self.hero_title = hero_title

        hero_subtitle = ctk.CTkLabel(
            hero_frame,
            text="Connectez-vous pour ouvrir l'application et accéder à votre tableau de bord.",
            font=ctk.CTkFont(size=13),
            text_color="#2d6d7a",
            justify="center",
        )
        hero_subtitle.pack(pady=(8, 0))
        self.hero_subtitle = hero_subtitle

        # ===== LOGIN CARD (avec effet d'ombre via layers) =====
        # Shadow layer (légère)
        shadow_frame = ctk.CTkFrame(
            center, 
            fg_color="#3EB8C8", 
            corner_radius=15
        )
        shadow_frame.place(relx=0.5, rely=0.58, anchor="center")
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
        content = ctk.CTkFrame(
            card,
            fg_color="#3E4F5A",
            corner_radius=0,
        )
        content.pack(padx=24, pady=24, fill="both", expand=True)
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
            text=self.translator.get("user_login", "CONNEXION UTILISATEUR"), 
            font=ctk.CTkFont(size=16, weight="bold", family="Arial"), 
            text_color="#B8C5CB"
        )
        title_label.pack(pady=(0, 24))
        self.title_label = title_label
        self.responsive_widgets['title_label'] = title_label
        self.translatable_widgets['title_label'] = title_label

        # Email ID
        email_label = ctk.CTkLabel(
            content, 
            text=self.translator.get("email_id", "📧  Email / Identifiant"), 
            font=ctk.CTkFont(size=11), 
            text_color="#8A9CA5",
            anchor="w"
        )
        email_label.pack(anchor="w", pady=(0, 6))
        self.responsive_widgets['email_label'] = email_label
        self.translatable_widgets['email_label'] = email_label

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
            text=self.translator.get("password_label", "🔒  Mot de passe"), 
            font=ctk.CTkFont(size=11), 
            text_color="#8A9CA5",
            anchor="w"
        )
        password_label.pack(anchor="w", pady=(0, 6))
        self.responsive_widgets['password_label'] = password_label
        self.translatable_widgets['password_label'] = password_label

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
        self.options_row = opts

        self.remember_me = ctk.CTkCheckBox(
            opts, 
            text=self.translator.get("remember_me", "Se souvenir de moi"), 
            checkbox_height=16, 
            checkbox_width=16, 
            font=ctk.CTkFont(size=10), 
            text_color="#8A9CA5", 
            fg_color="#5DD3E0", 
            hover_color="#4DC2D0", 
            border_color="#5A6B75"
        )
        self.remember_me.pack(side="left")
        self.translatable_widgets['remember_me_cb'] = self.remember_me

        self.forgot_label = ctk.CTkLabel(
            opts, 
            text=self.translator.get("forgot_password", "Mot de passe oublié ?"), 
            font=ctk.CTkFont(size=10), 
            text_color="#8A9CA5", 
            cursor="hand2"
        )
        self.forgot_label.pack(side="right")
        self.forgot_label.bind("<Button-1>", lambda _e: self._show_forgot_password_dialog())
        self.forgot_label.bind("<Enter>", lambda _e: self.forgot_label.configure(text_color="#5DD3E0"))
        self.forgot_label.bind("<Leave>", lambda _e: self.forgot_label.configure(text_color="#8A9CA5"))
        self.translatable_widgets['forgot_label'] = self.forgot_label

        # Status label (pour les erreurs)
        self.status_label = ctk.CTkLabel(
            content, 
            text="", 
            font=ctk.CTkFont(size=10, weight="bold"), 
            text_color="#FFB4B4"
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # LOGIN BUTTON
        action_row = ctk.CTkFrame(content, fg_color="#3E4F5A")
        action_row.pack(fill="x", pady=(0, 0))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)
        self.action_row = action_row

        self.login_btn = ctk.CTkButton(
            action_row,
            text=self.translator.get("login_btn", "CONNEXION"),
            height=42,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1A1A1A",
            hover_color="#000000",
            text_color="#FFFFFF",
            corner_radius=5,
            command=self._on_login
        )
        self.login_btn.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.translatable_widgets['login_btn'] = self.login_btn

        self.create_admin_btn = ctk.CTkButton(
            action_row,
            text=self.translator.get("create_admin_btn", "CRÉER COMPTE"),
            height=42,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2A3940",
            hover_color="#374F5A",
            text_color="#DDE6EA",
            corner_radius=5,
            border_width=1,
            border_color="#5A6B75",
            command=self._show_create_admin_dialog,
        )
        self.create_admin_btn.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self.translatable_widgets['create_admin_btn'] = self.create_admin_btn

        # ===== SOCIAL LOGIN : séparateur + icônes Google & GitHub =====
        or_frame = ctk.CTkFrame(content, fg_color="#3E4F5A")
        or_frame.pack(fill="x", pady=(16, 0))
        self.or_frame = or_frame

        ctk.CTkFrame(or_frame, fg_color="#5A6B75", height=1, corner_radius=0).pack(
            side="left", fill="x", expand=True, pady=8
        )
        self.or_label = ctk.CTkLabel(
            or_frame,
            text=self.translator.get("or_separator", "ou"),
            font=ctk.CTkFont(size=10),
            text_color="#8A9CA5",
            width=30,
        )
        self.or_label.pack(side="left", padx=8)
        self.translatable_widgets['or_label'] = self.or_label
        ctk.CTkFrame(or_frame, fg_color="#5A6B75", height=1, corner_radius=0).pack(
            side="left", fill="x", expand=True, pady=8
        )

        # Deux boutons icône côte-à-côte (logos Google & GitHub)
        social_row = ctk.CTkFrame(content, fg_color="#3E4F5A")
        social_row.pack(fill="x", pady=(10, 4))
        self.social_row = social_row
        social_row.grid_columnconfigure(0, weight=1)
        social_row.grid_columnconfigure(1, weight=1)

        self.google_btn = ctk.CTkButton(
            social_row,
            text=self.translator.get("login_google", "  G   Continuer avec Google"),
            image=self._make_google_icon(34),
            compound="left",
            height=46,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2A3940",
            hover_color="#374F5A",
            text_color="#EAF3F6",
            corner_radius=8,
            border_width=1,
            border_color="#5A6B75",
            command=self._on_google_login,
        )
        self.google_btn.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        self.github_btn = ctk.CTkButton(
            social_row,
            text=self.translator.get("login_github", "  ⬡   Continuer avec GitHub"),
            image=self._make_github_icon(34),
            compound="left",
            height=46,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#2A3940",
            hover_color="#374F5A",
            text_color="#EAF3F6",
            corner_radius=8,
            border_width=1,
            border_color="#5A6B75",
            command=self._on_github_login,
        )
        self.github_btn.grid(row=0, column=1, padx=(5, 0), sticky="nsew")

    def _update_card_size(self, window_width: int, window_height: int):
        """Ajuste la taille de la card de manière responsive."""
        try:
            # Espace vertical réel disponible pour la card (avec marges topbar + conteneurs)
            # Ajusté pour éviter de sous-dimensionner la card sur écrans moyens.
            available_h = max(window_height - 180, 320)

            # Largeur responsive
            aspect_ratio = (window_width / window_height) if window_height > 0 else 1.0
            if window_width < 700:
                card_width = max(min(window_width - 28, 340), 300)
            elif window_width < 1000:
                card_width = max(min(window_width - 56, 390), 320)
            elif window_width < 1700:
                card_width = max(min(int(window_width * 0.42), 460), 340)
            else:
                # Mode ultra-wide : largeur pilotée par ratio pour garder un rendu premium
                if aspect_ratio >= 2.0:  # écrans très larges (21:9+)
                    card_width = max(min(int(window_width * 0.30), 620), 440)
                elif aspect_ratio >= 1.7:  # 16:9 classique en plein écran
                    card_width = max(min(int(window_width * 0.33), 580), 430)
                else:
                    card_width = max(min(int(window_width * 0.35), 560), 420)

            # Densité responsive pilotée par la hauteur utile (empêche le clipping bas)
            if available_h < 470:
                # Mode très compact
                card_height = max(min(available_h, 470), 350)
                padding = 8
                icon_size = 34
                title_font_size = 11
                label_font_size = 8
                input_height = 28
                button_height = 30
                social_button_height = 32
                options_pady = (0, 5)
                or_pady = (6, 0)
                social_pady = (5, 1)
                title_bottom_pady = 10
                icon_bottom_pady = 7
                shadow_pady = 8
            elif available_h < 560:
                # Mode compact
                card_height = max(min(available_h, 560), 420)
                padding = 12
                icon_size = 42
                title_font_size = 12
                label_font_size = 9
                input_height = 31
                button_height = 34
                social_button_height = 36
                options_pady = (0, 7)
                or_pady = (8, 0)
                social_pady = (7, 2)
                title_bottom_pady = 14
                icon_bottom_pady = 10
                shadow_pady = 10
            elif available_h < 700:
                # Mode normal
                card_height = max(min(available_h, 680), 460)
                padding = 16
                icon_size = 54
                title_font_size = 14
                label_font_size = 10
                input_height = 34
                button_height = 38
                social_button_height = 40
                options_pady = (0, 9)
                or_pady = (10, 0)
                social_pady = (8, 3)
                title_bottom_pady = 20
                icon_bottom_pady = 13
                shadow_pady = 12
            else:
                card_height = max(min(available_h, 760), 480)
                padding = 24
                icon_size = 68
                title_font_size = 16
                label_font_size = 11
                input_height = 36
                button_height = 40
                social_button_height = 44
                options_pady = (0, 12)
                or_pady = (16, 0)
                social_pady = (10, 4)
                title_bottom_pady = 24
                icon_bottom_pady = 16
                shadow_pady = 15
            
            # Ajuster la hauteur à la hauteur réelle du contenu pour éviter la zone vide en bas
            try:
                if self.content_frame is not None:
                    self.content_frame.update_idletasks()
                    content_needed = self.content_frame.winfo_reqheight()
                    # marge verticale minimale pour limiter l'espace vide sous les boutons
                    desired = content_needed + 14
                    # borne pour conserver un rendu stable
                    card_height = max(min(desired, available_h), 320)
            except Exception:
                pass

            layout_profile = (
                "xs" if available_h < 470 else "sm" if available_h < 560 else "md" if available_h < 700 else "lg",
                "narrow" if window_width < 700 else "mid" if window_width < 1000 else "wide",
            )
            profile_changed = layout_profile != self._last_layout_profile
            self._last_layout_profile = layout_profile
            compact_mode = window_width < 680 or window_height < 620
            compact_mode_changed = compact_mode != self._last_compact_mode
            self._last_compact_mode = compact_mode

            if self.card_outer is not None:
                current_w = self.card_outer.winfo_width()
                current_h = self.card_outer.winfo_height()
                if abs(current_w - card_width) > 1 or abs(current_h - card_height) > 1:
                    self.card_outer.configure(width=card_width, height=card_height)
                self.card_outer.pack_propagate(False)
                self.card_outer.place_configure(relx=0.5, rely=0.60 if compact_mode else 0.58, anchor="center")
            
            # Ajuster le padding du contenu
            if self.content_frame is not None and profile_changed:
                self.content_frame.pack_configure(padx=padding, pady=padding)
            if hasattr(self, 'options_row') and profile_changed:
                self.options_row.pack_configure(pady=options_pady)
            if hasattr(self, 'or_frame') and profile_changed:
                self.or_frame.pack_configure(pady=or_pady)
            if hasattr(self, 'social_row') and profile_changed:
                self.social_row.pack_configure(pady=social_pady)

            if compact_mode_changed:
                self._apply_compact_layout(compact_mode)

            if self.topbar is not None:
                topbar_height = 46 if compact_mode else 50
                topbar_padx = 12 if compact_mode else 20
                self.topbar.configure(height=topbar_height)
                self.topbar.pack_configure(padx=topbar_padx, pady=(8 if compact_mode else 10, 0))
            if self.center_frame is not None:
                self.center_frame.pack_configure(padx=12 if compact_mode else 20, pady=12 if compact_mode else 20)
            if self.lang_switch is not None:
                self.lang_switch.configure(font=ctk.CTkFont(size=10 if compact_mode else 11, weight="bold"))
            if self.topbar_globe_label is not None:
                self.topbar_globe_label.configure(font=ctk.CTkFont(size=12 if compact_mode else 14))
            if self.hero_frame is not None:
                self.hero_frame.place_configure(relx=0.5, rely=0.07 if compact_mode else 0.11, anchor="n")
            if self.hero_badge is not None:
                self.hero_badge.configure(font=ctk.CTkFont(size=9 if compact_mode else 11, weight="bold"), padx=10 if compact_mode else 14, pady=4 if compact_mode else 6)
            if self.hero_title is not None:
                self.hero_title.configure(font=ctk.CTkFont(size=18 if compact_mode else 28, weight="bold"), wraplength=max(260, window_width - 80))
            if self.hero_subtitle is not None:
                self.hero_subtitle.configure(font=ctk.CTkFont(size=11 if compact_mode else 13), wraplength=max(240, window_width - 120))
            
            # Ajuster la taille de l'icône
            if self.icon_frame is not None:
                self.icon_frame.configure(width=icon_size, height=icon_size)
                corner_radius = icon_size // 2
                self.icon_frame.configure(corner_radius=corner_radius)
                self.icon_frame.pack_configure(pady=(0, icon_bottom_pady))
            
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
                self.responsive_widgets['title_label'].pack_configure(pady=(0, title_bottom_pady))
            
            for widget_name in ['email_label', 'password_label']:
                if widget_name in self.responsive_widgets:
                    self.responsive_widgets[widget_name].configure(
                        font=ctk.CTkFont(size=label_font_size)
                    )
            
            # Ajuster la hauteur des inputs
            if hasattr(self, 'entry_username'):
                self.entry_username.configure(height=input_height)
            if hasattr(self, 'entry_password'):
                self.entry_password.configure(height=input_height)
            
            # Ajuster la hauteur des boutons
            if hasattr(self, 'login_btn'):
                self.login_btn.configure(height=button_height)
            if hasattr(self, 'create_admin_btn'):
                self.create_admin_btn.configure(height=button_height)
            if hasattr(self, 'google_btn'):
                self.google_btn.configure(height=social_button_height)
            if hasattr(self, 'github_btn'):
                self.github_btn.configure(height=social_button_height)
                
        except Exception as e:
            logger.error(f"Error updating card size: {e}")
            pass

    def _apply_compact_layout(self, compact_mode: bool):
        """Réorganise les blocs du login pour petits écrans comme une page web responsive."""
        try:
            if hasattr(self, 'remember_me') and hasattr(self, 'forgot_label') and hasattr(self, 'options_row'):
                self.remember_me.pack_forget()
                self.forgot_label.pack_forget()
                if compact_mode:
                    self.remember_me.pack(anchor="w", pady=(0, 6))
                    self.forgot_label.pack(anchor="w")
                else:
                    self.remember_me.pack(side="left")
                    self.forgot_label.pack(side="right")

            if hasattr(self, 'login_btn') and hasattr(self, 'create_admin_btn'):
                if compact_mode:
                    self.action_row.grid_columnconfigure(0, weight=1)
                    self.action_row.grid_columnconfigure(1, weight=0)
                    self.login_btn.grid_configure(row=0, column=0, columnspan=2, padx=0, pady=(0, 8), sticky="ew")
                    self.create_admin_btn.grid_configure(row=1, column=0, columnspan=2, padx=0, pady=0, sticky="ew")
                else:
                    self.action_row.grid_columnconfigure(0, weight=1)
                    self.action_row.grid_columnconfigure(1, weight=1)
                    self.login_btn.grid_configure(row=0, column=0, columnspan=1, padx=(0, 8), pady=0, sticky="nsew")
                    self.create_admin_btn.grid_configure(row=0, column=1, columnspan=1, padx=(8, 0), pady=0, sticky="nsew")

            if hasattr(self, 'google_btn') and hasattr(self, 'github_btn') and hasattr(self, 'social_row'):
                if compact_mode:
                    self.social_row.grid_columnconfigure(0, weight=1)
                    self.social_row.grid_columnconfigure(1, weight=0)
                    self.google_btn.grid_configure(row=0, column=0, columnspan=2, padx=0, pady=(0, 8), sticky="ew")
                    self.github_btn.grid_configure(row=1, column=0, columnspan=2, padx=0, pady=0, sticky="ew")
                    self.google_btn.configure(text="Google")
                    self.github_btn.configure(text="GitHub")
                else:
                    self.social_row.grid_columnconfigure(0, weight=1)
                    self.social_row.grid_columnconfigure(1, weight=1)
                    self.google_btn.grid_configure(row=0, column=0, columnspan=1, padx=(0, 5), pady=0, sticky="nsew")
                    self.github_btn.grid_configure(row=0, column=1, columnspan=1, padx=(5, 0), pady=0, sticky="nsew")
                    self.google_btn.configure(text=self.translator.get("login_google", "  G   Continuer avec Google"))
                    self.github_btn.configure(text=self.translator.get("login_github", "  ⬡   Continuer avec GitHub"))
        except Exception as exc:
            logger.debug(f"Compact login layout update skipped: {exc}")

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
            top = self.winfo_toplevel()
            window_width = top.winfo_width()
            window_height = top.winfo_height()
            if window_width <= 1 or window_height <= 1:
                return

            if self._last_applied_window_size == (window_width, window_height):
                return

            # Éviter les appels trop fréquents
            if self._resize_after_id:
                self.after_cancel(self._resize_after_id)
            
            self._resize_after_id = self.after(100, self._apply_responsive_layout)
        except Exception:
            pass
    
    def _apply_responsive_layout(self):
        """Applique le layout responsive."""
        try:
            top = self.winfo_toplevel()
            window_width = top.winfo_width()
            window_height = top.winfo_height()
            
            if window_width > 0 and window_height > 0:
                self._last_window_size = (window_width, window_height)
                self._update_card_size(window_width, window_height)
                self._last_applied_window_size = (window_width, window_height)
        except Exception:
            pass

    def _fit_dialog_to_viewport(self, dialog, desired_width: int, desired_height: int,
                                min_width: int = 280, min_height: int = 140,
                                width_ratio: float = 0.92, height_ratio: float = 0.88):
        """Ajuste et centre un dialogue dans l'espace visible de la fenêtre principale."""
        try:
            fit_dialog_to_viewport(
                self,
                dialog,
                desired_width,
                desired_height,
                min_width=min_width,
                min_height=min_height,
                width_ratio=width_ratio,
                height_ratio=height_ratio,
            )
        except Exception:
            try:
                dialog.geometry(f"{desired_width}x{desired_height}")
            except Exception:
                pass

    def _on_language_change(self, value):
        """Change la langue et met à jour tous les textes"""
        if value == self.selected_language:
            return
        if self.dashboard_open:
            return

        self.selected_language = value
        self.translator = Translator(value)
        set_current_language(value)
        if self.parent_app and hasattr(self.parent_app, "update_ui_preferences"):
            try:
                self.parent_app.update_ui_preferences(language=value)
            except Exception:
                pass
        logger.info(f"Language changed to: {value}")
        self._translate_ui()

    def _translate_ui(self):
        """Met à jour le texte de tous les widgets traduits selon la langue active."""
        t = self.translator
        mapping = {
            'title_label':   t.get("user_login",      "CONNEXION UTILISATEUR"),
            'email_label':   t.get("email_id",         "📧  Email / Identifiant"),
            'password_label':t.get("password_label",   "🔒  Mot de passe"),
            'forgot_label':  t.get("forgot_password",  "Mot de passe oublié ?"),
            'or_label':      t.get("or_separator",     "ou"),
            'login_btn':     t.get("login_btn",        "CONNEXION"),
            'create_admin_btn': t.get("create_admin_btn", "CRÉER COMPTE"),
        }
        tw = getattr(self, 'translatable_widgets', {})
        for key, text in mapping.items():
            widget = tw.get(key)
            if widget:
                try:
                    widget.configure(text=text)
                except Exception:
                    pass
        # CTkCheckBox a son propre paramètre 'text'
        cb = tw.get('remember_me_cb')
        if cb:
            try:
                cb.configure(text=t.get("remember_me", "Se souvenir de moi"))
            except Exception:
                pass

        if hasattr(self, 'google_btn'):
            try:
                self.google_btn.configure(text=t.get("login_google", "  G   Continuer avec Google"))
            except Exception:
                pass
        if hasattr(self, 'github_btn'):
            try:
                self.github_btn.configure(text=t.get("login_github", "  ⬡   Continuer avec GitHub"))
            except Exception:
                pass

        if hasattr(self, 'hero_badge') and self.hero_badge:
            try:
                self.hero_badge.configure(text=t.translate_literal("UNIVERSITY OF REDEMPTION"))
            except Exception:
                pass

        if hasattr(self, 'hero_title') and self.hero_title:
            try:
                self.hero_title.configure(text=t.translate_literal("Bienvenue dans votre espace d'administration"))
            except Exception:
                pass

        if hasattr(self, 'hero_subtitle') and self.hero_subtitle:
            try:
                self.hero_subtitle.configure(text=t.translate_literal("Connectez-vous pour ouvrir l'application et accéder à votre tableau de bord."))
            except Exception:
                pass

        self._translate_widget_tree(self)

    def _translate_widget_tree(self, root_widget=None):
        """Traduit récursivement les textes de l'écran login et de ses dialogues."""
        root = root_widget or self

        def walk(widget):
            try:
                if isinstance(widget, tk.Toplevel):
                    title = widget.title()
                    if isinstance(title, str) and title.strip():
                        tt = self.translator.translate_literal(title)
                        if tt != title:
                            widget.title(tt)
            except Exception:
                pass

            try:
                txt = widget.cget("text")
                if isinstance(txt, str) and txt.strip():
                    ttxt = self.translator.translate_literal(txt)
                    if ttxt != txt:
                        widget.configure(text=ttxt)
            except Exception:
                pass

            try:
                ph = widget.cget("placeholder_text")
                if isinstance(ph, str) and ph.strip():
                    tph = self.translator.translate_literal(ph)
                    if tph != ph:
                        widget.configure(placeholder_text=tph)
            except Exception:
                pass

            try:
                vals = widget.cget("values")
                if isinstance(vals, (list, tuple)) and vals:
                    mapped = []
                    changed = False
                    for v in vals:
                        tv = self.translator.translate_literal(v) if isinstance(v, str) else v
                        mapped.append(tv)
                        changed = changed or (tv != v)
                    if changed:
                        widget.configure(values=mapped)
            except Exception:
                pass

            try:
                children = widget.winfo_children()
            except Exception:
                children = []
            for child in children:
                walk(child)

        walk(root)

    def _on_login(self):
        """Gère la connexion avec loading moderne intégré"""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.status_label.configure(text=self.translator.translate_literal("Veuillez entrer vos identifiants"))
            return

        # Désactiver le bouton login
        login_btn = getattr(self, 'login_btn', None)
        if login_btn:
            login_btn.configure(state="disabled")

        self.dashboard_open = True
        auth_t0 = perf_counter()

        def auth_worker():
            user = None
            error = None
            try:
                if self.auth_service is None:
                    svc_t0 = perf_counter()
                    self.auth_service = AuthenticationService()
                    logger.info("AuthenticationService lazy-init in %.1f ms", (perf_counter() - svc_t0) * 1000)
                user, error = self.auth_service.authenticate(username, password)
            except Exception as ex:
                error = f"{self.translator.translate_literal('Erreur')}: {str(ex)}"
                logger.error(f"Login error: {ex}", exc_info=True)
            finally:
                elapsed_ms = (perf_counter() - auth_t0) * 1000
                self.after(0, lambda: self._on_auth_completed(user, error, elapsed_ms, login_btn, username, password))

        threading.Thread(target=auth_worker, daemon=True, name="uor-auth-worker").start()

    def _on_auth_completed(self, user, error, elapsed_ms: float, login_btn, username: str, password: str):
        """Termine la phase d'authentification sur le thread UI."""
        if not self.winfo_exists():
            return

        logger.info("Authentication completed in %.1f ms", elapsed_ms)

        if error:
            self.status_label.configure(text=error)
            self.dashboard_open = False
            if login_btn:
                login_btn.configure(state="normal")
            return

        if not user:
            self.status_label.configure(text=self.translator.translate_literal("Connexion échouée"))
            self.dashboard_open = False
            if login_btn:
                login_btn.configure(state="normal")
            return

        logger.info(f"User {user.get('email')} logged in successfully")

        remember_me_checked = False
        try:
            remember_me_checked = bool(self.remember_me.get())
        except Exception:
            remember_me_checked = False

        if self.parent_app and hasattr(self.parent_app, "handle_login_preferences"):
            try:
                self.parent_app.handle_login_preferences(
                    identifier=username,
                    password=password,
                    remember_me=remember_me_checked,
                    language=self.selected_language,
                )
            except Exception:
                pass

        parent_frame = self.winfo_toplevel()
        progress = self.progress_tracker.create_overlay(parent_frame)
        progress.set_progress(20, self.translator.translate_literal("Authentification validée..."))

        # Exécuter la construction UI sur le thread principal (Tkinter thread-safe)
        self.after(30, lambda: self._build_dashboard_ui(parent_frame, progress, login_btn))

    def _build_dashboard_ui(self, parent_frame, progress, login_btn):
        """Demande à l'application d'ouvrir la page dashboard."""
        build_t0 = perf_counter()
        try:
            if self.parent_app:
                self.parent_app.open_dashboard_page(language=self.selected_language, progress=progress)
            else:
                progress.set_progress(45, self.translator.translate_literal("Initialisation de l'interface..."))

                # Lazy import pour réduire le temps de démarrage avant affichage login
                from ui.screens.admin.admin_dashboard import AdminDashboard

                dashboard = AdminDashboard(
                    parent=parent_frame, language=self.selected_language, theme=self.theme
                )

                progress.set_progress(80, self.translator.translate_literal("Chargement des données..."))
                parent_frame.update_idletasks()

                self.pack_forget()
                progress.set_progress(95, self.translator.translate_literal("Finalisation..."))
                progress.complete()
            logger.info("Dashboard initialized in %.1f ms", (perf_counter() - build_t0) * 1000)
        except Exception as e:
            logger.error(f"Dashboard init error: {e}", exc_info=True)
            try:
                progress.place_forget()
            except Exception:
                pass
            if login_btn:
                try:
                    if login_btn.winfo_exists():
                        login_btn.configure(state="normal")
                except Exception:
                    pass
            self.status_label.configure(text=f"{self.translator.translate_literal('Erreur')}: {str(e)}")
        finally:
            self.dashboard_open = False

    # =========================================================
    # MOT DE PASSE OUBLIÉ
    # =========================================================

    # =========================================================
    # ICÔNES LOGOS (générées via PIL, sans fichiers externes)
    # =========================================================

    def _make_google_icon(self, size: int = 28) -> "ctk.CTkImage":
        """Crée l'icône Google depuis assets/google.webp (fallback dessiné si indisponible)."""
        try:
            logo_path = os.path.join("assets", "google.webp")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                alpha = logo.split()[3]
                bbox = alpha.getbbox()
                if bbox:
                    logo = logo.crop(bbox)
                max_dim = max(1, int(size * 0.8))
                ratio = min(max_dim / logo.width, max_dim / logo.height)
                new_w = max(1, int(logo.width * ratio))
                new_h = max(1, int(logo.height * ratio))
                logo = logo.resize((new_w, new_h), Image.Resampling.LANCZOS)

                canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                x = (size - new_w) // 2
                y = (size - new_h) // 2
                canvas.paste(logo, (x, y), logo)
                icon = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(size, size))
                self.social_icons["google"] = icon
                return icon
        except Exception as e:
            logger.warning(f"Failed to load Google logo from assets: {e}")

        # Fallback dessiné
        from PIL import ImageDraw
        scale = 4
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, s - 3, s - 3], fill=(255, 255, 255, 255))
        r = s // 2 - 6
        cx, cy = s // 2, s // 2
        bbox = [cx - r, cy - r, cx + r, cy + r]
        w = max(s // 8, 4)
        d.arc(bbox, start=315, end=45, fill=(66, 133, 244), width=w)
        d.arc(bbox, start=45, end=135, fill=(234, 67, 53), width=w)
        d.arc(bbox, start=135, end=225, fill=(251, 188, 4), width=w)
        d.arc(bbox, start=225, end=315, fill=(52, 168, 83), width=w)
        d.rectangle([cx, cy - w // 2, cx + r - 2, cy + w // 2], fill=(66, 133, 244))
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        icon = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        self.social_icons["google"] = icon
        return icon

    def _make_github_icon(self, size: int = 28) -> "ctk.CTkImage":
        """Crée l'icône GitHub depuis assets/GitHub-Logo.png (fallback dessiné si indisponible)."""
        try:
            logo_path = os.path.join("assets", "GitHub-Logo.png")
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                alpha = logo.split()[3]
                bbox = alpha.getbbox()
                if bbox:
                    logo = logo.crop(bbox)
                max_dim = max(1, int(size * 0.8))
                ratio = min(max_dim / logo.width, max_dim / logo.height)
                new_w = max(1, int(logo.width * ratio))
                new_h = max(1, int(logo.height * ratio))
                logo = logo.resize((new_w, new_h), Image.Resampling.LANCZOS)

                canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
                x = (size - new_w) // 2
                y = (size - new_h) // 2
                canvas.paste(logo, (x, y), logo)
                icon = ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(size, size))
                self.social_icons["github"] = icon
                return icon
        except Exception as e:
            logger.warning(f"Failed to load GitHub logo from assets: {e}")

        # Fallback dessiné
        from PIL import ImageDraw
        scale = 4
        s = size * scale
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        bg = (13, 17, 23, 255)
        fg = (255, 255, 255, 220)
        d.ellipse([0, 0, s - 1, s - 1], fill=bg)
        hr = s // 4
        hy = s // 2 - s // 14
        d.ellipse([s // 2 - hr, hy - hr, s // 2 + hr, hy + hr], fill=fg)
        er = s // 9
        d.ellipse([s // 2 - hr - er + 4, hy - hr - er + 6,
                   s // 2 - hr + er + 4, hy - hr + er + 6], fill=fg)
        d.ellipse([s // 2 + hr - er - 4, hy - hr - er + 6,
                   s // 2 + hr + er - 4, hy - hr + er + 6], fill=fg)
        bw, bh = s // 4, s // 7
        bcy = hy + hr + bh - 4
        d.ellipse([s // 2 - bw, bcy - bh, s // 2 + bw, bcy + bh], fill=fg)
        er2 = max(s // 18, 2)
        ex = hr // 3
        d.ellipse([s // 2 - ex - er2, hy - er2, s // 2 - ex + er2, hy + er2], fill=bg)
        d.ellipse([s // 2 + ex - er2, hy - er2, s // 2 + ex + er2, hy + er2], fill=bg)
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        icon = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        self.social_icons["github"] = icon
        return icon

    # =========================================================
    # MOT DE PASSE OUBLIÉ
    # =========================================================

    def _show_forgot_password_dialog(self):
        """Ouvre le dialogue de réinitialisation du mot de passe."""
        t = self.translator

        dialog = ctk.CTkToplevel(self)
        dialog.title(t.get("fp_title", "Réinitialiser le mot de passe"))
        dialog.configure(fg_color="#3E4F5A")
        dialog.resizable(False, False)
        dialog.grab_set()

        dw, dh = 370, 430
        self._fit_dialog_to_viewport(dialog, dw, dh, min_width=320, min_height=360)

        frame = ctk.CTkFrame(dialog, fg_color="#3E4F5A")
        frame.pack(fill="both", expand=True, padx=28, pady=22)

        # Titre
        ctk.CTkLabel(
            frame,
            text=f"\U0001f511  {t.get('fp_title', 'Réinitialiser le mot de passe')}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#B8C5CB",
        ).pack(anchor="w", pady=(0, 18))

        def _field(label_key, label_default, ph_key, ph_default, show=""):
            ctk.CTkLabel(
                frame,
                text=t.get(label_key, label_default),
                font=ctk.CTkFont(size=11),
                text_color="#8A9CA5",
                anchor="w",
            ).pack(anchor="w", pady=(0, 4))
            entry = ctk.CTkEntry(
                frame,
                placeholder_text=t.get(ph_key, ph_default),
                height=36,
                show=show,
                corner_radius=5,
                border_width=1,
                fg_color="#2A3940",
                border_color="#5A6B75",
                text_color="#FFFFFF",
                font=ctk.CTkFont(size=11),
            )
            entry.pack(fill="x", pady=(0, 14))
            return entry

        entry_id     = _field("fp_identifier_label", "Email ou matricule",
                              "fp_identifier_ph",    "email@example.com ou MAT2024001")
        entry_new_pw = _field("fp_new_password",     "Nouveau mot de passe",
                              "fp_new_password",     "••••••••", show="•")
        entry_cfm_pw = _field("fp_confirm_password", "Confirmer le mot de passe",
                              "fp_confirm_password", "••••••••", show="•")

        status_lbl = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=10), text_color="#FFB4B4", wraplength=300,
        )
        status_lbl.pack(fill="x", pady=(0, 10))

        btn_row = ctk.CTkFrame(frame, fg_color="#3E4F5A")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text=t.get("fp_cancel_btn", "Annuler"),
            height=36, width=110,
            font=ctk.CTkFont(size=11),
            fg_color="#2A3940", hover_color="#374F5A",
            text_color="#8A9CA5", corner_radius=5,
            command=dialog.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text=t.get("fp_reset_btn", "Réinitialiser"),
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1A1A1A", hover_color="#000000",
            text_color="#FFFFFF", corner_radius=5,
            command=lambda: self._do_reset_password(
                entry_id.get(), entry_new_pw.get(), entry_cfm_pw.get(),
                status_lbl, dialog,
            ),
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

        entry_id.focus()

    def _do_reset_password(self, identifier: str, new_pw: str, confirm_pw: str,
                           status_lbl, dialog):
        """Effectue la réinitialisation du mot de passe (thread-safe)."""
        t = self.translator
        identifier = identifier.strip()
        new_pw     = new_pw.strip()
        confirm_pw = confirm_pw.strip()

        if not identifier or not new_pw or not confirm_pw:
            status_lbl.configure(
                text=t.get("fp_missing_fields", "Veuillez remplir tous les champs"),
                text_color="#FFB4B4",
            )
            return
        if len(new_pw) < 4:
            status_lbl.configure(
                text=t.get("fp_min_length", "Le mot de passe doit avoir au moins 4 caractères"),
                text_color="#FFB4B4",
            )
            return
        if new_pw != confirm_pw:
            status_lbl.configure(
                text=t.get("fp_no_match", "Les mots de passe ne correspondent pas"),
                text_color="#FFB4B4",
            )
            return

        status_lbl.configure(
            text=t.get("loading", "Traitement en cours…"),
            text_color="#8A9CA5",
        )
        dialog.update_idletasks()

        def worker():
            try:
                if self.auth_service is None:
                    self.auth_service = AuthenticationService()
                ok, msg = self.auth_service.reset_password_by_email(identifier, new_pw)
            except Exception as exc:
                ok, msg = False, str(exc)
            dialog.after(0, lambda: _finish(ok, msg))

        def _finish(ok: bool, msg: str):
            if not dialog.winfo_exists():
                return
            if ok:
                status_lbl.configure(
                    text=t.get("fp_success", "Mot de passe réinitialisé avec succès ✓"),
                    text_color="#6EE7B7",
                )
                dialog.after(1400, lambda: dialog.destroy() if dialog.winfo_exists() else None)
            else:
                status_lbl.configure(
                    text=msg or t.get("fp_not_found", "Aucun compte trouvé"),
                    text_color="#FFB4B4",
                )

        threading.Thread(target=worker, daemon=True, name="uor-reset-pw").start()

    def _show_create_admin_dialog(self):
        """Ouvre le dialogue de création d'un compte administrateur."""
        t = self.translator

        dialog = ctk.CTkToplevel(self)
        dialog.title(t.get("create_admin_btn", "Créer un compte admin"))
        dialog.configure(fg_color="#3E4F5A")
        dialog.resizable(False, False)
        dialog.grab_set()
        dialog.transient(self.winfo_toplevel())
        dialog.lift()

        dw, dh = 390, 470
        self._fit_dialog_to_viewport(dialog, dw, dh, min_width=340, min_height=400)
        dialog.update_idletasks()
        try:
            dialog.focus_force()
        except Exception:
            pass

        frame = ctk.CTkFrame(dialog, fg_color="#3E4F5A")
        frame.pack(fill="both", expand=True, padx=28, pady=22)

        ctk.CTkLabel(
            frame,
            text=t.get("create_admin_title", "Créer un compte administrateur"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#B8C5CB",
        ).pack(anchor="w", pady=(0, 16))

        def _field(label_text: str, placeholder: str, show: str = ""):
            ctk.CTkLabel(
                frame,
                text=label_text,
                font=ctk.CTkFont(size=11),
                text_color="#8A9CA5",
                anchor="w",
            ).pack(anchor="w", pady=(0, 4))
            e = ctk.CTkEntry(
                frame,
                placeholder_text=placeholder,
                height=36,
                show=show,
                corner_radius=5,
                border_width=1,
                fg_color="#2A3940",
                border_color="#5A6B75",
                text_color="#FFFFFF",
                font=ctk.CTkFont(size=11),
            )
            e.pack(fill="x", pady=(0, 12))
            return e

        entry_username = _field(
            t.get("username", "Nom d'utilisateur"),
            t.get("create_admin_username_ph", "admin.username"),
        )
        entry_email = _field(
            t.get("email", "Email"),
            t.get("create_admin_email_ph", "admin@example.com"),
        )
        entry_password = _field(
            t.get("password_label", "Mot de passe"),
            "••••••••",
            show="•",
        )
        entry_confirm = _field(
            t.get("fp_confirm_password", "Confirmer le mot de passe"),
            "••••••••",
            show="•",
        )

        status_lbl = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(size=10), text_color="#FFB4B4", wraplength=320,
        )
        status_lbl.pack(fill="x", pady=(0, 10))

        btn_row = ctk.CTkFrame(frame, fg_color="#3E4F5A")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row,
            text=t.get("cancel", "Annuler"),
            height=36, width=110,
            font=ctk.CTkFont(size=11),
            fg_color="#2A3940", hover_color="#374F5A",
            text_color="#8A9CA5", corner_radius=5,
            command=dialog.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text=t.get("create_admin_btn", "CRÉER COMPTE"),
            height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1A1A1A", hover_color="#000000",
            text_color="#FFFFFF", corner_radius=5,
            command=lambda: self._do_create_admin(
                entry_username.get(), entry_email.get(), entry_password.get(), entry_confirm.get(),
                status_lbl, dialog
            ),
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

        entry_username.focus()

    def _do_create_admin(self, username: str, email: str, password: str, confirm_password: str,
                         status_lbl, dialog):
        """Crée un compte administrateur en base de données."""
        t = self.translator
        username = (username or "").strip()
        email = (email or "").strip()
        password = (password or "").strip()
        confirm_password = (confirm_password or "").strip()

        if not username or not email or not password or not confirm_password:
            status_lbl.configure(text=t.get("fp_missing_fields", "Veuillez remplir tous les champs"), text_color="#FFB4B4")
            return
        if password != confirm_password:
            status_lbl.configure(text=t.get("fp_no_match", "Les mots de passe ne correspondent pas"), text_color="#FFB4B4")
            return
        if len(password) < 6:
            status_lbl.configure(text=t.get("create_admin_min_length", "Le mot de passe doit avoir au moins 6 caractères"), text_color="#FFB4B4")
            return

        status_lbl.configure(text=t.get("loading", "Traitement en cours…"), text_color="#8A9CA5")
        dialog.update_idletasks()

        def worker():
            try:
                if self.auth_service is None:
                    self.auth_service = AuthenticationService()
                ok, msg = self.auth_service.register_admin_account(username, email, password)
            except Exception as exc:
                ok, msg = False, str(exc)
            dialog.after(0, lambda: _finish(ok, msg))

        def _finish(ok: bool, msg: str):
            if not dialog.winfo_exists():
                return
            if ok:
                status_lbl.configure(
                    text=t.get("create_admin_success", "Compte administrateur créé avec succès ✓"),
                    text_color="#6EE7B7",
                )
                self.entry_username.delete(0, "end")
                self.entry_username.insert(0, username)
                self.entry_password.delete(0, "end")
                dialog.after(1200, lambda: dialog.destroy() if dialog.winfo_exists() else None)
            else:
                status_lbl.configure(text=msg or t.get("error", "Erreur"), text_color="#FFB4B4")

        threading.Thread(target=worker, daemon=True, name="uor-create-admin").start()

    # =========================================================
    # OAUTH  (Google / GitHub)
    # =========================================================

    def _on_google_login(self):
        """Lance l'authentification OAuth Google via le navigateur."""
        import os
        client_id     = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            self._show_oauth_not_configured("Google", "GOOGLE_OAUTH_CLIENT_ID\nGOOGLE_OAUTH_CLIENT_SECRET")
            return
        self._launch_oauth_flow(
            name="Google",
            auth_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            user_info_url="https://www.googleapis.com/oauth2/v3/userinfo",
            client_id=client_id,
            client_secret=client_secret,
            scope="openid email profile",
        )

    def _on_github_login(self):
        """Lance l'authentification OAuth GitHub via le navigateur."""
        import os
        client_id     = os.getenv("GITHUB_OAUTH_CLIENT_ID", "")
        client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "")
        if not client_id or not client_secret:
            self._show_oauth_not_configured("GitHub", "GITHUB_OAUTH_CLIENT_ID\nGITHUB_OAUTH_CLIENT_SECRET")
            return
        self._launch_oauth_flow(
            name="GitHub",
            auth_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            user_info_url="https://api.github.com/user",
            client_id=client_id,
            client_secret=client_secret,
            scope="user:email",
        )

    def _show_oauth_not_configured(self, provider: str, env_keys: str):
        """Informe l'utilisateur que l'OAuth n'est pas encore configuré."""
        t = self.translator
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"{provider} OAuth")
        dialog.configure(fg_color="#3E4F5A")
        dialog.resizable(False, False)
        dialog.grab_set()

        dw, dh = 370, 260
        self._fit_dialog_to_viewport(dialog, dw, dh, min_width=320, min_height=220)

        frame = ctk.CTkFrame(dialog, fg_color="#3E4F5A")
        frame.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            frame,
            text=f"\u23f3  {provider}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#B8C5CB",
        ).pack(anchor="w", pady=(0, 12))

        if self.selected_language == "FR":
            body = (
                f"La connexion avec {provider} sera bientôt disponible.\n\n"
                f"Cette fonctionnalité est en cours d'activation."
            )
        else:
            body = (
                f"{provider} login is coming soon.\n\n"
                f"This feature is currently being activated."
            )

        ctk.CTkLabel(
            frame, text=body,
            font=ctk.CTkFont(size=11), text_color="#8A9CA5",
            wraplength=310, justify="left",
        ).pack(anchor="w", pady=(0, 18))

        ctk.CTkButton(
            frame,
            text=t.get("close", "Fermer"),
            height=34,
            fg_color="#1A1A1A", hover_color="#000000",
            text_color="#FFFFFF", corner_radius=5,
            command=dialog.destroy,
        ).pack(fill="x")

    def _launch_oauth_flow(self, name: str, auth_url: str, token_url: str,
                            user_info_url: str, client_id: str, client_secret: str,
                            scope: str):
        """Lance le flux OAuth PKCE-like via navigateur + serveur HTTP local temporaire."""
        import socket
        import http.server
        import urllib.parse
        import secrets as _sec
        import requests as _req

        # Trouver un port libre
        with socket.socket() as _s:
            _s.bind(("127.0.0.1", 0))
            port = _s.getsockname()[1]

        redirect_uri = f"http://127.0.0.1:{port}/callback"
        state = _sec.token_urlsafe(16)

        params = {
            "client_id":     client_id,
            "redirect_uri":  redirect_uri,
            "scope":         scope,
            "state":         state,
            "response_type": "code",
        }
        if name == "Google":
            params["access_type"] = "online"

        full_auth_url = auth_url + "?" + urllib.parse.urlencode(params)

        # ---- Dialogue d'attente ----
        wait_dlg = ctk.CTkToplevel(self)
        wait_dlg.title(f"{name} — Connexion")
        wait_dlg.configure(fg_color="#3E4F5A")
        wait_dlg.resizable(False, False)
        wait_dlg.grab_set()

        dw, dh = 340, 170
        self._fit_dialog_to_viewport(wait_dlg, dw, dh, min_width=300, min_height=160)

        wframe = ctk.CTkFrame(wait_dlg, fg_color="#3E4F5A")
        wframe.pack(fill="both", expand=True, padx=20, pady=18)

        status_var = ctk.StringVar(
            value=f"\U0001f310  Connexion {name} en cours…" if self.selected_language == "FR"
            else f"\U0001f310  Connecting to {name}…"
        )
        ctk.CTkLabel(
            wframe, textvariable=status_var,
            font=ctk.CTkFont(size=12), text_color="#B8C5CB", wraplength=290,
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            wframe,
            text="Autorisez dans le navigateur…" if self.selected_language == "FR"
                 else "Authorize in the browser…",
            font=ctk.CTkFont(size=10), text_color="#8A9CA5",
        ).pack()

        result = {"code": None, "cancelled": False}

        def cancel():
            result["cancelled"] = True
            try:
                wait_dlg.destroy()
            except Exception:
                pass

        ctk.CTkButton(
            wframe,
            text=self.translator.get("cancel", "Annuler"),
            height=28, font=ctk.CTkFont(size=10),
            fg_color="#2A3940", hover_color="#374F5A",
            text_color="#8A9CA5", corner_radius=5,
            command=cancel,
        ).pack(pady=(10, 0))

        webbrowser.open(full_auth_url)

        def _oauth_server():
            from http.server import BaseHTTPRequestHandler, HTTPServer

            class _H(BaseHTTPRequestHandler):
                def log_message(self, fmt, *args):
                    pass

                def do_GET(self_h):
                    parsed = urllib.parse.urlparse(self_h.path)
                    if parsed.path == "/callback":
                        qs = urllib.parse.parse_qs(parsed.query)
                        code_v  = qs.get("code",  [None])[0]
                        state_v = qs.get("state", [None])[0]
                        if state_v == state and code_v:
                            result["code"] = code_v
                            html_ok = b"<html><body><script>window.close();</script><p>Vous pouvez fermer cet onglet.</p></body></html>"
                        else:
                            html_ok = b"<html><body><p>Erreur OAuth.</p></body></html>"
                        self_h.send_response(200)
                        self_h.send_header("Content-Type", "text/html; charset=utf-8")
                        self_h.end_headers()
                        self_h.wfile.write(html_ok)
                        self_h.server._stop = True

            srv = HTTPServer(("127.0.0.1", port), _H)
            srv.timeout = 1
            srv._stop = False
            elapsed = 0
            while not srv._stop and not result["cancelled"] and elapsed < 120:
                srv.handle_request()
                elapsed += 1
            srv.server_close()

            if result["cancelled"] or not result["code"]:
                return

            try:
                token_resp = _req.post(
                    token_url,
                    data={
                        "client_id":     client_id,
                        "client_secret": client_secret,
                        "code":          result["code"],
                        "redirect_uri":  redirect_uri,
                        "grant_type":    "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                    timeout=10,
                )
                token_json   = token_resp.json()
                access_token = token_json.get("access_token", "")
                if not access_token:
                    self.after(0, lambda: _err("Token non reçu"))
                    return

                user_resp = _req.get(
                    user_info_url,
                    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                    timeout=10,
                )
                user_json = user_resp.json()
                email = user_json.get("email", "")

                if not email and name == "GitHub":
                    em_resp = _req.get(
                        "https://api.github.com/user/emails",
                        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                        timeout=10,
                    )
                    for e_obj in (em_resp.json() or []):
                        if e_obj.get("primary"):
                            email = e_obj.get("email", "")
                            break

                if email:
                    self.after(0, lambda e=email: _login_with_email(e))
                else:
                    self.after(0, lambda: _err("Email introuvable"))

            except Exception as ex:
                self.after(0, lambda: _err(str(ex)))

        def _err(msg: str):
            if wait_dlg.winfo_exists():
                status_var.set(f"\u274c {self.translator.translate_literal('Erreur')}: {msg}")

        def _login_with_email(email: str):
            try:
                if self.auth_service is None:
                    self.auth_service = AuthenticationService()
                user = self.auth_service.authenticate_by_email_no_pw(email)
                if user:
                    try:
                        wait_dlg.destroy()
                    except Exception:
                        pass
                    logger.info(f"OAuth login success via {name}: {email}")
                    parent_frame = self.winfo_toplevel()
                    progress = self.progress_tracker.create_overlay(parent_frame)
                    progress.set_progress(20, self.translator.translate_literal("OAuth validé…"))
                    self.after(30, lambda: self._build_dashboard_ui(parent_frame, progress, self.login_btn))
                else:
                    if wait_dlg.winfo_exists():
                        status_var.set(
                            f"\u274c Aucun compte associé à : {email}"
                            if self.selected_language == "FR"
                            else f"\u274c No account linked to: {email}"
                        )
            except Exception as ex:
                if wait_dlg.winfo_exists():
                    status_var.set(f"\u274c {self.translator.translate_literal('Erreur')}: {str(ex)}")

        threading.Thread(target=_oauth_server, daemon=True, name=f"uor-oauth-{name.lower()}").start()
