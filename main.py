"""Point d'entrée principal de l'application U.O.R"""
import sys
import os
import logging
import customtkinter as ctk

# Ajouter le répertoire racine à sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialiser le logging
from config.logger import logger
from config.settings import APP_NAME, APP_VERSION, DEBUG

logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
logger.info(f"Debug mode: {DEBUG}")

try:
    from ui.screens.login_screen import LoginScreen
    from ui.screens.admin.admin_dashboard import AdminDashboard
    from ui.theme.theme_manager import ThemeManager
    
    class AppWrapper(ctk.CTk):
        """Wrapper principal qui gère le login et le dashboard"""
        
        def __init__(self):
            super().__init__()
            
            self.title("U.O.R - Système de Contrôle d'Accès")
            
            # Calcul responsive de la géométrie initiale
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Default size: 70% écran, min 800x600, max full screen
            default_width = max(800, min(1200, int(screen_width * 0.7)))
            default_height = max(600, min(900, int(screen_height * 0.75)))
            
            # Centrer
            x = (screen_width - default_width) // 2
            y = (screen_height - default_height) // 2
            
            self.geometry(f"{default_width}x{default_height}+{x}+{y}")
            self.minsize(800, 600)  # Minimum acceptable
            self.maxsize(screen_width, screen_height)
            
            self.current_screen = None
            self.login_screen = None
            self.dashboard = None
            self.language = "FR"
            self.theme = ThemeManager("light")
            
            # Bind resize event pour responsive adjustments
            self.bind("<Configure>", self._on_window_resize)
            
            # Lancer le login
            self._show_login()
            # Forcer l'affichage au premier plan
            self.after(150, self._force_show)
            logger.info("AppWrapper initialized")
        
        def _on_window_resize(self, event=None):
            """Gère les ajustements lors du redimensionnement"""
            try:
                # Si on a un dashboard ou login, on peut déclencher des updates responsive
                if self.dashboard and hasattr(self.dashboard, '_on_resize'):
                    self.dashboard._on_resize(event)
            except Exception as e:
                logger.debug(f"Resize handler error: {e}")
        
        def _show_login(self):
            """Affiche l'écran de login"""
            logger.info("Showing login screen")
            if self.login_screen:
                try:
                    self.login_screen.destroy()
                except:
                    pass
            
            self.login_screen = LoginScreen(parent_app=self)
            self.current_screen = "login"
            self._force_show()

        def _force_show(self):
            """Force l'affichage de la fenêtre principale"""
            try:
                self.update_idletasks()
                self.deiconify()
                self.lift()
                self.focus_force()
                try:
                    self.attributes("-topmost", True)
                    self.after(200, lambda: self.attributes("-topmost", False))
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"Force show error: {e}")
        
        def _show_dashboard(self, language="FR"):
            """Affiche le dashboard"""
            logger.info("Showing dashboard")
            self.language = language
            
            # Fermer le login
            if self.login_screen:
                try:
                    self.login_screen.destroy()
                except:
                    pass
            
            # Créer le dashboard comme frame dans le wrapper
            self.dashboard = AdminDashboard(parent=self, language=language, theme=self.theme)
            self.current_screen = "dashboard"
    
    def main():
        """Lance l'application"""
        app = AppWrapper()
        app.mainloop()
    
    if __name__ == "__main__":
        main()
        logger.info("Application terminated normally")
        
except Exception as e:
    logger.critical(f"Failed to start application: {e}", exc_info=True)
    sys.exit(1)
