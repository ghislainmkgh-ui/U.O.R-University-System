import logging
from datetime import datetime

class ServiceAuditLogger:
    """Génère des journaux d'audit pour la surveillance de la plateforme."""

    def __init__(self):
        logging.basicConfig(
            filename='logs/uor_system_audit.log',
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s'
        )

    def log_evenement(self, utilisateur, action, statut):
        """Enregistre une trace indélébile de l'activité."""
        message = f"Utilisateur: {utilisateur} | Action: {action} | Statut: {statut}"
        logging.info(message)
        if statut == "ECHEC_CRITIQUE":
            logging.warning(f"ALERTE SECURITE : Tentative suspecte par {utilisateur}")