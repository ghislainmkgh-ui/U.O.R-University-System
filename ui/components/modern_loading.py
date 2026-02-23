"""Overlay de chargement moderne avec progression en pourcentage"""
import customtkinter as ctk
import math
import threading
from typing import Callable, Optional


class ModernLoadingOverlay(ctk.CTkToplevel):
    """Fenêtre de chargement moderne avec cercle de progression"""
    
    def __init__(self, parent, title: str = "Chargement", on_cancel: Optional[Callable] = None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Centrer la fenêtre
        self.transient(parent)
        self.grab_set()
        
        # Positionnement central
        x = parent.winfo_x() + parent.winfo_width() // 2 - 200
        y = parent.winfo_y() + parent.winfo_height() // 2 - 250
        self.geometry(f"+{x}+{y}")
        
        # Couleurs
        self.bg_color = "#f8fafc"
        self.primary_color = "#3b82f6"
        self.configure(fg_color=self.bg_color)
        
        # État
        self.progress = 0
        self.status_text = "Initialisation..."
        self.is_complete = False
        self.on_cancel = on_cancel
        
        self._create_ui()
        self.after(100, self._update_animation)
    
    def _create_ui(self):
        """Crée l'interface"""
        main = ctk.CTkFrame(self, fg_color=self.bg_color)
        main.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Titre
        title_label = ctk.CTkLabel(
            main,
            text="U.O.R Chargement",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#1e293b"
        )
        title_label.pack(pady=(0, 30))
        
        # Canvas pour cercle de progression
        self.canvas = ctk.CTkCanvas(
            main,
            width=200,
            height=200,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(pady=(0, 30))
        
        # Label pourcentage
        self.percent_label = ctk.CTkLabel(
            main,
            text="0%",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color=self.primary_color
        )
        self.percent_label.pack()
        
        # Status text
        self.status_label = ctk.CTkLabel(
            main,
            text=self.status_text,
            font=ctk.CTkFont(size=12),
            text_color="#64748b"
        )
        self.status_label.pack(pady=(15, 0))
        
        # Bouton annuler
        if self.on_cancel:
            cancel_btn = ctk.CTkButton(
                main,
                text="Annuler",
                command=self._on_cancel,
                fg_color="#ef4444",
                hover_color="#dc2626",
                font=ctk.CTkFont(size=11),
                height=32
            )
            cancel_btn.pack(fill="x", pady=(30, 0))
    
    def set_progress(self, value: int, status: str = None):
        """Mettre à jour la progression (0-100)"""
        self.progress = max(0, min(100, value))
        if status:
            self.status_text = status
    
    def _draw_circle(self):
        """Dessine le cercle de progression"""
        self.canvas.delete("all")
        
        w, h = 200, 200
        x, y = 100, 100
        radius = 80
        
        # Cercle de fond gris
        self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            outline="#e2e8f0",
            width=8
        )
        
        # Cercle de progression bleu
        if self.progress > 0:
            # Convertir pourcentage en angle (0-360)
            angle = (self.progress / 100) * 360
            
            # Dessiner l'arc de progression
            self.canvas.create_arc(
                x - radius, y - radius,
                x + radius, y + radius,
                start=90,  # Commencer en haut
                extent=-angle,  # Aller dans le sens horaire
                outline=self.primary_color,
                width=8,
                style="arc"
            )
    
    def _update_animation(self):
        """Anime la progression"""
        self._draw_circle()
        self.percent_label.configure(text=f"{self.progress}%")
        self.status_label.configure(text=self.status_text)
        
        if not self.is_complete:
            self.after(100, self._update_animation)
    
    def _on_cancel(self):
        """Gère l'annulation"""
        if self.on_cancel:
            self.on_cancel()
        self.destroy()
    
    def complete(self):
        """Marquer comme complet et fermer"""
        self.is_complete = True
        self.progress = 100
        self.status_text = "Complet ✓"
        
        # Afficher 100% pendant 1 seconde puis fermer
        self.after(500, self.destroy)
    
    def close_immediately(self):
        """Fermer sans animation"""
        self.is_complete = True
        self.destroy()


class ProgressTracker:
    """Tracker pour coordonner la progression multi-étapes"""
    
    def __init__(self):
        self.overlay: Optional[ModernLoadingOverlay] = None
        self.stages = {}
        self.current_stage = 0
    
    def create_overlay(self, parent, title: str = "Chargement") -> ModernLoadingOverlay:
        """Créer l'overlay"""
        self.overlay = ModernLoadingOverlay(parent, title=title)
        return self.overlay
    
    def add_stage(self, name: str, weight: int = 1):
        """Ajouter une étape avec poids"""
        self.stages[name] = {"weight": weight, "complete": False}
    
    def update_stage(self, name: str, completion: float = 1.0):
        """Mettre à jour progression d'une étape"""
        if name in self.stages:
            self.stages[name]["complete"] = completion
            total_weight = sum(s["weight"] for s in self.stages.values())
            completed_weight = sum(
                s["weight"] * s["complete"] for s in self.stages.values()
            )
            progress = int((completed_weight / total_weight) * 100) if total_weight > 0 else 0
            
            if self.overlay:
                self.overlay.set_progress(progress, f"{name}...")
    
    def mark_stage_complete(self, name: str):
        """Marquer une étape comme complète"""
        self.update_stage(name, 1.0)
    
    def complete(self):
        """Marquer le chargement comme complet"""
        if self.overlay:
            self.overlay.complete()
