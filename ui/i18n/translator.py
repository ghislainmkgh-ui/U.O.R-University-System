"""Traductions français/anglais"""
import re

CURRENT_LANGUAGE = "FR"


LITERAL_TRANSLATIONS = {
    "FR": {
        "FR": "FR",
        "EN": "EN",
    },
    "EN": {
        "UNIVERSITY OF REDEMPTION": "UNIVERSITY OF REDEMPTION",
        "Bienvenue dans votre espace d'administration": "Welcome to your administration area",
        "Connectez-vous pour ouvrir l'application et accéder à votre tableau de bord.": "Log in to open the application and access your dashboard.",
        "TABLEAU DE BORD ADMIN": "ADMIN DASHBOARD",
        "Données Académiques": "Academic Data",
        "Transferts": "Transfers",
        "Déconnexion": "Logout",
        "Se déconnecter du système": "Log out of the system",
        "Mode: Compact": "Mode: Compact",
        "Mode: Complet": "Mode: Full",
        "Vue d'ensemble": "Overview",
        "Chargement...": "Loading...",
        "Déconnexion en cours...": "Logging out...",
        "Erreur": "Error",
        "Succès": "Success",
        "Attention": "Warning",
        "Avertissement": "Warning",
        "Annulé": "Cancelled",
        "Confirmation": "Confirmation",
        "Confirmation de déconnexion": "Logout confirmation",
        "Êtes-vous sûr de vouloir vous déconnecter?\n\nVous devrez vous reconnecter pour accéder au système.": "Are you sure you want to log out?\n\nYou will need to sign in again to access the system.",
        "Veuillez entrer vos identifiants": "Please enter your credentials",
        "Connexion échouée": "Login failed",
        "Authentification validée...": "Authentication validated...",
        "Initialisation de la page d'accueil...": "Initializing home page...",
        "Chargement des données...": "Loading data...",
        "Finalisation...": "Finalizing...",
        "Initialisation de l'interface...": "Initializing interface...",
        "Traitement en cours…": "Processing…",
        "Traitement en cours...": "Processing...",
        "OAuth validé…": "OAuth validated…",
        "Token non reçu": "Token not received",
        "Email introuvable": "Email not found",
        "Aucune année académique active": "No active academic year",
        "Veuillez entrer des montants valides (nombres)": "Please enter valid amounts (numbers)",
        "Tous les champs sont requis.": "All fields are required.",
        "La date de fin doit être après le début.": "End date must be after start date.",
        "Format de date invalide. Utilisez AAAA-MM-JJ": "Invalid date format. Use YYYY-MM-DD",
        "Impossible d'ajouter la période.": "Unable to add the period.",
        "Veuillez sélectionner un étudiant dans la liste": "Please select a student from the list",
        "Veuillez entrer le nom du cours": "Please enter the course name",
        "Veuillez entrer la note": "Please enter the grade",
        "Note et crédits doivent être des nombres": "Grade and credits must be numeric",
        "La note doit être entre 0 et 20": "Grade must be between 0 and 20",
        "Veuillez entrer le titre du document": "Please enter the document title",
        "Veuillez sélectionner un étudiant": "Please select a student",
        "Veuillez sélectionner une université de destination": "Please select a destination university",
        "Format université invalide": "Invalid university format",
        "Université introuvable": "University not found",
        "Étudiant introuvable": "Student not found",
        "Veuillez sélectionner une promotion": "Please select a promotion",
        "Promotion introuvable": "Promotion not found",
        "Veuillez indiquer la raison du rejet": "Please provide the rejection reason",
        "Demande de transfert rejetée": "Transfer request rejected",
        "Impossible de rejeter la demande": "Unable to reject the request",
        "Une erreur s'est produite": "An error occurred",
        "Erreur lors de la mise à jour": "Update error",
        "Seuils mis à jour avec succès": "Thresholds updated successfully",
        "Échec": "Failure",
        "Échec de mise à jour.": "Update failed.",
        "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.": "Please create the academic year first in the 'Academic Years' section.",
        "Fermer": "Close",
        "Annuler": "Cancel",
        "Rejeter": "Reject",
        "Approuver": "Approve",
        "Aucune faculté trouvée": "No faculty found",
        "Aucun département trouvé pour cette faculté": "No department found for this faculty",
        "Aucune promotion trouvée pour ce département": "No promotion found for this department",
        "Liste des étudiants par promotion": "Student list by promotion",
        "Informations académiques": "Academic information",
        "Aperçu": "Preview",
        "Aperçu photo": "Photo preview",
        "Historique d'Accès": "Access History",
        "Détail des Tentatives d'Accès": "Access Attempt Details",
        "Aucun log trouvé.": "No log found.",
        "Aucun paiement trouvé.": "No payment found.",
        "Aucun paiement enregistré.": "No payment recorded.",
        "Aucune donnée académique": "No academic data",
        "Dernières Notes": "Latest Grades",
        "Aucun étudiant sélectionné": "No student selected",
        "Aucun étudiant trouvé": "No student found",
        "Aucun étudiant": "No student",
        "Voir Détails": "View Details",
        "Aucun transfert enregistré": "No transfer recorded",
        "Sélectionner un étudiant": "Select a student",
        "Nom de la période:": "Period name:",
        "Date début:": "Start date:",
        "Début:": "Start:",
        "Fin:": "End:",
        "Statistiques Académiques": "Academic Statistics",
        "Comparaison des indicateurs clés": "Key indicators comparison",
        "Répartition Étudiants": "Student Distribution",
        "Sources académiques": "Academic sources",
        "Éligibilité": "Eligibility",
        "Journaux d'Accès": "Access Logs",
        "Consultez l'historique et les logs\nd'accès aux examens en temps réel.": "View exam access history and logs in real time.",
        "Voir les logs →": "View logs →",
        "Résumé Financier": "Financial Summary",
        "Voir finances →": "View finance →",
        "Communication ESP32 (Wi‑Fi)": "ESP32 Communication (Wi‑Fi)",
        "Statut: En attente de connexion ESP32": "Status: Waiting for ESP32 connection",
        "Année académique:": "Academic year:",
        "Sélectionnez une Faculté": "Select a Faculty",
        "Cliquez sur une faculté pour voir ses départements": "Click a faculty to view its departments",
        "Cliquez sur un département pour voir ses promotions": "Click a department to view its promotions",
        "Nouvel Étudiant": "New Student",
        "Remplissez tous les champs requis": "Fill in all required fields",
        "Informations personnelles": "Personal information",
        "Photo du visage (passeport)": "Face photo (passport style)",
        "Parcourir": "Browse",
        "Fond neutre • Visage centré • Une seule personne • Bonne lumière": "Neutral background • Centered face • Single person • Good lighting",
        "Modifier Étudiant": "Edit Student",
        "Valider": "Validate",
        "Enregistrer": "Save",
        "Enregistrer un Paiement": "Record a Payment",
        "Montant à payer": "Amount to pay",
        "Entrez le montant (ex: 50.00)": "Enter amount (e.g. 50.00)",
        "Enregistrer le Paiement": "Save Payment",
        "Historique des Paiements": "Payment History",
        "Filtrer par:": "Filter by:",
        "Statistiques par Faculté": "Statistics by Faculty",
        "Aucune statistique disponible.": "No statistics available.",
        "Frais & Seuils par Faculté → Promotion": "Fees & Thresholds by Faculty → Promotion",
        "Gérer les Périodes d'Examens": "Manage Exam Periods",
        "EMAIL NOTIFICATION": "EMAIL NOTIFICATION",
        "MESSAGE WHATSAPP": "WHATSAPP MESSAGE",
        "Gestion des Périodes d'Examens": "Exam Period Management",
        "Créez et organisez les sessions d'examen pour l'année académique": "Create and organize exam sessions for the academic year",
        "Ajouter une Période d'Examen": "Add an Exam Period",
        "Périodes Actuelles": "Current Periods",
        "Aucune période d'examen définie pour cette année.": "No exam period defined for this year.",
        "Initialisation...": "Initializing...",
        "Valider & Notifier": "Validate & Notify",
        "Gestion des Données Académiques": "Academic Data Management",
        "Ajouter les Données Académiques par Étudiant": "Add Academic Data by Student",
        "Gestion des notes, documents et certificats pour chaque étudiant": "Manage grades, documents, and certificates for each student",
        "Sélectionner un Étudiant": "Select a Student",
        "Faculté *": "Faculty *",
        "Département *": "Department *",
        "Promotion *": "Promotion *",
        "Rechercher un Étudiant": "Search a Student",
        "Nom, prénom ou numéro d'étudiant...": "Name, first name, or student number...",
        "Étudiants de la Promotion": "Students in Promotion",
        "Données Académiques Existantes": "Existing Academic Data",
        "Les données s'afficheront ici...": "Data will appear here...",
        "Ajouter les Données": "Add Data",
        "Documents": "Documents",
        "Nom du Cours *": "Course Name *",
        "Code du Cours": "Course Code",
        "Note (sur 20) *": "Grade (out of 20) *",
        "Date d'Examen": "Exam Date",
        "Professeur": "Professor",
        "Nom du professeur": "Professor name",
        "Ajouter la Note": "Add Grade",
        "Type de Document *": "Document Type *",
        "Titre du Document *": "Document Title *",
        "Auteur": "Author",
        "Description": "Description",
        "Ajouter le Document": "Add Document",
        "Transferts Inter-Universitaires": "Inter-University Transfers",
        "Initier un Transfert Sortant": "Initiate Outgoing Transfer",
        "Sélection Hiérarchique": "Hierarchical Selection",
        "Faculté :": "Faculty:",
        "Département :": "Department:",
        "Promotion :": "Promotion:",
        "Étudiants": "Students",
        "Rechercher :": "Search:",
        "Nom, Numéro ou Email": "Name, Number or Email",
        "Informations Étudiant": "Student Information",
        "Détails du Transfert": "Transfer Details",
        "Université de destination :": "Destination University:",
        "URL API de réception (modifiable) :": "Receiving API URL (editable):",
        "Sauvegarder l'URL API": "Save API URL",
        "Inclure les documents et ouvrages": "Include documents and works",
        "Notes (optionnel) :": "Notes (optional):",
        "Générer": "Generate",
        "Rafraîchir": "Refresh",
        "Aucun étudiant actif\ndans cette promotion": "No active student\nin this promotion",
        "Demandes de Transfert Entrantes": "Incoming Transfer Requests",
        "Aucune demande de transfert en attente": "No pending transfer request",
        "EN ATTENTE": "PENDING",
        "Approuver": "Approve",
        "Rejeter": "Reject",
        "Historique des Transferts": "Transfer History",
        "Erreur lors de l'affichage des informations": "Error displaying information",
        "Notes d'approbation:": "Approval notes:",
    },
}


