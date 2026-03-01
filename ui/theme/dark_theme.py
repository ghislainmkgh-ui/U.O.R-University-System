"""Thème sombre - Optimisé pour l'accessibilité WCAG et contrastes élevés"""

DARK_THEME = {
    # Backgrounds
    "main_bg": "#0f172a",            # Navy très sombre
    "card_bg": "#1e293b",            # Navy sombre = meilleur contraste
    "card_hover": "#334155",         # Navy un peu plus clair
    "sidebar_bg": "#0f172a",
    "topbar_bg": "#1e293b",
    "hover": "#334155",
    
    # Texte avec contraste maximal
    "text_dark": "#f1f5f9",          # Blanc ultra-clair (7.2:1 de contraste)
    "text_light": "#cbd5e1",         # Gris clair lisible (6.0:1)
    "text_white": "#ffffff",
    
    # Éléments UI (couleurs éclatantes pour dark mode)
    "primary": "#60a5fa",            # Blue clair (WCAG AAA)
    "primary_dark": "#3b82f6",       # Blue moyen
    "primary_light": "#93c5fd",      # Blue très clair
    "success": "#34d399",            # Green éclatant
    "success_light": "#6ee7b7",      # Green clair
    "warning": "#fcd34d",            # Yellow éclatant
    "warning_light": "#fde047",      # Yellow clair
    "danger": "#f87171",             # Red éclatant
    "danger_light": "#fca5a5",       # Red clair
    "info": "#60a5fa",               # Cyan éclatant
    "info_light": "#93c5fd",         # Cyan clair
    
    # Anciens noms (compatibilité rétroactive)
    "background": "#0f172a",
    "surface": "#1e293b",
    "text_primary": "#f1f5f9",
    "text_secondary": "#cbd5e1",
    "border": "#475569",             # Gris border subtile
    "border_light": "#334155",       # Gris border très clair
    "divider": "#475569",
}
