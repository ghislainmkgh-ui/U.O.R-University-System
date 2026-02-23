"""Overlay de chargement moderne intégré dans la page"""
import customtkinter as ctk
import threading
from typing import Callable, Optional


class LoadingOverlay(ctk.CTkFrame):
    """Overlay de chargement moderne sur la même page (pas popup séparée)"""
    
    def __init__(self, parent, on_cancel: Optional[Callable] = None):
        super().__init__(parent, fg_color="#000000")  # Semi-dark background
        self.on_cancel = on_cancel
        
        # État
        self.progress = 0
        self.status_text = "Initialisation..."
        self.is_complete = False
        self.spinner_index = 0
        self.spinner_chars = ["◐", "◓", "◑", "◒"]
        
        # Créer le contenu au centre
        center_frame = ctk.CTkFrame(self, fg_color="#f8fafc", corner_radius=16, width=380, height=420)
        center_frame.pack_propagate(False)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Titre
        title_label = ctk.CTkLabel(
            center_frame,
            text="U.O.R Chargement",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#1e293b"
        )
        title_label.pack(pady=(20, 25))
        
        # Spinner animé
        self.spinner_label = ctk.CTkLabel(
            center_frame,
            text="◐",
            font=ctk.CTkFont(size=60),
            text_color="#3b82f6"
        )
        self.spinner_label.pack(pady=(0, 20))
        
        # Pourcentage
        self.percent_label = ctk.CTkLabel(
            center_frame,
            text="0%",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="#3b82f6"
        )
        self.percent_label.pack()
        
        # Barre de progression
        progress_bg = ctk.CTkFrame(center_frame, fg_color="#e2e8f0", corner_radius=3, height=5)
        progress_bg.pack(fill="x", padx=20, pady=(20, 0))
        progress_bg.pack_propagate(False)
        
        self.progress_bar = ctk.CTkFrame(progress_bg, fg_color="#3b82f6", corner_radius=3, height=5)
        self.progress_bar.pack(side="left", fill="y")
        self.progress_bar.configure(width=0)
        
        # Status text
        self.status_label = ctk.CTkLabel(
            center_frame,
            text=self.status_text,
            font=ctk.CTkFont(size=11),
            text_color="#64748b"
        )
        self.status_label.pack(pady=(12, 0))
        
        # Bouton annuler
        if self.on_cancel:
            cancel_btn = ctk.CTkButton(
                center_frame,
                text="Annuler",
                command=self._on_cancel,
                fg_color="#ef4444",
                hover_color="#dc2626",
                font=ctk.CTkFont(size=10),
                height=28
            )
            cancel_btn.pack(fill="x", padx=20, pady=(20, 20))
        else:
            # Just padding at the bottom
            ctk.CTkFrame(center_frame, fg_color="transparent", height=20).pack()
        
        self.after(100, self._update_animation)
    
    def set_progress(self, value: int, status: str = None):
        """Mettre à jour la progression (0-100)"""
        self.progress = max(0, min(100, value))
        if status:
            self.status_text = status
    
    def _update_animation(self):
        """Anime le spinner et barre"""
        # Spinner rotatif
        self.spinner_label.configure(text=self.spinner_chars[self.spinner_index])
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
        
        # Pourcentage
        self.percent_label.configure(text=f"{self.progress}%")
        
        # Barre de progression (340 = 380 - 40 padding)
        progress_width = int(340 * (self.progress / 100))
        self.progress_bar.configure(width=progress_width)
        
        # Statut
        self.status_label.configure(text=self.status_text)
        
        if not self.is_complete:
            self.after(150, self._update_animation)
    
    def _on_cancel(self):
        """Gère l'annulation"""
        if self.on_cancel:
            self.on_cancel()
        self.place_forget()
    
    def complete(self):
        """Marquer comme complet"""
        self.is_complete = True
        self.progress = 100
        self.status_text = "Complet ✓"
        
        # Attendre 1 seconde puis disparaître
        self.after(1000, lambda: self.place_forget())
    
    def show(self):
        """Afficher l'overlay"""
        self.place(relx=0, rely=0, relwidth=1, relheight=1)


class ProgressTracker:
    """Tracker pour coordonner la progression multi-étapes"""
    
    def __init__(self):
        self.overlay: Optional[LoadingOverlay] = None
        self.stages = {}
        self.current_stage = 0
    
    def create_overlay(self, parent) -> LoadingOverlay:
        """Créer l'overlay sur la page parent"""
        self.overlay = LoadingOverlay(parent)
        self.overlay.show()
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