TERM_TRANSLATIONS = {
    "EN": {
        "Année académique": "Academic year",
        "Années académiques": "Academic years",
        "Période d'examen": "Exam period",
        "Périodes d'examens": "Exam periods",
        "Période": "Period",
        "Périodes": "Periods",
        "Faculté": "Faculty",
        "Facultés": "Faculties",
        "faculté": "faculty",
        "facultés": "faculties",
        "Département": "Department",
        "Départements": "Departments",
        "département": "department",
        "départements": "departments",
        "Promotion": "Promotion",
        "Promotions": "Promotions",
        "promotion": "promotion",
        "promotions": "promotions",
        "Étudiant": "Student",
        "Étudiants": "Students",
        "Étudiante": "Student",
        "Étudiantes": "Students",
        "étudiant": "student",
        "étudiants": "students",
        "étudiante": "student",
        "étudiantes": "students",
        "Inscrits": "Registered",
        "Inscrit": "Registered",
        "inscrits": "registered",
        "inscrit": "registered",
        "Sélectionner": "Select",
        "Sélectionnez": "Select",
        "sélectionnez": "select",
        "Ajouter": "Add",
        "ajouter": "add",
        "Modifier": "Edit",
        "modifier": "edit",
        "Supprimer": "Delete",
        "supprimer": "delete",
        "Gérer": "Manage",
        "Gestion": "Management",
        "Données": "Data",
        "Donnée": "Data",
        "Académiques": "Academic",
        "Académique": "Academic",
        "académiques": "academic",
        "académique": "academic",
        "Historique": "History",
        "Accès": "Access",
        "Tentatives": "Attempts",
        "Répartition": "Distribution",
        "Résumé": "Summary",
        "Financier": "Financial",
        "Finances": "Finance",
        "Voir": "View",
        "Rapport": "Report",
        "Aucun": "No",
        "Aucune": "No",
        "trouvé": "found",
        "trouvée": "found",
        "trouvés": "found",
        "trouvées": "found",
        "introuvable": "not found",
        "liste": "list",
        "cours": "course",
        "note": "grade",
        "notes": "grades",
        "Crédits": "Credits",
        "Titre": "Title",
        "Catégorie": "Category",
        "Rafraîchir": "Refresh",
        "Réinitialiser": "Reset",
        "Générer": "Generate",
        "Université": "University",
        "destination": "destination",
        "Informations": "Information",
        "détails": "details",
        "Détails": "Details",
        "Rechercher": "Search",
    }
}


