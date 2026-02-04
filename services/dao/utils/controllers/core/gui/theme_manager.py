import customtkinter as ctk

class ThemeManager:
    """Gère l'aspect visuel moderne et bilingue du logiciel."""
    
    @staticmethod
    def appliquer_mode_sombre():
        ctk.set_appearance_mode("dark")

    @staticmethod
    def appliquer_mode_clair():
        ctk.set_appearance_mode("light")

    @staticmethod
    def get_color_palette():
        # Palette inspirée de SB Admin Pro (Bleu professionnel, Gris doux)
        return {
            "primary": "#4e73df",
            "success": "#1cc88a",
            "warning": "#f6c23e",
            "danger": "#e74a3b"
        }