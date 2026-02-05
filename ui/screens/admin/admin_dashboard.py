"""Dashboard administrateur moderne - Style SB Admin Pro"""
import customtkinter as ctk
import logging
from datetime import datetime
from decimal import Decimal
from tkinter import filedialog, messagebox, StringVar
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from app.services.dashboard_service import DashboardService
from app.services.student.student_service import StudentService
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.face_recognition_service import FaceRecognitionService
from app.services.finance.finance_service import FinanceService
from app.services.finance.academic_year_service import AcademicYearService
from app.services.integration.notification_service import NotificationService
from core.models.student import Student

logger = logging.getLogger(__name__)


class AdminDashboard(ctk.CTkToplevel):
    """Tableau de bord administrateur moderne avec design professionnel"""
    
    def __init__(self, parent, language: str = "FR", theme: ThemeManager = None):
        super().__init__(parent)
        
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
        
        self.title("U.O.R - Administration Dashboard")
        self.geometry("1600x900")
        self.state('zoomed')  # Maximiser la fenêtre
        
        # Couleurs du thème moderne
        self.colors = {
            "sidebar_bg": "#1e293b",      # Bleu foncé sidebar
            "main_bg": "#f8fafc",         # Gris très clair background
            "card_bg": "#ffffff",         # Blanc pour les cartes
            "primary": "#3b82f6",         # Bleu moderne
            "success": "#10b981",         # Vert
            "warning": "#f59e0b",         # Orange
            "danger": "#ef4444",          # Rouge
            "info": "#06b6d4",            # Cyan
            "text_dark": "#1e293b",       # Texte foncé
            "text_light": "#64748b",      # Texte clair
            "text_white": "#ffffff",      # Texte blanc
            "border": "#e2e8f0",          # Bordure
            "hover": "#f1f5f9"            # Hover
        }
        
        self._create_ui()
    
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
            ("📊", "dashboard", "Dashboard", self._show_dashboard),
            ("👥", "students", "Étudiants", self._show_students),
            ("💰", "finance", "Finances", self._show_finance),
            ("�", "academic_years", "Années Acad.", self._show_academic_years),
            ("�📋", "access_logs", "Logs d'Accès", self._show_access_logs),
            ("📈", "reports", "Rapports", self._show_reports),
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
        
        # Top bar avec titre et langue
        topbar = ctk.CTkFrame(self.main_content, fg_color="transparent", height=70)
        topbar.pack(fill="x", padx=25, pady=(20, 0))
        topbar.pack_propagate(False)
        
        # Titre à gauche
        title_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="Dashboard",
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
        
        # Sélecteur de langue à droite
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
        self.lang_switch.set("FR")
        self.lang_switch.pack(side="left", padx=(5, 15), pady=10)
        
        # Content scrollable
        self.content_frame = ctk.CTkScrollableFrame(
            self.main_content,
            fg_color="transparent",
            scrollbar_button_color=self.colors["border"],
            scrollbar_button_hover_color=self.colors["text_light"]
        )
        self.content_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Afficher le dashboard par défaut
        self._show_dashboard()
    
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
    
    def _create_stat_card(self, parent, title, value, icon, color, action_text):
        """Crée une carte de statistique colorée"""
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=12, height=140)
        card.pack_propagate(False)
        
        # En-tête avec titre et icône
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_white"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            header,
            text=icon,
            font=ctk.CTkFont(size=20)
        ).pack(side="right")
        
        # Valeur
        ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors["text_white"]
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Action
        action_btn = ctk.CTkButton(
            card,
            text=action_text,
            fg_color="transparent",
            hover_color="#0a0a0a",
            text_color=self.colors["text_white"],
            font=ctk.CTkFont(size=11),
            height=25,
            corner_radius=6
        )
        action_btn.pack(anchor="w", padx=20, pady=(0, 15))
        
        return card
    
    def _update_nav_buttons(self, active_key):
        """Met à jour le style du menu actif"""
        for btn, key in self.nav_buttons:
            if key == active_key:
                btn.configure(fg_color=self.colors["primary"])
            else:
                btn.configure(fg_color="transparent")
    
    def _show_dashboard(self):
        """Affiche le dashboard principal avec données académiques"""
        self._clear_content()
        self._update_nav_buttons("dashboard")
        
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
        ctk.CTkLabel(
            info_card,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_light"],
            wraplength=350,
            justify="left"
        ).pack(anchor="w", padx=25, pady=(0, 15))
        
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
            ("Total Étudiants", str(total_students), "👥", self.colors["primary"], "Voir tous"),
            ("Accès Accordés", str(access_granted), "✅", self.colors["success"], "Voir logs"),
            ("Revenus Collectés", f"RWF {revenue:,.0f}", "💰", self.colors["warning"], "Détails"),
            ("Accès Refusés", str(access_denied), "❌", self.colors["danger"], "Rapports")
        ]
        
        for i, (title, value, icon, color, action) in enumerate(academic_stats):
            stat_card = self._create_stat_card(stats_row, title, value, icon, color, action)
            stat_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0 if i == len(academic_stats)-1 else 5))
        
        # === ROW 3: GRAPHIQUES ET DÉTAILS ===
        row3 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row3.pack(fill="both", expand=True)
        
        # Historique d'Accès Détaillé
        access_card = self._create_card(row3)
        access_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
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
        
        for header_text in ["Étudiant", "ID", "Action", "Heure"]:
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=15, pady=8)
        
        # Lignes du tableau
        for activity in activities:
            row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=10, pady=3)
            
            ctk.CTkLabel(
                row_frame,
                text=activity['student'],
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=15, pady=5, fill="x", expand=True)
            
            ctk.CTkLabel(
                row_frame,
                text=activity['id'],
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_light"]
            ).pack(side="left", padx=15, pady=5)
            
            action_color = self.colors["success"] if "accordé" in activity['action'] else self.colors["danger"]
            ctk.CTkLabel(
                row_frame,
                text=activity['action'],
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=action_color
            ).pack(side="left", padx=15, pady=5)
            
            time_str = activity['timestamp'].strftime("%H:%M") if hasattr(activity['timestamp'], 'strftime') else str(activity['timestamp'])[-8:-3]
            ctk.CTkLabel(
                row_frame,
                text=time_str,
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_light"]
            ).pack(side="right", padx=15, pady=5)
        
        # Résumé Financier
        financial_card = self._create_card(row3, width=380)
        financial_card.pack(side="right", fill="y", padx=(5, 0))
        financial_card.pack_propagate(False)
        
        ctk.CTkLabel(
            financial_card,
            text="💵 Résumé Financier",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Données financières
        financial_data = [
            (f"RWF {revenue:,.0f}", "Revenus Totaux", "green"),
            (f"RWF {revenue * 0.85:,.0f}", "Paiements Vérifiés", "blue"),
            (f"RWF {revenue * 0.15:,.0f}", "En Attente", "orange"),
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
    
    def _show_students(self):
        """Affiche la page Étudiants"""
        self._clear_content()
        self._update_nav_buttons("students")
        
        # === HEADER ===
        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header,
            text="👥 Gestion des Étudiants",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(side="left")

        add_btn = ctk.CTkButton(
            header,
            text="➕ Ajouter étudiant",
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
            text="🔍 Recherche:",
            font=ctk.CTkFont(size=12),
            text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(15, 10), pady=8)
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Nom, ID ou email...",
            height=30,
            border_color=self.colors["border"]
        )
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=8)
        
        # Tableau header
        header_frame = ctk.CTkFrame(table_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        
        headers = ["Nom Complet", "ID Étudiant", "Email", "Statut Paiement", "Éligibilité"]
        for header_text in headers:
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=15, pady=10, fill="x", expand=True)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        students_data = self.student_service.get_all_students_with_finance()

        if not students_data:
            ctk.CTkLabel(
                scroll_frame,
                text="Aucun étudiant trouvé.",
                font=ctk.CTkFont(size=12),
                text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        for student in students_data:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=4)

            fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
            student_number = student.get('student_number', '-')
            email = student.get('email') or "-"
            amount_paid = Decimal(str(student.get('amount_paid') or 0))
            threshold_required = Decimal(str(student.get('threshold_required') or 0))
            is_eligible = bool(student.get('is_eligible')) or (threshold_required > 0 and amount_paid >= threshold_required)

            if amount_paid <= 0:
                payment_status = "Non payé"
            elif threshold_required > 0 and amount_paid < threshold_required:
                payment_status = "Partiellement"
            else:
                payment_status = "Payé"

            eligibility_text = "✅ Éligible" if is_eligible else "❌ Non"

            ctk.CTkLabel(row, text=fullname, font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]).pack(side="left", padx=15, pady=8, fill="x", expand=True)
            ctk.CTkLabel(row, text=student_number, font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=email, font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)

            payment_color = self.colors["success"] if payment_status == "Payé" else (self.colors["warning"] if payment_status == "Partiellement" else self.colors["danger"])
            ctk.CTkLabel(row, text=payment_status, font=ctk.CTkFont(size=10), text_color=payment_color).pack(side="left", padx=15, pady=8)

            eligibility_color = self.colors["success"] if is_eligible else self.colors["danger"]
            ctk.CTkLabel(row, text=eligibility_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=eligibility_color).pack(side="right", padx=15, pady=8)

    def _open_add_student_dialog(self):
        """Ouvre la fenêtre d'inscription d'un nouvel étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Inscription Étudiant")
        dialog.geometry("520x640")
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="➕ Nouvel Étudiant",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(pady=(20, 10))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25, pady=10)

        def add_labeled_entry(label_text, placeholder="", is_password=False):
            ctk.CTkLabel(form, text=label_text, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 4))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, show="*" if is_password else "")
            entry.pack(fill="x")
            return entry

        student_number_entry = add_labeled_entry("Numéro étudiant", "Ex: STU2026-001")
        firstname_entry = add_labeled_entry("Prénom", "Ex: Jean")
        lastname_entry = add_labeled_entry("Nom", "Ex: Dupont")
        email_entry = add_labeled_entry("Email", "Ex: jean@uor.rw")

        promotions = self.student_service.get_promotions()
        promotion_map = {f"{p['name']} ({p['year']})": p['id'] for p in promotions}
        ctk.CTkLabel(form, text="Promotion", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 4))
        promotion_combo = ctk.CTkComboBox(form, values=list(promotion_map.keys()), width=200)
        if promotion_map:
            promotion_combo.set(list(promotion_map.keys())[0])
        promotion_combo.pack(fill="x")

        password_entry = add_labeled_entry("Mot de passe (6 chiffres)", "Ex: 123456", is_password=True)
        threshold_entry = add_labeled_entry("Seuil financier requis (RWF)", "Ex: 500000")

        ctk.CTkLabel(form, text="Photo du visage", font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(10, 4))
        photo_frame = ctk.CTkFrame(form, fg_color="transparent")
        photo_frame.pack(fill="x")
        photo_path_var = StringVar(value="")
        photo_entry = ctk.CTkEntry(photo_frame, textvariable=photo_path_var)
        photo_entry.pack(side="left", fill="x", expand=True)

        def choose_photo():
            file_path = filedialog.askopenfilename(
                title="Choisir une photo",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                photo_path_var.set(file_path)

        choose_btn = ctk.CTkButton(photo_frame, text="Parcourir", width=100, command=choose_photo)
        choose_btn.pack(side="right", padx=(10, 0))

        def save_student():
            student_number = student_number_entry.get().strip()
            firstname = firstname_entry.get().strip()
            lastname = lastname_entry.get().strip()
            email = email_entry.get().strip()
            promotion_label = promotion_combo.get().strip()
            password = password_entry.get().strip()
            threshold_text = threshold_entry.get().strip()
            photo_path = photo_path_var.get().strip()

            if not all([student_number, firstname, lastname, email, promotion_label, password, threshold_text, photo_path]):
                messagebox.showerror("Erreur", "Tous les champs sont obligatoires.")
                return

            if promotion_label not in promotion_map:
                messagebox.showerror("Erreur", "Promotion invalide.")
                return

            try:
                threshold_required = Decimal(threshold_text)
            except Exception:
                messagebox.showerror("Erreur", "Seuil financier invalide.")
                return

            if not self.face_service.is_available():
                messagebox.showerror("Erreur", "Reconnaissance faciale non disponible.")
                return

            try:
                encoding = self.face_service.register_face(photo_path, 1)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur photo: {e}")
                return

            if encoding is None:
                messagebox.showerror("Erreur", "Aucun visage détecté dans la photo.")
                return

            face_bytes = encoding.tobytes()
            student = Student(
                student_number=student_number,
                firstname=firstname,
                lastname=lastname,
                email=email,
                promotion_id=promotion_map[promotion_label]
            )

            student_id = self.auth_service.register_student_with_face(student, password, face_bytes)
            if not student_id:
                messagebox.showerror("Erreur", "Échec d'enregistrement de l'étudiant.")
                return

            finance_ok = self.finance_service.create_finance_profile(student_id, threshold_required)
            if not finance_ok:
                messagebox.showwarning("Attention", "Profil financier non créé.")

            messagebox.showinfo("Succès", "Étudiant enregistré avec succès.")
            dialog.destroy()
            self._show_students()

        save_btn = ctk.CTkButton(
            dialog,
            text="Enregistrer",
            fg_color=self.colors["success"],
            hover_color=self.colors["primary"],
            height=36,
            command=save_student
        )
        save_btn.pack(pady=(10, 20))
    
    def _show_finance(self):
        """Affiche la page Finances"""
        self._clear_content()
        self._update_nav_buttons("finance")
        
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
        
        kpis = [
            (f"RWF {revenue:,.0f}", "Revenus Totaux", "green"),
            (f"{payment_status['eligible']}", "Paiements Complètes", "blue"),
            (f"{payment_status['partial_paid']}", "Paiements Partiels", "orange"),
            (f"{payment_status['never_paid']}", "Non Payés", "red"),
        ]
        
        for i, (value, label, color_key) in enumerate(kpis):
            color_map = {"green": self.colors["success"], "blue": self.colors["info"], "orange": self.colors["warning"], "red": self.colors["danger"]}
            kpi_card = ctk.CTkFrame(kpi_frame, fg_color=color_map[color_key], corner_radius=8, height=100)
            kpi_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0 if i == 3 else 5))
            kpi_card.pack_propagate(False)
            
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
        header_frame = ctk.CTkFrame(table_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        
        headers = ["Étudiant", "ID", "Montant Payé", "Seuil Requis", "Statut", "Date"]
        for header_text in headers:
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=15, pady=10, fill="x", expand=True)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        # Dummy data
        payments = [
            ("Jean Dupont", "STU001", "RWF 500,000", "RWF 500,000", "Payé", "2025-01-15"),
            ("Marie Durant", "STU002", "RWF 250,000", "RWF 500,000", "Partiel", "2025-01-20"),
            ("Pierre Martin", "STU003", "RWF 0", "RWF 500,000", "Non payé", "-"),
            ("Sophie Bernard", "STU004", "RWF 600,000", "RWF 500,000", "Payé", "2025-01-10"),
            ("Luc Gautier", "STU005", "RWF 150,000", "RWF 500,000", "Partiel", "2025-01-25"),
        ]
        
        for payment in payments:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=4)
            
            ctk.CTkLabel(row, text=payment[0], font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]).pack(side="left", padx=15, pady=8, fill="x", expand=True)
            ctk.CTkLabel(row, text=payment[1], font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=payment[2], font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["success"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=payment[3], font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)
            
            color = self.colors["success"] if "Payé" in payment[4] else (self.colors["warning"] if "Partiel" in payment[4] else self.colors["danger"])
            ctk.CTkLabel(row, text=payment[4], font=ctk.CTkFont(size=10), text_color=color).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=payment[5], font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="right", padx=15, pady=8)
    
    def _show_access_logs(self):
        """Affiche les logs d'accès"""
        self._clear_content()
        self._update_nav_buttons("access_logs")
        
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
        header_frame = ctk.CTkFrame(table_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        
        headers = ["Étudiant", "ID", "Point d'Accès", "Résultat", "Mot de passe", "Visage", "Finance", "Heure"]
        for header_text in headers:
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=8, pady=10, fill="x", expand=True)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        # Dummy access logs
        logs = [
            ("Jean Dupont", "STU001", "Salle 101", "✅", "✓", "✓", "✓", "09:30"),
            ("Marie Durant", "STU002", "Salle 102", "❌", "✓", "✗", "✗", "09:35"),
            ("Pierre Martin", "STU003", "Salle 103", "❌", "✗", "✓", "✗", "09:40"),
            ("Sophie Bernard", "STU004", "Salle 101", "✅", "✓", "✓", "✓", "09:45"),
            ("Luc Gautier", "STU005", "Salle 104", "❌", "✓", "✓", "✗", "09:50"),
        ]
        
        for log in logs:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=3)
            
            ctk.CTkLabel(row, text=log[0], font=ctk.CTkFont(size=9), text_color=self.colors["text_dark"]).pack(side="left", padx=8, pady=6, fill="x", expand=True)
            ctk.CTkLabel(row, text=log[1], font=ctk.CTkFont(size=9), text_color=self.colors["text_light"]).pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=log[2], font=ctk.CTkFont(size=9), text_color=self.colors["text_light"]).pack(side="left", padx=8, pady=6)
            
            result_color = self.colors["success"] if "✅" in log[3] else self.colors["danger"]
            ctk.CTkLabel(row, text=log[3], font=ctk.CTkFont(size=9, weight="bold"), text_color=result_color).pack(side="left", padx=8, pady=6)
            
            for i in range(4, 7):
                color = self.colors["success"] if "✓" in log[i] else self.colors["danger"]
                ctk.CTkLabel(row, text=log[i], font=ctk.CTkFont(size=10), text_color=color).pack(side="left", padx=8, pady=6)
            
            ctk.CTkLabel(row, text=log[7], font=ctk.CTkFont(size=9), text_color=self.colors["text_light"]).pack(side="right", padx=8, pady=6)
    
    def _show_reports(self):
        """Affiche les rapports"""
        self._clear_content()
        self._update_nav_buttons("reports")
        
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
        header_frame = ctk.CTkFrame(report_card, fg_color=self.colors["border"], corner_radius=0)
        header_frame.pack(fill="x", padx=25, pady=(0, 0))
        
        headers = ["Faculté", "Département", "Total Étudiants", "Éligibles", "% Éligibilité", "Revenus"]
        for header_text in headers:
            ctk.CTkLabel(
                header_frame,
                text=header_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"]
            ).pack(side="left", padx=15, pady=10, fill="x", expand=True)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(report_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
        
        # Dummy data by faculty
        faculties_data = [
            ("Informatique", "Génie Logiciel", "45", "35", "77.8%", "RWF 17,500,000"),
            ("Informatique", "Réseaux", "30", "22", "73.3%", "RWF 11,000,000"),
            ("Gestion", "Comptabilité", "28", "20", "71.4%", "RWF 10,000,000"),
            ("Gestion", "Management", "35", "25", "71.4%", "RWF 12,500,000"),
            ("Sciences", "Biologie", "22", "15", "68.2%", "RWF 7,500,000"),
            ("Sciences", "Chimie", "18", "12", "66.7%", "RWF 6,000,000"),
            ("Droit", "Droit Civil", "25", "16", "64%", "RWF 8,000,000"),
        ]
        
        for faculty in faculties_data:
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=4)
            
            ctk.CTkLabel(row, text=faculty[0], font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left", padx=15, pady=8, fill="x", expand=True)
            ctk.CTkLabel(row, text=faculty[1], font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=faculty[2], font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=faculty[3], font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["success"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=faculty[4], font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["primary"]).pack(side="left", padx=15, pady=8)
            ctk.CTkLabel(row, text=faculty[5], font=ctk.CTkFont(size=10), text_color=self.colors["warning"]).pack(side="right", padx=15, pady=8)
    
    def _show_academic_years(self):
        """Affiche la gestion des années académiques"""
        self._clear_content()
        self._update_nav_buttons("academic_years")
        self.title_label.configure(text="Années Académiques")
        self.subtitle_label.configure(text="Gestion des seuils financiers et périodes d'examens")
        
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
            ctk.CTkLabel(threshold_row, text=f"{active_year['threshold_amount']:,.0f} FC", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["warning"]).pack(side="left", padx=(10, 0))
            
            # Frais finaux
            fee_row = ctk.CTkFrame(info_frame, fg_color="transparent", height=40)
            fee_row.pack(fill="x", padx=15, pady=10)
            fee_row.pack_propagate(False)
            ctk.CTkLabel(fee_row, text="Frais Finaux:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left")
            ctk.CTkLabel(fee_row, text=f"{active_year['final_fee']:,.0f} FC", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["success"]).pack(side="left", padx=(10, 0))
            
            # Validité partielle
            validity_row = ctk.CTkFrame(info_frame, fg_color="transparent", height=40)
            validity_row.pack(fill="x", padx=15, pady=(10, 15))
            validity_row.pack_propagate(False)
            ctk.CTkLabel(validity_row, text="Validité (paiement partiel):", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left")
            ctk.CTkLabel(validity_row, text=f"{active_year['partial_valid_days']} jours", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["info"]).pack(side="left", padx=(10, 0))
        else:
            ctk.CTkLabel(year_card, text="❌ Aucune année académique active", font=ctk.CTkFont(size=12), text_color=self.colors["danger"]).pack(anchor="w", padx=25, pady=10)
        
        # === Section: Mettre à jour les Seuils ===
        threshold_card = self._create_card(self.content_frame, height=280)
        threshold_card.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            threshold_card,
            text="⚙️ Mettre à jour les Seuils Financiers",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Form pour mettre à jour
        form_frame = ctk.CTkFrame(threshold_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=25, pady=(0, 20))
        
        # Nouveau seuil
        ctk.CTkLabel(form_frame, text="Nouveau Seuil (FC):", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(anchor="w", pady=(5, 2))
        new_threshold_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: 150000", height=35, corner_radius=6)
        new_threshold_entry.pack(fill="x", pady=(0, 15))
        if active_year:
            new_threshold_entry.insert(0, str(active_year['threshold_amount']))
        
        # Nouveaux frais finaux
        ctk.CTkLabel(form_frame, text="Nouveaux Frais Finaux (FC):", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(anchor="w", pady=(5, 2))
        new_fee_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: 250000", height=35, corner_radius=6)
        new_fee_entry.pack(fill="x", pady=(0, 20))
        if active_year:
            new_fee_entry.insert(0, str(active_year['final_fee']))
        
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
                header_frame = ctk.CTkFrame(exam_card, fg_color=self.colors["border"], corner_radius=0)
                header_frame.pack(fill="x", padx=25, pady=(0, 0))
                
                headers = ["Période", "Début", "Fin", "Durée"]
                for header_text in headers:
                    ctk.CTkLabel(
                        header_frame,
                        text=header_text,
                        font=ctk.CTkFont(size=11, weight="bold"),
                        text_color=self.colors["text_dark"]
                    ).pack(side="left", padx=15, pady=10, fill="x", expand=True)
                
                # Liste des périodes
                scroll_frame = ctk.CTkScrollableFrame(exam_card, fg_color="transparent")
                scroll_frame.pack(fill="both", expand=True, padx=25, pady=(15, 20))
                
                for period in exam_periods:
                    start = datetime.strptime(str(period['start_date']), "%Y-%m-%d")
                    end = datetime.strptime(str(period['end_date']), "%Y-%m-%d")
                    duration = (end - start).days
                    
                    row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
                    row.pack(fill="x", pady=4)
                    
                    ctk.CTkLabel(row, text=period['period_name'], font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left", padx=15, pady=8, fill="x", expand=True)
                    ctk.CTkLabel(row, text=start.strftime("%d/%m/%Y"), font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)
                    ctk.CTkLabel(row, text=end.strftime("%d/%m/%Y"), font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(side="left", padx=15, pady=8)
                    ctk.CTkLabel(row, text=f"{duration} jours", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["info"]).pack(side="right", padx=15, pady=8)
            else:
                ctk.CTkLabel(exam_card, text="❌ Aucune période d'examens définie", font=ctk.CTkFont(size=12), text_color=self.colors["warning"]).pack(anchor="w", padx=25, pady=20)
        else:
            ctk.CTkLabel(exam_card, text="❌ Créez une année académique d'abord", font=ctk.CTkFont(size=12), text_color=self.colors["danger"]).pack(anchor="w", padx=25, pady=20)
    
    def _update_thresholds(self, new_threshold_str, new_fee_str, academic_year_id):
        """Met à jour les seuils financiers et notifie tous les étudiants"""
        try:
            from decimal import Decimal
            
            new_threshold = Decimal(new_threshold_str)
            new_fee = Decimal(new_fee_str)
            
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
            
            messagebox.showinfo("Succès", f"Seuils mis à jour avec succès!\n\n"
                              f"Nouveau seuil: {float(new_threshold):,.0f} FC\n"
                              f"Nouveaux frais: {float(new_fee):,.0f} FC\n\n"
                              f"Tous les étudiants ont été notifiés par Email et WhatsApp.")
            
            # Recharger
            self._show_academic_years()
            
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Veuillez entrer des montants valides (nombres)")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour: {str(e)}")
            logger.error(f"Error updating thresholds: {e}")
    
    def _preview_notifications(self, new_threshold_str, new_fee_str):
        """Affiche une prévisualisation des notifications"""
        try:
            new_threshold = float(new_threshold_str)
            new_fee = float(new_fee_str)
            
            preview_msg = (
                "📱 PRÉVISUALISATION DES NOTIFICATIONS\n"
                "=" * 50 + "\n\n"
                "📧 EMAIL:\n"
                "---\n"
                "Bonjour Étudiant,\n\n"
                "Le seuil financier pour l'accès aux examens a été mis à jour.\n\n"
                f"Ancien seuil: [Ancien montant] FC\n"
                f"Nouveau seuil: {new_threshold:,.0f} FC\n\n"
                "IMPORTANT: Si vous aviez un code d'accès temporaire (paiement partiel),\n"
                "celui-ci a été invalidé.\n\n"
                "Cordialement,\n"
                "L'administration U.O.R\n\n"
                "WhatsApp:\n"
                "---\n"
                f"Le seuil financier a changé de [ancien] FC à {new_threshold:,.0f} FC.\n"
                "Votre code temporaire a été invalidé si applicable."
            )
            
            messagebox.showinfo("Prévisualisation", preview_msg)
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des montants valides")
    
    def _clear_content(self):
        """Efface le contenu"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def _on_language_change(self, value):
        """Change la langue"""
        self.translator.set_language(value)
        
        # Recréer l'interface complète
        for widget in self.winfo_children():
            widget.destroy()
        
        self._create_ui()
        logger.info(f"Langue changée à: {value}")
    
    def _on_logout(self):
        """Déconnecte l'utilisateur"""
        logger.info("Déconnexion")
        self.destroy()