def set_current_language(language: str):
    """Met à jour la langue UI globale active."""
    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = language if language in TRANSLATIONS else "FR"


def get_current_language() -> str:
    """Retourne la langue UI globale active."""
    return CURRENT_LANGUAGE if CURRENT_LANGUAGE in TRANSLATIONS else "FR"


def translate_ui_text(text, language: str = None):
    """Traduit un texte littéral selon la langue active.

    - FR: retourne le texte tel quel
    - EN: applique d'abord les traductions exactes puis des remplacements de fragments
    """
    if not isinstance(text, str):
        return text

    target_lang = language if language in TRANSLATIONS else get_current_language()
    if target_lang == "FR":
        return text

    lang_map = LITERAL_TRANSLATIONS.get(target_lang, {})
    translated = lang_map.get(text, text)

    # Traduction via correspondance exacte de valeurs FR issues des clés i18n
    if translated == text and target_lang != "FR":
        fr_dict = TRANSLATIONS.get("FR", {})
        target_dict = TRANSLATIONS.get(target_lang, {})
        fr_to_key = {}
        for k, v in fr_dict.items():
            if isinstance(v, str) and v not in fr_to_key:
                fr_to_key[v] = k
        key = fr_to_key.get(text)
        if key:
            maybe = target_dict.get(key)
            if isinstance(maybe, str) and maybe:
                translated = maybe

    # Remplacements contextuels (du plus long au plus court)
    for src, dst in sorted(lang_map.items(), key=lambda kv: len(kv[0]), reverse=True):
        if src in translated:
            translated = translated.replace(src, dst)

    needs_fallback = (translated == text)

    # Remplacements dérivés du dictionnaire FR -> langue cible (par fragments)
    if target_lang != "FR" and needs_fallback:
        fr_dict = TRANSLATIONS.get("FR", {})
        target_dict = TRANSLATIONS.get(target_lang, {})
        fr_pairs = []
        for k, fr_text in fr_dict.items():
            tgt_text = target_dict.get(k)
            if isinstance(fr_text, str) and isinstance(tgt_text, str) and fr_text and tgt_text and fr_text != tgt_text:
                fr_pairs.append((fr_text, tgt_text))
        for src, dst in sorted(fr_pairs, key=lambda kv: len(kv[0]), reverse=True):
            if src in translated:
                translated = translated.replace(src, dst)

    # Glossaire de termes métier (fallback)
    if needs_fallback:
        term_map = TERM_TRANSLATIONS.get(target_lang, {})
        for src, dst in sorted(term_map.items(), key=lambda kv: len(kv[0]), reverse=True):
            pattern = re.compile(rf"(?<!\w){re.escape(src)}(?!\w)")
            translated = pattern.sub(dst, translated)

    return translated

