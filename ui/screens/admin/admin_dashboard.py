import requests
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
import tkinter as tk
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
from app.services.transfer.transfer_service import TransferService
from core.models.student import Student

logger = logging.getLogger(__name__)


class ErrorManager:
    """Gère les messages d'erreur avec niveaux utilisateur et développeur"""
    
    # Mapping des erreurs: (type_erreur) -> (message_utilisateur, msg_log_template)
    ERROR_MESSAGES = {
        "database_connection": (
            "Une erreur s'est produite lors de la connexion à la base de données.",
            "Database connection error: {details}"
        ),
        "database_query": (
            "Une erreur s'est produite lors de la lecture des données.",
            "Database query error: {details}"
        ),
        "payment_invalid_amount": (
            "Le montant saisi est invalide. Veuillez vérifier et réessayer.",
            "Invalid payment amount: {details}"
        ),
        "payment_exceeds_limit": (
            "Le montant saisi dépasse ce qui reste à payer pour cet étudiant.",
            "Payment exceeds limit: {details}"
        ),
        "payment_already_paid": (
            "Cet étudiant a déjà complété tous ses paiements.",
            "Payment attempt for fully paid student: {details}"
        ),
        "payment_no_active_fees": (
            "Votre paiement a échoué en raison :\n\nLes frais académiques pour cette promotion ne sont pas définis ou connus.",
            "Payment rejected: No active academic fees for student: {details}"
        ),
        "payment_processing": (
            "Une erreur s'est produite lors du traitement du paiement.",
            "Payment processing error: {details}"
        ),
        "validation_error": (
            "Les données fournies sont invalides.",
            "Validation error: {details}"
        ),
        "unknown_error": (
            "Une erreur inattendue s'est produite. Veuillez réessayer.",
            "Unexpected error: {details}"
        ),
    }
    
    @staticmethod
    def show_error(error_type: str, details: str = None, parent=None):
        """
        Affiche un message d'erreur à l'utilisateur et enregistre pour le développeur
        
        Args:
            error_type: Type d'erreur (clé du mapping)
            details: Détails techniques de l'erreur
            parent: Widget parent (optionnel)
        """
        user_msg, log_template = ErrorManager.ERROR_MESSAGES.get(
            error_type, 
            ErrorManager.ERROR_MESSAGES["unknown_error"]
        )
        
        # Enregistrer le message complet pour le développeur
        log_msg = log_template.format(details=details or "No details provided")
        logger.error(log_msg)
        
        # Afficher un message simple à l'utilisateur
        messagebox.showerror("Erreur", user_msg, parent=parent)
    
    @staticmethod
    def show_success(title: str, message: str, parent=None):
        """Affiche un message de succès à l'utilisateur"""
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def show_warning(title: str, message: str, parent=None):
        """Affiche un avertissement à l'utilisateur"""
        messagebox.showwarning(title, message, parent=parent)


class ModernDialog:
    """Classe pour créer des dialogues modernes avec style cohérent"""
    
    @staticmethod
    def create_centered_dialog(parent_dashboard, title: str, width: int = 520, height: int = 480):
        """Crée et centre un dialogue sur le dashboard"""
        dialog = ctk.CTkToplevel(parent_dashboard)
        dialog.title(title)
        
        # Centrer sur le dashboard
        dashboard_x = parent_dashboard.winfo_rootx()
        dashboard_y = parent_dashboard.winfo_rooty()
        dashboard_width = parent_dashboard.winfo_width()
        dashboard_height = parent_dashboard.winfo_height()
        
        center_x = dashboard_x + (dashboard_width - width) // 2
        center_y = dashboard_y + (dashboard_height - height) // 2
        
        dialog.geometry(f"{width}x{height}+{center_x}+{center_y}")
        dialog.grab_set()
        dialog.resizable(False, False)
        
        return dialog
    
    @staticmethod
    def create_header(parent, title: str, subtitle: str = "", bg_color: str = "#0a84ff"):
        """Crée un en-tête coloré"""
        header = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=0)
        header.pack(fill="x", side="top")
        
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(15, 8 if subtitle else 15), padx=20)
        
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header,
                text=subtitle,
                font=ctk.CTkFont(size=12),
                text_color="#e8f4ff"
            )
            subtitle_label.pack(pady=(0, 15), padx=20)
        
        return header
    
    @staticmethod
    def create_content_frame(parent):
        """Crée un frame de contenu avec le bon style"""
        return ctk.CTkFrame(parent, fg_color="#f8f9fa")
    
    @staticmethod
    def create_button_frame(parent):
        """Crée un frame pour les boutons"""
        return ctk.CTkFrame(parent, fg_color="transparent")


