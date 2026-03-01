"""
Composants modernes et performants pour le dashboard
- Cercles de progression animés
- Graphiques temps réel
- Cartes de statistiques élégantes
- Indicateurs visuels pro
"""

import customtkinter as ctk
import math
import threading
import tkinter as tk
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CircularProgressBar(ctk.CTkCanvas):
    """Barre de progression circulaire, pro et moderne"""
    
    def __init__(
        self
        parent
        size: int = 150
        value: float = 0
        max_value: float = 100
        fg_color: str = "#f0f0f0"
        progress_color: str = "#4e73df"
        text_color: str = "#333333"
        thickness: int = 12
        **kwargs
    ):
        super().__init__(
            parent
            width=size
            height=size
            bg=parent.cget("fg_color") if hasattr(parent, "cget") else "#ffffff"
            highlightthickness=0
            **kwargs
        )
        
        self.size = size
        self.value = value
        self.max_value = max_value
        self.fg_color = fg_color
        self.progress_color = progress_color
        self.text_color = text_color
        self.thickness = thickness
        self.center = size / 2
        self.radius = (size - thickness) / 2
        
        # Configuration initiale
        self.pack_propagate(False)
        self.configure(width=size, height=size)
        self.draw()
    
    def draw(self, value: Optional[float] = None):
        """Dessine la barre de progression"""
        if value is not None:
            self.value = value
        
        self.delete("all")
        center = self.center
        radius = self.radius
        
        # Cercle fond (gris clair)
        self.create_oval(
            center - radius
            center - radius
            center + radius
            center + radius
            fill=self.fg_color
            outline=self.fg_color
            width=0
        )
        
        # Barre de progression (cercle coloré)
        percent = min(self.value / self.max_value, 1.0) * 360
        self._draw_arc(
            center, center, radius, self.thickness, 0, percent, fill=self.progress_color, width=self.thickness
        )
        
        # Texte central
        percent_text = f"{int((self.value / self.max_value) * 100)}%"
        self.create_text(
            center, center - 10
            text=percent_text
            font=("Segoe UI", 24, "bold")
            fill=self.text_color
        )
        
        # Label sous le pourcentage
        self.create_text(
            center, center + 20
            text="Complétion"
            font=("Segoe UI", 10)
            fill=self.text_color
        )
    
    def _draw_arc(self, x, y, radius, width, start, extent, **kwargs):
        """Dessine un arc de cercle"""
        # Convertir angles SVG to Tkinter canvas
        start_rad = math.radians(start - 90)
        extent_rad = math.radians(extent)
        
        # Points de contrôle pour l'arc
        x1 = x + radius * math.cos(start_rad)
        y1 = y + radius * math.sin(start_rad)
        x2 = x + radius * math.cos(start_rad + extent_rad)
        y2 = y + radius * math.sin(start_rad + extent_rad)
        
        # Large arc flag
        large_arc = 1 if extent > 180 else 0
        
        # SVG path simulé avec polygone
        if extent <= 1:
            return
        
        points = []
        steps = max(int(extent / 2), 2)
        for i in range(steps + 1):
            angle = start_rad + (i / steps) * extent_rad
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append(px)
            points.append(py)
        
        # Inverser pour créer anneau
        for i in range(steps, -1, -1):
            angle = start_rad + (i / steps) * extent_rad
            px = x + (radius - width) * math.cos(angle)
            py = y + (radius - width) * math.sin(angle)
            points.append(px)
            points.append(py)
        
        self.create_polygon(points, **kwargs)
    
    def update_value(self, value: float):
        """Met à jour la valeur avec animation lisse"""
        # Animation progressive
        current = self.value
        diff = value - current
        steps = 20
        
        def animate():
            for i in range(steps):
                new_val = current + (diff * (i + 1) / steps)
                self.draw(new_val)
                self.update()
                self.after(30)
        
        thread = threading.Thread(target=animate, daemon=True)
        thread.start()


