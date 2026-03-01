"""
Utilitaires de contraste et de couleurs pour garantir la lisibilité
dans tous les thèmes (clair/sombre)
"""

def calculate_luminance(hex_color: str) -> float:
    """Calcule la luminance relative d'une couleur (WCAG)"""
    hex_color = hex_color.lstrip('#')
    r, g, b = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    
    def adjust(c):
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = adjust(r), adjust(g), adjust(b)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return luminance


def calculate_contrast(color1: str, color2: str) -> float:
    """Calcule le ratio de contraste WCAG(1.0 - 21.0)"""
    l1 = calculate_luminance(color1)
    l2 = calculate_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_accessible(color1: str, color2: str, level: str = "AA") -> bool:
    """Vérifie si le contraste atteint le niveau d'accessibilité WCAG"""
    contrast = calculate_contrast(color1, color2)
    # AA = 4.5:1 pour le texte normal, 3:1 pour grand texte
    # AAA = 7:1 pour le texte normal, 4.5:1 pour grand texte
    min_ratio = 7.0 if level == "AAA" else 4.5
    return contrast >= min_ratio


class ThemeColorScheme:
    """Palette de couleurs cohérente garantissant les contrastes"""
    
    LIGHT_SCHEME = {
        "main_bg": "#f8f9fa",
        "card_bg": "#ffffff",
        "card_hover": "#f0f0f0",
        "sidebar_bg": "#ffffff",
        "topbar_bg": "#ffffff",
        
        # Texte (toujours foncé)
        "text_dark": "#1a1a1a",
        "text_light": "#6c757d",
        "text_white": "#ffffff",
        
        # Éléments UI
        "primary": "#4e73df",
        "primary_light": "#6a8aff",
        "primary_dark": "#2e59d9",
        "success": "#1cc88a",
        "success_light": "#22d3ee",
        "warning": "#f6c23e",
        "danger": "#e74a3b",
        "danger_light": "#ef5350",
        "info": "#4e73df",
        "info_light": "#6a8aff",
        
        # Borders et separators
        "border": "#dee2e6",
        "border_light": "#e9ecef",
        "divider": "#dee2e6",
        
        # Badges
        "badge_success": "#d1fae5",
        "badge_warning": "#fef3c7",
        "badge_danger": "#fee2e2",
        "badge_info": "#dbeafe",
    }
    
    DARK_SCHEME = {
        "main_bg": "#0f172a",
        "card_bg": "#1e293b",
        "card_hover": "#334155",
        "sidebar_bg": "#0f172a",
        "topbar_bg": "#1e293b",
        
        # Texte (toujours clair)
        "text_dark": "#f1f5f9",
        "text_light": "#cbd5e1",
        "text_white": "#ffffff",
        
        # Éléments UI - optimisés pour dark
        "primary": "#60a5fa",
        "primary_light": "#93c5fd",
        "primary_dark": "#3b82f6",
        "success": "#34d399",
        "success_light": "#6ee7b7",
        "warning": "#fcd34d",
        "danger": "#f87171",
        "danger_light": "#fca5a5",
        "info": "#60a5fa",
        "info_light": "#93c5fd",
        
        # Borders et separators
        "border": "#334155",
        "border_light": "#475569",
        "divider": "#334155",
        
        # Badges
        "badge_success": "#064e3b",
        "badge_warning": "#713f12",
        "badge_danger": "#7f1d1d",
        "badge_info": "#0c2340",
    }
    
    @staticmethod
    def validate_scheme(scheme: dict, name: str = "Scheme") -> dict:
        """Valide et corrige les contrastes d'une palette de couleurs"""
        issues = {}
        
        # Vérifier les textes sur fonds
        text_on_main = (scheme.get("text_dark"), scheme.get("main_bg"))
        text_on_card = (scheme.get("text_dark"), scheme.get("card_bg"))
        
        for pair, label in [(text_on_main, "text_dark on main_bg"), 
                             (text_on_card, "text_dark on card_bg")]:
            if not is_accessible(pair[0], pair[1], "AA"):
                issues[label] = calculate_contrast(pair[0], pair[1])
        
        return issues
    
    @staticmethod
    def get_text_color(bg_color: str, light_palette: bool = True) -> str:
        """Détermine si le texte doit être clair ou foncé"""
        luminance = calculate_luminance(bg_color)
        if light_palette:
            # En clair, si bg est lumineux, utiliser texte foncé
            return "#1a1a1a" if luminance > 0.5 else "#ffffff"
        else:
            # En sombre, si bg est lumineux, utiliser texte foncé
            return "#0f172a" if luminance > 0.5 else "#f1f5f9"


# Valider les schémas
LIGHT_ISSUES = ThemeColorScheme.validate_scheme(ThemeColorScheme.LIGHT_SCHEME, "Light")
DARK_ISSUES = ThemeColorScheme.validate_scheme(ThemeColorScheme.DARK_SCHEME, "Dark")

if LIGHT_ISSUES or DARK_ISSUES:
    import logging
    logger = logging.getLogger(__name__)
    if LIGHT_ISSUES:
        logger.warning(f"Light theme contrast issues: {LIGHT_ISSUES}")
    if DARK_ISSUES:
        logger.warning(f"Dark theme contrast issues: {DARK_ISSUES}")
