import sys
import os

from services.dao.utils.controllers.core.gui.login_window import LoginWindow
from services.dao.utils.controllers.admin_controller import ControleurAdmin
from services.dao.utils.lang_manager import GestionnaireLangue
from services.dao.utils.controllers.core.gui.main_window import DashboardPrincipal
from services.dao.etudiant_dao import EtudiantDAO
from services.report_service import ServiceRapports
from services.dao.DatabaseConnection import DatabaseConnection

class ApplicationOrchestrator:
    """Initialise et coordonne tous les composants du logiciel U.O.R."""

    def __init__(self):
        # 1. Initialisation des composants de données (DAO)
        self.etudiant_dao = EtudiantDAO()
        
        # 2. Initialisation des services métier
        self.rapport_service = ServiceRapports()
        self.lang_manager = GestionnaireLangue(langue_par_defaut="FR")
        
        # 3. Initialisation du contrôleur principal
        self.ctrl_admin = ControleurAdmin(
            self.etudiant_dao, 
            self.rapport_service, 
            self.lang_manager
        )

    def lancer_application(self):
        """Démarre le flux : Login -> Dashboard."""
        self.login_view = LoginWindow(on_login_success=self.ouvrir_dashboard)
        self.login_view.mainloop()

    def ouvrir_dashboard(self):
        """Lance l'interface principale après authentification."""
        self.app_principale = DashboardPrincipal(self.ctrl_admin)
        self.app_principale.mainloop()

# DÉMARRAGE DU LOGICIEL
if __name__ == "__main__":
    app = ApplicationOrchestrator()
    app.lancer_application()