class MiniLineChart(ctk.CTkFrame):
    """Petit graphique linéaire temps réel pour le dashboard"""
    
    def __init__(
        self
        parent
        title: str = "Graphique"
        height: int = 180
        data_provider: Optional[Callable] = None
        colors: Optional[Dict] = None
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.title = title
        self.height = height
        self.data_provider = data_provider or (lambda: [])
        self.colors = colors or {
            "bg": "#ffffff"
            "grid": "#e5e7eb"
            "line": "#4e73df"
            "text": "#333333"
            "light": "#999999"
        }
        
        self.data_points: List[float] = []
        self._create_ui()
        self._start_update_thread()
    
    def _create_ui(self):
        """Crée l'interface du graphique"""
        # Header
        header = ctk.CTkFrame(self, height=30)
        header.pack(fill="x", padx=12, pady=(12, 8))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header
            text=f"📈 {self.title}"
            font=("Segoe UI", 13, "bold")
            text_color=self.colors["text"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            header
            text="Temps réel"
            font=("Segoe UI", 10)
            text_color=self.colors["light"]
        ).pack(side="right")
        
        # Canvas pour le graphique
        self.canvas = tk.Canvas(
            self
            height=self.height - 60
            bg=self.colors["bg"]
            highlightthickness=1
            highlightbackground=self.colors["grid"]
            cursor="cross"
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        
        # Footer avec stats
        footer = ctk.CTkFrame(self, height=25)
        footer.pack(fill="x", padx=12, pady=(0, 10))
        footer.pack_propagate(False)
        
        ctk.CTkLabel(
            footer
            text="↑ 8.2% • Derniers 30 jours"
            font=("Segoe UI", 10)
            text_color=self.colors["light"]
        ).pack(side="left")
    
    def _on_canvas_resize(self, event):
        """Redessine le graphique lors du redimensionnement"""
        self._draw_chart()
    
    def _draw_chart(self):
        """Dessine le graphique"""
        if not self.canvas or not self.data_points:
            return
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        self.canvas.delete("all")
        
        # Grille
        self._draw_grid(width, height)
        
        # Ligne de données
        if len(self.data_points) > 1:
            self._draw_line(width, height)
    
    def _draw_grid(self, width: int, height: int):
        """Dessine la grille de fond"""
        grid_spacing = 40
        
        # Lignes verticales
        for x in range(0, width, grid_spacing):
            self.canvas.create_line(
                x, 0, x, height
                fill=self.colors["grid"]
                width=1
                dash=(2, 4)
            )
        
        # Lignes horizontales
        for y in range(0, height, grid_spacing):
            self.canvas.create_line(
                0, y, width, y
                fill=self.colors["grid"]
                width=1
                dash=(2, 4)
            )
    
    def _draw_line(self, width: int, height: int):
        """Dessine la ligne de données"""
        if len(self.data_points) < 2:
            return
        
        # Normaliser les données
        min_val = min(self.data_points)
        max_val = max(self.data_points) or 1
        range_val = max_val - min_val or 1
        
        x_spacing = width / (len(self.data_points) - 1)
        
        # Points
        points = []
        for i, val in enumerate(self.data_points):
            x = i * x_spacing
            y = height - ((val - min_val) / range_val) * (height - 20)
            points.append((x, y))
        
        # Dessiner la ligne
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            self.canvas.create_line(
                x1, y1, x2, y2
                fill=self.colors["line"]
                width=3
                smooth=True
            )
            # Points
            self.canvas.create_oval(
                x2 - 3, y2 - 3, x2 + 3, y2 + 3
                fill=self.colors["line"]
                outline=self.colors["line"]
            )
    
    def add_data(self, value: float):
        """Ajoute un nouveau point de données"""
        self.data_points.append(value)
        # Garder seulement les 30 derniers points
        if len(self.data_points) > 30:
            self.data_points.pop(0)
        self._draw_chart()
    
    def _start_update_thread(self):
        """Démarre le thread de mise à jour en temps réel"""
        def update():
            while True:
                try:
                    data = self.data_provider()
                    if isinstance(data, (int, float)):
                        self.add_data(data)
                    elif isinstance(data, list) and len(data) > 0:
                        self.data_points.extend(data[-1:])
                        if len(self.data_points) > 30:
                            self.data_points.pop(0)
                        self._draw_chart()
                    threading.Event().wait(2)  # Update every 2 seconds
                except Exception as e:
                    logger.error(f"Error updating chart: {e}")
                    threading.Event().wait(5)
        
        if self.data_provider:
            thread = threading.Thread(target=update, daemon=True)
            thread.start()


class StatCard(ctk.CTkFrame):
    """Carte de statistiques élégante avec icône, valeur et tendance"""
    
    def __init__(
        self
        parent
        icon: str = "📊"
        label: str = "Statistique"
        value: str = "0"
        unit: str = ""
        trend: Optional[str] = None
        trend_color: Optional[str] = None
        colors: Optional[Dict] = None
        clickable: bool = False
        on_click: Optional[Callable] = None
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.original_fg = self.cget("fg_color")
        self.colors = colors or {
            "bg": "#ffffff"
            "border": "#e5e7eb"
            "text": "#333333"
            "light": "#999999"
            "hover": "#f3f4f6"
        }
        self.clickable = clickable
        self.on_click = on_click
        
        self._create_ui(icon, label, value, unit, trend, trend_color)
        
        if clickable:
            self._make_interactive()
    
    def _create_ui(
        self
        icon: str
        label: str
        value: str
        unit: str
        trend: Optional[str]
        trend_color: Optional[str]
    ):
        """Crée l'interface de la carte"""
        # Header avec icône
        header = ctk.CTkFrame(self, height=40)
        header.pack(fill="x", padx=16, pady=(14, 8))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header
            text=icon
            font=("Segoe UI", 28)).pack(side="left")
        
        ctk.CTkLabel(
            header
            text=label
            font=("Segoe UI", 11, "bold")
            text_color=self.colors["light"]
        ).pack(anchor="w", padx=10, side="left")
        
        # Valeur principale
        value_frame = ctk.CTkFrame(self)
        value_frame.pack(fill="x", padx=16, pady=8)
        
        ctk.CTkLabel(
            value_frame
            text=f"{value}{unit}"
            font=("Segoe UI", 26, "bold")
            text_color=self.colors["text"]
        ).pack(anchor="w")
        
        # Tendance
        if trend:
            trend_frame = ctk.CTkFrame(self, height=20)
            trend_frame.pack(fill="x", padx=16, pady=(0, 12))
            trend_frame.pack_propagate(False)
            
            trend_fg = trend_color or "#10b981"
            ctk.CTkLabel(
                trend_frame
                text=trend
                font=("Segoe UI", 10, "bold")
                text_color=trend_fg
            ).pack(anchor="w")
    
    def _make_interactive(self):
        """Rend la carte interactive"""
        self.bind("<Enter>", self._on_hover_enter)
        self.bind("<Leave>", self._on_hover_leave)
        self.bind("<Button-1>", self._on_click)
        
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_hover_enter)
            child.bind("<Leave>", self._on_hover_leave)
            child.bind("<Button-1>", self._on_click)
    
    def _on_hover_enter(self, event=None):
        """Entre au survol"""
        if self.clickable:
            self.configure(fg_color=self.colors["hover"])
    
    def _on_hover_leave(self, event=None):
        """Sort du survol"""
        if self.clickable:
            self.configure(fg_color=self.original_fg)
    
    def _on_click(self, event=None):
        """Gère le clic"""
        if self.on_click and self.clickable:
            self.on_click()
    
    def update_value(self, value: str, unit: str = ""):
        """Met à jour la valeur principale"""
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, ctk.CTkLabel):
                        current_text = subchild.cget("text")
                        # Chercher le label avec la valeur (grande typographie)
                        font = subchild.cget("font")
                        if font and len(font) > 1 and font[1] == 26:
                            subchild.configure(text=f"{value}{unit}")