class Tooltip:
    """Simple tooltip that appears as a label next to the widget"""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.tooltip_label = None
        
    def show_tooltip(self, event=None):
        """Show the tooltip"""
        if self.tooltip_window is not None:
            return
        
        # Create a small toplevel window for tooltip
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_attributes("-topmost", True)
        
        # Create label inside
        self.tooltip_label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#1e293b",
            foreground="#f8fafc",
            padx=10,
            pady=6,
            font=("Arial", 10, "bold"),
            relief=tk.FLAT
        )
        self.tooltip_label.pack()
        
        # Position it next to the widget
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10
        y = self.widget.winfo_rooty() + (self.widget.winfo_height() // 2) - 15
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Schedule removal
        self.tooltip_window.after(2000, self.hide_tooltip)
    
    def hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window is not None:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None
            self.tooltip_label = None


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
        self.transfer_service = TransferService()
        self._photo_cache = {}
        self._esp32_status_label = None
        self._responsive_labels = []
        self.sidebar_mode = "compact"
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
            "academic_years": self._show_academic_years,
            "transfers": self._show_transfers
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
            text="TABLEAU DE BORD ADMIN",
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
            ("�", "academic_data", "Données Académiques", lambda: self._run_with_loading(self._show_student_academic_data)),
            ("�💰", "finance", self._t("finance", "Finances"), lambda: self._run_with_loading(self._show_finance)),
            ("📚", "academic_years", self._t("academic_years", "Années Acad."), lambda: self._run_with_loading(self._show_academic_years)),
            ("�", "transfers", self._t("transfers", "Transferts"), lambda: self._run_with_loading(self._show_transfers)),
            ("�📋", "access_logs", self._t("access_logs", "Logs d'Accès"), lambda: self._run_with_loading(self._show_access_logs)),
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
            
            # Add tooltip on hover (show label when icon-only in compact mode)
            def create_tooltip_binding(button, tooltip_text):
                tooltip_obj = Tooltip(button, tooltip_text)
                
                def on_enter(_event):
                    if self.sidebar_mode == "compact":
                        tooltip_obj.show_tooltip(_event)
                
                def on_leave(_event):
                    tooltip_obj.hide_tooltip()
                
                button.bind("<Enter>", on_enter)
                button.bind("<Leave>", on_leave)
            
            create_tooltip_binding(btn, label)
            
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
        
        # Add tooltip for logout button
        logout_tooltip = Tooltip(self.logout_btn, "Déconnexion")
        def show_logout_tooltip(_event):
            if self.sidebar_mode == "compact":
                logout_tooltip.show_tooltip(_event)
        def hide_logout_tooltip(_event):
            logout_tooltip.hide_tooltip()
        self.logout_btn.bind("<Enter>", show_logout_tooltip)
        self.logout_btn.bind("<Leave>", hide_logout_tooltip)
        
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
        # Forcer le mode compact (icônes seulement) pour gagner de l'espace
        self._apply_sidebar_mode("compact")
    
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
        
        # Toujours forcer le mode compact pour gagner de l'espace
        target_mode = "compact"
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
        
        # Responsive sizing: compact pour tenir dans l'écran
        if self.screen_width < 1200:
            dialog_width = min(520, max(420, int(self.screen_width * 0.45)))
            dialog_height = min(650, max(550, int(self.screen_height * 0.65)))
        else:
            dialog_width = min(600, max(520, int(self.screen_width * 0.4)))
            dialog_height = min(700, max(600, int(self.screen_height * 0.70)))
        
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        
        # Background moderne
        dialog.configure(fg_color=self.colors["main_bg"])
        
        self._animate_window_open(dialog)

        # === HEADER ÉLÉGANT (COMPACT) ===
        header = ctk.CTkFrame(dialog, fg_color=self.colors["primary"], corner_radius=0, height=55)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            header_content,
            text="➕ Nouvel Étudiant",
            font=self._font(18, "bold"),
            text_color=self.colors["text_white"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_content,
            text="Remplissez tous les champs requis",
            font=self._font(10),
            text_color="#e5f0ff"
        ).pack(side="left", padx=(15, 0))

        # === SCROLL FORM CONTAINER ===
        form_outer = ctk.CTkFrame(dialog, fg_color="transparent")
        form_outer.pack(fill="both", expand=True, padx=15, pady=12)

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
        section_identity.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            section_identity,
            text="👤 Informations personnelles",
            font=self._font(12, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=10, pady=(8, 6))

        identity_frame = ctk.CTkFrame(section_identity, fg_color="transparent")
        identity_frame.pack(fill="x", padx=10, pady=(0, 8))
        identity_frame.grid_columnconfigure(0, weight=1)
        identity_frame.grid_columnconfigure(1, weight=1)

        def add_labeled_entry(parent, label_text, placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(parent, text=label_text, font=self._font(10), text_color=self.colors["text_light"])
            label.grid(row=row, column=col, sticky="w", padx=4, pady=(5, 1), columnspan=col_span)
            entry = ctk.CTkEntry(
                parent,
                placeholder_text=placeholder,
                fg_color=self.colors["main_bg"],
                border_color=self.colors["border"],
                border_width=1,
                corner_radius=6,
                height=28
            )
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=4, pady=(0, 4))
            return entry

        student_number_entry = add_labeled_entry(identity_frame, "Matricule étudiant *", "STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry(identity_frame, "Prénom *", "Jean", row=0, col=1)
        lastname_entry = add_labeled_entry(identity_frame, "Nom *", "Dupont", row=2, col=0)
        email_entry = add_labeled_entry(identity_frame, "Email *", "jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry(identity_frame, "Téléphone WhatsApp *", "+243123456789", row=4, col=0, col_span=2)

        # === SECTION: ACADÉMIQUE ===
        section_academic = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_academic.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            section_academic,
            text="🎓 Informations académiques",
            font=self._font(12, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=10, pady=(8, 6))

        academic_frame = ctk.CTkFrame(section_academic, fg_color="transparent")
        academic_frame.pack(fill="x", padx=10, pady=(0, 8))
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
        section_photo.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            section_photo,
            text="📸 Photo du visage (passeport)",
            font=self._font(12, "bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=10, pady=(8, 6))

        photo_frame = ctk.CTkFrame(section_photo, fg_color="transparent")
        photo_frame.pack(fill="x", padx=10, pady=(0, 6))
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
            height=28
        )
        photo_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        choose_btn = ctk.CTkButton(
            photo_frame,
            text="📁 Parcourir",
            width=80,
            height=28,
            fg_color=self.colors["info"],
            hover_color="#0891b2",
            corner_radius=6
        )
        choose_btn.grid(row=0, column=1)

        preview_frame = ctk.CTkFrame(section_photo, fg_color="transparent")
        preview_frame.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(
            preview_frame,
            text="Aperçu",
            font=self._font(10),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(0, 4))

        preview_image_label = ctk.CTkLabel(preview_frame, text="")
        preview_image_label.pack(anchor="w")

        guidelines = ctk.CTkLabel(
            section_photo,
            text="Fond neutre • Visage centré • Une seule personne • Bonne lumière",
            font=self._font(9),
            text_color=self.colors["text_light"]
        )
        guidelines.pack(anchor="w", padx=10, pady=(0, 6))

        def choose_photo():
            file_path = filedialog.askopenfilename(
                title="Choisir une photo",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                photo_path_var.set(file_path)
                try:
                    image = Image.open(file_path)
                    image.thumbnail((100, 130))
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    preview_image_label.configure(image=ctk_image)
                    preview_image_label.image = ctk_image
                except Exception as e:
                    logger.warning(f"Preview photo error: {e}")

        choose_btn.configure(command=choose_photo)

        # === SECTION: BOUTONS ===
        button_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        button_frame.pack(fill="x", pady=(6, 0))
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
                ErrorManager.show_error("validation_error", "All fields are required", dialog)
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
                        ErrorManager.show_error("validation_error", f"Failed to create academic year: {selected_year_name}", dialog)
                        return
                else:
                    messagebox.showinfo("Annulé", "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.")
                    return
            
            if not selected_year_id:
                ErrorManager.show_error("validation_error", "Academic year is required", dialog)
                return

            faculty_matches = self.student_service.find_faculty_by_input(faculty_label)
            if not faculty_matches:
                faculty_id = self.student_service.create_faculty(faculty_label)
                if not faculty_id:
                    ErrorManager.show_error("validation_error", f"Failed to create faculty: {faculty_label}", dialog)
                    return
            else:
                faculty_id = faculty_matches[0]["id"]

            department_matches = self.student_service.find_department_by_input(department_label, faculty_id)
            if not department_matches:
                department_id = self.student_service.create_department(department_label, faculty_id)
                if not department_id:
                    ErrorManager.show_error("validation_error", f"Failed to create department: {department_label}", dialog)
                    return
            else:
                department_id = department_matches[0]["id"]

            promotion_matches = self.student_service.find_promotion_by_input(promotion_label, department_id)
            if not promotion_matches:
                promotion_id = self.student_service.create_promotion(promotion_label, department_id)
                if not promotion_id:
                    ErrorManager.show_error("validation_error", f"Failed to create promotion: {promotion_label}", dialog)
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
                ErrorManager.show_error("database_query", f"Failed to fetch academic year data for year_id: {selected_year_id}", dialog)
                return

            encoding = None
            if self.face_service.is_available():
                try:
                    encoding = self.face_service.register_face(photo_path, 1)
                except Exception as e:
                    ErrorManager.show_error("validation_error", f"Face registration failed: {str(e)}", dialog)
                    return

                if encoding is None:
                    ErrorManager.show_error("validation_error", "No face detected or multiple faces found. Use a passport photo.", dialog)
                    return

                quality_ok, quality_msg = self.face_service.validate_passport_photo(photo_path)
                if not quality_ok:
                    ErrorManager.show_error("validation_error", f"Photo quality insufficient: {quality_msg}", dialog)
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
                ErrorManager.show_error("validation_error", f"Failed to save photo: {str(e)}", dialog)
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
                ErrorManager.show_error("database_query", "Failed to register student", dialog)
                return

            finance_ok = self.finance_service.create_finance_profile(student_id, threshold_required, selected_year_id)
            if not finance_ok:
                logger.warning(f"Finance profile not created for student {student_id}")

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

            ErrorManager.show_success("Succès", "Étudiant enregistré avec succès.", dialog)
            dialog.destroy()
            self._show_students()

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Annuler",
            fg_color=self.colors["border"],
            text_color=self.colors["text_dark"],
            hover_color=self.colors["hover"],
            height=32,
            corner_radius=8,
            command=dialog.destroy
        )
        cancel_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        save_btn = ctk.CTkButton(
            button_frame,
            text="✓ Valider",
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=32,
            corner_radius=8,
            command=save_student
        )
        save_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _open_edit_student_dialog(self, student: dict):
        """Ouvre la fenêtre de modification complète d'un étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Modifier étudiant")
        dialog_width = min(620, max(520, int(self.screen_width * 0.5)))
        dialog_height = min(720, max(600, int(self.screen_height * 0.72)))
        
        # Centrer sur le dashboard
        dashboard_x = self.winfo_rootx()
        dashboard_y = self.winfo_rooty()
        dashboard_width = self.winfo_width()
        dashboard_height = self.winfo_height()
        
        center_x = dashboard_x + (dashboard_width - dialog_width) // 2
        center_y = dashboard_y + (dashboard_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
        dialog.grab_set()
        dialog.resizable(False, False)
        self._animate_window_open(dialog)

        student_id = student.get("id")
        details = self.student_service.get_student_with_academics(student_id) or student

        # === HEADER COLORÉ (COMPACT) ===
        header = ctk.CTkFrame(dialog, fg_color="#8b5cf6", corner_radius=0)
        header.pack(fill="x", side="top")
        
        ctk.CTkLabel(
            header,
            text="✏️ Modifier Étudiant",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(12, 6), padx=20)
        
        fullname = f"{details.get('firstname', '')} {details.get('lastname', '')}".strip()
        ctk.CTkLabel(
            header,
            text=fullname or "Aucun nom",
            font=ctk.CTkFont(size=11),
            text_color="#f3e8ff"
        ).pack(pady=(0, 10), padx=20)

        # === CONTENU PRINCIPAL ===
        content = ctk.CTkFrame(dialog, fg_color="#f8f9fa")
        content.pack(fill="both", expand=True, padx=0, pady=0)

        form_container = ctk.CTkFrame(content, fg_color="transparent")
        form_container.pack(fill="both", expand=True, padx=15, pady=10)

        form = ctk.CTkScrollableFrame(
            form_container,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["text_light"]
        )
        form.pack(fill="both", expand=True, padx=3, pady=3)

        fields_frame = ctk.CTkFrame(form, fg_color="transparent")
        fields_frame.pack(fill="x", padx=3, pady=3)
        fields_frame.grid_columnconfigure(0, weight=1)
        fields_frame.grid_columnconfigure(1, weight=1)

        def add_labeled_entry(label_text, value="", placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(fields_frame, text=label_text, font=self._font(10))
            label.grid(row=row, column=col, sticky="w", padx=4, pady=(5, 2))
            entry = ctk.CTkEntry(fields_frame, placeholder_text=placeholder, height=28)
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=4, pady=(0, 3))
            if value:
                entry.insert(0, value)
            return entry

        student_number_entry = add_labeled_entry("Matricule étudiant", details.get("student_number", ""), "Ex: STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry("Prénom", details.get("firstname", ""), "Ex: Jean", row=0, col=1)
        lastname_entry = add_labeled_entry("Nom", details.get("lastname", ""), "Ex: Dupont", row=2, col=0)
        email_entry = add_labeled_entry("Email", details.get("email", ""), "Ex: jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry("Téléphone WhatsApp", details.get("phone_number", ""), "Ex: +243123456789", row=4, col=0)

        # Année académique
        years = self.academic_year_service.get_years()
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}
        current_year_name = details.get("academic_year_name") or ""

        ctk.CTkLabel(fields_frame, text="Année académique", font=self._font(10)).grid(row=6, column=0, sticky="w", padx=4, pady=(5, 2))
        year_entry = ctk.CTkEntry(fields_frame, placeholder_text="Ex: 2024-2025", height=28)
        if current_year_name:
            year_entry.insert(0, current_year_name)
        year_entry.grid(row=7, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 3))

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
        photo_row.pack(fill="x", pady=(6, 0))
        photo_row.grid_columnconfigure(0, weight=0)
        photo_row.grid_columnconfigure(1, weight=1)
        photo_row.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(photo_row, text="Photo du visage (passeport)", font=self._font(10)).grid(row=0, column=0, sticky="w", padx=(0, 6))
        photo_path_var = StringVar(value="")
        photo_entry = ctk.CTkEntry(photo_row, textvariable=photo_path_var, height=28)
        photo_entry.grid(row=0, column=1, sticky="ew")

        preview_frame = ctk.CTkFrame(form, fg_color="transparent")
        preview_frame.pack(fill="x", pady=(4, 2))
        preview_label = ctk.CTkLabel(
            preview_frame,
            text="Aperçu photo",
            font=self._font(10),
            text_color=self.colors["text_light"]
        )
        preview_label.pack(anchor="w")

        preview_image_label = ctk.CTkLabel(preview_frame, text="")
        preview_image_label.pack(anchor="w", pady=(2, 0))

        existing_photo_path = details.get("passport_photo_path")
        existing_photo_blob = details.get("passport_photo_blob")
        existing_image = self._get_cached_photo(existing_photo_path, existing_photo_blob, size=(80, 100))
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
                    image.thumbnail((80, 100))
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    preview_image_label.configure(image=ctk_image)
                    preview_image_label.image = ctk_image
                except Exception as e:
                    logger.warning(f"Preview photo error: {e}")

        choose_btn = ctk.CTkButton(photo_row, text="Parcourir", width=80, height=28, command=choose_photo)
        choose_btn.grid(row=0, column=2, sticky="e", padx=(8, 0))

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
                ErrorManager.show_error("validation_error", "All fields are required", dialog)
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
                        ErrorManager.show_error("validation_error", f"Failed to create academic year: {selected_year_name}", dialog)
                        return
                else:
                    messagebox.showinfo("Annulé", "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.")
                    return

            faculty_matches = self.student_service.find_faculty_by_input(faculty_label)
            if not faculty_matches:
                faculty_id = self.student_service.create_faculty(faculty_label)
                if not faculty_id:
                    ErrorManager.show_error("validation_error", f"Failed to create faculty: {faculty_label}", dialog)
                    return
            else:
                faculty_id = faculty_matches[0]["id"]

            department_matches = self.student_service.find_department_by_input(department_label, faculty_id)
            if not department_matches:
                department_id = self.student_service.create_department(department_label, faculty_id)
                if not department_id:
                    ErrorManager.show_error("validation_error", f"Failed to create department: {department_label}", dialog)
                    return
            else:
                department_id = department_matches[0]["id"]

            promotion_matches = self.student_service.find_promotion_by_input(promotion_label, department_id)
            if not promotion_matches:
                promotion_id = self.student_service.create_promotion(promotion_label, department_id)
                if not promotion_id:
                    ErrorManager.show_error("validation_error", f"Failed to create promotion: {promotion_label}", dialog)
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
                    ErrorManager.show_error("validation_error", f"Failed to save photo: {str(e)}", dialog)
                    return

            logger.debug(f"Updating student {student_id} with data: {update_data}")
            if self.student_service.update_student(student_id, update_data):
                ErrorManager.show_success("Succès", "Étudiant modifié avec succès.", dialog)
                dialog.destroy()
                self._show_students()
            else:
                ErrorManager.show_error("database_query", f"Failed to update student {student_id}", dialog)

        button_row = ctk.CTkFrame(form, fg_color="transparent")
        button_row.pack(fill="x", pady=(8, 10))

        save_btn = ctk.CTkButton(
            button_row,
            text="Enregistrer",
            fg_color=self.colors["success"],
            hover_color=self.colors["primary"],
            height=32,
            command=save_changes
        )
        save_btn.pack(fill="x")

    def _open_payment_dialog(self, student: dict):
        """Ouvre une fenêtre pour enregistrer un paiement étudiant - Style moderne"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Enregistrer un paiement")
        
        # Dimension responsive et centré
        dialog_width = min(520, max(400, int(self.screen_width * 0.4)))
        dialog_height = min(480, max(360, int(self.screen_height * 0.5)))
        
        # Centrer sur le dashboard
        dashboard_x = self.winfo_rootx()
        dashboard_y = self.winfo_rooty()
        dashboard_width = self.winfo_width()
        dashboard_height = self.winfo_height()
        
        center_x = dashboard_x + (dashboard_width - dialog_width) // 2
        center_y = dashboard_y + (dashboard_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
        dialog.grab_set()
        dialog.resizable(False, False)
        self._animate_window_open(dialog)

        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        student_number = student.get("student_number", "-")
        student_id = student.get("id")

        # === HEADER COLORÉ ===
        header = ctk.CTkFrame(dialog, fg_color="#0a84ff", corner_radius=0)
        header.pack(fill="x", side="top")
        
        title_label = ctk.CTkLabel(
            header,
            text="💳 Enregistrer un Paiement",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        title_label.pack(pady=(15, 8), padx=20)
        
        student_info_label = ctk.CTkLabel(
            header,
            text=f"{fullname} • #{student_number}",
            font=ctk.CTkFont(size=12),
            text_color="#e8f4ff"
        )
        student_info_label.pack(pady=(0, 15), padx=20)

        # === CONTENU PRINCIPAL ===
        content = ctk.CTkFrame(dialog, fg_color=self.colors.get("main_bg", "#f8f9fa"))
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # Label Montant avec icône
        amount_label_box = ctk.CTkFrame(content, fg_color="transparent")
        amount_label_box.pack(fill="x", padx=25, pady=(20, 8))
        
        ctk.CTkLabel(
            amount_label_box,
            text="💰 Montant à payer",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#1e293b"
        ).pack(anchor="w")

        # Input Montant avec style amélioré
        amount_entry = ctk.CTkEntry(
            content,
            placeholder_text="Entrez le montant (ex: 50.00)",
            font=ctk.CTkFont(size=12),
            fg_color="#ffffff",
            text_color="#1e293b",
            placeholder_text_color="#cbd5e1",
            border_color="#cbd5e1",
            border_width=1,
            height=40,
            corner_radius=8
        )
        amount_entry.pack(fill="x", padx=25, pady=(0, 15))

        # Conteneur pour la barre de progression (caché initialement)
        loading_container = ctk.CTkFrame(content, fg_color="transparent")
        loading_container.pack(fill="x", padx=25, pady=(10, 0))
        
        # === BARRE DE PROGRESSION PERSONNALISÉE ===
        progress_frame = ctk.CTkFrame(loading_container, fg_color="transparent")
        progress_frame.pack(fill="x", pady=(0, 0))
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#0a84ff"
        )
        progress_label.pack(anchor="w", pady=(0, 6))
        
        # Barre de progression avec fond gris
        progress_bg = ctk.CTkFrame(progress_frame, fg_color="#e2e8f0", height=6, corner_radius=3)
        progress_bg.pack(fill="x")
        progress_bg.pack_propagate(False)
        
        progress_bar = ctk.CTkFrame(progress_bg, fg_color="#0a84ff", height=6, corner_radius=3)
        progress_bar.pack(side="left", fill="y")
        progress_bar.pack_propagate(False)
        
        # Pourcentage
        progress_pct_label = ctk.CTkLabel(
            progress_frame,
            text="0%",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#0a84ff"
        )
        progress_pct_label.pack(anchor="e", pady=(4, 0))
        
        def update_progress(percent: int, status_text: str = ""):
            """Met à jour la barre de progression"""
            progress_width = int((percent / 100) * (progress_bg.winfo_width() - 4))
            if progress_width > 0:
                progress_bar.configure(width=progress_width)
            progress_pct_label.configure(text=f"{percent}%")
            if status_text:
                progress_label.configure(text=status_text)

        def save_payment():
            amount_text = amount_entry.get().strip().replace(",", ".")
            if not amount_text:
                ErrorManager.show_error("validation_error", "Empty amount field", dialog)
                return
            try:
                amount_usd = Decimal(amount_text)
                if amount_usd <= 0:
                    ErrorManager.show_error("payment_invalid_amount", f"Amount {amount_usd} is not positive", dialog)
                    return

                finance = self.finance_service.get_student_finance(student_id)
                if not finance:
                    self.finance_service.create_finance_profile(student_id, None, student.get("academic_year_id"))
                    finance = self.finance_service.get_student_finance(student_id)

                # Vérifier que le profil finance existe
                if not finance:
                    ErrorManager.show_error(
                        "payment_processing",
                        "Impossible de créer le profil financier de l'étudiant",
                        dialog
                    )
                    return

                final_fee = finance.get("final_fee")
                if final_fee is None and finance.get("academic_year_id"):
                    year = self.academic_year_service.get_year_by_id(finance.get("academic_year_id"))
                    if year:
                        final_fee = year.get("final_fee")
                final_fee = Decimal(str(final_fee or 0))
                current_paid = Decimal(str(finance.get("amount_paid") or 0))
                
                # Vérifier si des frais académiques sont définis
                if final_fee <= 0:
                    ErrorManager.show_error(
                        "payment_no_active_fees",
                        f"Student {student_id} promotion has no active academic fees",
                        dialog
                    )
                    return
                
                # Vérifier si l'étudiant a déjà tout payé
                if current_paid >= final_fee:
                    ErrorManager.show_error(
                        "payment_already_paid",
                        f"Student {student_id} has already paid ${current_paid:.2f} (total: ${final_fee:.2f})",
                        dialog
                    )
                    return
                
                # Vérifier si le montant dépasse la limite
                if (current_paid + amount_usd) > final_fee:
                    remaining = final_fee - current_paid
                    if remaining < 0:
                        remaining = Decimal("0")
                    ErrorManager.show_error(
                        "payment_exceeds_limit",
                        f"Payment amount ${amount_usd} exceeds remaining balance ${remaining:.2f}",
                        dialog
                    )
                    return

                save_btn.configure(state="disabled")
                amount_entry.configure(state="disabled")
                progress_frame.pack(fill="x", padx=0, pady=(10, 15))

                def worker():
                    success = False
                    error_msg = None
                    try:
                        # Simuler la progression
                        for i in [10, 30, 60, 80]:
                            self.after(200, lambda p=i: update_progress(p, f"Traitement... {p}%"))
                            import time
                            time.sleep(0.3)
                        
                        success = self.finance_service.record_payment(student_id, amount_usd)
                    except Exception as ex:
                        error_msg = str(ex)

                    def finish():
                        if success:
                            update_progress(100, "Paiement enregistré ✓")
                            self.after(1500, lambda: [
                                ErrorManager.show_success("Succès", "Paiement enregistré avec succès.", dialog),
                                dialog.destroy(),
                                self._render_current_view()
                            ])
                        else:
                            progress_frame.pack_forget()
                            save_btn.configure(state="normal")
                            amount_entry.configure(state="normal")
                            if error_msg:
                                ErrorManager.show_error("payment_processing", error_msg, dialog)
                            else:
                                ErrorManager.show_error("payment_processing", "Unknown error", dialog)

                    self.after(0, finish)

                threading.Thread(target=worker, daemon=True).start()
            except Exception as ex:
                ErrorManager.show_error("payment_invalid_amount", str(ex), dialog)

        # === BOUTONS ===
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", padx=25, pady=(20, 20))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="✓ Enregistrer le Paiement",
            fg_color="#0a84ff",
            hover_color="#0078d4",
            text_color="#ffffff",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=42,
            corner_radius=8,
            command=save_payment
        )
        save_btn.pack(fill="x", pady=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Annuler",
            fg_color="#e2e8f0",
            hover_color="#cbd5e1",
            text_color="#1e293b",
            font=ctk.CTkFont(size=12),
            height=36,
            corner_radius=8,
            command=dialog.destroy
        )
        cancel_btn.pack(fill="x")

    def _open_payment_history_dialog(self, student: dict):
        """Ouvre la fenêtre d'historique de paiements par étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Historique des paiements")
        dialog_width = min(720, max(560, int(self.screen_width * 0.6)))
        dialog_height = min(600, max(420, int(self.screen_height * 0.7)))
        
        # Centrer sur le dashboard
        dashboard_x = self.winfo_rootx()
        dashboard_y = self.winfo_rooty()
        dashboard_width = self.winfo_width()
        dashboard_height = self.winfo_height()
        
        center_x = dashboard_x + (dashboard_width - dialog_width) // 2
        center_y = dashboard_y + (dashboard_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{center_x}+{center_y}")
        dialog.grab_set()
        dialog.resizable(False, False)
        self._animate_window_open(dialog)

        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        student_number = student.get("student_number", "-")
        student_id = student.get("id")

        # === HEADER COLORÉ ===
        header = ctk.CTkFrame(dialog, fg_color="#6366f1", corner_radius=0)
        header.pack(fill="x", side="top")
        
        ctk.CTkLabel(
            header,
            text="🧾 Historique des Paiements",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(15, 8), padx=20)
        
        ctk.CTkLabel(
            header,
            text=f"{fullname} • #{student_number}",
            font=ctk.CTkFont(size=12),
            text_color="#e0e7ff"
        ).pack(pady=(0, 15), padx=20)

        # === CONTENU PRINCIPAL ===
        content = ctk.CTkFrame(dialog, fg_color="#f8f9fa")
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # Info access code
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=12)

        access_code = self.finance_service.get_latest_access_code(student_id)
        if access_code:
            code_text = f"Code actuel: {access_code.get('access_code')} ({access_code.get('access_type')})"
            code_color = "#10b981"
        else:
            code_text = "Code actuel: Aucun code généré"
            code_color = "#cbd5e1"

        ctk.CTkLabel(
            info_frame,
            text=code_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=code_color
        ).pack(anchor="w")

        # === TABLE ===
        table = ctk.CTkFrame(content, fg_color="#ffffff", corner_radius=8, border_width=1, border_color="#e2e8f0")
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
        faculty_names = sorted({f.get("faculty_name") for f in faculties_data if f.get("faculty_name")})
        faculties = ["Toutes"] + faculty_names
        faculty_combo = ctk.CTkComboBox(filter_frame, values=faculties, width=150, height=30)
        faculty_combo.set("Toutes")
        faculty_combo.pack(side="left", padx=10, pady=10)

        def render_faculty_stats(selected_faculty: str):
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            data = faculties_data
            if selected_faculty != "Toutes":
                data = [f for f in faculties_data if f.get("faculty_name") == selected_faculty]

            if not data:
                ctk.CTkLabel(
                    scroll_frame,
                    text="Aucune statistique disponible.",
                    font=ctk.CTkFont(size=12),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
                return

            for faculty in data:
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

        render_faculty_stats("Toutes")
        faculty_combo.configure(command=lambda value: render_faculty_stats(value))
    
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
    
    # ==================== STUDENT ACADEMIC DATA ====================
    
    def _show_student_academic_data(self):
        """Affiche l'interface de gestion des données académiques avec sélection hiérarchique"""
        self.current_view = "academic_data"
        self._set_main_scrollbar_visible(True)
        self._update_nav_buttons("academic_data")
        self.title_label.configure(text="📝 Gestion des Données Académiques")
        self._clear_content()
        
        # Initialiser les variables de sélection
        if not hasattr(self, 'academic_state'):
            self.academic_state = {
                'faculty_id': None,
                'department_id': None,
                'promotion_id': None,
                'selected_student': None,
                'filtered_students': []
            }
        
        # Container
        container = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"]
        )
        container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = ctk.CTkFrame(container, fg_color=self.colors["primary"], corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame,
            text="📚 Ajouter les Données Académiques par Étudiant",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack(anchor="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="Gestion des notes, documents et certificats pour chaque étudiant",
            font=ctk.CTkFont(size=11),
            text_color="#e8f4ff"
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Content frame
        content = ctk.CTkFrame(container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ==== LEFT COLUMN: Selection & Student Info ====
        left_column = ctk.CTkFrame(content, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # ---- CARD 1: Sélection Hiérarchique ----
        selection_card = ctk.CTkFrame(left_column, fg_color=self.colors["card_bg"], corner_radius=12)
        selection_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            selection_card,
            text="1️⃣ Sélectionner un Étudiant",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Sous-section: Hierarchie
        hierarchy_frame = ctk.CTkFrame(selection_card, fg_color="transparent")
        hierarchy_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # FACULTÉ
        ctk.CTkLabel(
            hierarchy_frame,
            text="Faculté *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        faculty_options = self._get_academic_faculties()
        faculty_names = [f['name'] for f in faculty_options]
        
        self.academic_faculty_combo = ctk.CTkComboBox(
            hierarchy_frame,
            values=faculty_names if faculty_names else ["Aucune faculté"],
            height=36,
            font=ctk.CTkFont(size=10),
            command=self._on_academic_faculty_selected
        )
        self.academic_faculty_combo.pack(fill="x", pady=(0, 12))
        if faculty_names:
            self.academic_faculty_combo.set(faculty_names[0])
            self.academic_state['faculty_id'] = next((f['id'] for f in faculty_options if f['name'] == faculty_names[0]), None)
        
        # DÉPARTEMENT
        ctk.CTkLabel(
            hierarchy_frame,
            text="Département *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.academic_dept_combo = ctk.CTkComboBox(
            hierarchy_frame,
            values=["Sélectionnez une faculté d'abord"],
            height=36,
            font=ctk.CTkFont(size=10),
            command=self._on_academic_department_selected
        )
        self.academic_dept_combo.pack(fill="x", pady=(0, 12))
        
        # PROMOTION
        ctk.CTkLabel(
            hierarchy_frame,
            text="Promotion *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.academic_promotion_combo = ctk.CTkComboBox(
            hierarchy_frame,
            values=["Sélectionnez un département d'abord"],
            height=36,
            font=ctk.CTkFont(size=10),
            command=self._on_academic_promotion_selected
        )
        self.academic_promotion_combo.pack(fill="x", pady=(0, 12))
        
        # RECHERCHE ÉTUDIANT
        ctk.CTkLabel(
            hierarchy_frame,
            text="Rechercher un Étudiant",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.academic_search_entry = ctk.CTkEntry(
            hierarchy_frame,
            placeholder_text="Nom, prénom ou numéro d'étudiant...",
            height=36,
            font=ctk.CTkFont(size=10)
        )
        self.academic_search_entry.pack(fill="x", pady=(0, 12))
        self.academic_search_entry.bind("<KeyRelease>", self._on_academic_search_changed)
        
        # ---- CARD 2: Liste des Étudiants ----
        students_list_card = ctk.CTkFrame(left_column, fg_color=self.colors["card_bg"], corner_radius=12)
        students_list_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            students_list_card,
            text="📋 Étudiants de la Promotion",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(10, 8))
        
        # Scrollable list
        self.academic_students_scroll = ctk.CTkScrollableFrame(
            students_list_card,
            fg_color=self.colors["hover"],
            corner_radius=8,
            scrollbar_button_color=self.colors["border"],
            width=300,
            height=120
        )
        self.academic_students_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # ---- CARD 3: Infos de l'étudiant sélectionné ----
        info_card = ctk.CTkFrame(left_column, fg_color=self.colors["hover"], corner_radius=12)
        info_card.pack(fill="x", pady=(0, 15))
        
        self.academic_info_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        self.academic_info_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            self.academic_info_frame,
            text="Aucun étudiant sélectionné",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_light"]
        ).pack(anchor="w")
        
        # ---- CARD 4: Données Académiques Ajoutées ----
        self.academic_data_card = ctk.CTkFrame(left_column, fg_color=self.colors["card_bg"], corner_radius=12)
        self.academic_data_card.pack(fill="x", pady=(0, 0))
        
        ctk.CTkLabel(
            self.academic_data_card,
            text="📊 Données Académiques Existantes",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        self.academic_display_frame = ctk.CTkFrame(self.academic_data_card, fg_color="transparent")
        self.academic_display_frame.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        
        ctk.CTkLabel(
            self.academic_display_frame,
            text="Les données s'afficheront ici...",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_light"]
        ).pack(pady=10)
        
        # ==== RIGHT COLUMN: Forms ====
        right_column = ctk.CTkFrame(content, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Tabs for different data types
        ctk.CTkLabel(
            right_column,
            text="2️⃣ Ajouter les Données",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 10))
        
        tabs_frame = ctk.CTkFrame(right_column, fg_color=self.colors["card_bg"], corner_radius=12)
        tabs_frame.pack(fill="both", expand=True)
        
        # Tab buttons
        tab_btn_frame = ctk.CTkFrame(tabs_frame, fg_color="transparent")
        tab_btn_frame.pack(fill="x", padx=15, pady=(15, 0))
        
        self.academic_active_tab = "grades"
        self.academic_tab_buttons = []
        
        tab_configs = [
            ("grades", "📊 Ajouter une Note"),
            ("documents", "📄 Ajouter un Document"),
        ]
        
        for tab_key, tab_label in tab_configs:
            btn = ctk.CTkButton(
                tab_btn_frame,
                text=tab_label,
                fg_color=self.colors["primary"] if tab_key == "grades" else "transparent",
                hover_color=self.colors["primary"],
                text_color=self.colors["text_white"] if tab_key == "grades" else self.colors["text_dark"],
                height=40,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda k=tab_key: self._switch_academic_tab(k, tabs_frame)
            )
            btn.pack(side="left", padx=3, expand=True, fill="x")
            self.academic_tab_buttons.append({"button": btn, "key": tab_key})
        
        # Tab content container
        self.academic_tab_content = ctk.CTkFrame(tabs_frame, fg_color="transparent")
        self.academic_tab_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Show initial tab
        self._show_academic_grades_form()
    
    # ========== MÉTHODES DE CHARGEMENT HIÉRARCHIQUE ==========
    
    def _get_academic_faculties(self):
        """Récupère les facultés actives"""
        try:
            return self.student_service.get_faculties()
        except Exception as e:
            logger.error(f"Erreur chargement facultés: {e}")
            return []
    
    def _on_academic_faculty_selected(self, faculty_name):
        """Callback lors de la sélection d'une faculté"""
        try:
            faculties = self._get_academic_faculties()
            faculty = next((f for f in faculties if f['name'] == faculty_name), None)
            
            if not faculty:
                return
            
            self.academic_state['faculty_id'] = faculty['id']
            self.academic_state['department_id'] = None
            self.academic_state['promotion_id'] = None
            self.academic_state['selected_student'] = None
            self.academic_state['filtered_students'] = []
            
            # Charger départements
            departments = self.student_service.get_departments_by_faculty(faculty['id'])
            dept_names = [d['name'] for d in departments]
            
            if dept_names:
                self.academic_dept_combo.configure(values=dept_names)
                self.academic_dept_combo.set(dept_names[0])
                self._on_academic_department_selected(dept_names[0])
            else:
                self.academic_dept_combo.configure(values=["Aucun département"])
                self.academic_dept_combo.set("Aucun département")
                self.academic_promotion_combo.configure(values=["Aucune promotion"])
                self._clear_academic_students_list()
        except Exception as e:
            logger.error(f"Erreur sélection faculté: {e}")
    
    def _on_academic_department_selected(self, dept_name):
        """Callback lors de la sélection d'un département"""
        try:
            if not self.academic_state['faculty_id'] or dept_name == "Aucun département":
                return
            
            faculties = self._get_academic_faculties()
            faculty = next((f for f in faculties if f['id'] == self.academic_state['faculty_id']), None)
            
            if not faculty:
                return
            
            departments = self.student_service.get_departments_by_faculty(faculty['id'])
            dept = next((d for d in departments if d['name'] == dept_name), None)
            
            if not dept:
                return
            
            self.academic_state['department_id'] = dept['id']
            self.academic_state['promotion_id'] = None
            self.academic_state['selected_student'] = None
            self.academic_state['filtered_students'] = []
            
            # Charger promotions
            promotions = self.student_service.get_promotions_by_department(dept['id'])
            promo_names = [f"{p['name']} ({p['year']})" for p in promotions]
            
            if promo_names:
                self.academic_promotion_combo.configure(values=promo_names)
                self.academic_promotion_combo.set(promo_names[0])
                self._on_academic_promotion_selected(promo_names[0])
            else:
                self.academic_promotion_combo.configure(values=["Aucune promotion"])
                self.academic_promotion_combo.set("Aucune promotion")
                self._clear_academic_students_list()
        except Exception as e:
            logger.error(f"Erreur sélection département: {e}")
    
    def _on_academic_promotion_selected(self, promo_name):
        """Callback lors de la sélection d'une promotion"""
        try:
            if not self.academic_state['department_id'] or promo_name == "Aucune promotion":
                self._clear_academic_students_list()
                return
            
            departments = self.student_service.get_departments_by_faculty(self.academic_state['faculty_id'])
            dept = next((d for d in departments if d['id'] == self.academic_state['department_id']), None)
            
            if not dept:
                return
            
            promotions = self.student_service.get_promotions_by_department(dept['id'])
            promo = next((p for p in promotions if f"{p['name']} ({p['year']})" == promo_name), None)
            
            if not promo:
                return
            
            self.academic_state['promotion_id'] = promo['id']
            self.academic_state['selected_student'] = None
            
            # Charger les étudiants de cette promotion
            self._update_academic_students_list()
        except Exception as e:
            logger.error(f"Erreur sélection promotion: {e}")
    
    def _update_academic_students_list(self):
        """Met à jour la liste des étudiants de la promotion"""
        try:
            students = self._get_academic_students_by_promotion()
            self.academic_state['filtered_students'] = students
            
            # Vider la liste
            self._clear_academic_students_list()
            
            # Remplir avec les nouveaux étudiants
            if students:
                for student in students:
                    self._create_academic_student_button(student)
            else:
                ctk.CTkLabel(
                    self.academic_students_scroll,
                    text="Aucun étudiant",
                    font=ctk.CTkFont(size=10),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
        except Exception as e:
            logger.error(f"Erreur mise à jour liste étudiants: {e}")
    
    def _get_academic_students_by_promotion(self, search_text=""):
        """Récupère les étudiants de la promotion active"""
        try:
            if not self.academic_state['promotion_id']:
                return []
            
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            query = """
                SELECT s.id, s.student_number, s.firstname, s.lastname, 
                       s.email, s.promotion_id, p.name as promotion_name
                FROM student s
                JOIN promotion p ON s.promotion_id = p.id
                WHERE s.promotion_id = %s AND s.is_active = 1
                ORDER BY s.lastname, s.firstname
            """
            
            students = conn.execute_query(query, (self.academic_state['promotion_id'],))
            
            # Filtrer par recherche si nécessaire
            if search_text.strip():
                search_lower = search_text.lower().strip()
                students = [s for s in students if (
                    search_lower in f"{s['firstname']} {s['lastname']}".lower() or
                    search_lower in s['student_number'].lower() or
                    search_lower in (s.get('email', '') or '').lower()
                )]
            
            return students
        except Exception as e:
            logger.error(f"Erreur récupération étudiants: {e}")
            return []
    
    def _on_academic_search_changed(self, event=None):
        """Callback lors de la saisie de recherche"""
        try:
            search_text = self.academic_search_entry.get()
            students = self._get_academic_students_by_promotion(search_text)
            self.academic_state['filtered_students'] = students
            
            # Vider et remplir la liste
            self._clear_academic_students_list()
            
            if students:
                for student in students:
                    self._create_academic_student_button(student)
            else:
                ctk.CTkLabel(
                    self.academic_students_scroll,
                    text="Aucun étudiant trouvé",
                    font=ctk.CTkFont(size=10),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
        except Exception as e:
            logger.error(f"Erreur recherche étudiant: {e}")
    
    def _create_academic_student_button(self, student):
        """Crée un bouton pour afficher un étudiant"""
        try:
            scrollable_frame = getattr(self.academic_students_scroll, "_scrollable_frame", self.academic_students_scroll)
            
            btn_frame = ctk.CTkButton(
                scrollable_frame,
                text=f"{student['student_number']} - {student['firstname']} {student['lastname']}",
                fg_color=self.colors["hover"],
                hover_color=self.colors["primary"],
                text_color=self.colors["text_dark"],
                height=32,
                font=ctk.CTkFont(size=10),
                command=lambda s=student: self._select_academic_student(s),
                anchor="w"
            )
            btn_frame.pack(fill="x", padx=5, pady=2)
        except Exception as e:
            logger.error(f"Erreur création bouton étudiant: {e}")
    
    def _clear_academic_students_list(self):
        """Vide la liste des étudiants"""
        try:
            scrollable_frame = getattr(self.academic_students_scroll, "_scrollable_frame", self.academic_students_scroll)
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
        except Exception as e:
            logger.error(f"Erreur nettoyage liste: {e}")
    
    def _select_academic_student(self, student):
        """Sélectionne un étudiant et affiche ses infos"""
        try:
            self.academic_state['selected_student'] = student
            self._display_academic_student_info(student)
        except Exception as e:
            logger.error(f"Erreur sélection étudiant: {e}")
    
    def _display_academic_student_info(self, student):
        """Affiche les infos élargis de l'étudiant avec les données académiques"""
        try:
            # Vider le frame d'infos
            for widget in self.academic_info_frame.winfo_children():
                widget.destroy()
            
            info_frame = ctk.CTkFrame(self.academic_info_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=0, pady=0)
            
            # Infos de base
            ctk.CTkLabel(
                info_frame,
                text=f"👤 {student['firstname']} {student['lastname']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["primary"]
            ).pack(anchor="w", pady=(0, 3))
            
            ctk.CTkLabel(
                info_frame,
                text=f"ID: {student['student_number']} | Email: {student.get('email', 'N/A')}",
                font=ctk.CTkFont(size=9),
                text_color=self.colors["text_dark"]
            ).pack(anchor="w", pady=(0, 8))
            
            # Afficher les données académiques en bas
            self._display_academic_data_for_student(student)
        except Exception as e:
            logger.error(f"Erreur affichage info étudiant: {e}")
    
    def _display_academic_data_for_student(self, student):
        """Affiche les notes et documents existants de l'étudiant"""
        try:
            # Vider le frame
            for widget in self.academic_display_frame.winfo_children():
                widget.destroy()
            
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            # Récupérer les notes (augmenté à 10 pour plus de contexte)
            grades_query = """
                SELECT * FROM academic_record 
                WHERE student_id = %s 
                ORDER BY exam_date DESC, id DESC LIMIT 10
            """
            grades = conn.execute_query(grades_query, (student['id'],))
            
            # Récupérer les documents (augmenté à 10)
            docs_query = """
                SELECT * FROM student_document 
                WHERE student_id = %s 
                ORDER BY id DESC LIMIT 10
            """
            documents = conn.execute_query(docs_query, (student['id'],))
            
            if not grades and not documents:
                empty_label = ctk.CTkLabel(
                    self.academic_display_frame,
                    text="Aucune donnée académique",
                    font=ctk.CTkFont(size=10),
                    text_color=self.colors["text_light"]
                )
                empty_label.pack(pady=10)
                self.academic_display_frame.update_idletasks()
                return
            
            # Afficher les notes
            if grades:
                grades_header = ctk.CTkLabel(
                    self.academic_display_frame,
                    text="📊 Dernières Notes",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=self.colors["primary"]
                )
                grades_header.pack(anchor="w", pady=(0, 5))
                
                for grade in grades:
                    grade_text = (
                        f"• {grade.get('course_name', 'N/A')} - "
                        f"{grade.get('grade', 'N/A')}/20 ({grade.get('grade_letter', 'N/A')}) "
                        f"| {grade.get('status', 'N/A')}"
                    )
                    grade_label = ctk.CTkLabel(
                        self.academic_display_frame,
                        text=grade_text,
                        font=ctk.CTkFont(size=9),
                        text_color=self.colors["text_dark"],
                        anchor="w",
                        justify="left"
                    )
                    grade_label.pack(anchor="w", pady=1, padx=5)
            
            # Espace entre sections
            if grades and documents:
                spacer = ctk.CTkLabel(
                    self.academic_display_frame,
                    text="",
                    font=ctk.CTkFont(size=6)
                )
                spacer.pack(pady=3)
            
            # Afficher les documents
            if documents:
                docs_header = ctk.CTkLabel(
                    self.academic_display_frame,
                    text="📄 Documents",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=self.colors["primary"]
                )
                docs_header.pack(anchor="w", pady=(5, 5) if grades else (0, 5))
                
                for doc in documents:
                    doc_text = f"• {doc.get('document_type', 'N/A')} - {doc.get('title', 'N/A')}"
                    doc_label = ctk.CTkLabel(
                        self.academic_display_frame,
                        text=doc_text,
                        font=ctk.CTkFont(size=9),
                        text_color=self.colors["text_dark"],
                        anchor="w",
                        justify="left"
                    )
                    doc_label.pack(anchor="w", pady=1, padx=5)
            
            # Forcer la mise à jour de l'affichage
            self.academic_display_frame.update_idletasks()
            self.academic_data_card.update_idletasks()
            
        except Exception as e:
            logger.error(f"Erreur affichage données académiques: {e}", exc_info=True)
    
    def _on_academic_student_selected(self, value):
        """Appelé quand un étudiant est sélectionné"""
        if not value or value == "Aucun étudiant disponible":
            return
        
        student_number = value.split(" - ")[0]
        selected_student = next(
            (s for s in self.academic_students_list if s['student_number'] == student_number),
            None
        )
        
        if selected_student:
            self._display_academic_student_info(selected_student)
    
    def _display_academic_student_info(self, student):
        """Affiche les info de l'étudiant sélectionné"""
        try:
            for widget in self.academic_info_frame.winfo_children():
                widget.destroy()
            
            info_frame = ctk.CTkFrame(self.academic_info_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=15, pady=12)
            
            ctk.CTkLabel(
                info_frame,
                text=f"👤 {student['firstname']} {student['lastname']}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["primary"]
            ).pack(anchor="w", pady=2)
            
            ctk.CTkLabel(
                info_frame,
                text=f"ID: {student['student_number']} | {student.get('promotion_name', 'N/A')}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(anchor="w", pady=2)
        except Exception as e:
            logger.error(f"Erreur affichage info étudiant académique: {e}")
    
    def _switch_academic_tab(self, tab_key, parent):
        """Change d'onglet dans les données académiques"""
        self.academic_active_tab = tab_key
        
        # Update button colors
        for tab_btn in self.academic_tab_buttons:
            if tab_btn["key"] == tab_key:
                tab_btn["button"].configure(
                    fg_color=self.colors["primary"],
                    text_color=self.colors["text_white"]
                )
            else:
                tab_btn["button"].configure(
                    fg_color="transparent",
                    text_color=self.colors["text_dark"]
                )
        
        # Clear content
        for widget in self.academic_tab_content.winfo_children():
            widget.destroy()
        
        # Show new tab content
        if tab_key == "grades":
            self._show_academic_grades_form()
        elif tab_key == "documents":
            self._show_academic_documents_form()
    
    def _show_academic_grades_form(self):
        """Affiche le formulaire pour ajouter une note"""
        form = ctk.CTkFrame(self.academic_tab_content, fg_color="transparent")
        form.pack(fill="both", expand=True)
        
        # Course name
        ctk.CTkLabel(
            form,
            text="Nom du Cours *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        course_entry = ctk.CTkEntry(
            form,
            placeholder_text="Ex: Programmation Python, Algorithmes...",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        course_entry.pack(fill="x", pady=(0, 15))
        
        # Code and Credits row
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1,
            text="Code du Cours",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        code_entry = ctk.CTkEntry(
            col1,
            placeholder_text="Ex: PRG101",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        code_entry.pack(fill="both")
        
        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2,
            text="Crédits ECTS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        credits_entry = ctk.CTkEntry(
            col2,
            placeholder_text="Ex: 3, 4...",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        credits_entry.pack(fill="both")
        
        # Grade row
        row2 = ctk.CTkFrame(form, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row2, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1,
            text="Note (sur 20) *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        grade_entry = ctk.CTkEntry(
            col1,
            placeholder_text="Ex: 15.5",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        grade_entry.pack(fill="both")
        
        col2 = ctk.CTkFrame(row2, fg_color="transparent")
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2,
            text="Statut",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        status_combo = ctk.CTkComboBox(
            col2,
            values=["RÉUSSI", "ÉCHOUÉ", "EN COURS"],
            height=40,
            font=ctk.CTkFont(size=11)
        )
        status_combo.pack(fill="both")
        status_combo.set("RÉUSSI")
        
        # Semester and Date row
        row3 = ctk.CTkFrame(form, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row3, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1,
            text="Semestre",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        semester_combo = ctk.CTkComboBox(
            col1,
            values=["1", "2", "Annuel"],
            height=40,
            font=ctk.CTkFont(size=11)
        )
        semester_combo.pack(fill="both")
        semester_combo.set("Annuel")
        
        col2 = ctk.CTkFrame(row3, fg_color="transparent")
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2,
            text="Date d'Examen",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        date_entry = ctk.CTkEntry(
            col2,
            placeholder_text="YYYY-MM-DD",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        date_entry.pack(fill="both")
        
        # Professeur
        ctk.CTkLabel(
            form,
            text="Professeur",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        professor_entry = ctk.CTkEntry(
            form,
            placeholder_text="Nom du professeur",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        professor_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Ajouter la Note",
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._add_academic_grade(course_entry, code_entry, credits_entry, grade_entry, status_combo, semester_combo, date_entry, professor_entry)
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Réinitialiser",
            fg_color="#6b7280",
            hover_color="#4b5563",
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: [
                course_entry.delete(0, "end"),
                code_entry.delete(0, "end"),
                credits_entry.delete(0, "end"),
                grade_entry.delete(0, "end"),
                date_entry.delete(0, "end"),
                professor_entry.delete(0, "end")
            ]
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _show_academic_documents_form(self):
        """Affiche le formulaire pour ajouter un document"""
        form = ctk.CTkFrame(self.academic_tab_content, fg_color="transparent")
        form.pack(fill="both", expand=True)
        
        # Document type
        ctk.CTkLabel(
            form,
            text="Type de Document *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        doc_type_combo = ctk.CTkComboBox(
            form,
            values=["LIVRE", "THÈSE", "RAPPORT", "CERTIFICAT", "DIPLÔME", "AUTRE"],
            height=40,
            font=ctk.CTkFont(size=11)
        )
        doc_type_combo.pack(fill="x", pady=(0, 15))
        doc_type_combo.set("CERTIFICAT")
        
        # Title
        ctk.CTkLabel(
            form,
            text="Titre du Document *",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        title_entry = ctk.CTkEntry(
            form,
            placeholder_text="Ex: Certificat de Complétion, Thèse...",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        title_entry.pack(fill="x", pady=(0, 15))
        
        # Category and Author
        row1 = ctk.CTkFrame(form, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row1, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1,
            text="Catégorie",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        category_entry = ctk.CTkEntry(
            col1,
            placeholder_text="Ex: Sciences, Littérature",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        category_entry.pack(fill="both")
        
        col2 = ctk.CTkFrame(row1, fg_color="transparent")
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2,
            text="Auteur",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        author_entry = ctk.CTkEntry(
            col2,
            placeholder_text="Nom de l'auteur",
            height=40,
            font=ctk.CTkFont(size=11)
        )
        author_entry.pack(fill="both")
        
        # Description
        ctk.CTkLabel(
            form,
            text="Description",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        description_text = ctk.CTkTextbox(
            form,
            height=80,
            font=ctk.CTkFont(size=11)
        )
        description_text.pack(fill="both", pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(form, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Ajouter le Document",
            fg_color=self.colors["success"],
            hover_color="#059669",
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: self._add_academic_document(doc_type_combo, title_entry, category_entry, author_entry, description_text)
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Réinitialiser",
            fg_color="#6b7280",
            hover_color="#4b5563",
            height=45,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: [
                title_entry.delete(0, "end"),
                category_entry.delete(0, "end"),
                author_entry.delete(0, "end"),
                description_text.delete("1.0", "end")
            ]
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _add_academic_grade(self, course_entry, code_entry, credits_entry, grade_entry, status_combo, semester_combo, date_entry, professor_entry):
        """Ajoute une note académique pour l'étudiant sélectionné"""
        try:
            # Vérifier si un étudiant est sélectionné
            if not self.academic_state['selected_student']:
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant dans la liste")
                return
            
            student = self.academic_state['selected_student']
            
            # Valider les entrées
            course_name = course_entry.get().strip()
            grade_str = grade_entry.get().strip()
            
            if not course_name:
                messagebox.showwarning("Attention", "Veuillez entrer le nom du cours")
                return
            
            if not grade_str:
                messagebox.showwarning("Attention", "Veuillez entrer la note")
                return
            
            # Convertir les valeurs
            try:
                grade = float(grade_str)
                credits = int(credits_entry.get()) if credits_entry.get() else 0
            except ValueError:
                messagebox.showerror("Erreur", "Note et crédits doivent être des nombres")
                return
            
            if grade < 0 or grade > 20:
                messagebox.showwarning("Attention", "La note doit être entre 0 et 20")
                return
            
            # Insérer dans la base de données
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            query = """
                INSERT INTO academic_record 
                (student_id, promotion_id, course_name, course_code, credits, grade, grade_letter, 
                 semester, exam_date, professor_name, status, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            grade_letter = self._get_grade_letter(grade)
            exam_date = date_entry.get() if date_entry.get() else None
            
            conn.execute_update(query, (
                student['id'],
                student['promotion_id'],
                course_name,
                code_entry.get() or None,
                credits,
                grade,
                grade_letter,
                self._map_semester_to_db(semester_combo.get()),
                exam_date,
                professor_entry.get() or None,
                self._map_status_to_db(status_combo.get()),
                None
            ))
            
            # Effacer les champs AVANT le message (pour que l'utilisateur les voie se vider)
            course_entry.delete(0, "end")
            code_entry.delete(0, "end")
            credits_entry.delete(0, "end")
            grade_entry.delete(0, "end")
            date_entry.delete(0, "end")
            professor_entry.delete(0, "end")
            
            messagebox.showinfo(
                "Succès",
                f"✅ Note ajoutée avec succès pour {course_name}!\n\n"
                f"Étudiant: {student['firstname']} {student['lastname']}\n"
                f"Note: {grade}/20 ({grade_letter})"
            )
            
            # Mettre à jour l'affichage des données APRÈS le message
            # Cela donne un meilleur retour utilisateur
            self._display_academic_data_for_student(student)
            
        except Exception as e:
            logger.error(f"Erreur ajout note académique: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _add_academic_document(self, doc_type_combo, title_entry, category_entry, author_entry, description_text):
        """Ajoute un document académique pour l'étudiant sélectionné"""
        try:
            # Vérifier si un étudiant est sélectionné
            if not self.academic_state['selected_student']:
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant dans la liste")
                return
            
            student = self.academic_state['selected_student']
            
            # Valider les entrées
            title = title_entry.get().strip()
            doc_type = doc_type_combo.get()
            
            if not title:
                messagebox.showwarning("Attention", "Veuillez entrer le titre du document")
                return
            
            # Insérer dans la base de données
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            query = """
                INSERT INTO student_document 
                (student_id, document_type, title, description, author, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            description = description_text.get("1.0", "end-1c").strip()
            
            conn.execute_update(query, (
                student['id'],
                self._map_doc_type_to_db(doc_type),
                title,
                description or None,
                author_entry.get() or None,
                category_entry.get() or None
            ))
            
            # Effacer les champs AVANT le message
            title_entry.delete(0, "end")
            category_entry.delete(0, "end")
            author_entry.delete(0, "end")
            description_text.delete("1.0", "end")
            
            messagebox.showinfo(
                "Succès",
                f"✅ Document ajouté avec succès!\n\n"
                f"Étudiant: {student['firstname']} {student['lastname']}\n"
                f"Type: {doc_type}\n"
                f"Titre: {title}"
            )
            
            # Mettre à jour l'affichage des données APRÈS le message
            self._display_academic_data_for_student(student)
            
        except Exception as e:
            logger.error(f"Erreur ajout document académique: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _get_grade_letter(self, grade):
        """Convertit une note numérique en lettre"""
        if grade >= 18:
            return "A"
        elif grade >= 16:
            return "B"
        elif grade >= 14:
            return "C"
        elif grade >= 12:
            return "D"
        else:
            return "F"
    
    def _map_status_to_db(self, status_fr):
        """Convertit le statut français en anglais pour la base de données"""
        mapping = {
            "RÉUSSI": "PASSED",
            "ÉCHOUÉ": "FAILED",
            "EN COURS": "IN_PROGRESS"
        }
        return mapping.get(status_fr, "PASSED")
    
    def _map_semester_to_db(self, semester_fr):
        """Convertit le semestre français en anglais pour la base de données"""
        mapping = {
            "Annuel": "Annual",
            "1": "1",
            "2": "2"
        }
        return mapping.get(semester_fr, "Annual")
    
    def _map_doc_type_to_db(self, doc_type_fr):
        """Convertit le type de document français en anglais pour la base de données"""
        mapping = {
            "LIVRE": "BOOK",
            "THÈSE": "THESIS",
            "RAPPORT": "REPORT",
            "CERTIFICAT": "CERTIFICATE",
            "DIPLÔME": "DIPLOMA",
            "AUTRE": "OTHER"
        }
        return mapping.get(doc_type_fr, "OTHER")
    
    # ==================== TRANSFERS VIEW ====================
    
    def _show_transfers(self):
        """Affiche la page de gestion des transferts inter-universitaires"""
        self.current_view = "transfers"
        self._set_main_scrollbar_visible(True)
        self._update_nav_buttons("transfers")
        self.title_label.configure(text="🔄 Transferts Inter-Universitaires")
        self._clear_content()
        
        # Tabs container
        tabs_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        tabs_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(tabs_container, fg_color=self.colors["card_bg"], corner_radius=10)
        tab_frame.pack(fill="x", pady=(0, 20))
        
        tab_buttons_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
        tab_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Active tab tracker
        self.active_transfer_tab = "outgoing"
        
        # Tab buttons
        tab_buttons = []
        tabs_data = [
            ("outgoing", "📤 Transferts Sortants", self._show_outgoing_transfers),
            ("incoming", "📥 Demandes Entrantes", self._show_incoming_transfers),
            ("history", "📜 Historique", self._show_transfer_history)
        ]
        
        for tab_key, tab_label, tab_callback in tabs_data:
            btn = ctk.CTkButton(
                tab_buttons_frame,
                text=tab_label,
                fg_color=self.colors["primary"] if tab_key == "outgoing" else "transparent",
                hover_color=self.colors["primary"],
                text_color=self.colors["text_white"] if tab_key == "outgoing" else self.colors["text_dark"],
                corner_radius=8,
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda k=tab_key, c=tab_callback, btns=tab_buttons: self._switch_transfer_tab(k, c, btns)
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")
            tab_buttons.append({"button": btn, "key": tab_key})
        
        # Content container for tab views
        self.transfer_tab_content = ctk.CTkFrame(tabs_container, fg_color="transparent")
        self.transfer_tab_content.pack(fill="both", expand=True)
        
        # Show initial tab
        self._show_outgoing_transfers()
    
    def _switch_transfer_tab(self, tab_key, callback, tab_buttons):
        """Change d'onglet dans l'interface de transferts"""
        self.active_transfer_tab = tab_key
        
        # Update button colors
        for tab_btn in tab_buttons:
            if tab_btn["key"] == tab_key:
                tab_btn["button"].configure(
                    fg_color=self.colors["primary"],
                    text_color=self.colors["text_white"]
                )
            else:
                tab_btn["button"].configure(
                    fg_color="transparent",
                    text_color=self.colors["text_dark"]
                )
        
        # Clear ALL content FIRST before showing new tab
        for widget in self.transfer_tab_content.winfo_children():
            widget.destroy()
        
        # Now show new content
        callback()
    
    def _show_outgoing_transfers(self):
        """Affiche l'interface pour initier un transfert sortant avec sélection en cascade"""
        # Initialize transfer state if not exists
        if not hasattr(self, 'transfer_state'):
            self.transfer_state = {
                'faculty_id': None,
                'department_id': None,
                'promotion_id': None,
                'selected_student': None,
                'filtered_students': []
            }
        
        container = ctk.CTkScrollableFrame(
            self.transfer_tab_content,
            fg_color=self.colors["card_bg"],
            corner_radius=12
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="📤 Initier un Transfert Sortant",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Info card
        info_card = ctk.CTkFrame(container, fg_color=self.colors["info"], corner_radius=10)
        info_card.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            info_card,
            text="ℹ️  Transférez les données académiques d'un étudiant vers une autre université.\n"
                 "Sélection : Faculté → Département → Promotion → Étudiant",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_white"],
            justify="left"
        ).pack(padx=15, pady=12)
        
        # Main content in two columns
        main_content = ctk.CTkFrame(container, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # LEFT COLUMN - Selection and Student List
        left_column = ctk.CTkFrame(main_content, fg_color="transparent")
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Card 1: Faculty, Department, Promotion Selection
        selection_card = ctk.CTkFrame(left_column, fg_color=self.colors["hover"], corner_radius=10)
        selection_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            selection_card,
            text="📍 Sélection Hiérarchique",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Faculty selection
        ctk.CTkLabel(
            selection_card,
            text="Faculté :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        faculties = self._get_transfer_faculties()
        faculty_names = [f['name'] for f in faculties]
        
        self.transfer_faculty_combo = ctk.CTkComboBox(
            selection_card,
            values=faculty_names if faculty_names else ["Aucune faculté"],
            width=300,
            height=32,
            font=ctk.CTkFont(size=11),
            command=self._on_transfer_faculty_selected
        )
        self.transfer_faculty_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Department selection
        ctk.CTkLabel(
            selection_card,
            text="Département :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        self.transfer_dept_combo = ctk.CTkComboBox(
            selection_card,
            values=["Sélectionner une faculté d'abord"],
            width=300,
            height=32,
            font=ctk.CTkFont(size=11),
            command=self._on_transfer_department_selected
        )
        self.transfer_dept_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Promotion selection
        ctk.CTkLabel(
            selection_card,
            text="Promotion :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        self.transfer_promotion_combo = ctk.CTkComboBox(
            selection_card,
            values=["Sélectionner un département d'abord"],
            width=300,
            height=32,
            font=ctk.CTkFont(size=11),
            command=self._on_transfer_promotion_selected
        )
        self.transfer_promotion_combo.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Card 2: Student List with Search
        students_card = ctk.CTkFrame(left_column, fg_color=self.colors["hover"], corner_radius=10)
        students_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            students_card,
            text="👥 Étudiants",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Search
        ctk.CTkLabel(
            students_card,
            text="🔍 Rechercher :",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        self.transfer_search_entry = ctk.CTkEntry(
            students_card,
            width=300,
            height=32,
            placeholder_text="Nom, Numéro ou Email"
        )
        self.transfer_search_entry.pack(anchor="w", padx=15, pady=(0, 10))
        self.transfer_search_entry.bind("<KeyRelease>", self._on_transfer_search_changed)
        
        # Students list frame
        self.transfer_students_scroll = ctk.CTkScrollableFrame(
            students_card,
            fg_color=self.colors["card_bg"],
            corner_radius=8,
            width=320,
            height=250
        )
        self.transfer_students_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # RIGHT COLUMN - Student Info and Transfer Form
        right_column = ctk.CTkFrame(main_content, fg_color="transparent")
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Card 3: Selected Student Info
        student_info_card = ctk.CTkFrame(right_column, fg_color=self.colors["hover"], corner_radius=10)
        student_info_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            student_info_card,
            text="📋 Informations Étudiant",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.transfer_student_info_frame = ctk.CTkFrame(student_info_card, fg_color=self.colors["card_bg"], corner_radius=8)
        self.transfer_student_info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            self.transfer_student_info_frame,
            text="Sélectionner un étudiant",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_light"]
        ).pack(padx=10, pady=10)
        
        # Card 4: Transfer Form
        form_card = ctk.CTkFrame(right_column, fg_color=self.colors["hover"], corner_radius=10)
        form_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            form_card,
            text="🎯 Détails du Transfert",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        form_scroll = ctk.CTkScrollableFrame(form_card, fg_color="transparent")
        form_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Destination university + API URL editable field
        ctk.CTkLabel(
            form_scroll,
            text="Université de destination :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))

        partners = self._get_partner_universities()
        partner_options = [f"{p['university_name']} ({p['university_code']}) - {p['country']}" for p in partners]
        self._partner_id_map = {f"{p['university_name']} ({p['university_code']}) - {p['country']}": p for p in partners}

        self.transfer_destination_combo = ctk.CTkComboBox(
            form_scroll,
            values=partner_options if partner_options else ["Aucune université partenaire"],
            width=300,
            height=32,
            font=ctk.CTkFont(size=11),
            command=self._on_partner_university_changed
        )
        self.transfer_destination_combo.pack(anchor="w", pady=(0, 5))
        if partner_options:
            self.transfer_destination_combo.set(partner_options[0])

        # API URL editable field
        ctk.CTkLabel(
            form_scroll,
            text="URL API de réception (modifiable) :",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 2))
        self.partner_api_url_var = tk.StringVar()
        self.partner_api_url_entry = ctk.CTkEntry(
            form_scroll,
            width=350,
            height=30,
            textvariable=self.partner_api_url_var
        )
        self.partner_api_url_entry.pack(anchor="w", pady=(0, 5))
        # Save button
        self.save_api_url_btn = ctk.CTkButton(
            form_scroll,
            text="💾 Sauvegarder l'URL API",
            fg_color=self.colors["primary"],
            hover_color="#2563eb",
            text_color=self.colors["text_white"],
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_save_partner_api_url
        )
        self.save_api_url_btn.pack(anchor="w", pady=(0, 15))

        # Initial fill of API URL
        self._update_partner_api_url_entry()

    def _on_partner_university_changed(self, value):
        self._update_partner_api_url_entry()

    def _update_partner_api_url_entry(self):
        # Met à jour le champ d'URL API selon l'université sélectionnée
        selected = self.transfer_destination_combo.get()
        partner = self._partner_id_map.get(selected)
        if partner:
            self.partner_api_url_var.set(partner.get('api_url') or "")
        else:
            self.partner_api_url_var.set("")

    def _on_save_partner_api_url(self):
        # Sauvegarde l'URL API modifiée pour l'université sélectionnée
        selected = self.transfer_destination_combo.get()
        partner = self._partner_id_map.get(selected)
        new_url = self.partner_api_url_var.get().strip()
        if not partner:
            ErrorManager.show_error("validation_error", "Aucune université sélectionnée.")
            return
        try:
            self.transfer_service.set_partner_api_url(partner['id'], new_url)
            partner['api_url'] = new_url
            ErrorManager.show_success("Succès", "URL API sauvegardée avec succès.")
        except Exception as e:
            logger.error(f"Erreur sauvegarde URL API: {e}", exc_info=True)
            ErrorManager.show_error("database_query", str(e))
        
        # Include documents checkbox
        self.transfer_include_docs_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form_scroll,
            text="✓ Inclure les documents et ouvrages",
            variable=self.transfer_include_docs_var,
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=10)
        
        # Notes
        ctk.CTkLabel(
            form_scroll,
            text="Notes (optionnel) :",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        self.transfer_notes_text = ctk.CTkTextbox(
            form_scroll,
            width=300,
            height=70,
            font=ctk.CTkFont(size=10)
        )
        self.transfer_notes_text.pack(anchor="w", pady=(0, 20))
        
        # Action buttons
        button_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        button_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="📤 Générer",
            fg_color=self.colors["success"],
            hover_color="#059669",
            text_color=self.colors["text_white"],
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._generate_transfer_package_action
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Rafraîchir",
            fg_color=self.colors["primary"],
            hover_color="#2563eb",
            text_color=self.colors["text_white"],
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._refresh_outgoing_transfers
        ).pack(side="left", padx=5)
    
    def _refresh_outgoing_transfers(self):
        """Rafraîchit la page des transferts sortants"""
        try:
            # Vider complètement le contenu
            for widget in self.transfer_tab_content.winfo_children():
                widget.destroy()
            
            # Réafficher le contenu
            self._show_outgoing_transfers()
        except Exception as e:
            logger.error(f"Erreur rafraîchissement transferts sortants: {e}")
    
    # ========== TRANSFER CASCADE METHODS ==========
    
    def _get_transfer_faculties(self):
        """Récupère toutes les facultés"""
        try:
            return self.student_service.get_faculties()
        except Exception as e:
            logger.error(f"Erreur récupération facultés: {e}", exc_info=True)
            return []
    
    def _on_transfer_faculty_selected(self, faculty_name):
        """Gère la sélection d'une faculté"""
        try:
            faculties = self._get_transfer_faculties()
            faculty = next((f for f in faculties if f['name'] == faculty_name), None)
            
            if faculty:
                self.transfer_state['faculty_id'] = faculty['id']
                
                # Charger les départements
                departments = self.student_service.get_departments_by_faculty(faculty['id'])
                dept_names = [d['name'] for d in departments]
                
                self.transfer_dept_combo.configure(values=dept_names if dept_names else ["Aucun département"])
                if dept_names:
                    self.transfer_dept_combo.set(dept_names[0])
                    self._on_transfer_department_selected(dept_names[0])
                else:
                    self.transfer_dept_combo.set("Aucun département")
                    self.transfer_promotion_combo.configure(values=["Aucune promotion"])
                    self._clear_transfer_students_list()
            
        except Exception as e:
            logger.error(f"Erreur sélection faculté: {e}", exc_info=True)
    
    def _on_transfer_department_selected(self, dept_name):
        """Gère la sélection d'un département"""
        try:
            if not self.transfer_state['faculty_id']:
                return
            
            faculties = self._get_transfer_faculties()
            faculty = next((f for f in faculties if f['id'] == self.transfer_state['faculty_id']), None)
            
            if faculty:
                departments = self.student_service.get_departments_by_faculty(faculty['id'])
                department = next((d for d in departments if d['name'] == dept_name), None)
                
                if department:
                    self.transfer_state['department_id'] = department['id']
                    
                    # Charger les promotions
                    promotions = self.student_service.get_promotions_by_department(department['id'])
                    promo_names = [p['name'] for p in promotions]
                    
                    self.transfer_promotion_combo.configure(values=promo_names if promo_names else ["Aucune promotion"])
                    if promo_names:
                        self.transfer_promotion_combo.set(promo_names[0])
                        self._on_transfer_promotion_selected(promo_names[0])
                    else:
                        self.transfer_promotion_combo.set("Aucune promotion")
                        self._clear_transfer_students_list()
        
        except Exception as e:
            logger.error(f"Erreur sélection département: {e}", exc_info=True)
    
    def _on_transfer_promotion_selected(self, promo_name):
        """Gère la sélection d'une promotion"""
        try:
            if not self.transfer_state['department_id']:
                return
            
            departments = self.student_service.get_departments_by_faculty(self.transfer_state['faculty_id'])
            department = next((d for d in departments if d['id'] == self.transfer_state['department_id']), None)
            
            if department:
                promotions = self.student_service.get_promotions_by_department(department['id'])
                promotion = next((p for p in promotions if p['name'] == promo_name), None)
                
                if promotion:
                    self.transfer_state['promotion_id'] = promotion['id']
                    
                    # Charger les étudiants
                    self._update_transfer_students_list()
                    
                    # Effacer le champ de recherche
                    if hasattr(self, 'transfer_search_entry'):
                        self.transfer_search_entry.delete(0, "end")
        
        except Exception as e:
            logger.error(f"Erreur sélection promotion: {e}", exc_info=True)
    
    def _update_transfer_students_list(self):
        """Met à jour la liste des étudiants"""
        try:
            students = self._get_transfer_students_by_promotion()
            self.transfer_state['filtered_students'] = students
            self._clear_transfer_students_list()
            
            if not students:
                # Afficher un message si aucun étudiant
                ctk.CTkLabel(
                    self.transfer_students_scroll,
                    text="Aucun étudiant actif\ndans cette promotion",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
                logger.info("Aucun étudiant trouvé pour cette promotion")
            else:
                for student in students:
                    btn = self._create_transfer_student_button(student)
                    btn.pack(fill="x", padx=5, pady=3)
                logger.info(f"{len(students)} étudiant(s) affiché(s)")
        
        except Exception as e:
            logger.error(f"Erreur mise à jour liste étudiants: {e}", exc_info=True)
    
    def _get_transfer_students_by_promotion(self, search_text=""):
        """Récupère les étudiants filtrés par promotion"""
        try:
            if not self.transfer_state['promotion_id']:
                return []
            
            from core.database.connection import DatabaseConnection
            db = DatabaseConnection()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, student_number, firstname, lastname, email FROM student
                WHERE promotion_id = %s AND is_active = TRUE
            """
            
            params = [self.transfer_state['promotion_id']]
            
            if search_text:
                query += """ AND (student_number LIKE %s OR firstname LIKE %s 
                            OR lastname LIKE %s OR email LIKE %s)"""
                search_like = f"%{search_text}%"
                params.extend([search_like, search_like, search_like, search_like])
            
            query += " ORDER BY firstname, lastname"
            
            cursor.execute(query, params)
            students = cursor.fetchall()
            
            logger.info(f"Étudiants trouvés pour promotion {self.transfer_state['promotion_id']}: {len(students)}")
            
            return students
        
        except Exception as e:
            logger.error(f"Erreur récupération étudiants: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                db.close_connection(conn)
    
    def _on_transfer_search_changed(self, event=None):
        """Gère la recherche en temps réel"""
        try:
            search_text = self.transfer_search_entry.get().strip()
            students = self._get_transfer_students_by_promotion(search_text)
            self.transfer_state['filtered_students'] = students
            self._clear_transfer_students_list()
            
            if not students:
                # Afficher un message si aucun résultat
                message = "Aucun résultat" if search_text else "Aucun étudiant actif\ndans cette promotion"
                ctk.CTkLabel(
                    self.transfer_students_scroll,
                    text=message,
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
            else:
                for student in students:
                    btn = self._create_transfer_student_button(student)
                    btn.pack(fill="x", padx=5, pady=3)
        
        except Exception as e:
            logger.error(f"Erreur recherche: {e}", exc_info=True)
    
    def _create_transfer_student_button(self, student):
        """Crée un bouton pour chaque étudiant"""
        student_text = f"{student['student_number']} - {student['firstname']} {student['lastname']}"
        
        btn = ctk.CTkButton(
            self.transfer_students_scroll,
            text=student_text,
            font=ctk.CTkFont(size=11),
            fg_color=self.colors["card_bg"],
            text_color=self.colors["text_dark"],
            hover_color=self.colors["primary"],
            height=35,
            corner_radius=8,
            command=lambda s=student: self._select_transfer_student(s)
        )
        
        return btn
    
    def _select_transfer_student(self, student):
        """Sélectionne un étudiant"""
        try:
            self.transfer_state['selected_student'] = student
            self._display_student_transfer_info(student)
        
        except Exception as e:
            logger.error(f"Erreur sélection étudiant: {e}", exc_info=True)
    
    def _clear_transfer_students_list(self):
        """Efface la liste des étudiants"""
        try:
            for widget in self.transfer_students_scroll.winfo_children():
                widget.destroy()
        except Exception as e:
            logger.error(f"Erreur suppression liste: {e}", exc_info=True)
    
    def _show_incoming_transfers(self):
        """Affiche les demandes de transfert entrantes en attente"""
        container = ctk.CTkScrollableFrame(
            self.transfer_tab_content,
            fg_color=self.colors["card_bg"],
            corner_radius=12
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="📥 Demandes de Transfert Entrantes",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Get pending requests
        pending_requests = self.transfer_service.get_pending_transfer_requests()
        
        if not pending_requests:
            # No requests
            no_data_frame = ctk.CTkFrame(container, fg_color=self.colors["hover"], corner_radius=10)
            no_data_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                no_data_frame,
                text="📭 Aucune demande de transfert en attente",
                font=ctk.CTkFont(size=16),
                text_color=self.colors["text_light"]
            ).pack(pady=40)
        else:
            # Display requests
            for request in pending_requests:
                self._create_transfer_request_card(container, request)
    
    def _create_transfer_request_card(self, parent, request):
        """Crée une carte pour une demande de transfert"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["hover"], corner_radius=12)
        card.pack(fill="x", padx=20, pady=10)
        
        # Header
        card_header = ctk.CTkFrame(card, fg_color="transparent")
        card_header.pack(fill="x", padx=15, pady=12)
        
        # Student name
        ctk.CTkLabel(
            card_header,
            text=f"👤 {request['external_firstname']} {request['external_lastname']}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Status badge
        status_frame = ctk.CTkFrame(card_header, fg_color=self.colors["warning"], corner_radius=15)
        status_frame.pack(side="right", padx=5)
        
        ctk.CTkLabel(
            status_frame,
            text="⏳ EN ATTENTE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack(padx=10, pady=3)
        
        # Details
        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        details_text = (
            f"📋 Code: {request['request_code']}\n"
            f"🏫 Université source: {request['source_university']} ({request.get('source_university_code', 'N/A')})\n"
            f"📧 Email: {request.get('external_email', 'N/A')}\n"
            f"☎️ Téléphone: {request.get('external_phone', 'N/A')}\n"
            f"📅 Date de demande: {request['requested_date'].strftime('%d/%m/%Y %H:%M') if request.get('requested_date') else 'N/A'}"
        )
        
        ctk.CTkLabel(
            details_frame,
            text=details_text,
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_dark"],
            justify="left"
        ).pack(anchor="w")
        
        # Action buttons
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkButton(
            button_frame,
            text="👁️ Voir Détails",
            fg_color=self.colors["info"],
            hover_color="#0891b2",
            text_color=self.colors["text_white"],
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda r=request: self._view_transfer_request_details(r)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="✅ Approuver",
            fg_color=self.colors["success"],
            hover_color="#059669",
            text_color=self.colors["text_white"],
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda r=request: self._approve_transfer_request(r)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Rejeter",
            fg_color=self.colors["danger"],
            hover_color="#dc2626",
            text_color=self.colors["text_white"],
            height=35,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda r=request: self._reject_transfer_request(r)
        ).pack(side="left", padx=5)
    
    def _show_transfer_history(self):
        """Affiche l'historique des transferts"""
        container = ctk.CTkScrollableFrame(
            self.transfer_tab_content,
            fg_color=self.colors["card_bg"],
            corner_radius=12
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header,
            text="📜 Historique des Transferts",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Get transfer history
        history = self.transfer_service.get_transfer_history(limit=50)
        
        if not history:
            # No history
            no_data_frame = ctk.CTkFrame(container, fg_color=self.colors["hover"], corner_radius=10)
            no_data_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                no_data_frame,
                text="📭 Aucun transfert enregistré",
                font=ctk.CTkFont(size=16),
                text_color=self.colors["text_light"]
            ).pack(pady=40)
        else:
            # Create table header
            table_header = ctk.CTkFrame(container, fg_color=self.colors["primary"], corner_radius=8)
            table_header.pack(fill="x", padx=20, pady=(0, 10))
            
            headers = ["Code", "Étudiant", "Type", "Université", "Date", "Statut", "Livraison", "Détails"]
            header_widths = [120, 150, 100, 200, 120, 100, 110, 80]
            
            header_row = ctk.CTkFrame(table_header, fg_color="transparent")
            header_row.pack(fill="x", padx=10, pady=8)
            
            for header_text, width in zip(headers, header_widths):
                ctk.CTkLabel(
                    header_row,
                    text=header_text,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=self.colors["text_white"],
                    width=width
                ).pack(side="left", padx=5)
            
            # Create table rows
            for i, transfer in enumerate(history):
                self._create_transfer_history_row(container, transfer, i)
    
    def _create_transfer_history_row(self, parent, transfer, index):
        """Crée une ligne d'historique de transfert"""
        bg_color = self.colors["card_bg"] if index % 2 == 0 else self.colors["hover"]
        
        row = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=8)
        row.pack(fill="x", padx=20, pady=2)
        
        row_content = ctk.CTkFrame(row, fg_color="transparent")
        row_content.pack(fill="x", padx=10, pady=8)
        
        # Data
        transfer_code = transfer.get('transfer_code', 'N/A')[:15] + "..." if len(transfer.get('transfer_code', '')) > 15 else transfer.get('transfer_code', 'N/A')
        student_name = f"{transfer.get('firstname', '')} {transfer.get('lastname', '')}".strip() or "N/A"
        transfer_type = "📤 Sortant" if transfer.get('transfer_type') == 'OUTGOING' else "📥 Entrant"
        university = transfer.get('destination_university', 'N/A') if transfer.get('transfer_type') == 'OUTGOING' else transfer.get('source_university', 'N/A')
        transfer_date = transfer['transfer_date'].strftime('%d/%m/%Y') if transfer.get('transfer_date') else 'N/A'
        
        # Status color
        status = transfer.get('status', 'N/A')
        status_colors = {
            'COMPLETED': self.colors['success'],
            'PENDING': self.colors['warning'],
            'IN_PROGRESS': self.colors['info'],
            'REJECTED': self.colors['danger'],
            'CANCELLED': self.colors['text_light']
        }
        status_color = status_colors.get(status, self.colors['text_light'])

        # Delivery status color
        delivery_status = transfer.get('delivery_status', 'non_envoye')
        delivery_colors = {
            'envoye': self.colors['success'],
            'echec': self.colors['danger'],
            'non_envoye': self.colors['warning']
        }
        delivery_color = delivery_colors.get(delivery_status, self.colors['text_light'])
        delivery_label = {
            'envoye': '✅ Envoyé',
            'echec': '❌ Échec',
            'non_envoye': '⏳ Non envoyé'
        }.get(delivery_status, delivery_status)

        # Columns
        widths = [120, 150, 100, 200, 120, 100, 110, 80]
        values = [transfer_code, student_name, transfer_type, university[:25], transfer_date]

        for value, width in zip(values, widths[:5]):
            ctk.CTkLabel(
                row_content,
                text=value,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"],
                width=width,
                anchor="w"
            ).pack(side="left", padx=5)

        # Status badge
        status_frame = ctk.CTkFrame(row_content, fg_color=status_color, corner_radius=10, width=100)
        status_frame.pack(side="left", padx=5)
        ctk.CTkLabel(
            status_frame,
            text=status,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack(padx=8, pady=3)

        # Delivery badge
        delivery_frame = ctk.CTkFrame(row_content, fg_color=delivery_color, corner_radius=10, width=110)
        delivery_frame.pack(side="left", padx=5)
        ctk.CTkLabel(
            delivery_frame,
            text=delivery_label,
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack(padx=8, pady=3)

        # Details button
        ctk.CTkButton(
            row_content,
            text="👁️",
            fg_color=self.colors["info"],
            hover_color="#0891b2",
            text_color=self.colors["text_white"],
            width=60,
            height=28,
            font=ctk.CTkFont(size=12),
            command=lambda t=transfer: self._view_transfer_history_details(t)
        ).pack(side="left", padx=5)
    
    # Helper methods for transfers
    
    def _get_all_students_for_transfer(self):
        """Récupère tous les étudiants actifs"""
        try:
            return self.student_service.get_all_students_with_finance()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des étudiants: {e}", exc_info=True)
            return []
    
    def _get_partner_universities(self):
        """Récupère les universités partenaires"""
        try:
            conn = self.transfer_service.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM partner_university 
                WHERE is_active = TRUE 
                ORDER BY university_name
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des universités: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.transfer_service.db.close_connection(conn)
    
    def _on_transfer_student_combo_changed(self, value):
        """Appelé quand la sélection du combo étudiant change"""
        try:
            if not value or value == "Aucun étudiant disponible":
                return
            
            student_number = value.split(" - ")[0]
            selected_student = next(
                (s for s in self.transfer_available_students if s['student_number'] == student_number),
                None
            )
            
            if selected_student:
                self._display_student_transfer_info(selected_student)
        except Exception as e:
            logger.error(f"Erreur changement combo étudiant: {e}", exc_info=True)
    
    def _on_transfer_student_selected(self, value, students):
        """Appelé quand un étudiant est sélectionné pour transfert"""
        student_number = value.split(" - ")[0]
        selected_student = next((s for s in students if s['student_number'] == student_number), None)
        
        if selected_student:
            self._display_student_transfer_info(selected_student)
    
    def _display_student_transfer_info(self, student):
        """Affiche les informations détaillées de l'étudiant sélectionné"""
        try:
            # Clear previous content
            for widget in self.transfer_student_info_frame.winfo_children():
                widget.destroy()
            
            # Get academic summary
            summary = self.transfer_service.get_student_academic_summary(student['id'])
            
            # Header with student info
            header_frame = ctk.CTkFrame(self.transfer_student_info_frame, fg_color="transparent")
            header_frame.pack(fill="x", padx=15, pady=(12, 8))
            
            student_name = f"{student['firstname']} {student['lastname']}"
            ctk.CTkLabel(
                header_frame,
                text=f"📋 {student_name}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=self.colors["primary"]
            ).pack(anchor="w")
            
            # Academic data
            data_frame = ctk.CTkFrame(self.transfer_student_info_frame, fg_color="transparent")
            data_frame.pack(fill="x", padx=15, pady=(0, 12))
            
            # Row 1: Number and Email
            row1 = ctk.CTkFrame(data_frame, fg_color="transparent")
            row1.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row1,
                text=f"Numéro: {student['student_number']}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(
                row1,
                text=f"Promotion: {student.get('promotion_name', 'N/A')}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left")
            
            # Row 2: Courses and Credits
            row2 = ctk.CTkFrame(data_frame, fg_color="transparent")
            row2.pack(fill="x", pady=3)
            
            courses = summary.get('total_courses', 0) or 0
            credits = summary.get('total_credits', 0) or 0
            average = summary.get('average_grade', 0)
            
            ctk.CTkLabel(
                row2,
                text=f"📚 Cours: {courses}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(
                row2,
                text=f"⭐ Crédits: {credits}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=(0, 20))
            
            avg_text = f"{float(average):.2f}" if average else "N/A"
            ctk.CTkLabel(
                row2,
                text=f"📊 Moyenne: {avg_text}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left")
            
            # Row 3: Documents
            docs = summary.get('total_documents', 0) or 0
            row3 = ctk.CTkFrame(data_frame, fg_color="transparent")
            row3.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row3,
                text=f"📄 Documents: {docs}",
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left")
            
        except Exception as e:
            logger.error(f"Erreur affichage info étudiant: {e}", exc_info=True)
            ctk.CTkLabel(
                self.transfer_student_info_frame,
                text="❌ Erreur lors de l'affichage des informations",
                font=ctk.CTkFont(size=11),
                text_color="#ef4444"
            ).pack(padx=15, pady=12)
    
    def _generate_transfer_package_action(self):
        """Génère et enregistre le package de transfert avec le système de cascade"""
        try:
            # Vérifier qu'un étudiant est sélectionné
            selected_student = self.transfer_state.get('selected_student')
            if not selected_student:
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant")
                return
            
            # Vérifier la destination
            dest_value = self.transfer_destination_combo.get()
            if not dest_value or dest_value == "Aucune université partenaire":
                messagebox.showwarning("Attention", "Veuillez sélectionner une université de destination")
                return
            
            try:
                dest_code = dest_value.split("(")[1].split(")")[0]
            except:
                messagebox.showerror("Erreur", "Format université invalide")
                return
            
            # Récupérer l'université partenaire
            partners = self._get_partner_universities()
            selected_partner = next((p for p in partners if p['university_code'] == dest_code), None)
            
            if not selected_partner:
                messagebox.showerror("Erreur", "Université introuvable")
                return
            
            # Récupérer les options
            include_docs = self.transfer_include_docs_var.get()
            notes = self.transfer_notes_text.get("1.0", "end-1c").strip()
            
            # Initier le transfert
            success, result = self.transfer_service.initiate_outgoing_transfer(
                student_id=selected_student['id'],
                destination_university=selected_partner['university_name'],
                destination_code=selected_partner['university_code'],
                initiated_by="Admin",
                include_documents=include_docs,
                notes=notes if notes else None
            )
            
            if success:
                # Envoi automatique à l'API partenaire
                delivery_status = "non envoyé"
                delivery_message = ""
                try:
                    api_url = selected_partner.get('api_url')
                    if api_url:
                        # Récupérer les données du transfert
                        transfer_data = self.transfer_service.get_transfer_package_by_code(result)
                        import json
                        from app.services.transfer.transfer_service import CustomJSONEncoder
                        headers = {'Content-Type': 'application/json'}
                        response = requests.post(api_url, data=json.dumps(transfer_data, cls=CustomJSONEncoder), headers=headers, timeout=10)
                        if response.status_code == 200:
                            delivery_status = "envoyé"
                            delivery_message = "✅ Données envoyées avec succès à l'API partenaire."
                        else:
                            delivery_status = "échec"
                            delivery_message = f"❌ Erreur lors de l'envoi à l'API partenaire: {response.status_code} {response.text}"
                    else:
                        delivery_message = "⚠️ Aucune URL API définie pour l'université partenaire."
                except Exception as ex:
                    delivery_status = "échec"
                    delivery_message = f"❌ Exception lors de l'envoi à l'API partenaire: {ex}"

                # Afficher le résultat à l'utilisateur
                messagebox.showinfo(
                    "Succès",
                    f"✅ Transfert créé avec succès!\n\n"
                    f"Code de transfert: {result}\n\n"
                    f"Statut de livraison: {delivery_status}\n{delivery_message}"
                )
                # Enregistrer le statut de livraison dans la base
                status_map = {"envoyé": "envoye", "échec": "echec", "non envoyé": "non_envoye"}
                self.transfer_service.update_delivery_status(result, status_map.get(delivery_status, "non_envoye"), delivery_message)
                self._refresh_outgoing_transfers()
            else:
                messagebox.showerror(
                    "Erreur",
                    f"❌ Impossible de créer le transfert:\n{result}"
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du package: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _generate_transfer_package(self, students, partners):
        """Génère et enregistre le package de transfert"""
        try:
            # Get selected student
            selected_value = self.transfer_student_combo.get()
            if not selected_value or selected_value == "Aucun étudiant disponible":
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant")
                return
            
            student_number = selected_value.split(" - ")[0]
            selected_student = next((s for s in students if s['student_number'] == student_number), None)
            
            if not selected_student:
                messagebox.showerror("Erreur", "Étudiant introuvable")
                return
            
            # Get selected destination
            dest_value = self.transfer_destination_combo.get()
            if not dest_value or dest_value == "Aucune université partenaire":
                messagebox.showwarning("Attention", "Veuillez sélectionner une université de destination")
                return
            
            dest_code = dest_value.split("(")[1].split(")")[0]
            selected_partner = next((p for p in partners if p['university_code'] == dest_code), None)
            
            if not selected_partner:
                messagebox.showerror("Erreur", "Université introuvable")
                return
            
            # Get options
            include_docs = self.transfer_include_docs_var.get()
            notes = self.transfer_notes_text.get("1.0", "end-1c").strip()
            
            # Initiate transfer
            success, result = self.transfer_service.initiate_outgoing_transfer(
                student_id=selected_student['id'],
                destination_university=selected_partner['university_name'],
                destination_code=selected_partner['university_code'],
                initiated_by="Admin",  # TODO: Use actual logged-in user
                include_documents=include_docs,
                notes=notes if notes else None
            )
            
            if success:
                messagebox.showinfo(
                    "Succès",
                    f"Transfert créé avec succès!\n\n"
                    f"Code de transfert: {result}\n\n"
                    f"Les données ont été enregistrées et peuvent être "
                    f"exportées vers l'université destinataire."
                )
                # Refresh the view
                self._show_outgoing_transfers()
            else:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible de créer le transfert:\n{result}"
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du package: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _view_transfer_request_details(self, request):
        """Affiche les détails d'une demande de transfert"""
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails - {request['request_code']}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Scroll frame
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=self.colors["card_bg"])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            scroll,
            text=f"Demande de Transfert - {request['request_code']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        # Parse JSON data
        import json
        
        try:
            if request.get('received_data_json'):
                transfer_data = json.loads(request['received_data_json'])
                
                # Display formatted data
                json_display = json.dumps(transfer_data, indent=2, ensure_ascii=False)
                
                text_widget = ctk.CTkTextbox(scroll, height=400, font=ctk.CTkFont(size=10))
                text_widget.pack(fill="both", expand=True, pady=10)
                text_widget.insert("1.0", json_display)
                text_widget.configure(state="disabled")
        except Exception as e:
            ctk.CTkLabel(
                scroll,
                text=f"Erreur lors du chargement des données: {e}",
                text_color=self.colors["danger"]
            ).pack(pady=20)
        
        # Close button
        ctk.CTkButton(
            scroll,
            text="Fermer",
            fg_color=self.colors["primary"],
            command=dialog.destroy,
            height=40
        ).pack(pady=10, fill="x")
    
    def _approve_transfer_request(self, request):
        """Approuve une demande de transfert entrante"""
        # Create approval dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Approuver le Transfert")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color=self.colors["card_bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text=f"✅ Approuver le Transfert",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text=f"Étudiant: {request['external_firstname']} {request['external_lastname']}\n"
                 f"Source: {request['source_university']}",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_dark"]
        ).pack(pady=10)
        
        # Select promotion
        ctk.CTkLabel(
            frame,
            text="Sélectionner la promotion de destination:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Get promotions
        promotions = self._get_all_promotions()
        promo_options = [f"{p['name']} - {p['department_name']}" for p in promotions]
        
        promo_combo = ctk.CTkComboBox(
            frame,
            values=promo_options if promo_options else ["Aucune promotion"],
            width=400,
            height=35
        )
        promo_combo.pack(padx=20, pady=(0, 15))
        if promo_options:
            promo_combo.set(promo_options[0])
        
        # Notes
        ctk.CTkLabel(
            frame,
            text="Notes d'approbation:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        notes_text = ctk.CTkTextbox(frame, height=80, width=400)
        notes_text.pack(padx=20, pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def do_approve():
            selected_promo = promo_combo.get()
            if not selected_promo or selected_promo == "Aucune promotion":
                messagebox.showwarning("Attention", "Veuillez sélectionner une promotion")
                return
            
            promo_name = selected_promo.split(" - ")[0]
            selected_promotion = next((p for p in promotions if p['name'] == promo_name), None)
            
            if not selected_promotion:
                messagebox.showerror("Erreur", "Promotion introuvable")
                return
            
            approval_notes = notes_text.get("1.0", "end-1c").strip()
            
            # Approve
            success, result = self.transfer_service.approve_incoming_transfer(
                request_id=request['id'],
                approved_by="Admin",  # TODO: Use actual logged-in user
                target_promotion_id=selected_promotion['id'],
                approval_notes=approval_notes if approval_notes else None
            )
            
            if success:
                messagebox.showinfo(
                    "Succès",
                    f"Transfert approuvé avec succès!\n\n"
                    f"ID Étudiant créé: {result}\n\n"
                    f"L'étudiant a été créé avec un mot de passe temporaire: ChangeMe123!"
                )
                dialog.destroy()
                self._show_incoming_transfers()
            else:
                messagebox.showerror("Erreur", f"Impossible d'approuver le transfert:\n{result}")
        
        ctk.CTkButton(
            button_frame,
            text="✅ Approuver",
            fg_color=self.colors["success"],
            hover_color="#059669",
            command=do_approve,
            height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            fg_color=self.colors["text_light"],
            hover_color="#64748b",
            command=dialog.destroy,
            height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _reject_transfer_request(self, request):
        """Rejette une demande de transfert"""
        # Create rejection dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rejeter le Transfert")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()
        
        frame = ctk.CTkFrame(dialog, fg_color=self.colors["card_bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="❌ Rejeter le Transfert",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            frame,
            text="Raison du rejet:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        reason_text = ctk.CTkTextbox(frame, height=100, width=400)
        reason_text.pack(padx=20, pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def do_reject():
            reason = reason_text.get("1.0", "end-1c").strip()
            if not reason:
                messagebox.showwarning("Attention", "Veuillez indiquer la raison du rejet")
                return
            
            success = self.transfer_service.reject_incoming_transfer(
                request_id=request['id'],
                rejected_by="Admin",  # TODO: Use actual logged-in user
                rejection_reason=reason
            )
            
            if success:
                messagebox.showinfo("Succès", "Demande de transfert rejetée")
                dialog.destroy()
                self._show_incoming_transfers()
            else:
                messagebox.showerror("Erreur", "Impossible de rejeter la demande")
        
        ctk.CTkButton(
            button_frame,
            text="❌ Rejeter",
            fg_color=self.colors["danger"],
            hover_color="#dc2626",
            command=do_reject,
            height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="Annuler",
            fg_color=self.colors["text_light"],
            hover_color="#64748b",
            command=dialog.destroy,
            height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _view_transfer_history_details(self, transfer):
        """Affiche les détails d'un transfert dans l'historique"""
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails - {transfer['transfer_code']}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=self.colors["card_bg"])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            scroll,
            text=f"Détails du Transfert - {transfer['transfer_code']}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        # Display transfer info
        info_text = (
            f"Type: {transfer['transfer_type']}\n"
            f"Étudiant: {transfer.get('firstname', '')} {transfer.get('lastname', '')}\n"
            f"Source: {transfer.get('source_university', 'N/A')}\n"
            f"Destination: {transfer.get('destination_university', 'N/A')}\n"
            f"Date: {transfer['transfer_date'].strftime('%d/%m/%Y %H:%M') if transfer.get('transfer_date') else 'N/A'}\n"
            f"Statut: {transfer.get('status', 'N/A')}\n"
            f"Notes transférées: {transfer.get('records_count', 0)}\n"
            f"Documents transférés: {transfer.get('documents_count', 0)}\n"
            f"Crédits totaux: {transfer.get('total_credits', 0)}\n"
        )
        
        ctk.CTkLabel(
            scroll,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_dark"],
            justify="left"
        ).pack(pady=10, anchor="w")
        
        # Close button
        ctk.CTkButton(
            scroll,
            text="Fermer",
            fg_color=self.colors["primary"],
            command=dialog.destroy,
            height=40
        ).pack(pady=10, fill="x")
    
    def _get_all_promotions(self):
        """Récupère toutes les promotions avec départements"""
        try:
            conn = self.transfer_service.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT p.id, p.name, d.name as department_name, f.name as faculty_name
                FROM promotion p
                LEFT JOIN department d ON p.department_id = d.id
                LEFT JOIN faculty f ON d.faculty_id = f.id
                WHERE p.is_active = TRUE
                ORDER BY f.name, d.name, p.name
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des promotions: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.transfer_service.db.close_connection(conn)
    
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
