"""Dashboard administrateur moderne - Style SB Admin Pro"""
import customtkinter as ctk
import logging
import os
import shutil
import io
import hashlib
import threading
import re
from datetime import datetime
from decimal import Decimal
from tkinter import filedialog, messagebox, StringVar
from PIL import Image
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from ui.components.modern_widgets import LoadingIndicator
from app.services.dashboard_service import DashboardService
from app.services.student.student_service import StudentService
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.face_recognition_service import FaceRecognitionService
from app.services.finance.finance_service import FinanceService
from app.services.finance.academic_year_service import AcademicYearService
from app.services.integration.notification_service import NotificationService
from app.services.integration.esp32_status_service import ESP32StatusService
from core.models.student import Student

logger = logging.getLogger(__name__)


class AdminDashboard(ctk.CTkFrame):
    """Tableau de bord administrateur moderne avec design professionnel"""
    
    def __init__(self, parent, language: str = "FR", theme: ThemeManager = None):
        super().__init__(parent)
        
        self.parent_window = parent
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.ui_mode, self.ui_scale = self._get_screen_profile()
        ctk.set_widget_scaling(self.ui_scale)

        self.selected_language = language
        self.translator = Translator(language)
        self.theme = theme if theme else ThemeManager("light")
        self.current_view = "dashboard"
        self.dashboard_service = DashboardService()
        self.student_service = StudentService()
        self.auth_service = AuthenticationService()
        self.face_service = FaceRecognitionService()
        self.finance_service = FinanceService()
        self.academic_year_service = AcademicYearService()
        self.notification_service = NotificationService()
        self.esp32_service = ESP32StatusService()
        self._photo_cache = {}
        self._esp32_status_label = None
        self._responsive_labels = []
        self.sidebar_mode = "full"
        self._loading_overlay = None
        self._loading_indicator = None
        self._loading_visible = False
        
        # Adaptive sidebar widths based on screen size
        if self.screen_width < 900:
            self.sidebar_width_full = 200  # Small screen: narrower sidebar
            self.sidebar_width_compact = 60
            self.sidebar_collapse_breakpoint = 1000
        elif self.screen_width < 1200:
            self.sidebar_width_full = 240
            self.sidebar_width_compact = 75
            self.sidebar_collapse_breakpoint = 1200
        elif self.screen_width < 1400:
            self.sidebar_width_full = 260
            self.sidebar_width_compact = 85
            self.sidebar_collapse_breakpoint = 1400
        else:
            self.sidebar_width_full = 280
            self.sidebar_width_compact = 90
            self.sidebar_collapse_breakpoint = 1100
        
        self.table_mode = "large"
        self.table_compact_breakpoint = 1200
        self.sidebar_hover_expanded = False
        self._sidebar_anim_job = None
        self._sidebar_animating = False
        self._sidebar_update_debounce_job = None
        self._scrolling_active = False
        self.debug_students_table = False
        
        self.colors = self._get_color_palette()
        ctk.set_appearance_mode("Dark" if self.theme.current_theme == "dark" else "Light")
        
        self.pack(fill="both", expand=True)
        self._create_ui()
    def _register_wrap(self, label, ratio: float = 0.35, min_width: int = 280, max_width: int = 600):
        """Enregistre un label pour ajuster automatiquement son wraplength"""
        self._responsive_labels.append((label, ratio, min_width, max_width))

    def _on_resize(self, _event=None):
        if not self._responsive_labels:
            self._update_sidebar_layout()
            self._update_table_mode()
            return
        width = self.winfo_width() or self.screen_width
        for label, ratio, min_w, max_w in self._responsive_labels:
            try:
                wrap = int(max(min_w, min(max_w, width * ratio)))
                label.configure(wraplength=wrap)
            except Exception:
                continue
        self._update_sidebar_layout()
        self._update_table_mode()

    def _get_screen_profile(self):
        """Détermine le mode d'affichage et le scaling selon la taille d'écran (RESPONSIVE)"""
        if self.screen_width < 900:
            # Très petit écran: Mobile-like
            ctk.set_appearance_mode("Light")  # Meilleur contrast
            return "tiny", 0.75  # Smaller UI scale
        if self.screen_width < 1200:
            # Petit/Medium: Compact
            return "small", 0.85
        if self.screen_width < 1400:
            # Medium: Tablet
            return "tablet", 0.95
        # Grand écran: Desktop
        return "desktop", 1.0

    def _scaled(self, value: int) -> int:
        return max(10, int(value * self.ui_scale))

    def _font(self, size: int, weight: str = "normal"):
        return ctk.CTkFont(size=self._scaled(size), weight=weight)

    def _t(self, key: str, default: str = "") -> str:
        """Raccourci traduction avec fallback"""
        return self.translator.get(key, default)

    def _get_color_palette(self):
        """Retourne la palette selon le thème"""
        if self.theme.current_theme == "dark":
            return {
                "sidebar_bg": "#0f172a",
                "main_bg": "#0b1220",
                "card_bg": "#111827",
                "primary": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "info": "#06b6d4",
                "text_dark": "#e5e7eb",
                "text_light": "#9ca3af",
                "text_white": "#ffffff",
                "border": "#1f2937",
                "hover": "#111827"
            }
        return {
            "sidebar_bg": "#1e293b",
            "main_bg": "#f8fafc",
            "card_bg": "#ffffff",
            "primary": "#3b82f6",
            "success": "#10b981",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#06b6d4",
            "text_dark": "#1e293b",
            "text_light": "#64748b",
            "text_white": "#ffffff",
            "border": "#e2e8f0",
            "hover": "#f1f5f9"
        }

    def _toggle_theme(self):
        """Bascule le thème et reconstruit l'UI"""
        new_theme = "dark" if self.theme.current_theme == "light" else "light"
        self.theme.set_theme(new_theme)
        self.colors = self._get_color_palette()
        ctk.set_appearance_mode("Dark" if new_theme == "dark" else "Light")
        self._recreate_ui()

    def _recreate_ui(self):
        """Recrée l'interface en conservant la vue active"""
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()

    def _render_current_view(self):
        """Réaffiche la vue en cours"""
        self._set_main_scrollbar_visible(True)
        view_map = {
            "dashboard": self._show_dashboard,
            "students": self._show_students,
            "finance": self._show_finance,
            "access_logs": self._show_access_logs,
            "reports": self._show_reports,
            "academic_years": self._show_academic_years
        }
        view_map.get(self.current_view, self._show_dashboard)()

    def _ensure_loading_overlay(self):
        """Prépare un overlay de chargement pour masquer les rechargements visibles."""
        if self._loading_overlay or not hasattr(self, "main_content"):
            return

        overlay = ctk.CTkFrame(self.main_content, fg_color=self.colors["main_bg"])
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        card = ctk.CTkFrame(overlay, fg_color=self.colors["card_bg"], corner_radius=12)
        card.place(relx=0.5, rely=0.4, anchor="center")

        indicator = LoadingIndicator(card, text="Chargement...", color=self.colors.get("primary", "#3b82f6"))
        indicator.pack(padx=24, pady=24)
        indicator.start()

        self._loading_overlay = overlay
        self._loading_indicator = indicator
        overlay.place_forget()

    def _show_loading_overlay(self, text: str = "Chargement..."):
        if self._loading_visible:
            return
        self._ensure_loading_overlay()
        if not self._loading_overlay:
            return
        self._loading_visible = True
        try:
            if self._loading_indicator:
                self._loading_indicator.start(text)
        except Exception:
            pass
        try:
            self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._loading_overlay.lift()
        except Exception:
            pass

    def _hide_loading_overlay(self):
        if not self._loading_overlay:
            return
        self._loading_visible = False
        try:
            if self._loading_indicator:
                self._loading_indicator.stop()
        except Exception:
            pass
        try:
            self._loading_overlay.place_forget()
        except Exception:
            pass

    def _run_with_loading(self, action, text: str = "Chargement..."):
        """Exécute une action en affichant un loader pour éviter l'effet de recharge."""
        self._show_loading_overlay(text)
        try:
            try:
                self.update_idletasks()
            except Exception:
                pass
            action()
        finally:
            self._hide_loading_overlay()
    
    def _create_ui(self):
        """Crée l'interface moderne du dashboard"""
        self.configure(fg_color=self.colors["main_bg"])
        
        # Container principal
        container = ctk.CTkFrame(self, fg_color=self.colors["main_bg"])
        container.pack(fill="both", expand=True)
        
        # === SIDEBAR MODERNE ===
        sidebar = ctk.CTkFrame(container, fg_color=self.colors["sidebar_bg"], width=self.sidebar_width_full, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.sidebar = sidebar
        
        # Logo et titre
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", pady=(20, 10))
        logo_frame.pack_propagate(False)
        
        self.logo_title_label = ctk.CTkLabel(
            logo_frame,
            text="U.O.R",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.colors["text_white"]
        )
        self.logo_title_label.pack()
        
        self.logo_subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="ADMIN DASHBOARD",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_light"]
        )
        self.logo_subtitle_label.pack()
        
        # Séparateur
        ctk.CTkFrame(sidebar, height=1, fg_color="#334155").pack(fill="x", padx=20, pady=15)
        
        # Navigation
        nav_items = [
            ("📊", "dashboard", self._t("dashboard", "Dashboard"), lambda: self._run_with_loading(self._show_dashboard)),
            ("👥", "students", self._t("students", "Étudiants"), lambda: self._run_with_loading(self._show_students)),
            ("💰", "finance", self._t("finance", "Finances"), lambda: self._run_with_loading(self._show_finance)),
            ("📚", "academic_years", self._t("academic_years", "Années Acad."), lambda: self._run_with_loading(self._show_academic_years)),
            ("📋", "access_logs", self._t("access_logs", "Logs d'Accès"), lambda: self._run_with_loading(self._show_access_logs)),
            ("📈", "reports", self._t("reports", "Rapports"), lambda: self._run_with_loading(self._show_reports)),
        ]
        
        self.nav_buttons = []
        for icon, key, label, callback in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon}  {label}",
                fg_color="transparent",
                hover_color="#334155",
                text_color=self.colors["text_white"],
                anchor="w",
                command=callback,
                height=45,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold")
            )
            btn.pack(fill="x", padx=15, pady=3)
            self.nav_buttons.append({"button": btn, "key": key, "icon": icon, "label": label})
        
        # Spacer
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)
        
        # Logout
        logout_height = 46
        logout_font_size = 13
        if self.screen_width >= 1400:
            logout_height = 58
            logout_font_size = 15
        elif self.screen_width < 900:
            logout_height = 42
            logout_font_size = 12

        self.logout_btn = ctk.CTkButton(
            sidebar,
            text="🚪  Déconnexion",
            fg_color=self.colors["danger"],
            hover_color="#dc2626",
            text_color=self.colors["text_white"],
            command=self._on_logout,
            height=logout_height,
            corner_radius=8,
            anchor="w",
            border_width=1,
            border_color="#b91c1c",
            font=ctk.CTkFont(size=logout_font_size, weight="bold")
        )
        self.logout_btn.pack(fill="x", padx=15, pady=(12, 22))
        
        # === MAIN CONTENT ===
        self.main_content = ctk.CTkFrame(container, fg_color=self.colors["main_bg"])
        self.main_content.pack(side="right", fill="both", expand=True)
        self.main_content.bind("<Configure>", self._on_resize)
        try:
            self.parent_window.bind("<Configure>", self._on_resize)
        except Exception:
            pass
        
        # Top bar avec titre et langue
        topbar = ctk.CTkFrame(self.main_content, fg_color="transparent", height=42)
        topbar.pack(fill="x", padx=25, pady=(6, 0))
        topbar.pack_propagate(False)
        
        # Titre à gauche
        title_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text=self._t("dashboard", "Dashboard"),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors["text_dark"]
        )
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(
            title_frame,
            text=f"Vue d'ensemble • {datetime.now().strftime('%d %B %Y')}",
            font=ctk.CTkFont(size=13),
            text_color=self.colors["text_light"]
        )
        self.subtitle_label.pack(anchor="w")
        
        # Sélecteur de langue et thème à droite
        lang_frame = ctk.CTkFrame(topbar, fg_color=self.colors["card_bg"], corner_radius=8)
        lang_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(
            lang_frame,
            text="🌐",
            font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(15, 5), pady=10)
        
        self.lang_switch = ctk.CTkSegmentedButton(
            lang_frame,
            values=["FR", "EN"],
            command=self._on_language_change,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors["border"],
            selected_color=self.colors["primary"],
            selected_hover_color="#2563eb",
            unselected_color=self.colors["card_bg"],
            unselected_hover_color=self.colors["hover"]
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.pack(side="left", padx=(5, 15), pady=10)

        theme_btn = ctk.CTkButton(
            lang_frame,
            text="🌙" if self.theme.current_theme == "light" else "☀️",
            width=40,
            height=32,
            fg_color=self.colors["border"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text_dark"],
            command=self._toggle_theme
        )
        theme_btn.pack(side="left", padx=(0, 15), pady=10)
        
        # Content container + scrollable frame (for slide animation)
        self.content_container = ctk.CTkFrame(self.main_content, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=25, pady=6)

        self.content_frame = ctk.CTkScrollableFrame(
            self.content_container,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["text_light"]
        )
        self.content_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._ensure_loading_overlay()
        
        # Afficher la vue active
        self._render_current_view()
        self._update_sidebar_layout()
    
    def _create_card(self, parent, width=None, height=None):
        """Crée une carte avec ombre moderne"""
        card = ctk.CTkFrame(
            parent,
            fg_color=self.colors["card_bg"],
            corner_radius=12
        )
        if width:
            card.configure(width=width)
        if height:
            card.configure(height=height)
            card.pack_propagate(False)
        return card

    def _shade_color(self, hex_color: str, factor: float = 0.9) -> str:
        """Assombrit légèrement une couleur hex"""
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _animate_view_transition(self):
        """Animation glissante de transition entre vues"""
        if not hasattr(self, "content_container"):
            return

        self.content_container.update_idletasks()
        width = self.content_container.winfo_width() or 1200
        self.content_frame.place_configure(x=width, y=0, relwidth=1, relheight=1)

        def slide(x):
            if x <= 0:
                self.content_frame.place_configure(x=0, y=0, relwidth=1, relheight=1)
                return
            self.content_frame.place_configure(x=x, y=0, relwidth=1, relheight=1)
            self.after(10, lambda: slide(x - max(40, width // 20)))

        slide(width)

    def _animate_window_open(self, window):
        """Affiche correctement une fenêtre secondaire (centré, sans animation lourde)."""
        if not window:
            return

        try:
            window.update_idletasks()
        except Exception:
            return

        try:
            parent = self.winfo_toplevel()
            if parent is not window:
                window.transient(parent)
        except Exception:
            pass

        # Center la fenêtre sur l'écran
        try:
            window_width = window.winfo_width()
            window_height = window.winfo_height()
            
            # Si dimensions pas encore calculées, utiliser screen
            if window_width == 1 or window_height == 1:
                window.update_idletasks()
                window_width = window.winfo_width()
                window_height = window.winfo_height()
            
            screen_width = self.screen_width
            screen_height = self.screen_height
            
            # Position centré
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            
            # S'assurer que la fenêtre n'est pas en dehors de l'écran
            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))
            
            window.geometry(f"+{x}+{y}")
        except Exception:
            pass

        try:
            window.deiconify()
            window.lift()
            window.focus_set()
        except Exception:
            pass

    def _show_loading_dialog(self, title: str = "Traitement en cours..."):
        """Affiche un dialog avec un loading indicator
        
        Returns: (dialog_window, loading_indicator_widget)
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("350x120")
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        x = dialog.winfo_screenwidth() // 2 - 175
        y = dialog.winfo_screenheight() // 2 - 60
        dialog.geometry(f"+{x}+{y}")
        
        # Contenu
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        loading = LoadingIndicator(container, text=title, color=self.colors.get("primary", "#3b82f6"))
        loading.start()
        
        self._animate_window_open(dialog)
        return dialog, loading

    def _update_sidebar_layout(self):
        """Met à jour l'affichage de la sidebar selon la taille de fenêtre (avec debouncing)"""
        # Debouncer les updates pendant le scrolling pour éviter le lag
        if self._sidebar_update_debounce_job:
            self.after_cancel(self._sidebar_update_debounce_job)
        
        self._sidebar_update_debounce_job = self.after(200, self._do_update_sidebar_layout)
    
    def _do_update_sidebar_layout(self):
        """Effectue réellement la mise à jour du sidebar"""
        self._sidebar_update_debounce_job = None
        
        try:
            window_width = self.parent_window.winfo_width() if self.parent_window else self.winfo_width()
        except Exception:
            window_width = self.winfo_width()

        force_compact = self.ui_mode in ("tiny", "small", "tablet")
        target_mode = "compact" if force_compact or window_width < self.sidebar_collapse_breakpoint else "full"
        if target_mode == self.sidebar_mode:
            return

        self._apply_sidebar_mode(target_mode)

    def _apply_sidebar_mode(self, mode: str):
        """Applique le mode compact ou complet à la sidebar"""
        self.sidebar_mode = mode

        if mode == "compact":
            self.sidebar.configure(width=self.sidebar_width_compact)
            self.logo_title_label.configure(text="U.O.R", font=ctk.CTkFont(size=22, weight="bold"))
            if self.logo_subtitle_label.winfo_ismapped():
                self.logo_subtitle_label.pack_forget()

            for item in self.nav_buttons:
                btn = item["button"]
                btn.configure(
                    text=item["icon"],
                    anchor="center",
                    font=ctk.CTkFont(size=18, weight="bold")
                )

            if self.logout_btn:
                self.logout_btn.configure(text="🚪", anchor="center")
                try:
                    self.logout_btn.pack_configure(padx=8)
                except Exception:
                    pass

            # DISABLED: Hover binding causes constant flickering/flashing
            # self._bind_sidebar_hover_expand()
        else:
            self.sidebar.configure(width=self.sidebar_width_full)
            self.logo_title_label.configure(text="U.O.R", font=ctk.CTkFont(size=32, weight="bold"))
            if not self.logo_subtitle_label.winfo_ismapped():
                self.logo_subtitle_label.pack()

            for item in self.nav_buttons:
                btn = item["button"]
                btn.configure(
                    text=f"{item['icon']}  {item['label']}",
                    anchor="w",
                    font=ctk.CTkFont(size=13, weight="bold")
                )

            if self.logout_btn:
                self.logout_btn.configure(text="🚪  Déconnexion", anchor="w")
                try:
                    self.logout_btn.pack_configure(padx=15)
                except Exception:
                    pass

            self._unbind_sidebar_hover_expand()

    def _bind_sidebar_hover_expand(self):
        if not self.sidebar:
            return

        self.sidebar.bind("<Enter>", self._on_sidebar_enter)
        self.sidebar.bind("<Leave>", self._on_sidebar_leave)

    def _animate_sidebar_width(self, target_width: int, duration_ms: int = 180, on_complete=None):
        if not self.sidebar:
            return

        if self._sidebar_anim_job:
            try:
                self.after_cancel(self._sidebar_anim_job)
            except Exception:
                pass
            self._sidebar_anim_job = None

        self._sidebar_animating = True
        try:
            current_width = int(self.sidebar.cget("width"))
        except Exception:
            current_width = self.sidebar_width_compact

        steps = max(1, int(duration_ms / 15))
        delta = (target_width - current_width) / steps

        def step(count=0, width=current_width):
            if count >= steps:
                self.sidebar.configure(width=target_width)
                self._sidebar_animating = False
                if on_complete:
                    on_complete()
                return
            width += delta
            self.sidebar.configure(width=int(width))
            self._sidebar_anim_job = self.after(15, lambda: step(count + 1, width))

        step()

    def _unbind_sidebar_hover_expand(self):
        if not self.sidebar:
            return

        self.sidebar.unbind("<Enter>")
        self.sidebar.unbind("<Leave>")
        self.sidebar_hover_expanded = False

    def _on_sidebar_enter(self, _event=None):
        """Expand sidebar on hover (sans animation lourde pour éviter flicker)"""
        if self.sidebar_mode != "compact" or self.sidebar_hover_expanded:
            return
        self.sidebar_hover_expanded = True
        self.logo_subtitle_label.pack()
        for item in self.nav_buttons:
            btn = item["button"]
            btn.configure(
                text=f"{item['icon']}  {item['label']}",
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold")
            )
        if self.logout_btn:
            self.logout_btn.configure(text="🚪  Déconnexion", anchor="w")

        # Expand sidebar directement sans animation (évite flicker)
        self.sidebar.configure(width=self.sidebar_width_full)

    def _on_sidebar_leave(self, _event=None):
        """Collapse sidebar on leave (sans animation)"""
        if self.sidebar_mode != "compact" or not self.sidebar_hover_expanded:
            return
        self.sidebar_hover_expanded = False
        
        # Collapse directement
        if self.logo_subtitle_label.winfo_ismapped():
            self.logo_subtitle_label.pack_forget()
        for item in self.nav_buttons:
            btn = item["button"]
            btn.configure(
                text=item["icon"],
                anchor="center",
                font=ctk.CTkFont(size=18, weight="bold")
            )
        if self.logout_btn:
            self.logout_btn.configure(text="🚪", anchor="center")

        # Collapse sidebar directement sans animation
        self.sidebar.configure(width=self.sidebar_width_compact)

    def _get_table_mode(self) -> str:
        """Retourne le mode de tableau en fonction de la largeur de fenêtre"""
        try:
            window_width = self.parent_window.winfo_width() if self.parent_window else self.winfo_width()
        except Exception:
            window_width = self.winfo_width()
        return "compact" if window_width < self.table_compact_breakpoint else "large"

    def _update_table_mode(self):
        """Met à jour le mode des tableaux et rafraîchit la vue si besoin"""
        new_mode = self._get_table_mode()
        if new_mode == self.table_mode:
            return
        self.table_mode = new_mode
        self._render_current_view()

    def _make_card_clickable(self, card, command):
        """Rend une carte cliquable avec effet hover"""
        if not command:
            return
        command = lambda: self._run_with_loading(command)
        base_color = card.cget("fg_color")
        hover_color = self._shade_color(base_color, 0.9)

        def on_enter(_):
            card.configure(fg_color=hover_color)

        def on_leave(_):
            card.configure(fg_color=base_color)

        def on_click(_):
            command()

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", on_click)

    def _fc_to_usd(self, amount_usd: float) -> float:
        try:
            return float(amount_usd)
        except Exception:
            return 0.0

    def _format_usd(self, amount_usd: float) -> str:
        return f"${self._fc_to_usd(amount_usd):,.2f}"

    def _get_cached_photo(self, photo_path: str = None, photo_blob: bytes = None, size=(40, 50)):
        """Retourne une image CTkImage depuis cache"""
        cache_key = None
        if photo_path:
            cache_key = f"path:{photo_path}:{size}"
        elif photo_blob:
            digest = hashlib.sha256(photo_blob).hexdigest()
            cache_key = f"blob:{digest}:{size}"

        if cache_key and cache_key in self._photo_cache:
            return self._photo_cache[cache_key]

        image = None
        try:
            if photo_path and os.path.exists(photo_path):
                image = Image.open(photo_path)
            elif photo_blob:
                image = Image.open(io.BytesIO(photo_blob))
            if image:
                image.thumbnail(size)
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                if cache_key:
                    self._photo_cache[cache_key] = ctk_image
                return ctk_image
        except Exception:
            return None

        return None

    def _render_photo_cell(self, row, column_index: int, photo_path: str = None, photo_blob: bytes = None, size=(40, 50)):
        """Rend une cellule photo dans un tableau"""
        photo_frame = ctk.CTkFrame(row, fg_color="transparent")
        photo_frame.grid(row=0, column=column_index, sticky="ew", padx=10, pady=6)
        ctk_image = self._get_cached_photo(photo_path, photo_blob, size=size)
        if ctk_image:
            photo_label = ctk.CTkLabel(photo_frame, image=ctk_image, text="")
            photo_label.image = ctk_image
            photo_label.pack()
        else:
            ctk.CTkLabel(photo_frame, text="—", text_color=self.colors["text_light"]).pack()
    
    def _create_stat_card(self, parent, title, value, icon, color, action_text, action_command=None):
        """Crée une carte de statistique colorée - RESPONSIVE"""
        is_small_screen = self.screen_width < 1000
        
        card_height = 120 if is_small_screen else 140
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=12, height=card_height)
        card.pack_propagate(False)
        hover_color = self._shade_color(color, 0.9)
        
        # En-tête avec titre et icône
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15 if is_small_screen else 20, pady=(15 if is_small_screen else 20, 8))
        
        title_size = 10 if is_small_screen else 12
        header_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=title_size),
            text_color=self.colors["text_white"]
        )
        header_label.pack(side="left")
        
        icon_size = 16 if is_small_screen else 20
        icon_label = ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=icon_size)
        )
        icon_label.pack(side="right")
        
        # Valeur
        value_size = 20 if is_small_screen else 28
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=value_size, weight="bold"),
            text_color=self.colors["text_white"]
        )
        value_label.pack(anchor="w", padx=15 if is_small_screen else 20, pady=(0, 10))
        
        # Action
        action_size = 9 if is_small_screen else 11
        wrapped_command = (lambda: self._run_with_loading(action_command)) if action_command else None
        action_btn = ctk.CTkButton(
            card,
            text=action_text,
            fg_color="transparent",
            hover_color="#0a0a0a",
            text_color=self.colors["text_white"],
            font=ctk.CTkFont(size=action_size),
            height=22 if is_small_screen else 25,
            corner_radius=6,
            command=wrapped_command
        )
        action_btn.pack(anchor="w", padx=15 if is_small_screen else 20, pady=(0, 10))

        if action_command:
            def on_enter(_):
                card.configure(fg_color=hover_color)

            def on_leave(_):
                card.configure(fg_color=color)

            def on_click(_):
                wrapped_command()

            for widget in (card, header, header_label, icon_label, value_label):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
        
        return card

    def _configure_table_columns(self, frame, column_weights, min_widths=None):
        """Configure la grille des colonnes pour un tableau"""
        for idx, weight in enumerate(column_weights):
            try:
                weight_value = int(round(weight))
            except Exception:
                weight_value = 1
            if weight_value <= 0:
                weight_value = 1
            min_size = None
            if min_widths and idx < len(min_widths):
                min_size = min_widths[idx]
            if min_size:
                frame.grid_columnconfigure(idx, weight=weight_value, minsize=min_size)
            else:
                frame.grid_columnconfigure(idx, weight=weight_value)

    def _set_scrollbar_visible(self, scrollable_frame, visible: bool, width: int = None):
        """Affiche ou masque la barre de scroll d'un CTkScrollableFrame"""
        bar = getattr(scrollable_frame, "_scrollbar", None)
        if not bar:
            return
        target_width = width if width is not None else self._scaled(12)
        if not visible:
            target_width = 0
        try:
            bar.configure(width=target_width)
        except Exception:
            pass

    def _set_main_scrollbar_visible(self, visible: bool):
        """Gère la barre de scroll principale (content_frame)"""
        if hasattr(self, "content_frame"):
            self._set_scrollbar_visible(self.content_frame, visible)

    def _create_table_header(self, parent, headers, column_weights, anchors=None, min_widths=None, padx=10, pady=10):
        """Crée un header de tableau aligné - RESPONSIVE"""
        # Adapter font size pour petit écran
        is_tiny_screen = self.screen_width < 900
        header_font_size = 9 if is_tiny_screen else 11
        
        header_frame = ctk.CTkFrame(parent, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=(0, 0))

        for col, header_text in enumerate(headers):
            anchor = anchors[col] if anchors else "center"
            label = ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=header_font_size, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=anchor,
                wraplength=min_widths[col] - 4 if min_widths and col < len(min_widths) else 0
            )
            label.grid(row=0, column=col, sticky="ew", padx=padx, pady=pady)

        self._configure_table_columns(header_frame, column_weights, min_widths=min_widths)
        return header_frame

    def _get_table_layout(self, key: str, fallback_count: int = 0):
        """Retourne un layout standardisé (weights + anchors) pour les tableaux - RESPONSIVE"""
        # Adapte les layout selon la taille d'écran
        is_small_screen = self.screen_width < 1200
        is_tiny_screen = self.screen_width < 900
        
        layouts = {
            "dashboard_access": {
                "weights": [3, 1.2, 2, 1] if not is_tiny_screen else [2, 1, 1.5, 0.8],
                "anchors": ["w", "w", "w", "e"],
                "min_widths_large": [220, 90, 160, 90],
                "min_widths_compact": [140, 70, 100, 70],
                "min_widths_tiny": [100, 60, 80, 60],
            },
            "students_promo": {
                "weights": [1.2, 3, 3, 1.2, 1.2, 1.2, 2] if not is_small_screen else [1, 2, 2, 1, 1, 1, 1.5],
                "anchors": ["center", "w", "w", "center", "center", "center", "center"],
                "min_widths_large": [70, 200, 220, 95, 95, 95, 150],
                "min_widths_compact": [60, 160, 180, 85, 85, 85, 120],
                "min_widths_tiny": [50, 120, 140, 75, 75, 75, 100],
            },
            "payment_history": {
                "weights": [2.2, 1.2, 1.2] if not is_tiny_screen else [2, 1, 1],
                "anchors": ["w", "e", "center"],
                "min_widths_large": [220, 120, 120],
                "min_widths_compact": [160, 100, 100],
                "min_widths_tiny": [120, 80, 80],
            },
            "finance_payments": {
                "weights": [1.2, 3, 1.2, 2, 2, 1.2, 1.2] if not is_small_screen else [1, 2, 1, 1.5, 1.5, 1, 1],
                "anchors": ["center", "w", "w", "e", "e", "center", "center"],
                "min_widths_large": [70, 220, 90, 150, 150, 110, 110],
                "min_widths_compact": [60, 170, 80, 120, 120, 95, 95],
                "min_widths_tiny": [50, 130, 70, 100, 100, 80, 80],
            },
            "access_logs": {
                "weights": [1.2, 3, 1.2, 2, 1, 1, 1, 1, 1.2] if not is_small_screen else [1, 2, 1, 1.5, 0.8, 0.8, 0.8, 0.8, 1],
                "anchors": ["center", "w", "w", "w", "center", "center", "center", "center", "e"],
                "min_widths_large": [70, 220, 90, 160, 90, 90, 90, 90, 100],
                "min_widths_compact": [60, 170, 80, 130, 75, 75, 75, 75, 90],
                "min_widths_tiny": [50, 130, 70, 100, 65, 65, 65, 65, 80],
            },
            "reports_faculty": {
                "weights": [1.2, 2.5, 2.5, 1.2, 1.2, 1.2, 2] if not is_small_screen else [1, 2, 2, 1, 1, 1, 1.5],
                "anchors": ["center", "w", "w", "center", "center", "center", "e"],
                "min_widths_large": [70, 180, 180, 120, 120, 120, 150],
                "min_widths_compact": [60, 150, 150, 110, 110, 110, 130],
                "min_widths_tiny": [50, 120, 120, 95, 95, 95, 110],
            },
            "academic_promos": {
                "weights": [2.2, 3, 3, 1.2, 1.2, 1.2, 1.2] if not is_small_screen else [2, 2.2, 2.2, 1, 1, 1, 1],
                "anchors": ["center", "center", "center", "center", "center", "center", "center"],
                "min_widths_large": [180, 220, 220, 90, 110, 110, 110],
                "min_widths_compact": [160, 180, 180, 80, 95, 95, 95],
                "min_widths_tiny": [140, 140, 140, 75, 85, 85, 85],
            },
            "exam_periods": {
                "weights": [3, 1.2, 1.2, 1.2] if not is_tiny_screen else [2, 1, 1, 1],
                "anchors": ["w", "center", "center", "e"],
                "min_widths_large": [220, 120, 120, 110],
                "min_widths_compact": [180, 100, 100, 95],
                "min_widths_tiny": [140, 85, 85, 80],
            },
        }

        layout = layouts.get(key)
        if layout:
            mode = self._get_table_mode()
            if is_tiny_screen and "min_widths_tiny" in layout:
                min_widths = layout.get("min_widths_tiny")
            elif mode == "compact":
                min_widths = layout.get("min_widths_compact") or layout.get("min_widths_large")
            else:
                min_widths = layout.get("min_widths_large")
            return {
                "weights": layout["weights"],
                "anchors": layout["anchors"],
                "min_widths": min_widths,
            }

        fallback_weights = [1] * max(0, fallback_count)
        fallback_anchors = ["center"] * max(0, fallback_count)
        fallback_min_widths = [60] * max(0, fallback_count)  # Réduit pour petit écran
        return {"weights": fallback_weights, "anchors": fallback_anchors, "min_widths": fallback_min_widths}

    def _populate_table_row(self, row, values, column_weights, text_colors=None, font_sizes=None,
                            font_weights=None, anchors=None, min_widths=None, padx=10, pady=8):
        """Ajoute des cellules alignées dans une ligne - RESPONSIVE"""
        # Adapter les font sizes pour petit écran
        is_tiny_screen = self.screen_width < 900
        
        for col, value in enumerate(values):
            color = text_colors[col] if text_colors else self.colors["text_dark"]
            base_size = font_sizes[col] if font_sizes else 10
            # Réduire la taille de font pour petit écran
            size = max(8, base_size - 1) if is_tiny_screen else base_size
            weight = font_weights[col] if font_weights else "normal"
            anchor = anchors[col] if anchors else "center"

            label = ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=size, weight=weight),
                text_color=color,
                anchor=anchor,
                wraplength=min_widths[col] - 4 if min_widths else 0  # Allow text wrapping
            )
            label.grid(row=0, column=col, sticky="ew", padx=padx, pady=pady)

        self._configure_table_columns(row, column_weights, min_widths=min_widths)

    def _populate_table_row_with_offset(self, row, values, column_weights, start_col=0,
                                        text_colors=None, font_sizes=None, font_weights=None,
                                        anchors=None, min_widths=None, padx=10, pady=8):
        """Ajoute des cellules alignées avec un décalage de colonne - RESPONSIVE"""
        # Adapter les font sizes pour petit écran
        is_tiny_screen = self.screen_width < 900
        
        self._configure_table_columns(row, column_weights, min_widths=min_widths)
        for idx, value in enumerate(values):
            color = text_colors[idx] if text_colors else self.colors["text_dark"]
            base_size = font_sizes[idx] if font_sizes else 10
            # Réduire la taille de font pour petit écran
            size = max(8, base_size - 1) if is_tiny_screen else base_size
            weight = font_weights[idx] if font_weights else "normal"
            anchor = anchors[idx] if anchors else "center"
            
            col_idx = start_col + idx
            wrap_width = min_widths[col_idx] - 4 if min_widths and col_idx < len(min_widths) else 0

            label = ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=size, weight=weight),
                text_color=color,
                anchor=anchor,
                wraplength=wrap_width if wrap_width > 0 else 0
            )
            label.grid(row=0, column=col_idx, sticky="ew", padx=padx, pady=pady)
    
    def _update_nav_buttons(self, active_key):
        """Met à jour le style du menu actif"""
        for item in self.nav_buttons:
            btn = item["button"]
            key = item["key"]
            if key == active_key:
                btn.configure(fg_color=self.colors["primary"])
            else:
                btn.configure(fg_color="transparent")
    
    def _show_dashboard(self):
        """Affiche le dashboard principal avec données académiques"""
        self.current_view = "dashboard"
        self._clear_content()
        self._update_nav_buttons("dashboard")
        self.title_label.configure(text=self._t("dashboard", "Dashboard"))
        self.subtitle_label.configure(
            text="{} • {}".format(
                self._t("overview", "Vue d'ensemble"),
                datetime.now().strftime("%d %B %Y")
            )
        )
        
        # Charger les données académiques
        total_students = self.dashboard_service.get_total_students()
        eligible_students = self.dashboard_service.get_eligible_students()
        non_eligible_students = self.dashboard_service.get_non_eligible_students()
        access_granted = self.dashboard_service.get_access_granted()
        access_denied = self.dashboard_service.get_access_denied()
        revenue = self.dashboard_service.get_revenue_collected()
        completion = self.dashboard_service.get_degree_of_completion()
        activities = self.dashboard_service.get_recent_activities(8)
        
        # === ROW 1: INFO + ACTIVITÉS + PROGRESSION ===
        row1 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 20))
        
        # Carte d'Information Académique
        info_card = self._create_card(row1, height=250)
        info_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._make_card_clickable(info_card, self._show_students)
        
        ctk.CTkLabel(
            info_card,
            text="📚 Plateforme d'Accès aux Examens",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 5))
        
        info_text = (
            "Gestion académique centralisée pour l'accès sécurisé aux examens. "
            "Contrôlez l'éligibilité des étudiants, suivez les paiements et "
            "consultez l'historique d'accès en temps réel."
        )
        info_label = ctk.CTkLabel(
            info_card,
            text=info_text,
            font=self._font(12),
            text_color=self.colors["text_light"],
            wraplength=350,
            justify="left"
        )
        info_label.pack(anchor="w", padx=25, pady=(0, 15))
        self._register_wrap(info_label, ratio=0.32, min_width=260, max_width=520)
        
        # Stats d'une ligne (single line with responsive wrap)
        stats_row_info = ctk.CTkFrame(info_card, fg_color="transparent")
        stats_row_info.pack(fill="x", padx=25, pady=8)

        stats_font_size = 12 if self.screen_width < 1200 else 13
        stats_text = (
            f"👥 Total: {total_students}    "
            f"✅ Éligibles: {eligible_students}    "
            f"❌ Non éligibles: {non_eligible_students}"
        )

        stats_label = ctk.CTkLabel(
            stats_row_info,
            text=stats_text,
            font=ctk.CTkFont(size=stats_font_size, weight="bold"),
            text_color=self.colors["text_dark"],
            anchor="w",
            justify="left",
            wraplength=360
        )
        stats_label.pack(anchor="w", fill="x")
        self._register_wrap(stats_label, ratio=0.55, min_width=240, max_width=520)
        
        # Image académique
        img_frame = ctk.CTkFrame(info_card, fg_color=self.colors["primary"], height=80, corner_radius=8)
        img_frame.pack(fill="x", padx=25, pady=(10, 20))
        img_frame.pack_propagate(False)
        ctk.CTkLabel(
            img_frame,
            text="🎓",
            font=ctk.CTkFont(size=50)
        ).pack(expand=True)
        
        # Activités Récentes
        activity_card = self._create_card(row1, height=250)
        activity_card.pack(side="left", fill="both", expand=True, padx=(5, 5))
        self._make_card_clickable(activity_card, self._show_access_logs)
        
        ctk.CTkLabel(
            activity_card,
            text="🕐 Activités Récentes",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Afficher les activités
        for activity in activities[:4]:
            act_item = ctk.CTkFrame(activity_card, fg_color="transparent")
            act_item.pack(fill="x", padx=25, pady=4)
            
            color = self.colors["success"] if activity["status"] == "granted" else self.colors["danger"]
            dot = ctk.CTkLabel(act_item, text="●", text_color=color, font=ctk.CTkFont(size=14))
            dot.pack(side="left", padx=(0, 10))
            
            text_frame = ctk.CTkFrame(act_item, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                text_frame,
                text=activity['action'],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                text_frame,
                text=f"{activity['student']} ({activity['id']})",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_light"]
            ).pack(anchor="w")
        
        # Progression vers l'Éligibilité
        progress_card = self._create_card(row1, height=250)
        progress_card.pack(side="left", fill="both", expand=True, padx=(5, 0))
        self._make_card_clickable(progress_card, self._show_finance)
        
        ctk.CTkLabel(
            progress_card,
            text="📊 Taux d'Éligibilité",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 10))
        
        # Pourcentage d'éligibilité
        percentage = completion["percentage"]
        ctk.CTkLabel(
            progress_card,
            text=f"{percentage:.1f}%",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.colors["primary"]
        ).pack(anchor="w", padx=25, pady=(0, 5))
        
        # Barre de progression globale
        overall_bar = ctk.CTkProgressBar(
            progress_card,
            height=12,
            progress_color=self.colors["primary"],
            fg_color=self.colors["border"]
        )
        overall_bar.set(percentage / 100)
        overall_bar.pack(fill="x", padx=25, pady=(0, 15))
        
        # Détails
        detail_text = f"{completion['eligible']} / {completion['total']} étudiants éligibles"
        ctk.CTkLabel(
            progress_card,
            text=detail_text,
            font=ctk.CTkFont(size=11 if self.screen_width < 1200 else 12),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", padx=25, pady=(0, 8))
        
        # Autres progressions
        others = [
            ("Accès Accordés", access_granted, 15, self.colors["success"]),
            ("Accès Refusés", access_denied, 5, self.colors["danger"]),
        ]
        
        for label, count, est_max, color in others:
            item = ctk.CTkFrame(progress_card, fg_color="transparent")
            item.pack(fill="x", padx=25, pady=5)
            
            label_frame = ctk.CTkFrame(item, fg_color="transparent")
            label_frame.pack(fill="x")
            
            ctk.CTkLabel(
                label_frame,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color=self.colors["text_dark"]
            ).pack(side="left")
            
            ctk.CTkLabel(
                label_frame,
                text=f"{count}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=color
            ).pack(side="right")
            
            # Mini bar
            bar_value = min(count / est_max, 1.0)
            mini_bar = ctk.CTkProgressBar(
                item,
                height=4,
                progress_color=color,
                fg_color=self.colors["border"]
            )
            mini_bar.set(bar_value)
            mini_bar.pack(fill="x", pady=(2, 0))
        
        # === ROW 2: STAT CARDS ACADÉMIQUES ===
        stats_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 20))
        
        academic_stats = [
            ("Total Étudiants", str(total_students), "👥", self.colors["primary"], "Voir tous", self._show_students),
            ("Accès Accordés", str(access_granted), "✅", self.colors["success"], "Voir logs", self._show_access_logs),
            ("Revenus Collectés", self._format_usd(revenue), "💰", self.colors["warning"], "Détails", self._show_finance),
            ("Accès Refusés", str(access_denied), "❌", self.colors["danger"], "Rapports", self._show_reports)
        ]

        # Responsive: layout horizontal ou vertical selon écran
        is_small_screen = self.screen_width < 1000
        stats_layout_side = "top" if is_small_screen else "left"
        
        for i, (title, value, icon, color, action, command) in enumerate(academic_stats):
            stat_card = self._create_stat_card(stats_row, title, value, icon, color, action, action_command=command)
            stat_card.pack(side=stats_layout_side, fill="both", expand=True, padx=(0 if i == 0 else 3), pady=(0 if i == 0 else 3))
        
        # === ROW 3: GRAPHIQUES ET DÉTAILS ===
        row3 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row3.pack(fill="both", expand=True)
        
        # Historique d'Accès Détaillé
        access_card = self._create_card(row3)
        access_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self._make_card_clickable(access_card, self._show_access_logs)
        
        ctk.CTkLabel(
            access_card,
            text="📋 Historique d'Accès Détaillé",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Tableau des activités
        table_frame = ctk.CTkFrame(access_card, fg_color=self.colors["hover"], corner_radius=8)
        table_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        # Header du tableau
        headers = ["Étudiant", "ID", "Action", "Heure"]
        layout = self._get_table_layout("dashboard_access", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table_frame, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=8)
        
        # Lignes du tableau
        layout = self._get_table_layout("dashboard_access")
        row_min_widths = layout["min_widths"]
        for activity in activities:
            row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=3)
            
            action_color = self.colors["success"] if "accordé" in activity['action'] else self.colors["danger"]
            time_str = activity['timestamp'].strftime("%H:%M") if hasattr(activity['timestamp'], 'strftime') else str(activity['timestamp'])[-8:-3]

            row_values = [activity['student'], activity['id'], activity['action'], time_str]
            row_colors = [self.colors["text_dark"], self.colors["text_light"], action_color, self.colors["text_light"]]
            row_weights = ["normal", "normal", "bold", "normal"]
            row_anchors = ["w", "w", "w", "e"]
            self._populate_table_row(
                row_frame,
                row_values,
                column_weights,
                text_colors=row_colors,
                font_weights=row_weights,
                anchors=row_anchors,
                min_widths=row_min_widths,
                padx=15,
                pady=5
            )
        
        # Résumé Financier
        fin_width = 320 if self.screen_width < 1000 else (360 if self.screen_width < 1400 else 400)
        financial_card = self._create_card(row3, width=fin_width)
        financial_card.pack(side="right", fill="y", padx=(5, 0))
        financial_card.pack_propagate(False)
        self._make_card_clickable(financial_card, self._show_finance)
        
        ctk.CTkLabel(
            financial_card,
            text="💵 Résumé Financier",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Données financières
        financial_data = [
            (self._format_usd(revenue), "Revenus Totaux", "green"),
            (self._format_usd(revenue * 0.85), "Paiements Vérifiés", "blue"),
            (self._format_usd(revenue * 0.15), "En Attente", "orange"),
        ]
        
        for amount, label, color_key in financial_data:
            fin_item = ctk.CTkFrame(financial_card, fg_color=self.colors["hover"], corner_radius=8)
            fin_item.pack(fill="x", padx=20, pady=6)
            
            ctk.CTkLabel(
                fin_item,
                text=amount,
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(anchor="w", padx=15, pady=(10, 0))
            
            ctk.CTkLabel(
                fin_item,
                text=label,
                font=ctk.CTkFont(size=11),
                text_color=self.colors["text_light"]
            ).pack(anchor="w", padx=15, pady=(0, 10))

        # === ROW 4: ESP32 COMMUNICATION ===
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row4.pack(fill="x", pady=(20, 0))

        esp_card = self._create_card(row4)
        esp_card.pack(fill="x", expand=True)

        ctk.CTkLabel(
            esp_card,
            text="📡 Communication ESP32 (Wi‑Fi)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 8))

        ctk.CTkLabel(
            esp_card,
            text=(
                "• L’ESP32 se connecte au Wi‑Fi et contacte le serveur U.O.R.\n"
                "• L’étudiant envoie: Matricule + Code d’accès + Photo.\n"
                "• Le système répond: ACCÈS_OK / ERR_AUTH / ERR_FACE / ERR_FINANCE."
            ),
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_light"],
            justify="left"
        ).pack(anchor="w", padx=25, pady=(0, 12))

        status_row = ctk.CTkFrame(esp_card, fg_color=self.colors["hover"], corner_radius=8)
        status_row.pack(fill="x", padx=25, pady=(0, 20))
        self._esp32_status_label = ctk.CTkLabel(
            status_row,
            text="Statut: En attente de connexion ESP32",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["warning"]
        )
        self._esp32_status_label.pack(anchor="w", padx=15, pady=10)

        self._refresh_esp32_status()
    
    def _show_students(self):
        """Affiche la page Étudiants avec navigation hiérarchique Faculté > Département > Promotion"""
        self._set_main_scrollbar_visible(False)
        self.current_view = "students"
        self._clear_content()
        self._update_nav_buttons("students")
        self.title_label.configure(text=self._t("students_title", "Gestion des Étudiants"))
        self.subtitle_label.configure(text=self._t("students_subtitle", "Gestion et suivi des étudiants"))
        
        # Variables de navigation (préserver si déjà définies)
        if not hasattr(self, "nav_state") or not isinstance(self.nav_state, dict):
            self.nav_state = {
                'level': 'faculty',  # faculty, department, promotion
                'selected_faculty': None,
                'selected_department': None,
                'selected_promotion': None
            }
        if not hasattr(self, "selected_academic_year_id"):
            self.selected_academic_year_id = None
        
        # === HEADER ===

        # Récupérer toutes les données des étudiants
        self.students_full_data_all = self.student_service.get_all_students_with_finance()

        # Si l'année sélectionnée n'a aucun étudiant, réinitialiser le filtre
        if self.selected_academic_year_id:
            has_students_for_year = any(
                s.get("academic_year_id") == self.selected_academic_year_id
                for s in self.students_full_data_all
            )
            if not has_students_for_year:
                self.selected_academic_year_id = None

        # === NAVIGATION ANNÉE ACADÉMIQUE ===
        year_filter_frame = ctk.CTkFrame(self.content_frame, fg_color=self.colors["hover"], corner_radius=8, height=48)
        year_filter_frame.pack(fill="x", pady=(0, 6))
        year_filter_frame.pack_propagate(False)

        ctk.CTkLabel(
            year_filter_frame,
            text="📅 Année académique:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(15, 10), pady=4)

        academic_years = self.academic_year_service.get_years()
        year_names = [y.get("year_name") for y in academic_years if y.get("year_name")]
        self.academic_year_map = {y.get("year_name"): y.get("academic_year_id") for y in academic_years}

        year_filter = ctk.CTkComboBox(
            year_filter_frame,
            values=["Toutes Années"] + year_names,
            width=220,
            height=30
        )
        if self.selected_academic_year_id:
            current_name = next(
                (name for name, yid in self.academic_year_map.items() if yid == self.selected_academic_year_id),
                None
            )
            year_filter.set(current_name or "Toutes Années")
        else:
            year_filter.set("Toutes Années")
        year_filter.pack(side="left", padx=(0, 10), pady=4)

        ctk.CTkFrame(year_filter_frame, fg_color="transparent").pack(side="left", fill="x", expand=True)

        try:
            layout_width = self.parent_window.winfo_width() if self.parent_window else self.winfo_width()
        except Exception:
            layout_width = self.winfo_width()
        if not layout_width:
            layout_width = self.screen_width
        is_compact_layout = layout_width < 1100

        actions_row = None
        if is_compact_layout:
            actions_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            actions_row.pack(fill="x", pady=(0, 6))

        self.students_stats_label = ctk.CTkLabel(
            year_filter_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"]
        )
        self.students_stats_label.pack(side="left", padx=(0, 10), pady=4)

        add_btn_parent = actions_row if actions_row is not None else year_filter_frame
        add_btn = ctk.CTkButton(
            add_btn_parent,
            text=f"➕ {self._t('add_student', 'Ajouter étudiant')}",
            fg_color=self.colors["primary"],
            hover_color=self.colors["info"],
            text_color=self.colors["text_white"],
            height=32,
            corner_radius=8,
            command=self._open_add_student_dialog
        )
        add_btn.pack(side="right", padx=(0, 10), pady=4)

        has_year_data = any(s.get("academic_year_id") for s in self.students_full_data_all)
        if not has_year_data or not year_names:
            year_filter.configure(state="disabled")
        
        # === BREADCRUMB (Fil d'Ariane) ===
        self.breadcrumb_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.breadcrumb_frame.pack(fill="x", pady=(0, 4))
        
        # === CONTAINER PRINCIPAL ===
        self.students_main_card = self._create_card(self.content_frame)
        self.students_main_card.pack(fill="both", expand=True)

        # Afficher la vue initiale (Facultés)
        self._update_students_stats()
        self._render_students_navigation()

        year_filter.configure(command=lambda _value: self._on_students_year_change(year_filter.get()))
    
    def _render_students_navigation(self):
        """Rend la navigation hiérarchique selon le niveau actuel"""
        self.students_full_data = self._get_students_filtered_by_year()
        # Nettoyer le contenu
        for widget in self.students_main_card.winfo_children():
            widget.destroy()
        
        # Mettre à jour le breadcrumb
        self._update_breadcrumb()
        
        # Afficher le niveau approprié
        if self.nav_state['level'] == 'faculty':
            self._show_faculties_view()
        elif self.nav_state['level'] == 'department':
            self._show_departments_view()
        elif self.nav_state['level'] == 'promotion':
            self._show_promotions_view()

    def _get_students_filtered_by_year(self):
        """Retourne les étudiants filtrés par année académique sélectionnée"""
        data = self.students_full_data_all or []
        if not self.selected_academic_year_id:
            return data
        return [s for s in data if s.get("academic_year_id") == self.selected_academic_year_id]

    def _update_students_stats(self):
        """Met à jour les stats rapides selon l'année sélectionnée"""
        data = self._get_students_filtered_by_year()
        total = len(data)
        eligible = sum(1 for s in data if s.get("is_eligible"))
        non_eligible = total - eligible
        if self.students_stats_label:
            self.students_stats_label.configure(
                text=f"Total: {total} | ✅ Éligibles: {eligible} | ❌ Non-éligibles: {non_eligible}"
            )

    def _on_students_year_change(self, selected_value: str):
        """Gère le changement d'année académique pour la vue étudiants"""
        if selected_value == "Toutes Années":
            self.selected_academic_year_id = None
        else:
            self.selected_academic_year_id = self.academic_year_map.get(selected_value)

        self.nav_state['level'] = 'faculty'
        self.nav_state['selected_faculty'] = None
        self.nav_state['selected_department'] = None
        self.nav_state['selected_promotion'] = None

        self._update_students_stats()
        self._render_students_navigation()
    
    def _update_breadcrumb(self):
        """Met à jour le fil d'Ariane"""
        for widget in self.breadcrumb_frame.winfo_children():
            widget.destroy()
        
        # Icône maison pour retour aux facultés
        home_btn = ctk.CTkButton(
            self.breadcrumb_frame,
            text="🏛️ Facultés",
            fg_color=self.colors["primary"] if self.nav_state['level'] == 'faculty' else "transparent",
            hover_color=self.colors["hover"],
            text_color=self.colors["text_white"] if self.nav_state['level'] == 'faculty' else self.colors["primary"],
            height=28,
            corner_radius=6,
            command=lambda: self._navigate_to('faculty')
        )
        home_btn.pack(side="left", padx=(0, 5))
        
        if self.nav_state['selected_faculty']:
            # Séparateur
            ctk.CTkLabel(
                self.breadcrumb_frame,
                text="›",
                font=ctk.CTkFont(size=16),
                text_color=self.colors["text_light"]
            ).pack(side="left", padx=5)
            
            # Bouton faculté
            faculty_btn = ctk.CTkButton(
                self.breadcrumb_frame,
                text=f"📚 {self.nav_state['selected_faculty']['name']}",
                fg_color=self.colors["primary"] if self.nav_state['level'] == 'department' else "transparent",
                hover_color=self.colors["hover"],
                text_color=self.colors["text_white"] if self.nav_state['level'] == 'department' else self.colors["primary"],
                height=28,
                corner_radius=6,
                command=lambda: self._navigate_to('department')
            )
            faculty_btn.pack(side="left", padx=(0, 5))
        
        if self.nav_state['selected_department']:
            # Séparateur
            ctk.CTkLabel(
                self.breadcrumb_frame,
                text="›",
                font=ctk.CTkFont(size=16),
                text_color=self.colors["text_light"]
            ).pack(side="left", padx=5)
            
            # Bouton département
            dept_btn = ctk.CTkButton(
                self.breadcrumb_frame,
                text=f"📂 {self.nav_state['selected_department']['name']}",
                fg_color=self.colors["primary"],
                hover_color=self.colors["hover"],
                text_color=self.colors["text_white"],
                height=28,
                corner_radius=6,
                state="disabled"
            )
            dept_btn.pack(side="left")
    
    def _navigate_to(self, level):
        """Navigation entre les niveaux"""
        if level == 'faculty':
            self.nav_state['level'] = 'faculty'
            self.nav_state['selected_faculty'] = None
            self.nav_state['selected_department'] = None
            self.nav_state['selected_promotion'] = None
        elif level == 'department':
            self.nav_state['level'] = 'department'
            self.nav_state['selected_department'] = None
            self.nav_state['selected_promotion'] = None
        
        self._render_students_navigation()
    
    def _show_faculties_view(self):
        """Affiche les cartes des facultés"""
        # Titre
        title_frame = ctk.CTkFrame(self.students_main_card, fg_color="transparent")
        title_frame.pack(fill="x", padx=25, pady=(6, 6))
        
        ctk.CTkLabel(
            title_frame,
            text="🏛️ Sélectionnez une Faculté",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Cliquez sur une faculté pour voir ses départements",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(5, 0))
        
        # Scroll frame pour les cartes
        scroll_frame = ctk.CTkScrollableFrame(self.students_main_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        # Regrouper les étudiants par faculté
        faculties_data = {}
        for student in self.students_full_data:
            faculty_id = student.get('faculty_id')
            faculty_name = student.get('faculty_name')
            faculty_code = student.get('faculty_code')
            
            if not faculty_id or not faculty_name:
                continue
            
            if faculty_id not in faculties_data:
                faculties_data[faculty_id] = {
                    'id': faculty_id,
                    'name': faculty_name,
                    'code': faculty_code or faculty_name[:3].upper(),
                    'students': []
                }
            faculties_data[faculty_id]['students'].append(student)
        
        # Créer les cartes
        if not faculties_data:
            ctk.CTkLabel(
                scroll_frame,
                text="Aucune faculté trouvée",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_light"]
            ).pack(pady=50)
            return
        
        # Grille de cartes (2 colonnes)
        for idx, (faculty_id, faculty_info) in enumerate(sorted(faculties_data.items(), key=lambda x: x[1]['name'])):
            card = ctk.CTkFrame(
                scroll_frame,
                fg_color=self.colors["hover"],
                corner_radius=12,
                cursor="hand2"
            )
            card.pack(fill="x", pady=8)
            
            # Bind click event
            card.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            # Contenu de la carte
            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=20, pady=15)
            content_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            # Header
            header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            header_frame.pack(fill="x")
            header_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            icon_label = ctk.CTkLabel(
                header_frame,
                text="🏛️",
                font=ctk.CTkFont(size=32)
            )
            icon_label.pack(side="left", padx=(0, 15))
            icon_label.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)
            info_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            name_label = ctk.CTkLabel(
                info_frame,
                text=faculty_info['name'],
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor="w"
            )
            name_label.pack(anchor="w")
            name_label.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            code_label = ctk.CTkLabel(
                info_frame,
                text=f"Code: {faculty_info['code']}",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"],
                anchor="w"
            )
            code_label.pack(anchor="w")
            code_label.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            # Stats
            students_count = len(faculty_info['students'])
            eligible_count = sum(1 for s in faculty_info['students'] if s.get('is_eligible'))
            
            stats_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            stats_frame.pack(fill="x", pady=(10, 0))
            stats_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            self._create_stat_badge(stats_frame, "👥", f"{students_count} étudiants", self.colors["info"]).pack(side="left", padx=(0, 10))
            self._create_stat_badge(stats_frame, "✅", f"{eligible_count} éligibles", self.colors["success"]).pack(side="left")
    
    def _show_departments_view(self):
        """Affiche les départements de la faculté sélectionnée"""
        if not self.nav_state['selected_faculty']:
            return
        
        # Titre
        title_frame = ctk.CTkFrame(self.students_main_card, fg_color="transparent")
        title_frame.pack(fill="x", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(
            title_frame,
            text=f"📂 Départements de {self.nav_state['selected_faculty']['name']}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Cliquez sur un département pour voir ses promotions",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(5, 0))
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(self.students_main_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        # Regrouper par département
        departments_data = {}
        faculty_id = self.nav_state['selected_faculty']['id']
        
        for student in self.students_full_data:
            if student.get('faculty_id') != faculty_id:
                continue
            
            dept_id = student.get('department_id')
            dept_name = student.get('department_name')
            dept_code = student.get('department_code')
            
            if not dept_id or not dept_name:
                continue
            
            if dept_id not in departments_data:
                departments_data[dept_id] = {
                    'id': dept_id,
                    'name': dept_name,
                    'code': dept_code or dept_name[:3].upper(),
                    'students': []
                }
            departments_data[dept_id]['students'].append(student)
        
        if not departments_data:
            ctk.CTkLabel(
                scroll_frame,
                text="Aucun département trouvé pour cette faculté",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_light"]
            ).pack(pady=50)
            return
        
        # Créer les cartes
        for dept_id, dept_info in sorted(departments_data.items(), key=lambda x: x[1]['name']):
            card = ctk.CTkFrame(
                scroll_frame,
                fg_color=self.colors["hover"],
                corner_radius=12,
                cursor="hand2"
            )
            card.pack(fill="x", pady=8)
            
            card.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            # Contenu
            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=20, pady=15)
            content_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            # Header
            header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            header_frame.pack(fill="x")
            header_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            icon_label = ctk.CTkLabel(
                header_frame,
                text="📂",
                font=ctk.CTkFont(size=32)
            )
            icon_label.pack(side="left", padx=(0, 15))
            icon_label.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)
            info_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            name_label = ctk.CTkLabel(
                info_frame,
                text=dept_info['name'],
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor="w"
            )
            name_label.pack(anchor="w")
            name_label.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            code_label = ctk.CTkLabel(
                info_frame,
                text=f"Code: {dept_info['code']}",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"],
                anchor="w"
            )
            code_label.pack(anchor="w")
            code_label.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            # Stats
            students_count = len(dept_info['students'])
            eligible_count = sum(1 for s in dept_info['students'] if s.get('is_eligible'))
            
            stats_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            stats_frame.pack(fill="x", pady=(10, 0))
            stats_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            self._create_stat_badge(stats_frame, "👥", f"{students_count} étudiants", self.colors["info"]).pack(side="left", padx=(0, 10))
            self._create_stat_badge(stats_frame, "✅", f"{eligible_count} éligibles", self.colors["success"]).pack(side="left")
    
    def _show_promotions_view(self):
        """Affiche les promotions et étudiants du département sélectionné"""
        if not self.nav_state['selected_department']:
            return
        
        # Titre avec barre de recherche
        title_frame = ctk.CTkFrame(self.students_main_card, fg_color="transparent")
        title_frame.pack(fill="x", padx=25, pady=(20, 15))
        
        left_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            left_frame,
            text=f"🎓 Promotions - {self.nav_state['selected_department']['name']}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            left_frame,
            text="Liste des étudiants par promotion",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(5, 0))
        
        # Barre de recherche
        search_frame = ctk.CTkFrame(self.students_main_card, fg_color=self.colors["hover"], corner_radius=8, height=44)
        search_frame.pack(fill="x", padx=25, pady=(0, 6))
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(15, 5), pady=8)
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Rechercher un étudiant (nom, email...)...",
            height=30,
            border_width=0,
            fg_color="transparent"
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(5, 15), pady=4)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(self.students_main_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(0, 10))
        
        # Regrouper par promotion
        promotions_data = {}
        dept_id = self.nav_state['selected_department']['id']
        content_parent = getattr(scroll_frame, "_scrollable_frame", scroll_frame)
        
        for student in self.students_full_data:
            if student.get('department_id') != dept_id:
                continue
            
            promo_id = student.get('promotion_id')
            promo_name = student.get('promotion_name')
            promo_year = student.get('promotion_year')
            promo_fee = student.get('promotion_fee', 0)
            promo_threshold = student.get('promotion_threshold', 0)
            
            if not promo_id or not promo_name:
                continue
            
            if promo_id not in promotions_data:
                promotions_data[promo_id] = {
                    'id': promo_id,
                    'name': promo_name,
                    'year': promo_year,
                    'fee': promo_fee,
                    'threshold': promo_threshold,
                    'students': []
                }
            promotions_data[promo_id]['students'].append(student)
        
        if not promotions_data:
            ctk.CTkLabel(
                content_parent,
                text="Aucune promotion trouvée pour ce département",
                font=ctk.CTkFont(size=14),
                text_color=self.colors["text_light"]
            ).pack(pady=50)
            return
        
        def render_students(filter_text=""):
            for widget in content_parent.winfo_children():
                widget.destroy()
            
            query = filter_text.lower().strip()
            
            # Pour chaque promotion
            for promo_id, promo_info in sorted(promotions_data.items(), key=lambda x: x[1]['name']):
                # Filtrer les étudiants
                filtered_students = []
                for student in promo_info['students']:
                    fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
                    email = student.get('email', '')
                    student_number = student.get('student_number', '')
                    
                    haystack = f"{fullname} {email} {student_number}".lower()
                    if query and query not in haystack:
                        continue
                    filtered_students.append(student)
                
                if not filtered_students:
                    continue
                
                # En-tête de promotion
                promo_header = ctk.CTkFrame(content_parent, fg_color=self.colors["primary"], corner_radius=8)
                promo_header.pack(fill="x", pady=(0 if promo_id == list(promotions_data.keys())[0] else 15, 8))
                
                promo_header_content = ctk.CTkFrame(promo_header, fg_color="transparent")
                promo_header_content.pack(fill="x", padx=15, pady=10)
                
                ctk.CTkLabel(
                    promo_header_content,
                    text=f"🎓 {promo_info['name']} ({promo_info['year']})",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=self.colors["text_white"]
                ).pack(side="left")
                
                # Stats promotion
                stats_label = ctk.CTkLabel(
                    promo_header_content,
                    text=f"👥 {len(filtered_students)} étudiant{'s' if len(filtered_students) > 1 else ''} | 💰 Frais: ${promo_info['fee']:.2f} | Seuil: ${promo_info['threshold']:.2f}",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_white"]
                )
                stats_label.pack(side="right")
                
                # Tableau des étudiants
                table_frame = ctk.CTkFrame(content_parent, fg_color=self.colors["card_bg"], corner_radius=8)
                table_frame.pack(fill="x", expand=False, pady=(0, 10))
                
                # Header du tableau
                headers = ["Photo", "Nom Complet", "Email", "💰 Payé", "Éligibilité", "Solde ($)", "Actions"]
                layout = self._get_table_layout("students_promo", len(headers))
                column_weights = layout["weights"]
                header_anchors = layout["anchors"]
                min_widths = layout["min_widths"]
                self._create_table_header(table_frame, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=8)

                # Conteneur scrollable des lignes (header fixe)
                rows_scroll = ctk.CTkScrollableFrame(
                    table_frame,
                    fg_color="transparent",
                    height=self._scaled(260),
                    scrollbar_button_color=self.colors["border"],
                    scrollbar_button_hover_color=self.colors["text_light"]
                )
                rows_scroll.pack(fill="x", padx=0, pady=(0, 8))

                self._set_scrollbar_visible(rows_scroll, False)

                rows_container = getattr(rows_scroll, "_scrollable_frame", rows_scroll)

                # Lignes des étudiants
                for index, student in enumerate(filtered_students):
                    self._render_student_row_in_promotion(rows_container, student, column_weights, row_index=index)

                rows_scroll.update_idletasks()
                table_frame.update_idletasks()
        
        # Rendu initial
        render_students()
        search_entry.bind("<KeyRelease>", lambda e: render_students(search_entry.get()))
    
    def _render_student_row_in_promotion(self, parent, student, column_weights, row_index: int = 0):
        """Rend une ligne étudiant dans la vue promotion"""
        row = ctk.CTkFrame(parent, fg_color=self.colors["hover"], corner_radius=0)
        row.grid(row=row_index, column=0, sticky="ew", pady=1, padx=0)
        parent.grid_columnconfigure(0, weight=1)
        layout = self._get_table_layout("students_promo")
        min_widths = layout["min_widths"]
        self._configure_table_columns(row, column_weights, min_widths=min_widths)
        
        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        email = student.get('email') or "-"
        photo_path = student.get('passport_photo_path')
        photo_blob = student.get('passport_photo_blob')
        amount_paid = Decimal(str(student.get('amount_paid') or 0))
        
        promotion_threshold = Decimal(str(student.get('promotion_threshold') or 0))
        promotion_fee = Decimal(str(student.get('promotion_fee') or 0))
        
        is_eligible = bool(student.get('is_eligible')) or (promotion_threshold > 0 and amount_paid >= promotion_threshold)
        remaining_amount = max(Decimal("0"), promotion_fee - amount_paid)
        
        # Photo
        self._render_photo_cell(row, 0, photo_path=photo_path, photo_blob=photo_blob, size=(35, 45))

        eligibility_text = "✅" if is_eligible else "❌"
        row_values = [
            fullname,
            email,
            f"${amount_paid:.2f}",
            eligibility_text,
            f"${remaining_amount:.2f}",
        ]
        row_colors = [
            self.colors["text_dark"],
            self.colors["text_light"],
            self.colors["success"] if amount_paid >= promotion_fee else self.colors["warning"],
            self.colors["success"] if is_eligible else self.colors["danger"],
            self.colors["text_light"],
        ]
        row_weights = ["normal", "normal", "bold", "bold", "normal"]
        row_anchors = layout["anchors"][1:6]
        row_min_widths = min_widths[1:6] if min_widths else None

        self._populate_table_row_with_offset(
            row,
            row_values,
            column_weights,
            start_col=1,
            text_colors=row_colors,
            font_weights=row_weights,
            anchors=row_anchors,
            min_widths=row_min_widths,
            padx=10,
            pady=6
        )
        
        # Actions
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.grid(row=0, column=6, sticky="ew", padx=10, pady=6)
        
        ctk.CTkButton(
            action_frame,
            text="✏️",
            width=30,
            height=24,
            fg_color=self.colors["info"],
            hover_color="#0891b2",
            command=lambda s=student: self._open_edit_student_dialog(s)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame,
            text="💰",
            width=30,
            height=24,
            fg_color=self.colors["primary"],
            hover_color="#2563eb",
            command=lambda s=student: self._open_payment_dialog(s)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame,
            text="📜",
            width=30,
            height=24,
            fg_color=self.colors["warning"],
            hover_color="#f59e0b",
            command=lambda s=student: self._open_payment_history_dialog(s)
        ).pack(side="left", padx=2)
    
    def _create_stat_badge(self, parent, icon, text, color):
        """Crée un badge de statistique"""
        badge = ctk.CTkFrame(parent, fg_color=color, corner_radius=6)
        badge.bind("<Button-1>", lambda e: None)  # Propagate click to parent
        
        content = ctk.CTkFrame(badge, fg_color="transparent")
        content.pack(padx=8, pady=4)
        content.bind("<Button-1>", lambda e: None)
        
        ctk.CTkLabel(
            content,
            text=f"{icon} {text}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack()
        
        return badge
    
    def _select_faculty(self, faculty_info):
        """Sélectionne une faculté et passe aux départements"""
        self.nav_state['level'] = 'department'
        self.nav_state['selected_faculty'] = faculty_info
        self._render_students_navigation()
    
    def _select_department(self, dept_info):
        """Sélectionne un département et passe aux promotions"""
        self.nav_state['level'] = 'promotion'
        self.nav_state['selected_department'] = dept_info
        self._render_students_navigation()
    

    def _open_add_student_dialog(self):
        """Ouvre la fenêtre d'inscription d'un nouvel étudiant (élégant, centré, responsive)"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Inscription Étudiant")
        
        # Responsive sizing: petit écran = compact, grand écran = plus grand
        if self.screen_width < 1200:
            dialog_width = min(520, max(420, int(self.screen_width * 0.45)))
            dialog_height = min(750, max(650, int(self.screen_height * 0.75)))
        else:
            dialog_width = min(600, max(520, int(self.screen_width * 0.4)))
            dialog_height = min(800, max(700, int(self.screen_height * 0.8)))
        
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        
        # Background moderne
        dialog.configure(fg_color=self.colors["main_bg"])
        
        self._animate_window_open(dialog)

        # === HEADER ÉLÉGANT ===
        header = ctk.CTkFrame(dialog, fg_color=self.colors["primary"], corner_radius=0, height=70)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            header_content,
            text="➕ Nouvel Étudiant",
            font=self._font(20, "bold"),
            text_color=self.colors["text_white"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_content,
            text="Remplissez tous les champs requis",
            font=self._font(11),
            text_color="#e5f0ff"
        ).pack(side="left", padx=(15, 0))

        # === SCROLL FORM CONTAINER ===
        form_outer = ctk.CTkFrame(dialog, fg_color="transparent")
        form_outer.pack(fill="both", expand=True, padx=20, pady=15)

        form_scroll = ctk.CTkScrollableFrame(
            form_outer,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["text_light"],
            corner_radius=8
        )
        form_scroll.pack(fill="both", expand=True)
        form_scroll.grid_columnconfigure(0, weight=1)

        # === SECTION: IDENTITÉ ===
        section_identity = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_identity.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            section_identity,
            text="👤 Informations personnelles",
            font=self._font(13, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=12, pady=(10, 8))

        identity_frame = ctk.CTkFrame(section_identity, fg_color="transparent")
        identity_frame.pack(fill="x", padx=12, pady=(0, 10))
        identity_frame.grid_columnconfigure(0, weight=1)
        identity_frame.grid_columnconfigure(1, weight=1)

        def add_labeled_entry(parent, label_text, placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(parent, text=label_text, font=self._font(11), text_color=self.colors["text_light"])
            label.grid(row=row, column=col, sticky="w", padx=5, pady=(8, 2), columnspan=col_span)
            entry = ctk.CTkEntry(
                parent,
                placeholder_text=placeholder,
                fg_color=self.colors["main_bg"],
                border_color=self.colors["border"],
                border_width=1,
                corner_radius=6,
                height=32
            )
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=5, pady=(0, 6))
            return entry

        student_number_entry = add_labeled_entry(identity_frame, "Numéro étudiant *", "STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry(identity_frame, "Prénom *", "Jean", row=0, col=1)
        lastname_entry = add_labeled_entry(identity_frame, "Nom *", "Dupont", row=2, col=0)
        email_entry = add_labeled_entry(identity_frame, "Email *", "jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry(identity_frame, "Téléphone WhatsApp *", "+243123456789", row=4, col=0, col_span=2)

        # === SECTION: ACADÉMIQUE ===
        section_academic = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_academic.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            section_academic,
            text="🎓 Informations académiques",
            font=self._font(13, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=12, pady=(10, 8))

        academic_frame = ctk.CTkFrame(section_academic, fg_color="transparent")
        academic_frame.pack(fill="x", padx=12, pady=(0, 10))
        academic_frame.grid_columnconfigure(0, weight=1)
        academic_frame.grid_columnconfigure(1, weight=1)

        # Année académique
        years = self.academic_year_service.get_years_financials()
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}

        year_entry = add_labeled_entry(academic_frame, "Année académique *", "2024-2025", row=0, col=0, col_span=2)
        
        threshold_info_label = ctk.CTkLabel(
            academic_frame,
            text="ℹ️ Sélectionnez une année pour voir le seuil financier",
            font=self._font(10),
            text_color=self.colors["text_light"]
        )
        threshold_info_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(4, 6))
        
        def update_threshold_info(*args):
            """Met à jour l'affichage du seuil lorsque l'année change"""
            selected_year_name = year_entry.get().strip()
            if selected_year_name and selected_year_name in year_map:
                year_id = year_map[selected_year_name]
                year_data = next((y for y in years if y.get("academic_year_id") == year_id), None)
                if year_data:
                    threshold = year_data.get("threshold_amount", 0) or 0
                    final_fee = year_data.get("final_fee", 0) or 0
                    threshold_info_label.configure(
                        text=f"💰 Seuil: ${threshold:,.2f} | Frais: ${final_fee:,.2f}",
                        text_color=self.colors["success"]
                    )
                else:
                    threshold_info_label.configure(
                        text="ℹ️ Sélectionnez une année pour voir le seuil financier",
                        text_color=self.colors["text_light"]
                    )
            else:
                threshold_info_label.configure(
                    text="ℹ️ Sélectionnez une année pour voir le seuil financier",
                    text_color=self.colors["text_light"]
                )
        
        year_entry.bind("<KeyRelease>", update_threshold_info)
        year_entry.bind("<FocusOut>", update_threshold_info)

        faculty_entry = add_labeled_entry(academic_frame, "Faculté *", "Informatique / INF", row=3, col=0)
        department_entry = add_labeled_entry(academic_frame, "Département *", "Génie Informatique", row=3, col=1)
        promotion_entry = add_labeled_entry(academic_frame, "Promotion *", "L3-LMD/G.I", row=5, col=0, col_span=2)

        # === SECTION: PHOTO ===
        section_photo = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_photo.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            section_photo,
            text="📸 Photo du visage (passeport)",
            font=self._font(13, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=12, pady=(10, 8))

        photo_frame = ctk.CTkFrame(section_photo, fg_color="transparent")
        photo_frame.pack(fill="x", padx=12, pady=(0, 10))
        photo_frame.grid_columnconfigure(0, weight=1)
        photo_frame.grid_columnconfigure(1, weight=0)

        photo_path_var = StringVar(value="")
        photo_entry = ctk.CTkEntry(
            photo_frame,
            textvariable=photo_path_var,
            fg_color=self.colors["main_bg"],
            border_color=self.colors["border"],
            border_width=1,
            corner_radius=6,
            height=32
        )
        photo_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        choose_btn = ctk.CTkButton(
            photo_frame,
            text="📁 Parcourir",
            width=90,
            height=32,
            fg_color=self.colors["info"],
            hover_color="#0891b2",
            corner_radius=6
        )
        choose_btn.grid(row=0, column=1)

        preview_frame = ctk.CTkFrame(section_photo, fg_color="transparent")
        preview_frame.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(
            preview_frame,
            text="Aperçu",
            font=self._font(11),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(0, 6))

        preview_image_label = ctk.CTkLabel(preview_frame, text="")
        preview_image_label.pack(anchor="w")

        guidelines = ctk.CTkLabel(
            section_photo,
            text="Fond neutre • Visage centré • Une seule personne • Bonne lumière",
            font=self._font(10),
            text_color=self.colors["text_light"]
        )
        guidelines.pack(anchor="w", padx=12, pady=(0, 10))

        def choose_photo():
            file_path = filedialog.askopenfilename(
                title="Choisir une photo",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                photo_path_var.set(file_path)
                try:
                    image = Image.open(file_path)
                    image.thumbnail((140, 180))
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    preview_image_label.configure(image=ctk_image)
                    preview_image_label.image = ctk_image
                except Exception as e:
                    logger.warning(f"Preview photo error: {e}")

        choose_btn.configure(command=choose_photo)

        # === SECTION: BOUTONS ===
        button_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        button_frame.pack(fill="x", pady=(8, 0))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        def save_student():
            student_number = student_number_entry.get().strip()
            firstname = firstname_entry.get().strip()
            lastname = lastname_entry.get().strip()
            email = email_entry.get().strip()
            phone_number = phone_entry.get().strip()
            faculty_label = faculty_entry.get().strip()
            department_label = department_entry.get().strip()
            promotion_label = promotion_entry.get().strip()
            selected_year_name = year_entry.get().strip()
            selected_year_id = year_map.get(selected_year_name) if selected_year_name else None
            photo_path = photo_path_var.get().strip()

            if not all([student_number, firstname, lastname, email, phone_number, faculty_label, department_label, promotion_label, photo_path, selected_year_name]):
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires.")
                return

            if selected_year_name and not selected_year_id:
                create_year = messagebox.askyesno(
                    "Année académique manquante",
                    f"L'année académique '{selected_year_name}' n'existe pas.\n\n"
                    "Voulez-vous la créer maintenant avec les paramètres par défaut?\n\n"
                    "• Seuil financier: $300\n"
                    "• Frais finaux: $500\n"
                    "• Validité partielle: 30 jours"
                )
                
                if create_year:
                    selected_year_id = self.academic_year_service.create_year_simple(selected_year_name)
                    if not selected_year_id:
                        messagebox.showerror("Erreur", f"Impossible de créer l'année académique '{selected_year_name}'.")
                        return
                else:
                    messagebox.showinfo("Annulé", "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.")
                    return
            
            if not selected_year_id:
                messagebox.showerror("Erreur", "Année académique requise.")
                return

            faculty_matches = self.student_service.find_faculty_by_input(faculty_label)
            if not faculty_matches:
                faculty_id = self.student_service.create_faculty(faculty_label)
                if not faculty_id:
                    messagebox.showerror("Erreur", "Impossible de créer la faculté.")
                    return
            else:
                faculty_id = faculty_matches[0]["id"]

            department_matches = self.student_service.find_department_by_input(department_label, faculty_id)
            if not department_matches:
                department_id = self.student_service.create_department(department_label, faculty_id)
                if not department_id:
                    messagebox.showerror("Erreur", "Impossible de créer le département.")
                    return
            else:
                department_id = department_matches[0]["id"]

            promotion_matches = self.student_service.find_promotion_by_input(promotion_label, department_id)
            if not promotion_matches:
                promotion_id = self.student_service.create_promotion(promotion_label, department_id)
                if not promotion_id:
                    messagebox.showerror("Erreur", "Impossible de créer la promotion.")
                    return
            else:
                promotion_id = promotion_matches[0]["id"]

            year_data = next((y for y in years if y.get("academic_year_id") == selected_year_id), None)
            threshold_required = None
            final_fee_value = None
            
            if year_data:
                threshold_required = Decimal(str(year_data.get("threshold_amount", 0)))
                final_fee_value = Decimal(str(year_data.get("final_fee", threshold_required)))
            else:
                messagebox.showerror("Erreur", "Impossible de récupérer les informations financières de l'année académique.")
                return

            encoding = None
            if self.face_service.is_available():
                try:
                    encoding = self.face_service.register_face(photo_path, 1)
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur photo: {e}")
                    return

                if encoding is None:
                    messagebox.showerror("Erreur", "Aucun visage détecté (ou plusieurs visages). Utilisez une photo passeport.")
                    return

                quality_ok, quality_msg = self.face_service.validate_passport_photo(photo_path)
                if not quality_ok:
                    messagebox.showerror("Qualité photo insuffisante", quality_msg)
                    return
            else:
                messagebox.showwarning(
                    "Info",
                    "Reconnaissance faciale non disponible. La photo passeport sera utilisée plus tard pour la validation."
                )

            storage_dir = os.path.join(os.getcwd(), "storage", "student_photos")
            os.makedirs(storage_dir, exist_ok=True)
            ext = os.path.splitext(photo_path)[1].lower()
            stored_photo_name = f"{student_number}{ext}"
            stored_photo_path = os.path.join(storage_dir, stored_photo_name)
            try:
                shutil.copy2(photo_path, stored_photo_path)
                with open(stored_photo_path, "rb") as f:
                    photo_blob = f.read()
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder la photo: {e}")
                return

            face_bytes = encoding.tobytes() if encoding is not None else None
            student = Student(
                student_number=student_number,
                firstname=firstname,
                lastname=lastname,
                email=email,
                phone_number=phone_number,
                promotion_id=promotion_id,
                passport_photo_path=stored_photo_path,
                passport_photo_blob=photo_blob,
                academic_year_id=selected_year_id
            )

            student_id = self.auth_service.register_student_with_face(student, None, face_bytes)
            if not student_id:
                messagebox.showerror("Erreur", "Échec d'enregistrement de l'étudiant.")
                return

            finance_ok = self.finance_service.create_finance_profile(student_id, threshold_required, selected_year_id)
            if not finance_ok:
                messagebox.showwarning("Attention", "Profil financier non créé.")

            try:
                self.notification_service.send_welcome_notification(
                    student_email=email,
                    student_phone=phone_number,
                    student_name=f"{firstname} {lastname}",
                    student_number=student_number,
                    threshold_required=float(threshold_required) if threshold_required else 0.0,
                    final_fee=float(final_fee_value) if final_fee_value else 0.0
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome notification: {e}")

            messagebox.showinfo("Succès", "Étudiant enregistré avec succès.")
            dialog.destroy()
            self._show_students()

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Annuler",
            fg_color=self.colors["border"],
            text_color=self.colors["text_dark"],
            hover_color=self.colors["hover"],
            height=40,
            corner_radius=8,
            command=dialog.destroy
        )
        cancel_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        save_btn = ctk.CTkButton(
            button_frame,
            text="✓ Valider",
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=40,
            corner_radius=8,
            command=save_student
        )
        save_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _open_edit_student_dialog(self, student: dict):
        """Ouvre la fenêtre de modification complète d'un étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Modifier étudiant")
        dialog_width = min(620, max(520, int(self.screen_width * 0.5)))
        dialog_height = min(840, max(720, int(self.screen_height * 0.82)))
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        self._animate_window_open(dialog)

        student_id = student.get("id")
        details = self.student_service.get_student_with_academics(student_id) or student

        ctk.CTkLabel(
            dialog,
            text="✏️ Modifier Étudiant",
            font=self._font(20, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(self._scaled(18), self._scaled(8)))

        form_container = ctk.CTkFrame(dialog, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=self._scaled(18), pady=self._scaled(10))

        form = ctk.CTkScrollableFrame(
            form_container,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["text_light"]
        )
        form.pack(fill="both", expand=True, padx=5, pady=5)

        fields_frame = ctk.CTkFrame(form, fg_color="transparent")
        fields_frame.pack(fill="x", padx=5, pady=5)
        fields_frame.grid_columnconfigure(0, weight=1)
        fields_frame.grid_columnconfigure(1, weight=1)

        def add_labeled_entry(label_text, value="", placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(fields_frame, text=label_text, font=self._font(12))
            label.grid(row=row, column=col, sticky="w", padx=5, pady=(8, 4))
            entry = ctk.CTkEntry(fields_frame, placeholder_text=placeholder)
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=5)
            if value:
                entry.insert(0, value)
            return entry

        student_number_entry = add_labeled_entry("Numéro étudiant", details.get("student_number", ""), "Ex: STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry("Prénom", details.get("firstname", ""), "Ex: Jean", row=0, col=1)
        lastname_entry = add_labeled_entry("Nom", details.get("lastname", ""), "Ex: Dupont", row=2, col=0)
        email_entry = add_labeled_entry("Email", details.get("email", ""), "Ex: jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry("Téléphone WhatsApp", details.get("phone_number", ""), "Ex: +243123456789", row=4, col=0)

        # Année académique
        years = self.academic_year_service.get_years()
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}
        current_year_name = details.get("academic_year_name") or ""

        ctk.CTkLabel(fields_frame, text="Année académique", font=self._font(12)).grid(row=6, column=0, sticky="w", padx=5, pady=(8, 4))
        year_entry = ctk.CTkEntry(fields_frame, placeholder_text="Ex: 2024-2025")
        if current_year_name:
            year_entry.insert(0, current_year_name)
        year_entry.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5)

        faculty_display = details.get("faculty_name") or ""
        if details.get("faculty_code"):
            faculty_display = f"{faculty_display} / {details.get('faculty_code')}".strip()
        department_display = details.get("department_name") or ""
        if details.get("department_code"):
            department_display = f"{department_display} / {details.get('department_code')}".strip()
        promotion_display = details.get("promotion_name") or ""

        faculty_entry = add_labeled_entry("Faculté", faculty_display, "Ex: Informatique / INF", row=8, col=0)
        department_entry = add_labeled_entry("Département", department_display, "Ex: Génie Informatique / G.I", row=8, col=1)
        promotion_entry = add_labeled_entry("Promotion", promotion_display, "Ex: L3-LMD/G.I", row=10, col=0, col_span=2)

        photo_row = ctk.CTkFrame(form, fg_color="transparent")
        photo_row.pack(fill="x", pady=(10, 2))
        photo_row.grid_columnconfigure(0, weight=0)
        photo_row.grid_columnconfigure(1, weight=1)
        photo_row.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(photo_row, text="Photo du visage (passeport)", font=self._font(12)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        photo_path_var = StringVar(value="")
        photo_entry = ctk.CTkEntry(photo_row, textvariable=photo_path_var)
        photo_entry.grid(row=0, column=1, sticky="ew")

        preview_frame = ctk.CTkFrame(form, fg_color="transparent")
        preview_frame.pack(fill="x", pady=(8, 4))
        preview_label = ctk.CTkLabel(
            preview_frame,
            text="Aperçu photo",
            font=self._font(11),
            text_color=self.colors["text_light"]
        )
        preview_label.pack(anchor="w")

        preview_image_label = ctk.CTkLabel(preview_frame, text="")
        preview_image_label.pack(anchor="w", pady=(6, 0))

        existing_photo_path = details.get("passport_photo_path")
        existing_photo_blob = details.get("passport_photo_blob")
        existing_image = self._get_cached_photo(existing_photo_path, existing_photo_blob, size=(140, 180))
        if existing_image:
            preview_image_label.configure(image=existing_image)
            preview_image_label.image = existing_image

        def choose_photo():
            file_path = filedialog.askopenfilename(
                title="Choisir une photo",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                photo_path_var.set(file_path)
                try:
                    image = Image.open(file_path)
                    image.thumbnail((140, 180))
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    preview_image_label.configure(image=ctk_image)
                    preview_image_label.image = ctk_image
                except Exception as e:
                    logger.warning(f"Preview photo error: {e}")

        choose_btn = ctk.CTkButton(photo_row, text="Parcourir", width=110, command=choose_photo)
        choose_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        ctk.CTkLabel(
            form,
            text="Fond neutre, visage centré, une seule personne, bonne lumière.",
            font=self._font(10),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(0, 6))

        def save_changes():
            student_number = student_number_entry.get().strip()
            firstname = firstname_entry.get().strip()
            lastname = lastname_entry.get().strip()
            email = email_entry.get().strip()
            phone_number = phone_entry.get().strip()
            faculty_label = faculty_entry.get().strip()
            department_label = department_entry.get().strip()
            promotion_label = promotion_entry.get().strip()
            selected_year_name = year_entry.get().strip()
            selected_year_id = year_map.get(selected_year_name) if selected_year_name else None
            photo_path = photo_path_var.get().strip()

            if not all([student_number, firstname, lastname, email, phone_number, faculty_label, department_label, promotion_label, selected_year_name]):
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires.")
                return

            if selected_year_name and not selected_year_id:
                # L'année n'existe pas - proposer de la créer
                create_year = messagebox.askyesno(
                    "Année académique manquante",
                    f"L'année académique '{selected_year_name}' n'existe pas.\n\n"
                    "Voulez-vous la créer maintenant avec les paramètres par défaut?\n\n"
                    "• Seuil financier: $300\n"
                    "• Frais finaux: $500\n"
                    "• Validité partielle: 30 jours"
                )
                
                if create_year:
                    selected_year_id = self.academic_year_service.create_year_simple(selected_year_name)
                    if not selected_year_id:
                        messagebox.showerror("Erreur", f"Impossible de créer l'année académique '{selected_year_name}'.")
                        return
                else:
                    messagebox.showinfo("Annulé", "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.")
                    return

            faculty_matches = self.student_service.find_faculty_by_input(faculty_label)
            if not faculty_matches:
                faculty_id = self.student_service.create_faculty(faculty_label)
                if not faculty_id:
                    messagebox.showerror("Erreur", "Impossible de créer la faculté.")
                    return
            else:
                faculty_id = faculty_matches[0]["id"]

            department_matches = self.student_service.find_department_by_input(department_label, faculty_id)
            if not department_matches:
                department_id = self.student_service.create_department(department_label, faculty_id)
                if not department_id:
                    messagebox.showerror("Erreur", "Impossible de créer le département.")
                    return
            else:
                department_id = department_matches[0]["id"]

            promotion_matches = self.student_service.find_promotion_by_input(promotion_label, department_id)
            if not promotion_matches:
                promotion_id = self.student_service.create_promotion(promotion_label, department_id)
                if not promotion_id:
                    messagebox.showerror("Erreur", "Impossible de créer la promotion.")
                    return
            else:
                promotion_id = promotion_matches[0]["id"]

            update_data = {
                "student_number": student_number,
                "firstname": firstname,
                "lastname": lastname,
                "email": email,
                "phone_number": phone_number,
                "promotion_id": promotion_id,
                "academic_year_id": selected_year_id,
            }

            if photo_path:
                storage_dir = os.path.join(os.getcwd(), "storage", "student_photos")
                os.makedirs(storage_dir, exist_ok=True)
                ext = os.path.splitext(photo_path)[1].lower()
                stored_photo_name = f"{student_number}{ext}"
                stored_photo_path = os.path.join(storage_dir, stored_photo_name)
                try:
                    shutil.copy2(photo_path, stored_photo_path)
                    with open(stored_photo_path, "rb") as f:
                        photo_blob = f.read()
                    update_data["passport_photo_path"] = stored_photo_path
                    update_data["passport_photo_blob"] = photo_blob
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de sauvegarder la photo: {e}")
                    return

            logger.debug(f"Updating student {student_id} with data: {update_data}")
            if self.student_service.update_student(student_id, update_data):
                messagebox.showinfo("Succès", "Étudiant modifié avec succès.")
                dialog.destroy()
                self._show_students()
            else:
                messagebox.showerror("Erreur", "Échec de la modification. Consultez les logs pour plus de détails.")

        button_row = ctk.CTkFrame(form, fg_color="transparent")
        button_row.pack(fill="x", pady=(10, 16))

        save_btn = ctk.CTkButton(
            button_row,
            text="Enregistrer",
            fg_color=self.colors["success"],
            hover_color=self.colors["primary"],
            height=self._scaled(36),
            command=save_changes
        )
        save_btn.pack(fill="x")

    def _open_payment_dialog(self, student: dict):
        """Ouvre une fenêtre pour enregistrer un paiement étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Enregistrer un paiement")
        dialog_width = min(460, max(360, int(self.screen_width * 0.35)))
        dialog_height = min(320, max(240, int(self.screen_height * 0.35)))
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        self._animate_window_open(dialog)

        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        student_number = student.get("student_number", "-")
        student_id = student.get("id")

        ctk.CTkLabel(
            dialog,
            text="💳 Enregistrer un paiement",
            font=self._font(18, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            dialog,
            text=f"{fullname} ({student_number})",
            font=self._font(12),
            text_color=self.colors["text_light"]
        ).pack(pady=(0, 10))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(form, text="Montant payé ($)", font=self._font(12)).pack(anchor="w")
        amount_entry = ctk.CTkEntry(form, placeholder_text="Ex: 50")
        amount_entry.pack(fill="x", pady=(6, 10))

        # Conteneur pour l'indicateur de chargement (caché initialement)
        loading_container = ctk.CTkFrame(form, fg_color="transparent")
        loading_container.pack(anchor="w", pady=(0, 6))
        
        loading_indicator = LoadingIndicator(loading_container, text="Traitement du paiement...")
        loading_indicator.pack(fill="x")

        def save_payment():
            amount_text = amount_entry.get().strip().replace(",", ".")
            if not amount_text:
                messagebox.showerror("Erreur", "Veuillez saisir un montant.")
                return
            try:
                amount_usd = Decimal(amount_text)
                if amount_usd <= 0:
                    messagebox.showerror("Erreur", "Le montant doit être supérieur à 0.")
                    return

                finance = self.finance_service.get_student_finance(student_id)
                if not finance:
                    self.finance_service.create_finance_profile(student_id, None, student.get("academic_year_id"))
                    finance = self.finance_service.get_student_finance(student_id)

                if finance:
                    final_fee = finance.get("final_fee")
                    if final_fee is None and finance.get("academic_year_id"):
                        year = self.academic_year_service.get_year_by_id(finance.get("academic_year_id"))
                        if year:
                            final_fee = year.get("final_fee")
                    final_fee = Decimal(str(final_fee or finance.get("threshold_required") or 0))
                    current_paid = Decimal(str(finance.get("amount_paid") or 0))
                    if final_fee > 0 and (current_paid + amount_usd) > final_fee:
                        remaining = final_fee - current_paid
                        if remaining < 0:
                            remaining = Decimal("0")
                        messagebox.showerror(
                            "Erreur",
                            f"Paiement refusé. Montant restant: ${remaining:.2f}."
                        )
                        return

                save_btn.configure(state="disabled")
                amount_entry.configure(state="disabled")
                loading_indicator.start("Traitement du paiement...")

                def worker():
                    success = False
                    error_msg = None
                    try:
                        success = self.finance_service.record_payment(student_id, amount_usd)
                    except Exception as ex:
                        error_msg = str(ex)

                    def finish():
                        loading_indicator.stop()
                        save_btn.configure(state="normal")
                        amount_entry.configure(state="normal")
                        if success:
                            messagebox.showinfo("Succès", "Paiement enregistré avec succès.")
                            dialog.destroy()
                            self._render_current_view()
                        else:
                            if error_msg:
                                messagebox.showerror("Erreur", f"Échec de l'enregistrement du paiement: {error_msg}")
                            else:
                                messagebox.showerror("Erreur", "Échec de l'enregistrement du paiement.")

                    self.after(0, finish)

                threading.Thread(target=worker, daemon=True).start()
            except Exception:
                messagebox.showerror("Erreur", "Montant invalide.")

        save_btn = ctk.CTkButton(
            dialog,
            text="Enregistrer",
            fg_color=self.colors["success"],
            hover_color=self.colors["primary"],
            height=self._scaled(36),
            command=save_payment
        )
        save_btn.pack(fill="x", padx=20, pady=(5, 15))

    def _open_payment_history_dialog(self, student: dict):
        """Ouvre la fenêtre d'historique de paiements par étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Historique des paiements")
        dialog_width = min(720, max(560, int(self.screen_width * 0.6)))
        dialog_height = min(600, max(420, int(self.screen_height * 0.7)))
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        self._animate_window_open(dialog)

        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        student_number = student.get("student_number", "-")
        student_id = student.get("id")

        ctk.CTkLabel(
            dialog,
            text="🧾 Historique des paiements",
            font=self._font(18, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            dialog,
            text=f"{fullname} ({student_number})",
            font=self._font(12),
            text_color=self.colors["text_light"]
        ).pack(pady=(0, 10))

        access_code = self.finance_service.get_latest_access_code(student_id)
        if access_code:
            code_text = f"Code actuel: {access_code.get('access_code')} ({access_code.get('access_type')})"
        else:
            code_text = "Code actuel: Aucun code généré"

        ctk.CTkLabel(
            dialog,
            text=code_text,
            font=self._font(12, "bold"),
            text_color=self.colors["info"] if access_code else self.colors["text_light"]
        ).pack(pady=(0, 12))

        table = ctk.CTkFrame(dialog, fg_color=self.colors["hover"], corner_radius=8)
        table.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        headers = ["Date", "Montant ($)", "Méthode"]
        layout = self._get_table_layout("payment_history", len(headers))
        weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table, headers, weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=6)

        scroll = ctk.CTkScrollableFrame(table, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        history = self.finance_service.get_student_payment_history(student_id)
        if not history:
            ctk.CTkLabel(
                scroll,
                text="Aucun paiement enregistré.",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        cumulative = Decimal("0")
        layout = self._get_table_layout("payment_history")
        min_widths = layout["min_widths"]
        for item in history:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)
            created_at = item.get("created_at")
            date_text = created_at.strftime("%d/%m/%Y %H:%M") if hasattr(created_at, "strftime") else str(created_at)
            amount_value = Decimal(str(item.get('amount_paid_usd') or 0))
            cumulative += amount_value
            row_values = [
                date_text,
                f"{amount_value:.2f}\nCumul: {cumulative:.2f}",
                item.get("payment_method") or "-",
            ]
            self._populate_table_row(
                row,
                row_values,
                weights,
                text_colors=[self.colors["text_dark"]] * 3,
                font_sizes=[10] * 3,
                anchors=["w", "e", "center"],
                min_widths=min_widths,
                padx=10,
                pady=4
            )

    def _refresh_esp32_status(self):
        """Met à jour le statut ESP32 sans bloquer l'UI"""
        if not self._esp32_status_label:
            return

        def worker():
            status = self.esp32_service.check_status()
            self.after(0, lambda: self._update_esp32_status_label(status))

        threading.Thread(target=worker, daemon=True).start()
        self.after(self.esp32_service.refresh_interval_ms, self._refresh_esp32_status)

    def _update_esp32_status_label(self, status):
        if not self._esp32_status_label:
            return
        try:
            if not self._esp32_status_label.winfo_exists():
                return
            self._esp32_status_label.configure(text=f"Statut: {status.text}", text_color=status.color)
        except Exception:
            return
    
    def _show_finance(self):
        """Affiche la page Finances"""
        self.current_view = "finance"
        self._clear_content()
        self._update_nav_buttons("finance")
        self.title_label.configure(text=self._t("finance_title", "Gestion Financière"))
        self.subtitle_label.configure(text=self._t("finance_subtitle", "Suivi des paiements et seuils"))
        
        # === HEADER ===
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="💰 Gestion Financière",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # === KPIs FINANCIERS ===
        kpi_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        
        revenue = self.dashboard_service.get_revenue_collected()
        payment_status = self.dashboard_service.get_students_by_payment_status()
        if not payment_status:
            payment_status = {"never_paid": 0, "partial_paid": 0, "eligible": 0}
        
        kpis = [
            (self._format_usd(revenue), "Revenus Totaux", "green"),
            (f"{payment_status['eligible']}", "Paiements Complètes", "blue"),
            (f"{payment_status['partial_paid']}", "Paiements Partiels", "orange"),
            (f"{payment_status['never_paid']}", "Non Payés", "red"),
        ]
        
        # Responsive: layout horizontal ou vertical selon écran
        is_small_screen = self.screen_width < 1000
        kpi_layout_side = "top" if is_small_screen else "left"  # Vertical si petit écran
        
        for i, (value, label, color_key) in enumerate(kpis):
            color_map = {"green": self.colors["success"], "blue": self.colors["info"], "orange": self.colors["warning"], "red": self.colors["danger"]}
            kpi_card = ctk.CTkFrame(kpi_frame, fg_color=color_map[color_key], corner_radius=8, height=80 if is_small_screen else 100)
            kpi_card.pack(side=kpi_layout_side, fill="both", expand=True, padx=(0 if i == 0 else 3), pady=(0 if i == 0 else 3))
            kpi_card.pack_propagate(False)
            self._make_card_clickable(kpi_card, self._show_finance)
            
            # Adaptive font sizes
            value_font_size = 16 if is_small_screen else 20
            label_font_size = 8 if is_small_screen else 10
            
            ctk.CTkLabel(kpi_card, text=value, font=ctk.CTkFont(size=value_font_size, weight="bold"), text_color=self.colors["text_white"]).pack(expand=True)
            ctk.CTkLabel(kpi_card, text=label, font=ctk.CTkFont(size=label_font_size), text_color=self.colors["text_white"]).pack()
        
        # === TABLEAU PAIEMENTS ===
        table_card = self._create_card(self.content_frame)
        table_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            table_card,
            text="📊 Historique des Paiements",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Tableau header
        headers = ["Photo", "Étudiant", "ID", "Montant Payé ($)", "Seuil Requis ($)", "Statut", "Date"]
        layout = self._get_table_layout("finance_payments", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table_card, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=10)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        payments = self.dashboard_service.get_students_finance_overview()
        if not payments:
            ctk.CTkLabel(
                scroll_frame,
                text="Aucun paiement trouvé.",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        for payment in payments:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=4)

            self._configure_table_columns(row, column_weights, min_widths=min_widths)

            fullname = f"{payment.get('firstname', '')} {payment.get('lastname', '')}".strip()
            student_number = payment.get('student_number', '-')
            amount_paid = Decimal(str(payment.get('amount_paid') or 0))
            threshold_required = Decimal(str(payment.get('threshold_required') or 0))
            is_eligible = bool(payment.get('is_eligible')) or (threshold_required > 0 and amount_paid >= threshold_required)
            last_date = payment.get('last_payment_date') or "-"

            if amount_paid <= 0:
                status = "Non payé"
            elif threshold_required > 0 and amount_paid < threshold_required:
                status = "Partiel"
            else:
                status = "Payé"

            color = self.colors["success"] if status == "Payé" else (self.colors["warning"] if status == "Partiel" else self.colors["danger"])
            self._render_photo_cell(
                row,
                0,
                photo_path=payment.get('passport_photo_path'),
                photo_blob=payment.get('passport_photo_blob'),
                size=(36, 44)
            )
            row_values = [
                fullname,
                student_number,
                self._format_usd(amount_paid),
                self._format_usd(threshold_required),
                status,
                str(last_date)
            ]
            row_colors = [self.colors["text_dark"], self.colors["text_light"], self.colors["success"], self.colors["text_light"], color, self.colors["text_light"]]
            row_weights = ["normal", "normal", "bold", "normal", "normal", "normal"]
            layout = self._get_table_layout("finance_payments")
            row_anchors = layout["anchors"][1:]
            row_min_widths = min_widths[1:] if min_widths else None
            self._populate_table_row_with_offset(
                row,
                row_values,
                column_weights,
                start_col=1,
                text_colors=row_colors,
                font_weights=row_weights,
                anchors=row_anchors,
                min_widths=row_min_widths
            )
    
    def _show_access_logs(self):
        """Affiche les logs d'accès"""
        self.current_view = "access_logs"
        self._clear_content()
        self._update_nav_buttons("access_logs")
        self.title_label.configure(text=self._t("access_logs_title", "Historique d'Accès"))
        self.subtitle_label.configure(text=self._t("access_logs_subtitle", "Suivi des tentatives d'accès"))
        
        # === HEADER ===
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="📋 Historique d'Accès",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # === STATISTIQUES RAPIDES ===
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        
        granted = self.dashboard_service.get_access_granted()
        denied = self.dashboard_service.get_access_denied()
        total_attempts = granted + denied
        
        stat_items = [
            (str(granted), "Accès Accordés", self.colors["success"]),
            (str(denied), "Accès Refusés", self.colors["danger"]),
            (str(total_attempts), "Total Tentatives", self.colors["info"]),
        ]
        
        # Responsive: layout horizontal ou vertical selon écran
        is_small_screen = self.screen_width < 1000
        stat_layout_side = "top" if is_small_screen else "left"
        
        for i, (value, label, color) in enumerate(stat_items):
            stat_card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=8, height=70 if is_small_screen else 80)
            stat_card.pack(side=stat_layout_side, fill="both", expand=True, padx=(0 if i == 0 else 3), pady=(0 if i == 0 else 3))
            stat_card.pack_propagate(False)
            self._make_card_clickable(stat_card, self._show_access_logs)
            
            value_font = 15 if is_small_screen else 18
            label_font = 9 if is_small_screen else 11
            
            ctk.CTkLabel(stat_card, text=value, font=ctk.CTkFont(size=value_font, weight="bold"), text_color=self.colors["text_white"]).pack(expand=True)
            ctk.CTkLabel(stat_card, text=label, font=ctk.CTkFont(size=label_font), text_color=self.colors["text_white"]).pack()
        
        # === TABLEAU LOGS ===
        table_card = self._create_card(self.content_frame)
        table_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            table_card,
            text="📊 Détail des Tentatives d'Accès",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Tableau header
        headers = ["Photo", "Étudiant", "ID", "Point d'Accès", "Résultat", "Mot de passe", "Visage", "Finance", "Heure"]
        layout = self._get_table_layout("access_logs", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table_card, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=8, pady=10)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        logs = self.dashboard_service.get_access_logs_with_students()
        if not logs:
            ctk.CTkLabel(
                scroll_frame,
                text="Aucun log trouvé.",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        for log in logs:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=3)

            self._configure_table_columns(row, column_weights, min_widths=min_widths)

            status = str(log.get('status') or '').upper()
            result_symbol = "✅" if status == "GRANTED" else "❌"
            result_color = self.colors["success"] if status == "GRANTED" else self.colors["danger"]

            password_ok = "✓" if log.get('password_validated') else "✗"
            face_ok = "✓" if log.get('face_validated') else "✗"
            finance_ok = "✓" if log.get('finance_validated') else "✗"

            created_at = log.get('created_at')
            time_str = created_at.strftime("%H:%M") if hasattr(created_at, 'strftime') else str(created_at)[-8:-3]

            display_row = [
                f"{log.get('firstname', '')} {log.get('lastname', '')}".strip(),
                log.get('student_number', '-'),
                log.get('access_point') or "-",
                result_symbol,
                password_ok,
                face_ok,
                finance_ok,
                time_str
            ]

            cell_colors = [
                self.colors["text_dark"],
                self.colors["text_light"],
                self.colors["text_light"],
                result_color,
                self.colors["success"] if password_ok == "✓" else self.colors["danger"],
                self.colors["success"] if face_ok == "✓" else self.colors["danger"],
                self.colors["success"] if finance_ok == "✓" else self.colors["danger"],
                self.colors["text_light"],
            ]
            row_weights = ["normal", "normal", "normal", "bold", "normal", "normal", "normal", "normal"]
            layout = self._get_table_layout("access_logs")
            row_anchors = layout["anchors"][1:]
            row_min_widths = min_widths[1:] if min_widths else None
            self._render_photo_cell(
                row,
                0,
                photo_path=log.get('passport_photo_path'),
                photo_blob=log.get('passport_photo_blob'),
                size=(36, 44)
            )
            self._populate_table_row_with_offset(
                row,
                display_row,
                column_weights,
                start_col=1,
                text_colors=cell_colors,
                font_sizes=[9, 9, 9, 9, 10, 10, 10, 9],
                font_weights=row_weights,
                anchors=row_anchors,
                min_widths=row_min_widths,
                padx=8,
                pady=6
            )
    
    def _show_reports(self):
        """Affiche les rapports"""
        self.current_view = "reports"
        self._clear_content()
        self._update_nav_buttons("reports")
        self.title_label.configure(text=self._t("reports_title", "Rapports et Statistiques"))
        self.subtitle_label.configure(text=self._t("reports_subtitle", "Analyse par faculté et performance"))
        
        # === HEADER ===
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="📈 Rapports et Statistiques",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # === FILTRES ===
        filter_frame = ctk.CTkFrame(self.content_frame, fg_color=self.colors["hover"], corner_radius=8)
        filter_frame.pack(fill="x", pady=(0, 20), padx=20)
        self._make_card_clickable(filter_frame, self._show_reports)
        
        ctk.CTkLabel(
            filter_frame,
            text="🔍 Filtrer par:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(15, 20), pady=10)
        
        faculties = ["Toutes", "Informatique", "Gestion", "Sciences", "Droit"]
        faculty_combo = ctk.CTkComboBox(filter_frame, values=faculties, width=150, height=30)
        faculty_combo.set("Toutes")
        faculty_combo.pack(side="left", padx=10, pady=10)
        
        # === RAPPORTS PAR FACULTÉ ===
        report_card = self._create_card(self.content_frame)
        report_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            report_card,
            text="📊 Statistiques par Faculté",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Tableau header
        headers = ["Photo", "Faculté", "Département", "Total Étudiants", "Éligibles", "% Éligibilité", "Revenus"]
        layout = self._get_table_layout("reports_faculty", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(report_card, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=10)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(report_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        faculties_data = self.dashboard_service.get_faculty_stats_with_photos()
        if not faculties_data:
            ctk.CTkLabel(
                scroll_frame,
                text="Aucune statistique disponible.",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        for faculty in faculties_data:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=4)

            self._configure_table_columns(row, column_weights, min_widths=min_widths)
            total = int(faculty.get('total_students') or 0)
            eligible = int(faculty.get('eligible_students') or 0)
            percentage = (eligible / total * 100) if total else 0
            revenue = Decimal(str(faculty.get('revenue') or 0))

            self._render_photo_cell(
                row,
                0,
                photo_path=faculty.get('passport_photo_path'),
                photo_blob=faculty.get('passport_photo_blob'),
                size=(36, 44)
            )
            row_values = [
                faculty.get('faculty_name') or "-",
                faculty.get('department_name') or "-",
                str(total),
                str(eligible),
                f"{percentage:.1f}%",
                self._format_usd(revenue)
            ]
            row_colors = [
                self.colors["text_dark"],
                self.colors["text_light"],
                self.colors["text_dark"],
                self.colors["success"],
                self.colors["primary"],
                self.colors["warning"],
            ]
            row_weights = ["bold", "normal", "normal", "bold", "bold", "normal"]
            layout = self._get_table_layout("reports_faculty")
            row_anchors = layout["anchors"][1:]
            row_min_widths = min_widths[1:] if min_widths else None
            self._populate_table_row_with_offset(
                row,
                row_values,
                column_weights,
                start_col=1,
                text_colors=row_colors,
                font_weights=row_weights,
                anchors=row_anchors,
                min_widths=row_min_widths
            )
    
    def _show_academic_years(self):
        """Affiche la gestion des années académiques"""
        self.current_view = "academic_years"
        self._clear_content()
        self._update_nav_buttons("academic_years")
        self.title_label.configure(text=self._t("academic_years_title", "Années Académiques"))
        self.subtitle_label.configure(text=self._t("academic_years_subtitle", "Gestion des seuils financiers et périodes d'examens"))
        active_year = self.academic_year_service.get_active_year()
        
        # === Section: Frais & Seuils par Faculté → Promotion ===
        promo_card = self._create_card(self.content_frame)
        promo_card.pack(fill="both", expand=True, pady=(0, 20))

        ctk.CTkLabel(
            promo_card,
            text="🎓 Frais & Seuils par Faculté → Promotion",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 10))

        # Filtres faculté
        filter_row = ctk.CTkFrame(promo_card, fg_color="transparent")
        filter_row.pack(fill="x", padx=25, pady=(0, 10))

        ctk.CTkLabel(
            filter_row,
            text="🏛️ Faculté:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(0, 10))

        promotions = self.student_service.get_promotions_with_fees()
        faculty_names = sorted({p.get("faculty_name") for p in promotions if p.get("faculty_name")})
        faculty_filter = ctk.CTkComboBox(
            filter_row,
            values=["Toutes Facultés"] + faculty_names,
            width=220,
            height=32
        )
        faculty_filter.set("Toutes Facultés")
        faculty_filter.pack(side="left")

        promo_headers = ["Faculté", "Promotion", "Département", "Année", "Frais ($)", "Seuil ($)", "Action"]
        layout = self._get_table_layout("academic_promos", len(promo_headers))
        promo_weights = layout["weights"]
        promo_anchors = layout["anchors"]
        promo_min_widths = layout["min_widths"]
        self._create_table_header(promo_card, promo_headers, promo_weights, anchors=promo_anchors, min_widths=promo_min_widths, padx=10, pady=10)

        promo_scroll = ctk.CTkScrollableFrame(promo_card, fg_color="transparent")
        promo_scroll.pack(fill="both", expand=True, padx=25, pady=(15, 20))

        def render_promotions():
            for widget in promo_scroll.winfo_children():
                widget.destroy()

            selected_faculty = faculty_filter.get()
            filtered_promos = promotions
            if selected_faculty != "Toutes Facultés":
                filtered_promos = [p for p in promotions if p.get("faculty_name") == selected_faculty]

            if not filtered_promos:
                ctk.CTkLabel(
                    promo_scroll,
                    text="Aucune promotion trouvée pour cette faculté.",
                    font=ctk.CTkFont(size=12),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
                return

            for promo in filtered_promos:
                row = ctk.CTkFrame(promo_scroll, fg_color=self.colors["hover"], corner_radius=6)
                row.pack(fill="x", pady=4)
                self._configure_table_columns(row, promo_weights, min_widths=promo_min_widths)

                fee_value = promo.get('fee_usd') or 0
                threshold_value = promo.get('threshold_amount') or 0

                ctk.CTkLabel(
                    row,
                    text=promo.get('faculty_name') or "-",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_light"],
                    anchor="center"
                ).grid(row=0, column=0, sticky="ew", padx=10, pady=6)

                ctk.CTkLabel(
                    row,
                    text=promo.get('name') or "-",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_dark"],
                    anchor="center"
                ).grid(row=0, column=1, sticky="ew", padx=10, pady=6)

                ctk.CTkLabel(
                    row,
                    text=promo.get('department_name') or "-",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_light"],
                    anchor="center"
                ).grid(row=0, column=2, sticky="ew", padx=10, pady=6)

                ctk.CTkLabel(
                    row,
                    text=str(promo.get('year') or "-"),
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_dark"],
                    anchor="center"
                ).grid(row=0, column=3, sticky="ew", padx=10, pady=6)

                fee_entry = ctk.CTkEntry(row, width=140, justify="center")
                fee_entry.insert(0, f"{Decimal(str(fee_value)):.2f}")
                fee_entry.grid(row=0, column=4, sticky="ew", padx=10, pady=6)

                threshold_entry = ctk.CTkEntry(row, width=140, justify="center")
                threshold_entry.insert(0, f"{Decimal(str(threshold_value)):.2f}")
                threshold_entry.grid(row=0, column=5, sticky="ew", padx=10, pady=6)

                def make_save(promotion_id, fee_widget, threshold_widget, save_btn_ref):
                    def _save():
                        try:
                            fee_val = Decimal(fee_widget.get().strip())
                            threshold_val = Decimal(threshold_widget.get().strip())
                            if fee_val < 0 or threshold_val < 0:
                                raise ValueError
                            if threshold_val > fee_val:
                                messagebox.showerror(
                                    "Erreur de Validation",
                                    "Le seuil ne peut pas dépasser les frais académiques."
                                )
                                return
                            
                            # Afficher le loading dialog
                            loading_dialog, loading_indicator = self._show_loading_dialog(
                                "Mise à jour des frais et notifications..."
                            )
                            save_btn_ref.configure(state="disabled")
                            fee_widget.configure(state="disabled")
                            threshold_widget.configure(state="disabled")
                            
                            def worker():
                                success = False
                                notification_count = 0
                                failed_count = 0
                                skipped_no_contact = 0
                                error_msg = None
                                
                                try:
                                    # Récupérer les anciennes valeurs avant la mise à jour
                                    old_promo = self.student_service.get_promotion_details(promotion_id)
                                    old_fee = float(old_promo.get('fee_usd', 0)) if old_promo else 0
                                    old_threshold = float(old_promo.get('threshold_amount', 0)) if old_promo else 0
                                    
                                    # Mettre à jour la BD
                                    if self.student_service.update_promotion_financials(promotion_id, fee_val, threshold_val):
                                        success = True

                                        channel_status = self.notification_service.get_channel_status()
                                        email_ok = channel_status.get("email_configured")
                                        whatsapp_ok = channel_status.get("whatsapp_configured")
                                        
                                        # Récupérer les étudiants et envoyer les notifications
                                        students = self.student_service.get_students_by_promotion(promotion_id)
                                        if students:
                                            for i, student in enumerate(students):
                                                loading_indicator.set_status(
                                                    f"Notification {i+1}/{len(students)} aux étudiants..."
                                                )
                                                try:
                                                    student_email = student.get('email')
                                                    student_phone = student.get('phone_number')
                                                    if not student_email and not student_phone:
                                                        skipped_no_contact += 1
                                                        continue

                                                    sent = self.notification_service.send_threshold_change_notification(
                                                        student_email=student_email,
                                                        student_phone=student_phone,
                                                        student_name=f"{student.get('firstname', '')} {student.get('lastname', '')}",
                                                        old_threshold=old_threshold if old_threshold > 0 else None,
                                                        new_threshold=float(threshold_val),
                                                        old_final_fee=old_fee if old_fee > 0 else None,
                                                        new_final_fee=float(fee_val)
                                                    )
                                                    if sent:
                                                        notification_count += 1
                                                    else:
                                                        failed_count += 1
                                                except Exception as notif_err:
                                                    logger.warning(f"Failed to notify student {student.get('id')}: {notif_err}")
                                                    failed_count += 1
                                        else:
                                            skipped_no_contact = 0
                                            failed_count = 0
                                            notification_count = 0
                                        
                                except Exception as ex:
                                    error_msg = str(ex)
                                
                                def finish():
                                    loading_indicator.stop()
                                    loading_dialog.destroy()
                                    save_btn_ref.configure(state="normal")
                                    fee_widget.configure(state="normal")
                                    threshold_widget.configure(state="normal")
                                    
                                    if success:
                                        if not email_ok and not whatsapp_ok:
                                            messagebox.showwarning(
                                                "Succès",
                                                "Frais et seuil mis à jour.\nNotifications non envoyées (Email/WhatsApp non configurés)."
                                            )
                                        elif notification_count > 0:
                                            summary = f"Frais et seuil mis à jour.\n{notification_count} notification(s) envoyée(s)."
                                            if failed_count:
                                                summary += f"\n{failed_count} échec(s) d'envoi."
                                            if skipped_no_contact:
                                                summary += f"\n{skipped_no_contact} étudiant(s) sans email/téléphone."
                                            messagebox.showinfo("Succès", summary)
                                        else:
                                            messagebox.showinfo(
                                                "Succès",
                                                "Frais et seuil mis à jour.\n(Aucun étudiant notifié)"
                                            )
                                        self._show_academic_years()  # Rafraîchir la vue
                                    else:
                                        if error_msg:
                                            messagebox.showerror("Erreur", f"Échec: {error_msg}")
                                        else:
                                            messagebox.showerror("Erreur", "Échec de mise à jour.")
                                
                                self.after(0, finish)
                            
                            threading.Thread(target=worker, daemon=True).start()
                            
                        except Exception:
                            messagebox.showerror("Erreur", "Montants invalides.")
                    return _save

                save_btn = ctk.CTkButton(
                    row,
                    text="Enregistrer",
                    width=110,
                    fg_color=self.colors["primary"],
                    hover_color="#2563eb",
                    text_color=self.colors["text_white"],
                    command=make_save(promo.get('id'), fee_entry, threshold_entry, None)
                )
                save_btn.grid(row=0, column=6, sticky="ew", padx=10, pady=6)
                
                # Passer le bouton à la fonction make_save
                save_btn.configure(command=make_save(promo.get('id'), fee_entry, threshold_entry, save_btn))

        render_promotions()
        faculty_filter.configure(command=lambda _value: render_promotions())
        
        # === Section: Périodes d'Examens ===
        exam_card = self._create_card(self.content_frame)
        exam_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            exam_card,
            text="📅 Périodes d'Examens",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        if active_year:
            exam_periods = self.academic_year_service.get_exam_periods(active_year['academic_year_id'])
            
            if exam_periods:
                # Tableau des périodes
                headers = ["Période", "Début", "Fin", "Durée"]
                layout = self._get_table_layout("exam_periods", len(headers))
                column_weights = layout["weights"]
                header_anchors = layout["anchors"]
                min_widths = layout["min_widths"]
                self._create_table_header(exam_card, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=10)
                
                # Liste des périodes
                scroll_frame = ctk.CTkScrollableFrame(exam_card, fg_color="transparent")
                scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
                
                for period in exam_periods:
                    start = datetime.strptime(str(period['start_date']), "%Y-%m-%d")
                    end = datetime.strptime(str(period['end_date']), "%Y-%m-%d")
                    duration = (end - start).days
                    
                    row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
                    row.pack(fill="x", pady=4)

                    self._configure_table_columns(row, column_weights, min_widths=min_widths)
                    row_values = [period['period_name'], start.strftime("%d/%m/%Y"), end.strftime("%d/%m/%Y"), f"{duration} jours"]
                    row_colors = [self.colors["text_dark"], self.colors["text_light"], self.colors["text_light"], self.colors["info"]]
                    row_weights = ["bold", "normal", "normal", "bold"]
                    row_anchors = ["w", "center", "center", "e"]
                    self._populate_table_row(
                        row,
                        row_values,
                        column_weights,
                        text_colors=row_colors,
                        font_weights=row_weights,
                        anchors=row_anchors,
                        min_widths=min_widths
                    )
            else:
                ctk.CTkLabel(exam_card, text="❌ Aucune période d'examens définie", font=ctk.CTkFont(size=12), text_color=self.colors["warning"]).pack(anchor="w", padx=25, pady=20)
        else:
            ctk.CTkLabel(exam_card, text="❌ Créez une année académique d'abord", font=ctk.CTkFont(size=12), text_color=self.colors["danger"]).pack(anchor="w", padx=25, pady=20)
    
    def _update_thresholds(self, new_threshold_str, new_fee_str, academic_year_id):
        """Met à jour les seuils financiers et notifie tous les étudiants"""
        try:
            from decimal import Decimal
            
            new_threshold_usd = Decimal(new_threshold_str)
            new_fee_usd = Decimal(new_fee_str)
            new_threshold = new_threshold_usd
            new_fee = new_fee_usd
            
            # VALIDATION CRITIQUE : Le seuil ne peut JAMAIS dépasser les frais académiques
            if new_threshold > new_fee:
                messagebox.showerror(
                    "Erreur de Validation",
                    f"Le seuil financier (${float(new_threshold):,.2f}) ne peut pas dépasser \n"
                    f"les frais académiques totaux (${float(new_fee):,.2f}).\n\n"
                    f"Le seuil représente le minimum à payer pour accéder aux examens.\n"
                    f"Les frais totaux sont le montant complèt à payer dans l'année.\n\n"
                    f"Veuillez corriger les valeurs."
                )
                return
            
            if not academic_year_id:
                messagebox.showerror("Erreur", "Aucune année académique active")
                return
            
            # Récupérer l'année pour avoir partial_valid_days
            active_year = self.academic_year_service.get_active_year()
            partial_valid_days = active_year.get('partial_valid_days', 30) if active_year else 30
            
            # Mettre à jour
            self.finance_service.update_financial_thresholds(
                academic_year_id=academic_year_id,
                threshold_amount=new_threshold,
                final_fee=new_fee,
                partial_valid_days=partial_valid_days
            )
            
            channel_status = self.notification_service.get_channel_status()
            email_ok = channel_status.get("email_configured")
            whatsapp_ok = channel_status.get("whatsapp_configured")
            notif_line = "Notifications envoyées via Email et WhatsApp."
            if not email_ok and not whatsapp_ok:
                notif_line = "Notifications non envoyées (Email/WhatsApp non configurés)."
            elif not email_ok:
                notif_line = "Notifications envoyées via WhatsApp uniquement (Email non configuré)."
            elif not whatsapp_ok:
                notif_line = "Notifications envoyées via Email uniquement (WhatsApp non configuré)."

            messagebox.showinfo("Succès", f"Seuils mis à jour avec succès!\n\n"
                              f"Nouveau seuil: ${float(new_threshold_usd):,.2f}\n"
                              f"Nouveaux frais: ${float(new_fee_usd):,.2f}\n\n"
                              f"{notif_line}")
            
            # Recharger la vue en cours (rafraîchissement automatique)
            self._render_current_view()
            
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Veuillez entrer des montants valides (nombres)")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour: {str(e)}")
            logger.error(f"Error updating thresholds: {e}")
    
    def _preview_notifications(self, new_threshold_str, new_fee_str):
        """Affiche une prévisualisation des notifications avec exemple d'étudiant"""
        try:
            new_threshold = float(new_threshold_str) if new_threshold_str.strip() else 300
            new_fee = float(new_fee_str) if new_fee_str.strip() else 500
            
            # Récupérer un étudiant d'exemple pour la prévisualisation
            students = self.student_service.get_students_by_promotion(1)
            example_student = students[0] if students else None
            
            student_name = example_student.get("firstname", "Jean") if example_student else "Jean"
            student_phone = example_student.get("phone_number", "+243...") if example_student else "+243..."
            
            active_year = self.academic_year_service.get_active_year()
            old_threshold = float(active_year.get("threshold_amount") or 300) if active_year else 300
            old_fee = float(active_year.get("final_fee") or 500) if active_year else 500
            
            preview_window = ctk.CTkToplevel(self)
            preview_window.title("📢 Prévisualisation des Notifications")
            preview_window.geometry("700x600")
            preview_window.grab_set()
            self._animate_window_open(preview_window)
            
            # Header
            ctk.CTkLabel(
                preview_window,
                text="📧 EMAIL NOTIFICATION",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(anchor="w", padx=20, pady=(15, 10))
            
            # Email content frame
            email_frame = ctk.CTkFrame(preview_window, fg_color=self.colors["border"], corner_radius=8)
            email_frame.pack(fill="both", padx=20, pady=(0, 15), expand=False)
            
            email_content = (
                f"De: noreply@uor.rw\n"
                f"À: {student_name}@example.com\n"
                f"Sujet: ⚠️ Mise à jour - Seuils Financiers pour Accès aux Examens\n\n"
                f"{'─' * 60}\n\n"
                f"Bonjour {student_name},\n\n"
                f"Ceci est une notification importante concernant votre \n"
                f"accès aux examens.\n\n"
                f"📊 CHANGE DE SEUILS DÉTECTÉE:\n\n"
                f"  • Ancien seuil: ${old_threshold:,.2f}\n"
                f"  • Nouveau seuil: ${new_threshold:,.2f}\n"
                f"  • Anciens frais: ${old_fee:,.2f}\n"
                f"  • Nouveaux frais: ${new_fee:,.2f}\n\n"
                f"⚠️  IMPORTANT:\n"
                f"Si vous aviez un code d'accès temporaire (paiement partiel),\n"
                f"celui-ci a été annulé et doit être renouvelé.\n\n"
                f"📝 ACTION REQUISE:\n"
                f"Veuillez vous connecter à votre compte pour vérifier\n"
                f"votre statut de paiement.\n\n"
                f"Questions? Contactez l'administration U.O.R.\n\n"
                f"Cordialement,\n"
                f"L'équipe U.O.R - Accès aux Examens"
            )
            
            email_label = ctk.CTkLabel(
                email_frame,
                text=email_content,
                font=ctk.CTkFont(size=10, family="Courier"),
                text_color=self.colors["text_dark"],
                justify="left"
            )
            email_label.pack(anchor="w", padx=15, pady=15)
            
            # Divider
            ctk.CTkLabel(
                preview_window,
                text="",
                font=ctk.CTkFont(size=3)
            ).pack()
            
            # WhatsApp section
            ctk.CTkLabel(
                preview_window,
                text="💬 MESSAGE WHATSAPP",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(anchor="w", padx=20, pady=(10, 10))
            
            # WhatsApp content frame (bubble style)
            whatsapp_frame = ctk.CTkFrame(preview_window, fg_color=self.colors["info"], corner_radius=12)
            whatsapp_frame.pack(fill="both", padx=20, pady=(0, 15), expand=False)
            
            whatsapp_content = (
                f"🔔 U.O.R - ALERTE SEUILS FINANCIERS\n\n"
                f"Bonjour {student_name},\n\n"
                f"Les seuils d'accès aux examens ont changé:\n\n"
                f"❌ Ancien: ${old_threshold:,.2f}\n"
                f"✅ Nouveau: ${new_threshold:,.2f}\n\n"
                f"Frais complets: ${new_fee:,.2f}\n\n"
                f"⚠️ Les codes d'accès temporaires ont été annulés.\n\n"
                f"Gérez votre paiement sur le portail."
            )
            
            whatsapp_label = ctk.CTkLabel(
                whatsapp_frame,
                text=whatsapp_content,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_white"],
                justify="left"
            )
            whatsapp_label.pack(anchor="w", padx=12, pady=12)
            
            # Close button
            ctk.CTkButton(
                preview_window,
                text="Fermer",
                fg_color=self.colors["primary"],
                hover_color="#2563eb",
                command=preview_window.destroy
            ).pack(pady=(0, 15), padx=20, fill="x")
            
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Veuillez entrer des montants valides (nombres)")
    
    def _clear_content(self):
        """Efface le contenu"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        if not self._loading_visible:
            self._animate_view_transition()
    
    def _on_language_change(self, value):
        """Change la langue"""
        self.selected_language = value
        self.translator.set_language(value)
        self._recreate_ui()
        logger.info(f"Langue changée à: {value}")
    
    def _on_logout(self):
        """Déconnecte l'utilisateur"""
        logger.info("Déconnexion")
        try:
            if hasattr(self.parent_window, "dashboard"):
                self.parent_window.dashboard = None
            self.destroy()
            if hasattr(self.parent_window, "_show_login"):
                self.parent_window._show_login()
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
            try:
                self.destroy()
            except Exception:
                pass
