from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

class ReportGenerator:
    """Génère des rapports PDF officiels et structurés pour l'U.O.R."""

    def generer_liste_eligibilite(self, promotion_nom, etudiants_eligibles):
        """Crée un PDF listant les étudiants ayant atteint le seuil financier."""
        nom_fichier = f"Rapport_Eligibilite_{promotion_nom}_{datetime.now().strftime('%Y%m%d')}.pdf"
        c = canvas.Canvas(nom_fichier, pagesize=A4)
        
        # En-tête professionnel
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 800, "UNIVERSITÉ OFFICIELLE DE RUWENZORI (U.O.R)")
        c.setFont("Helvetica", 12)
        c.drawString(100, 780, f"Liste des étudiants éligibles - Promotion : {promotion_nom}")
        c.line(100, 775, 500, 775)

        # Corps du rapport
        y = 750
        c.setFont("Helvetica-Bold", 10)
        c.drawString(100, y, "Matricule")
        c.drawString(200, y, "Nom & Prénom")
        c.drawString(400, y, "Statut Financier")
        
        c.setFont("Helvetica", 10)
        for etu in etudiants_eligibles:
            y -= 20
            c.drawString(100, y, etu['matricule'])
            c.drawString(200, y, f"{etu['nom']} {etu['prenom']}")
            c.drawString(400, y, "SEUIL ATTEINT")
            
            if y < 100: # Gestion du saut de page
                c.showPage()
                y = 800

        c.save()
        return nom_fichier