class AnimatedCounter(ctk.CTkLabel):
    """Compteur animé qui compte jusqu'à la valeur"""
    
    def __init__(self, parent, start: int = 0, end: int = 100, duration: float = 1.0, **kwargs):
        super().__init__(parent, **kwargs)
        self.start = start
        self.end = end
        self.duration = duration
        self.current = start
        
        self.configure(text=str(start))
        self._animate()
    
    def _animate(self):
        """Anime le compteur"""
        steps = int(self.duration * 30)  # 30 FPS
        increment = (self.end - self.start) / max(steps, 1)
        
        def count():
            for i in range(steps):
                self.current = int(self.start + increment * (i + 1))
                self.configure(text=str(self.current))
                self.after(int(1000 / 30))
            
            self.configure(text=str(self.end))
        
        thread = threading.Thread(target=count, daemon=True)
        thread.start()


class DashboardMetric(ctk.CTkFrame):
    """Métrique complète: titre + cercle progress + sous-info"""
    
    def __init__(
        self
        parent
        title: str = "Métrique"
        current: float = 0
        max_val: float = 100
        unit: str = ""
        details: Optional[str] = None
        colors: Optional[Dict] = None
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.colors = colors or {}
        self._create_ui(title, current, max_val, unit, details)
    
    def _create_ui(self, title: str, current: float, max_val: float, unit: str, details: Optional[str]):
        """Crée l'interface"""
        # Titre
        ctk.CTkLabel(
            self
            text=title
            font=("Segoe UI", 12, "bold")
            text_color=self.colors.get("text", "#333333")
        ).pack(anchor="w", padx=10, pady=(10, 8))
        
        # Cercle et info
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=10)
        
        # Cercle à gauche
        circle = CircularProgressBar(
            content
            size=80
            value=current
            max_value=max_val
            progress_color=self.colors.get("primary", "#4e73df")
            fg_color=self.colors.get("border", "#e5e7eb")
            text_color=self.colors.get("text", "#333333")
            thickness=8
        )
        circle.pack(side="left", padx=(0, 10))
        
        # Info à droite
        info = ctk.CTkFrame(content)
        info.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(
            info
            text=f"{current:.1f}{unit}"
            font=("Segoe UI", 18, "bold")
            text_color=self.colors.get("text", "#333333")
        ).pack(anchor="w")
        
        if details:
            ctk.CTkLabel(
                info
                text=details
                font=("Segoe UI", 9)
                text_color=self.colors.get("light", "#999999")
            ).pack(anchor="w", pady=(2, 0))


