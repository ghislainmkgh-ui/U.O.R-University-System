"""Composants UI réutilisables"""
import customtkinter as ctk
import threading
import time


class StatCard(ctk.CTkFrame):
    """Carte statistique réutilisable avec support de thème"""
    
    def __init__(self, parent, title: str, value: str, color: str, theme=None, command=None, **kwargs):
        # Déterminer la couleur de fond
        if theme:
            color_map = {
                "primary": theme.get_color("primary"),
                "success": theme.get_color("success"),
                "warning": theme.get_color("warning"),
                "danger": theme.get_color("danger"),
                "info": theme.get_color("info"),
            }
            bg_color = color_map.get(color, color)
        else:
            color_map = {
                "primary": "#0078D4",
                "success": "#28A745",
                "warning": "#FFC107",
                "danger": "#DC3545",
                "info": "#17A2B8",
            }
            bg_color = color_map.get(color, color)
        
        super().__init__(parent, fg_color=bg_color, corner_radius=14, **kwargs)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Titre
        ctk.CTkLabel(
            self, 
            text=title.upper(), 
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Valeur
        ctk.CTkLabel(
            self, 
            text=value, 
            text_color="white",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(anchor="w", padx=20, pady=(0, 10))
        
        # Bouton optionnel
        if command:
            ctk.CTkButton(
                self, 
                text="View", 
                command=command,
                fg_color="transparency",
                text_color="white",
                border_width=1,
                border_color="white",
                height=32,
                font=ctk.CTkFont(size=11)
            ).pack(anchor="w", padx=20, pady=(0, 20))


class ProgressBar(ctk.CTkFrame):
    """Barre de progrès avec label"""
    
    def __init__(self, parent, label: str, value: float = 0.0, color: str = "#4e73df", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        ctk.CTkLabel(self, text=label).pack(anchor="w", pady=(0, 4))
        progress = ctk.CTkProgressBar(self, progress_color=color)
        progress.pack(fill="x", pady=(0, 0))
        progress.set(value)


class DataTable(ctk.CTkFrame):
    """Tableau de données simple"""
    
    def __init__(self, parent, columns: list, data: list = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.columns = columns
        self.data = data or []
        self._create_headers()
        self._populate_data()
    
    def _create_headers(self):
        """Crée les en-têtes"""
        for col_idx, col in enumerate(self.columns):
            label = ctk.CTkLabel(self, text=col, font=ctk.CTkFont(weight="bold"))
            label.grid(row=0, column=col_idx, padx=10, pady=10, sticky="ew")
    
    def _populate_data(self):
        """Remplit le tableau avec les données"""
        for row_idx, row_data in enumerate(self.data, start=1):
            for col_idx, value in enumerate(row_data):
                label = ctk.CTkLabel(self, text=str(value))
                label.grid(row=row_idx, column=col_idx, padx=10, pady=5, sticky="ew")
    
    def update_data(self, data: list):
        """Mise à jour des données"""
        self.data = data
        for widget in self.winfo_children():
            widget.destroy()
        self._create_headers()
        self._populate_data()


class LoadingSpinner(ctk.CTkFrame):
    """Spinner animé pour indiquer le chargement"""
    
    def __init__(self, parent, size: int = 30, color: str = "#3b82f6", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.size = size
        self.color = color
        self.running = False
        self.rotation = 0
        
        # Canvas pour dessiner le spinner
        self.canvas = ctk.CTkCanvas(
            self,
            width=size,
            height=size,
            bg_color="transparent",
            highlightthickness=0
        )
        self.canvas.pack()
        
    def start(self):
        """Démarre l'animation"""
        self.running = True
        self._animate()
    
    def stop(self):
        """Arrête l'animation"""
        self.running = False
        self.canvas.delete("all")
    
    def _animate(self):
        """Anime le spinner"""
        if not self.running:
            return
        
        self.canvas.delete("all")
        center = self.size / 2
        radius = self.size / 2 - 4
        
        # Dessine les segments du spinner
        for i in range(8):
            angle = (i * 45 + self.rotation) * 3.14159 / 180
            opacity = int(255 * (i / 8))
            
            x1 = center + (radius - 6) * __import__('math').cos(angle)
            y1 = center + (radius - 6) * __import__('math').sin(angle)
            x2 = center + radius * __import__('math').cos(angle)
            y2 = center + radius * __import__('math').sin(angle)
            
            # Variation d'opacité pour l'effet de rotation
            color_intensity = int(255 * (i / 8))
            
        self.rotation = (self.rotation + 15) % 360
        self.after(50, self._animate)


class LoadingIndicator(ctk.CTkFrame):
    """Indicateur de chargement avec texte et spinner"""
    
    def __init__(self, parent, text: str = "Traitement en cours...", 
                 color: str = "#3b82f6", **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.color = color
        self.running = False
        
        # Frame horizontal pour spinner + texte
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=5)
        
        # Spinner simple avec des caractères
        self.spinner_label = ctk.CTkLabel(
            content_frame,
            text="⠋",
            font=ctk.CTkFont(size=16),
            text_color=color
        )
        self.spinner_label.pack(side="left", padx=(0, 10))
        
        # Texte de statut
        self.status_label = ctk.CTkLabel(
            content_frame,
            text=text,
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af"
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.frame_index = 0
    
    def start(self, text: str = None):
        """Démarre l'animation"""
        if text:
            self.status_label.configure(text=text)
        self.running = True
        self._animate()
    
    def stop(self):
        """Arrête l'animation"""
        self.running = False
        self.frame_index = 0
    
    def set_status(self, text: str):
        """Mets à jour le texte de statut"""
        self.status_label.configure(text=text)
    
    def _animate(self):
        """Anime le spinner"""
        if not self.running:
            return
        
        self.spinner_label.configure(text=self.spinner_chars[self.frame_index])
        self.frame_index = (self.frame_index + 1) % len(self.spinner_chars)
        self.after(80, self._animate)


class ProgressBar(ctk.CTkProgressBar):
    """Barre de progression avec animation"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.progress = 0
        self.target = 0
        self.animating = False
    
    def animate_to(self, target: float, duration: int = 2000):
        """Anime la progression vers une valeur cible
        
        Args:
            target: Valeur cible (0-1)
            duration: Durée en millisecondes
        """
        self.target = max(0, min(1, target))
        self.animating = True
        steps = 20
        step_value = (self.target - self.progress) / steps
        step_duration = duration // steps
        
        def step():
            if self.animating and self.progress < self.target:
                self.progress += step_value
                self.set(self.progress)
                self.after(step_duration, step)
            else:
                self.animating = False
        
        step()
    
    def reset(self):
        """Réinitialise la barre"""
        self.set(0)
        self.progress = 0
        self.target = 0

