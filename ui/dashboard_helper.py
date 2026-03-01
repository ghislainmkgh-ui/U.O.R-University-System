"""
Helper pour faciliter l'intégration des composants modernes dans le dashboard existant
Fournit des fonctions de factory pour créer rapidement les cartes, graphiques, cercles
"""

import customtkinter as ctk
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, List
from ui.components.modern_dashboard_components import (
    CircularProgressBar, MiniLineChart, StatCard, DashboardMetric, AnimatedCounter
)
import logging

logger = logging.getLogger(__name__)


class DashboardHelper:
    """Helper pour créer des éléments dashboard modernes"""
    
    @staticmethod
    def create_metric_card(
        parent
        title: str
        icon: str
        value: str
        unit: str = ""
        trend: Optional[str] = None
        trend_color: Optional[str] = None
        colors: Optional[Dict] = None
        onclick: Optional[Callable] = None
    ) -> ctk.CTkFrame:
        """Crée une carte métrique simple et élégante"""
        card = StatCard(
            parent
            icon=icon
            label=title
            value=value
            unit=unit
            trend=trend
            trend_color=trend_color
            colors=colors or {}
            clickable=onclick is not None
            on_click=onclick
            fg_color=colors.get("card_bg", "#ffffff") if colors else "#ffffff"
            corner_radius=12
            border_width=1
            border_color=colors.get("border", "#e5e7eb") if colors else "#e5e7eb"
        )
        return card
    
    @staticmethod
    def create_progress_circle(
        parent
        title: str
        current: float
        max_val: float = 100
        unit: str = "%"
        colors: Optional[Dict] = None
        size: int = 150
    ) -> ctk.CTkFrame:
        """Crée un widget de progression circulaire"""
        container = ctk.CTkFrame(parent)
        
        # Titre
        ctk.CTkLabel(
            container
            text=title
            font=("Segoe UI", 12, "bold")
            text_color=colors.get("text_dark", "#333333") if colors else "#333333"
        ).pack(pady=(0, 10))
        
        # Cercle de progression
        circle = CircularProgressBar(
            container
            size=size
            value=current
            max_value=max_val
            progress_color=colors.get("primary", "#4e73df") if colors else "#4e73df"
            fg_color=colors.get("border", "#e5e7eb") if colors else "#e5e7eb"
            text_color=colors.get("text_dark", "#333333") if colors else "#333333"
            thickness=12
        )
        circle.pack()
        
        return container
    
    @staticmethod
    def create_animated_stat(
        parent
        label: str
        start: int = 0
        end: int = 100
        duration: float = 1.0
        colors: Optional[Dict] = None
        icon: str = "📊"
    ) -> ctk.CTkFrame:
        """Crée une statistique avec compteur animé"""
        container = ctk.CTkFrame(parent)
        
        # Icône et label
        header = ctk.CTkFrame(container)
        header.pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            header
            text=icon
            font=("Segoe UI", 20)
        ).pack(side="left", padx=(0, 8))
        
        ctk.CTkLabel(
            header
            text=label
            font=("Segoe UI", 11, "bold")
            text_color=colors.get("text_light", "#999999") if colors else "#999999"
        ).pack(side="left")
        
        # Compteur animé
        counter = AnimatedCounter(
            container
            start=start
            end=end
            duration=duration
            font=("Segoe UI", 28, "bold")
            text_color=colors.get("text_dark", "#333333") if colors else "#333333")
        counter.pack(anchor="w", pady=(0, 5))
        
        return container
    
    @staticmethod
    def create_mini_chart(
        parent
        title: str = "Graphique"
        height: int = 180
        data_provider: Optional[Callable] = None
        colors: Optional[Dict] = None
    ) -> MiniLineChart:
        """Crée un mini graphique avec données temps réel"""
        chart = MiniLineChart(
            parent
            title=title
            height=height
            data_provider=data_provider
            colors={
                "bg": colors.get("card_bg", "#ffffff") if colors else "#ffffff"
                "grid": colors.get("border", "#e5e7eb") if colors else "#e5e7eb"
                "line": colors.get("primary", "#4e73df") if colors else "#4e73df"
                "text": colors.get("text_dark", "#333333") if colors else "#333333"
                "light": colors.get("text_light", "#999999") if colors else "#999999"
            }
            fg_color=colors.get("card_bg", "#ffffff") if colors else "#ffffff"
            corner_radius=12
        )
        return chart
    
    @staticmethod
    def create_stat_row(
        parent
        stats: List[Dict]
        colors: Optional[Dict] = None
    ) -> ctk.CTkFrame:
        """Crée une rangée de statistiques"""
        row = ctk.CTkFrame(parent)
        
        for stat in stats:
            card = DashboardHelper.create_metric_card(
                row
                title=stat.get("title", "")
                icon=stat.get("icon", "📊")
                value=stat.get("value", "0")
                unit=stat.get("unit", "")
                trend=stat.get("trend")
                trend_color=stat.get("trend_color")
                colors=colors
                onclick=stat.get("onclick")
            )
            card.pack(side="left", fill="both", expand=True, padx=5)
        
        return row