TRANSLATIONS = {
    "FR": {
        # Langue et plateforme
        "language": "Langue",
        "exam_access_platform": "Plateforme d'Accès aux Examens",
        
        # Navigation
        "dashboard": "Tableau de Bord",
        "students": "Étudiants",
        "finance": "Finances",
        "access_logs": "Logs d'Accès",
        "reports": "Rapports",
        "academic_years": "Années Acad.",
        "settings": "Paramètres",
        "theme": "Thème",
        "light_theme": "Clair",
        "dark_theme": "Sombre",
        
        # Authentification
        "login": "Connexion",
        "logout": "Déconnexion",
        "username": "Nom d'utilisateur",
        "password": "Mot de passe",
        "remember_me": "Se souvenir de moi",
        "welcome": "Bienvenue",
        "access_granted": "Accès Autorisé",
        "access_denied": "Accès Refusé",
        
        # Dashboard
        "total_students": "Total Étudiants",
        "eligible": "Éligibles",
        "non_eligible": "Non Éligibles",
        "recent_activity": "Activité Récente",
        "access_attempt": "Tentative d'Accès",
        "granted": "Autorisé",
        "denied": "Refusé",
        "overview": "Vue d'ensemble",
        "dashboard_title": "Dashboard",
        "dashboard_subtitle": "Vue d'ensemble",
        
        # Étudiants
        "student_number": "Matricule d'Étudiant",
        "firstname": "Prénom",
        "lastname": "Nom",
        "email": "Email",
        "faculty": "Faculté",
        "department": "Département",
        "promotion": "Promotion",
        "status": "Statut",
        "active": "Actif",
        "inactive": "Inactif",
        
        # Finances
        "amount_paid": "Montant Payé",
        "threshold": "Seuil",
        "remaining": "Restant",
        "payment": "Paiement",
        "payment_date": "Date de Paiement",
        "eligible_students": "Étudiants Éligibles",
        "non_eligible_students": "Étudiants Non Éligibles",
        "total_collected": "Total Collecté",
        
        # Logs
        "access_point": "Point d'Accès",
        "timestamp": "Date/Heure",
        "password_check": "Vérification Mot de Passe",
        "face_recognition": "Reconnaissance Faciale",
        "finance_check": "Vérification Finances",
        "verified": "Vérifiée",
        "failed": "Échouée",
        
        # Boutons
        "add": "Ajouter",
        "add_student": "Ajouter Étudiant",
        "add_payment": "Ajouter Paiement",
        "edit": "Modifier",
        "delete": "Supprimer",
        "save": "Enregistrer",
        "cancel": "Annuler",
        "submit": "Soumettre",
        "view": "Voir",
        "search": "Rechercher",
        "search_placeholder": "Nom, ID ou email...",
        "export": "Exporter",
        "import": "Importer",
        "refresh": "Actualiser",
        
        # Messages
        "loading": "Chargement...",
        "success": "Succès",
        "error": "Erreur",
        "warning": "Avertissement",
        "no_data": "Aucune donnée",
        "no_students": "Aucun étudiant trouvé.",
        "invalid_input": "Entrée invalide",
        "confirm_delete": "Êtes-vous sûr?",

        "students_title": "Gestion des Étudiants",
        "students_subtitle": "Gestion et suivi des étudiants",
        "finance_title": "Gestion Financière",
        "finance_subtitle": "Suivi des paiements et seuils",
        "access_logs_title": "Historique d'Accès",
        "access_logs_subtitle": "Suivi des tentatives d'accès",
        "reports_title": "Rapports et Statistiques",
        "reports_subtitle": "Analyse par faculté et performance",
        "academic_years_title": "Années Académiques",
        "academic_years_subtitle": "Gestion des seuils financiers et périodes d'examens",
        
        # Dashboard Détaillé (Nouveau)
        "academic_platform": "Plateforme d'Accès Académique",
        "platform_description": "Gestion académique centralisée pour l'accès sécurisé aux examens",
        "manage_eligibility": "Contrôlez l'éligibilité des étudiants",
        "track_payments": "Suivez les paiements",
        "view_access_history": "Consultez l'historique d'accès",
        "exam_access_security": "temps réel",
        
        # Statistiques Dashboard
        "total_students": "Total Étudiants",
        "eligible_count": "Éligibles",
        "non_eligible_count": "Non Éligibles",
        "access_statistics": "Statistiques d'Accès",
        "granted_count": "Autorisés",
        "denied_count": "Refusés",
        "completion_rate": "Taux d'Éligibilité",
        "financial_overview": "Aperçu Financier",
        "total_revenue": "Revenus Totaux",
        "recent_activities": "Activités Récentes",
        "no_activities": "Aucune activité récente",
        
        # Cartes Dashboard
        "platform_card_title": "📚 Plateforme d'Accès aux Examens",
        "activities_card_title": "🕐 Activités Récentes",
        "eligibility_card_title": "📊 Taux d'Éligibilité",
        "access_card_title": "🔐 Accès",
        "finance_card_title": "💰 Finances",
        
        # Graphiques
        "real_time": "Temps réel",
        "access_evolution": "Évolution des accès",
        "financial_evolution": "Évolution financière",
        "last_30_days": "Derniers 30 jours",
        "growth_rate": "Taux de croissance",
        "completion": "Complétion",
        
        # Actions
        "view_details": "Voir Détails",
        "manage_students": "Gérer Les Étudiants",
        "manage_finance": "Gérer Les Finances",
        "view_logs": "Voir Les Journaux",
        "generate_report": "Générer Rapport",
        
        # Dialogues et Modales
        "confirmation": "Confirmation",
        "are_you_sure": "Êtes-vous sûr?",
        "yes": "Oui",
        "no": "Non",
        "ok": "D'accord",
        "close": "Fermer",
        
        # Messages d'Erreur et de Succès
        "operation_success": "Opération réussie",
        "operation_failed": "L'opération a échoué",
        "please_try_again": "Veuillez réessayer",
        "network_error": "Erreur réseau",
        "connection_lost": "Connexion perdue",
        "reconnecting": "Reconnexion",
        
        # Formatage de Données
        "currency_symbol": "FC",
        "date_format": "%d/%m/%Y",
        "time_format": "%H:%M:%S",
        "datetime_format": "%d/%m/%Y %H:%M",

        # Écran de connexion
        "user_login": "CONNEXION UTILISATEUR",
        "email_id": "\U0001f4e7  Email / Identifiant",
        "password_label": "\U0001f512  Mot de passe",
        "forgot_password": "Mot de passe oublié ?",
        "login_btn": "CONNEXION",
        "create_admin_btn": "CRÉER COMPTE",
        "create_admin_title": "Créer un compte administrateur",
        "create_admin_username_ph": "admin.username",
        "create_admin_email_ph": "admin@example.com",
        "create_admin_success": "Compte administrateur créé avec succès ✓",
        "create_admin_min_length": "Le mot de passe doit avoir au moins 6 caractères",
        "or_separator": "ou",
        "login_google": "  G   Continuer avec Google",
        "login_github": "  ⬡   Continuer avec GitHub",
        "enter_credentials": "Veuillez entrer vos identifiants",

        # Dialogue mot de passe oublié
        "fp_title": "Réinitialiser le mot de passe",
        "fp_identifier_label": "Email ou matricule",
        "fp_identifier_ph": "email@example.com ou MAT2024001",
        "fp_new_password": "Nouveau mot de passe",
        "fp_confirm_password": "Confirmer le mot de passe",
        "fp_reset_btn": "Réinitialiser",
        "fp_cancel_btn": "Annuler",
        "fp_no_match": "Les mots de passe ne correspondent pas",
        "fp_missing_fields": "Veuillez remplir tous les champs",
        "fp_not_found": "Aucun compte trouvé pour cet identifiant",
        "fp_success": "Mot de passe réinitialisé avec succès ✓",
        "fp_min_length": "Le mot de passe doit avoir au moins 4 caractères",
    },
    "EN": {
        # Language and platform
        "language": "Language",
        "exam_access_platform": "Exam Access Platform",
        
        # Navigation
        "dashboard": "Dashboard",
        "students": "Students",
        "finance": "Finance",
        "access_logs": "Access Logs",
        "reports": "Reports",
        "academic_years": "Academic Years",
        "settings": "Settings",
        "theme": "Theme",
        "light_theme": "Light",
        "dark_theme": "Dark",
        
        # Authentication
        "login": "Login",
        "logout": "Logout",
        "username": "Username",
        "password": "Password",
        "remember_me": "Remember me",
        "welcome": "Welcome",
        "access_granted": "Access Granted",
        "access_denied": "Access Denied",
        
        # Dashboard
        "total_students": "Total Students",
        "eligible": "Eligible",
        "non_eligible": "Non-Eligible",
        "recent_activity": "Recent Activity",
        "access_attempt": "Access Attempt",
        "granted": "Granted",
        "denied": "Denied",
        "overview": "Overview",
        "dashboard_title": "Dashboard",
        "dashboard_subtitle": "Overview",
        
        # Students
        "student_number": "Student Number",
        "firstname": "First Name",
        "lastname": "Last Name",
        "email": "Email",
        "faculty": "Faculty",
        "department": "Department",
        "promotion": "Promotion",
        "status": "Status",
        "active": "Active",
        "inactive": "Inactive",
        
        # Finance
        "amount_paid": "Amount Paid",
        "threshold": "Threshold",
        "remaining": "Remaining",
        "payment": "Payment",
        "payment_date": "Payment Date",
        "eligible_students": "Eligible Students",
        "non_eligible_students": "Non-Eligible Students",
        "total_collected": "Total Collected",
        
        # Logs
        "access_point": "Access Point",
        "timestamp": "Date/Time",
        "password_check": "Password Check",
        "face_recognition": "Face Recognition",
        "finance_check": "Finance Check",
        "verified": "Verified",
        "failed": "Failed",
        
        # Buttons
        "add": "Add",
        "add_student": "Add Student",
        "add_payment": "Add Payment",
        "edit": "Edit",
        "delete": "Delete",
        "save": "Save",
        "cancel": "Cancel",
        "submit": "Submit",
        "view": "View",
        "search": "Search",
        "search_placeholder": "Name, ID or email...",
        "export": "Export",
        "import": "Import",
        "refresh": "Refresh",
        
        # Messages
        "loading": "Loading...",
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "no_data": "No data",
        "no_students": "No students found.",
        "invalid_input": "Invalid input",
        "confirm_delete": "Are you sure?",

        "students_title": "Student Management",
        "students_subtitle": "Manage and track students",
        "finance_title": "Finance Management",
        "finance_subtitle": "Payments and thresholds monitoring",
        "access_logs_title": "Access History",
        "access_logs_subtitle": "Track access attempts",
        "reports_title": "Reports and Statistics",
        "reports_subtitle": "Analysis by faculty and performance",
        "academic_years_title": "Academic Years",
        "academic_years_subtitle": "Manage thresholds and exam periods",
        
        # Detailed Dashboard (New)
        "academic_platform": "Academic Access Platform",
        "platform_description": "Centralized academic management for secure exam access",
        "manage_eligibility": "Control student eligibility",
        "track_payments": "Track payments",
        "view_access_history": "View access history",
        "exam_access_security": "Real-time",
        
        # Dashboard Statistics
        "total_students": "Total Students",
        "eligible_count": "Eligible",
        "non_eligible_count": "Non-Eligible",
        "access_statistics": "Access Statistics",
        "granted_count": "Granted",
        "denied_count": "Denied",
        "completion_rate": "Eligibility Rate",
        "financial_overview": "Financial Overview",
        "total_revenue": "Total Revenue",
        "recent_activities": "Recent Activities",
        "no_activities": "No recent activities",
        
        # Dashboard Cards
        "platform_card_title": "📚 Exam Access Platform",
        "activities_card_title": "🕐 Recent Activities",
        "eligibility_card_title": "📊 Eligibility Rate",
        "access_card_title": "🔐 Access",
        "finance_card_title": "💰 Finance",
        
        # Charts
        "real_time": "Real-time",
        "access_evolution": "Access Evolution",
        "financial_evolution": "Financial Evolution",
        "last_30_days": "Last 30 Days",
        "growth_rate": "Growth Rate",
        "completion": "Completion",
        
        # Actions
        "view_details": "View Details",
        "manage_students": "Manage Students",
        "manage_finance": "Manage Finance",
        "view_logs": "View Logs",
        "generate_report": "Generate Report",
        
        # Dialogs and Modals
        "confirmation": "Confirmation",
        "are_you_sure": "Are you sure?",
        "yes": "Yes",
        "no": "No",
        "ok": "Okay",
        "close": "Close",
        
        # Error and Success Messages
        "operation_success": "Operation successful",
        "operation_failed": "Operation failed",
        "please_try_again": "Please try again",
        "network_error": "Network error",
        "connection_lost": "Connection lost",
        "reconnecting": "Reconnecting",
        
        # Data Formatting
        "currency_symbol": "FC",
        "date_format": "%d/%m/%Y",
        "time_format": "%H:%M:%S",
        "datetime_format": "%d/%m/%Y %H:%M",

        # Login screen
        "user_login": "USER LOGIN",
        "email_id": "\U0001f4e7  Email / Username",
        "password_label": "\U0001f512  Password",
        "forgot_password": "Forgot Password?",
        "login_btn": "LOGIN",
        "create_admin_btn": "CREATE ACCOUNT",
        "create_admin_title": "Create administrator account",
        "create_admin_username_ph": "admin.username",
        "create_admin_email_ph": "admin@example.com",
        "create_admin_success": "Administrator account created successfully ✓",
        "create_admin_min_length": "Password must be at least 6 characters",
        "or_separator": "or",
        "login_google": "  G   Continue with Google",
        "login_github": "  ⬡   Continue with GitHub",
        "enter_credentials": "Please enter your credentials",

        # Forgot password dialog
        "fp_title": "Reset Password",
        "fp_identifier_label": "Email or student ID",
        "fp_identifier_ph": "email@example.com or ID2024001",
        "fp_new_password": "New password",
        "fp_confirm_password": "Confirm password",
        "fp_reset_btn": "Reset",
        "fp_cancel_btn": "Cancel",
        "fp_no_match": "Passwords do not match",
        "fp_missing_fields": "Please fill in all fields",
        "fp_not_found": "No account found for this identifier",
        "fp_success": "Password reset successfully ✓",
        "fp_min_length": "Password must be at least 4 characters",
    }
}


class Translator:
    """Service de traduction"""
    
    def __init__(self, language: str = "FR"):
        self.language = language if language in TRANSLATIONS else "FR"
        set_current_language(self.language)
    
    def set_language(self, language: str):
        """Change la langue"""
        if language in TRANSLATIONS:
            self.language = language
            set_current_language(language)
            return True
        return False
    
    def get(self, key: str, default: str = None) -> str:
        """Récupère une traduction"""
        text = TRANSLATIONS[self.language].get(key, None)
        return text if text else (default or key)
    
    def _(self, key: str) -> str:
        """Alias pour get()"""
        return self.get(key)

    def translate_literal(self, text: str) -> str:
        """Traduit un texte littéral non basé sur une clé i18n."""
        return translate_ui_text(text, self.language)