class ModernStatisticsPanel(ctk.CTkFrame):
    """Panneau statistique moderne avec visualisation élégante"""
    
    def __init__(
        self
        parent
        title: str = "Statistiques"
        items: List[Dict] = None
        colors: Optional[Dict] = None
        **kwargs
    ):
        """
        Args:
            items: Liste de dicts avec 'label', 'value', 'max', 'color'
            Exemple: [{'label': 'Éligibles', 'value': 12, 'max': 16, 'color': '#10b981'}]
        """
        super().__init__(parent, **kwargs)
        
        self.colors = colors or {
            "bg": "#ffffff"
            "text": "#333333"
            "light": "#999999"
            "border": "#e5e7eb"
        }
        self.items = items or []
        
        self._create_ui(title)
    
    def _create_ui(self, title: str):
        """Crée l'interface du panneau"""
        # Titre
        header = ctk.CTkFrame(self, fg_color=self.colors["bg"], height=35)
        header.pack(fill="x", padx=16, pady=(16, 12))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header
            text=title
            font=("Segoe UI", 14, "bold")
            text_color=self.colors["text"]
        ).pack(side="left")
        
        # Contenu: micro-visuels + stats
        content_area = ctk.CTkScrollableFrame(
            self
            fg_color=self.colors["bg"]
            scrollbar_button_color=self.colors["border"]
        )
        content_area.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        
        for item in self.items:
            self._create_stat_item(content_area, item)
    
    def _create_stat_item(self, parent, item: Dict):
        """Crée un élément statistique unique"""
        item_frame = ctk.CTkFrame(parent, fg_color=self.colors["border"], corner_radius=8)
        item_frame.pack(fill="x", pady=6)
        
        # En-tête: label + pourcentage
        header = ctk.CTkFrame(item_frame, fg_color=self.colors["border"])
        header.pack(fill="x", padx=12, pady=(10, 6))
        
        label = ctk.CTkLabel(
            header
            text=item.get('label', 'Item')
            font=("Segoe UI", 11, "bold")
            text_color=self.colors["text"]
        )
        label.pack(side="left")
        
        value = item.get('value', 0)
        max_val = item.get('max', 100)
        percent = (value / max_val * 100) if max_val > 0 else 0
        
        percent_label = ctk.CTkLabel(
            header
            text=f"{percent:.0f}%"
            font=("Segoe UI", 11, "bold")
            text_color=item.get('color', '#4e73df')
        )
        percent_label.pack(side="right")
        
        # Petit graphique: barre colorée + mini cercle
        bar_frame = ctk.CTkFrame(item_frame, fg_color=self.colors["border"])
        bar_frame.pack(fill="x", padx=12, pady=(0, 10))
        
        # Barre de progression chic
        bar = ctk.CTkProgressBar(
            bar_frame
            height=6
            progress_color=item.get('color', '#4e73df')
            fg_color=self.colors["border"]
        )
        bar.set(min(percent / 100, 1.0))
        bar.pack(fill="x", pady=(0, 6))
        
        # Détails: chiffres
        details = ctk.CTkFrame(bar_frame, fg_color=self.colors["border"])
        details.pack(fill="x")
        
        ctk.CTkLabel(
            details
            text=f"{value} / {max_val}"
            font=("Segoe UI", 9)
            text_color=self.colors["light"]
        ).pack(side="left")
        
        trend = item.get('trend', '')
        if trend:
            ctk.CTkLabel(
                details
                text=trend
                font=("Segoe UI", 9, "bold")
                text_color=item.get('color', '#4e73df')
            ).pack(side="right")


