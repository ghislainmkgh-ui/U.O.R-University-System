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
            self.geometry("1200x700")
            self.minsize(800, 600)        
            self.current_screen = None
            self.login_screen = None
            self.dashboard = None
            self.language = "FR"
            self.theme = ThemeManager("light")
            
            # Lancer le login
            self._show_login()
            logger.info("AppWrapper initialized")
        
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
            self.deiconify()
            self.lift()
            self.focus_set()
        
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
