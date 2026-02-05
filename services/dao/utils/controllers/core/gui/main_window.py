import customtkinter as ctk
from services.dao.utils.controllers.core.gui.components.sidebar import SidebarNavigation

class DashboardPrincipal(ctk.CTk):
    def __init__(self, controleur_admin):
        super().__init__()
        self.ctrl = controleur_admin
        self.lang_manager = getattr(self.ctrl, "lang", None)
        self.current_lang = "FR"
        
        # Configuration de la fenêtre
        self.title("U.O.R - Plateforme de Contrôle d'Accès")
        self.geometry("1100x600")
        
        # Configuration du Layout (Grille)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Barre latérale
        self.sidebar = SidebarNavigation(self, self.get_nav_callbacks())
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Zone de contenu principal (Dashboard)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.show_dashboard()

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def creer_widgets_stats(self):
        """Crée le dashboard moderne (header, cartes, activité, progrès)."""
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=2)

        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_stack = ctk.CTkFrame(header, fg_color="transparent")
        title_stack.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(title_stack, text=self._t("dashboard", "Dashboard"),
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(title_stack, text="Résumé des accès, finances et activités.",
                     text_color="#6c757d").pack(anchor="w")

        date_chip = ctk.CTkButton(header, text="Févr 2026", corner_radius=18,
                                  fg_color="#4e73df", hover_color="#2e59d9")
        date_chip.grid(row=0, column=1, sticky="e", padx=(0, 10))

        cards = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        cards.grid(row=1, column=0, columnspan=2, sticky="ew")
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1)

        self._create_stat_card(cards, 0, "Éligibles", "540", "Voir", "#1cc88a", self.show_eligibles)
        self._create_stat_card(cards, 1, "Non éligibles", "120", "Voir", "#f6c23e", self.show_non_eligibles)
        self._create_stat_card(cards, 2, "Fraudes détectées", "07", "Voir", "#e74a3b", self.show_non_eligibles)
        self._create_stat_card(cards, 3, "Requêtes en cours", "24", "Voir", "#4e73df", self.show_etudiants)

        left_col = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        left_col.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(10, 0))
        left_col.grid_rowconfigure(1, weight=1)

        chart_card = ctk.CTkFrame(left_col)
        chart_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(chart_card, text="Évolution des accès", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(chart_card, text="(Graphique à connecter)", text_color="#6c757d").pack(anchor="w", padx=16, pady=(0, 12))

        activity_card = ctk.CTkFrame(left_col)
        activity_card.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(activity_card, text="Activités récentes", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(12, 6))
        for item in [
            "Entrée validée — Admin 08:40",
            "Accès refusé — Étudiant #492",
            "Paiement confirmé — Finance",
            "Session terminée — Porte A2"
        ]:
            ctk.CTkLabel(activity_card, text=f"• {item}").pack(anchor="w", padx=16, pady=2)

        right_col = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        right_col.grid(row=2, column=1, sticky="nsew", pady=(10, 0))
        right_col.grid_rowconfigure(1, weight=1)

        progress_card = ctk.CTkFrame(right_col)
        progress_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(progress_card, text="Progress Tracker", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(12, 8))
        self._progress_row(progress_card, "Seuil financier", 0.78, "#1cc88a")
        self._progress_row(progress_card, "Reconnaissance faciale", 0.54, "#4e73df")
        self._progress_row(progress_card, "Contrôle accès", 0.32, "#f6c23e")

        status_card = ctk.CTkFrame(right_col)
        status_card.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(status_card, text="État du système", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkLabel(status_card, text="• API Finance : OK", text_color="#1cc88a").pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(status_card, text="• Caméras : OK", text_color="#1cc88a").pack(anchor="w", padx=16, pady=2)
        ctk.CTkLabel(status_card, text="• Portes : En attente", text_color="#f6c23e").pack(anchor="w", padx=16, pady=2)

    def show_dashboard(self):
        self.clear_main_frame()
        self.creer_widgets_stats()

    def show_etudiants(self):
        self.clear_main_frame()
        title = ctk.CTkLabel(self.main_frame, text="Gestion Étudiants",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))
        ctk.CTkLabel(self.main_frame, text="Sélectionnez une faculté, département et promotion.") \
            .grid(row=1, column=0, sticky="w")

    def show_eligibles(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Étudiants éligibles",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w")
        self._render_stats_list("eligibles")

    def show_non_eligibles(self):
        self.clear_main_frame()
        ctk.CTkLabel(self.main_frame, text="Étudiants non éligibles",
                     font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, sticky="w")
        self._render_stats_list("non_payes")

    def _render_stats_list(self, key):
        try:
            stats = self.ctrl.obtenir_stats_financieres()
            items = stats.get(key, []) if isinstance(stats, dict) else []
            if not items:
                ctk.CTkLabel(self.main_frame, text="Aucune donnée à afficher.") \
                    .grid(row=1, column=0, sticky="w", pady=(10, 0))
                return
            for idx, item in enumerate(items, start=1):
                ctk.CTkLabel(self.main_frame, text=f"{idx}. {item}") \
                    .grid(row=idx, column=0, sticky="w", pady=2)
        except Exception as exc:
            ctk.CTkLabel(self.main_frame, text=f"Erreur lors du chargement: {exc}", text_color="#e74a3b") \
                .grid(row=1, column=0, sticky="w", pady=(10, 0))

    def change_language(self, label):
        mapping = {"Français": "FR", "English": "EN"}
        lang = mapping.get(label, "FR")
        if self.lang_manager:
            self.lang_manager.changer_langue(lang)
        self.current_lang = lang
        self.show_dashboard()

    def _t(self, key, fallback):
        if self.lang_manager:
            return self.lang_manager.get_texte(key)
        return fallback

    def _create_stat_card(self, parent, column, title, value, action_label, color, action):
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=14)
        card.grid(row=0, column=column, padx=8, pady=6, sticky="nsew")
        ctk.CTkLabel(card, text=title.upper(), text_color="white",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=12, pady=(12, 4))
        ctk.CTkLabel(card, text=value, text_color="white",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=12)
        ctk.CTkButton(card, text=action_label, command=action,
                      fg_color=color, hover_color="#111111",
                      border_width=1, border_color="white",
                      text_color="white", height=28).pack(anchor="w", padx=12, pady=(6, 12))

    def _progress_row(self, parent, label, value, color):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(row, text=label).pack(anchor="w")
        bar = ctk.CTkProgressBar(row, progress_color=color)
        bar.pack(fill="x", pady=(4, 0))
        bar.set(value)

    def get_nav_callbacks(self):
        return {
            'dashboard': self.show_dashboard,
            'etudiants': self.show_etudiants,
            'langue': self.change_language
        }