class DataSimulator:
    """Simule des données temps réel pour les graphiques en développement"""
    
    @staticmethod
    def generate_random_data(count: int = 30, min_val: float = 0, max_val: float = 100) -> list:
        """Génère des données aléatoires"""
        import random
        return [random.uniform(min_val, max_val) for _ in range(count)]
    
    @staticmethod
    def generate_growing_data(count: int = 30, start: float = 50, max_val: float = 100) -> list:
        """Génère des données avec croissance progressive"""
        data = []
        for i in range(count):
            val = start + (i / count) * (max_val - start)
            data.append(val)
        return data
    
    @staticmethod  
    def generate_sine_wave(count: int = 30, amplitude: float = 50, center: float = 50) -> list:
        """Génère une onde sinus"""
        import math
        data = []
        for i in range(count):
            val = center + amplitude * math.sin(2 * math.pi * i / count)
            data.append(val)
        return data
    
    @staticmethod
    def create_data_provider(data_type: str = "random"):
        """Crée une fonction provider pour graphiques temps réel"""
        def provider():
            if data_type == "random":
                import random
                return random.uniform(20, 95)
            elif data_type == "growing":
                return (datetime.now().minute / 60) * 100
            elif data_type == "sine":
                import math
                return 50 + 40 * math.sin(datetime.now().timestamp() / 10)
            return 50
        return provider


# Exemples de mise à jour facile du dashboard existant
QUICK_INTEGRATION_EXAMPLE = """
# Dans _show_dashboard() :

from ui.dashboard_helper import DashboardHelper, DataSimulator

# --- Créer une rangée de stats modernes ---
stats = [
    {
        "title": "Total Étudiants"
        "icon": "👥"
        "value": str(total_students)
        "trend": "↑ 5.2%"
        "trend_color": "#059669"
        "onclick": lambda: self._show_students()
    }
    {
        "title": "Éligibles"
        "icon": "✅"
        "value": str(eligible_students)
        "trend": "↑ 2.1%"
        "trend_color": "#059669"
        "onclick": lambda: self._show_students()
    }
    {
        "title": "Revenus"
        "icon": "💰"
        "value": f"{revenue:,.0f}"
        "unit": " FC"
        "trend": "↑ 12.5%"
        "trend_color": "#059669"
        "onclick": lambda: self._show_finance()
    }
]

stat_row = DashboardHelper.create_stat_row(self.content_frame, stats, colors=self.colors)
stat_row.pack(fill="x", pady=(0, 20))

# --- Ajouter un cercle de progression ---
progress = DashboardHelper.create_progress_circle(
    self.content_frame
    "Taux d'Éligibilité"
    current=completion
    max_val=100
    colors=self.colors
)
progress.pack(fill="x", padx=20, pady=(0, 20))

# --- Ajouter un graphique temps réel ---
chart = DashboardHelper.create_mini_chart(
    self.content_frame
    title="Évolution des Accès"
    height=250
    data_provider=DataSimulator.create_data_provider("random")
    colors=self.colors
)
chart.pack(fill="both", expand=True, padx=20, pady=(0, 20))
"""
