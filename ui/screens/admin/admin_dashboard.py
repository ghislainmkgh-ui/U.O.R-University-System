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
        
        self.colors = self._get_color_palette()
        ctk.set_appearance_mode("Dark" if self.theme.current_theme == "dark" else "Light")
        
        self.pack(fill="both", expand=True)
        self._create_ui()
    def _register_wrap(self, label, ratio: float = 0.35, min_width: int = 280, max_width: int = 600):
        """Enregistre un label pour ajuster automatiquement son wraplength"""
        self._responsive_labels.append((label, ratio, min_width, max_width))

    def _on_resize(self, _event=None):
        if not self._responsive_labels:
            return
        width = self.winfo_width() or self.screen_width
        for label, ratio, min_w, max_w in self._responsive_labels:
            try:
                wrap = int(max(min_w, min(max_w, width * ratio)))
                label.configure(wraplength=wrap)
            except Exception:
                continue

    def _get_screen_profile(self):
        """Détermine le mode d'affichage selon la taille d'écran"""
        if self.screen_width < 1200:
            return "small", 0.9
        if self.screen_width < 1400:
            return "tablet", 0.95
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
        view_map = {
            "dashboard": self._show_dashboard,
            "students": self._show_students,
            "finance": self._show_finance,
            "access_logs": self._show_access_logs,
            "reports": self._show_reports,
            "academic_years": self._show_academic_years
        }
        view_map.get(self.current_view, self._show_dashboard)()
    
    def _create_ui(self):
        """Crée l'interface moderne du dashboard"""
        self.configure(fg_color=self.colors["main_bg"])
        
        # Container principal
        container = ctk.CTkFrame(self, fg_color=self.colors["main_bg"])
        container.pack(fill="both", expand=True)
        
        # === SIDEBAR MODERNE ===
        sidebar = ctk.CTkFrame(container, fg_color=self.colors["sidebar_bg"], width=280, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo et titre
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", pady=(20, 10))
        logo_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            logo_frame,
            text="U.O.R",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack()
        
        ctk.CTkLabel(
            logo_frame,
            text="ADMIN DASHBOARD",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_light"]
        ).pack()
        
        # Séparateur
        ctk.CTkFrame(sidebar, height=1, fg_color="#334155").pack(fill="x", padx=20, pady=15)
        
        # Navigation
        nav_items = [
            ("📊", "dashboard", self._t("dashboard", "Dashboard"), self._show_dashboard),
            ("👥", "students", self._t("students", "Étudiants"), self._show_students),
            ("💰", "finance", self._t("finance", "Finances"), self._show_finance),
            ("📚", "academic_years", self._t("academic_years", "Années Acad."), self._show_academic_years),
            ("📋", "access_logs", self._t("access_logs", "Logs d'Accès"), self._show_access_logs),
            ("📈", "reports", self._t("reports", "Rapports"), self._show_reports),
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
            self.nav_buttons.append((btn, key))
        
        # Spacer
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)
        
        # Logout
        ctk.CTkButton(
            sidebar,
            text="🚪  Déconnexion",
            fg_color=self.colors["danger"],
            hover_color="#dc2626",
            text_color=self.colors["text_white"],
            command=self._on_logout,
            height=45,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(fill="x", padx=15, pady=(10, 20))
        
        # === MAIN CONTENT ===
        self.main_content = ctk.CTkFrame(container, fg_color=self.colors["main_bg"])
        self.main_content.pack(side="right", fill="both", expand=True)
        self.main_content.bind("<Configure>", self._on_resize)
        
        # Top bar avec titre et langue
        topbar = ctk.CTkFrame(self.main_content, fg_color="transparent", height=70)
        topbar.pack(fill="x", padx=25, pady=(20, 0))
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
        self.content_container.pack(fill="both", expand=True, padx=25, pady=20)

        self.content_frame = ctk.CTkScrollableFrame(
            self.content_container,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["text_light"]
        )
        self.content_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Afficher la vue active
        self._render_current_view()
    
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

    def _make_card_clickable(self, card, command):
        """Rend une carte cliquable avec effet hover"""
        if not command:
            return
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
        """Crée une carte de statistique colorée"""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=12, height=140)
        card.pack_propagate(False)
        hover_color = self._shade_color(color, 0.9)
        
        # En-tête avec titre et icône
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        header_label = ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_white"]
        )
        header_label.pack(side="left")
        
        icon_label = ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(side="right")
        
        # Valeur
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors["text_white"]
        )
        value_label.pack(anchor="w", padx=20, pady=(0, 15))
        
        # Action
        action_btn = ctk.CTkButton(
            card,
            text=action_text,
            fg_color="transparent",
            hover_color="#0a0a0a",
            text_color=self.colors["text_white"],
            font=ctk.CTkFont(size=11),
            height=25,
            corner_radius=6,
            command=action_command
        )
        action_btn.pack(anchor="w", padx=20, pady=(0, 15))

        if action_command:
            def on_enter(_):
                card.configure(fg_color=hover_color)

            def on_leave(_):
                card.configure(fg_color=color)

            def on_click(_):
                action_command()

            for widget in (card, header, header_label, icon_label, value_label):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
        
        return card

    def _configure_table_columns(self, frame, column_weights):
        """Configure la grille des colonnes pour un tableau"""
        for idx, weight in enumerate(column_weights):
            frame.grid_columnconfigure(idx, weight=weight)

    def _create_table_header(self, parent, headers, column_weights, padx=15, pady=10):
        """Crée un header de tableau aligné"""
        header_frame = ctk.CTkFrame(parent, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))

        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor="w"
            ).grid(row=0, column=col, sticky="ew", padx=padx, pady=pady)

        self._configure_table_columns(header_frame, column_weights)
        return header_frame

    def _populate_table_row(self, row, values, column_weights, text_colors=None, font_sizes=None,
                            font_weights=None, anchors=None, padx=15, pady=8):
        """Ajoute des cellules alignées dans une ligne"""
        for col, value in enumerate(values):
            color = text_colors[col] if text_colors else self.colors["text_dark"]
            size = font_sizes[col] if font_sizes else 10
            weight = font_weights[col] if font_weights else "normal"
            anchor = anchors[col] if anchors else "w"

            ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=size, weight=weight),
                text_color=color,
                anchor=anchor
            ).grid(row=0, column=col, sticky="ew", padx=padx, pady=pady)

        self._configure_table_columns(row, column_weights)

    def _populate_table_row_with_offset(self, row, values, column_weights, start_col=0,
                                        text_colors=None, font_sizes=None, font_weights=None,
                                        anchors=None, padx=15, pady=8):
        """Ajoute des cellules alignées avec un décalage de colonne"""
        self._configure_table_columns(row, column_weights)
        for idx, value in enumerate(values):
            color = text_colors[idx] if text_colors else self.colors["text_dark"]
            size = font_sizes[idx] if font_sizes else 10
            weight = font_weights[idx] if font_weights else "normal"
            anchor = anchors[idx] if anchors else "w"

            ctk.CTkLabel(
                row,
                text=value,
                font=ctk.CTkFont(size=size, weight=weight),
                text_color=color,
                anchor=anchor
            ).grid(row=0, column=start_col + idx, sticky="ew", padx=padx, pady=pady)
    
    def _update_nav_buttons(self, active_key):
        """Met à jour le style du menu actif"""
        for btn, key in self.nav_buttons:
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
        
        # Stats d'une ligne
        stats_row_info = ctk.CTkFrame(info_card, fg_color="transparent")
        stats_row_info.pack(fill="x", padx=25, pady=10)
        
        ctk.CTkLabel(
            stats_row_info,
            text=f"👥 Total: {total_students}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["primary"]
        ).pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(
            stats_row_info,
            text=f"✅ Éligibles: {eligible_students}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["success"]
        ).pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(
            stats_row_info,
            text=f"❌ Non éligibles: {non_eligible_students}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors["danger"]
        ).pack(side="left")
        
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
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"]
        ).pack(anchor="w", padx=25, pady=(0, 10))
        
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

        for i, (title, value, icon, color, action, command) in enumerate(academic_stats):
            stat_card = self._create_stat_card(stats_row, title, value, icon, color, action, action_command=command)
            stat_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0 if i == len(academic_stats)-1 else 5))
        
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
        header_frame = ctk.CTkFrame(table_frame, fg_color=self.colors["border"], corner_radius=8)
        header_frame.pack(fill="x", padx=10, pady=10)
        headers = ["Étudiant", "ID", "Action", "Heure"]
        column_weights = [3, 1, 2, 1]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor="w"
            ).grid(row=0, column=col, sticky="ew", padx=15, pady=8)
        self._configure_table_columns(header_frame, column_weights)
        
        # Lignes du tableau
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
                padx=15,
                pady=5
            )
        
        # Résumé Financier
        financial_card = self._create_card(row3, width=380)
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
        """Affiche la page Étudiants"""
        self.current_view = "students"
        self._clear_content()
        self._update_nav_buttons("students")
        self.title_label.configure(text=self._t("students_title", "Gestion des Étudiants"))
        self.subtitle_label.configure(text=self._t("students_subtitle", "Gestion et suivi des étudiants"))
        
        # === HEADER ===
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text=f"👥 {self._t('students_title', 'Gestion des Étudiants')}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")

        add_btn = ctk.CTkButton(
            header,
            text=f"➕ {self._t('add_student', 'Ajouter étudiant')}",
            fg_color=self.colors["primary"],
            hover_color=self.colors["info"],
            text_color=self.colors["text_white"],
            height=32,
            corner_radius=8,
            command=self._open_add_student_dialog
        )
        add_btn.pack(side="right")
        
        # Stats rapides
        stats_frame = ctk.CTkFrame(header, fg_color="transparent")
        stats_frame.pack(side="right")
        
        total = self.dashboard_service.get_total_students()
        eligible = self.dashboard_service.get_eligible_students()
        non_eligible = self.dashboard_service.get_non_eligible_students()
        
        ctk.CTkLabel(
            stats_frame,
            text=f"Total: {total} | Éligibles: {eligible} | Non-éligibles: {non_eligible}",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"]
        ).pack()
        
        # === TABLEAU ÉTUDIANTS ===
        table_card = self._create_card(self.content_frame)
        table_card.pack(fill="both", expand=True)
        
        # Recherche
        search_frame = ctk.CTkFrame(table_card, fg_color=self.colors["hover"], corner_radius=8)
        search_frame.pack(fill="x", padx=25, pady=(20, 15))
        
        ctk.CTkLabel(
            search_frame,
            text=f"🔍 {self._t('search', 'Recherche')}: ",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(15, 10), pady=8)
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text=self._t("search_placeholder", "Nom, ID ou email..."),
            height=30,
            border_color=self.colors["border"]
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=8)

        # Filtre par année académique
        years = self.academic_year_service.get_years()
        year_values = ["Toutes"] + [y.get("year_name") or y.get("name") for y in years if (y.get("year_name") or y.get("name"))]
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}
        year_filter = ctk.CTkComboBox(
            search_frame,
            values=year_values,
            width=180,
            height=30
        )
        year_filter.set("Toutes")
        year_filter.pack(side="right", padx=(0, 15), pady=8)
        
        # Tableau header
        headers = ["Photo", "Nom Complet", "ID Étudiant", "Email", "Statut Paiement", "Éligibilité", "Solde restant ($)", "Action"]
        column_weights = [1, 3, 1, 3, 2, 1, 2, 1]
        header_frame = ctk.CTkFrame(table_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        header_anchors = ["center", "w", "w", "w", "center", "center", "e", "center"]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=header_anchors[col]
            ).grid(row=0, column=col, sticky="ew", padx=15, pady=10)
        self._configure_table_columns(header_frame, column_weights)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        students_data = self.student_service.get_all_students_with_finance()

        def render_students(filter_text: str = ""):
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            query = filter_text.lower().strip()
            filtered = []
            selected_year = year_filter.get()
            selected_year_id = year_map.get(selected_year) if selected_year != "Toutes" else None
            for student in students_data:
                fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
                student_number = student.get('student_number', '-')
                email = student.get('email') or "-"
                haystack = f"{fullname} {student_number} {email}".lower()
                if selected_year_id and student.get("academic_year_id") and student.get("academic_year_id") != selected_year_id:
                    continue
                if not query or query in haystack:
                    filtered.append(student)

            if not filtered:
                ctk.CTkLabel(
                    scroll_frame,
                    text=self._t("no_students", "Aucun étudiant trouvé."),
                    font=ctk.CTkFont(size=12),
                    text_color=self.colors["text_light"]
                ).pack(pady=20)
                return

            for student in filtered:
                row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
                row.pack(fill="x", pady=4)

                self._configure_table_columns(row, column_weights)

                fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
                student_number = student.get('student_number', '-')
                email = student.get('email') or "-"
                photo_path = student.get('passport_photo_path')
                photo_blob = student.get('passport_photo_blob')
                amount_paid = Decimal(str(student.get('amount_paid') or 0))
                threshold_required = Decimal(str(student.get('threshold_required') or 0))
                is_eligible = bool(student.get('is_eligible')) or (threshold_required > 0 and amount_paid >= threshold_required)
                remaining_amount = threshold_required - amount_paid
                if remaining_amount < 0:
                    remaining_amount = Decimal("0")

                if amount_paid <= 0:
                    payment_status = "Non payé"
                elif threshold_required > 0 and amount_paid < threshold_required:
                    payment_status = "Partiellement"
                else:
                    payment_status = "Payé"

                eligibility_text = "✅ Éligible" if is_eligible else "❌ Non"

                payment_color = self.colors["success"] if payment_status == "Payé" else (self.colors["warning"] if payment_status == "Partiellement" else self.colors["danger"])
                eligibility_color = self.colors["success"] if is_eligible else self.colors["danger"]

                self._render_photo_cell(row, 0, photo_path=photo_path, photo_blob=photo_blob, size=(40, 50))

                row_values = [fullname, student_number, email, payment_status, eligibility_text, self._format_usd(remaining_amount)]
                row_colors = [self.colors["text_dark"], self.colors["text_light"], self.colors["text_light"], payment_color, eligibility_color, self.colors["text_light"]]
                row_weights = ["normal", "normal", "normal", "normal", "bold", "normal"]
                row_anchors = ["w", "w", "w", "center", "center", "e"]
                self._populate_table_row_with_offset(
                    row,
                    row_values,
                    column_weights,
                    start_col=1,
                    text_colors=row_colors,
                    font_weights=row_weights,
                    anchors=row_anchors,
                    padx=15,
                    pady=6
                )

                action_frame = ctk.CTkFrame(row, fg_color="transparent")
                action_frame.grid(row=0, column=7, sticky="e", padx=10, pady=6)

                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="Modifier",
                    width=90,
                    height=24,
                    fg_color=self.colors["info"],
                    hover_color="#0891b2",
                    text_color=self.colors["text_white"],
                    command=lambda s=student: self._open_edit_student_dialog(s)
                )
                edit_btn.pack(side="top", pady=(0, 4))

                pay_btn = ctk.CTkButton(
                    action_frame,
                    text="Paiement",
                    width=90,
                    height=24,
                    fg_color=self.colors["primary"],
                    hover_color="#2563eb",
                    text_color=self.colors["text_white"],
                    command=lambda s=student: self._open_payment_dialog(s)
                )
                pay_btn.pack(side="top")

                history_btn = ctk.CTkButton(
                    action_frame,
                    text="Historique",
                    width=90,
                    height=24,
                    fg_color=self.colors["warning"],
                    hover_color="#f59e0b",
                    text_color=self.colors["text_white"],
                    command=lambda s=student: self._open_payment_history_dialog(s)
                )
                history_btn.pack(side="top", pady=(4, 0))

        render_students()
        search_entry.bind("<KeyRelease>", lambda event: render_students(search_entry.get()))
        year_filter.configure(command=lambda _value: render_students(search_entry.get()))

    def _open_add_student_dialog(self):
        """Ouvre la fenêtre d'inscription d'un nouvel étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Inscription Étudiant")
        dialog_width = min(620, max(520, int(self.screen_width * 0.5)))
        dialog_height = min(820, max(700, int(self.screen_height * 0.8)))
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        self._animate_window_open(dialog)

        ctk.CTkLabel(
            dialog,
            text="➕ Nouvel Étudiant",
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

        def add_labeled_entry(label_text, placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(fields_frame, text=label_text, font=self._font(12))
            label.grid(row=row, column=col, sticky="w", padx=5, pady=(8, 4))
            entry = ctk.CTkEntry(fields_frame, placeholder_text=placeholder)
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=5)
            return entry

        student_number_entry = add_labeled_entry("Numéro étudiant", "Ex: STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry("Prénom", "Ex: Jean", row=0, col=1)
        lastname_entry = add_labeled_entry("Nom", "Ex: Dupont", row=2, col=0)
        email_entry = add_labeled_entry("Email", "Ex: jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry("Téléphone WhatsApp", "Ex: +243123456789", row=4, col=0)

        threshold_entry = add_labeled_entry("Seuil financier requis ($)", "Optionnel si année académique active", row=4, col=1)

        # Année académique (saisie manuelle)
        years = self.academic_year_service.get_years()
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}

        ctk.CTkLabel(fields_frame, text="Année académique", font=self._font(12)).grid(row=6, column=0, sticky="w", padx=5, pady=(8, 4))
        year_entry = ctk.CTkEntry(fields_frame, placeholder_text="Ex: 2024-2025")
        year_entry.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5)

        faculty_entry = add_labeled_entry("Faculté", "Ex: Informatique / INF", row=8, col=0)
        department_entry = add_labeled_entry("Département", "Ex: Génie Informatique / G.I", row=8, col=1)
        promotion_entry = add_labeled_entry("Promotion", "Ex: L3-LMD/G.I", row=10, col=0, col_span=2)

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

        def save_student():
            student_number = student_number_entry.get().strip()
            firstname = firstname_entry.get().strip()
            lastname = lastname_entry.get().strip()
            email = email_entry.get().strip()
            phone_number = phone_entry.get().strip()
            faculty_label = faculty_entry.get().strip()
            department_label = department_entry.get().strip()
            promotion_label = promotion_entry.get().strip()
            threshold_text = threshold_entry.get().strip()
            selected_year_name = year_entry.get().strip()
            selected_year_id = year_map.get(selected_year_name) if selected_year_name else None
            photo_path = photo_path_var.get().strip()

            if not all([student_number, firstname, lastname, email, phone_number, faculty_label, department_label, promotion_label, photo_path, selected_year_name]):
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

            threshold_required = None
            if threshold_text:
                try:
                    threshold_required = Decimal(threshold_text)
                except Exception:
                    messagebox.showerror("Erreur", "Seuil financier invalide.")
                    return
            else:
                active_year = self.academic_year_service.get_active_year()
                if not active_year:
                    threshold_required = Decimal("0")

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

            # Envoyer une notification de bienvenue à l'étudiant
            try:
                active_year = self.academic_year_service.get_active_year() if not threshold_required else None
                if not threshold_required and active_year:
                    threshold_required = Decimal(str(active_year.get('threshold_amount') or 0))
                    final_fee_value = Decimal(str(active_year.get('final_fee') or threshold_required))
                else:
                    final_fee_value = threshold_required if threshold_required else Decimal("0")
                
                self.notification_service.send_welcome_notification(
                    student_email=email,
                    student_phone=phone_number,
                    student_name=f"{firstname} {lastname}",
                    student_number=student_number,
                    threshold_required=float(threshold_required) if threshold_required else 0.0,
                    final_fee=float(final_fee_value)
                )
            except Exception as e:
                logger.warning(f"Failed to send welcome notification: {e}")

            messagebox.showinfo("Succès", "Étudiant enregistré avec succès.")
            dialog.destroy()
            self._show_students()

        button_row = ctk.CTkFrame(form, fg_color="transparent")
        button_row.pack(fill="x", pady=(10, 16))

        save_btn = ctk.CTkButton(
            button_row,
            text="Valider",
            fg_color=self.colors["success"],
            hover_color=self.colors["primary"],
            height=self._scaled(36),
            command=save_student
        )
        save_btn.pack(fill="x")

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

                if self.finance_service.record_payment(student_id, amount_usd):
                    messagebox.showinfo("Succès", "Paiement enregistré.")
                    dialog.destroy()
                    self._show_students()
                else:
                    messagebox.showerror("Erreur", "Échec de l'enregistrement du paiement.")
            except Exception:
                messagebox.showerror("Erreur", "Montant invalide.")

        ctk.CTkButton(
            dialog,
            text="Enregistrer",
            fg_color=self.colors["success"],
            hover_color=self.colors["primary"],
            height=self._scaled(36),
            command=save_payment
        ).pack(fill="x", padx=20, pady=(5, 15))

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
        weights = [2, 1, 1]
        header_row = ctk.CTkFrame(table, fg_color=self.colors["border"], corner_radius=8)
        header_row.pack(fill="x", padx=10, pady=10)
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_row,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor="w"
            ).grid(row=0, column=col, sticky="ew", padx=10, pady=6)
        self._configure_table_columns(header_row, weights)

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
        self._esp32_status_label.configure(text=f"Statut: {status.text}", text_color=status.color)
    
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
        
        for i, (value, label, color_key) in enumerate(kpis):
            color_map = {"green": self.colors["success"], "blue": self.colors["info"], "orange": self.colors["warning"], "red": self.colors["danger"]}
            kpi_card = ctk.CTkFrame(kpi_frame, fg_color=color_map[color_key], corner_radius=8, height=100)
            kpi_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0 if i == 3 else 5))
            kpi_card.pack_propagate(False)
            self._make_card_clickable(kpi_card, self._show_finance)
            
            ctk.CTkLabel(kpi_card, text=value, font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["text_white"]).pack(expand=True)
            ctk.CTkLabel(kpi_card, text=label, font=ctk.CTkFont(size=10), text_color=self.colors["text_white"]).pack()
        
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
        column_weights = [1, 3, 1, 2, 2, 1, 1]
        header_frame = ctk.CTkFrame(table_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        header_anchors = ["center", "w", "w", "e", "e", "center", "center"]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=header_anchors[col]
            ).grid(row=0, column=col, sticky="ew", padx=15, pady=10)
        self._configure_table_columns(header_frame, column_weights)
        
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

            self._configure_table_columns(row, column_weights)

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
            row_anchors = ["w", "w", "e", "e", "center", "center"]
            self._populate_table_row_with_offset(
                row,
                row_values,
                column_weights,
                start_col=1,
                text_colors=row_colors,
                font_weights=row_weights,
                anchors=row_anchors
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
        
        for i, (value, label, color) in enumerate(stat_items):
            stat_card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=8, height=80)
            stat_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0 if i == 2 else 5))
            stat_card.pack_propagate(False)
            self._make_card_clickable(stat_card, self._show_access_logs)
            
            ctk.CTkLabel(stat_card, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_white"]).pack(expand=True)
            ctk.CTkLabel(stat_card, text=label, font=ctk.CTkFont(size=11), text_color=self.colors["text_white"]).pack()
        
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
        column_weights = [1, 3, 1, 2, 1, 1, 1, 1, 1]
        header_frame = ctk.CTkFrame(table_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        header_anchors = ["center", "w", "w", "w", "center", "center", "center", "center", "e"]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=header_anchors[col]
            ).grid(row=0, column=col, sticky="ew", padx=8, pady=10)
        self._configure_table_columns(header_frame, column_weights)
        
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

            self._configure_table_columns(row, column_weights)

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
            row_anchors = ["w", "w", "w", "center", "center", "center", "center", "e"]
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
        column_weights = [1, 2, 2, 1, 1, 1, 2]
        header_frame = ctk.CTkFrame(report_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        header_anchors = ["center", "w", "w", "center", "center", "center", "e"]
        for col, header_text in enumerate(headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=header_anchors[col]
            ).grid(row=0, column=col, sticky="ew", padx=15, pady=10)
        self._configure_table_columns(header_frame, column_weights)
        
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

            self._configure_table_columns(row, column_weights)
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
            row_anchors = ["w", "w", "center", "center", "center", "e"]
            self._populate_table_row_with_offset(
                row,
                row_values,
                column_weights,
                start_col=1,
                text_colors=row_colors,
                font_weights=row_weights,
                anchors=row_anchors
            )
    
    def _show_academic_years(self):
        """Affiche la gestion des années académiques"""
        self.current_view = "academic_years"
        self._clear_content()
        self._update_nav_buttons("academic_years")
        self.title_label.configure(text=self._t("academic_years_title", "Années Académiques"))
        self.subtitle_label.configure(text=self._t("academic_years_subtitle", "Gestion des seuils financiers et périodes d'examens"))
        
        # === Section: Année Académique Active ===
        active_year = self.academic_year_service.get_active_year()
        
        year_card = self._create_card(self.content_frame, height=200)
        year_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            year_card,
            text="📚 Année Académique Active",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        if active_year:
            # Frame pour les infos
            info_frame = ctk.CTkFrame(year_card, fg_color=self.colors["border"], corner_radius=8)
            info_frame.pack(fill="x", padx=25, pady=(0, 15))
            
            # Année
            year_row = ctk.CTkFrame(info_frame, fg_color="transparent", height=40)
            year_row.pack(fill="x", padx=15, pady=10)
            year_row.pack_propagate(False)
            ctk.CTkLabel(year_row, text="Année:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left")
            ctk.CTkLabel(year_row, text=active_year['year_name'], font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]).pack(side="left", padx=(10, 0))
            
            # Seuil
            threshold_row = ctk.CTkFrame(info_frame, fg_color="transparent", height=40)
            threshold_row.pack(fill="x", padx=15, pady=10)
            threshold_row.pack_propagate(False)
            ctk.CTkLabel(threshold_row, text="Seuil Financier:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left")
            ctk.CTkLabel(threshold_row, text=f"{self._format_usd(active_year['threshold_amount'])}", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["warning"]).pack(side="left", padx=(10, 0))
            
            # Frais finaux
            fee_row = ctk.CTkFrame(info_frame, fg_color="transparent", height=40)
            fee_row.pack(fill="x", padx=15, pady=10)
            fee_row.pack_propagate(False)
            ctk.CTkLabel(fee_row, text="Frais Finaux:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left")
            ctk.CTkLabel(fee_row, text=f"{self._format_usd(active_year['final_fee'])}", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["success"]).pack(side="left", padx=(10, 0))
            
            # Validité partielle
            validity_row = ctk.CTkFrame(info_frame, fg_color="transparent", height=40)
            validity_row.pack(fill="x", padx=15, pady=(10, 15))
            validity_row.pack_propagate(False)
            ctk.CTkLabel(validity_row, text="Validité (paiement partiel):", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left")
            ctk.CTkLabel(validity_row, text=f"{active_year['partial_valid_days']} jours", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["info"]).pack(side="left", padx=(10, 0))
        else:
            ctk.CTkLabel(year_card, text="❌ Aucune année académique active", font=ctk.CTkFont(size=12), text_color=self.colors["danger"]).pack(anchor="w", padx=25, pady=10)
        
        # === Section: Mettre à jour les Seuils ===
        threshold_card = self._create_card(self.content_frame)
        threshold_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            threshold_card,
            text="⚙️ Mettre à jour les Seuils Financiers",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))

        channel_status = self.notification_service.get_channel_status()
        email_status = "✅" if channel_status.get("email_configured") else "❌"
        whatsapp_status = "✅" if channel_status.get("whatsapp_configured") else "❌"
        ctk.CTkLabel(
            threshold_card,
            text=f"Notifications: Email {email_status} • WhatsApp {whatsapp_status}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors["info"] if channel_status.get("email_configured") or channel_status.get("whatsapp_configured") else self.colors["warning"]
        ).pack(anchor="w", padx=25, pady=(0, 10))
        
        # Form pour mettre à jour
        form_frame = ctk.CTkFrame(threshold_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=25, pady=(0, 20))
        
        # Nouveau seuil
        ctk.CTkLabel(form_frame, text="Nouveau Seuil ($):", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(anchor="w", pady=(5, 2))
        new_threshold_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: 1000", height=35, corner_radius=6)
        new_threshold_entry.pack(fill="x", pady=(0, 15))
        if active_year:
            new_threshold_entry.insert(0, f"{self._fc_to_usd(active_year['threshold_amount']):.2f}")
        
        # Nouveaux frais finaux
        ctk.CTkLabel(form_frame, text="Nouveaux Frais Finaux ($):", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(anchor="w", pady=(5, 2))
        new_fee_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: 2000", height=35, corner_radius=6)
        new_fee_entry.pack(fill="x", pady=(0, 20))
        if active_year:
            new_fee_entry.insert(0, f"{self._fc_to_usd(active_year['final_fee']):.2f}")
        
        # Buttons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        ctk.CTkButton(
            button_frame,
            text="💾 Mettre à jour",
            fg_color=self.colors["primary"],
            hover_color="#2563eb",
            text_color=self.colors["text_white"],
            command=lambda: self._update_thresholds(
                new_threshold_entry.get(),
                new_fee_entry.get(),
                active_year['academic_year_id'] if active_year else None
            ),
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        ctk.CTkButton(
            button_frame,
            text="📢 Prévisualiser Notifications",
            fg_color=self.colors["info"],
            hover_color="#0891b2",
            text_color=self.colors["text_white"],
            command=lambda: self._preview_notifications(new_threshold_entry.get(), new_fee_entry.get()),
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", fill="x", expand=True)

        # === Section: Frais par Promotion ===
        promo_card = self._create_card(self.content_frame)
        promo_card.pack(fill="both", expand=True, pady=(0, 20))

        ctk.CTkLabel(
            promo_card,
            text="🎓 Frais Académiques par Promotion",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))

        promo_headers = ["Promotion", "Département", "Année", "Frais ($)", "Action"]
        promo_weights = [3, 3, 1, 1, 1]
        header_frame = ctk.CTkFrame(promo_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        promo_anchors = ["w", "w", "center", "e", "center"]
        for col, header_text in enumerate(promo_headers):
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=promo_anchors[col]
            ).grid(row=0, column=col, sticky="ew", padx=15, pady=10)
        self._configure_table_columns(header_frame, promo_weights)

        promo_scroll = ctk.CTkScrollableFrame(promo_card, fg_color="transparent")
        promo_scroll.pack(fill="both", expand=True, padx=25, pady=(15, 20))

        promotions = self.student_service.get_promotions_with_fees()
        if not promotions:
            ctk.CTkLabel(
                promo_scroll,
                text="Aucune promotion trouvée.",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"]
            ).pack(pady=20)
        else:
            for promo in promotions:
                row = ctk.CTkFrame(promo_scroll, fg_color=self.colors["hover"], corner_radius=6)
                row.pack(fill="x", pady=4)
                self._configure_table_columns(row, promo_weights)

                fee_value = promo.get('fee_usd') or 0

                ctk.CTkLabel(
                    row,
                    text=promo.get('name') or "-",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_dark"],
                    anchor="w"
                ).grid(row=0, column=0, sticky="ew", padx=15, pady=6)

                ctk.CTkLabel(
                    row,
                    text=promo.get('department_name') or "-",
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_light"],
                    anchor="w"
                ).grid(row=0, column=1, sticky="ew", padx=15, pady=6)

                ctk.CTkLabel(
                    row,
                    text=str(promo.get('year') or "-"),
                    font=ctk.CTkFont(size=11),
                    text_color=self.colors["text_dark"],
                    anchor="center"
                ).grid(row=0, column=2, sticky="ew", padx=15, pady=6)

                fee_entry = ctk.CTkEntry(row, width=120)
                fee_entry.insert(0, f"{Decimal(str(fee_value)):.2f}")
                fee_entry.grid(row=0, column=3, sticky="e", padx=15, pady=6)

                def make_save(promotion_id, entry_widget):
                    def _save():
                        try:
                            value = Decimal(entry_widget.get().strip())
                            if value < 0:
                                raise ValueError
                            if self.student_service.update_promotion_fee(promotion_id, value):
                                messagebox.showinfo("Succès", "Frais mis à jour.")
                            else:
                                messagebox.showerror("Erreur", "Échec de mise à jour.")
                        except Exception:
                            messagebox.showerror("Erreur", "Montant invalide.")
                    return _save

                save_btn = ctk.CTkButton(
                    row,
                    text="Enregistrer",
                    width=110,
                    fg_color=self.colors["primary"],
                    hover_color="#2563eb",
                    text_color=self.colors["text_white"],
                    command=make_save(promo.get('id'), fee_entry)
                )
                save_btn.grid(row=0, column=4, sticky="e", padx=15, pady=6)
        
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
                column_weights = [3, 1, 1, 1]
                header_frame = ctk.CTkFrame(exam_card, fg_color=self.colors["border"], corner_radius=0)
                header_frame.pack(fill="x", padx=25, pady=(0, 0))
                header_anchors = ["w", "center", "center", "e"]
                for col, header_text in enumerate(headers):
                    ctk.CTkLabel(
                        header_frame,
                        text=header_text,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.colors["text_dark"],
                        anchor=header_anchors[col]
                    ).grid(row=0, column=col, sticky="ew", padx=15, pady=10)
                self._configure_table_columns(header_frame, column_weights)
                
                # Liste des périodes
                scroll_frame = ctk.CTkScrollableFrame(exam_card, fg_color="transparent")
                scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
                
                for period in exam_periods:
                    start = datetime.strptime(str(period['start_date']), "%Y-%m-%d")
                    end = datetime.strptime(str(period['end_date']), "%Y-%m-%d")
                    duration = (end - start).days
                    
                    row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
                    row.pack(fill="x", pady=4)

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
                        anchors=row_anchors
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
            
            # Recharger
            self._show_academic_years()
            
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
        self.destroy()
