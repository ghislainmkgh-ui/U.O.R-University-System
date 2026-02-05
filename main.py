"""Point d'entrée principal de l'application U.O.R"""
import sys
import os
import logging

# Ajouter le répertoire racine à sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialiser le logging
from config.logger import logger
from config.settings import APP_NAME, APP_VERSION, DEBUG

logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
logger.info(f"Debug mode: {DEBUG}")

try:
    from ui.screens.login_screen import LoginScreen
    
    def main():
        """Lance l'application"""
        app = LoginScreen()
        app.mainloop()
    
    if __name__ == "__main__":
        main()
        logger.info("Application terminated normally")
        
except Exception as e:
    logger.critical(f"Failed to start application: {e}", exc_info=True)
    sys.exit(1)
