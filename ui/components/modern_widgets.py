"""Composants UI réutilisables"""
import customtkinter as ctk


class StatCard(ctk.CTkFrame):
    """Carte statistique réutilisable"""
    
    def __init__(self, parent, title: str, value: str, color: str, command=None, **kwargs):
        super().__init__(parent, fg_color=color, corner_radius=14, **kwargs)
        
        ctk.CTkLabel(self, text=title.upper(), text_color="white",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkLabel(self, text=value, text_color="white",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=12)
        
        if command:
            ctk.CTkButton(self, text="View", command=command,
                         fg_color=color, hover_color="#111111",
                         border_width=1, border_color="white",
                         text_color="white", height=28).pack(anchor="w", padx=12, pady=(6, 12))


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