class ElegantCircularProgress(ctk.CTkCanvas):
    """Cercle de progression ultra-moderne avec animations"""
    
    def __init__(
        self
        parent
        size: int = 200
        value: float = 0
        max_value: float = 100
        primary_color: str = "#3b82f6"
        secondary_color: str = "#e5e7eb"
        text_color: str = "#1e293b"
        title: str = ""
        subtitle: str = ""
        thickness: int = 16
        **kwargs
    ):
        # Déterminer la couleur de fond du canvas
        parent_bg = "#ffffff"
        try:
            if hasattr(parent, "cget"):
                parent_bg_raw = parent.cget("fg_color")
                if isinstance(parent_bg_raw, (list, tuple)) and len(parent_bg_raw) > 0:
                    parent_bg = parent_bg_raw[0]
                elif isinstance(parent_bg_raw, str):
                    parent_bg = parent_bg_raw
        except Exception:
            pass
        
        super().__init__(
            parent
            width=size
            height=size
            bg=parent_bg
            highlightthickness=0
            **kwargs
        )
        
        self.size = size
        self.value = value
        self.max_value = max_value
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.text_color = text_color
        self.title = title
        self.subtitle = subtitle
        self.thickness = thickness
        self.center = size / 2
        self.radius = (size - thickness - 20) / 2
        
        self.pack_propagate(False)
        self.configure(width=size, height=size)
        self.draw()
    
    def draw(self, value: Optional[float] = None):
        """Dessine le cercle moderne"""
        if value is not None:
            self.value = value
        
        self.delete("all")
        center = self.center
        radius = self.radius
        
        # Cercle de fond (très clair)
        self.create_oval(
            center - radius
            center - radius
            center + radius
            center + radius
            fill=self.secondary_color
            outline=self.secondary_color
            width=0
        )
        
        # Arc de progression coloré (gradient effect)
        percent = min(self.value / self.max_value, 1.0) * 360
        self._draw_arc(
            center, center, radius, self.thickness, 0, percent, fill=self.primary_color, width=self.thickness
        )
        
        # Halo/ombre sous le cercle
        shadow_radius = radius + 5
        self.create_oval(
            center - shadow_radius
            center - shadow_radius + 4
            center + shadow_radius
            center + shadow_radius + 4
            fill="#00000015"
            outline=""
        )
        
        # Texte central - big number
        percent_text = f"{int((self.value / self.max_value) * 100)}%"
        self.create_text(
            center, center - 15
            text=percent_text
            font=("Segoe UI", 32, "bold")
            fill=self.primary_color
        )
        
        # Titre
        if self.title:
            self.create_text(
                center, center + 20
                text=self.title
                font=("Segoe UI", 11, "bold")
                fill=self.text_color
            )
        
        # Sous-titre
        if self.subtitle:
            self.create_text(
                center, center + 38
                text=self.subtitle
                font=("Segoe UI", 9)
                fill="#999999"
            )
    
    def _draw_arc(self, x, y, radius, width, start, extent, **kwargs):
        """Dessine un arc lisse"""
        start_rad = math.radians(start - 90)
        extent_rad = math.radians(extent)
        
        if extent <= 1:
            return
        
        points = []
        steps = max(int(extent / 2), 2)
        
        # Arc exterior
        for i in range(steps + 1):
            angle = start_rad + (i / steps) * extent_rad
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append(px)
            points.append(py)
        
        # Arc interieur (pour créer l'anneau)
        for i in range(steps, -1, -1):
            angle = start_rad + (i / steps) * extent_rad
            px = x + (radius - width) * math.cos(angle)
            py = y + (radius - width) * math.sin(angle)
            points.append(px)
            points.append(py)
        
        self.create_polygon(points, **kwargs)
    
    def update_value(self, value: float):
        """Met à jour avec animation douce"""
        current = self.value
        diff = value - current
        steps = 15
        
        def animate():
            for i in range(steps):
                new_val = current + (diff * (i + 1) / steps)
                self.draw(new_val)
                self.update()
                self.after(20)
        
        thread = threading.Thread(target=animate, daemon=True)
        thread.start()

