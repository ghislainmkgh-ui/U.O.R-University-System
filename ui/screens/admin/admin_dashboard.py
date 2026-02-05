"""Dashboard administrateur"""
import customtkinter as ctk
import logging
from ui.i18n.translator import Translator
from ui.theme.theme_manager import ThemeManager
from ui.components.modern_widgets import StatCard
from app.services.finance.finance_service import FinanceService
from app.services.student.student_service import StudentService

logger = logging.getLogger(__name__)


class AdminDashboard(ctk.CTk):
    """Tableau de bord administrateur principal"""
    
    def __init__(self):
        super().__init__()
        
        self.translator = Translator("FR")
        self.theme = ThemeManager("light")
        self.finance_service = FinanceService()
        self.student_service = StudentService()
        
        self.title("U.O.R - Administration")
        self.geometry("1400x900")
        
        self._create_ui()
    
    def _create_ui(self):
        """Crée l'interface du dashboard"""
        bg_color = self.theme.get_color("background")
        self.configure(fg_color=bg_color)
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self._create_sidebar()
        
        # Contenu principal
        main_frame = ctk.CTkFrame(self, fg_color=bg_color)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        self._create_header(main_frame)
        self._create_stats(main_frame)
        self._create_content_area(main_frame)
    
    def _create_sidebar(self):
        """Crée la barre latérale"""
        sidebar = ctk.CTkFrame(self, fg_color=self.theme.get_color("surface"), corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(10, weight=1)
        
        # Logo
        ctk.CTkLabel(
            sidebar,
            text="U.O.R\nADMIN",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.theme.get_color("primary")
        ).grid(row=0, column=0, padx=20, pady=30)
        
        # Menu items
        menu_items = [
            ("Dashboard", "📊"),
            ("Students", "👥"),
            ("Finance", "💰"),
            ("Access Logs", "🔑"),
            ("Reports", "📋"),
        ]
        
        for idx, (item, icon) in enumerate(menu_items, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon} {item}",
                fg_color="transparent",
                text_color=self.theme.get_color("text_primary"),
                hover_color=self.theme.get_color("primary"),
                command=lambda i=item: self._on_menu_click(i)
            )
            btn.grid(row=idx, column=0, padx=10, pady=8, sticky="ew")
        
        # Logout button
        ctk.CTkButton(
            sidebar,
            text="Logout",
            fg_color=self.theme.get_color("danger"),
            hover_color="#c0392b"
        ).grid(row=20, column=0, padx=10, pady=10, sticky="ew")
    
    def _create_header(self, parent):
        """Crée le header"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(
            header,
            text="Dashboard",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header,
            text="Bienvenue sur la plateforme U.O.R",
            text_color=self.theme.get_color("text_secondary")
        ).pack(anchor="w")
    
    def _create_stats(self, parent):
        """Crée les cartes de statistiques"""
        stats_frame = ctk.CTkFrame(parent, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)
        
        StatCard(
            stats_frame, 
            "Eligible", 
            "540",
            self.theme.get_color("success")
        ).grid(row=0, column=0, padx=5, sticky="ew")
        
        StatCard(
            stats_frame,
            "Non Eligible",
            "120",
            self.theme.get_color("warning")
        ).grid(row=0, column=1, padx=5, sticky="ew")
        
        StatCard(
            stats_frame,
            "Fraud Detected",
            "7",
            self.theme.get_color("danger")
        ).grid(row=0, column=2, padx=5, sticky="ew")
        
        StatCard(
            stats_frame,
            "Pending",
            "24",
            self.theme.get_color("info")
        ).grid(row=0, column=3, padx=5, sticky="ew")
    
    def _create_content_area(self, parent):
        """Crée la zone de contenu principal"""
        content = ctk.CTkFrame(
            parent,
            fg_color=self.theme.get_color("surface"),
            corner_radius=14
        )
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        ctk.CTkLabel(
            content,
            text="Recent Activities",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # Placeholder pour activités
        for i, activity in enumerate([
            "✓ Student access granted - 08:45",
            "✗ Payment verification failed - 08:30",
            "✓ Face recognition successful - 08:15",
            "✓ New payment recorded - 08:00",
        ], start=1):
            ctk.CTkLabel(content, text=activity).grid(row=i, column=0, padx=20, pady=5, sticky="w")
    
    def _on_menu_click(self, item):
        """Gère les clics sur le menu"""
        logger.info(f"Menu item clicked: {item}")
