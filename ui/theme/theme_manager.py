"""Gestionnaire de thème (clair/sombre)"""
from ui.theme.light_theme import LIGHT_THEME
from ui.theme.dark_theme import DARK_THEME


class ThemeManager:
    """Gère les thèmes de l'application"""
    
    THEMES = {
        "light": LIGHT_THEME,
        "dark": DARK_THEME
    }
    
    def __init__(self, theme: str = "light"):
        self.current_theme = theme if theme in self.THEMES else "light"
        self.colors = self.THEMES[self.current_theme]
    
    def set_theme(self, theme: str):
        """Change le thème"""
        if theme in self.THEMES:
            self.current_theme = theme
            self.colors = self.THEMES[theme]
            return True
        return False
    
    def get_color(self, key: str, default: str = "#000000") -> str:
        """Récupère une couleur du thème"""
        return self.colors.get(key, default)