class ModernBarChart(ctk.CTkCanvas):
    """Diagramme en barres moderne, animé et élégant pour les statistiques du dashboard"""
    
    def __init__(
        self
        parent
        width: int = 600
        height: int = 300
        title: str = "Statistiques"
        items: List[Dict] = None
        bg_color: str = "#ffffff"
        grid_color: str = "#e5e7eb"
        text_color: str = "#333333"
        **kwargs
    ):
        """
        Args:
            items: List[Dict] avec 'label', 'value', 'max', 'color', 'icon'
            Exemple: [
                {'label': 'Éligibles', 'value': 12, 'max': 16, 'color': '#10b981', 'icon': '✓'}
                {'label': 'Non éligibles', 'value': 4, 'max': 16, 'color': '#ef4444', 'icon': '✗'}
            ]
        """
        super().__init__(
            parent
            width=width
            height=height
            bg=bg_color
            highlightthickness=0
            **kwargs
        )
        
        self.width = width
        self.height = height
        self.title = title
        self.items = items or []
        self.bg_color = bg_color
        self.grid_color = grid_color
        self.text_color = text_color
        self.animated_values = {}
        
        self.bind("<Configure>", lambda e: self.draw_chart())
        self.draw_chart()
    
    def draw_chart(self):
        """Dessine le diagramme en barres moderne"""
        self.delete("all")
        
        if not self.items:
            return
        
        width = self.winfo_width() or self.width
        height = self.winfo_height() or self.height
        
        if width <= 1 or height <= 1:
            return
        
        # Titre
        title_y = 20
        self.create_text(
            width // 2, title_y
            text=self.title
            font=("Segoe UI", 16, "bold")
            fill=self.text_color
            anchor="center"
        )
        
        # Zone du diagramme (en dessous du titre)
        chart_top = 50
        chart_bottom = height - 30
        chart_height = chart_bottom - chart_top
        
        # Marge de gauche pour les labels
        left_margin = 120
        right_margin = 40
        chart_width = width - left_margin - right_margin
        
        # Trouver la valeur max
        max_value = max([item.get('max', item.get('value', 0)) for item in self.items or [100]])
        if max_value <= 0:
            max_value = 100
        
        # Nombre de barres
        num_bars = len(self.items)
        if num_bars == 0:
            return
        
        bar_height = (chart_height - (num_bars - 1) * 15) / num_bars
        bar_height = min(bar_height, 50)
        bar_spacing = (chart_height - num_bars * bar_height) / (num_bars + 1)
        
        # Dessiner chaque barre
        for idx, item in enumerate(self.items):
            label = item.get('label', f'Item {idx}')
            value = item.get('value', 0)
            max_val = item.get('max', 100)
            color = item.get('color', '#3b82f6')
            icon = item.get('icon', '')
            percentage = (value / max_value) * 100
            
            # Position Y de la barre
            y = chart_top + (idx + 1) * bar_spacing + idx * bar_height
            
            # Initialiser la valeur animée
            key = f"bar_{idx}"
            if key not in self.animated_values:
                self.animated_values[key] = 0
            
            current_width = (self.animated_values[key] / max_value) * chart_width
            
            # Barre de progress (background gris clair)
            self.create_rectangle(
                left_margin, y
                left_margin + chart_width, y + bar_height
                fill="#f3f4f6"
                outline="#e5e7eb"
                width=1
            )
            
            # Barre colorée animée
            bar_width = (value / max_value) * chart_width
            self.create_rectangle(
                left_margin, y
                left_margin + bar_width, y + bar_height
                fill=color
                outline=self._shade_color(color, 0.8)
                width=2
            )
            
            # Label et icône à gauche
            label_x = left_margin - 10
            label_y = y + bar_height // 2
            
            label_text = f"{icon} {label}" if icon else label
            self.create_text(
                label_x, label_y
                text=label_text
                font=("Segoe UI", 11, "bold")
                fill=self.text_color
                anchor="e"
                justify="right"
            )
            
            # Valeur et pourcentage à la fin de la barre
            if bar_width > 50:  # Afficher le texte dans la barre si assez d'espace
                text_x = left_margin + bar_width - 8
                value_text = f"{value}/{max_val}"
                self.create_text(
                    text_x, label_y
                    text=value_text
                    font=("Segoe UI", 10, "bold")
                    fill="#ffffff"
                    anchor="e"
                )
            else:  # Sinon l'afficher à droite
                text_x = left_margin + chart_width + 8
                value_text = f"{value}/{max_val} ({percentage:.0f}%)"
                self.create_text(
                    text_x, label_y
                    text=value_text
                    font=("Segoe UI", 10)
                    fill=self.text_color
                    anchor="w"
                )
            
            # Effet de shine/gradient
            shine_height = bar_height // 4
            self.create_rectangle(
                left_margin, y
                left_margin + bar_width, y + shine_height
                fill="#ffffff"
                outline="#ffffff"
                width=0
            )
            self.tag_lower(self.create_rectangle(
                left_margin, y
                left_margin + bar_width, y + shine_height
                fill="#ffffff"
                outline="#ffffff"
                width=0
            ))
        
        # Ligne de base
        self.create_line(
            left_margin, chart_bottom
            left_margin + chart_width, chart_bottom
            fill=self.grid_color
            width=1
        )
    
    def update_data(self, new_items: List[Dict]):
        """Met à jour les données et réanime les barres"""
        self.items = new_items
        self.animated_values.clear()
        
        # Animation des barres
        for i in range(20):
            self.after(i * 30, lambda: self.draw_chart())
    
    def _shade_color(self, hex_color: str, factor: float = 0.8) -> str:
        """Assombrit une color hex"""
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color