import requests
"""Dashboard administrateur moderne - Style SB Admin Pro"""
import customtkinter as ctk
import logging
import os
import shutil
import io
import hashlib
import threading
import re
import time
from datetime import datetime
from decimal import Decimal
from tkinter import filedialog, messagebox as tk_messagebox, StringVar
import tkinter as tk
from tkinter import ttk
from PIL import Image
from ui.i18n.translator import Translator, get_current_language, set_current_language, translate_ui_text
from ui.theme.theme_manager import ThemeManager
from ui.responsive import fit_existing_dialog
from ui.components.modern_widgets import LoadingIndicator
from app.services.dashboard_service import DashboardService
from app.services.student.student_service import StudentService
from app.services.auth.authentication_service import AuthenticationService
from app.services.auth.face_recognition_service import FaceRecognitionService
from app.services.finance.finance_service import FinanceService
from app.services.finance.academic_year_service import AcademicYearService
from app.services.integration.notification_service import NotificationService
from app.services.integration.esp32_status_service import ESP32StatusService
from app.services.transfer.transfer_service import TransferService
from core.models.student import Student

logger = logging.getLogger(__name__)


class LocalizedMessageBoxProxy:
    """Proxy messagebox qui traduit automatiquement titres et messages.

    Garantit qu'aucune popup ne mélange FR/EN quand l'utilisateur change de langue.
    """

    @staticmethod
    def _translate(title, message):
        lang = get_current_language()
        return translate_ui_text(title, lang), translate_ui_text(message, lang)

    @staticmethod
    def showerror(title, message, **kwargs):
        t_title, t_message = LocalizedMessageBoxProxy._translate(title, message)
        return tk_messagebox.showerror(t_title, t_message, **kwargs)

    @staticmethod
    def showwarning(title, message, **kwargs):
        t_title, t_message = LocalizedMessageBoxProxy._translate(title, message)
        return tk_messagebox.showwarning(t_title, t_message, **kwargs)

    @staticmethod
    def showinfo(title, message, **kwargs):
        t_title, t_message = LocalizedMessageBoxProxy._translate(title, message)
        return tk_messagebox.showinfo(t_title, t_message, **kwargs)

    @staticmethod
    def askyesno(title, message, **kwargs):
        t_title, t_message = LocalizedMessageBoxProxy._translate(title, message)
        return tk_messagebox.askyesno(t_title, t_message, **kwargs)


# Toutes les utilisations locales de `messagebox` dans ce module passent par ce proxy.
messagebox = LocalizedMessageBoxProxy


class ErrorManager:
    """Gère les messages d'erreur avec niveaux utilisateur et développeur"""
    
    # Mapping des erreurs: (type_erreur) -> (message_utilisateur, msg_log_template)
    ERROR_MESSAGES = {
        "database_connection": (
            "Une erreur s'est produite lors de la connexion à la base de données.", "Database connection error: {details}"
        ), "database_query": (
            "Une erreur s'est produite lors de la lecture des données.", "Database query error: {details}"
        ), "payment_invalid_amount": (
            "Le montant saisi est invalide. Veuillez vérifier et réessayer.", "Invalid payment amount: {details}"
        ), "payment_exceeds_limit": (
            "Le montant saisi dépasse ce qui reste à payer pour cet étudiant.", "Payment exceeds limit: {details}"
        ), "payment_already_paid": (
            "Cet étudiant a déjà complété tous ses paiements.", "Payment attempt for fully paid student: {details}"
        ), "payment_no_active_fees": (
            "Votre paiement a échoué en raison :\n\nLes frais académiques pour cette promotion ne sont pas définis ou connus.", "Payment rejected: No active academic fees for student: {details}"
        ), "payment_processing": (
            "Une erreur s'est produite lors du traitement du paiement.", "Payment processing error: {details}"
        ), "validation_error": (
            "Les données fournies sont invalides.", "Validation error: {details}"
        ), "unknown_error": (
            "Une erreur inattendue s'est produite. Veuillez réessayer.", "Unexpected error: {details}"
        ), }
    
    @staticmethod
    def show_error(error_type: str, details: str = None, parent=None):
        """
        Affiche un message d'erreur à l'utilisateur et enregistre pour le développeur
        
        Args:
            error_type: Type d'erreur (clé du mapping)
            details: Détails techniques de l'erreur
            parent: Widget parent (optionnel)
        """
        user_msg, log_template = ErrorManager.ERROR_MESSAGES.get(
            error_type, ErrorManager.ERROR_MESSAGES["unknown_error"]
        )
        
        # Enregistrer le message complet pour le développeur
        log_msg = log_template.format(details=details or "No details provided")
        logger.error(log_msg)
        
        # Afficher un message utilisateur clair
        display_msg = user_msg
        detailed_types = {
            "validation_error",
            "payment_invalid_amount",
            "payment_exceeds_limit",
            "payment_no_active_fees",
            "payment_processing",
        }
        if error_type in detailed_types and details:
            display_msg = f"{user_msg}\n\nDétail: {details}"

        messagebox.showerror("Erreur", display_msg, parent=parent)
    
    @staticmethod
    def show_success(title: str, message: str, parent=None):
        """Affiche un message de succès à l'utilisateur"""
        messagebox.showinfo(title, message, parent=parent)
    
    @staticmethod
    def show_warning(title: str, message: str, parent=None):
        """Affiche un avertissement à l'utilisateur"""
        messagebox.showwarning(title, message, parent=parent)


class ModernDialog:
    """Classe pour créer des dialogues modernes avec style cohérent"""
    
    @staticmethod
    def create_centered_dialog(parent_dashboard, title: str, width: int = 520, height: int = 480):
        """Crée et centre un dialogue sur le dashboard"""
        dialog = ctk.CTkToplevel(parent_dashboard)
        dialog.title(title)
        
        # Centrer sur le dashboard
        dashboard_x = parent_dashboard.winfo_rootx()
        dashboard_y = parent_dashboard.winfo_rooty()
        dashboard_width = parent_dashboard.winfo_width()
        dashboard_height = parent_dashboard.winfo_height()
        
        center_x = dashboard_x + (dashboard_width - width) // 2
        center_y = dashboard_y + (dashboard_height - height) // 2
        
        dialog.geometry(f"{width}x{height}+{center_x}+{center_y}")
        dialog.grab_set()
        dialog.resizable(False, False)
        try:
            parent_dashboard._animate_window_open(dialog)
        except Exception:
            pass
        
        return dialog
    
    @staticmethod
    def create_header(parent, title: str, subtitle: str = "", bg_color: str = "#0a84ff"):
        """Crée un en-tête coloré centré"""
        header = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=0)
        header.pack(fill="x", side="top")
        
        title_label = ctk.CTkLabel(
            header, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff"
        )
        title_label.pack(pady=(15, 8 if subtitle else 15), padx=20)
        
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header, text=subtitle, font=ctk.CTkFont(size=12), text_color="#e8f4ff"
            )
            subtitle_label.pack(pady=(0, 15), padx=20)
        
        return header
    
    @staticmethod
    def create_content_frame(parent):
        """Crée un frame de contenu avec le bon style"""
        return ctk.CTkFrame(parent, fg_color="#f8f9fa")
    
    @staticmethod
    def create_button_frame(parent):
        """Crée un frame pour les boutons"""
        return ctk.CTkFrame(parent)


class Tooltip:
    """Simple tooltip that appears as a label next to the widget"""
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.tooltip_label = None
        
    def show_tooltip(self, event=None):
        """Show the tooltip"""
        if self.tooltip_window is not None:
            return
        
        # Create a small toplevel window for tooltip
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_attributes("-topmost", True)
        
        # Create label inside
        self.tooltip_label = tk.Label(
            self.tooltip_window, text=self.text, background="#1e293b", foreground="#f8fafc", padx=10, pady=6, font=("Arial", 10, "bold"), relief=tk.FLAT
        )
        self.tooltip_label.pack()
        
        # Position it next to the widget
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 10
        y = self.widget.winfo_rooty() + (self.widget.winfo_height() // 2) - 15
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Schedule removal
        self.tooltip_window.after(2000, self.hide_tooltip)
    
    def hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window is not None:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None
            self.tooltip_label = None


class AdminDashboard(ctk.CTkFrame):
    """Tableau de bord administrateur moderne avec design professionnel"""
    
    def __init__(self, parent, language: str = "FR", theme: ThemeManager = None, initial_view: str = "dashboard", current_user: dict = None):
        super().__init__(parent)
        
        self.parent_window = parent
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.ui_mode, self.ui_scale = self._get_screen_profile()
        try:
            ctk.set_widget_scaling(self.ui_scale)
        except Exception as exc:
            logger.debug(f"Widget scaling update skipped at init: {exc}")

        self.selected_language = language
        self.translator = Translator(language)
        set_current_language(language)
        self.theme = theme if theme else ThemeManager("light")
        self.current_user = current_user or {}
        self.current_user_role = str(self.current_user.get("role") or "user").strip().lower()
        self.current_user_email = str(self.current_user.get("email") or "").strip().lower()
        self.is_super_admin = self.current_user_role == "super_admin"
        self.is_limited_user = self.current_user_role == "user"
        self.current_view = initial_view if initial_view else "dashboard"
        self.dashboard_service = DashboardService()
        self.student_service = StudentService()
        self.auth_service = AuthenticationService()
        # Lazy init: face_recognition est coûteux et ne sert pas au chargement initial du dashboard
        self.face_service = None
        self.finance_service = FinanceService()
        self.academic_year_service = AcademicYearService()
        self.notification_service = NotificationService()
        self.esp32_service = ESP32StatusService()
        self.transfer_service = TransferService()
        self._photo_cache = {}
        self._esp32_status_label = None
        self._esp32_poll_job = None
        self._esp32_poll_active = False
        self._responsive_labels = []
        self.sidebar_mode = "compact"
        self._loading_overlay = None
        self._loading_indicator = None
        self._loading_visible = False
        self._loading_started_at = 0.0
        self._loading_hide_job = None
        self._loading_failsafe_job = None
        self._loading_min_visible_ms = 280
        self._section_loading_overlay = None
        self._section_loading_indicator = None
        self._section_loading_job = None
        self._section_loading_failsafe_job = None
        self._migration_dialog_opening = False
        self._view_switch_in_progress = False
        self._ui_rebuild_in_progress = False
        self.topbar = None
        self.footer = None
        self._theme_switch_in_progress = False
        self._last_resize_size = None
        self._initial_layout_stabilized = False
        self._translation_watchdog_job = None
        self._watchdog_lang = None
        self._idle_last_activity = time.monotonic()
        self._idle_check_job = None
        
        # Adaptive sidebar widths based on screen size
        if self.screen_width < 900:
            self.sidebar_width_full = 200  # Small screen: narrower sidebar
            self.sidebar_width_compact = 60
            self.sidebar_collapse_breakpoint = 1000
        elif self.screen_width < 1200:
            self.sidebar_width_full = 240
            self.sidebar_width_compact = 75
            self.sidebar_collapse_breakpoint = 1200
        elif self.screen_width < 1400:
            self.sidebar_width_full = 260
            self.sidebar_width_compact = 85
            self.sidebar_collapse_breakpoint = 1400
        else:
            self.sidebar_width_full = 280
            self.sidebar_width_compact = 90
            self.sidebar_collapse_breakpoint = 1100
        
        self.table_mode = "large"
        self.table_compact_breakpoint = 1200
        self.sidebar_hover_expanded = False
        self._sidebar_anim_job = None
        self._sidebar_animating = False
        self._sidebar_update_debounce_job = None
        self._resize_debounce_job = None
        self._table_mode_refresh_job = None
        self._view_data_cache = {}
        self._prefetch_inflight = set()
        self._prefetch_after_job = None
        self._scheduled_render_jobs = {}
        self._scrolling_active = False
        self.debug_students_table = False
        self.sidebar_mode_manual = None  # None=auto, "compact"=forcer compact, "full"=forcer complet
        
        self.colors = self._get_color_palette()
        ctk.set_appearance_mode("Dark" if self.theme.current_theme == "dark" else "Light")
        
        self.pack(fill="both", expand=True)
        self._create_ui()

    def _persist_ui_context(self, *, language=None, theme=None, view=None):
        """Demande au wrapper principal de mémoriser l'état UI courant."""
        try:
            if hasattr(self.parent_window, "update_ui_preferences"):
                self.parent_window.update_ui_preferences(language=language, theme=theme, last_view=view)
        except Exception:
            pass

    def _get_current_window_size(self):
        """Retourne la taille réelle de la fenêtre courante, avec fallback écran."""
        try:
            top = self.winfo_toplevel()
            width = top.winfo_width() or self.winfo_width() or self.screen_width
            height = top.winfo_height() or self.winfo_height() or self.screen_height
            return max(width, 1), max(height, 1)
        except Exception:
            return self.screen_width, self.screen_height

    def _refresh_responsive_metrics(self):
        """Met à jour les métriques responsives à partir de la taille réelle de la fenêtre."""
        width, height = self._get_current_window_size()
        self.screen_width = width
        self.screen_height = height

        previous_mode = getattr(self, "ui_mode", None)
        previous_scale = getattr(self, "ui_scale", None)
        self.ui_mode, self.ui_scale = self._get_screen_profile()

        if previous_mode != self.ui_mode or previous_scale != self.ui_scale:
            try:
                ctk.set_widget_scaling(self.ui_scale)
            except Exception:
                pass

        if self.screen_width < 900:
            self.sidebar_width_full = 200
            self.sidebar_width_compact = 60
            self.sidebar_collapse_breakpoint = 1000
        elif self.screen_width < 1200:
            self.sidebar_width_full = 240
            self.sidebar_width_compact = 75
            self.sidebar_collapse_breakpoint = 1200
        elif self.screen_width < 1400:
            self.sidebar_width_full = 260
            self.sidebar_width_compact = 85
            self.sidebar_collapse_breakpoint = 1400
        else:
            self.sidebar_width_full = 280
            self.sidebar_width_compact = 90
            self.sidebar_collapse_breakpoint = 1100

        self.table_compact_breakpoint = 1200 if self.screen_width >= 1000 else 1000

    def _get_face_service(self) -> FaceRecognitionService:
        """Initialise la reconnaissance faciale à la demande."""
        if self.face_service is None:
            self.face_service = FaceRecognitionService()
            logger.info("FaceRecognitionService initialized on-demand")
        return self.face_service

    def _get_cached_data(self, cache_key: str, loader, ttl_seconds: float = 30.0):
        """Retourne des données en cache (stratégie stale-while-revalidate).

        - Si les données existent en cache (même périmées) : retour immédiat + rafraîchissement
          silencieux en arrière-plan si le TTL est dépassé.
        - Si le cache est vide (premier accès) : chargement synchrone bloquant.
        Cela rend toutes les navigations après la première quasi-instantanées.
        """
        try:
            now = time.monotonic()
            cached = self._view_data_cache.get(cache_key)
            if cached:
                # Données présentes : retour immédiat
                if (now - cached["timestamp"]) >= ttl_seconds:
                    # Périmées : lancer un rafraîchissement silencieux en arrière-plan
                    self._queue_prefetch(cache_key, loader)
                return cached["value"]

            # Cache vide (tout premier accès) : chargement synchrone
            value = loader()
            self._view_data_cache[cache_key] = {"timestamp": now, "value": value}
            return value
        except Exception:
            try:
                return loader()
            except Exception:
                return []

    def _invalidate_view_cache(self, *cache_keys):
        """Invalide tout ou partie du cache UI après une mutation de données."""
        if not cache_keys:
            self._view_data_cache.clear()
            return

        for cache_key in cache_keys:
            self._view_data_cache.pop(cache_key, None)

    def _store_prefetched_data(self, cache_key: str, value):
        """Stocke en cache le résultat d'un préchargement background sur le thread UI."""
        self._view_data_cache[cache_key] = {
            "timestamp": time.monotonic(),
            "value": value,
        }

    def _queue_prefetch(self, cache_key: str, loader):
        """Précharge une source de données lourde en arrière-plan sans bloquer l'interface."""
        if cache_key in self._prefetch_inflight:
            return

        cached = self._view_data_cache.get(cache_key)
        if cached and (time.monotonic() - cached["timestamp"]) < 10.0:
            return

        self._prefetch_inflight.add(cache_key)

        def worker():
            try:
                value = loader()
                self.after(0, lambda: self._store_prefetched_data(cache_key, value))
            except Exception as exc:
                logger.debug(f"Prefetch failed for {cache_key}: {exc}")
            finally:
                self.after(0, lambda: self._prefetch_inflight.discard(cache_key))

        threading.Thread(target=worker, daemon=True).start()

    def _schedule_heavy_views_prefetch(self, delay_ms: int = 500):
        """Planifie le préchargement des vues lourdes après stabilisation de l'UI."""
        try:
            if self._prefetch_after_job:
                self.after_cancel(self._prefetch_after_job)
        except Exception:
            pass

        self._prefetch_after_job = self.after(delay_ms, self._prefetch_heavy_views)

    def _prefetch_heavy_views(self):
        """Précharge les données des écrans les plus lourds pour accélérer la première ouverture."""
        self._prefetch_after_job = None
        prefetch_map = {
            "students_all_with_finance": self.student_service.get_all_students_with_finance,
            "academic_years": self.academic_year_service.get_years,
            "promotions_with_fees": self.student_service.get_promotions_with_fees,
            "active_academic_year": self.academic_year_service.get_active_year,
            "transfer_faculties": self.student_service.get_faculties,
            "faculty_stats_with_photos": self.dashboard_service.get_faculty_stats_with_photos,
            "access_stats": lambda: {
                "granted": self.dashboard_service.get_access_granted(),
                "denied": self.dashboard_service.get_access_denied(),
            },
            "finance_snapshot": lambda: {
                "revenue": self.dashboard_service.get_revenue_collected(),
                "payment_status": self.dashboard_service.get_students_by_payment_status(),
                "payments": self.dashboard_service.get_students_finance_overview(),
            },
            "dashboard_snapshot": lambda: {
                "total_students": self.dashboard_service.get_total_students(),
                "eligible_students": self.dashboard_service.get_eligible_students(),
                "non_eligible_students": self.dashboard_service.get_non_eligible_students(),
                "access_granted": self.dashboard_service.get_access_granted(),
                "access_denied": self.dashboard_service.get_access_denied(),
                "revenue": self.dashboard_service.get_revenue_collected(),
                "completion": self.dashboard_service.get_degree_of_completion(),
                "activities": self.dashboard_service.get_recent_activities(8),
            },
        }

        for cache_key, loader in prefetch_map.items():
            self._queue_prefetch(cache_key, loader)

    def _cancel_scheduled_render(self, render_key: str):
        """Annule un rendu progressif programmé."""
        render_state = self._scheduled_render_jobs.pop(render_key, None)
        if not render_state:
            return
        job_id = render_state.get("job")
        if job_id:
            try:
                self.after_cancel(job_id)
            except Exception:
                pass

    def _cancel_scheduled_renders(self, prefix: str = None):
        """Annule un ensemble de rendus programmés, utile avant une reconstruction UI."""
        render_keys = list(self._scheduled_render_jobs.keys())
        for render_key in render_keys:
            if prefix is None or render_key.startswith(prefix):
                self._cancel_scheduled_render(render_key)

    def _stop_translation_watchdog(self):
        """Annule le job périodique de traduction."""
        try:
            if self._translation_watchdog_job:
                self.after_cancel(self._translation_watchdog_job)
        except Exception:
            pass
        self._translation_watchdog_job = None

    def _start_idle_watcher(self):
        """Démarre la surveillance d'inactivité (déconnexion auto après 30 min)."""
        self._idle_last_activity = time.monotonic()
        try:
            top = self.winfo_toplevel()
            top.bind_all("<Motion>", self._reset_idle_timer, add="+")
            top.bind_all("<ButtonPress>", self._reset_idle_timer, add="+")
            top.bind_all("<KeyPress>", self._reset_idle_timer, add="+")
        except Exception:
            pass
        self._idle_check_job = self.after(60_000, self._idle_check_tick)

    def _reset_idle_timer(self, _event=None):
        """Réinitialise le compteur d'inactivité dès qu'une action est détectée."""
        self._idle_last_activity = time.monotonic()

    def _idle_check_tick(self):
        """Vérifie toutes les minutes si l'inactivité dépasse 30 minutes."""
        if not self.winfo_exists():
            return
        elapsed = time.monotonic() - self._idle_last_activity
        if elapsed >= 1800:  # 30 minutes
            logger.info("Déconnexion automatique après 30 minutes d'inactivité.")
            try:
                self._on_logout()
            except Exception:
                pass
        else:
            self._idle_check_job = self.after(60_000, self._idle_check_tick)

    def _stop_idle_watcher(self):
        """Annule la surveillance d'inactivité et détache les bindings."""
        try:
            if self._idle_check_job:
                self.after_cancel(self._idle_check_job)
        except Exception:
            pass
        self._idle_check_job = None
        try:
            top = self.winfo_toplevel()
            top.unbind_all("<Motion>")
            top.unbind_all("<ButtonPress>")
            top.unbind_all("<KeyPress>")
        except Exception:
            pass

    def _render_in_batches(self, render_key: str, items, render_item, batch_size: int = 18, delay_ms: int = 1, on_complete=None):
        """Construit une liste d'éléments UI par lots pour éviter de figer l'interface."""
        self._cancel_scheduled_render(render_key)

        items = list(items or [])
        if not items:
            if on_complete:
                on_complete()
            return

        token = object()
        self._scheduled_render_jobs[render_key] = {"token": token, "job": None}
        total_items = len(items)
        current_index = 0

        def step():
            nonlocal current_index
            render_state = self._scheduled_render_jobs.get(render_key)
            if not render_state or render_state.get("token") is not token:
                return

            end_index = min(current_index + batch_size, total_items)
            for item_index in range(current_index, end_index):
                render_item(items[item_index], item_index)
            current_index = end_index

            if current_index < total_items:
                render_state["job"] = self.after(delay_ms, step)
            else:
                self._scheduled_render_jobs.pop(render_key, None)
                if on_complete:
                    on_complete()

        step()


    def _register_wrap(self, label, ratio: float = 0.35, min_width: int = 280, max_width: int = 600):
        """Enregistre un label pour ajuster automatiquement son wraplength"""
        self._responsive_labels.append((label, ratio, min_width, max_width))

    def _on_resize(self, _event=None):
        """Gère le redimensionnement avec responsive design complet"""
        try:
            width, height = self._get_current_window_size()
            if self._last_resize_size == (width, height):
                return
            self._last_resize_size = (width, height)

            if self._resize_debounce_job:
                self.after_cancel(self._resize_debounce_job)
            self._resize_debounce_job = self.after(120, self._apply_responsive_resize)
        except Exception as e:
            logger.debug(f"Resize event error: {e}")

    def _apply_responsive_resize(self):
        """Applique les recalculs responsive après debounce pour éviter les rerenders coûteux."""
        self._resize_debounce_job = None
        try:
            self._refresh_responsive_metrics()
            if not self._responsive_labels:
                self._update_sidebar_layout()
                self._update_table_mode()
                self._update_responsive_padding()
                return

            width = self.winfo_width() or self.screen_width

            for label, ratio, min_w, max_w in self._responsive_labels:
                try:
                    wrap = int(max(min_w, min(max_w, width * ratio)))
                    label.configure(wraplength=wrap)
                except Exception:
                    continue

            self._update_sidebar_layout()
            self._update_table_mode()
            self._update_responsive_padding()

            if self.current_view == "students":
                try:
                    content_width = self.content_frame.winfo_width() if hasattr(self, "content_frame") else 0
                    if content_width <= 1:
                        content_width = self.winfo_toplevel().winfo_width()
                    compact_now = content_width < 1250
                    compact_before = getattr(self, "_students_compact_layout", None)

                    if (
                        compact_before is not None
                        and compact_now != compact_before
                        and not getattr(self, "_students_layout_refreshing", False)
                    ):
                        self._students_layout_refreshing = True
                        self.after(20, self._refresh_students_layout_for_resize)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Responsive resize apply error: {e}")

    def _refresh_students_layout_for_resize(self):
        """Reconstruit la vue Étudiants après changement de breakpoint responsive"""
        try:
            if self.current_view == "students" and not self._view_switch_in_progress and not self._loading_visible:
                self._show_students()
        finally:
            self._students_layout_refreshing = False
    
    def _update_responsive_padding(self):
        """Ajuste les paddings et espacements selon la taille d'écran"""
        try:
            if self.screen_width < 768:
                main_pad = 12
                bottom_pad = 10
                topbar_height = 112
                font_size_title = 18
                font_size_subtitle = 10
            elif self.screen_width < 1024:
                main_pad = 18
                bottom_pad = 12
                topbar_height = 82
                font_size_title = 24
                font_size_subtitle = 11
            else:
                main_pad = 25
                bottom_pad = 15
                topbar_height = 90
                font_size_title = 28
                font_size_subtitle = 13
            
            if hasattr(self, 'topbar') and self.topbar:
                self.topbar.configure(height=topbar_height)
                self.topbar.pack_configure(padx=main_pad, pady=(6, 0))

            if hasattr(self, 'content_container') and self.content_container:
                self.content_container.pack_configure(padx=main_pad, pady=6)

            if hasattr(self, 'footer') and self.footer:
                self.footer.pack_configure(padx=main_pad, pady=(0, bottom_pad))
            
            # Ajuster les tailles de police dynamiquement
            if hasattr(self, 'title_label'):
                self.title_label.configure(
                    font=ctk.CTkFont(size=font_size_title, weight="bold")
                )
            
            if hasattr(self, 'subtitle_label'):
                self.subtitle_label.configure(
                    font=ctk.CTkFont(size=font_size_subtitle)
                )

            if hasattr(self, 'lang_switch') and self.lang_switch:
                self.lang_switch.configure(
                    font=ctk.CTkFont(size=11 if self.screen_width < 900 else 12, weight="bold")
                )

            if hasattr(self, 'theme_btn') and self.theme_btn:
                theme_size = 30 if self.screen_width < 900 else 32
                self.theme_btn.configure(width=38 if self.screen_width < 900 else 40, height=theme_size)

            if hasattr(self, 'lang_frame') and self.lang_frame:
                self.lang_frame.configure(corner_radius=10 if self.screen_width < 900 else 8)

            if hasattr(self, 'logo_frame') and self.logo_frame:
                self.logo_frame.configure(height=64 if self.screen_width < 900 else 80)

            if hasattr(self, 'logo_title_label') and self.logo_title_label:
                self.logo_title_label.configure(font=ctk.CTkFont(size=22 if self.screen_width < 900 else 32, weight="bold"))

            if hasattr(self, 'logo_subtitle_label') and self.logo_subtitle_label and self.sidebar_mode != "compact":
                self.logo_subtitle_label.configure(font=ctk.CTkFont(size=9 if self.screen_width < 900 else 11))

            if hasattr(self, 'sidebar_expand_btn') and self.sidebar_expand_btn:
                self.sidebar_expand_btn.configure(height=42 if self.screen_width < 900 else 50)

            if hasattr(self, 'sidebar_mode_label') and self.sidebar_mode_label:
                if self.screen_width < 900 and self.sidebar_mode == "compact":
                    self.sidebar_mode_label.pack_forget()
                elif not self.sidebar_mode_label.winfo_ismapped():
                    self.sidebar_mode_label.pack(pady=(6, 0))

            if hasattr(self, 'nav_buttons') and self.nav_buttons:
                for item in self.nav_buttons:
                    btn = item.get("button")
                    if not btn:
                        continue
                    if self.sidebar_mode == "compact":
                        btn.configure(
                            height=36 if self.screen_width < 900 else 45,
                            corner_radius=10 if self.screen_width < 900 else 8,
                            font=ctk.CTkFont(size=16 if self.screen_width < 900 else 18, weight="bold")
                        )
                        try:
                            btn.pack_configure(padx=10 if self.screen_width < 900 else 15, pady=4 if self.screen_width < 900 else 3)
                        except Exception:
                            pass
                    else:
                        btn.configure(
                            height=40 if self.screen_width < 900 else 45,
                            corner_radius=10 if self.screen_width < 900 else 8,
                            font=ctk.CTkFont(size=11 if self.screen_width < 900 else 13, weight="bold")
                        )
                        try:
                            btn.pack_configure(padx=12 if self.screen_width < 900 else 15, pady=4 if self.screen_width < 900 else 3)
                        except Exception:
                            pass

            self._update_topbar_layout()
            self._update_footer_layout()

            if hasattr(self, 'logout_btn') and self.logout_btn:
                logout_height = 46 if self.screen_width < 900 else (50 if self.screen_width < 1400 else 60)
                logout_font_size = 12 if self.screen_width < 900 else (13 if self.screen_width < 1400 else 14)
                self.logout_btn.configure(
                    height=logout_height,
                    font=ctk.CTkFont(size=logout_font_size, weight="bold")
                )
        except Exception as e:
            logger.debug(f"Responsive padding update error: {e}")

    def _update_topbar_layout(self):
        """Adapte la topbar selon la largeur disponible pour éviter les chevauchements."""
        if not hasattr(self, "topbar") or not self.topbar:
            return
        if not hasattr(self, "title_frame") or not hasattr(self, "lang_frame"):
            return

        is_small = self.screen_width < 1024
        is_tiny = self.screen_width < 900

        try:
            self.title_frame.place_forget()
        except Exception:
            pass
        try:
            self.title_frame.pack_forget()
        except Exception:
            pass
        try:
            self.lang_frame.pack_forget()
        except Exception:
            pass

        if is_tiny:
            self.title_frame.pack(side="top", anchor="w", padx=12, pady=(8, 4), fill="x")
            self.lang_frame.pack(side="top", anchor="e", padx=8, pady=(0, 8))
            self.title_label.configure(anchor="w", justify="left")
            self.subtitle_label.configure(anchor="w", justify="left")
        elif is_small:
            self.title_frame.place(relx=0.42, rely=0.5, anchor="center")
            self.lang_frame.pack(side="right", padx=10, pady=10)
            self.title_label.configure(anchor="center", justify="center")
            self.subtitle_label.configure(anchor="center", justify="center")
        else:
            self.title_frame.place(relx=0.5, rely=0.5, anchor="center")
            self.lang_frame.pack(side="right", padx=10, pady=10)
            self.title_label.configure(anchor="center", justify="center")
            self.subtitle_label.configure(anchor="center", justify="center")

    def _update_footer_layout(self):
        """Réorganise le footer pour qu'il reste lisible en petite largeur."""
        if not hasattr(self, "footer_left_frame") or not hasattr(self, "footer_right_frame"):
            return

        try:
            self.footer_left_frame.pack_forget()
            self.footer_right_frame.pack_forget()
        except Exception:
            pass

        if self.screen_width < 900:
            self.footer_left_frame.pack(fill="x", anchor="w")
            self.footer_right_frame.pack(fill="x", anchor="w", pady=(6, 0))
        else:
            self.footer_left_frame.pack(side="left", fill="x", expand=True)
            self.footer_right_frame.pack(side="right")

    def _get_screen_profile(self):
        """Détermine le mode d'affichage et le scaling selon la taille d'écran (RESPONSIVE)"""
        if self.screen_width < 900:
            # Très petit écran: Mobile-like
            return "tiny", 0.75  # Smaller UI scale
        if self.screen_width < 1200:
            # Petit/Medium: Compact
            return "small", 0.85
        if self.screen_width < 1400:
            # Medium: Tablet
            return "tablet", 0.95
        # Grand écran: Desktop
        return "desktop", 1.0

    def _scaled(self, value: int) -> int:
        return max(10, int(value * self.ui_scale))

    def _font(self, size: int, weight: str = "normal"):
        return ctk.CTkFont(size=self._scaled(size), weight=weight)

    def _t(self, key: str, default: str = "") -> str:
        """Raccourci traduction avec fallback"""
        text = self.translator.get(key, default)
        return self.translator.translate_literal(text)

    def _can_access_view(self, view_key: str) -> bool:
        """Détermine si l'utilisateur courant peut accéder à une vue."""
        if view_key == "access_requests":
            return self.is_super_admin
        if self.is_limited_user and view_key in {"academic_data", "academic_years", "transfers"}:
            return False
        return True

    def _handle_forbidden_view(self, view_key: str):
        """Affiche un message de refus et revient sur le dashboard."""
        messagebox.showwarning(
            self._t("access_denied", "Accès refusé"),
            self._t(
                "access_denied_message",
                "Vous n'avez pas l'autorisation d'accéder à cette page."
            ),
        )
        self.current_view = "dashboard"
        self._persist_ui_context(view=self.current_view)
        self._show_dashboard()

    def _translate_widget_tree(self, root_widget=None):
        """Traduit récursivement les textes visibles des widgets CustomTkinter.

        Objectif: éviter les mélanges FR/EN même quand certains textes ont
        été écrits en dur dans l'UI.
        """
        root = root_widget or self

        def walk(widget):
            # Traduire le titre des fenêtres secondaires
            try:
                if isinstance(widget, tk.Toplevel):
                    title = widget.title()
                    if isinstance(title, str) and title.strip():
                        translated_title = self.translator.translate_literal(title)
                        if translated_title != title:
                            widget.title(translated_title)
            except Exception:
                pass

            # Traduire texte principal
            try:
                txt = widget.cget("text")
                if isinstance(txt, str) and txt.strip():
                    translated = self.translator.translate_literal(txt)
                    if translated != txt:
                        widget.configure(text=translated)
            except Exception:
                pass

            # Traduire des listes de valeurs (Combo/Option/Segmented)
            try:
                values = widget.cget("values")
                if isinstance(values, (list, tuple)) and values:
                    new_values = []
                    changed = False
                    for v in values:
                        tv = self.translator.translate_literal(v) if isinstance(v, str) else v
                        new_values.append(tv)
                        changed = changed or (tv != v)
                    if changed:
                        widget.configure(values=new_values)
            except Exception:
                pass

            # Traduire le texte dessiné dans les Canvas (donut/charts)
            try:
                if isinstance(widget, tk.Canvas):
                    for item in widget.find_all():
                        try:
                            if widget.type(item) == "text":
                                raw = widget.itemcget(item, "text")
                                if isinstance(raw, str) and raw.strip():
                                    tr = self.translator.translate_literal(raw)
                                    if tr != raw:
                                        widget.itemconfigure(item, text=tr)
                        except Exception:
                            continue
            except Exception:
                pass

            # Traduire placeholder des champs si disponible
            try:
                ph = widget.cget("placeholder_text")
                if isinstance(ph, str) and ph.strip():
                    translated_ph = self.translator.translate_literal(ph)
                    if translated_ph != ph:
                        widget.configure(placeholder_text=translated_ph)
            except Exception:
                pass

            # Descendre récursivement
            try:
                children = widget.winfo_children()
            except Exception:
                children = []

            for child in children:
                walk(child)

        walk(root)

    def _translate_all_windows(self):
        """Traduit le contenu de la fenêtre principale et des dialogues ouverts."""
        try:
            self._translate_widget_tree(self)
        except Exception:
            pass

        try:
            root = self.winfo_toplevel()
            for child in root.winfo_children():
                try:
                    if isinstance(child, tk.Toplevel):
                        self._translate_widget_tree(child)
                except Exception:
                    continue
        except Exception:
            pass

    def _start_translation_watchdog(self):
        """Maintient la traduction appliquée même sur les widgets/dialogues créés tardivement."""
        try:
            if self._translation_watchdog_job:
                self.after_cancel(self._translation_watchdog_job)
        except Exception:
            pass

        def _tick():
            if not self.winfo_exists():
                return
            # Only do full tree walk if language recently changed or on a slower tick
            current_lang = getattr(self, "selected_language", None)
            if current_lang != getattr(self, "_watchdog_lang", None):
                self._watchdog_lang = current_lang
                self._translate_all_windows()
            else:
                # Periodic light pass (less frequent)
                self._translate_all_windows()
            self._translation_watchdog_job = self.after(2500, _tick)

        self._translation_watchdog_job = self.after(250, _tick)
        self._watchdog_lang = getattr(self, "selected_language", None)

    def _get_color_palette(self):
        """Retourne la palette selon le thème"""
        if self.theme.current_theme == "dark":
            return {
                "sidebar_bg": "#0f172a", "main_bg": "#0b1220", "card_bg": "#111827", "primary": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444", "info": "#06b6d4", "text_dark": "#e5e7eb", "text_light": "#9ca3af", "text_white": "#ffffff", "border": "#1f2937", "hover": "#111827"
            }
        return {
            "sidebar_bg": "#1e293b", "main_bg": "#f8fafc", "card_bg": "#ffffff", "primary": "#3b82f6", "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444", "info": "#06b6d4", "text_dark": "#1e293b", "text_light": "#64748b", "text_white": "#ffffff", "border": "#e2e8f0", "hover": "#f1f5f9"
        }

    def _toggle_theme(self):
        """Bascule le thème et reconstruit l'UI de manière stable (anti-flicker)."""
        if self._theme_switch_in_progress or self._ui_rebuild_in_progress:
            return

        self._theme_switch_in_progress = True
        self._ui_rebuild_in_progress = True
        self._view_switch_in_progress = True
        if hasattr(self, "theme_btn") and self.theme_btn:
            try:
                self.theme_btn.configure(state="disabled")
            except Exception:
                pass

        new_theme = "dark" if self.theme.current_theme == "light" else "light"
        self.theme.set_theme(new_theme)
        self._persist_ui_context(theme=new_theme, view=self.current_view)
        self.colors = self._get_color_palette()
        ctk.set_appearance_mode("Dark" if new_theme == "dark" else "Light")
        self._show_loading_overlay("Application du thème...")
        self.after_idle(self._recreate_ui)

    def _recreate_ui(self):
        """Recrée l'interface en conservant la vue active"""
        try:
            self._stop_translation_watchdog()
            try:
                self._cancel_scheduled_renders()
            except Exception:
                pass

            for widget in self.winfo_children():
                widget.destroy()
            self._create_ui()
        finally:
            self._theme_switch_in_progress = False
            self._ui_rebuild_in_progress = False
            self._view_switch_in_progress = False

    def _render_current_view(self):
        """Réaffiche la vue en cours"""
        self._set_main_scrollbar_visible(True)
        view_map = {
            "dashboard": self._show_dashboard,
            "students": self._show_students,
            "finance": self._show_finance,
            "access_logs": self._show_access_logs,
            "reports": self._show_reports,
            "academic_years": self._show_academic_years,
            "exam_periods": self._show_exam_periods,
            "academic_data": self._show_student_academic_data,
            "transfers": self._show_transfers,
            "access_requests": self._show_access_requests,
        }
        if not self._can_access_view(self.current_view):
            self.current_view = "dashboard"
        view_map.get(self.current_view, self._show_dashboard)()
        self._translate_all_windows()

    def _refresh_after_payment_success(self):
        """Rafraîchit la vue de façon ciblée après un paiement (moins de reconstruction visible)."""
        self._invalidate_view_cache(
            "dashboard_snapshot",
            "students_all_with_finance",
            "finance_snapshot",
        )
        self._schedule_heavy_views_prefetch(delay_ms=500)

        # Rafraîchissement léger de la vue active quand c'est possible.
        if self.current_view == "students" and hasattr(self, "students_main_card"):
            try:
                self.students_full_data_all = self._get_cached_data(
                    "students_all_with_finance",
                    self.student_service.get_all_students_with_finance,
                    ttl_seconds=45.0,
                )
                self._refresh_students_navigation_with_loading("Actualisation après paiement...")
                return
            except Exception as exc:
                logger.debug(f"Light students refresh failed after payment: {exc}")

        if self.current_view == "finance":
            self._run_with_loading(
                lambda: self._show_finance(getattr(self, "_finance_filter", "all")),
                "Actualisation des finances...",
            )
            return

        # Fallback sûr pour les autres vues.
        self._run_with_loading(self._render_current_view, "Actualisation de la page...")

    def _ensure_loading_overlay(self):
        """Prépare un overlay de chargement pour masquer les rechargements visibles."""
        if self._loading_overlay or not hasattr(self, "main_content"):
            return

        overlay = ctk.CTkFrame(self.main_content, fg_color=self.colors["main_bg"])
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        card = ctk.CTkFrame(overlay, fg_color=self.colors["card_bg"], corner_radius=12)
        card.place(relx=0.5, rely=0.4, anchor="center")

        indicator = LoadingIndicator(card, text="Chargement...", color=self.colors.get("primary", "#3b82f6"))
        indicator.pack(padx=24, pady=24)
        indicator.start()

        self._loading_overlay = overlay
        self._loading_indicator = indicator
        overlay.place_forget()

    def _show_loading_overlay(self, text: str = "Chargement..."):
        if self._loading_visible:
            try:
                if self._loading_indicator:
                    self._loading_indicator.set_status(self.translator.translate_literal(text))
            except Exception:
                pass
            return
        self._ensure_loading_overlay()
        if not self._loading_overlay:
            return
        self._loading_visible = True
        self._loading_started_at = time.monotonic()

        # Sécurité anti-écran gris bloqué
        try:
            if self._loading_failsafe_job:
                self.after_cancel(self._loading_failsafe_job)
        except Exception:
            pass
        self._loading_failsafe_job = self.after(6000, self._force_reset_loading_state)

        display_text = self.translator.translate_literal(text)
        try:
            if self._loading_indicator:
                self._loading_indicator.start(display_text)
        except Exception:
            pass
        try:
            self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._loading_overlay.lift()
        except Exception:
            pass

    def _hide_loading_overlay(self):
        if not self._loading_overlay:
            return

        # Evite les flashs visuels: le loader reste visible un minimum
        elapsed_ms = int((time.monotonic() - (self._loading_started_at or 0.0)) * 1000)
        remaining_ms = self._loading_min_visible_ms - elapsed_ms
        if remaining_ms > 0:
            try:
                if self._loading_hide_job:
                    self.after_cancel(self._loading_hide_job)
            except Exception:
                pass
            self._loading_hide_job = self.after(remaining_ms, self._hide_loading_overlay)
            return

        self._loading_hide_job = None
        self._loading_visible = False
        try:
            if self._loading_failsafe_job:
                self.after_cancel(self._loading_failsafe_job)
        except Exception:
            pass
        self._loading_failsafe_job = None
        try:
            if self._loading_indicator:
                self._loading_indicator.stop()
        except Exception:
            pass
        try:
            self._loading_overlay.place_forget()
        except Exception:
            pass

    def _force_reset_loading_state(self):
        """Débloque l'interface si un chargement reste bloqué trop longtemps."""
        self._loading_failsafe_job = None
        self._loading_visible = False
        self._view_switch_in_progress = False
        self._loading_hide_job = None
        try:
            if self._loading_indicator:
                self._loading_indicator.stop()
        except Exception:
            pass
        try:
            if self._loading_overlay:
                self._loading_overlay.place_forget()
        except Exception:
            pass

    def _run_with_loading(self, action, text: str = "Chargement..."):
        """Navigation fluide : affiche l'overlay, laisse Tkinter le peindre, puis exécute l'action.

        En différant l'exécution via after(), l'overlay est visible AVANT que le
        fil principal ne soit occupé à construire les widgets → feedback immédiat.
        """
        if self._view_switch_in_progress:
            return

        self._view_switch_in_progress = True
        self._show_loading_overlay(text)

        def _execute_and_hide():
            try:
                action()
            except Exception as exc:
                logger.error(f"View transition error: {exc}")
            finally:
                self._hide_loading_overlay()
                self._view_switch_in_progress = False

        # 24 ms: 1 frame confortable pour peindre l'overlay avant le rendu
        self.after(24, _execute_and_hide)

    def _show_section_loading(self, target_widget, text: str = "Chargement..."):
        """Affiche un spinner local sur une section (carte/table) sans bloquer toute la page."""
        try:
            self._hide_section_loading()
            if not target_widget or not target_widget.winfo_exists():
                return

            overlay = ctk.CTkFrame(target_widget, fg_color=self.colors["main_bg"])
            overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
            overlay.lift()

            card = ctk.CTkFrame(overlay, fg_color=self.colors["card_bg"], corner_radius=12)
            card.place(relx=0.5, rely=0.5, anchor="center")

            indicator = LoadingIndicator(
                card,
                text=self.translator.translate_literal(text),
                color=self.colors.get("primary", "#3b82f6"),
            )
            indicator.pack(padx=18, pady=16)
            indicator.start()

            self._section_loading_overlay = overlay
            self._section_loading_indicator = indicator

            # failsafe local anti-blocage
            self._section_loading_failsafe_job = self.after(5000, self._hide_section_loading)
        except Exception:
            self._hide_section_loading()

    def _hide_section_loading(self):
        """Cache le spinner local de section."""
        try:
            if self._section_loading_failsafe_job:
                self.after_cancel(self._section_loading_failsafe_job)
        except Exception:
            pass
        self._section_loading_failsafe_job = None

        try:
            if self._section_loading_job:
                self.after_cancel(self._section_loading_job)
        except Exception:
            pass
        self._section_loading_job = None

        try:
            if self._section_loading_indicator:
                self._section_loading_indicator.stop()
        except Exception:
            pass
        self._section_loading_indicator = None

        try:
            if self._section_loading_overlay:
                self._section_loading_overlay.place_forget()
                self._section_loading_overlay.destroy()
        except Exception:
            pass
        self._section_loading_overlay = None

    def _run_with_section_loading(self, target_widget, action, text: str = "Chargement..."):
        """Exécute une action avec spinner local si possible, sinon fallback global."""
        try:
            if target_widget and target_widget.winfo_exists():
                self._show_section_loading(target_widget, text)

                def _run_local():
                    try:
                        action()
                    finally:
                        self._hide_section_loading()

                self._section_loading_job = self.after(20, _run_local)
                return
        except Exception:
            pass

        # Fallback sûr
        self._run_with_loading(action, text)

    def _refresh_students_navigation_with_loading(self, text: str = "Actualisation des étudiants..."):
        """Rafraîchit la navigation Étudiants avec un feedback spinner cohérent."""

        def _action():
            self._update_students_stats()
            self._render_students_navigation()

        target = getattr(self, "students_main_card", None)
        self._run_with_section_loading(target, _action, text)
    
    def _create_ui(self):
        """Crée l'interface moderne du dashboard"""
        self.configure(fg_color=self.colors["main_bg"])
        
        # Container principal
        container = ctk.CTkFrame(self, fg_color=self.colors["main_bg"])
        container.pack(fill="both", expand=True)
        
        # === SIDEBAR MODERNE ===
        sidebar = ctk.CTkFrame(container, fg_color=self.colors["sidebar_bg"], width=self.sidebar_width_full, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.sidebar = sidebar
        
        # Logo et titre (zone fixe en haut)
        logo_frame = ctk.CTkFrame(sidebar, height=80, fg_color=self.colors["sidebar_bg"])
        logo_frame.pack(fill="x", pady=(20, 10))
        logo_frame.pack_propagate(False)
        self.logo_frame = logo_frame
        
        self.logo_title_label = ctk.CTkLabel(
            logo_frame, text="U.O.R", font=ctk.CTkFont(size=32, weight="bold"), text_color=self.colors["text_dark"]
        )
        self.logo_title_label.pack()
        
        self.logo_subtitle_label = ctk.CTkLabel(
            logo_frame, text=self._t("admin_dashboard_subtitle", "TABLEAU DE BORD ADMIN"), font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]
        )
        self.logo_subtitle_label.pack()
        
        # === BARRES HORIZONTALES POUR REDIMENSIONNER ===
        bars_frame = ctk.CTkFrame(sidebar, fg_color=self.colors["sidebar_bg"])
        bars_frame.pack(fill="x", padx=15, pady=12)
        bars_frame.pack_propagate(True)
        
        # Bouton stylisé avec barres - utiliser un Frame cliquable
        self.sidebar_expand_btn = ctk.CTkFrame(
            bars_frame,
            fg_color="#1e293b",
            border_width=1,
            border_color="#334155",
            corner_radius=8,
            height=50
        )
        self.sidebar_expand_btn.pack(fill="x", pady=0)
        self.sidebar_expand_btn.pack_propagate(False)
        
        # Rendre le frame cliquable avec hover effect
        def on_expand_enter(e):
            self.sidebar_expand_btn.configure(fg_color="#334155")
            self.sidebar_expand_btn.configure(border_color="#475569")
        
        def on_expand_leave(e):
            self.sidebar_expand_btn.configure(fg_color="#1e293b")
            self.sidebar_expand_btn.configure(border_color="#334155")
        
        self.sidebar_expand_btn.bind("<Button-1>", lambda e: self._toggle_sidebar_expand())
        self.sidebar_expand_btn.bind("<Enter>", on_expand_enter)
        self.sidebar_expand_btn.bind("<Leave>", on_expand_leave)
        
        # Créer 4 barres horizontales stylisées dans le frame
        bars_inner = ctk.CTkFrame(self.sidebar_expand_btn, fg_color="transparent")
        bars_inner.pack(expand=True)
        
        for i in range(4):
            bar = ctk.CTkFrame(
                bars_inner, 
                height=2.5, 
                width=30,
                fg_color="#94a3b8",
                corner_radius=1
            )
            bar.pack(fill="x", pady=2)
        
        # Rendre aussi les barres cliquables et hover-actives
        bars_inner.bind("<Button-1>", lambda e: self._toggle_sidebar_expand())
        bars_inner.bind("<Enter>", on_expand_enter)
        bars_inner.bind("<Leave>", on_expand_leave)
        
        for child in bars_inner.winfo_children():
            child.bind("<Button-1>", lambda e: self._toggle_sidebar_expand())
            child.bind("<Enter>", on_expand_enter)
            child.bind("<Leave>", on_expand_leave)
        
        # Label du mode
        self.sidebar_mode_label = ctk.CTkLabel(
            bars_frame,
            text=self._t("sidebar_mode_compact", "Mode: Compact") if self.sidebar_mode == "compact" else self._t("sidebar_mode_full", "Mode: Complet"),
            text_color="#64748b",
            font=ctk.CTkFont(size=8)
        )
        self.sidebar_mode_label.pack(pady=(6, 0))
        
        # Séparateur
        ctk.CTkFrame(sidebar, height=1, fg_color="#334155").pack(fill="x", padx=20, pady=15)
        
        # Zone de navigation scrollable
        nav_scrollable = ctk.CTkScrollableFrame(
            sidebar, 
            fg_color=self.colors["sidebar_bg"],
            scrollbar_button_color="#475569",
            scrollbar_button_hover_color="#64748b"
        )
        nav_scrollable.pack(fill="both", expand=True, padx=0, pady=0)
        self.nav_scrollable = nav_scrollable
        
        # Navigation
        nav_items = [
            ("📊", "dashboard", self._t("dashboard", "Dashboard"), lambda: self._run_with_loading(self._show_dashboard, "Préparation du dashboard...")),
            ("👥", "students", self._t("students", "Étudiants"), lambda: self._run_with_loading(self._show_students, "Chargement des étudiants...")),
            ("🧾", "academic_data", self._t("academic_data", "Données Académiques"), lambda: self._run_with_loading(self._show_student_academic_data, "Chargement des données académiques...")),
            ("💰", "finance", self._t("finance", "Finances"), lambda: self._run_with_loading(self._show_finance, "Chargement des finances...")),
            ("📚", "academic_years", self._t("academic_years", "Années Acad."), lambda: self._run_with_loading(self._show_academic_years, "Chargement des années académiques...")),
            ("🔄", "transfers", self._t("transfers", "Transferts"), lambda: self._run_with_loading(self._show_transfers, "Chargement des transferts...")),
            ("📋", "access_logs", self._t("access_logs", "Logs d'Accès"), lambda: self._run_with_loading(self._show_access_logs, "Chargement des journaux d'accès...")),
            ("📈", "reports", self._t("reports", "Rapports"), lambda: self._run_with_loading(self._show_reports, "Génération des rapports...")),
        ]

        if self.is_super_admin:
            nav_items.insert(
                2,
                ("✅", "access_requests", self._t("access_requests", "Demandes d'accès"), lambda: self._run_with_loading(self._show_access_requests, "Chargement des demandes d'accès...")),
            )

        nav_items = [item for item in nav_items if self._can_access_view(item[1])]
        
        self.nav_buttons = []
        for icon, key, label, callback in nav_items:
            btn = ctk.CTkButton(
                nav_scrollable, text=f"{icon}  {label}", hover_color="#334155", text_color=self.colors["text_white"], anchor="w", command=callback, height=45, corner_radius=8, font=ctk.CTkFont(size=13, weight="bold")
            )
            btn.pack(fill="x", padx=15, pady=3)
            
            # Add tooltip on hover (show label when icon-only in compact mode)
            def create_tooltip_binding(button, tooltip_text):
                tooltip_obj = Tooltip(button, tooltip_text)
                
                def on_enter(_event):
                    if self.sidebar_mode == "compact":
                        tooltip_obj.show_tooltip(_event)
                
                def on_leave(_event):
                    tooltip_obj.hide_tooltip()
                
                button.bind("<Enter>", on_enter)
                button.bind("<Leave>", on_leave)
            
            create_tooltip_binding(btn, label)
            
            self.nav_buttons.append({"button": btn, "key": key, "icon": icon, "label": label})
        
        # Zone logout fixe en bas
        logout_footer = ctk.CTkFrame(sidebar, fg_color=self.colors["sidebar_bg"], height=100)
        logout_footer.pack(fill="x", side="bottom", pady=0)
        logout_footer.pack_propagate(False)
        self.logout_footer = logout_footer
        
        # Séparateur avant logout
        ctk.CTkFrame(logout_footer, height=1, fg_color="#334155").pack(fill="x", padx=20, pady=(8, 12))
        
        # Logout - Style amélioré
        logout_height = 50
        logout_font_size = 13
        if self.screen_width >= 1400:
            logout_height = 60
            logout_font_size = 14
        elif self.screen_width < 900:
            logout_height = 46
            logout_font_size = 12

        self.logout_btn = ctk.CTkButton(
            logout_footer,
            text=f"🚪  {self._t('logout', 'Déconnexion')}",
            fg_color="#dc2626",
            hover_color="#b91c1c",
            text_color="#ffffff",
            command=self._confirm_logout,
            height=logout_height,
            corner_radius=10,
            anchor="center",
            border_width=2,
            border_color="#991b1b",
            font=ctk.CTkFont(size=logout_font_size, weight="bold")
        )
        self.logout_btn.pack(fill="x", padx=15, pady=(0, 20))
        
        # Add tooltip for logout button
        logout_tooltip = Tooltip(self.logout_btn, self._t("logout_tooltip", "Se déconnecter du système"))
        def show_logout_tooltip(_event):
            if self.sidebar_mode == "compact":
                logout_tooltip.show_tooltip(_event)
        def hide_logout_tooltip(_event):
            logout_tooltip.hide_tooltip()
        self.logout_btn.bind("<Enter>", show_logout_tooltip)
        self.logout_btn.bind("<Leave>", hide_logout_tooltip)
        
        # === MAIN CONTENT ===
        self.main_content = ctk.CTkFrame(container, fg_color=self.colors["main_bg"])
        self.main_content.pack(side="right", fill="both", expand=True)
        self.main_content.bind("<Configure>", self._on_resize)
        
        # Top bar avec titre et langue
        topbar = ctk.CTkFrame(self.main_content, height=90, corner_radius=10, border_width=1, border_color=self.colors["border"])
        topbar.pack(fill="x", padx=25, pady=(6, 0))
        topbar.pack_propagate(False)
        self.topbar = topbar
        
        # Titre centré au milieu
        title_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        title_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.title_frame = title_frame
        
        self.title_label = ctk.CTkLabel(
            title_frame, text=self._t("dashboard", "Dashboard"), font=ctk.CTkFont(size=28, weight="bold"), text_color=self.colors["text_dark"]
        )
        self.title_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            title_frame, text=f"Vue d'ensemble • {datetime.now().strftime('%d %B %Y')}", font=ctk.CTkFont(size=13), text_color=self.colors["text_light"]
        )
        self.subtitle_label.pack()
        
        # Sélecteur de langue et thème à droite
        lang_frame = ctk.CTkFrame(topbar, fg_color=self.colors["card_bg"], corner_radius=10, border_width=1, border_color=self.colors["border"])
        lang_frame.pack(side="right", padx=10)
        self.lang_frame = lang_frame
        
        ctk.CTkLabel(
            lang_frame, text="🌐", font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=(15, 5), pady=10)
        
        self.lang_switch = ctk.CTkSegmentedButton(
            lang_frame, values=["FR", "EN"], command=self._on_language_change, font=ctk.CTkFont(size=12, weight="bold"), fg_color=self.colors["border"], selected_color=self.colors["primary"], selected_hover_color="#2563eb", unselected_color=self.colors["card_bg"], unselected_hover_color=self.colors["hover"]
        )
        self.lang_switch.set(self.selected_language)
        self.lang_switch.pack(side="left", padx=(5, 15), pady=10)

        theme_btn = ctk.CTkButton(
            lang_frame, text="🌙" if self.theme.current_theme == "light" else "☀️", width=40, height=32, fg_color=self.colors["border"], hover_color=self.colors["hover"], text_color=self.colors["text_dark"], command=self._toggle_theme
        )
        theme_btn.pack(side="left", padx=(0, 15), pady=10)
        self.theme_btn = theme_btn
        
        # Content container + scrollable frame (for slide animation)
        self.content_container = ctk.CTkFrame(self.main_content)
        self.content_container.pack(fill="both", expand=True, padx=25, pady=6)

        self.content_frame = ctk.CTkScrollableFrame(
            self.content_container, scrollbar_button_color=self.colors["border"], scrollbar_button_hover_color=self.colors["text_light"]
        )
        self.content_frame.pack(fill="both", expand=True)
        
        self.content_frame.update_idletasks()
        
        # === FOOTER HARMONISÉ ===
        footer = self._create_footer()
        footer.pack(fill="x", padx=25, pady=(0, 15), side="bottom")
        self.footer = footer
        
        self._ensure_loading_overlay()
        
        # Afficher la vue active
        self._render_current_view()
        # Sécurité post-rendu: évite un overlay résiduel lors du premier affichage
        self.after(300, self._force_reset_loading_state)
        self._translate_all_windows()
        self._start_translation_watchdog()
        # Appliquer le mode responsive automatique selon la largeur réelle
        self._do_update_sidebar_layout()
        self._update_topbar_layout()
        # Stabilisation post-montage: certains widgets CustomTkinter n'ont pas
        # encore leur taille finale au tout premier rendu.
        self.after(90, self._stabilize_initial_layout)
        self.after(260, self._stabilize_initial_layout)
        # Préchauffer le cache plus tôt pour que les premières navigations soient instantanées
        self._schedule_heavy_views_prefetch(delay_ms=600)
        # Démarrer la surveillance d'inactivité (déconnexion auto après 30 min)
        self.after(500, self._start_idle_watcher)

    def _stabilize_initial_layout(self):
        """Force un recalcul complet du layout juste après l'affichage initial.

        Corrige le cas où le dashboard n'est pas entièrement visible tant qu'il
        n'y a pas eu une interaction (clic/changement de thème).
        """
        if not self.winfo_exists():
            return

        try:
            self.update_idletasks()
            self._refresh_responsive_metrics()
            self._do_update_sidebar_layout()
            self._update_topbar_layout()
            self._update_footer_layout()
            self._update_responsive_padding()

            # Re-render unique après taille réelle disponible
            if not self._initial_layout_stabilized:
                self._initial_layout_stabilized = True
                self._render_current_view()
                self.update_idletasks()
        except Exception as exc:
            logger.debug(f"Initial layout stabilization skipped: {exc}")
    
    def _create_card(self, parent, width=None, height=None):
        """Crée une carte avec ombre moderne"""
        card = ctk.CTkFrame(
            parent, fg_color=self.colors["card_bg"], corner_radius=12
        )
        if width:
            card.configure(width=width)
        if height:
            card.configure(height=height)
            card.pack_propagate(False)
        return card

    def _create_footer(self):
        """Crée un footer harmonisé et responsive"""
        footer = ctk.CTkFrame(self.main_content, fg_color=self.colors["card_bg"], corner_radius=8)
        
        # Responsive padding
        padx = 15 if self.screen_width < 900 else 20
        pady = 8 if self.screen_width < 900 else 10
        
        # Container du footer
        footer_content = ctk.CTkFrame(footer, fg_color=self.colors["card_bg"])
        footer_content.pack(fill="x", padx=padx, pady=pady)
        
        # Infos à gauche
        left_frame = ctk.CTkFrame(footer_content, fg_color=self.colors["card_bg"])
        left_frame.pack(side="left", fill="x", expand=True)
        self.footer_left_frame = left_frame
        
        sync_status = "✓ Synchronisé" if hasattr(self, '_last_sync') else "En cours..."
        ctk.CTkLabel(
            left_frame,
            text=f"🔄 {sync_status}",
            font=ctk.CTkFont(size=10 if self.screen_width < 900 else 11),
            text_color=self.colors["text_light"]
        ).pack(side="left", padx=(0, 15))
        
        # Info temps réel
        current_time = datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            left_frame,
            text=f"⏰ {current_time}",
            font=ctk.CTkFont(size=10 if self.screen_width < 900 else 11),
            text_color=self.colors["text_light"]
        ).pack(side="left")
        
        # Infos à droite
        right_frame = ctk.CTkFrame(footer_content, fg_color=self.colors["card_bg"])
        right_frame.pack(side="right")
        self.footer_right_frame = right_frame
        
        version_text = "v1.1.0" if self.screen_width >= 900 else "v1.1"
        ctk.CTkLabel(
            right_frame,
            text=f"U.O.R Platform • {version_text}",
            font=ctk.CTkFont(size=9 if self.screen_width < 900 else 10),
            text_color=self.colors["text_light"]
        ).pack(side="right")

        self._update_footer_layout()
        
        return footer

    def _shade_color(self, hex_color: str, factor: float = 0.9) -> str:
        """Assombrit légèrement une couleur hex"""
        try:
            hex_color = hex_color.lstrip("#")
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            r = max(0, min(255, int(r * factor)))
            g = max(0, min(255, int(g * factor)))
            b = max(0, min(255, int(b * factor)))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _animate_view_transition(self):
        """Animation glissante de transition entre vues"""
        # Transition instantanée : aucun glissement visible
        if not hasattr(self, "content_frame"):
            return
        try:
            self.content_frame.place_configure(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

    def _center_and_show_dialog(self, window):
        """Centre une fenêtre de dialogue sur l'écran sans l'agrandir."""
        if not window:
            return

        try:
            if not window.winfo_exists():
                return
            window.update_idletasks()
        except Exception:
            return

        try:
            # Ne pas agrandir au-delà de ce qui est défini, juste centrer
            window_width = window.winfo_width()
            window_height = window.winfo_height()

            parent = self.winfo_toplevel()
            parent_width = parent.winfo_width() or self.screen_width
            parent_height = parent.winfo_height() or self.screen_height
            parent_x = parent.winfo_rootx() if parent.winfo_ismapped() else 0
            parent_y = parent.winfo_rooty() if parent.winfo_ismapped() else 0

            x = parent_x + max(0, (parent_width - window_width) // 2)
            y = parent_y + max(0, (parent_height - window_height) // 2)

            # Vérifier que la fenêtre reste à l'écran
            max_x = max(0, self.screen_width - window_width)
            max_y = max(0, self.screen_height - window_height)
            x = max(0, min(x, max_x))
            y = max(0, min(y, max_y))

            window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def _animate_window_open(self, window):
        """Affiche correctement une fenêtre secondaire (centré, sans animation lourde)."""
        if not window:
            return

        try:
            window.update_idletasks()
        except Exception:
            return

        try:
            parent = self.winfo_toplevel()
            if parent is not window:
                window.transient(parent)
        except Exception:
            pass

        try:
            window.withdraw()
        except Exception:
            pass

        def finalize_open():
            try:
                if not window.winfo_exists():
                    return
            except Exception:
                return

            self._center_and_show_dialog(window)

            try:
                window.deiconify()
                window.lift()
                window.focus_set()
            except Exception:
                pass

        window.after(50, finalize_open)

    def _show_loading_dialog(self, title: str = "Traitement en cours..."):
        """Affiche un dialog avec un loading indicator
        
        Returns: (dialog_window, loading_indicator_widget)
        """
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("350x120")
        dialog.grab_set()
        dialog.resizable(False, False)
        
        # Contenu
        container = ctk.CTkFrame(dialog)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        loading = LoadingIndicator(container, text=title, color=self.colors.get("primary", "#3b82f6"))
        loading.pack(fill="x", expand=True)
        loading.start()

        self._animate_window_open(dialog)
        return dialog, loading

    def _update_sidebar_layout(self):
        """Met à jour l'affichage de la sidebar selon la taille de fenêtre (avec debouncing)"""
        # Debouncer les updates pendant le scrolling pour éviter le lag
        if self._sidebar_update_debounce_job:
            self.after_cancel(self._sidebar_update_debounce_job)
        
        self._sidebar_update_debounce_job = self.after(200, self._do_update_sidebar_layout)
    
    def _do_update_sidebar_layout(self):
        """Effectue réellement la mise à jour du sidebar"""
        self._sidebar_update_debounce_job = None

        # Recalculer la taille réelle courante avant de décider compact/complet.
        try:
            self._refresh_responsive_metrics()
        except Exception:
            pass
        
        # Si l'utilisateur a manuellement changé le mode, respecter son choix
        if self.sidebar_mode_manual is not None:
            return
        
        # Sinon, utiliser le mode auto selon la largeur réelle de la fenêtre
        target_mode = "compact" if self.screen_width < self.sidebar_collapse_breakpoint else "full"
        if target_mode == self.sidebar_mode:
            return

        self._apply_sidebar_mode(target_mode)
    
    def _toggle_sidebar_expand(self):
        """Bascule entre le mode compact et le mode complet"""
        if self._view_switch_in_progress or self._ui_rebuild_in_progress:
            return

        # Déterminer le nouveau mode
        if self.sidebar_mode == "compact":
            new_mode = "full"
        else:
            new_mode = "compact"
        
        # Marquer que c'est un choix manuel
        self.sidebar_mode_manual = new_mode
        
        # Appliquer le nouveau mode
        self._apply_sidebar_mode(new_mode)
        
        # Mettre à jour le label
        self._update_sidebar_mode_label()

    def _apply_sidebar_mode(self, mode: str):
        """Applique le mode compact ou complet à la sidebar"""
        self.sidebar_mode = mode

        if mode == "compact":
            self.sidebar.configure(width=self.sidebar_width_compact)
            self.logo_title_label.configure(text="U.O.R", font=ctk.CTkFont(size=22, weight="bold"))
            if self.logo_subtitle_label.winfo_ismapped():
                self.logo_subtitle_label.pack_forget()

            for item in self.nav_buttons:
                btn = item["button"]
                btn.configure(
                    text=item["icon"], anchor="center", font=ctk.CTkFont(size=18, weight="bold")
                )

            if self.logout_btn:
                # En mode compact, garder le texte mais plus petit
                self.logout_btn.configure(
                    text="🚪" if self.screen_width < 900 else "🚪 Quitter",
                    anchor="center",
                    font=ctk.CTkFont(size=11, weight="bold")
                )
                try:
                    self.logout_btn.pack_configure(padx=8)
                except Exception:
                    pass

            # DISABLED: Hover binding causes constant flickering/flashing
            # self._bind_sidebar_hover_expand()
        else:
            self.sidebar.configure(width=self.sidebar_width_full)
            self.logo_title_label.configure(text="U.O.R", font=ctk.CTkFont(size=32, weight="bold"))
            if not self.logo_subtitle_label.winfo_ismapped():
                self.logo_subtitle_label.pack()

            for item in self.nav_buttons:
                btn = item["button"]
                btn.configure(
                    text=f"{item['icon']}  {item['label']}", anchor="w", font=ctk.CTkFont(size=13, weight="bold")
                )

            if self.logout_btn:
                self.logout_btn.configure(
                    text=f"🚪  {self._t('logout', 'Déconnexion')}",
                    anchor="center",
                    font=ctk.CTkFont(size=13, weight="bold")
                )
                try:
                    self.logout_btn.pack_configure(padx=15)
                except Exception:
                    pass

            self._unbind_sidebar_hover_expand()

        try:
            self._update_responsive_padding()
        except Exception:
            pass

    def _update_sidebar_mode_label(self):
        """Met à jour le label pour afficher le mode actuel"""
        try:
            if self.sidebar_mode == "compact":
                label_text = self._t("sidebar_mode_compact", "Mode: Compact")
            else:
                label_text = self._t("sidebar_mode_full", "Mode: Complet")
            
            # Mettre à jour le label
            if hasattr(self, 'sidebar_mode_label') and self.sidebar_mode_label:
                self.sidebar_mode_label.configure(text=label_text)
        except Exception as e:
            logger.warning(f"Error updating sidebar mode label: {e}")

    def _bind_sidebar_hover_expand(self):
        if not self.sidebar:
            return

        self.sidebar.bind("<Enter>", self._on_sidebar_enter)
        self.sidebar.bind("<Leave>", self._on_sidebar_leave)

    def _animate_sidebar_width(self, target_width: int, duration_ms: int = 180, on_complete=None):
        if not self.sidebar:
            return

        if self._sidebar_anim_job:
            try:
                self.after_cancel(self._sidebar_anim_job)
            except Exception:
                pass
            self._sidebar_anim_job = None

        self._sidebar_animating = True
        try:
            current_width = int(self.sidebar.cget("width"))
        except Exception:
            current_width = self.sidebar_width_compact

        steps = max(1, int(duration_ms / 15))
        delta = (target_width - current_width) / steps

        def step(count=0, width=current_width):
            if count >= steps:
                self.sidebar.configure(width=target_width)
                self._sidebar_animating = False
                if on_complete:
                    on_complete()
                return
            width += delta
            self.sidebar.configure(width=int(width))
            self._sidebar_anim_job = self.after(15, lambda: step(count + 1, width))

        step()

    def _unbind_sidebar_hover_expand(self):
        if not self.sidebar:
            return

        self.sidebar.unbind("<Enter>")
        self.sidebar.unbind("<Leave>")
        self.sidebar_hover_expanded = False

    def _on_sidebar_enter(self, _event=None):
        """Expand sidebar on hover (sans animation lourde pour éviter flicker)"""
        if self.sidebar_mode != "compact" or self.sidebar_hover_expanded:
            return
        self.sidebar_hover_expanded = True
        self.logo_subtitle_label.pack()
        for item in self.nav_buttons:
            btn = item["button"]
            btn.configure(
                text=f"{item['icon']}  {item['label']}", anchor="w", font=ctk.CTkFont(size=13, weight="bold")
            )
        if self.logout_btn:
            self.logout_btn.configure(text=f"🚪  {self._t('logout', 'Déconnexion')}", anchor="w")

        # Expand sidebar directement sans animation (évite flicker)
        self.sidebar.configure(width=self.sidebar_width_full)

    def _on_sidebar_leave(self, _event=None):
        """Collapse sidebar on leave (sans animation)"""
        if self.sidebar_mode != "compact" or not self.sidebar_hover_expanded:
            return
        self.sidebar_hover_expanded = False
        
        # Collapse directement
        if self.logo_subtitle_label.winfo_ismapped():
            self.logo_subtitle_label.pack_forget()
        for item in self.nav_buttons:
            btn = item["button"]
            btn.configure(
                text=item["icon"], anchor="center", font=ctk.CTkFont(size=18, weight="bold")
            )
        if self.logout_btn:
            self.logout_btn.configure(text="🚪", anchor="center")

        # Collapse sidebar directement sans animation
        self.sidebar.configure(width=self.sidebar_width_compact)

    def _get_table_mode(self) -> str:
        """Retourne le mode de tableau en fonction de la largeur de fenêtre"""
        try:
            window_width = self.parent_window.winfo_width() if self.parent_window else self.winfo_width()
        except Exception:
            window_width = self.winfo_width()
        return "compact" if window_width < self.table_compact_breakpoint else "large"

    def _update_table_mode(self):
        """Met à jour le mode des tableaux et rafraîchit la vue si besoin"""
        new_mode = self._get_table_mode()
        if new_mode == self.table_mode:
            return
        self.table_mode = new_mode
        refreshable_views = {"students", "finance", "access_logs", "reports", "academic_years", "transfers"}
        if self.current_view not in refreshable_views:
            return

        if self._table_mode_refresh_job:
            self.after_cancel(self._table_mode_refresh_job)
        self._table_mode_refresh_job = self.after(80, self._refresh_current_view_after_table_mode_change)

    def _refresh_current_view_after_table_mode_change(self):
        """Rafraîchit la vue courante après changement de mode tableau, avec debounce."""
        self._table_mode_refresh_job = None
        try:
            if self._view_switch_in_progress or self._loading_visible:
                return
            self._render_current_view()
        except Exception as e:
            logger.debug(f"Table mode refresh error: {e}")

    def _make_card_clickable(self, card, command):
        """Rend une carte cliquable avec effet hover"""
        if not command:
            return
        original_command = command
        command = lambda: self._run_with_loading(original_command)
        base_color = card.cget("fg_color")
        hover_color = self._shade_color(base_color, 0.9)

        def on_enter(_):
            card.configure(fg_color=hover_color)

        def on_leave(_):
            card.configure(fg_color=base_color)

        def on_click(_):
            command()

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", on_click)

    def _fc_to_usd(self, amount_usd: float) -> float:
        try:
            return float(amount_usd)
        except Exception:
            return 0.0

    def _format_usd(self, amount_usd: float) -> str:
        return f"${self._fc_to_usd(amount_usd):,.2f}"

    def _get_cached_photo(self, photo_path: str = None, photo_blob: bytes = None, size=(40, 50)):
        """Retourne une image CTkImage depuis cache"""
        cache_key = None
        if photo_path:
            cache_key = f"path:{photo_path}:{size}"
        elif photo_blob:
            digest = hashlib.sha256(photo_blob).hexdigest()
            cache_key = f"blob:{digest}:{size}"

        if cache_key and cache_key in self._photo_cache:
            return self._photo_cache[cache_key]

        image = None
        try:
            if photo_path and os.path.exists(photo_path):
                image = Image.open(photo_path)
            elif photo_blob:
                image = Image.open(io.BytesIO(photo_blob))
            if image:
                image.thumbnail(size)
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                if cache_key:
                    self._photo_cache[cache_key] = ctk_image
                return ctk_image
        except Exception:
            return None

        return None

    def _render_photo_cell(self, row, column_index: int, photo_path: str = None, photo_blob: bytes = None, size=(40, 50)):
        """Rend une cellule photo dans un tableau"""
        photo_frame = ctk.CTkFrame(row)
        photo_frame.grid(row=0, column=column_index, sticky="ew", padx=10, pady=6)
        ctk_image = self._get_cached_photo(photo_path, photo_blob, size=size)
        if ctk_image:
            photo_label = ctk.CTkLabel(photo_frame, image=ctk_image, text="")
            photo_label.image = ctk_image
            photo_label.pack()
        else:
            ctk.CTkLabel(photo_frame, text="—", text_color=self.colors["text_light"]).pack()
    
    def _create_stat_card(self, parent, title, value, icon, color, action_text, action_command=None):
        """Crée une carte de statistique colorée - RESPONSIVE"""
        is_tiny_screen = self.screen_width < 860
        is_small_screen = self.screen_width < 1000
        
        card_height = 102 if is_tiny_screen else (120 if is_small_screen else 140)
        card = ctk.CTkFrame(parent, fg_color=color, corner_radius=12, height=card_height)
        card.pack_propagate(False)
        hover_color = self._shade_color(color, 0.9)
        
        # En-tête avec titre et icône
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12 if is_tiny_screen else (15 if is_small_screen else 20), pady=(12 if is_tiny_screen else (15 if is_small_screen else 20), 6 if is_tiny_screen else 8))
        
        title_size = 9 if is_tiny_screen else (10 if is_small_screen else 12)
        header_label = ctk.CTkLabel(
            header, text=title, font=ctk.CTkFont(size=title_size), text_color=self.colors["text_white"]
        )
        header_label.pack(side="left")
        
        icon_size = 14 if is_tiny_screen else (16 if is_small_screen else 20)
        icon_label = ctk.CTkLabel(
            header, text=icon, font=ctk.CTkFont(size=icon_size)
        )
        icon_label.pack(side="right")
        
        # Valeur
        value_size = 17 if is_tiny_screen else (20 if is_small_screen else 28)
        value_label = ctk.CTkLabel(
            card, text=value, font=ctk.CTkFont(size=value_size, weight="bold"), text_color=self.colors["text_white"]
        )
        value_label.pack(anchor="w", padx=12 if is_tiny_screen else (15 if is_small_screen else 20), pady=(0, 8 if is_tiny_screen else 10))
        
        # Action
        action_size = 8 if is_tiny_screen else (9 if is_small_screen else 11)
        wrapped_command = (lambda: self._run_with_loading(action_command)) if action_command else None
        action_btn = ctk.CTkButton(
            card, text=action_text, hover_color="#0a0a0a", text_color=self.colors["text_white"], font=ctk.CTkFont(size=action_size), height=20 if is_tiny_screen else (22 if is_small_screen else 25), corner_radius=6, command=wrapped_command
        )
        action_btn.pack(anchor="w", padx=12 if is_tiny_screen else (15 if is_small_screen else 20), pady=(0, 8 if is_tiny_screen else 10))

        if action_command:
            def on_enter(_):
                card.configure(fg_color=hover_color)

            def on_leave(_):
                card.configure(fg_color=color)

            def on_click(_):
                wrapped_command()

            for widget in (card, header, header_label, icon_label, value_label):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
                widget.bind("<Button-1>", on_click)
        
        return card

    def _configure_table_columns(self, frame, column_weights, min_widths=None):
        """Configure la grille des colonnes pour un tableau"""
        for idx, weight in enumerate(column_weights):
            try:
                weight_value = int(round(weight))
            except Exception:
                weight_value = 1
            if weight_value <= 0:
                weight_value = 1
            min_size = None
            if min_widths and idx < len(min_widths):
                min_size = min_widths[idx]
            if min_size:
                frame.grid_columnconfigure(idx, weight=weight_value, minsize=min_size)
            else:
                frame.grid_columnconfigure(idx, weight=weight_value)

    def _create_horizontal_scrollable_table(self, parent, headers, column_weights, anchors=None, min_widths=None):
        """Crée une table avec scroll horizontal si nécessaire - retourne le conteneur des rows"""
        # Calculer la largeur totale requise
        total_min_width = sum(min_widths) if min_widths else 0
        can_fit = total_min_width + 50 < (self.screen_width - 120)  # 120px pour sidebar + margins
        
        scroll_container = ctk.CTkFrame(parent, fg_color="transparent")
        scroll_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # En-tête
        header_frame = self._create_table_header(scroll_container, headers, column_weights, 
                                                 anchors=anchors, min_widths=min_widths, 
                                                 padx=10, pady=8)
        
        # Scroll frame pour les données (utilise le scrolling vertical par défaut)
        data_scroll = ctk.CTkScrollableFrame(scroll_container, fg_color="transparent")
        data_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        return data_scroll


    def _set_scrollbar_visible(self, scrollable_frame, visible: bool, width: int = None):
        """Affiche ou masque la barre de scroll d'un CTkScrollableFrame"""
        bar = getattr(scrollable_frame, "_scrollbar", None)
        if not bar:
            return
        target_width = width if width is not None else self._scaled(12)
        if not visible:
            target_width = 0
        try:
            bar.configure(width=target_width)
        except Exception:
            pass

    def _set_main_scrollbar_visible(self, visible: bool):
        """Gère la barre de scroll principale (content_frame)"""
        if hasattr(self, "content_frame"):
            self._set_scrollbar_visible(self.content_frame, visible)

    def _get_table_spacing_profile(self) -> dict:
        """Retourne des espacements harmonisés pour un rendu doux et lisible."""
        if self.screen_width < 900:
            return {
                "header_padx": 8,
                "header_pady": 7,
                "row_padx": 8,
                "row_pady": 7,
                "max_lines": 2,
            }
        if self.screen_width < 1200:
            return {
                "header_padx": 9,
                "header_pady": 8,
                "row_padx": 9,
                "row_pady": 8,
                "max_lines": 2,
            }
        return {
            "header_padx": 10,
            "header_pady": 9,
            "row_padx": 10,
            "row_pady": 9,
            "max_lines": 3,
        }

    def _table_justify_from_anchor(self, anchor: str) -> str:
        """Mappe un anchor Tk en justify pour garder un rendu propre."""
        anchor = (anchor or "center").lower()
        if anchor in ("w", "nw", "sw", "left"):
            return "left"
        if anchor in ("e", "ne", "se", "right"):
            return "right"
        return "center"

    def _format_table_text(self, value, wrap_width: int = 0, max_lines: int = 2) -> str:
        """Formate le texte d'une cellule pour éviter les débordements visuels.

        - Respecte les retours ligne existants
        - Coupe proprement avec ellipsis si trop long
        """
        text = "" if value is None else str(value)
        if wrap_width <= 0:
            return text

        # Approximation simple chars/ligne selon largeur pixels
        chars_per_line = max(8, int(wrap_width / 7))
        if chars_per_line <= 0:
            return text

        output_lines = []
        source_lines = text.split("\n") if "\n" in text else [text]

        for source in source_lines:
            source = source.strip()
            if not source:
                output_lines.append("")
                continue

            words = source.split()
            if not words:
                output_lines.append(source)
                continue

            current = words[0]
            for w in words[1:]:
                candidate = f"{current} {w}"
                if len(candidate) <= chars_per_line:
                    current = candidate
                else:
                    output_lines.append(current)
                    current = w
            output_lines.append(current)

        if len(output_lines) <= max_lines:
            return "\n".join(output_lines)

        trimmed = output_lines[:max_lines]
        last = trimmed[-1].rstrip()
        if len(last) >= chars_per_line:
            trim_at = max(0, chars_per_line - 1)
            trimmed[-1] = trimmed[-1][:trim_at].rstrip() + "…"
        else:
            trimmed[-1] = (trimmed[-1] + " …").strip()
        return "\n".join(trimmed)

    def _create_table_header(self, parent, headers, column_weights, anchors=None, min_widths=None, padx=10, pady=10):
        """Crée un header de tableau aligné - RESPONSIVE"""
        # Adapter font size pour petit écran
        is_tiny_screen = self.screen_width < 900
        header_font_size = 9 if is_tiny_screen else 11
        spacing = self._get_table_spacing_profile()
        header_padx = max(padx, spacing["header_padx"])
        header_pady = max(pady, spacing["header_pady"])
        max_lines = spacing["max_lines"]
        is_dark = self.theme.current_theme == "dark"
        header_bg = self._shade_color(self.colors["border"], 1.06) if is_dark else self._shade_color(self.colors["border"], 0.985)
        header_border = self._shade_color(self.colors["border"], 1.24) if is_dark else self._shade_color(self.colors["border"], 0.90)
        
        header_frame = ctk.CTkFrame(
            parent,
            fg_color=header_bg,
            corner_radius=10,
            border_width=1,
            border_color=header_border,
        )
        header_frame.pack(fill="x", padx=0, pady=(0, 0))

        for col, header_text in enumerate(headers):
            anchor = anchors[col] if anchors else "center"
            cell_width = min_widths[col] - 16 if min_widths and col < len(min_widths) else 0
            justify = self._table_justify_from_anchor(anchor)
            display_text = self._format_table_text(header_text, wrap_width=cell_width, max_lines=max_lines)
            label = ctk.CTkLabel(
                header_frame,
                text=display_text,
                font=ctk.CTkFont(size=header_font_size, weight="bold"),
                text_color=self.colors["text_dark"],
                anchor=anchor,
                justify=justify,
                wraplength=cell_width if cell_width > 0 else 0,
            )
            label.grid(row=0, column=col, sticky="ew", padx=header_padx, pady=header_pady)

        self._configure_table_columns(header_frame, column_weights, min_widths=min_widths)
        return header_frame

    def _style_table_row(self, row, row_index: int, enable_hover: bool = True):
        """Applique un style premium de ligne (zebra + hover) pour les tables."""
        is_dark = self.theme.current_theme == "dark"
        base = self.colors["hover"]

        if is_dark:
            stripe = self._shade_color(base, 1.08)
            hover = self._shade_color(base, 1.18)
            border_normal = self._shade_color(base, 1.30)
            border_hover = self._shade_color(base, 1.45)
        else:
            stripe = self._shade_color(base, 0.96)
            hover = self._shade_color(base, 0.90)
            border_normal = self._shade_color(base, 0.88)
            border_hover = self._shade_color(base, 0.80)

        base_color = base if row_index % 2 == 0 else stripe
        row.configure(
            fg_color=base_color,
            corner_radius=8,
            border_width=1,
            border_color=border_normal,
        )

        if not enable_hover:
            return

        def on_enter(_event=None):
            try:
                row.configure(fg_color=hover, border_color=border_hover)
            except Exception:
                pass

        def on_leave(_event=None):
            try:
                row.configure(fg_color=base_color, border_color=border_normal)
            except Exception:
                pass

        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

    def _get_table_layout(self, key: str, fallback_count: int = 0):
        """Retourne un layout standardisé (weights + anchors) pour les tableaux - RESPONSIVE"""
        # Adapte les layout selon la taille d'écran
        is_small_screen = self.screen_width < 1200
        is_tiny_screen = self.screen_width < 900
        
        layouts = {
            "dashboard_access": {
                "weights": [3, 1.2, 2, 1] if not is_tiny_screen else [2, 1, 1.5, 0.8], "anchors": ["w", "w", "w", "e"], "min_widths_large": [220, 90, 160, 90], "min_widths_compact": [140, 70, 100, 70], "min_widths_tiny": [100, 60, 80, 60], }, "students_promo": {
                "weights": [1.2, 3, 3, 1.2, 1.2, 1.2, 2] if not is_small_screen else [1, 2, 2, 1, 1, 1, 1.5], "anchors": ["center", "w", "w", "center", "center", "center", "center"], "min_widths_large": [70, 200, 220, 95, 95, 95, 150], "min_widths_compact": [60, 160, 180, 85, 85, 85, 120], "min_widths_tiny": [50, 120, 140, 75, 75, 75, 100], }, "payment_history": {
                "weights": [2.2, 1.2, 1.2] if not is_tiny_screen else [2, 1, 1], "anchors": ["w", "e", "center"], "min_widths_large": [220, 120, 120], "min_widths_compact": [160, 100, 100], "min_widths_tiny": [120, 80, 80], }, "finance_payments": {
                "weights": [1.2, 3, 1.2, 2, 2, 1.2, 1.2] if not is_small_screen else [1, 2, 1, 1.5, 1.5, 1, 1], "anchors": ["center", "w", "w", "e", "e", "center", "center"], "min_widths_large": [70, 220, 90, 150, 150, 110, 110], "min_widths_compact": [60, 170, 80, 120, 120, 95, 95], "min_widths_tiny": [50, 130, 70, 100, 100, 80, 80], }, "access_logs": {
                "weights": [1.2, 3, 1.2, 2, 1, 1, 1, 1, 1.2] if not is_small_screen else [1, 2, 1, 1.5, 0.8, 0.8, 0.8, 0.8, 1], "anchors": ["center", "w", "w", "w", "center", "center", "center", "center", "e"], "min_widths_large": [70, 220, 90, 160, 90, 90, 90, 90, 100], "min_widths_compact": [60, 170, 80, 130, 75, 75, 75, 75, 90], "min_widths_tiny": [50, 130, 70, 100, 65, 65, 65, 65, 80], }, "reports_faculty": {
                "weights": [1.2, 2.5, 2.5, 1.2, 1.2, 1.2, 2] if not is_small_screen else [1, 2, 2, 1, 1, 1, 1.5], "anchors": ["center", "w", "w", "center", "center", "center", "e"], "min_widths_large": [70, 180, 180, 120, 120, 120, 150], "min_widths_compact": [60, 150, 150, 110, 110, 110, 130], "min_widths_tiny": [50, 120, 120, 95, 95, 95, 110], }, "academic_promos": {
                "weights": [2.2, 3, 3, 1.2, 1.6, 1.6, 1.4] if not is_small_screen else [2, 2.2, 2.2, 1, 1.4, 1.4, 1.2], "anchors": ["w", "w", "w", "center", "center", "center", "center"], "min_widths_large": [150, 180, 180, 90, 150, 150, 140], "min_widths_compact": [140, 170, 170, 80, 140, 140, 130], "min_widths_tiny": [120, 130, 130, 70, 120, 120, 115], }, "exam_periods": {
                "weights": [3, 1.2, 1.2, 1.2] if not is_tiny_screen else [2, 1, 1, 1], "anchors": ["w", "center", "center", "e"], "min_widths_large": [220, 120, 120, 110], "min_widths_compact": [180, 100, 100, 95], "min_widths_tiny": [140, 85, 85, 80], }, }

        layout = layouts.get(key)
        if layout:
            mode = self._get_table_mode()
            if is_tiny_screen and "min_widths_tiny" in layout:
                min_widths = layout.get("min_widths_tiny")
            elif mode == "compact":
                min_widths = layout.get("min_widths_compact") or layout.get("min_widths_large")
            else:
                min_widths = layout.get("min_widths_large")
            return {
                "weights": layout["weights"], "anchors": layout["anchors"], "min_widths": min_widths, }

        fallback_weights = [1] * max(0, fallback_count)
        fallback_anchors = ["center"] * max(0, fallback_count)
        fallback_min_widths = [60] * max(0, fallback_count)  # Réduit pour petit écran
        return {"weights": fallback_weights, "anchors": fallback_anchors, "min_widths": fallback_min_widths}

    def _populate_table_row(self, row, values, column_weights, text_colors=None, font_sizes=None, font_weights=None, anchors=None, min_widths=None, padx=10, pady=8):
        """Ajoute des cellules alignées dans une ligne - RESPONSIVE"""
        # Adapter les font sizes pour petit écran
        is_tiny_screen = self.screen_width < 900
        spacing = self._get_table_spacing_profile()
        row_padx = max(padx, spacing["row_padx"])
        row_pady = max(pady, spacing["row_pady"])
        max_lines = spacing["max_lines"]
        
        for col, value in enumerate(values):
            color = text_colors[col] if text_colors else self.colors["text_dark"]
            base_size = font_sizes[col] if font_sizes else 10
            # Réduire la taille de font pour petit écran
            size = max(8, base_size - 1) if is_tiny_screen else base_size
            weight = font_weights[col] if font_weights else "normal"
            anchor = anchors[col] if anchors else "center"
            justify = self._table_justify_from_anchor(anchor)
            cell_width = min_widths[col] - 16 if min_widths and col < len(min_widths) else 0
            display_text = self._format_table_text(value, wrap_width=cell_width, max_lines=max_lines)

            label = ctk.CTkLabel(
                row,
                text=display_text,
                font=ctk.CTkFont(size=size, weight=weight),
                text_color=color,
                anchor=anchor,
                justify=justify,
                wraplength=cell_width if cell_width > 0 else 0,
            )
            label.grid(row=0, column=col, sticky="ew", padx=row_padx, pady=row_pady)

        self._configure_table_columns(row, column_weights, min_widths=min_widths)

    def _populate_table_row_with_offset(self, row, values, column_weights, start_col=0, text_colors=None, font_sizes=None, font_weights=None, anchors=None, min_widths=None, padx=10, pady=8):
        """Ajoute des cellules alignées avec un décalage de colonne - RESPONSIVE"""
        # Adapter les font sizes pour petit écran
        is_tiny_screen = self.screen_width < 900
        spacing = self._get_table_spacing_profile()
        row_padx = max(padx, spacing["row_padx"])
        row_pady = max(pady, spacing["row_pady"])
        max_lines = spacing["max_lines"]
        
        self._configure_table_columns(row, column_weights, min_widths=min_widths)
        for idx, value in enumerate(values):
            color = text_colors[idx] if text_colors else self.colors["text_dark"]
            base_size = font_sizes[idx] if font_sizes else 10
            # Réduire la taille de font pour petit écran
            size = max(8, base_size - 1) if is_tiny_screen else base_size
            weight = font_weights[idx] if font_weights else "normal"
            anchor = anchors[idx] if anchors else "center"
            justify = self._table_justify_from_anchor(anchor)
            
            col_idx = start_col + idx
            wrap_width = min_widths[col_idx] - 16 if min_widths and col_idx < len(min_widths) else 0
            display_text = self._format_table_text(value, wrap_width=wrap_width, max_lines=max_lines)

            label = ctk.CTkLabel(
                row,
                text=display_text,
                font=ctk.CTkFont(size=size, weight=weight),
                text_color=color,
                anchor=anchor,
                justify=justify,
                wraplength=wrap_width if wrap_width > 0 else 0,
            )
            label.grid(row=0, column=col_idx, sticky="ew", padx=row_padx, pady=row_pady)
    
    def _update_nav_buttons(self, active_key):
        """Met à jour le style du menu actif"""
        for item in self.nav_buttons:
            btn = item["button"]
            key = item["key"]
            if key == active_key:
                btn.configure(fg_color=self.colors["primary"])
            else:
                btn.configure()
    
    def _show_dashboard(self):
        """Affiche le dashboard principal - Style Pro (SB Admin)"""
        self.current_view = "dashboard"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("dashboard")
        self.title_label.configure(text=self._t("dashboard", "Dashboard"))
        self.subtitle_label.configure(
            text="{} \u2022 {}".format(
                self._t("overview", "Vue d'ensemble"), datetime.now().strftime("%d %B %Y")
            )
        )

        # \u2500\u2500 donn\u00e9es
        snap = self._get_cached_data(
            "dashboard_snapshot",
            lambda: {
                "total_students": self.dashboard_service.get_total_students(),
                "eligible_students": self.dashboard_service.get_eligible_students(),
                "non_eligible_students": self.dashboard_service.get_non_eligible_students(),
                "access_granted": self.dashboard_service.get_access_granted(),
                "access_denied": self.dashboard_service.get_access_denied(),
                "revenue": self.dashboard_service.get_revenue_collected(),
                "completion": self.dashboard_service.get_degree_of_completion(),
                "activities": self.dashboard_service.get_recent_activities(8),
            },
            ttl_seconds=60.0,
        )
        total = snap["total_students"]
        eligible = snap["eligible_students"]
        non_eligible = snap["non_eligible_students"]
        access_granted = snap["access_granted"]
        access_denied = snap["access_denied"]
        revenue = snap["revenue"]
        completion = snap["completion"]

        # \u2500\u2500 responsive
        try:
            self._refresh_responsive_metrics()
        except Exception:
            pass

        try:
            cw = self.content_frame.winfo_width()
            if cw <= 1:
                cw = self.winfo_toplevel().winfo_width()
        except Exception:
            cw = self.screen_width

        try:
            top_w = self.winfo_toplevel().winfo_width() or 0
            if top_w > cw:
                cw = top_w
        except Exception:
            pass
        is_narrow = cw < 1200

        C = self.colors
        is_dark = self.theme.current_theme == "dark"
        eligible_pct = round((eligible / total * 100) if total else 0, 1)
        completion_pct = completion.get("percentage", 0)
        access_pct = round((access_granted / max(total, 1)) * 100, 0)

        # KPI Cards row
        kpi_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 18))

        kpi_items = [
            (
                f"{total:,}", "\u00c9tudiants Inscrits", "\U0001f465", "#7C3AED",
                "#EDE9FE" if not is_dark else "#2D1B6B",
                f"\u2191 {eligible_pct:.0f}% \u00e9ligibles",
            ),
            (
                self._format_usd(revenue), "Revenus Collect\u00e9s", "\U0001f4b0", "#D97706",
                "#FEF3C7" if not is_dark else "#3D2400",
                "Frais acad\u00e9miques",
            ),
            (
                f"{eligible:,}", "\u00c9tudiants \u00c9ligibles", "\u2705", "#10B981",
                "#D1FAE5" if not is_dark else "#064E3B",
                f"sur {total:,} inscrits",
            ),
            (
                f"{access_granted:,}", "Acc\u00e8s Accord\u00e9s", "\U0001f511", "#0D9488",
                "#CCFBF1" if not is_dark else "#003D35",
                f"\u2191 {access_pct:.0f}% du total",
            ),
        ]

        for i, (val, lbl, icon, _ic_color, ic_bg, trend) in enumerate(kpi_items):
            kpad = (0, 8) if i < 3 else (0, 0)
            card = ctk.CTkFrame(
                kpi_row, fg_color=C["card_bg"], corner_radius=12,
                border_width=1, border_color=C["border"]
            )
            card.pack(side="left", fill="both", expand=True, padx=kpad)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="both", expand=True, padx=18, pady=16)
            left_side = ctk.CTkFrame(inner, fg_color="transparent")
            left_side.pack(side="left", fill="both", expand=True)
            ctk.CTkLabel(
                left_side, text=val,
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=C["text_dark"], anchor="w"
            ).pack(anchor="w")
            ctk.CTkLabel(
                left_side, text=lbl,
                font=ctk.CTkFont(size=11), text_color=C["text_light"], anchor="w"
            ).pack(anchor="w", pady=(2, 8))
            ctk.CTkLabel(
                left_side, text=trend,
                font=ctk.CTkFont(size=10), text_color="#10B981", anchor="w"
            ).pack(anchor="w")
            ic_frame = ctk.CTkFrame(inner, fg_color=ic_bg, width=48, height=48, corner_radius=24)
            ic_frame.pack(side="right", anchor="n")
            ic_frame.pack_propagate(False)
            ctk.CTkLabel(ic_frame, text=icon, font=ctk.CTkFont(size=20)).pack(expand=True)

        # Charts row (Bar + Donut)
        charts_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        charts_row.pack(fill="both" if not is_narrow else "x", expand=not is_narrow, pady=(0, 18))

        # Bar chart card
        bar_card = self._create_card(charts_row)
        bar_card.pack(
            side="top" if is_narrow else "left",
            fill="both", expand=True,
            padx=(0, 10) if not is_narrow else 0,
            pady=(0, 15) if is_narrow else 0,
        )
        bar_card.configure(height=300)
        bar_card.pack_propagate(False)

        bar_header = ctk.CTkFrame(bar_card, fg_color="transparent")
        bar_header.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(
            bar_header, text="Statistiques Acad\u00e9miques",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=C["text_dark"]
        ).pack(side="left")
        ctk.CTkButton(
            bar_header, text="VOIR RAPPORT  \u203a", width=115, height=26,
            fg_color="transparent", hover_color=C["hover"],
            text_color=C["primary"], font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self._run_with_loading(self._show_students, "Chargement des étudiants...")
        ).pack(side="right")
        ctk.CTkLabel(
            bar_header, text="Comparaison des indicateurs cl\u00e9s",
            font=ctk.CTkFont(size=10), text_color=C["text_light"]
        ).pack(side="left", padx=10)

        bar_body = ctk.CTkFrame(bar_card, fg_color="transparent")
        bar_body.pack(fill="both", expand=True, padx=20, pady=(10, 14))

        stat_panel = ctk.CTkFrame(bar_body, fg_color="transparent", width=130)
        stat_panel.pack(side="left", fill="y", padx=(0, 14))
        stat_panel.pack_propagate(False)

        for s_label, s_value, s_color in [
            ("Revenus Actuels", self._format_usd(revenue), C["text_dark"]),
            ("Total \u00c9tudiants", f"{total:,}", C["text_dark"]),
            ("Taux \u00c9ligibilit\u00e9", f"{eligible_pct:.0f}%", C["success"]),
        ]:
            ctk.CTkLabel(
                stat_panel, text=s_label,
                font=ctk.CTkFont(size=9), text_color=C["text_light"]
            ).pack(anchor="w")
            ctk.CTkLabel(
                stat_panel, text=s_value,
                font=ctk.CTkFont(size=14, weight="bold"), text_color=s_color
            ).pack(anchor="w", pady=(0, 10))

        bar_canvas_bg = "#1e1e2e" if is_dark else "#FFFFFF"
        bar_canvas = tk.Canvas(bar_body, bg=bar_canvas_bg, highlightthickness=0)
        bar_canvas.pack(side="left", fill="both", expand=True)

        _bar_values = [total, eligible, non_eligible, access_granted, access_denied]
        _bar_labels = ["\u00c9tudiants", "\u00c9ligibles", "Non-\u00e9lig.", "Acc\u00e8s+", "Acc\u00e8s-"]
        _bar_colors = ["#3B82F6", "#10B981", "#EF4444", "#10B981", "#EF4444"]

        def _draw_bars(event=None):
            bar_canvas.delete("all")
            w = bar_canvas.winfo_width()
            h = bar_canvas.winfo_height()
            if w < 20 or h < 20:
                return
            grid_col = "#2a2a3e" if is_dark else "#E5E7EB"
            grid_text_col = "#9CA3AF" if is_dark else "#6B7280"
            label_col = "#9CA3AF" if is_dark else "#1e293b"
            pl, pr, pt, pb = 45, 10, 15, 45
            cw_c = w - pl - pr
            ch_c = h - pt - pb
            max_val = max(_bar_values) if any(v > 0 for v in _bar_values) else 1
            n = len(_bar_values)
            slot_w = cw_c / n
            bw = slot_w * 0.55
            for gi in range(5):
                gy = pt + ch_c * gi / 4
                bar_canvas.create_line(pl, gy, w - pr, gy, fill=grid_col, width=1)
                gv = max_val * (4 - gi) / 4
                bar_canvas.create_text(
                    pl - 4, gy, text=f"{int(gv):,}",
                    anchor="e", fill=grid_text_col, font=("Segoe UI", 7)
                )
            for bi, (v, lbl_b, bc) in enumerate(zip(_bar_values, _bar_labels, _bar_colors)):
                bx = pl + bi * slot_w + (slot_w - bw) / 2
                bh = (v / max_val) * ch_c
                by = pt + ch_c - bh
                bar_canvas.create_rectangle(bx, by, bx + bw, pt + ch_c, fill=bc, width=0)
                bar_canvas.create_text(
                    bx + bw / 2, pt + ch_c + 18, text=lbl_b,
                    fill=label_col, font=("Segoe UI", 9, "bold")
                )
            bar_canvas.create_line(pl, pt + ch_c, w - pr, pt + ch_c, fill=grid_col, width=1)

        bar_canvas.bind("<Configure>", _draw_bars)
        bar_card.after(80, _draw_bars)

        # Donut chart card
        donut_card = self._create_card(charts_row)
        donut_card.pack(side="top" if is_narrow else "left", fill="both", expand=True)
        donut_card.configure(height=300)
        donut_card.pack_propagate(False)

        donut_header = ctk.CTkFrame(donut_card, fg_color="transparent")
        donut_header.pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(
            donut_header, text="R\u00e9partition \u00c9tudiants",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=C["text_dark"]
        ).pack(side="left")
        ctk.CTkButton(
            donut_header, text="VOIR RAPPORT  \u203a", width=115, height=26,
            fg_color="transparent", hover_color=C["hover"],
            text_color=C["primary"], font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda: self._run_with_loading(self._show_students, "Chargement des étudiants...")
        ).pack(side="right")
        ctk.CTkLabel(
            donut_header, text="Sources acad\u00e9miques",
            font=ctk.CTkFont(size=10), text_color=C["text_light"]
        ).pack(side="left", padx=10)

        legend_row = ctk.CTkFrame(donut_card, fg_color="transparent")
        legend_row.pack(fill="x", padx=20, pady=(8, 0))
        _pending = max(0, total - eligible - non_eligible)
        _donut_segs = [
            (eligible, "\u00c9ligibles", "#10B981"),
            (non_eligible, "Non-\u00e9ligibles", "#EF4444"),
            (_pending, "En cours", "#F59E0B"),
            (access_denied, "Refus\u00e9s", "#EF4444"),
        ]
        _donut_segs = [(v, l, c) for v, l, c in _donut_segs if v > 0]
        for _v, _lbl, _col in _donut_segs:
            _leg = ctk.CTkFrame(legend_row, fg_color="transparent")
            _leg.pack(side="left", padx=(0, 10))
            _dot = ctk.CTkFrame(_leg, fg_color=_col, width=10, height=10, corner_radius=5)
            _dot.pack(side="left", padx=(0, 3))
            _dot.pack_propagate(False)
            ctk.CTkLabel(_leg, text=_lbl, font=ctk.CTkFont(size=9), text_color=C["text_light"]).pack(side="left")

        donut_canvas_bg = "#1e1e2e" if is_dark else "#FFFFFF"
        donut_canvas = tk.Canvas(donut_card, bg=donut_canvas_bg, highlightthickness=0)
        donut_canvas.pack(fill="both", expand=True, padx=20, pady=(8, 16))

        _d_values = [v for v, _, _ in _donut_segs]
        _d_colors = [c for _, _, c in _donut_segs]

        def _draw_donut(event=None):
            donut_canvas.delete("all")
            dw = donut_canvas.winfo_width()
            dh = donut_canvas.winfo_height()
            if dw < 20 or dh < 20:
                return
            hole_col = "#1e1e2e" if is_dark else "#FFFFFF"
            cx, cy = dw / 2, dh / 2
            outer_r = min(dw, dh) / 2 - 12
            inner_r = outer_r * 0.52
            total_d = sum(_d_values) or 1
            angle = -90.0
            for val_d, col_d in zip(_d_values, _d_colors):
                extent = (val_d / total_d) * 359.9
                donut_canvas.create_arc(
                    cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r,
                    start=angle, extent=extent, fill=col_d, outline="white", width=2
                )
                angle += extent
            donut_canvas.create_oval(
                cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                fill=hole_col, outline=""
            )
            donut_canvas.create_text(
                cx, cy - 8, text=f"{completion_pct:.0f}%",
                font=("Segoe UI", 16, "bold"),
                fill="#7C3AED" if not is_dark else "#A78BFA"
            )
            donut_canvas.create_text(
                cx, cy + 10, text="\u00c9ligibilit\u00e9",
                font=("Segoe UI", 9), fill="#9CA3AF"
            )

        donut_canvas.bind("<Configure>", _draw_donut)
        donut_card.after(80, _draw_donut)

        # Bottom info cards row
        bottom_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(0, 18))

        left_bot = self._create_card(bottom_row)
        left_bot.pack(side="left", fill="both", expand=True, padx=(0, 10))
        left_bot.configure(height=160)
        left_bot.pack_propagate(False)
        lb_inner = ctk.CTkFrame(left_bot, fg_color="transparent")
        lb_inner.pack(fill="both", expand=True, padx=18, pady=16)
        lb_left = ctk.CTkFrame(lb_inner, fg_color="transparent")
        lb_left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            lb_left, text="Journaux d'Acc\u00e8s",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C["text_dark"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            lb_left,
            text="Consultez l'historique et les logs\nd'acc\u00e8s aux examens en temps r\u00e9el.",
            font=ctk.CTkFont(size=10), text_color=C["text_light"], justify="left"
        ).pack(anchor="w", pady=(6, 10))
        ctk.CTkButton(
            lb_left, text="Voir les logs \u2192", width=115, height=28,
            fg_color=C["primary"], hover_color="#2563eb",
            text_color="#fff", font=ctk.CTkFont(size=10, weight="bold"),
            corner_radius=6, command=lambda: self._run_with_loading(self._show_access_logs, "Chargement des logs d'accès...")
        ).pack(anchor="w")
        ic_box = ctk.CTkFrame(
            lb_inner, fg_color="#EDE9FE" if not is_dark else "#2D1B6B",
            width=60, height=60, corner_radius=12
        )
        ic_box.pack(side="right", anchor="center")
        ic_box.pack_propagate(False)
        ctk.CTkLabel(ic_box, text="\U0001f6e1\ufe0f", font=ctk.CTkFont(size=26)).pack(expand=True)

        right_bot = self._create_card(bottom_row)
        right_bot.pack(side="left", fill="both", expand=True)
        right_bot.configure(height=160)
        right_bot.pack_propagate(False)
        rb_inner = ctk.CTkFrame(right_bot, fg_color="transparent")
        rb_inner.pack(fill="both", expand=True, padx=18, pady=16)
        rb_left = ctk.CTkFrame(rb_inner, fg_color="transparent")
        rb_left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            rb_left, text="R\u00e9sum\u00e9 Financier",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C["text_dark"]
        ).pack(anchor="w")
        ctk.CTkLabel(
            rb_left,
            text=f"Gestion de {total:,} dossiers\net {self._format_usd(revenue)} collect\u00e9s.",
            font=ctk.CTkFont(size=10), text_color=C["text_light"], justify="left"
        ).pack(anchor="w", pady=(6, 4))
        _storage_pct = min(eligible / max(total, 1), 1.0)
        _storage_bar = ctk.CTkProgressBar(
            rb_left, height=6, progress_color="#7C3AED", fg_color=C["border"], corner_radius=3
        )
        _storage_bar.set(_storage_pct)
        _storage_bar.pack(anchor="w", fill="x", pady=(4, 3))
        ctk.CTkLabel(
            rb_left, text=f"{eligible:,} \u00e9ligibles sur {total:,} total",
            font=ctk.CTkFont(size=9), text_color=C["text_light"]
        ).pack(anchor="w")
        ctk.CTkButton(
            rb_left, text="Voir finances \u2192", width=115, height=28,
            fg_color="transparent", hover_color=C["hover"],
            text_color=C["primary"], font=ctk.CTkFont(size=10, weight="bold"),
            corner_radius=6, command=lambda: self._run_with_loading(self._show_finance, "Chargement des finances...")
        ).pack(anchor="w", pady=(4, 0))
        ic_box2 = ctk.CTkFrame(
            rb_inner, fg_color="#CCFBF1" if not is_dark else "#003D35",
            width=60, height=60, corner_radius=12
        )
        ic_box2.pack(side="right", anchor="center")
        ic_box2.pack_propagate(False)
        ctk.CTkLabel(ic_box2, text="\U0001f5c4\ufe0f", font=ctk.CTkFont(size=26)).pack(expand=True)

        # ESP32 Status row
        row4 = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        row4.pack(fill="x", pady=(0, 18))
        esp_card = self._create_card(row4)
        esp_card.pack(fill="x", expand=True)
        ctk.CTkLabel(
            esp_card, text="\U0001f4e1 Communication ESP32 (Wi\u2011Fi)",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=C["text_dark"]
        ).pack(anchor="w", padx=20, pady=(18, 8))
        ctk.CTkLabel(
            esp_card,
            text=(
                "\u2022 L'ESP32 se connecte au Wi\u2011Fi et contacte le serveur U.O.R.\n"
                "\u2022 L'\u00e9tudiant envoie: Matricule + Code d'acc\u00e8s + Photo.\n"
                "\u2022 Le syst\u00e8me r\u00e9pond: ACC\u00c8S_OK / ERR_AUTH / ERR_FACE / ERR_FINANCE."
            ),
            font=ctk.CTkFont(size=11), text_color=C["text_light"],
            justify="left", wraplength=max(280, int(cw * 0.65)),
        ).pack(anchor="w", padx=20, pady=(0, 12))
        _status_row = ctk.CTkFrame(esp_card, fg_color=C["hover"], corner_radius=8)
        _status_row.pack(fill="x", padx=20, pady=(0, 20))
        self._esp32_status_label = ctk.CTkLabel(
            _status_row, text="Statut: En attente de connexion ESP32",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=C["warning"]
        )
        self._esp32_status_label.pack(anchor="w", padx=15, pady=10)
        self._start_esp32_status_polling(initial_delay_ms=1200)

    def _show_students(self):
        """Affiche la page Étudiants avec navigation hiérarchique Faculté > Département > Promotion"""
        self._set_main_scrollbar_visible(False)
        self.current_view = "students"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("students")
        self.title_label.configure(text=self._t("students_title", "Gestion des Étudiants"))
        self.subtitle_label.configure(text=self._t("students_subtitle", "Gestion et suivi des étudiants"))
        
        # Variables de navigation (préserver si déjà définies)
        if not hasattr(self, "nav_state") or not isinstance(self.nav_state, dict):
            self.nav_state = {
                'level': 'faculty', # faculty, department, promotion
                'selected_faculty': None, 'selected_department': None, 'selected_promotion': None
            }
        if not hasattr(self, "selected_academic_year_id"):
            self.selected_academic_year_id = None
        
        # === HEADER ===

        # Récupérer toutes les données des étudiants (cache court pour accélérer la navigation)
        self.students_full_data_all = self._get_cached_data(
            "students_all_with_finance",
            self.student_service.get_all_students_with_finance,
            ttl_seconds=45.0,
        )

        # Si l'année sélectionnée n'a aucun étudiant, réinitialiser le filtre
        if self.selected_academic_year_id:
            has_students_for_year = any(
                s.get("academic_year_id") == self.selected_academic_year_id
                for s in self.students_full_data_all
            )
            if not has_students_for_year:
                self.selected_academic_year_id = None

        # Déterminer le layout compact basé sur la largeur RÉELLE de la zone contenu
        try:
            self.update_idletasks()
            content_width = self.content_frame.winfo_width() if self.content_frame else 0
            window_width = self.winfo_toplevel().winfo_width()
            if content_width <= 1:
                content_width = window_width
        except Exception:
            content_width = self.winfo_width() or self.screen_width

        # Seuil légèrement plus large pour tenir compte de la sidebar + paddings
        is_compact_layout = content_width < 1250
        self._students_compact_layout = is_compact_layout

        # === NAVIGATION ANNÉE ACADÉMIQUE ===
        # Adapter la hauteur pour petit écran
        is_tiny_students = content_width < 900
        filter_height = 64 if is_tiny_students else (36 if is_compact_layout else 48)
        filter_pady = (0, 4) if is_compact_layout else (0, 6)
        filter_padx = (10, 8) if is_compact_layout else (15, 10)
        filter_font_size = 10 if is_compact_layout else 12
        
        year_filter_frame = ctk.CTkFrame(self.content_frame, fg_color=self.colors["hover"], corner_radius=8, height=filter_height)
        year_filter_frame.pack(fill="x", pady=filter_pady)
        year_filter_frame.pack_propagate(False)

        year_label = ctk.CTkLabel(
            year_filter_frame, text="📅 Année académique:", font=ctk.CTkFont(size=filter_font_size, weight="bold"), text_color=self.colors["text_dark"]
        )
        if is_tiny_students:
            year_label.pack(anchor="w", padx=filter_padx[0], pady=(6, 0))
        else:
            year_label.pack(side="left", padx=filter_padx, pady=4)

        academic_years = self._get_cached_data(
            "academic_years",
            self.academic_year_service.get_years,
            ttl_seconds=60.0,
        )
        year_names = [y.get("year_name") for y in academic_years if y.get("year_name")]
        self.academic_year_map = {y.get("year_name"): y.get("academic_year_id") for y in academic_years}

        combo_width = 160 if is_tiny_students else (180 if is_compact_layout else 220)
        combo_height = 28 if is_compact_layout else 30
        year_filter = ctk.CTkComboBox(
            year_filter_frame, values=["Toutes Années"] + year_names, width=combo_width, height=combo_height
        )
        if self.selected_academic_year_id:
            current_name = next(
                (name for name, yid in self.academic_year_map.items() if yid == self.selected_academic_year_id), None
            )
            year_filter.set(current_name or "Toutes Années")
        else:
            year_filter.set("Toutes Années")
        if is_tiny_students:
            year_filter.pack(anchor="w", padx=filter_padx[0], pady=(4, 6))
        else:
            year_filter.pack(side="left", padx=(0, 10), pady=4)

        # === STATS ET BOUTON RESPONSIVE ===
        actions_row = None
        if is_compact_layout:
            # Sur petit écran: créer une disposition sur 2 lignes
            actions_row = ctk.CTkFrame(self.content_frame, fg_color=self.colors["main_bg"])
            actions_row.pack(fill="x", pady=(0, 6))
            
            # Ligne 1: Stats
            stats_line = ctk.CTkFrame(actions_row, fg_color=self.colors["main_bg"])
            stats_line.pack(fill="x", padx=(15, 10), pady=(0, 4))
            
            self.students_stats_label = ctk.CTkLabel(
                stats_line, text="", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
            )
            self.students_stats_label.pack(side="left", padx=(0, 0), pady=2)
            
            # Ligne 2: Bouton
            add_btn_parent = ctk.CTkFrame(actions_row, fg_color=self.colors["main_bg"])
            add_btn_parent.pack(fill="x", padx=(15, 10), pady=(0, 0))
        else:
            ctk.CTkFrame(year_filter_frame).pack(side="left", fill="x", expand=True)

            # Sur grand écran: disposition classique inline
            self.students_stats_label = ctk.CTkLabel(
                year_filter_frame, text="", font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]
            )
            self.students_stats_label.pack(side="left", padx=(10, 10), pady=4)
            add_btn_parent = year_filter_frame

        btn_height = 28 if is_compact_layout else 32
        btn_text = "➕ Ajouter" if is_compact_layout else f"➕ {self._t('add_student', 'Ajouter étudiant')}"
        add_btn = ctk.CTkButton(
            add_btn_parent, text=btn_text, fg_color=self.colors["primary"], hover_color=self.colors["info"], text_color=self.colors["text_white"], height=btn_height, corner_radius=8, command=self._open_add_student_dialog
        )
        add_btn.pack(side="right", padx=(0, 10) if is_compact_layout else (0, 10), pady=4)

        has_year_data = any(s.get("academic_year_id") for s in self.students_full_data_all)
        if not has_year_data or not year_names:
            year_filter.configure(state="disabled")
        
        # === BREADCRUMB (Fil d'Ariane) ===
        breadcrumb_pady = (0, 2) if is_compact_layout else (0, 4)
        self.breadcrumb_frame = ctk.CTkFrame(self.content_frame)
        self.breadcrumb_frame.pack(fill="x", pady=breadcrumb_pady)
        
        # === CONTAINER PRINCIPAL ===
        self.students_main_card = self._create_card(self.content_frame)
        self.students_main_card.pack(fill="both", expand=True)

        # Afficher la vue initiale (Facultés)
        self._update_students_stats()
        self._render_students_navigation()

        year_filter.configure(command=lambda _value: self._on_students_year_change(year_filter.get()))
    
    def _render_students_navigation(self):
        """Rend la navigation hiérarchique selon le niveau actuel"""
        self.students_full_data = self._get_students_filtered_by_year()
        # Nettoyer le contenu
        for widget in self.students_main_card.winfo_children():
            widget.destroy()
        
        # Mettre à jour le breadcrumb
        self._update_breadcrumb()
        
        # Afficher le niveau approprié
        if self.nav_state['level'] == 'faculty':
            self._show_faculties_view()
        elif self.nav_state['level'] == 'department':
            self._show_departments_view()
        elif self.nav_state['level'] == 'promotion':
            self._show_promotions_view()

    def _get_students_filtered_by_year(self):
        """Retourne les étudiants filtrés par année académique sélectionnée"""
        data = self.students_full_data_all or []
        if not self.selected_academic_year_id:
            return data
        return [s for s in data if s.get("academic_year_id") == self.selected_academic_year_id]

    def _update_students_stats(self):
        """Met à jour les stats rapides selon l'année sélectionnée"""
        data = self._get_students_filtered_by_year()
        total = len(data)
        eligible = sum(1 for s in data if s.get("is_eligible"))
        non_eligible = total - eligible
        
        if self.students_stats_label:
            # Format responsive aligné sur le layout réel de la page
            if getattr(self, "_students_compact_layout", False):
                # Format court pour petit écran
                stats_text = f"📊 {total} | ✅ {eligible} | ❌ {non_eligible}"
            else:
                # Format complet pour grand écran
                stats_text = f"Total: {total} | ✅ Éligibles: {eligible} | ❌ Non-éligibles: {non_eligible}"
            
            self.students_stats_label.configure(text=stats_text)

    def _on_students_year_change(self, selected_value: str):
        """Gère le changement d'année académique pour la vue étudiants"""
        if selected_value == "Toutes Années":
            self.selected_academic_year_id = None
        else:
            self.selected_academic_year_id = self.academic_year_map.get(selected_value)

        self.nav_state['level'] = 'faculty'
        self.nav_state['selected_faculty'] = None
        self.nav_state['selected_department'] = None
        self.nav_state['selected_promotion'] = None

        self._refresh_students_navigation_with_loading("Filtrage par année académique...")
    
    def _update_breadcrumb(self):
        """Met à jour le fil d'Ariane"""
        for widget in self.breadcrumb_frame.winfo_children():
            widget.destroy()
        
        # Icône maison pour retour aux facultés
        home_btn = ctk.CTkButton(
            self.breadcrumb_frame, text="🏛️ Facultés", fg_color=self.colors["primary"] if self.nav_state['level'] == 'faculty' else "transparent", hover_color=self.colors["hover"], text_color=self.colors["text_white"] if self.nav_state['level'] == 'faculty' else self.colors["primary"], height=28, corner_radius=6, command=lambda: self._navigate_to('faculty')
        )
        home_btn.pack(side="left", padx=(0, 5))
        
        if self.nav_state['selected_faculty']:
            # Séparateur
            ctk.CTkLabel(
                self.breadcrumb_frame, text="›", font=ctk.CTkFont(size=16), text_color=self.colors["text_light"]
            ).pack(side="left", padx=5)
            
            # Bouton faculté
            faculty_btn = ctk.CTkButton(
                self.breadcrumb_frame, text=f"📚 {self.nav_state['selected_faculty']['name']}", fg_color=self.colors["primary"] if self.nav_state['level'] == 'department' else "transparent", hover_color=self.colors["hover"], text_color=self.colors["text_white"] if self.nav_state['level'] == 'department' else self.colors["primary"], height=28, corner_radius=6, command=lambda: self._navigate_to('department')
            )
            faculty_btn.pack(side="left", padx=(0, 5))
        
        if self.nav_state['selected_department']:
            # Séparateur
            ctk.CTkLabel(
                self.breadcrumb_frame, text="›", font=ctk.CTkFont(size=16), text_color=self.colors["text_light"]
            ).pack(side="left", padx=5)
            
            # Bouton département
            dept_btn = ctk.CTkButton(
                self.breadcrumb_frame, text=f"📂 {self.nav_state['selected_department']['name']}", fg_color=self.colors["primary"], hover_color=self.colors["hover"], text_color=self.colors["text_white"], height=28, corner_radius=6, state="disabled"
            )
            dept_btn.pack(side="left")
    
    def _navigate_to(self, level):
        """Navigation entre les niveaux"""
        if level == 'faculty':
            self.nav_state['level'] = 'faculty'
            self.nav_state['selected_faculty'] = None
            self.nav_state['selected_department'] = None
            self.nav_state['selected_promotion'] = None
        elif level == 'department':
            self.nav_state['level'] = 'department'
            self.nav_state['selected_department'] = None
            self.nav_state['selected_promotion'] = None
        
        self._refresh_students_navigation_with_loading("Chargement de la navigation...")
    
    def _show_faculties_view(self):
        """Affiche les cartes des facultés"""
        is_compact = self._students_compact_layout if hasattr(self, '_students_compact_layout') else False
        
        # Titre - réduit sur petits écrans
        title_padx = 15 if is_compact else 25
        title_pady = (4, 4) if is_compact else (6, 6)
        title_font = 16 if is_compact else 20
        
        title_frame = ctk.CTkFrame(self.students_main_card)
        title_frame.pack(fill="x", padx=title_padx, pady=title_pady)
        
        ctk.CTkLabel(
            title_frame, text="🏛️ Sélectionnez une Faculté", font=ctk.CTkFont(size=title_font, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w")
        
        # Toujours afficher le sous-titre pour clarifier l'action
        subtitle_font = 10 if is_compact else 12
        ctk.CTkLabel(
            title_frame, text="Cliquez sur une faculté pour voir ses départements", font=ctk.CTkFont(size=subtitle_font), text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(3 if is_compact else 5, 0))
        
        # Scroll frame pour les cartes - plus d'espace sur petits écrans
        scroll_padx = 15 if is_compact else 25
        scroll_pady = (0, 10) if is_compact else (0, 20)
        scroll_frame = ctk.CTkScrollableFrame(self.students_main_card)
        scroll_frame.pack(fill="both", expand=True, padx=scroll_padx, pady=scroll_pady)
        
        # Regrouper les étudiants par faculté
        faculties_data = {}
        for student in self.students_full_data:
            faculty_id = student.get('faculty_id')
            faculty_name = student.get('faculty_name')
            faculty_code = student.get('faculty_code')
            
            if not faculty_id or not faculty_name:
                continue
            
            if faculty_id not in faculties_data:
                faculties_data[faculty_id] = {
                    'id': faculty_id, 'name': faculty_name, 'code': faculty_code or faculty_name[:3].upper(), 'students': []
                }
            faculties_data[faculty_id]['students'].append(student)
        
        # Check si pas de facultés
        if not faculties_data:
            ctk.CTkLabel(
                scroll_frame, text="Aucune faculté trouvée", font=ctk.CTkFont(size=14), text_color=self.colors["text_light"]
            ).pack(pady=50)
            return
        
        # Créer les cartes - plus compactes sur petits écrans
        card_pady = 5 if is_compact else 8
        card_padx = 12 if is_compact else 20
        card_pady_internal = 10 if is_compact else 15
        icon_size = 24 if is_compact else 32
        icon_padx = 10 if is_compact else 15
        name_font = 14 if is_compact else 16
        
        for idx, (faculty_id, faculty_info) in enumerate(sorted(faculties_data.items(), key=lambda x: x[1]['name'])):
            card = ctk.CTkFrame(
                scroll_frame, fg_color=self.colors["card_bg"], corner_radius=12, cursor="hand2", border_width=1, border_color=self.colors["border"]
            )
            card.pack(fill="x", pady=card_pady)
            
            # Bind click event
            card.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            # Contenu de la carte
            content_frame = ctk.CTkFrame(card, fg_color=self.colors["card_bg"])
            content_frame.pack(fill="both", expand=True, padx=card_padx, pady=card_pady_internal)
            content_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            # Header
            header_frame = ctk.CTkFrame(content_frame, fg_color=self.colors["card_bg"])
            header_frame.pack(fill="x")
            header_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            icon_label = ctk.CTkLabel(
                header_frame, text="🏛️", font=ctk.CTkFont(size=icon_size), fg_color=self.colors["card_bg"]
            )
            icon_label.pack(side="left", padx=(0, icon_padx))
            icon_label.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            info_frame = ctk.CTkFrame(header_frame, fg_color=self.colors["card_bg"])
            info_frame.pack(side="left", fill="x", expand=True)
            info_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            name_label = ctk.CTkLabel(
                info_frame, text=faculty_info['name'], font=ctk.CTkFont(size=name_font, weight="bold"), text_color=self.colors["text_dark"], anchor="w", fg_color=self.colors["card_bg"]
            )
            name_label.pack(anchor="w")
            name_label.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            code_label = ctk.CTkLabel(
                info_frame, text=f"Code: {faculty_info['code']}", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"], anchor="w", fg_color=self.colors["card_bg"]
            )
            code_label.pack(anchor="w")
            code_label.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            # Stats
            students_count = len(faculty_info['students'])
            eligible_count = sum(1 for s in faculty_info['students'] if s.get('is_eligible'))
            
            stats_frame = ctk.CTkFrame(content_frame)
            stats_frame.pack(fill="x", pady=(10, 0))
            stats_frame.bind("<Button-1>", lambda e, f=faculty_info: self._select_faculty(f))
            
            self._create_stat_badge(stats_frame, "👥", f"{students_count} étudiants", self.colors["info"]).pack(side="left", padx=(0, 10))
            self._create_stat_badge(stats_frame, "✅", f"{eligible_count} éligibles", self.colors["success"]).pack(side="left")
    
    def _show_departments_view(self):
        """Affiche les départements de la faculté sélectionnée"""
        if not self.nav_state['selected_faculty']:
            return
        
        is_compact = self._students_compact_layout if hasattr(self, '_students_compact_layout') else False
        
        # Titre
        title_frame = ctk.CTkFrame(self.students_main_card)
        title_padx = 15 if is_compact else 25
        title_pady = (10, 8) if is_compact else (20, 15)
        title_frame.pack(fill="x", padx=title_padx, pady=title_pady)
        
        title_font = 16 if is_compact else 20
        ctk.CTkLabel(
            title_frame, text=f"📂 Départements de {self.nav_state['selected_faculty']['name']}", font=ctk.CTkFont(size=title_font, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w")
        
        # Toujours afficher le sous-titre
        subtitle_font = 10 if is_compact else 12
        ctk.CTkLabel(
            title_frame, text="Cliquez sur un département pour voir ses promotions", font=ctk.CTkFont(size=subtitle_font), text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(3 if is_compact else 5, 0))
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(self.students_main_card)
        scroll_padx = 15 if is_compact else 25
        scroll_pady = (0, 10) if is_compact else (0, 20)
        scroll_frame.pack(fill="both", expand=True, padx=scroll_padx, pady=scroll_pady)
        
        # Regrouper par département
        departments_data = {}
        faculty_id = self.nav_state['selected_faculty']['id']
        
        for student in self.students_full_data:
            if student.get('faculty_id') != faculty_id:
                continue
            
            dept_id = student.get('department_id')
            dept_name = student.get('department_name')
            dept_code = student.get('department_code')
            
            if not dept_id or not dept_name:
                continue
            
            if dept_id not in departments_data:
                departments_data[dept_id] = {
                    'id': dept_id, 'name': dept_name, 'code': dept_code or dept_name[:3].upper(), 'students': []
                }
            departments_data[dept_id]['students'].append(student)
        
        if not departments_data:
            ctk.CTkLabel(
                scroll_frame, text="Aucun département trouvé pour cette faculté", font=ctk.CTkFont(size=14), text_color=self.colors["text_light"]
            ).pack(pady=50)
            return
        
        # Créer les cartes
        card_pady = 5 if is_compact else 8
        content_padx = 12 if is_compact else 20
        content_pady = 10 if is_compact else 15
        icon_size = 24 if is_compact else 32
        name_font = 14 if is_compact else 16
        stats_pady = (8, 0) if is_compact else (10, 0)
        
        for dept_id, dept_info in sorted(departments_data.items(), key=lambda x: x[1]['name']):
            card = ctk.CTkFrame(
                scroll_frame, fg_color=self.colors["card_bg"], corner_radius=12, cursor="hand2", border_width=1, border_color=self.colors["border"]
            )
            card.pack(fill="x", pady=card_pady)
            
            card.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            # Contenu
            content_frame = ctk.CTkFrame(card)
            content_frame.pack(fill="both", expand=True, padx=content_padx, pady=content_pady)
            content_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            # Header
            header_frame = ctk.CTkFrame(content_frame)
            header_frame.pack(fill="x")
            header_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            icon_label = ctk.CTkLabel(
                header_frame, text="📂", font=ctk.CTkFont(size=icon_size)
            )
            icon_label.pack(side="left", padx=(0, 15))
            icon_label.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            info_frame = ctk.CTkFrame(header_frame)
            info_frame.pack(side="left", fill="x", expand=True)
            info_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            name_label = ctk.CTkLabel(
                info_frame, text=dept_info['name'], font=ctk.CTkFont(size=name_font, weight="bold"), text_color=self.colors["text_dark"], anchor="w"
            )
            name_label.pack(anchor="w")
            name_label.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            code_label = ctk.CTkLabel(
                info_frame, text=f"Code: {dept_info['code']}", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"], anchor="w"
            )
            code_label.pack(anchor="w")
            code_label.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            # Stats
            students_count = len(dept_info['students'])
            eligible_count = sum(1 for s in dept_info['students'] if s.get('is_eligible'))
            
            stats_frame = ctk.CTkFrame(content_frame)
            stats_frame.pack(fill="x", pady=stats_pady)
            stats_frame.bind("<Button-1>", lambda e, d=dept_info: self._select_department(d))
            
            self._create_stat_badge(stats_frame, "👥", f"{students_count} étudiants", self.colors["info"]).pack(side="left", padx=(0, 10))
            self._create_stat_badge(stats_frame, "✅", f"{eligible_count} éligibles", self.colors["success"]).pack(side="left")
    
    def _show_promotions_view(self):
        """Affiche les promotions et étudiants du département sélectionné"""
        if not self.nav_state['selected_department']:
            return
        
        # Titre avec barre de recherche - compact sur petits écrans
        is_compact = self._students_compact_layout if hasattr(self, '_students_compact_layout') else False
        title_padx = 15 if is_compact else 25
        title_pady = (10, 8) if is_compact else (20, 15)
        title_font = 16 if is_compact else 20
        subtitle_font = 10 if is_compact else 12
        
        title_frame = ctk.CTkFrame(self.students_main_card)
        title_frame.pack(fill="x", padx=title_padx, pady=title_pady)
        
        left_frame = ctk.CTkFrame(title_frame)
        left_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            left_frame, text=f"🎓 Promotions - {self.nav_state['selected_department']['name']}", font=ctk.CTkFont(size=title_font, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w")
        
        # Toujours afficher le sous-titre, même sur petits écrans
        ctk.CTkLabel(
            left_frame, text="Liste des étudiants par promotion", font=ctk.CTkFont(size=subtitle_font), text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(3 if is_compact else 5, 0))
        
        # Barre de recherche - plus compacte sur petits écrans
        search_height = 36 if is_compact else 44
        search_padx = 15 if is_compact else 25
        search_pady = (0, 4) if is_compact else (0, 6)
        
        search_frame = ctk.CTkFrame(self.students_main_card, fg_color=self.colors["hover"], corner_radius=8, height=search_height)
        search_frame.pack(fill="x", padx=search_padx, pady=search_pady)
        search_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            search_frame, text="🔍", font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=(15, 5), pady=8)
        
        search_placeholder = "Rechercher..." if is_compact else "Rechercher un étudiant (nom, email...)..."
        search_entry_height = 28 if is_compact else 30
        search_entry = ctk.CTkEntry(
            search_frame, placeholder_text=search_placeholder, height=search_entry_height, border_width=0)
        search_entry.pack(side="left", fill="x", expand=True, padx=(5, 10 if is_compact else 15), pady=4)
        
        # Scroll frame - plus d'espace disponible sur petits écrans
        scroll_padx = 15 if is_compact else 25
        scroll_pady = (0, 6) if is_compact else (0, 10)
        
        scroll_frame = ctk.CTkScrollableFrame(self.students_main_card)
        scroll_frame.pack(fill="both", expand=True, padx=scroll_padx, pady=scroll_pady)
        
        # Regrouper par promotion
        promotions_data = {}
        dept_id = self.nav_state['selected_department']['id']
        content_parent = getattr(scroll_frame, "_scrollable_frame", scroll_frame)
        
        for student in self.students_full_data:
            if student.get('department_id') != dept_id:
                continue
            
            promo_id = student.get('promotion_id')
            promo_name = student.get('promotion_name')
            promo_year = student.get('promotion_year')
            promo_fee = student.get('promotion_fee', 0)
            promo_threshold = student.get('promotion_threshold', 0)
            
            if not promo_id or not promo_name:
                continue
            
            if promo_id not in promotions_data:
                promotions_data[promo_id] = {
                    'id': promo_id, 'name': promo_name, 'year': promo_year, 'fee': promo_fee, 'threshold': promo_threshold, 'students': []
                }
            promotions_data[promo_id]['students'].append(student)
        
        if not promotions_data:
            ctk.CTkLabel(
                content_parent, text="Aucune promotion trouvée pour ce département", font=ctk.CTkFont(size=14), text_color=self.colors["text_light"]
            ).pack(pady=50)
            return
        
        def render_students(filter_text=""):
            self._cancel_scheduled_renders("students_")
            for widget in content_parent.winfo_children():
                widget.destroy()
            
            query = filter_text.lower().strip()
            
            # Pour chaque promotion
            for promo_id, promo_info in sorted(promotions_data.items(), key=lambda x: x[1]['name']):
                # Filtrer les étudiants
                filtered_students = []
                for student in promo_info['students']:
                    fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
                    email = student.get('email', '')
                    student_number = student.get('student_number', '')
                    
                    haystack = f"{fullname} {email} {student_number}".lower()
                    if query and query not in haystack:
                        continue
                    filtered_students.append(student)
                
                if not filtered_students:
                    continue
                
                # En-tête de promotion - meilleure lisibilité
                promo_pady_top = 0 if promo_id == list(promotions_data.keys())[0] else (8 if is_compact else 15)
                promo_pady_bottom = 5 if is_compact else 8
                promo_padx = 10 if is_compact else 15
                
                # Utiliser un fond plus foncé pour meilleur contraste
                promo_bg = self.colors["text_dark"] if self.theme.current_theme == "light" else self.colors["primary"]
                promo_header = ctk.CTkFrame(content_parent, fg_color=promo_bg, corner_radius=8)
                promo_header.pack(fill="x", pady=(promo_pady_top, promo_pady_bottom), padx=promo_padx)
                
                promo_header_padx = 10 if is_compact else 15
                promo_header_pady = 6 if is_compact else 10
                promo_header_content = ctk.CTkFrame(promo_header, fg_color="transparent")
                promo_header_content.pack(fill="x", padx=promo_header_padx, pady=promo_header_pady)
                
                # Tailles de police augmentées pour meilleure lisibilité
                promo_title_font = 13 if is_compact else 14
                ctk.CTkLabel(
                    promo_header_content, text=f"🎓 {promo_info['name']} ({promo_info['year']})", font=ctk.CTkFont(size=promo_title_font, weight="bold"), text_color=self.colors["text_white"]
                ).pack(side="left")
                
                # Stats promotion - lisibles même sur petits écrans
                stats_font = 11 if is_compact else 11
                stats_text = f"👥 {len(filtered_students)} | 💰 ${promo_info['fee']:.0f} | Seuil: ${promo_info['threshold']:.0f}" if is_compact else f"👥 {len(filtered_students)} étudiant{'s' if len(filtered_students) > 1 else ''} | 💰 Frais: ${promo_info['fee']:.2f} | Seuil: ${promo_info['threshold']:.2f}"
                stats_label = ctk.CTkLabel(
                    promo_header_content, text=stats_text, font=ctk.CTkFont(size=stats_font), text_color=self.colors["text_white"]
                )
                stats_label.pack(side="right")
                
                # Tableau des étudiants - plus d'espace sur petits écrans
                table_pady = (0, 6) if is_compact else (0, 10)
                table_padx = 10 if is_compact else 15
                table_frame = ctk.CTkFrame(content_parent, fg_color=self.colors["card_bg"], corner_radius=8)
                table_frame.pack(fill="x", expand=False, pady=table_pady, padx=table_padx)
                
                # Header du tableau
                headers = ["Photo", "Nom Complet", "Email", "💰 Payé", "Éligibilité", "Solde ($)", "Actions"]
                layout = self._get_table_layout("students_promo", len(headers))
                column_weights = layout["weights"]
                header_anchors = layout["anchors"]
                min_widths = layout["min_widths"]
                
                header_pady = 6 if is_compact else 8
                self._create_table_header(table_frame, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=header_pady)

                # Conteneur scrollable des lignes - plus de hauteur sur petits écrans
                table_height = self._scaled(320) if is_compact else self._scaled(260)
                rows_scroll = ctk.CTkScrollableFrame(
                    table_frame, height=table_height, scrollbar_button_color=self.colors["border"], scrollbar_button_hover_color=self.colors["text_light"]
                )
                bottom_pady = 4 if is_compact else 8
                rows_scroll.pack(fill="x", padx=0, pady=(0, bottom_pady))

                self._set_scrollbar_visible(rows_scroll, False)

                rows_container = getattr(rows_scroll, "_scrollable_frame", rows_scroll)

                # Lignes des étudiants rendues par lots pour éviter les freezes
                self._render_in_batches(
                    render_key=f"students_promo_{promo_id}",
                    items=filtered_students,
                    render_item=lambda student_item, row_index, target=rows_container, weights=column_weights: self._render_student_row_in_promotion(
                        target, student_item, weights, row_index=row_index
                    ),
                    batch_size=14,
                    delay_ms=1,
                    on_complete=lambda scroll=rows_scroll, table=table_frame: [
                        scroll.update_idletasks(),
                        table.update_idletasks(),
                    ],
                )
        
        search_state = {"job": None}

        def schedule_students_render(_event=None):
            if search_state["job"]:
                self.after_cancel(search_state["job"])
            search_state["job"] = self.after(180, lambda: render_students(search_entry.get()))

        # Rendu initial
        render_students()
        search_entry.bind("<KeyRelease>", schedule_students_render)
    
    def _render_student_row_in_promotion(self, parent, student, column_weights, row_index: int = 0):
        """Rend une ligne étudiant dans la vue promotion"""
        row = ctk.CTkFrame(parent, fg_color=self.colors["hover"], corner_radius=0)
        row.grid(row=row_index, column=0, sticky="ew", pady=1, padx=0)
        parent.grid_columnconfigure(0, weight=1)
        layout = self._get_table_layout("students_promo")
        min_widths = layout["min_widths"]
        self._configure_table_columns(row, column_weights, min_widths=min_widths)
        
        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        email = student.get('email') or "-"
        photo_path = student.get('passport_photo_path')
        photo_blob = student.get('passport_photo_blob')
        amount_paid = Decimal(str(student.get('amount_paid') or 0))
        
        promotion_threshold = Decimal(str(student.get('promotion_threshold') or 0))
        promotion_fee = Decimal(str(student.get('promotion_fee') or 0))
        
        is_eligible = bool(student.get('is_eligible')) or (promotion_threshold > 0 and amount_paid >= promotion_threshold)
        remaining_amount = max(Decimal("0"), promotion_fee - amount_paid)

        if is_eligible:
            eligibility_text = "✅"
            eligibility_color = self.colors["success"]
        elif amount_paid > 0:
            eligibility_text = "🟡"
            eligibility_color = self.colors["warning"]
        else:
            eligibility_text = "❌"
            eligibility_color = self.colors["danger"]
        
        # Photo
        self._render_photo_cell(row, 0, photo_path=photo_path, photo_blob=photo_blob, size=(35, 45))

        row_values = [
            fullname, email, f"${amount_paid:.2f}", eligibility_text, f"${remaining_amount:.2f}", ]
        row_colors = [
            self.colors["text_dark"], self.colors["text_light"], self.colors["success"] if amount_paid >= promotion_fee else self.colors["warning"], eligibility_color, self.colors["text_light"], ]
        row_weights = ["normal", "normal", "bold", "bold", "normal"]
        row_anchors = layout["anchors"][1:6]
        row_min_widths = min_widths[1:6] if min_widths else None

        self._populate_table_row_with_offset(
            row, row_values, column_weights, start_col=1, text_colors=row_colors, font_weights=row_weights, anchors=row_anchors, min_widths=row_min_widths, padx=10, pady=6
        )
        
        # Actions
        action_frame = ctk.CTkFrame(row)
        action_frame.grid(row=0, column=6, sticky="ew", padx=10, pady=6)

        def _bind_tooltip(btn, tip_text):
            tip = Tooltip(btn, tip_text)
            btn.bind("<Enter>", lambda e: tip.show_tooltip(e))
            btn.bind("<Leave>", lambda e: tip.hide_tooltip())

        edit_btn = ctk.CTkButton(
            action_frame, text="✏️", width=30, height=24, fg_color=self.colors["info"], hover_color="#0891b2", command=lambda s=student: self._open_edit_student_dialog(s)
        )
        edit_btn.pack(side="left", padx=2)
        _bind_tooltip(edit_btn, self._t("edit_student_tooltip", "Modifier l'étudiant"))

        pay_btn = ctk.CTkButton(
            action_frame, text="💰", width=30, height=24, fg_color=self.colors["primary"], hover_color="#2563eb", command=lambda s=student: self._open_payment_dialog(s)
        )
        pay_btn.pack(side="left", padx=2)
        _bind_tooltip(pay_btn, self._t("payment_tooltip", "Enregistrer un paiement"))

        hist_btn = ctk.CTkButton(
            action_frame, text="📜", width=30, height=24, fg_color=self.colors["warning"], hover_color="#f59e0b", command=lambda s=student: self._open_payment_history_dialog(s)
        )
        hist_btn.pack(side="left", padx=2)
        _bind_tooltip(hist_btn, self._t("payment_history_tooltip", "Historique des paiements"))
    
    def _create_stat_badge(self, parent, icon, text, color):
        """Crée un badge de statistique"""
        badge = ctk.CTkFrame(parent, fg_color=color, corner_radius=6)
        badge.bind("<Button-1>", lambda e: None)  # Propagate click to parent
        
        content = ctk.CTkFrame(badge, fg_color="transparent")
        content.pack(padx=8, pady=4)
        content.bind("<Button-1>", lambda e: None)
        
        ctk.CTkLabel(
            content, text=f"{icon} {text}", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_white"]
        ).pack()
        
        return badge
    
    def _select_faculty(self, faculty_info):
        """Sélectionne une faculté et passe aux départements"""
        self.nav_state['level'] = 'department'
        self.nav_state['selected_faculty'] = faculty_info
        self._refresh_students_navigation_with_loading("Chargement des départements...")
    
    def _select_department(self, dept_info):
        """Sélectionne un département et passe aux promotions"""
        self.nav_state['level'] = 'promotion'
        self.nav_state['selected_department'] = dept_info
        self._refresh_students_navigation_with_loading("Chargement des promotions...")
    

    def _open_add_student_dialog(self):
        """Ouvre la fenêtre d'inscription d'un nouvel étudiant (élégant, centré, responsive)"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Inscription Étudiant")
        
        # Compact sizing - smaller initial size
        dialog_width = 480
        dialog_height = 520
        
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        dialog.resizable(True, True)
        
        # Background moderne
        dialog.configure(fg_color=self.colors["main_bg"])
        
        self._center_and_show_dialog(dialog)

        # === HEADER ÉLÉGANT (COMPACT) ===
        header = ctk.CTkFrame(dialog, fg_color=self.colors["primary"], corner_radius=0, height=55)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(
            header_content, text="➕ Nouvel Étudiant", font=self._font(18, "bold"), text_color=self.colors["text_white"]
        ).pack(side="left")

        ctk.CTkLabel(
            header_content, text="Remplissez tous les champs requis", font=self._font(10), text_color="#e5f0ff"
        ).pack(side="left", padx=(15, 0))

        # === SCROLL FORM CONTAINER ===
        form_outer = ctk.CTkFrame(dialog)
        form_outer.pack(fill="both", expand=True, padx=15, pady=12)

        form_scroll = ctk.CTkScrollableFrame(
            form_outer, scrollbar_button_color=self.colors["border"], scrollbar_button_hover_color=self.colors["text_light"], corner_radius=8
        )
        form_scroll.pack(fill="both", expand=True)
        form_scroll.grid_columnconfigure(0, weight=1)

        # === SECTION: IDENTITÉ ===
        section_identity = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_identity.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            section_identity, text="👤 Informations personnelles", font=self._font(12, "bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=10, pady=(8, 6))

        identity_frame = ctk.CTkFrame(section_identity)
        identity_frame.pack(fill="x", padx=10, pady=(0, 8))
        identity_frame.grid_columnconfigure(0, weight=1)
        identity_frame.grid_columnconfigure(1, weight=1)

        def add_labeled_entry(parent, label_text, placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(parent, text=label_text, font=self._font(10), text_color=self.colors["text_light"])
            label.grid(row=row, column=col, sticky="w", padx=4, pady=(5, 1), columnspan=col_span)
            entry = ctk.CTkEntry(
                parent, placeholder_text=placeholder, fg_color=self.colors["main_bg"], border_color=self.colors["border"], border_width=1, corner_radius=6, height=28
            )
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=4, pady=(0, 4))
            return entry

        student_number_entry = add_labeled_entry(identity_frame, "Matricule étudiant *", "STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry(identity_frame, "Prénom *", "Jean", row=0, col=1)
        lastname_entry = add_labeled_entry(identity_frame, "Nom *", "Dupont", row=2, col=0)
        email_entry = add_labeled_entry(identity_frame, "Email *", "jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry(identity_frame, "Téléphone WhatsApp *", "+243123456789", row=4, col=0, col_span=2)

        # === SECTION: ACADÉMIQUE ===
        section_academic = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_academic.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            section_academic, text="🎓 Informations académiques", font=self._font(12, "bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=10, pady=(8, 6))

        academic_frame = ctk.CTkFrame(section_academic)
        academic_frame.pack(fill="x", padx=10, pady=(0, 8))
        academic_frame.grid_columnconfigure(0, weight=1)
        academic_frame.grid_columnconfigure(1, weight=1)

        # Année académique
        years = self.academic_year_service.get_years_financials()
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}

        year_entry = add_labeled_entry(academic_frame, "Année académique *", "2024-2025", row=0, col=0, col_span=2)
        
        threshold_info_label = ctk.CTkLabel(
            academic_frame, text="ℹ️ Sélectionnez une année pour voir le seuil financier", font=self._font(10), text_color=self.colors["text_light"]
        )
        threshold_info_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=(4, 6))
        
        def update_threshold_info(*args):
            """Met à jour l'affichage du seuil lorsque l'année change"""
            selected_year_name = year_entry.get().strip()
            if selected_year_name and selected_year_name in year_map:
                year_id = year_map[selected_year_name]
                year_data = next((y for y in years if y.get("academic_year_id") == year_id), None)
                if year_data:
                    threshold = year_data.get("threshold_amount", 0) or 0
                    final_fee = year_data.get("final_fee", 0) or 0
                    threshold_info_label.configure(
                        text=f"💰 Seuil: ${threshold:,.2f} | Frais: ${final_fee:,.2f}", text_color=self.colors["success"]
                    )
                else:
                    threshold_info_label.configure(
                        text="ℹ️ Sélectionnez une année pour voir le seuil financier", text_color=self.colors["text_light"]
                    )
            else:
                threshold_info_label.configure(
                    text="ℹ️ Sélectionnez une année pour voir le seuil financier", text_color=self.colors["text_light"]
                )
        
        year_entry.bind("<KeyRelease>", update_threshold_info)
        year_entry.bind("<FocusOut>", update_threshold_info)

        # --- Faculté (combobox + saisie libre) ---
        faculties = self.student_service.get_faculties() or []
        faculty_names = [f"{f['name']} / {f['code']}" if f.get('code') else f['name'] for f in faculties]
        faculty_id_map = {}
        for f in faculties:
            key = f"{f['name']} / {f['code']}" if f.get('code') else f['name']
            faculty_id_map[key] = f['id']

        ctk.CTkLabel(academic_frame, text="Faculté *", font=self._font(10), text_color=self.colors["text_light"]).grid(
            row=3, column=0, sticky="w", padx=4, pady=(5, 1))
        faculty_entry = ctk.CTkComboBox(
            academic_frame, values=faculty_names if faculty_names else [""],
            fg_color=self.colors["main_bg"], border_color=self.colors["border"],
            border_width=1, corner_radius=6, height=28, button_color=self.colors["primary"]
        )
        faculty_entry.grid(row=4, column=0, sticky="ew", padx=4, pady=(0, 4))
        if faculty_names:
            faculty_entry.set(faculty_names[0])
        else:
            faculty_entry.set("")

        # --- Département (cascade sur faculté) ---
        ctk.CTkLabel(academic_frame, text="Département *", font=self._font(10), text_color=self.colors["text_light"]).grid(
            row=3, column=1, sticky="w", padx=4, pady=(5, 1))
        department_entry = ctk.CTkComboBox(
            academic_frame, values=[""],
            fg_color=self.colors["main_bg"], border_color=self.colors["border"],
            border_width=1, corner_radius=6, height=28, button_color=self.colors["primary"]
        )
        department_entry.grid(row=4, column=1, sticky="ew", padx=4, pady=(0, 4))
        department_entry.set("")
        dept_id_map = {}

        # --- Promotion (cascade sur département) ---
        ctk.CTkLabel(academic_frame, text="Promotion *", font=self._font(10), text_color=self.colors["text_light"]).grid(
            row=5, column=0, sticky="w", padx=4, pady=(5, 1), columnspan=2)
        promotion_entry = ctk.CTkComboBox(
            academic_frame, values=[""],
            fg_color=self.colors["main_bg"], border_color=self.colors["border"],
            border_width=1, corner_radius=6, height=28, button_color=self.colors["primary"]
        )
        promotion_entry.grid(row=6, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 4))
        promotion_entry.set("")
        promo_id_map = {}

        def _reload_departments(*args):
            fac_val = faculty_entry.get().strip()
            fac_id = faculty_id_map.get(fac_val)
            if fac_id:
                depts = self.student_service.get_departments_by_faculty(fac_id) or []
            else:
                depts = []
            dept_id_map.clear()
            dept_names = []
            for d in depts:
                key = f"{d['name']} / {d['code']}" if d.get('code') else d['name']
                dept_names.append(key)
                dept_id_map[key] = d['id']
            department_entry.configure(values=dept_names if dept_names else [""])
            department_entry.set(dept_names[0] if dept_names else "")
            _reload_promotions()

        def _reload_promotions(*args):
            dept_val = department_entry.get().strip()
            dept_id = dept_id_map.get(dept_val)
            if dept_id:
                promos = self.student_service.get_promotions_by_department(dept_id) or []
            else:
                promos = []
            promo_id_map.clear()
            promo_names = []
            for p in promos:
                key = f"{p['name']}" + (f" ({p['year']})" if p.get('year') else "")
                promo_names.append(key)
                promo_id_map[key] = p['id']
            promotion_entry.configure(values=promo_names if promo_names else [""])
            promotion_entry.set(promo_names[0] if promo_names else "")

        faculty_entry.configure(command=_reload_departments)
        department_entry.configure(command=_reload_promotions)
        # Charger les départements de la première faculté
        _reload_departments()

        # === SECTION: PHOTO ===
        section_photo = ctk.CTkFrame(form_scroll, fg_color=self.colors["card_bg"], corner_radius=10)
        section_photo.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            section_photo, text="📸 Photo du visage (passeport)", font=self._font(12, "bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=10, pady=(8, 6))

        photo_frame = ctk.CTkFrame(section_photo)
        photo_frame.pack(fill="x", padx=10, pady=(0, 6))
        photo_frame.grid_columnconfigure(0, weight=1)
        photo_frame.grid_columnconfigure(1, weight=0)

        photo_path_var = StringVar(value="")
        photo_entry = ctk.CTkEntry(
            photo_frame, textvariable=photo_path_var, fg_color=self.colors["main_bg"], border_color=self.colors["border"], border_width=1, corner_radius=6, height=28
        )
        photo_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        choose_btn = ctk.CTkButton(
            photo_frame, text="📁 Parcourir", width=80, height=28, fg_color=self.colors["info"], hover_color="#0891b2", corner_radius=6
        )
        choose_btn.grid(row=0, column=1)

        preview_frame = ctk.CTkFrame(section_photo)
        preview_frame.pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkLabel(
            preview_frame, text="Aperçu", font=self._font(10), text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(0, 4))

        preview_image_label = ctk.CTkLabel(preview_frame, text="")
        preview_image_label.pack(anchor="w")

        guidelines = ctk.CTkLabel(
            section_photo, text="Fond neutre • Visage centré • Une seule personne • Bonne lumière", font=self._font(9), text_color=self.colors["text_light"]
        )
        guidelines.pack(anchor="w", padx=10, pady=(0, 6))

        def choose_photo():
            file_path = filedialog.askopenfilename(
                title="Choisir une photo", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                photo_path_var.set(file_path)
                try:
                    image = Image.open(file_path)
                    image.thumbnail((100, 130))
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    preview_image_label.configure(image=ctk_image)
                    preview_image_label.image = ctk_image
                except Exception as e:
                    logger.warning(f"Preview photo error: {e}")

        choose_btn.configure(command=choose_photo)

        # === SECTION: BOUTONS ===
        button_frame = ctk.CTkFrame(form_scroll)
        button_frame.pack(fill="x", pady=(6, 0))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        field_widgets = {
            "student_number": student_number_entry,
            "firstname": firstname_entry,
            "lastname": lastname_entry,
            "email": email_entry,
            "phone": phone_entry,
            "year": year_entry,
            "faculty": faculty_entry,
            "department": department_entry,
            "promotion": promotion_entry,
            "photo": photo_entry,
        }

        default_border_color = self.colors["border"]
        error_border_color = self.colors["danger"]

        validation_feedback = ctk.CTkLabel(
            form_scroll,
            text="",
            font=self._font(10),
            text_color=self.colors["danger"],
            justify="left",
            wraplength=dialog_width - 80,
        )
        validation_feedback.pack(fill="x", pady=(4, 8), padx=4)
        validation_feedback.pack_forget()

        def reset_field_errors():
            for widget in field_widgets.values():
                try:
                    widget.configure(border_color=default_border_color, border_width=1)
                except Exception:
                    continue
            validation_feedback.configure(text="")
            validation_feedback.pack_forget()

        def mark_field_error(field_key: str):
            widget = field_widgets.get(field_key)
            if widget is None:
                return
            try:
                widget.configure(border_color=error_border_color, border_width=2)
            except Exception:
                pass

        def show_form_errors(errors: list, focus_field: str = None):
            if not errors:
                return
            feedback = "⚠️ Veuillez corriger les points suivants :\n" + "\n".join([f"• {err}" for err in errors])
            validation_feedback.configure(text=feedback)
            validation_feedback.pack(fill="x", pady=(4, 8), padx=4)
            if focus_field and field_widgets.get(focus_field):
                try:
                    field_widgets[focus_field].focus_set()
                except Exception:
                    pass

        def parse_registration_error(raw_error: str):
            details = (raw_error or "").strip()
            lower = details.lower()
            if not details:
                return "Échec d'enregistrement: cause inconnue.", None

            if "duplicate entry" in lower:
                if "student_number" in lower or "matricule" in lower:
                    return "Ce matricule existe déjà. Veuillez en saisir un autre.", "student_number"
                if "email" in lower:
                    return "Cette adresse email est déjà utilisée.", "email"
                if "phone" in lower or "telephone" in lower:
                    return "Ce numéro de téléphone est déjà utilisé.", "phone"
                return "Un enregistrement avec ces informations existe déjà.", None

            if "cannot be null" in lower:
                return "Certaines informations obligatoires sont manquantes.", None

            return f"Échec d'enregistrement: {details}", None

        def save_student():
            reset_field_errors()

            student_number = student_number_entry.get().strip()
            firstname = firstname_entry.get().strip()
            lastname = lastname_entry.get().strip()
            email = email_entry.get().strip()
            phone_number = phone_entry.get().strip()
            faculty_label = faculty_entry.get().strip()
            department_label = department_entry.get().strip()
            promotion_label = promotion_entry.get().strip()
            selected_year_name = year_entry.get().strip()
            selected_year_id = year_map.get(selected_year_name) if selected_year_name else None
            photo_path = photo_path_var.get().strip()

            errors = []
            first_error_field = None

            def add_error(field_key: str, message: str):
                nonlocal first_error_field
                errors.append(message)
                mark_field_error(field_key)
                if first_error_field is None:
                    first_error_field = field_key

            required_fields = [
                ("student_number", student_number, "Le matricule étudiant est obligatoire."),
                ("firstname", firstname, "Le prénom est obligatoire."),
                ("lastname", lastname, "Le nom est obligatoire."),
                ("email", email, "L'email est obligatoire."),
                ("phone", phone_number, "Le téléphone WhatsApp est obligatoire."),
                ("faculty", faculty_label, "La faculté est obligatoire."),
                ("department", department_label, "Le département est obligatoire."),
                ("promotion", promotion_label, "La promotion est obligatoire."),
                ("year", selected_year_name, "L'année académique est obligatoire."),
                ("photo", photo_path, "La photo passeport est obligatoire."),
            ]

            for field_key, value, message in required_fields:
                if not value:
                    add_error(field_key, message)

            if student_number:
                valid, msg = self.auth_service.validators.validate_student_number(student_number)
                if not valid:
                    add_error("student_number", f"Matricule invalide ({msg}).")

            if email:
                valid, msg = self.auth_service.validators.validate_email(email)
                if not valid:
                    add_error("email", f"Email invalide ({msg}).")

            if phone_number:
                valid, msg = self.auth_service.validators.validate_phone(phone_number)
                if not valid:
                    add_error("phone", f"Téléphone invalide ({msg}).")

            if photo_path:
                allowed_ext = {".jpg", ".jpeg", ".png", ".bmp"}
                ext = os.path.splitext(photo_path)[1].lower()
                if not os.path.isfile(photo_path):
                    add_error("photo", "Le fichier photo sélectionné est introuvable.")
                elif ext not in allowed_ext:
                    add_error("photo", "Format de photo non supporté (utilisez JPG, JPEG, PNG ou BMP).")

            if errors:
                show_form_errors(errors, first_error_field)
                return

            if selected_year_name and not selected_year_id:
                create_year = messagebox.askyesno(
                    "Année académique manquante", f"L'année académique '{selected_year_name}' n'existe pas.\n\n"
                    "Voulez-vous la créer maintenant avec les paramètres par défaut?\n\n"
                    "• Seuil financier: $300\n"
                    "• Frais finaux: $500\n"
                    "• Validité partielle: 30 jours"
                )

                if create_year:
                    selected_year_id = self.academic_year_service.create_year_simple(selected_year_name)
                    if not selected_year_id:
                        add_error("year", f"Impossible de créer l'année académique '{selected_year_name}'.")
                        show_form_errors(errors, first_error_field)
                        return
                else:
                    messagebox.showinfo("Annulé", "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.")
                    return

            if not selected_year_id:
                add_error("year", "Année académique invalide ou non reconnue.")
                show_form_errors(errors, first_error_field)
                return

            # --- Résolution faculté/département/promotion (maps ComboBox ou BD) ---
            faculty_id = faculty_id_map.get(faculty_label)
            if not faculty_id:
                fm = self.student_service.find_faculty_by_input(faculty_label)
                faculty_id = fm[0]["id"] if fm else self.student_service.create_faculty(faculty_label)
                if not faculty_id:
                    add_error("faculty", f"Impossible de créer la faculté '{faculty_label}'.")
                    show_form_errors(errors, first_error_field)
                    return

            dept_id = dept_id_map.get(department_label)
            if not dept_id:
                dm = self.student_service.find_department_by_input(department_label, faculty_id)
                dept_id = dm[0]["id"] if dm else self.student_service.create_department(department_label, faculty_id)
                if not dept_id:
                    add_error("department", f"Impossible de créer le département '{department_label}'.")
                    show_form_errors(errors, first_error_field)
                    return

            promo_id = promo_id_map.get(promotion_label)
            if not promo_id:
                pm = self.student_service.find_promotion_by_input(promotion_label, dept_id)
                promo_id = pm[0]["id"] if pm else self.student_service.create_promotion(promotion_label, dept_id)
                if not promo_id:
                    add_error("promotion", f"Impossible de créer la promotion '{promotion_label}'.")
                    show_form_errors(errors, first_error_field)
                    return

            year_data = next((y for y in years if y.get("academic_year_id") == selected_year_id), None)
            if not year_data:
                ErrorManager.show_error("database_query", f"Failed to fetch academic year data for year_id: {selected_year_id}", dialog)
                return

            threshold_required = Decimal(str(year_data.get("threshold_amount", 0)))
            final_fee_value = Decimal(str(year_data.get("final_fee", threshold_required)))

            # --- Désactiver le bouton et lancer le travail lourd en arrière-plan ---
            save_btn.configure(state="disabled", text="⏳ Enregistrement...")

            def _do_heavy():
                result = {"ok": False, "error": None, "field": None}
                try:
                    face_service = self._get_face_service()
                    encoding = None
                    if face_service.is_available():
                        try:
                            encoding = face_service.register_face(photo_path, 1)
                        except Exception as e:
                            result["error"] = f"Échec de l'analyse faciale: {e}"
                            result["field"] = "photo"
                            return
                        if encoding is None:
                            result["error"] = "Aucun visage détecté (ou plusieurs visages). Utilisez une photo passeport claire."
                            result["field"] = "photo"
                            return
                        quality_ok, quality_msg = face_service.validate_passport_photo(photo_path)
                        if not quality_ok:
                            result["error"] = f"Qualité photo insuffisante: {quality_msg}"
                            result["field"] = "photo"
                            return
                    else:
                        result["error"] = "Reconnaissance faciale indisponible sur ce poste (bibliothèque face_recognition requise)."
                        result["field"] = "photo"
                        return

                    storage_dir = os.path.join(os.getcwd(), "storage", "student_photos")
                    os.makedirs(storage_dir, exist_ok=True)
                    ext = os.path.splitext(photo_path)[1].lower()
                    stored_photo_name = f"{student_number}{ext}"
                    stored_photo_path = os.path.join(storage_dir, stored_photo_name)
                    try:
                        shutil.copy2(photo_path, stored_photo_path)
                        with open(stored_photo_path, "rb") as f:
                            photo_blob = f.read()
                    except Exception as e:
                        result["error"] = f"Impossible d'enregistrer la photo: {e}"
                        result["field"] = "photo"
                        return

                    face_bytes = encoding.tobytes() if encoding is not None else None
                    student = Student(
                        student_number=student_number, firstname=firstname, lastname=lastname,
                        email=email, phone_number=phone_number, promotion_id=promo_id,
                        passport_photo_path=stored_photo_path, passport_photo_blob=photo_blob,
                        academic_year_id=selected_year_id
                    )

                    student_id = self.auth_service.register_student_with_face(student, None, face_bytes)
                    if not student_id:
                        raw_error = self.auth_service.get_last_error()
                        user_error, field_key = parse_registration_error(raw_error)
                        result["error"] = user_error
                        result["field"] = field_key
                        return

                    finance_ok = self.finance_service.create_finance_profile(student_id, threshold_required, selected_year_id)
                    if not finance_ok:
                        logger.warning(f"Finance profile not created for student {student_id}")

                    def _send_welcome_notification_async():
                        try:
                            self.notification_service.send_welcome_notification(
                                student_email=email,
                                student_phone=phone_number,
                                student_name=f"{firstname} {lastname}",
                                student_number=student_number,
                                threshold_required=float(threshold_required),
                                final_fee=float(final_fee_value),
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send welcome notification: {e}")

                    # Ne pas bloquer la confirmation UI sur les appels réseau (email/WhatsApp)
                    threading.Thread(target=_send_welcome_notification_async, daemon=True).start()

                    result["ok"] = True
                except Exception as e:
                    logger.error(f"save_student background error: {e}")
                    result["error"] = f"Erreur inattendue: {e}"
                finally:
                    dialog.after(0, lambda: _on_done(result))

            def _on_done(result):
                save_btn.configure(state="normal", text="✓ Valider")
                if result["ok"]:
                    ErrorManager.show_success("Succès", "Étudiant enregistré avec succès.", dialog)
                    dialog.destroy()
                    self._invalidate_view_cache(
                        "dashboard_snapshot", "students_all_with_finance",
                        "academic_years", "finance_snapshot",
                    )
                    self._schedule_heavy_views_prefetch(delay_ms=250)
                    self._run_with_loading(self._show_students, "Actualisation des étudiants...")
                else:
                    if result.get("field"):
                        mark_field_error(result["field"])
                    show_form_errors([result["error"] or "Erreur inconnue"], result.get("field"))

            import threading
            threading.Thread(target=_do_heavy, daemon=True).start()

        cancel_btn = ctk.CTkButton(
            button_frame, text="Annuler", fg_color=self.colors["border"], text_color=self.colors["text_dark"], hover_color=self.colors["hover"], height=32, corner_radius=8, command=dialog.destroy
        )
        cancel_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        save_btn = ctk.CTkButton(
            button_frame, text="✓ Valider", fg_color=self.colors["success"], hover_color="#059669", height=32, corner_radius=8, command=save_student
        )
        save_btn.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _open_edit_student_dialog(self, student: dict):
        """Ouvre la fenêtre de modification complète d'un étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Modifier étudiant")
        dialog_width = 520
        dialog_height = 580
        
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        dialog.resizable(True, True)
        self._center_and_show_dialog(dialog)

        student_id = student.get("id")
        details = self.student_service.get_student_with_academics(student_id) or student

        # === HEADER COLORÉ (COMPACT) ===
        header = ctk.CTkFrame(dialog, fg_color="#8b5cf6", corner_radius=0)
        header.pack(fill="x", side="top")
        
        ctk.CTkLabel(
            header, text="✏️ Modifier Étudiant", font=ctk.CTkFont(size=16, weight="bold"), text_color="#ffffff"
        ).pack(pady=(12, 6), padx=20)
        
        fullname = f"{details.get('firstname', '')} {details.get('lastname', '')}".strip()
        ctk.CTkLabel(
            header, text=fullname or "Aucun nom", font=ctk.CTkFont(size=11), text_color="#f3e8ff"
        ).pack(pady=(0, 10), padx=20)

        # === CONTENU PRINCIPAL ===
        content = ctk.CTkFrame(dialog, fg_color="#f8f9fa")
        content.pack(fill="both", expand=True, padx=0, pady=0)

        form_container = ctk.CTkFrame(content)
        form_container.pack(fill="both", expand=True, padx=15, pady=10)

        form = ctk.CTkScrollableFrame(
            form_container, scrollbar_button_color=self.colors["border"], scrollbar_button_hover_color=self.colors["text_light"]
        )
        form.pack(fill="both", expand=True, padx=3, pady=3)

        fields_frame = ctk.CTkFrame(form)
        fields_frame.pack(fill="x", padx=3, pady=3)
        fields_frame.grid_columnconfigure(0, weight=1)
        fields_frame.grid_columnconfigure(1, weight=1)

        def add_labeled_entry(label_text, value="", placeholder="", row=0, col=0, col_span=1):
            label = ctk.CTkLabel(fields_frame, text=label_text, font=self._font(10))
            label.grid(row=row, column=col, sticky="w", padx=4, pady=(5, 2))
            entry = ctk.CTkEntry(fields_frame, placeholder_text=placeholder, height=28)
            entry.grid(row=row + 1, column=col, columnspan=col_span, sticky="ew", padx=4, pady=(0, 3))
            if value:
                entry.insert(0, value)
            return entry

        student_number_entry = add_labeled_entry("Matricule étudiant", details.get("student_number", ""), "Ex: STU2026-001", row=0, col=0)
        firstname_entry = add_labeled_entry("Prénom", details.get("firstname", ""), "Ex: Jean", row=0, col=1)
        lastname_entry = add_labeled_entry("Nom", details.get("lastname", ""), "Ex: Dupont", row=2, col=0)
        email_entry = add_labeled_entry("Email", details.get("email", ""), "Ex: jean@uor.rw", row=2, col=1)
        phone_entry = add_labeled_entry("Téléphone WhatsApp", details.get("phone_number", ""), "Ex: +243123456789", row=4, col=0)

        # Année académique
        years = self.academic_year_service.get_years()
        year_map = {(y.get("year_name") or y.get("name")): y.get("academic_year_id") for y in years if (y.get("year_name") or y.get("name"))}
        current_year_name = details.get("academic_year_name") or ""

        ctk.CTkLabel(fields_frame, text="Année académique", font=self._font(10)).grid(row=6, column=0, sticky="w", padx=4, pady=(5, 2))
        year_entry = ctk.CTkEntry(fields_frame, placeholder_text="Ex: 2024-2025", height=28)
        if current_year_name:
            year_entry.insert(0, current_year_name)
        year_entry.grid(row=7, column=0, columnspan=2, sticky="ew", padx=4, pady=(0, 3))

        faculty_display = details.get("faculty_name") or ""
        if details.get("faculty_code"):
            faculty_display = f"{faculty_display} / {details.get('faculty_code')}".strip()
        department_display = details.get("department_name") or ""
        if details.get("department_code"):
            department_display = f"{department_display} / {details.get('department_code')}".strip()
        promotion_display = details.get("promotion_name") or ""

        faculty_entry = add_labeled_entry("Faculté", faculty_display, "Ex: Informatique / INF", row=8, col=0)
        department_entry = add_labeled_entry("Département", department_display, "Ex: Génie Informatique / G.I", row=8, col=1)
        promotion_entry = add_labeled_entry("Promotion", promotion_display, "Ex: L3-LMD/G.I", row=10, col=0, col_span=2)

        photo_row = ctk.CTkFrame(form)
        photo_row.pack(fill="x", pady=(6, 0))
        photo_row.grid_columnconfigure(0, weight=0)
        photo_row.grid_columnconfigure(1, weight=1)
        photo_row.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(photo_row, text="Photo du visage (passeport)", font=self._font(10)).grid(row=0, column=0, sticky="w", padx=(0, 6))
        photo_path_var = StringVar(value="")
        photo_entry = ctk.CTkEntry(photo_row, textvariable=photo_path_var, height=28)
        photo_entry.grid(row=0, column=1, sticky="ew")

        preview_frame = ctk.CTkFrame(form)
        preview_frame.pack(fill="x", pady=(4, 2))
        preview_label = ctk.CTkLabel(
            preview_frame, text="Aperçu photo", font=self._font(10), text_color=self.colors["text_light"]
        )
        preview_label.pack(anchor="w")

        preview_image_label = ctk.CTkLabel(preview_frame, text="")
        preview_image_label.pack(anchor="w", pady=(2, 0))

        existing_photo_path = details.get("passport_photo_path")
        existing_photo_blob = details.get("passport_photo_blob")
        existing_image = self._get_cached_photo(existing_photo_path, existing_photo_blob, size=(80, 100))
        if existing_image:
            preview_image_label.configure(image=existing_image)
            preview_image_label.image = existing_image

        def choose_photo():
            file_path = filedialog.askopenfilename(
                title="Choisir une photo", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
            )
            if file_path:
                photo_path_var.set(file_path)
                try:
                    image = Image.open(file_path)
                    image.thumbnail((80, 100))
                    ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
                    preview_image_label.configure(image=ctk_image)
                    preview_image_label.image = ctk_image
                except Exception as e:
                    logger.warning(f"Preview photo error: {e}")

        choose_btn = ctk.CTkButton(photo_row, text="Parcourir", width=80, height=28, command=choose_photo)
        choose_btn.grid(row=0, column=2, sticky="e", padx=(8, 0))

        ctk.CTkLabel(
            form, text="Fond neutre, visage centré, une seule personne, bonne lumière.", font=self._font(10), text_color=self.colors["text_light"]
        ).pack(anchor="w", pady=(0, 6))

        def save_changes():
            student_number = student_number_entry.get().strip()
            firstname = firstname_entry.get().strip()
            lastname = lastname_entry.get().strip()
            email = email_entry.get().strip()
            phone_number = phone_entry.get().strip()
            faculty_label = faculty_entry.get().strip()
            department_label = department_entry.get().strip()
            promotion_label = promotion_entry.get().strip()
            selected_year_name = year_entry.get().strip()
            selected_year_id = year_map.get(selected_year_name) if selected_year_name else None
            photo_path = photo_path_var.get().strip()

            if not all([student_number, firstname, lastname, email, phone_number, faculty_label, department_label, promotion_label, selected_year_name]):
                ErrorManager.show_error("validation_error", "All fields are required", dialog)
                return

            if selected_year_name and not selected_year_id:
                # L'année n'existe pas - proposer de la créer
                create_year = messagebox.askyesno(
                    "Année académique manquante", f"L'année académique '{selected_year_name}' n'existe pas.\n\n"
                    "Voulez-vous la créer maintenant avec les paramètres par défaut?\n\n"
                    "• Seuil financier: $300\n"
                    "• Frais finaux: $500\n"
                    "• Validité partielle: 30 jours"
                )
                
                if create_year:
                    selected_year_id = self.academic_year_service.create_year_simple(selected_year_name)
                    if not selected_year_id:
                        ErrorManager.show_error("validation_error", f"Failed to create academic year: {selected_year_name}", dialog)
                        return
                else:
                    messagebox.showinfo("Annulé", "Veuillez créer l'année académique d'abord dans la section 'Années Académiques'.")
                    return

            faculty_matches = self.student_service.find_faculty_by_input(faculty_label)
            if not faculty_matches:
                faculty_id = self.student_service.create_faculty(faculty_label)
                if not faculty_id:
                    ErrorManager.show_error("validation_error", f"Failed to create faculty: {faculty_label}", dialog)
                    return
            else:
                faculty_id = faculty_matches[0]["id"]

            department_matches = self.student_service.find_department_by_input(department_label, faculty_id)
            if not department_matches:
                department_id = self.student_service.create_department(department_label, faculty_id)
                if not department_id:
                    ErrorManager.show_error("validation_error", f"Failed to create department: {department_label}", dialog)
                    return
            else:
                department_id = department_matches[0]["id"]

            promotion_matches = self.student_service.find_promotion_by_input(promotion_label, department_id)
            if not promotion_matches:
                promotion_id = self.student_service.create_promotion(promotion_label, department_id)
                if not promotion_id:
                    ErrorManager.show_error("validation_error", f"Failed to create promotion: {promotion_label}", dialog)
                    return
            else:
                promotion_id = promotion_matches[0]["id"]

            update_data = {
                "student_number": student_number, "firstname": firstname, "lastname": lastname, "email": email, "phone_number": phone_number, "promotion_id": promotion_id, "academic_year_id": selected_year_id, }

            if photo_path:
                storage_dir = os.path.join(os.getcwd(), "storage", "student_photos")
                os.makedirs(storage_dir, exist_ok=True)
                ext = os.path.splitext(photo_path)[1].lower()
                stored_photo_name = f"{student_number}{ext}"
                stored_photo_path = os.path.join(storage_dir, stored_photo_name)
                try:
                    shutil.copy2(photo_path, stored_photo_path)
                    with open(stored_photo_path, "rb") as f:
                        photo_blob = f.read()
                    update_data["passport_photo_path"] = stored_photo_path
                    update_data["passport_photo_blob"] = photo_blob
                except Exception as e:
                    ErrorManager.show_error("validation_error", f"Failed to save photo: {str(e)}", dialog)
                    return

            logger.debug(f"Updating student {student_id} with data: {update_data}")
            if self.student_service.update_student(student_id, update_data):
                ErrorManager.show_success("Succès", "Étudiant modifié avec succès.", dialog)
                dialog.destroy()
                self._invalidate_view_cache(
                    "dashboard_snapshot",
                    "students_all_with_finance",
                    "academic_years",
                    "finance_snapshot",
                )
                self._schedule_heavy_views_prefetch(delay_ms=250)
                self._run_with_loading(self._show_students, "Actualisation des étudiants...")
            else:
                ErrorManager.show_error("database_query", f"Failed to update student {student_id}", dialog)

        button_row = ctk.CTkFrame(form)
        button_row.pack(fill="x", pady=(8, 10))

        save_btn = ctk.CTkButton(
            button_row, text="Enregistrer", fg_color=self.colors["success"], hover_color=self.colors["primary"], height=32, command=save_changes
        )
        save_btn.pack(fill="x")

    def _open_payment_dialog(self, student: dict):
        """Ouvre une fenêtre pour enregistrer un paiement étudiant - Style moderne"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Enregistrer un paiement")
        
        # Compact sizing
        dialog_width = 420
        dialog_height = 400
        
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        dialog.resizable(True, True)
        self._center_and_show_dialog(dialog)

        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        student_number = student.get("student_number", "-")
        student_id = student.get("id")

        # === HEADER COLORÉ ===
        header = ctk.CTkFrame(dialog, fg_color="#0a84ff", corner_radius=0)
        header.pack(fill="x", side="top")
        
        title_label = ctk.CTkLabel(
            header, text="💳 Enregistrer un Paiement", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff"
        )
        title_label.pack(pady=(15, 8), padx=20)
        
        student_info_label = ctk.CTkLabel(
            header, text=f"{fullname} • #{student_number}", font=ctk.CTkFont(size=12), text_color="#e8f4ff"
        )
        student_info_label.pack(pady=(0, 15), padx=20)

        # === CONTENU PRINCIPAL ===
        content = ctk.CTkFrame(dialog, fg_color=self.colors.get("main_bg", "#f8f9fa"))
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # Label Montant avec icône
        amount_label_box = ctk.CTkFrame(content)
        amount_label_box.pack(fill="x", padx=25, pady=(20, 8))
        
        ctk.CTkLabel(
            amount_label_box, text="💰 Montant à payer", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1e293b"
        ).pack(anchor="w")

        # Input Montant avec style amélioré
        amount_entry = ctk.CTkEntry(
            content, placeholder_text="Entrez le montant (ex: 50.00)", font=ctk.CTkFont(size=12), fg_color="#ffffff", text_color="#1e293b", placeholder_text_color="#cbd5e1", border_color="#cbd5e1", border_width=1, height=40, corner_radius=8
        )
        amount_entry.pack(fill="x", padx=25, pady=(0, 15))

        # Conteneur pour la barre de progression (caché initialement)
        loading_container = ctk.CTkFrame(content)
        loading_container.pack(fill="x", padx=25, pady=(10, 0))
        
        # === BARRE DE PROGRESSION PERSONNALISÉE ===
        progress_frame = ctk.CTkFrame(loading_container)
        progress_frame.pack(fill="x", pady=(0, 0))
        
        progress_label = ctk.CTkLabel(
            progress_frame, text="", font=ctk.CTkFont(size=11), text_color="#0a84ff"
        )
        progress_label.pack(anchor="w", pady=(0, 6))
        
        # Barre de progression avec fond gris
        progress_bg = ctk.CTkFrame(progress_frame, fg_color="#e2e8f0", height=6, corner_radius=3)
        progress_bg.pack(fill="x")
        progress_bg.pack_propagate(False)
        
        progress_bar = ctk.CTkFrame(progress_bg, fg_color="#0a84ff", height=6, corner_radius=3)
        progress_bar.pack(side="left", fill="y")
        progress_bar.pack_propagate(False)
        
        # Pourcentage
        progress_pct_label = ctk.CTkLabel(
            progress_frame, text="0%", font=ctk.CTkFont(size=10, weight="bold"), text_color="#0a84ff"
        )
        progress_pct_label.pack(anchor="e", pady=(4, 0))
        
        def update_progress(percent: int, status_text: str = ""):
            """Met à jour la barre de progression"""
            progress_width = int((percent / 100) * (progress_bg.winfo_width() - 4))
            if progress_width > 0:
                progress_bar.configure(width=progress_width)
            progress_pct_label.configure(text=f"{percent}%")
            if status_text:
                progress_label.configure(text=status_text)

        def map_payment_service_error(raw_error: str):
            details = (raw_error or "").strip()
            lower = details.lower()

            if not details:
                return "payment_processing", "Erreur inconnue lors de l'enregistrement du paiement"

            if "no_active_fees" in lower or "no active fees" in lower:
                return "payment_no_active_fees", details

            if "overpayment" in lower:
                return "payment_exceeds_limit", details

            if "no_finance_profile" in lower:
                return "payment_processing", "Aucun profil financier trouvé pour cet étudiant"

            if "no_promotion_data" in lower:
                return "payment_processing", "Impossible de déterminer la promotion/frais de l'étudiant"

            return "payment_processing", details

        def save_payment():
            amount_text = amount_entry.get().strip().replace(",", ".")
            if not amount_text:
                ErrorManager.show_error("validation_error", "Empty amount field", dialog)
                return
            try:
                amount_usd = Decimal(amount_text)
                if amount_usd <= 0:
                    ErrorManager.show_error("payment_invalid_amount", f"Amount {amount_usd} is not positive", dialog)
                    return

                finance = self.finance_service.get_student_finance(student_id)
                if not finance:
                    self.finance_service.create_finance_profile(student_id, None, student.get("academic_year_id"))
                    finance = self.finance_service.get_student_finance(student_id)

                # Vérifier que le profil finance existe
                if not finance:
                    ErrorManager.show_error(
                        "payment_processing", "Impossible de créer le profil financier de l'étudiant", dialog
                    )
                    return

                final_fee = finance.get("final_fee")
                if final_fee is None and finance.get("academic_year_id"):
                    year = self.academic_year_service.get_year_by_id(finance.get("academic_year_id"))
                    if year:
                        final_fee = year.get("final_fee")
                final_fee = Decimal(str(final_fee or 0))
                current_paid = Decimal(str(finance.get("amount_paid") or 0))
                
                # Vérifier si des frais académiques sont définis
                if final_fee <= 0:
                    ErrorManager.show_error(
                        "payment_no_active_fees", f"Student {student_id} promotion has no active academic fees", dialog
                    )
                    return
                
                # Vérifier si l'étudiant a déjà tout payé
                if current_paid >= final_fee:
                    ErrorManager.show_error(
                        "payment_already_paid", f"Student {student_id} has already paid ${current_paid:.2f} (total: ${final_fee:.2f})", dialog
                    )
                    return
                
                # Vérifier si le montant dépasse la limite
                if (current_paid + amount_usd) > final_fee:
                    remaining = final_fee - current_paid
                    if remaining < 0:
                        remaining = Decimal("0")
                    ErrorManager.show_error(
                        "payment_exceeds_limit", f"Payment amount ${amount_usd} exceeds remaining balance ${remaining:.2f}", dialog
                    )
                    return

                save_btn.configure(state="disabled")
                amount_entry.configure(state="disabled")
                progress_frame.pack(fill="x", padx=0, pady=(10, 15))

                def worker():
                    success = False
                    error_msg = None
                    try:
                        # Simuler la progression
                        for i in [10, 30, 60, 80]:
                            self.after(200, lambda p=i: update_progress(p, f"Traitement... {p}%"))
                            import time
                            time.sleep(0.3)
                        
                        success = self.finance_service.record_payment(student_id, amount_usd)
                    except Exception as ex:
                        error_msg = str(ex)

                    def finish():
                        if success:
                            update_progress(100, "Paiement enregistré ✓")
                            self.after(1500, lambda: [
                                ErrorManager.show_success("Succès", "Paiement enregistré avec succès.", dialog), dialog.destroy(), self._refresh_after_payment_success()
                            ])
                        else:
                            progress_frame.pack_forget()
                            save_btn.configure(state="normal")
                            amount_entry.configure(state="normal")
                            service_error = self.finance_service.get_last_error()
                            if error_msg:
                                mapped_type, mapped_details = map_payment_service_error(error_msg)
                                ErrorManager.show_error(mapped_type, mapped_details, dialog)
                            elif service_error:
                                mapped_type, mapped_details = map_payment_service_error(service_error)
                                ErrorManager.show_error(mapped_type, mapped_details, dialog)
                            else:
                                ErrorManager.show_error(
                                    "payment_processing",
                                    "Échec du paiement sans détail technique. Vérifiez les frais de la promotion et le profil financier.",
                                    dialog,
                                )

                    self.after(0, finish)

                threading.Thread(target=worker, daemon=True).start()
            except Exception as ex:
                ErrorManager.show_error("payment_invalid_amount", str(ex), dialog)

        # === BOUTONS ===
        button_frame = ctk.CTkFrame(content)
        button_frame.pack(fill="x", padx=25, pady=(20, 20))
        
        save_btn = ctk.CTkButton(
            button_frame, text="✓ Enregistrer le Paiement", fg_color="#0a84ff", hover_color="#0078d4", text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=42, corner_radius=8, command=save_payment
        )
        save_btn.pack(fill="x", pady=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            button_frame, text="Annuler", fg_color="#e2e8f0", hover_color="#cbd5e1", text_color="#1e293b", font=ctk.CTkFont(size=12), height=36, corner_radius=8, command=dialog.destroy
        )
        cancel_btn.pack(fill="x")

    def _open_payment_history_dialog(self, student: dict):
        """Ouvre la fenêtre d'historique de paiements par étudiant"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Historique des paiements")
        dialog_width = 540
        dialog_height = 480
        
        dialog.geometry(f"{dialog_width}x{dialog_height}")
        dialog.grab_set()
        dialog.resizable(True, True)
        self._center_and_show_dialog(dialog)

        fullname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip()
        student_number = student.get("student_number", "-")
        student_id = student.get("id")

        # === HEADER COLORÉ ===
        header = ctk.CTkFrame(dialog, fg_color="#6366f1", corner_radius=0)
        header.pack(fill="x", side="top")
        
        ctk.CTkLabel(
            header, text="🧾 Historique des Paiements", font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff"
        ).pack(pady=(15, 8), padx=20)
        
        ctk.CTkLabel(
            header, text=f"{fullname} • #{student_number}", font=ctk.CTkFont(size=12), text_color="#e0e7ff"
        ).pack(pady=(0, 15), padx=20)

        # === CONTENU PRINCIPAL ===
        content = ctk.CTkFrame(dialog, fg_color="#f8f9fa")
        content.pack(fill="both", expand=True, padx=0, pady=0)

        # Info access code
        info_frame = ctk.CTkFrame(content)
        info_frame.pack(fill="x", padx=20, pady=12)

        access_code = self.finance_service.get_latest_access_code(student_id)
        if access_code:
            code_text = f"Code actuel: {access_code.get('access_code')} ({access_code.get('access_type')})"
            code_color = "#10b981"
        else:
            code_text = "Code actuel: Aucun code généré"
            code_color = "#cbd5e1"

        ctk.CTkLabel(
            info_frame, text=code_text, font=ctk.CTkFont(size=12, weight="bold"), text_color=code_color
        ).pack(anchor="w")

        # === TABLE ===
        table = ctk.CTkFrame(content, fg_color="#ffffff", corner_radius=8, border_width=1, border_color="#e2e8f0")
        table.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        headers = ["Date", "Montant ($)", "Méthode"]
        layout = self._get_table_layout("payment_history", len(headers))
        weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table, headers, weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=6)

        scroll = ctk.CTkScrollableFrame(table)
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        history = self.finance_service.get_student_payment_history(student_id)
        if not history:
            ctk.CTkLabel(
                scroll, text="Aucun paiement enregistré.", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        cumulative = Decimal("0")
        layout = self._get_table_layout("payment_history")
        min_widths = layout["min_widths"]
        for row_index, item in enumerate(history):
            row = ctk.CTkFrame(scroll)
            row.pack(fill="x", pady=4)
            created_at = item.get("created_at")
            date_text = created_at.strftime("%d/%m/%Y %H:%M") if hasattr(created_at, "strftime") else str(created_at)
            amount_value = Decimal(str(item.get('amount_paid_usd') or 0))
            cumulative += amount_value
            row_values = [
                date_text, f"{amount_value:.2f}\nCumul: {cumulative:.2f}", item.get("payment_method") or "-", ]
            self._populate_table_row(
                row, row_values, weights, text_colors=[self.colors["text_dark"]] * 3, font_sizes=[10] * 3, anchors=["w", "e", "center"], min_widths=min_widths, padx=10, pady=4
            )
            self._style_table_row(row, row_index)

    def _start_esp32_status_polling(self, initial_delay_ms: int = 0):
        """Démarre le polling ESP32 (si une étiquette valide est présente)."""
        self._stop_esp32_status_polling()
        if not self._esp32_status_label:
            return
        try:
            if not self._esp32_status_label.winfo_exists():
                self._esp32_status_label = None
                return
        except Exception:
            self._esp32_status_label = None
            return

        self._esp32_poll_active = True
        delay = max(0, int(initial_delay_ms))
        self._esp32_poll_job = self.after(delay, self._refresh_esp32_status)

    def _stop_esp32_status_polling(self):
        """Arrête proprement le polling ESP32 pour éviter les tâches orphelines."""
        self._esp32_poll_active = False
        if self._esp32_poll_job is not None:
            try:
                self.after_cancel(self._esp32_poll_job)
            except Exception:
                pass
            self._esp32_poll_job = None

    def _refresh_esp32_status(self):
        """Met à jour le statut ESP32 sans bloquer l'UI"""
        if not self._esp32_poll_active or not self._esp32_status_label:
            self._stop_esp32_status_polling()
            return

        try:
            if not self._esp32_status_label.winfo_exists():
                self._esp32_status_label = None
                self._stop_esp32_status_polling()
                return
        except Exception:
            self._esp32_status_label = None
            self._stop_esp32_status_polling()
            return

        def worker():
            status = self.esp32_service.check_status()
            self.after(0, lambda: self._update_esp32_status_label(status))

        threading.Thread(target=worker, daemon=True).start()
        self._esp32_poll_job = self.after(self.esp32_service.refresh_interval_ms, self._refresh_esp32_status)

    def _update_esp32_status_label(self, status):
        if not self._esp32_status_label:
            return
        try:
            if not self._esp32_status_label.winfo_exists():
                return
            self._esp32_status_label.configure(text=f"Statut: {status.text}", text_color=status.color)
        except Exception:
            return
    
    def _show_finance(self, filter_category="all"):
        """Affiche la page Finances
        
        Args:
            filter_category: Filtre à appliquer ("all", "paid", "partial", "unpaid")
        """
        self.current_view = "finance"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("finance")
        self.title_label.configure(text=self._t("finance_title", "Gestion Financière"))
        self.subtitle_label.configure(text=self._t("finance_subtitle", "Suivi des paiements et seuils"))
        
        # Sauvegarder le filtre actuel
        if not hasattr(self, '_finance_filter'):
            self._finance_filter = "all"
        self._finance_filter = filter_category
        
        # === KPIs FINANCIERS ===
        kpi_frame = ctk.CTkFrame(self.content_frame)
        kpi_frame.pack(fill="x", pady=(0, 20))
        
        finance_snapshot = self._get_cached_data(
            "finance_snapshot",
            lambda: {
                "revenue": self.dashboard_service.get_revenue_collected(),
                "payment_status": self.dashboard_service.get_students_by_payment_status(),
                "payments": self.dashboard_service.get_students_finance_overview(),
            },
            ttl_seconds=60.0,
        )
        revenue = finance_snapshot["revenue"]
        payment_status = finance_snapshot["payment_status"]
        if not payment_status:
            payment_status = {"never_paid": 0, "partial_paid": 0, "eligible": 0}
        
        kpis = [
            (self._format_usd(revenue), "Revenus Totaux", "green", "all"), 
            (f"{payment_status['eligible']}", "Paiements Complètes", "blue", "paid"), 
            (f"{payment_status['partial_paid']}", "Paiements Partiels", "orange", "partial"), 
            (f"{payment_status['never_paid']}", "Non Payés", "red", "unpaid"),
        ]
        
        # Responsive: layout horizontal ou vertical selon écran
        is_tiny_finance = self.screen_width < 900
        is_small_screen = self.screen_width < 1000

        if is_tiny_finance:
            kpi_rows = [ctk.CTkFrame(kpi_frame), ctk.CTkFrame(kpi_frame)]
            kpi_rows[0].pack(fill="x", pady=(0, 6))
            kpi_rows[1].pack(fill="x")
        
        for i, (value, label, color_key, category) in enumerate(kpis):
            color_map = {"green": self.colors["success"], "blue": self.colors["info"], "orange": self.colors["warning"], "red": self.colors["danger"]}
            
            # Bordure pour indiquer la carte active
            border_width = 3 if category == filter_category else 0
            border_color = "#ffffff" if category == filter_category else color_map[color_key]
            
            kpi_card = ctk.CTkFrame(
                kpi_frame if not is_tiny_finance else kpi_rows[i // 2], 
                fg_color=color_map[color_key], 
                corner_radius=8, 
                height=72 if is_tiny_finance else (80 if is_small_screen else 100),
                border_width=border_width,
                border_color=border_color
            )
            if is_tiny_finance:
                kpi_card.pack(side="left", fill="both", expand=True, padx=(0, 4) if i % 2 == 0 else (4, 0), pady=0)
            else:
                kpi_layout_side = "top" if is_small_screen else "left"
                kpi_card.pack(side=kpi_layout_side, fill="both", expand=True, padx=(0 if i == 0 else 3), pady=(0 if i == 0 else 3))
            kpi_card.pack_propagate(False)
            
            # Rendre la carte cliquable avec le filtre approprié
            kpi_card.configure(cursor="hand2")
            kpi_card.bind(
                "<Button-1>",
                lambda e, cat=category: self._run_with_section_loading(
                    self.content_frame,
                    lambda: self._show_finance(cat),
                    "Actualisation des finances...",
                ),
            )
            
            value_font_size = 14 if is_tiny_finance else (16 if is_small_screen else 20)
            label_font_size = 8 if is_small_screen else 10
            
            value_label = ctk.CTkLabel(kpi_card, text=value, font=ctk.CTkFont(size=value_font_size, weight="bold"), text_color=self.colors["text_white"])
            value_label.pack(expand=True)
            value_label.bind(
                "<Button-1>",
                lambda e, cat=category: self._run_with_section_loading(
                    self.content_frame,
                    lambda: self._show_finance(cat),
                    "Actualisation des finances...",
                ),
            )
            
            label_widget = ctk.CTkLabel(kpi_card, text=label, font=ctk.CTkFont(size=label_font_size), text_color=self.colors["text_white"])
            label_widget.pack(pady=(0, 8 if is_tiny_finance else 10))
            label_widget.bind(
                "<Button-1>",
                lambda e, cat=category: self._run_with_section_loading(
                    self.content_frame,
                    lambda: self._show_finance(cat),
                    "Actualisation des finances...",
                ),
            )
        
        # === TABLEAU PAIEMENTS ===
        table_card = self._create_card(self.content_frame)
        table_card.pack(fill="both", expand=True)
        
        # Titre avec indication du filtre actif
        filter_labels = {
            "all": "📊 Historique des Paiements - Tous",
            "paid": "📊 Historique des Paiements - Payés Complètement",
            "partial": "📊 Historique des Paiements - Paiements Partiels",
            "unpaid": "📊 Historique des Paiements - Non Payés"
        }
        
        ctk.CTkLabel(
            table_card, text=filter_labels.get(filter_category, filter_labels["all"]), font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Zone table alignée (même largeur pour en-tête + lignes)
        table_zone = ctk.CTkFrame(table_card, fg_color="transparent")
        table_zone.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Tableau header
        headers = ["Photo", "Étudiant", "ID", "Montant Payé ($)", "Seuil Requis ($)", "Statut", "Date"]
        layout = self._get_table_layout("finance_payments", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table_zone, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=10)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_zone, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=(15, 0))
        
        payments = finance_snapshot["payments"]
        if not payments:
            ctk.CTkLabel(
                scroll_frame, text="Aucun paiement trouvé.", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
            ).pack(pady=20)
            return
        
        # Filtrer les paiements selon la catégorie sélectionnée
        filtered_payments = []
        for payment in payments:
            # Gérer les valeurs NULL de la base de données
            amount_paid_raw = payment.get('amount_paid')
            amount_paid = Decimal(str(amount_paid_raw)) if amount_paid_raw is not None else Decimal('0')
            is_eligible = payment.get('is_eligible')
            
            # Déterminer le statut (même logique que get_students_by_payment_status)
            # NULL ou 0 = non payé
            if amount_paid_raw is None or amount_paid == 0:
                payment_status = "unpaid"
            elif amount_paid > 0 and (is_eligible is None or is_eligible == 0):
                payment_status = "partial"
            else:  # is_eligible == 1
                payment_status = "paid"
            
            # Appliquer le filtre
            if filter_category == "all" or filter_category == payment_status:
                filtered_payments.append(payment)
        
        # Afficher un message si aucun résultat
        if not filtered_payments:
            ctk.CTkLabel(
                scroll_frame, text=f"Aucun étudiant dans cette catégorie.", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
            ).pack(pady=20)
            return
        
        self._cancel_scheduled_renders("finance_")
        self._render_in_batches(
            render_key="finance_rows",
            items=filtered_payments,
            render_item=lambda payment_item, row_index: self._render_finance_payment_row(
                scroll_frame, payment_item, column_weights, min_widths, row_index
            ),
            batch_size=18,
            delay_ms=1,
            on_complete=scroll_frame.update_idletasks,
        )

    def _render_finance_payment_row(self, parent, payment, column_weights, min_widths, row_index: int = 0):
        """Rend une ligne de paiement dans la vue finance."""
        row = ctk.CTkFrame(parent, fg_color=self.colors["hover"], corner_radius=6)
        row.pack(fill="x", pady=4)

        self._configure_table_columns(row, column_weights, min_widths=min_widths)

        fullname = f"{payment.get('firstname', '')} {payment.get('lastname', '')}".strip()
        student_number = payment.get('student_number', '-')
        amount_paid = Decimal(str(payment.get('amount_paid') or 0))
        threshold_required = Decimal(str(payment.get('threshold_required') or 0))
        last_date = payment.get('last_payment_date') or "-"

        if amount_paid <= 0:
            status = "Non payé"
        elif threshold_required > 0 and amount_paid < threshold_required:
            status = "Partiel"
        else:
            status = "Payé"

        color = self.colors["success"] if status == "Payé" else (self.colors["warning"] if status == "Partiel" else self.colors["danger"])
        self._render_photo_cell(
            row, 0, photo_path=payment.get('passport_photo_path'), photo_blob=payment.get('passport_photo_blob'), size=(36, 44)
        )

        row_values = [
            fullname, student_number, self._format_usd(amount_paid), self._format_usd(threshold_required), status, str(last_date)
        ]
        row_colors = [self.colors["text_dark"], self.colors["text_light"], self.colors["success"], self.colors["text_light"], color, self.colors["text_light"]]
        row_weights = ["normal", "normal", "bold", "normal", "normal", "normal"]
        layout = self._get_table_layout("finance_payments")
        row_anchors = layout["anchors"][1:]

        self._populate_table_row_with_offset(
            row, row_values, column_weights, start_col=1, text_colors=row_colors, font_weights=row_weights, anchors=row_anchors, min_widths=min_widths
        )
        self._style_table_row(row, row_index)
    
    def _show_access_logs(self):
        """Affiche les logs d'accès"""
        self.current_view = "access_logs"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("access_logs")
        self.title_label.configure(text=self._t("access_logs_title", "Historique d'Accès"))
        self.subtitle_label.configure(text=self._t("access_logs_subtitle", "Suivi des tentatives d'accès"))
        
        # === HEADER ===
        header = ctk.CTkFrame(self.content_frame)
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            header, text="📋 Historique d'Accès", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # === STATISTIQUES RAPIDES ===
        stats_frame = ctk.CTkFrame(self.content_frame)
        stats_frame.pack(fill="x", pady=(0, 20))

        access_stats = self._get_cached_data(
            "access_stats",
            lambda: {
                "granted": self.dashboard_service.get_access_granted(),
                "denied": self.dashboard_service.get_access_denied(),
            },
            ttl_seconds=30.0,
        )
        granted = access_stats["granted"]
        denied = access_stats["denied"]
        total_attempts = granted + denied
        
        stat_items = [
            (str(granted), "Accès Accordés", self.colors["success"]), (str(denied), "Accès Refusés", self.colors["danger"]), (str(total_attempts), "Total Tentatives", self.colors["info"]), ]
        
        # Responsive: layout horizontal ou vertical selon écran
        is_small_screen = self.screen_width < 1000
        stat_layout_side = "top" if is_small_screen else "left"
        
        for i, (value, label, color) in enumerate(stat_items):
            stat_card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=8, height=70 if is_small_screen else 80)
            stat_card.pack(side=stat_layout_side, fill="both", expand=True, padx=(0 if i == 0 else 3), pady=(0 if i == 0 else 3))
            stat_card.pack_propagate(False)
            self._make_card_clickable(stat_card, self._show_access_logs)
            
            value_font = 15 if is_small_screen else 18
            label_font = 9 if is_small_screen else 11
            
            ctk.CTkLabel(stat_card, text=value, font=ctk.CTkFont(size=value_font, weight="bold"), text_color=self.colors["text_white"]).pack(expand=True)
            ctk.CTkLabel(stat_card, text=label, font=ctk.CTkFont(size=label_font), text_color=self.colors["text_white"]).pack()
        
        # === TABLEAU LOGS ===
        table_card = self._create_card(self.content_frame)
        table_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            table_card, text="📊 Détail des Tentatives d'Accès", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Zone table alignée (même largeur pour en-tête + lignes)
        table_zone = ctk.CTkFrame(table_card, fg_color="transparent")
        table_zone.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Tableau header
        headers = ["Photo", "Étudiant", "ID", "Point d'Accès", "Résultat", "Mot de passe", "Visage", "Finance", "Heure"]
        layout = self._get_table_layout("access_logs", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table_zone, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=8, pady=10)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_zone, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=(15, 0))
        
        logs = self._get_cached_data(
            "access_logs_list",
            self.dashboard_service.get_access_logs_with_students,
            ttl_seconds=30.0,
        )
        if not logs:
            ctk.CTkLabel(
                scroll_frame, text="Aucun log trouvé.", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
            ).pack(pady=20)
            return

        for row_index, log in enumerate(logs):
            row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
            row.pack(fill="x", pady=3)

            self._configure_table_columns(row, column_weights, min_widths=min_widths)

            status = str(log.get('status') or '').upper()
            result_symbol = "✅" if status == "GRANTED" else "❌"
            result_color = self.colors["success"] if status == "GRANTED" else self.colors["danger"]

            password_ok = "✓" if log.get('password_validated') else "✗"
            face_ok = "✓" if log.get('face_validated') else "✗"
            finance_ok = "✓" if log.get('finance_validated') else "✗"

            created_at = log.get('created_at')
            time_str = created_at.strftime("%H:%M") if hasattr(created_at, 'strftime') else str(created_at)[-8:-3]

            display_row = [
                f"{log.get('firstname', '')} {log.get('lastname', '')}".strip(), log.get('student_number', '-'), log.get('access_point') or "-", result_symbol, password_ok, face_ok, finance_ok, time_str
            ]

            cell_colors = [
                self.colors["text_dark"], self.colors["text_light"], self.colors["text_light"], result_color, self.colors["success"] if password_ok == "✓" else self.colors["danger"], self.colors["success"] if face_ok == "✓" else self.colors["danger"], self.colors["success"] if finance_ok == "✓" else self.colors["danger"], self.colors["text_light"], ]
            row_weights = ["normal", "normal", "normal", "bold", "normal", "normal", "normal", "normal"]
            layout = self._get_table_layout("access_logs")
            row_anchors = layout["anchors"][1:]
            row_min_widths = min_widths
            self._render_photo_cell(
                row, 0, photo_path=log.get('passport_photo_path'), photo_blob=log.get('passport_photo_blob'), size=(36, 44)
            )
            self._populate_table_row_with_offset(
                row, display_row, column_weights, start_col=1, text_colors=cell_colors, font_sizes=[9, 9, 9, 9, 10, 10, 10, 9], font_weights=row_weights, anchors=row_anchors, min_widths=row_min_widths, padx=8, pady=6
            )
            self._style_table_row(row, row_index)
    
    def _show_reports(self):
        """Affiche les rapports"""
        self.current_view = "reports"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("reports")
        self.title_label.configure(text=self._t("reports_title", "Rapports et Statistiques"))
        self.subtitle_label.configure(text=self._t("reports_subtitle", "Analyse par faculté et performance"))
        
        # === FILTRES ===
        filter_frame = ctk.CTkFrame(self.content_frame, fg_color=self.colors["hover"], corner_radius=8)
        filter_frame.pack(fill="x", pady=(0, 20), padx=20)
        self._make_card_clickable(filter_frame, self._show_reports)
        
        ctk.CTkLabel(
            filter_frame, text="🔍 Filtrer par:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(15, 20), pady=10)
        
        # === RAPPORTS PAR FACULTÉ ===
        report_card = self._create_card(self.content_frame)
        report_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            report_card, text="📊 Statistiques par Faculté", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 15))
        
        # Zone table alignée (même largeur pour en-tête + lignes)
        table_zone = ctk.CTkFrame(report_card, fg_color="transparent")
        table_zone.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # Tableau header
        headers = ["Photo", "Faculté", "Département", "Total Étudiants", "Éligibles", "% Éligibilité", "Revenus"]
        layout = self._get_table_layout("reports_faculty", len(headers))
        column_weights = layout["weights"]
        header_anchors = layout["anchors"]
        min_widths = layout["min_widths"]
        self._create_table_header(table_zone, headers, column_weights, anchors=header_anchors, min_widths=min_widths, padx=10, pady=10)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(table_zone, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=(15, 0))
        
        faculties_data = self._get_cached_data(
            "faculty_stats_with_photos",
            self.dashboard_service.get_faculty_stats_with_photos,
            ttl_seconds=30.0,
        )
        faculty_names = sorted({f.get("faculty_name") for f in faculties_data if f.get("faculty_name")})
        faculties = ["Toutes"] + faculty_names
        faculty_combo = ctk.CTkComboBox(filter_frame, values=faculties, width=150, height=30)
        faculty_combo.set("Toutes")
        faculty_combo.pack(side="left", padx=10, pady=10)

        def render_faculty_stats(selected_faculty: str):
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            data = faculties_data
            if selected_faculty != "Toutes":
                data = [f for f in faculties_data if f.get("faculty_name") == selected_faculty]

            if not data:
                ctk.CTkLabel(
                    scroll_frame, text="Aucune statistique disponible.", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
                ).pack(pady=20)
                return

            for row_index, faculty in enumerate(data):
                row = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=6)
                row.pack(fill="x", pady=4)

                self._configure_table_columns(row, column_weights, min_widths=min_widths)
                total = int(faculty.get('total_students') or 0)
                eligible = int(faculty.get('eligible_students') or 0)
                percentage = (eligible / total * 100) if total else 0
                revenue = Decimal(str(faculty.get('revenue') or 0))

                self._render_photo_cell(
                    row, 0, photo_path=faculty.get('passport_photo_path'), photo_blob=faculty.get('passport_photo_blob'), size=(36, 44)
                )
                row_values = [
                    faculty.get('faculty_name') or "-", faculty.get('department_name') or "-", str(total), str(eligible), f"{percentage:.1f}%", self._format_usd(revenue)
                ]
                row_colors = [
                    self.colors["text_dark"], self.colors["text_light"], self.colors["text_dark"], self.colors["success"], self.colors["primary"], self.colors["warning"], ]
                row_weights = ["bold", "normal", "normal", "bold", "bold", "normal"]
                layout = self._get_table_layout("reports_faculty")
                row_anchors = layout["anchors"][1:]
                row_min_widths = min_widths
                self._populate_table_row_with_offset(
                    row, row_values, column_weights, start_col=1, text_colors=row_colors, font_weights=row_weights, anchors=row_anchors, min_widths=row_min_widths
                )
                self._style_table_row(row, row_index)

        render_faculty_stats("Toutes")
        faculty_combo.configure(command=lambda value: render_faculty_stats(value))

    def _show_access_requests(self):
        """Affiche les demandes d'accès en attente (super admin uniquement)."""
        if not self._can_access_view("access_requests"):
            self._handle_forbidden_view("access_requests")
            return

        self.current_view = "access_requests"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("access_requests")
        self.title_label.configure(text=self._t("access_management_title", "Gestion des Accès"))
        self.subtitle_label.configure(text=self._t("access_management_subtitle", "Demandes en attente & utilisateurs approuvés"))

        reviewer = self.current_user_email or "super_admin"

        outer = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=20, pady=12)

        tab_bar = ctk.CTkFrame(outer, fg_color=self.colors["card_bg"], corner_radius=10)
        tab_bar.pack(fill="x", pady=(0, 12))

        tab_btn_frame = ctk.CTkFrame(tab_bar, fg_color="transparent")
        tab_btn_frame.pack(fill="x", padx=10, pady=8)

        tab_content = ctk.CTkFrame(outer, fg_color="transparent")
        tab_content.pack(fill="both", expand=True)

        current_tab = {"key": "pending"}
        tab_btns = {}

        def _switch_tab(key):
            current_tab["key"] = key
            for k, btn in tab_btns.items():
                if k == key:
                    btn.configure(fg_color=self.colors["primary"], text_color=self.colors["text_white"])
                else:
                    btn.configure(fg_color="transparent", text_color=self.colors["text_dark"])
            for w in tab_content.winfo_children():
                w.destroy()
            if key == "pending":
                _render_pending(tab_content)
            else:
                _render_users(tab_content)

        def _render_pending(parent):
            card = self._create_card(parent)
            card.pack(fill="both", expand=True)

            ctk.CTkLabel(
                card, text=f"✅  {self._t('pending_access_requests_title', 'Demandes en attente de validation')}",
                font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_dark"],
            ).pack(anchor="w", padx=20, pady=(16, 4))

            pending = self._get_cached_data(
                "pending_access_requests",
                self.auth_service.get_pending_access_requests,
                ttl_seconds=15.0,
            )

            if not pending:
                ctk.CTkLabel(
                    card, text=f"✔  {self._t('no_pending_requests', 'Aucune demande en attente.')}",
                    font=ctk.CTkFont(size=12), text_color=self.colors["text_light"],
                ).pack(anchor="w", padx=20, pady=16)
                return

            body = ctk.CTkScrollableFrame(card, fg_color="transparent")
            body.pack(fill="both", expand=True, padx=20, pady=(6, 16))

            for req in pending:
                row = ctk.CTkFrame(body, fg_color=self.colors["hover"], corner_radius=8)
                row.pack(fill="x", pady=5)

                left = ctk.CTkFrame(row, fg_color="transparent")
                left.pack(side="left", fill="both", expand=True, padx=14, pady=10)

                requested_at = req.get("requested_at")
                if hasattr(requested_at, "strftime"):
                    requested_at = requested_at.strftime("%Y-%m-%d %H:%M")

                ctk.CTkLabel(
                    left, text=f"👤  {req.get('username', '-')}",
                    font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"], anchor="w",
                ).pack(anchor="w")
                ctk.CTkLabel(
                    left, text=f"📧  {req.get('email', '-')}   •   🕒  {requested_at or '-'}",
                    font=ctk.CTkFont(size=11), text_color=self.colors["text_light"], anchor="w",
                ).pack(anchor="w", pady=(3, 0))

                actions = ctk.CTkFrame(row, fg_color="transparent")
                actions.pack(side="right", padx=14, pady=10)

                def _approve(rid=req.get("id")):
                    self._invalidate_view_cache("pending_access_requests", "approved_administrators")
                    ok, msg = self.auth_service.approve_access_request(rid, reviewer_identifier=reviewer)
                    if ok:
                        messagebox.showinfo(self._t("success", "Succès"), msg)
                        _switch_tab("pending")
                    else:
                        messagebox.showerror(self._t("error", "Erreur"), msg)

                def _reject(rid=req.get("id")):
                    if not messagebox.askyesno(
                        self._t("confirmation", "Confirmation"),
                        self._t("reject_request_confirm", "Rejeter cette demande d'accès ?"),
                    ):
                        return
                    self._invalidate_view_cache("pending_access_requests")
                    ok, msg = self.auth_service.reject_access_request(rid, reviewer_identifier=reviewer)
                    if ok:
                        messagebox.showinfo(self._t("success", "Succès"), msg)
                        _switch_tab("pending")
                    else:
                        messagebox.showerror(self._t("error", "Erreur"), msg)

                ctk.CTkButton(
                    actions, text=f"✓  {self._t('approve', 'Valider')}", fg_color=self.colors["success"],
                    hover_color="#059669", text_color=self.colors["text_white"],
                    width=100, height=32, corner_radius=7, command=_approve,
                ).pack(side="left", padx=(0, 8))
                ctk.CTkButton(
                    actions, text=f"✗  {self._t('reject', 'Rejeter')}", fg_color=self.colors["danger"],
                    hover_color="#b91c1c", text_color=self.colors["text_white"],
                    width=100, height=32, corner_radius=7, command=_reject,
                ).pack(side="left")

        def _render_users(parent):
            card = self._create_card(parent)
            card.pack(fill="both", expand=True)

            ctk.CTkLabel(
                card, text=f"👥  {self._t('approved_users_title', 'Utilisateurs approuvés')}",
                font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_dark"],
            ).pack(anchor="w", padx=20, pady=(16, 4))

            admins = self._get_cached_data(
                "approved_administrators",
                self.auth_service.get_approved_administrators,
                ttl_seconds=20.0,
            )

            if not admins:
                ctk.CTkLabel(
                    card, text=self._t("no_users_found", "Aucun utilisateur trouvé."),
                    font=ctk.CTkFont(size=12), text_color=self.colors["text_light"],
                ).pack(anchor="w", padx=20, pady=16)
                return

            hdr = ctk.CTkFrame(card, fg_color=self.colors["primary"], corner_radius=6)
            hdr.pack(fill="x", padx=20, pady=(8, 0))
            for col_txt in [
                self._t("user", "Utilisateur"),
                self._t("email", "Email"),
                self._t("status", "Statut"),
                self._t("role", "Rôle"),
                self._t("action", "Action"),
            ]:
                ctk.CTkLabel(
                    hdr, text=col_txt, font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=self.colors["text_white"], anchor="w",
                ).pack(side="left", expand=True, fill="x", padx=8, pady=7)

            body = ctk.CTkScrollableFrame(card, fg_color="transparent")
            body.pack(fill="both", expand=True, padx=20, pady=(4, 16))

            for adm in admins:
                is_sa = bool(adm.get("is_super_admin"))
                is_active = bool(adm.get("is_active", 1))
                adm_id = adm.get("id")

                row = ctk.CTkFrame(body, fg_color=self.colors["hover"], corner_radius=6)
                row.pack(fill="x", pady=4)

                def _lbl(parent_w, text, color=None, weight="normal"):
                    return ctk.CTkLabel(
                        parent_w, text=text,
                        font=ctk.CTkFont(size=12, weight=weight),
                        text_color=color or self.colors["text_dark"], anchor="w",
                    )

                _lbl(row, f"👤  {adm.get('username', '-')}", weight="bold").pack(
                    side="left", expand=True, fill="x", padx=10, pady=8)
                _lbl(row, f"📧  {adm.get('email') or '-'}", self.colors["text_light"]).pack(
                    side="left", expand=True, fill="x", padx=6, pady=8)

                status_txt = (
                    f"✅ {self._t('active', 'Actif')}" if is_active
                    else f"🔴 {self._t('inactive', 'Inactif')}"
                )
                _lbl(row, status_txt, self.colors["success"] if is_active else self.colors["danger"]).pack(
                    side="left", expand=True, fill="x", padx=6, pady=8)

                role_txt = (
                    f"⭐ {self._t('super_admin', 'Super Admin')}" if is_sa
                    else f"🔧 {self._t('admin', 'Admin')}"
                )
                _lbl(row, role_txt, self.colors["warning"] if is_sa else self.colors["info"]).pack(
                    side="left", expand=True, fill="x", padx=6, pady=8)

                btn_f = ctk.CTkFrame(row, fg_color="transparent")
                btn_f.pack(side="left", padx=8, pady=6)

                if not is_sa:
                    def _delete(aid=adm_id, uname=adm.get("username", "?")):
                        if not messagebox.askyesno(
                            self._t("confirm_delete_user", "Confirmer la suppression"),
                            self._t(
                                "delete_user_irreversible",
                                "Supprimer définitivement l'utilisateur « {username} » ?\n\nCette action est irréversible.",
                            ).format(username=uname),
                            icon="warning",
                        ):
                            return
                        self._invalidate_view_cache("approved_administrators", "dashboard_snapshot")
                        ok, msg = self.auth_service.delete_administrator(
                            aid, requester_is_super_admin=self.is_super_admin
                        )
                        if ok:
                            messagebox.showinfo(self._t("success", "Succès"), msg)
                            _switch_tab("users")
                        else:
                            messagebox.showerror(self._t("error", "Erreur"), msg)

                    ctk.CTkButton(
                        btn_f, text=f"🗑  {self._t('delete', 'Supprimer')}",
                        fg_color=self.colors["danger"], hover_color="#b91c1c",
                        text_color=self.colors["text_white"],
                        width=110, height=30, corner_radius=7, command=_delete,
                    ).pack()
                else:
                    ctk.CTkLabel(btn_f, text="—", font=ctk.CTkFont(size=11),
                                 text_color=self.colors["text_light"]).pack()

        for key, label in [
            ("pending", f"📋  {self._t('access_tab_pending', 'Demandes en attente')}"),
            ("users", f"👥  {self._t('access_tab_users', 'Utilisateurs approuvés')}"),
        ]:
            btn = ctk.CTkButton(
                tab_btn_frame, text=label,
                fg_color=self.colors["primary"] if key == "pending" else "transparent",
                hover_color=self.colors["primary"],
                text_color=self.colors["text_white"] if key == "pending" else self.colors["text_dark"],
                corner_radius=8, height=38, font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda k=key: _switch_tab(k),
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")
            tab_btns[key] = btn

        _render_pending(tab_content)
    
    def _show_academic_years(self):
        """Affiche la gestion des années académiques"""
        if not self._can_access_view("academic_years"):
            self._handle_forbidden_view("academic_years")
            return
        self.current_view = "academic_years"
        self._persist_ui_context(view=self.current_view)
        self._set_main_scrollbar_visible(True)
        self._clear_content()
        self._update_nav_buttons("academic_years")
        self.title_label.configure(text=self._t("academic_years_title", "Années Académiques"))
        self.subtitle_label.configure(text=self._t("academic_years_subtitle", "Gestion des seuils financiers et périodes d'examens"))
        active_year = self._get_cached_data(
            "active_academic_year",
            self.academic_year_service.get_active_year,
            ttl_seconds=60.0,
        )
        
        # === Section: Frais & Seuils par Faculté → Promotion ===
        promo_card = self._create_card(self.content_frame)
        promo_card.pack(fill="x", expand=False, pady=(0, 12))

        ctk.CTkLabel(
            promo_card, text="🎓 Frais & Seuils par Faculté → Promotion", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=25, pady=(20, 10))

        # Filtres faculté
        filter_row = ctk.CTkFrame(promo_card)
        filter_row.pack(fill="x", padx=25, pady=(0, 10))

        ctk.CTkLabel(
            filter_row, text="🏛️ Faculté:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left", padx=(0, 10))

        promotions = self._get_cached_data(
            "promotions_with_fees",
            self.student_service.get_promotions_with_fees,
            ttl_seconds=45.0,
        )
        faculty_names = sorted({p.get("faculty_name") for p in promotions if p.get("faculty_name")})
        faculty_filter = ctk.CTkComboBox(
            filter_row, values=["Toutes Facultés"] + faculty_names, width=220, height=32
        )
        faculty_filter.set("Toutes Facultés")
        faculty_filter.pack(side="left")

        ctk.CTkButton(
            filter_row,
            text="📅 Gérer les périodes d'examens",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=self.colors["primary"],
            hover_color=self.colors["info"],
            text_color=self.colors["text_white"],
            height=32,
            corner_radius=8,
            command=lambda: self._run_with_loading(self._show_exam_periods),
        ).pack(side="right")

        if self.is_super_admin:
            ctk.CTkButton(
                filter_row,
                text="🔁 Bascule étudiants (année)",
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=self.colors["warning"],
                hover_color="#d97706",
                text_color=self.colors["text_white"],
                height=32,
                corner_radius=8,
                command=self._safe_open_bulk_academic_year_migration_dialog,
            ).pack(side="right", padx=(0, 8))

        promo_headers = ["Faculté", "Promotion", "Département", "Année", "Frais ($)", "Seuil ($)", "Action"]
        layout = self._get_table_layout("academic_promos", len(promo_headers))
        promo_weights = layout["weights"]
        promo_anchors = layout["anchors"]
        promo_min_widths = layout["min_widths"]
        
        # Créer un container pour l'en-tête et les données avec scroll horizontal si nécessaire
        promo_table_container = ctk.CTkFrame(promo_card, fg_color="transparent")
        table_height = 330 if self.screen_width < 1100 else 360
        promo_table_container.pack(fill="x", expand=False, padx=25, pady=(15, 16))
        promo_table_container.configure(height=table_height)
        promo_table_container.pack_propagate(False)
        
        # Utiliser la fonction générique de scroll horizontal
        promo_scroll = self._create_horizontal_scrollable_table(
            promo_table_container, promo_headers, promo_weights, 
            anchors=promo_anchors, min_widths=promo_min_widths
        )

        def render_promotions():
            for widget in promo_scroll.winfo_children():
                widget.destroy()

            selected_faculty = faculty_filter.get()
            filtered_promos = promotions
            if selected_faculty != "Toutes Facultés":
                filtered_promos = [p for p in promotions if p.get("faculty_name") == selected_faculty]

            if not filtered_promos:
                ctk.CTkLabel(
                    promo_scroll, text="Aucune promotion trouvée pour cette faculté.", font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
                ).pack(pady=20)
                return

            for row_index, promo in enumerate(filtered_promos):
                row = ctk.CTkFrame(promo_scroll, fg_color="transparent", corner_radius=8, height=52)
                row.pack(fill="x", pady=4)
                row.pack_propagate(False)
                self._configure_table_columns(row, promo_weights, min_widths=promo_min_widths)
                self._style_table_row(row, row_index, enable_hover=True)

                fee_value = promo.get('fee_usd') or 0
                threshold_value = promo.get('threshold_amount') or 0

                ctk.CTkLabel(
                    row, text=promo.get('faculty_name') or "-", font=ctk.CTkFont(size=11), text_color=self.colors["text_light"], anchor=promo_anchors[0]
                ).grid(row=0, column=0, sticky="ew", padx=10, pady=8)

                ctk.CTkLabel(
                    row, text=promo.get('name') or "-", font=ctk.CTkFont(size=11), text_color=self.colors["text_dark"], anchor=promo_anchors[1]
                ).grid(row=0, column=1, sticky="ew", padx=10, pady=8)

                ctk.CTkLabel(
                    row, text=promo.get('department_name') or "-", font=ctk.CTkFont(size=11), text_color=self.colors["text_light"], anchor=promo_anchors[2]
                ).grid(row=0, column=2, sticky="ew", padx=10, pady=8)

                ctk.CTkLabel(
                    row, text=str(promo.get('year') or "-"), font=ctk.CTkFont(size=11), text_color=self.colors["text_dark"], anchor=promo_anchors[3]
                ).grid(row=0, column=3, sticky="ew", padx=10, pady=8)

                fee_entry = ctk.CTkEntry(row, justify="center", width=120)
                fee_entry.insert(0, f"{Decimal(str(fee_value)):.2f}")
                fee_entry.grid(row=0, column=4, sticky="ew", padx=10, pady=8)

                threshold_entry = ctk.CTkEntry(row, justify="center", width=120)
                threshold_entry.insert(0, f"{Decimal(str(threshold_value)):.2f}")
                threshold_entry.grid(row=0, column=5, sticky="ew", padx=10, pady=8)

                def make_save(promotion_id, fee_widget, threshold_widget, save_btn_ref):
                    def _save():
                        try:
                            fee_val = Decimal(fee_widget.get().strip())
                            threshold_val = Decimal(threshold_widget.get().strip())
                            if fee_val < 0 or threshold_val < 0:
                                raise ValueError
                            if threshold_val > fee_val:
                                messagebox.showerror(
                                    "Erreur de Validation", "Le seuil ne peut pas dépasser les frais académiques."
                                )
                                return
                            
                            # Afficher le loading dialog
                            loading_dialog, loading_indicator = self._show_loading_dialog(
                                "Mise à jour des frais et notifications..."
                            )
                            save_btn_ref.configure(state="disabled")
                            fee_widget.configure(state="disabled")
                            threshold_widget.configure(state="disabled")
                            
                            def worker():
                                success = False
                                notification_count = 0
                                failed_count = 0
                                skipped_no_contact = 0
                                error_msg = None
                                
                                try:
                                    # Récupérer les anciennes valeurs avant la mise à jour
                                    old_promo = self.student_service.get_promotion_details(promotion_id)
                                    old_fee = float(old_promo.get('fee_usd', 0)) if old_promo else 0
                                    old_threshold = float(old_promo.get('threshold_amount', 0)) if old_promo else 0
                                    
                                    # Mettre à jour la BD
                                    if self.student_service.update_promotion_financials(promotion_id, fee_val, threshold_val):
                                        success = True

                                        channel_status = self.notification_service.get_channel_status()
                                        email_ok = channel_status.get("email_configured")
                                        whatsapp_ok = channel_status.get("whatsapp_configured")
                                        
                                        # Récupérer les étudiants et envoyer les notifications
                                        students = self.student_service.get_students_by_promotion(promotion_id)
                                        if students:
                                            for i, student in enumerate(students):
                                                loading_indicator.set_status(
                                                    f"Notification {i+1}/{len(students)} aux étudiants..."
                                                )
                                                try:
                                                    student_email = student.get('email')
                                                    student_phone = student.get('phone_number')
                                                    if not student_email and not student_phone:
                                                        skipped_no_contact += 1
                                                        continue

                                                    sent = self.notification_service.send_threshold_change_notification(
                                                        student_email=student_email, student_phone=student_phone, student_name=f"{student.get('firstname', '')} {student.get('lastname', '')}", old_threshold=old_threshold if old_threshold > 0 else None, new_threshold=float(threshold_val), old_final_fee=old_fee if old_fee > 0 else None, new_final_fee=float(fee_val)
                                                    )
                                                    if sent:
                                                        notification_count += 1
                                                    else:
                                                        failed_count += 1
                                                except Exception as notif_err:
                                                    logger.warning(f"Failed to notify student {student.get('id')}: {notif_err}")
                                                    failed_count += 1
                                        else:
                                            skipped_no_contact = 0
                                            failed_count = 0
                                            notification_count = 0
                                        
                                except Exception as ex:
                                    error_msg = str(ex)
                                
                                def finish():
                                    loading_indicator.stop()
                                    loading_dialog.destroy()
                                    save_btn_ref.configure(state="normal")
                                    fee_widget.configure(state="normal")
                                    threshold_widget.configure(state="normal")
                                    
                                    if success:
                                        if not email_ok and not whatsapp_ok:
                                            messagebox.showwarning(
                                                "Succès", "Frais et seuil mis à jour.\nNotifications non envoyées (Email/WhatsApp non configurés)."
                                            )
                                        elif notification_count > 0:
                                            summary = f"Frais et seuil mis à jour.\n{notification_count} notification(s) envoyée(s)."
                                            if failed_count:
                                                summary += f"\n{failed_count} échec(s) d'envoi."
                                            if skipped_no_contact:
                                                summary += f"\n{skipped_no_contact} étudiant(s) sans email/téléphone."
                                            messagebox.showinfo("Succès", summary)
                                        else:
                                            messagebox.showinfo(
                                                "Succès", "Frais et seuil mis à jour.\n(Aucun étudiant notifié)"
                                            )
                                        self._show_academic_years()  # Rafraîchir la vue
                                    else:
                                        if error_msg:
                                            messagebox.showerror("Erreur", f"Échec: {error_msg}")
                                        else:
                                            messagebox.showerror("Erreur", "Échec de mise à jour.")
                                
                                self.after(0, finish)
                            
                            threading.Thread(target=worker, daemon=True).start()
                            
                        except Exception:
                            messagebox.showerror("Erreur", "Montants invalides.")
                    return _save

                save_btn = ctk.CTkButton(
                    row, text="Enregistrer", width=120, fg_color=self.colors["primary"], hover_color="#2563eb", text_color=self.colors["text_white"], command=make_save(promo.get('id'), fee_entry, threshold_entry, None)
                )
                save_btn.grid(row=0, column=6, sticky="ew", padx=10, pady=8)
                
                # Passer le bouton à la fonction make_save
                save_btn.configure(command=make_save(promo.get('id'), fee_entry, threshold_entry, save_btn))

        render_promotions()
        faculty_filter.configure(command=lambda _value: render_promotions())
        
        # === Section: Périodes d'Examens (Bouton) ===
        exam_card = self._create_card(self.content_frame)
        exam_card.pack(fill="x", expand=False, pady=(8, 0))
        
        exam_btn_frame = ctk.CTkFrame(exam_card, fg_color="transparent")
        exam_btn_frame.pack(fill="x", padx=25, pady=14)
        
        ctk.CTkButton(
            exam_btn_frame, text="📅 Gérer les Périodes d'Examens", font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors["primary"], hover_color=self.colors["info"], text_color=self.colors["text_white"],
            height=45, corner_radius=8, command=lambda: self._run_with_loading(self._show_exam_periods)
        ).pack(fill="x", expand=True)

        if self.is_super_admin:
            try:
                self._render_academic_year_migration_audit_card()
            except Exception as audit_render_err:
                logger.warning(f"Failed to render audit card: {audit_render_err}")

    def _render_academic_year_migration_audit_card(self):
        """Affiche un historique compact des bascules annuelles journalisées."""
        audit_card = self._create_card(self.content_frame)
        audit_card.pack(fill="x", expand=False, pady=(8, 0))

        ctk.CTkLabel(
            audit_card,
            text="🧾 Journal d'audit — bascules annuelles",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.colors["text_dark"],
        ).pack(anchor="w", padx=25, pady=(16, 6))

        ctk.CTkLabel(
            audit_card,
            text="Historique récent des migrations d'étudiants entre années académiques.",
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_light"],
        ).pack(anchor="w", padx=25, pady=(0, 10))

        audit_rows = self._get_cached_data(
            "academic_year_migration_audit",
            lambda: self.student_service.get_recent_academic_year_migration_audit(8),
            ttl_seconds=20.0,
        )

        if not audit_rows:
            empty_label = ctk.CTkLabel(
                audit_card,
                text="Aucune bascule annuelle journalisée pour le moment.",
                font=ctk.CTkFont(size=11),
                text_color=self.colors["text_light"],
            )
            empty_label.pack(anchor="w", padx=25, pady=(0, 16))
            return

        body = ctk.CTkScrollableFrame(audit_card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        for idx, row_data in enumerate(audit_rows):
            row = ctk.CTkFrame(body, fg_color=self.colors["hover"], corner_radius=8)
            row.pack(fill="x", pady=4)
            # Avoid styling if not present to prevent crashes
            try:
                self._style_table_row(row, idx, enable_hover=False)
            except Exception:
                pass

            created_at = row_data.get("created_at")
            created_text = created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, "strftime") else str(created_at or "-")
            src_name = row_data.get("from_year_name") or f"ID {row_data.get('from_academic_year_id')}"
            dst_name = row_data.get("to_year_name") or f"ID {row_data.get('to_academic_year_id')}"
            actor = row_data.get("actor_identifier") or "super_admin"
            moved = int(row_data.get("moved_count") or 0)
            regenerated = int(row_data.get("regenerated_full_count") or 0)
            eligible_only = bool(row_data.get("eligible_only"))

            ctk.CTkLabel(
                row,
                text=f"{created_text} • {actor}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.colors["text_dark"],
            ).pack(anchor="w", padx=12, pady=(10, 2))

            ctk.CTkLabel(
                row,
                text=(
                    f"{src_name} → {dst_name} | migrés: {moved} | "
                    f"codes FULL régénérés: {regenerated} | filtre éligibles: {'oui' if eligible_only else 'non'}"
                ),
                font=ctk.CTkFont(size=10),
                text_color=self.colors["text_light"],
                justify="left",
                wraplength=max(300, self.screen_width - 240),
            ).pack(anchor="w", padx=12, pady=(0, 10))

    def _open_bulk_academic_year_migration_dialog(self):
        """Super Admin : bascule en lot des étudiants d'une année vers une autre."""
        if not self.is_super_admin:
            self._handle_forbidden_view("academic_years")
            return

        years = self.academic_year_service.get_years_financials() or self.academic_year_service.get_years() or []
        if not years:
            messagebox.showerror("Erreur", "Aucune année académique disponible.")
            return

        active_year = self.academic_year_service.get_active_year() or {}
        active_year_id = active_year.get("academic_year_id")

        year_options = []
        year_map = {}
        for y in years:
            yid = y.get("academic_year_id")
            yname = y.get("year_name") or y.get("name") or f"Année {yid}"
            label = f"{yname} (ID:{yid})"
            year_options.append(label)
            year_map[label] = yid

        dialog = ctk.CTkToplevel(self)
        dialog.title("Bascule annuelle (Super Admin)")
        dialog.geometry("620x390")
        dialog.resizable(False, False)
        # Ouverture modale stable (évite le couple grab_set + withdraw animé)
        try:
            dialog.transient(self.winfo_toplevel())
        except Exception:
            pass
        self._center_and_show_dialog(dialog)
        try:
            dialog.lift()
            dialog.focus_set()
            dialog.grab_set()
        except Exception:
            pass

        card = ctk.CTkFrame(dialog)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            card,
            text="🔁 Bascule d'étudiants vers une nouvelle année académique",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=self.colors["text_dark"],
        ).pack(anchor="w", padx=14, pady=(14, 6))

        ctk.CTkLabel(
            card,
            text=(
                "Réinscription annuelle: met à jour l'année académique, remet les paiements à zéro, "
                "retire les anciens codes d'accès. Les nouveaux codes seront générés après les nouveaux paiements."
            ),
            font=ctk.CTkFont(size=11),
            text_color=self.colors["text_light"],
            justify="left",
        ).pack(anchor="w", padx=14, pady=(0, 10))

        form = ctk.CTkFrame(card, fg_color=self.colors["hover"], corner_radius=10)
        form.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(form, text="Année source", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(form, text="Année cible", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, sticky="w", padx=12, pady=(10, 4))

        from_combo = ctk.CTkComboBox(form, values=year_options, width=260)
        to_combo = ctk.CTkComboBox(form, values=year_options, width=260)
        from_combo.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")
        to_combo.grid(row=1, column=1, padx=12, pady=(0, 10), sticky="w")

        if year_options:
            from_combo.set(year_options[0])
            to_combo.set(year_options[0])

        if active_year_id is not None:
            target_label = next((lbl for lbl, yid in year_map.items() if yid == active_year_id), None)
            if target_label:
                to_combo.set(target_label)

        eligible_only_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form,
            text="Migrer uniquement les étudiants éligibles (recommandé)",
            variable=eligible_only_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            form,
            text="ℹ️ Après migration, les étudiants sont considérés comme réinscrits: aucun code FULL conservé.",
            font=ctk.CTkFont(size=10),
            text_color=self.colors["text_light"],
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 10))

        info = ctk.CTkLabel(
            card,
            text="⚠️ Action sensible : cette opération impacte l'accès examen. Vérifiez source/cible avant validation.",
            text_color=self.colors["warning"],
            font=ctk.CTkFont(size=11),
            justify="left",
        )
        info.pack(anchor="w", padx=14, pady=(0, 10))

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=(0, 12))

        def run_migration():
            from_label = from_combo.get().strip()
            to_label = to_combo.get().strip()
            from_year_id = year_map.get(from_label)
            to_year_id = year_map.get(to_label)

            if not from_year_id or not to_year_id:
                messagebox.showerror("Erreur", "Année source/cible invalide.")
                return

            if int(from_year_id) == int(to_year_id):
                messagebox.showwarning("Validation", "L'année source et l'année cible sont identiques.")
                return

            preview = self.student_service.migrate_students_to_academic_year(
                from_academic_year_id=int(from_year_id),
                to_academic_year_id=int(to_year_id),
                eligible_only=bool(eligible_only_var.get()),
                dry_run=True,
            )
            if not preview.get("success"):
                messagebox.showerror("Prévisualisation impossible", preview.get("message", "Erreur de prévisualisation."))
                return

            to_move = int(preview.get("moved_count") or 0)
            eligible_count = len(preview.get("eligible_student_ids", []))

            if to_move == 0:
                messagebox.showinfo("Aucune migration", "Aucun étudiant ne correspond aux critères choisis.")
                return

            if not messagebox.askyesno(
                "Confirmation",
                f"Confirmer la bascule en lot ?\n\nSource: {from_label}\nCible: {to_label}\n\n"
                f"Filtre éligibles: {'Oui' if eligible_only_var.get() else 'Non'}\n"
                f"Mode: Réinscription annuelle (paiements/code remis à zéro)\n\n"
                f"Prévisualisation:\n"
                f"- Étudiants à migrer: {to_move}\n"
                f"- Étudiants éligibles concernés: {eligible_count}"
            ):
                return

            loading_dialog, loading_indicator = self._show_loading_dialog("Migration annuelle en cours...")

            def worker():
                result = self.student_service.migrate_students_to_academic_year(
                    from_academic_year_id=int(from_year_id),
                    to_academic_year_id=int(to_year_id),
                    eligible_only=bool(eligible_only_var.get()),
                    dry_run=False,
                )

                regenerated = 0

                if result.get("success"):
                    try:
                        self.student_service.log_academic_year_migration_audit(
                            actor_identifier=self.current_user_email or self.current_user.get("username") or "super_admin",
                            actor_role=self.current_user_role or "super_admin",
                            from_academic_year_id=int(from_year_id),
                            to_academic_year_id=int(to_year_id),
                            eligible_only=bool(eligible_only_var.get()),
                            moved_student_ids=result.get("moved_student_ids", []),
                            eligible_student_ids=result.get("eligible_student_ids", []),
                            regenerated_full_count=regenerated,
                        )
                    except Exception as audit_err:
                        logger.warning(f"Audit logging failed after academic year migration: {audit_err}")

                def finish():
                    try:
                        loading_indicator.stop()
                    except Exception:
                        pass
                    try:
                        loading_dialog.destroy()
                    except Exception:
                        pass

                    if not result.get("success"):
                        messagebox.showerror("Erreur migration", result.get("message", "Échec migration."))
                        return

                    self._invalidate_view_cache(
                        "students_all_with_finance",
                        "academic_years",
                        "active_academic_year",
                        "dashboard_snapshot",
                        "finance_snapshot",
                        "academic_year_migration_audit",
                    )
                    self._schedule_heavy_views_prefetch(delay_ms=250)

                    messagebox.showinfo(
                        "Migration terminée",
                        f"Étudiants migrés: {result.get('moved_count', 0)}\n"
                        f"Éligibles migrés: {len(result.get('eligible_student_ids', []))}\n"
                        "Codes d'accès conservés: 0 (réinscription annuelle)"
                    )

                    dialog.destroy()
                    self._run_with_loading(self._show_academic_years)

                self.after(0, finish)

            threading.Thread(target=worker, daemon=True).start()

        ctk.CTkButton(
            btns,
            text="Annuler",
            fg_color=self.colors["border"],
            text_color=self.colors["text_dark"],
            hover_color=self.colors["hover"],
            width=130,
            command=dialog.destroy,
        ).pack(side="left")

        ctk.CTkButton(
            btns,
            text="Valider la bascule",
            fg_color=self.colors["primary"],
            hover_color="#2563eb",
            text_color=self.colors["text_white"],
            width=180,
            command=run_migration,
        ).pack(side="right")

    def _safe_open_bulk_academic_year_migration_dialog(self):
        """Ouvre le dialog de bascule avec protection anti-crash globale."""
        if self._migration_dialog_opening:
            return

        self._migration_dialog_opening = True
        try:
            self._open_bulk_academic_year_migration_dialog()
        except Exception as e:
            logger.error(f"Failed to open bulk migration dialog: {e}", exc_info=True)
            try:
                messagebox.showerror(
                    "Erreur",
                    "Impossible d'ouvrir la fenêtre de bascule des étudiants.\n"
                    "Veuillez réessayer ou contacter l'administrateur.",
                )
            except Exception:
                pass
        finally:
            self._migration_dialog_opening = False
    
    def _update_thresholds(self, new_threshold_str, new_fee_str, academic_year_id):
        """Met à jour les seuils financiers et notifie tous les étudiants"""
        try:
            from decimal import Decimal
            
            new_threshold_usd = Decimal(new_threshold_str)
            new_fee_usd = Decimal(new_fee_str)
            new_threshold = new_threshold_usd
            new_fee = new_fee_usd
            
            # VALIDATION CRITIQUE : Le seuil ne peut JAMAIS dépasser les frais académiques
            if new_threshold > new_fee:
                messagebox.showerror(
                    "Erreur de Validation", f"Le seuil financier (${float(new_threshold):,.2f}) ne peut pas dépasser \n"
                    f"les frais académiques totaux (${float(new_fee):,.2f}).\n\n"
                    f"Le seuil représente le minimum à payer pour accéder aux examens.\n"
                    f"Les frais totaux sont le montant complèt à payer dans l'année.\n\n"
                    f"Veuillez corriger les valeurs."
                )
                return
            
            if not academic_year_id:
                messagebox.showerror("Erreur", "Aucune année académique active")
                return
            
            # Récupérer l'année pour avoir partial_valid_days
            active_year = self.academic_year_service.get_active_year()
            partial_valid_days = active_year.get('partial_valid_days', 30) if active_year else 30
            
            # Mettre à jour
            self.finance_service.update_financial_thresholds(
                academic_year_id=academic_year_id, threshold_amount=new_threshold, final_fee=new_fee, partial_valid_days=partial_valid_days
            )
            
            channel_status = self.notification_service.get_channel_status()
            email_ok = channel_status.get("email_configured")
            whatsapp_ok = channel_status.get("whatsapp_configured")
            notif_line = "Notifications envoyées via Email et WhatsApp."
            if not email_ok and not whatsapp_ok:
                notif_line = "Notifications non envoyées (Email/WhatsApp non configurés)."
            elif not email_ok:
                notif_line = "Notifications envoyées via WhatsApp uniquement (Email non configuré)."
            elif not whatsapp_ok:
                notif_line = "Notifications envoyées via Email uniquement (WhatsApp non configuré)."

            messagebox.showinfo("Succès", f"Seuils mis à jour avec succès!\n\n"
                              f"Nouveau seuil: ${float(new_threshold_usd):,.2f}\n"
                              f"Nouveaux frais: ${float(new_fee_usd):,.2f}\n\n"
                              f"{notif_line}")
            
            # Recharger la vue en cours (rafraîchissement automatique)
            self._render_current_view()
            
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Veuillez entrer des montants valides (nombres)")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour: {str(e)}")
            logger.error(f"Error updating thresholds: {e}")
    
    def _preview_notifications(self, new_threshold_str, new_fee_str):
        """Affiche une prévisualisation des notifications avec exemple d'étudiant"""
        try:
            new_threshold = float(new_threshold_str) if new_threshold_str.strip() else 300
            new_fee = float(new_fee_str) if new_fee_str.strip() else 500
            
            # Récupérer un étudiant d'exemple pour la prévisualisation
            students = self.student_service.get_students_by_promotion(1)
            example_student = students[0] if students else None
            
            student_name = example_student.get("firstname", "Jean") if example_student else "Jean"
            student_phone = example_student.get("phone_number", "+243...") if example_student else "+243..."
            
            active_year = self.academic_year_service.get_active_year()
            old_threshold = float(active_year.get("threshold_amount") or 300) if active_year else 300
            old_fee = float(active_year.get("final_fee") or 500) if active_year else 500
            
            preview_window = ctk.CTkToplevel(self)
            preview_window.title("📢 Prévisualisation des Notifications")
            preview_window.geometry("700x600")
            preview_window.grab_set()
            preview_window.resizable(True, True)
            self._animate_window_open(preview_window)
            
            # Header
            ctk.CTkLabel(
                preview_window, text="📧 EMAIL NOTIFICATION", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
            ).pack(anchor="w", padx=20, pady=(15, 10))
            
            # Email content frame
            email_frame = ctk.CTkFrame(preview_window, fg_color=self.colors["border"], corner_radius=8)
            email_frame.pack(fill="both", padx=20, pady=(0, 15), expand=False)
            
            email_content = (
                f"De: noreply@uor.rw\n"
                f"À: {student_name}@example.com\n"
                f"Sujet: ⚠️ Mise à jour - Seuils Financiers pour Accès aux Examens\n\n"
                f"{'─' * 60}\n\n"
                f"Bonjour {student_name},\n\n"
                f"Ceci est une notification importante concernant votre \n"
                f"accès aux examens.\n\n"
                f"📊 CHANGE DE SEUILS DÉTECTÉE:\n\n"
                f"  • Ancien seuil: ${old_threshold:,.2f}\n"
                f"  • Nouveau seuil: ${new_threshold:,.2f}\n"
                f"  • Anciens frais: ${old_fee:,.2f}\n"
                f"  • Nouveaux frais: ${new_fee:,.2f}\n\n"
                f"⚠️  IMPORTANT:\n"
                f"Si vous aviez un code d'accès temporaire (paiement partiel),\n"
                f"celui-ci a été annulé et doit être renouvelé.\n\n"
                f"📝 ACTION REQUISE:\n"
                f"Veuillez vous connecter à votre compte pour vérifier\n"
                f"votre statut de paiement.\n\n"
                f"Questions? Contactez l'administration U.O.R.\n\n"
                f"Cordialement,\n"
                f"L'équipe U.O.R - Accès aux Examens"
            )
            
            email_label = ctk.CTkLabel(
                email_frame, text=email_content, font=ctk.CTkFont(size=10, family="Courier"), text_color=self.colors["text_dark"], justify="left"
            )
            email_label.pack(anchor="w", padx=15, pady=15)
            
            # Divider
            ctk.CTkLabel(
                preview_window, text="", font=ctk.CTkFont(size=3)
            ).pack()
            
            # WhatsApp section
            ctk.CTkLabel(
                preview_window, text="💬 MESSAGE WHATSAPP", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
            ).pack(anchor="w", padx=20, pady=(10, 10))
            
            # WhatsApp content frame (bubble style)
            whatsapp_frame = ctk.CTkFrame(preview_window, fg_color=self.colors["info"], corner_radius=12)
            whatsapp_frame.pack(fill="both", padx=20, pady=(0, 15), expand=False)
            
            whatsapp_content = (
                f"🔔 U.O.R - ALERTE SEUILS FINANCIERS\n\n"
                f"Bonjour {student_name},\n\n"
                f"Les seuils d'accès aux examens ont changé:\n\n"
                f"❌ Ancien: ${old_threshold:,.2f}\n"
                f"✅ Nouveau: ${new_threshold:,.2f}\n\n"
                f"Frais complets: ${new_fee:,.2f}\n\n"
                f"⚠️ Les codes d'accès temporaires ont été annulés.\n\n"
                f"Gérez votre paiement sur le portail."
            )
            
            whatsapp_label = ctk.CTkLabel(
                whatsapp_frame, text=whatsapp_content, font=ctk.CTkFont(size=10), text_color=self.colors["text_white"], justify="left"
            )
            whatsapp_label.pack(anchor="w", padx=12, pady=12)
            
            # Close button
            ctk.CTkButton(
                preview_window, text="Fermer", fg_color=self.colors["primary"], hover_color="#2563eb", command=preview_window.destroy
            ).pack(pady=(0, 15), padx=20, fill="x")
            
        except (ValueError, TypeError):
            messagebox.showerror("Erreur", "Veuillez entrer des montants valides (nombres)")
    
    # ==================== EXAM PERIODS MANAGEMENT ====================
    
    def _show_exam_periods(self):
        """Vue dédiée et responsif pour gérer les périodes d'examens"""
        self.current_view = "exam_periods"
        self._persist_ui_context(view=self.current_view)
        self._clear_content()
        self._update_nav_buttons("academic_years")
        self.title_label.configure(text="📅 Gestion des Périodes d'Examens")
        self.subtitle_label.configure(text="Créez et organisez les sessions d'examen pour l'année académique")

        back_row = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        back_row.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(
            back_row,
            text="⬅ Retour à Années Académiques",
            fg_color=self.colors["border"],
            hover_color=self.colors["hover"],
            text_color=self.colors["text_dark"],
            width=240,
            height=34,
            corner_radius=8,
            command=lambda: self._run_with_loading(self._show_academic_years),
        ).pack(side="left")
        
        active_year = self.academic_year_service.get_active_year()
        if not active_year:
            ctk.CTkLabel(
                self.content_frame, text="❌ Aucune année académique active", 
                font=ctk.CTkFont(size=14), text_color=self.colors["danger"]
            ).pack(pady=30)
            return
        
        # Déterminer layout responsif
        self.update_idletasks()
        content_width = self.content_frame.winfo_width() if self.content_frame else 800
        is_compact = content_width < 900
        
        # === CARD 1: Formulaire d'ajout ===
        form_card = self._create_card(self.content_frame)
        form_card.pack(fill="x", padx=0, pady=(0, 15))
        
        ctk.CTkLabel(
            form_card, text="➕ Ajouter une Période d'Examen", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Formulaire adaptif
        form_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        if is_compact:
            # Layout vertical sur petit écran
            ctk.CTkLabel(form_frame, text="Nom de la période:", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(anchor="w", pady=(0, 3))
            period_name_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: Session 1 - Janvier 2026", width=300)
            period_name_entry.pack(fill="x", pady=(0, 10))
            
            date_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            date_frame.pack(fill="x", pady=(0, 10))
            
            ctk.CTkLabel(date_frame, text="Date début:", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(anchor="w", pady=(0, 3))
            start_entry = ctk.CTkEntry(date_frame, placeholder_text="AAAA-MM-JJ", width=150)
            start_entry.pack(side="left", padx=(0, 10))
            
            ctk.CTkLabel(date_frame, text="Date fin:", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]).pack(anchor="w", side="left", padx=(10, 0), pady=(0, 3))
            end_entry = ctk.CTkEntry(date_frame, placeholder_text="AAAA-MM-JJ", width=150)
            end_entry.pack(side="left", padx=(0, 10))
        else:
            # Layout horizontal sur grand écran
            ctk.CTkLabel(form_frame, text="Nom:", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left", padx=(0, 10))
            period_name_entry = ctk.CTkEntry(form_frame, placeholder_text="Ex: Session 1 - Janvier 2026", width=250)
            period_name_entry.pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(form_frame, text="Début:", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left", padx=(0, 10))
            start_entry = ctk.CTkEntry(form_frame, placeholder_text="AAAA-MM-JJ", width=130)
            start_entry.pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(form_frame, text="Fin:", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]).pack(side="left", padx=(0, 10))
            end_entry = ctk.CTkEntry(form_frame, placeholder_text="AAAA-MM-JJ", width=130)
            end_entry.pack(side="left", padx=(0, 20))
        
        def add_exam_period():
            name = period_name_entry.get().strip()
            start_str = start_entry.get().strip()
            end_str = end_entry.get().strip()
            
            if not all([name, start_str, end_str]):
                messagebox.showerror("Erreur", "Tous les champs sont requis.")
                return
            
            try:
                start_dt = datetime.strptime(start_str, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_str, "%Y-%m-%d").date()
                if end_dt < start_dt:
                    messagebox.showerror("Erreur", "La date de fin doit être après le début.")
                    return
            except ValueError:
                messagebox.showerror("Erreur", "Format de date invalide. Utilisez AAAA-MM-JJ")
                return
            
            # Ajouter la période et notifier les étudiants
            success = self.academic_year_service.add_exam_period(
                active_year['academic_year_id'], name, start_dt, end_dt
            )
            
            if success:
                # Afficher dialogue de progression
                progress_dialog = ctk.CTkToplevel(self)
                progress_dialog.title("📬 Envoi des Notifications")
                progress_dialog.geometry("400x150")
                progress_dialog.grab_set()
                progress_dialog.resizable(False, False)
                self._animate_window_open(progress_dialog)
                
                ctk.CTkLabel(
                    progress_dialog, text="📬 Envoi des notifications aux étudiants...",
                    font=ctk.CTkFont(size=12, weight="bold")
                ).pack(pady=20)
                
                progress_bar = ctk.CTkProgressBar(progress_dialog, width=350)
                progress_bar.pack(pady=10, padx=25)
                progress_bar.set(0)
                
                status_label = ctk.CTkLabel(
                    progress_dialog, text="Initialisation...",
                    font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
                )
                status_label.pack(pady=10)
                
                progress_dialog.update()
                
                # Variables pour stocker les résultats
                notification_result = {'result': None}

                def _update_progress_ui(msg, val):
                    try:
                        if progress_dialog.winfo_exists():
                            status_label.configure(text=msg)
                            progress_bar.set(val)
                    except Exception:
                        pass
                
                def send_notifications_background():
                    """Envoyer les notifications dans un thread séparé"""
                    try:
                        def _safe_progress(msg, val):
                            try:
                                self.after(0, lambda m=msg, v=val: _update_progress_ui(m, v))
                            except Exception:
                                pass

                        result = self._notify_students_exam_period_sync(
                            period_name=name,
                            start_date=start_dt,
                            end_date=end_dt,
                            academic_year_id=active_year['academic_year_id'],
                            progress_callback=_safe_progress
                        )
                        notification_result['result'] = result
                    except Exception as e:
                        logger.error(f"❌ Erreur notifications background: {e}")
                        notification_result['result'] = {'error': str(e)}
                
                # Lancer dans un thread séparé pour ne pas bloquer l'UI
                import threading
                notification_thread = threading.Thread(target=send_notifications_background, daemon=True)
                notification_thread.start()
                
                # Attendre dans une boucle non-bloquante
                def wait_for_notifications():
                    if notification_thread.is_alive():
                        progress_dialog.after(100, wait_for_notifications)
                    else:
                        progress_dialog.destroy()
                        
                        result = notification_result['result']
                        if result and 'error' not in result:
                            # Afficher résumé
                            if result['total'] > 0:
                                messagebox.showinfo(
                                    "Résumé des Notifications",
                                    f"Période: {name}\n\n"
                                    f"✅ Notifiés: {result['notified']}/{result['total']}\n"
                                    f"🎓 Étudiants éligibles: {result.get('eligible', 0)}\n"
                                    f"📧 Avec code: {result['with_code']}\n"
                                    f"💬 Paiement reçu (sans code): {result.get('paid_no_code',0)}\n"
                                    f"❌ Non payés: {result.get('unpaid',0)}\n"
                                    f"⏭️  Sans contact: {result['skipped']}\n\n"
                                    f"Messages: {result['messages']}"
                                )
                            else:
                                messagebox.showinfo(
                                    "Résumé des Notifications",
                                    f"Période: {name}\n\nAucun étudiant à notifier.\n{result['messages']}"
                                )
                        else:
                            messagebox.showerror(
                                "Erreur Notifications",
                                f"Une erreur s'est produite:\n{result.get('error', 'Erreur inconnue')}" if result else "Erreur inconnue"
                            )
                        
                        # Nettoyer et rafraîchir la liste
                        period_name_entry.delete(0, "end")
                        start_entry.delete(0, "end")
                        end_entry.delete(0, "end")
                        self._show_exam_periods()  # Rafraîchir la liste
                
                wait_for_notifications()
            else:
                messagebox.showerror("Erreur", "Impossible d'ajouter la période.")
        
        button_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkButton(
            button_frame, text="✅ Valider & Notifier", fg_color=self.colors["primary"],
            hover_color=self.colors["info"], text_color=self.colors["text_white"],
            height=40, corner_radius=8, command=add_exam_period
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_frame, text="❌ Annuler", fg_color=self.colors["danger"],
            hover_color="#dc2626", text_color=self.colors["text_white"],
            height=40, corner_radius=8, 
            command=lambda: self._run_with_loading(self._show_academic_years)
        ).pack(side="left")
        
        # === CARD 2: Liste des périodes ===
        list_card = self._create_card(self.content_frame)
        list_card.pack(fill="both", expand=True, padx=0)
        
        ctk.CTkLabel(
            list_card, text="📋 Périodes Actuelles", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        exam_periods = self.academic_year_service.get_exam_periods(active_year['academic_year_id'])
        
        if exam_periods:
            scroll_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
            scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            
            for period in exam_periods:
                start = datetime.strptime(str(period['start_date']), "%Y-%m-%d")
                end = datetime.strptime(str(period['end_date']), "%Y-%m-%d")
                duration = (end - start).days
                
                period_frame = ctk.CTkFrame(scroll_frame, fg_color=self.colors["hover"], corner_radius=12)
                period_frame.pack(fill="x", pady=8)
                
                info_frame = ctk.CTkFrame(period_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=15, pady=12)
                
                ctk.CTkLabel(
                    info_frame, text=period['period_name'], 
                    font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
                ).pack(anchor="w")
                
                date_info = f"📅 {start.strftime('%d/%m/%Y')} → {end.strftime('%d/%m/%Y')} ({duration} jours)"
                ctk.CTkLabel(
                    info_frame, text=date_info, 
                    font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
                ).pack(anchor="w", pady=(5, 0))
        else:
            ctk.CTkLabel(
                list_card, text="Aucune période d'examen définie pour cette année.",
                font=ctk.CTkFont(size=12), text_color=self.colors["text_light"]
            ).pack(pady=40)
    
    def _notify_students_exam_period_sync(self, period_name: str, start_date, end_date, academic_year_id: int, progress_callback=None):
        """Notifie TOUS les étudiants. Code d'accès seulement pour ceux qui ont payé. OPTIMISÉ pour rapidité."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        result = {
            'total': 0, 'notified': 0, 'skipped': 0,
            'with_code': 0, 'paid_no_code': 0, 'eligible': 0, 'unpaid': 0,
            'messages': ""
        }
        
        try:
            if progress_callback:
                progress_callback("Récupération des étudiants...", 0.2)
            
            students_list = self.student_service.get_all_students_with_finance()
            if not students_list:
                result['messages'] = "Aucun étudiant en base de données"
                return result
            
            result['total'] = len(students_list)
            
            if progress_callback:
                progress_callback(f"Préparation des notifications... (0/{result['total']})", 0.25)
            
            # Préparer les données pour envoi paralléle
            notifs_to_send = []
            skipped_count = 0
            with_code_count = 0
            paid_no_code_count = 0
            unpaid_count = 0
            
            for idx, student in enumerate(students_list):
                student_id = student.get('student_id') or student.get('id')
                email = student.get('email', '').strip()
                phone = student.get('phone_number', '').strip()

                if progress_callback and result['total'] > 0:
                    prep_prog = (idx + 1) / result['total']
                    progress_callback(
                        f"Préparation des notifications... ({idx + 1}/{result['total']})",
                        0.25 + 0.30 * prep_prog,
                    )
                
                if not email and not phone:
                    skipped_count += 1
                    continue
                
                # Vérifier état financier et code d'accès
                has_valid_code = False
                code_value = None
                code_text = None
                paid = False
                
                # déterminer si l'étudiant a déjà payé le seuil
                # (priorité à la valeur préchargée, fallback service finance)
                raw_eligible = student.get('is_eligible')
                if raw_eligible is not None:
                    try:
                        if isinstance(raw_eligible, str):
                            paid = raw_eligible.strip().lower() in {"1", "true", "yes", "oui"}
                        else:
                            paid = bool(int(raw_eligible))
                    except Exception:
                        paid = bool(raw_eligible)
                elif student_id is not None:
                    try:
                        paid = self.finance_service.is_threshold_reached(student_id)
                    except Exception:
                        paid = False
                
                if student_id is not None:
                    try:
                        access_code = self.finance_service.get_latest_access_code(student_id)
                    except Exception:
                        access_code = None
                else:
                    access_code = None
                
                # NOTE PERF: on n'émet plus de nouveau code ici pour éviter les blocages UI
                # lors des envois en masse. Si aucun code existe encore, on notifie "code à venir".
                
                if access_code:
                    code_type = access_code.get('access_type', 'unknown')
                    code_value = access_code.get('access_code')
                    expires = access_code.get('expires_at')
                    
                    if code_type == 'full':
                        has_valid_code = True
                        code_text = "Valide toute l'année"
                    elif code_type == 'partial' and expires:
                        try:
                            if isinstance(expires, str):
                                expires_dt = datetime.strptime(expires, "%Y-%m-%d").date()
                            else:
                                expires_dt = expires.date() if hasattr(expires, 'date') else expires
                            
                            if expires_dt >= start_date:
                                has_valid_code = True
                                code_text = f"Jusqu'au {expires_dt.strftime('%d/%m/%Y')}"
                        except:
                            pass
                
                # Construire messages
                student_name = f"{student.get('firstname', '').strip()} {student.get('lastname', '').strip()}".strip() or f"Étudiant {student_id}"
                
                if has_valid_code and code_value:
                    email_subject = f"📅 Nouvelle Période d'Examen: {period_name}"
                    email_body = f"""Bonjour {student_name},\n\nPériode d'examen confirmée: {period_name}\nDates: {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n\n🔐 Votre code d'accès: {code_value}\n({code_text})\n\nConservez ce code précieusement!\n\nU.O.R - Administration"""
                    whatsapp_msg = f"🔔 *Période d'examen confirmée*\n{period_name}\n📅 {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n\n🔐 Code: `{code_value}`\n({code_text})\n\nU.O.R"
                    with_code_count += 1
                elif paid:
                    # payé mais aucun code (rare)
                    email_subject = f"📅 Période d'Examen: {period_name} - Paiement reçu"
                    email_body = f"""Bonjour {student_name},\n\nMerci pour votre paiement.\nLa période d'examen {period_name} est confirmée:\n{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n\nVotre code d'accès sera envoyé sous peu.\n\nU.O.R - Administration"""
                    whatsapp_msg = f"📅 Période d'examen: {period_name}\n{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n\n✓ Paiement reçu, code à venir\n\nU.O.R"
                    paid_no_code_count += 1
                else:
                    # pas payé
                    email_subject = f"📅 Période d'Examen: {period_name} - ACTION REQUISE"
                    email_body = f"""Bonjour {student_name},\n\nPériode d'examen confirmée: {period_name}\nDates: {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n\n❌ Vous n'avez pas d'accès actuellement.\n\n📝 Régularisez votre paiement pour recevoir un code d'accès.\n\nU.O.R - Administration"""
                    whatsapp_msg = f"📅 Période d'examen: {period_name}\n{start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n\n❌ Régularisez votre paiement pour l'accès\n\nU.O.R"
                    unpaid_count += 1
                
                notifs_to_send.append({
                    'email': email,
                    'phone': phone,
                    'email_subject': email_subject,
                    'email_body': email_body,
                    'whatsapp_msg': whatsapp_msg
                })
            
            result['skipped'] = skipped_count
            result['with_code'] = with_code_count
            result['paid_no_code'] = paid_no_code_count
            result['eligible'] = with_code_count + paid_no_code_count
            result['unpaid'] = unpaid_count
            
            # Envoyer les notifications en parallèle
            notified_count = 0
            if progress_callback:
                progress_callback(f"Envoi des notifications... (0/{len(notifs_to_send)})", 0.58)
            # utiliser autant de threads que de notifications pour maximiser la vitesse
            max_workers = min(len(notifs_to_send), 20) or 1
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(self._send_notification, notif) for notif in notifs_to_send]

                # Attendre et compter
                for i, future in enumerate(as_completed(futures)):
                    try:
                        if future.result():
                            notified_count += 1
                    except:
                        pass

                    # Callback progression toutes les 5% seulement
                    if progress_callback and len(futures) > 0:
                        prog = (i + 1) / len(futures)
                        if prog % 0.05 < 0.01 or i == len(futures) - 1:
                            progress = 0.58 + 0.40 * prog
                            progress_callback(f"Envoi... ({i + 1}/{len(futures)})", progress)
            
            result['notified'] = notified_count
            result['messages'] = "Notifications envoyées avec succès"
            
        except Exception as e:
            result['messages'] = f"Erreur: {str(e)}"
        
        return result
    
    def _send_notification(self, notif_data):
        """Envoie une notification (email et/ou WhatsApp). Appelé en parallèle."""
        try:
            sent = False
            
            if notif_data['email']:
                try:
                    if self.notification_service._send_email(
                        notif_data['email'],
                        notif_data['email_subject'],
                        notif_data['email_body']
                    ):
                        sent = True
                except:
                    pass
            
            if notif_data['phone']:
                try:
                    if self.notification_service._send_whatsapp(
                        notif_data['phone'],
                        notif_data['whatsapp_msg']
                    ):
                        sent = True
                except:
                    pass
            
            return sent
        except:
            return False
    
    def _notify_students_exam_period(self, period_name: str, start_date, end_date, academic_year_id: int):
        """Notifie les étudiants en arrière-plan (legacy, maintenant synchrone par défaut)"""
        # Maintenu pour compatibilité, appelle la version synchrone
        self._notify_students_exam_period_sync(period_name, start_date, end_date, academic_year_id)
    
    # ==================== STUDENT ACADEMIC DATA ====================
    
    def _show_student_academic_data(self):
        """Affiche l'interface de gestion des données académiques avec sélection hiérarchique"""
        if not self._can_access_view("academic_data"):
            self._handle_forbidden_view("academic_data")
            return
        self.current_view = "academic_data"
        self._persist_ui_context(view=self.current_view)
        self._set_main_scrollbar_visible(True)
        self._update_nav_buttons("academic_data")
        self.title_label.configure(text="📝 Gestion des Données Académiques")
        self._clear_content()
        
        # Initialiser les variables de sélection
        if not hasattr(self, 'academic_state'):
            self.academic_state = {
                'faculty_id': None, 'department_id': None, 'promotion_id': None, 'selected_student': None, 'filtered_students': []
            }
        
        # Container
        container = ctk.CTkScrollableFrame(
            self.content_frame, scrollbar_button_color=self.colors["border"]
        )
        container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = ctk.CTkFrame(container, fg_color=self.colors["primary"], corner_radius=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        ctk.CTkLabel(
            header_frame, text="📚 Ajouter les Données Académiques par Étudiant", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_white"], justify="center"
        ).pack(anchor="center", fill="x", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(
            header_frame, text="Gestion des notes, documents et certificats pour chaque étudiant", font=ctk.CTkFont(size=11), text_color="#e8f4ff", justify="center"
        ).pack(anchor="center", fill="x", padx=20, pady=(0, 15))
        
        # Content frame
        content = ctk.CTkFrame(container)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ==== LEFT COLUMN: Selection & Student Info ====
        left_column = ctk.CTkFrame(content)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # ---- CARD 1: Sélection Hiérarchique ----
        selection_card = ctk.CTkFrame(left_column, fg_color=self.colors["card_bg"], corner_radius=12)
        selection_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            selection_card, text="1️⃣ Sélectionner un Étudiant", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Sous-section: Hierarchie
        hierarchy_frame = ctk.CTkFrame(selection_card)
        hierarchy_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # FACULTÉ
        ctk.CTkLabel(
            hierarchy_frame, text="Faculté *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        faculty_options = self._get_academic_faculties()
        faculty_names = [f['name'] for f in faculty_options]
        
        self.academic_faculty_combo = ctk.CTkComboBox(
            hierarchy_frame, values=faculty_names if faculty_names else ["Aucune faculté"], height=36, font=ctk.CTkFont(size=10), command=self._on_academic_faculty_selected
        )
        self.academic_faculty_combo.pack(fill="x", pady=(0, 12))
        if faculty_names:
            self.academic_faculty_combo.set(faculty_names[0])
            self.academic_state['faculty_id'] = next((f['id'] for f in faculty_options if f['name'] == faculty_names[0]), None)
        
        # DÉPARTEMENT
        ctk.CTkLabel(
            hierarchy_frame, text="Département *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.academic_dept_combo = ctk.CTkComboBox(
            hierarchy_frame, values=["Sélectionnez une faculté d'abord"], height=36, font=ctk.CTkFont(size=10), command=self._on_academic_department_selected
        )
        self.academic_dept_combo.pack(fill="x", pady=(0, 12))
        
        # PROMOTION
        ctk.CTkLabel(
            hierarchy_frame, text="Promotion *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.academic_promotion_combo = ctk.CTkComboBox(
            hierarchy_frame, values=["Sélectionnez un département d'abord"], height=36, font=ctk.CTkFont(size=10), command=self._on_academic_promotion_selected
        )
        self.academic_promotion_combo.pack(fill="x", pady=(0, 12))
        
        # RECHERCHE ÉTUDIANT
        ctk.CTkLabel(
            hierarchy_frame, text="Rechercher un Étudiant", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        self.academic_search_entry = ctk.CTkEntry(
            hierarchy_frame, placeholder_text="Nom, prénom ou numéro d'étudiant...", height=36, font=ctk.CTkFont(size=10)
        )
        self.academic_search_entry.pack(fill="x", pady=(0, 12))
        self.academic_search_entry.bind("<KeyRelease>", self._on_academic_search_changed)
        
        # ---- CARD 2: Liste des Étudiants ----
        students_list_card = ctk.CTkFrame(left_column, fg_color=self.colors["card_bg"], corner_radius=12)
        students_list_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            students_list_card, text="📋 Étudiants de la Promotion", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(10, 8))
        
        # Scrollable list
        self.academic_students_scroll = ctk.CTkScrollableFrame(
            students_list_card, fg_color=self.colors["hover"], corner_radius=8, scrollbar_button_color=self.colors["border"], width=300, height=120
        )
        self.academic_students_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # ---- CARD 3: Infos de l'étudiant sélectionné ----
        info_card = ctk.CTkFrame(left_column, fg_color=self.colors["hover"], corner_radius=12)
        info_card.pack(fill="x", pady=(0, 15))
        
        self.academic_info_frame = ctk.CTkFrame(info_card)
        self.academic_info_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(
            self.academic_info_frame, text="Aucun étudiant sélectionné", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_light"]
        ).pack(anchor="w")
        
        # ---- CARD 4: Données Académiques Ajoutées ----
        self.academic_data_card = ctk.CTkFrame(left_column, fg_color=self.colors["card_bg"], corner_radius=12)
        self.academic_data_card.pack(fill="x", pady=(0, 0))
        
        ctk.CTkLabel(
            self.academic_data_card, text="📊 Données Académiques Existantes", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        self.academic_display_frame = ctk.CTkFrame(self.academic_data_card)
        self.academic_display_frame.pack(fill="both", expand=True, padx=15, pady=(0, 12))
        
        ctk.CTkLabel(
            self.academic_display_frame, text="Les données s'afficheront ici...", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
        ).pack(pady=10)
        
        # ==== RIGHT COLUMN: Forms ====
        right_column = ctk.CTkFrame(content)
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Tabs for different data types
        ctk.CTkLabel(
            right_column, text="2️⃣ Ajouter les Données", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 10))
        
        tabs_frame = ctk.CTkFrame(right_column, fg_color=self.colors["card_bg"], corner_radius=12)
        tabs_frame.pack(fill="both", expand=True)
        
        # Tab buttons
        tab_btn_frame = ctk.CTkFrame(tabs_frame)
        tab_btn_frame.pack(fill="x", padx=15, pady=(15, 0))
        
        self.academic_active_tab = "grades"
        self.academic_tab_buttons = []
        
        tab_configs = [
            ("grades", "📊 Ajouter une Note"), ("documents", "📄 Ajouter un Document"), ]
        
        for tab_key, tab_label in tab_configs:
            btn = ctk.CTkButton(
                tab_btn_frame, text=tab_label, fg_color=self.colors["primary"] if tab_key == "grades" else "transparent", hover_color=self.colors["primary"], text_color=self.colors["text_white"] if tab_key == "grades" else self.colors["text_dark"], height=40, font=ctk.CTkFont(size=12, weight="bold"), command=lambda k=tab_key: self._switch_academic_tab(k, tabs_frame)
            )
            btn.pack(side="left", padx=3, expand=True, fill="x")
            self.academic_tab_buttons.append({"button": btn, "key": tab_key})
        
        # Tab content container
        self.academic_tab_content = ctk.CTkFrame(tabs_frame)
        self.academic_tab_content.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Show initial tab
        self._show_academic_grades_form()
    
    # ========== MÉTHODES DE CHARGEMENT HIÉRARCHIQUE ==========
    
    def _get_academic_faculties(self):
        """Récupère les facultés actives"""
        try:
            return self.student_service.get_faculties()
        except Exception as e:
            logger.error(f"Erreur chargement facultés: {e}")
            return []
    
    def _on_academic_faculty_selected(self, faculty_name):
        """Callback lors de la sélection d'une faculté"""
        try:
            faculties = self._get_academic_faculties()
            faculty = next((f for f in faculties if f['name'] == faculty_name), None)
            
            if not faculty:
                return
            
            self.academic_state['faculty_id'] = faculty['id']
            self.academic_state['department_id'] = None
            self.academic_state['promotion_id'] = None
            self.academic_state['selected_student'] = None
            self.academic_state['filtered_students'] = []
            
            # Charger départements
            departments = self.student_service.get_departments_by_faculty(faculty['id'])
            dept_names = [d['name'] for d in departments]
            
            if dept_names:
                self.academic_dept_combo.configure(values=dept_names)
                self.academic_dept_combo.set(dept_names[0])
                self._on_academic_department_selected(dept_names[0])
            else:
                self.academic_dept_combo.configure(values=["Aucun département"])
                self.academic_dept_combo.set("Aucun département")
                self.academic_promotion_combo.configure(values=["Aucune promotion"])
                self._clear_academic_students_list()
        except Exception as e:
            logger.error(f"Erreur sélection faculté: {e}")
    
    def _on_academic_department_selected(self, dept_name):
        """Callback lors de la sélection d'un département"""
        try:
            if not self.academic_state['faculty_id'] or dept_name == "Aucun département":
                return
            
            faculties = self._get_academic_faculties()
            faculty = next((f for f in faculties if f['id'] == self.academic_state['faculty_id']), None)
            
            if not faculty:
                return
            
            departments = self.student_service.get_departments_by_faculty(faculty['id'])
            dept = next((d for d in departments if d['name'] == dept_name), None)
            
            if not dept:
                return
            
            self.academic_state['department_id'] = dept['id']
            self.academic_state['promotion_id'] = None
            self.academic_state['selected_student'] = None
            self.academic_state['filtered_students'] = []
            
            # Charger promotions
            promotions = self.student_service.get_promotions_by_department(dept['id'])
            promo_names = [f"{p['name']} ({p['year']})" for p in promotions]
            
            if promo_names:
                self.academic_promotion_combo.configure(values=promo_names)
                self.academic_promotion_combo.set(promo_names[0])
                self._on_academic_promotion_selected(promo_names[0])
            else:
                self.academic_promotion_combo.configure(values=["Aucune promotion"])
                self.academic_promotion_combo.set("Aucune promotion")
                self._clear_academic_students_list()
        except Exception as e:
            logger.error(f"Erreur sélection département: {e}")
    
    def _on_academic_promotion_selected(self, promo_name):
        """Callback lors de la sélection d'une promotion"""
        try:
            if not self.academic_state['department_id'] or promo_name == "Aucune promotion":
                self._clear_academic_students_list()
                return
            
            departments = self.student_service.get_departments_by_faculty(self.academic_state['faculty_id'])
            dept = next((d for d in departments if d['id'] == self.academic_state['department_id']), None)
            
            if not dept:
                return
            
            promotions = self.student_service.get_promotions_by_department(dept['id'])
            promo = next((p for p in promotions if f"{p['name']} ({p['year']})" == promo_name), None)
            
            if not promo:
                return
            
            self.academic_state['promotion_id'] = promo['id']
            self.academic_state['selected_student'] = None
            
            # Charger les étudiants de cette promotion
            self._update_academic_students_list()
        except Exception as e:
            logger.error(f"Erreur sélection promotion: {e}")
    
    def _update_academic_students_list(self):
        """Met à jour la liste des étudiants de la promotion"""
        try:
            students = self._get_academic_students_by_promotion()
            self.academic_state['filtered_students'] = students
            
            # Vider la liste
            self._clear_academic_students_list()
            
            # Remplir avec les nouveaux étudiants
            if students:
                for student in students:
                    self._create_academic_student_button(student)
            else:
                ctk.CTkLabel(
                    self.academic_students_scroll, text="Aucun étudiant", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
                ).pack(pady=20)
        except Exception as e:
            logger.error(f"Erreur mise à jour liste étudiants: {e}")
    
    def _get_academic_students_by_promotion(self, search_text=""):
        """Récupère les étudiants de la promotion active"""
        try:
            if not self.academic_state['promotion_id']:
                return []
            
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            query = """
                SELECT s.id, s.student_number, s.firstname, s.lastname, s.email, s.promotion_id, p.name as promotion_name
                FROM student s
                JOIN promotion p ON s.promotion_id = p.id
                WHERE s.promotion_id = %s AND s.is_active = 1
                ORDER BY s.lastname, s.firstname
            """
            
            students = conn.execute_query(query, (self.academic_state['promotion_id'],))
            
            # Filtrer par recherche si nécessaire
            if search_text.strip():
                search_lower = search_text.lower().strip()
                students = [s for s in students if (
                    search_lower in f"{s['firstname']} {s['lastname']}".lower() or
                    search_lower in s['student_number'].lower() or
                    search_lower in (s.get('email', '') or '').lower()
                )]
            
            return students
        except Exception as e:
            logger.error(f"Erreur récupération étudiants: {e}")
            return []
    
    def _on_academic_search_changed(self, event=None):
        """Callback lors de la saisie de recherche"""
        try:
            search_text = self.academic_search_entry.get()
            students = self._get_academic_students_by_promotion(search_text)
            self.academic_state['filtered_students'] = students
            
            # Vider et remplir la liste
            self._clear_academic_students_list()
            
            if students:
                for student in students:
                    self._create_academic_student_button(student)
            else:
                ctk.CTkLabel(
                    self.academic_students_scroll, text="Aucun étudiant trouvé", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
                ).pack(pady=20)
        except Exception as e:
            logger.error(f"Erreur recherche étudiant: {e}")
    
    def _create_academic_student_button(self, student):
        """Crée un bouton pour afficher un étudiant"""
        try:
            scrollable_frame = getattr(self.academic_students_scroll, "_scrollable_frame", self.academic_students_scroll)
            
            btn_frame = ctk.CTkButton(
                scrollable_frame, text=f"{student['student_number']} - {student['firstname']} {student['lastname']}", fg_color=self.colors["hover"], hover_color=self.colors["primary"], text_color=self.colors["text_dark"], height=32, font=ctk.CTkFont(size=10), command=lambda s=student: self._select_academic_student(s), anchor="w"
            )
            btn_frame.pack(fill="x", padx=5, pady=2)
        except Exception as e:
            logger.error(f"Erreur création bouton étudiant: {e}")
    
    def _clear_academic_students_list(self):
        """Vide la liste des étudiants"""
        try:
            scrollable_frame = getattr(self.academic_students_scroll, "_scrollable_frame", self.academic_students_scroll)
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
        except Exception as e:
            logger.error(f"Erreur nettoyage liste: {e}")
    
    def _select_academic_student(self, student):
        """Sélectionne un étudiant et affiche ses infos"""
        try:
            self.academic_state['selected_student'] = student
            self._display_academic_student_info(student)
        except Exception as e:
            logger.error(f"Erreur sélection étudiant: {e}")
    
    def _display_academic_student_info(self, student):
        """Affiche les infos élargis de l'étudiant avec les données académiques"""
        try:
            # Vider le frame d'infos
            for widget in self.academic_info_frame.winfo_children():
                widget.destroy()
            
            info_frame = ctk.CTkFrame(self.academic_info_frame)
            info_frame.pack(fill="x", padx=0, pady=0)
            
            # Infos de base
            ctk.CTkLabel(
                info_frame, text=f"👤 {student['firstname']} {student['lastname']}", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["primary"]
            ).pack(anchor="w", pady=(0, 3))
            
            ctk.CTkLabel(
                info_frame, text=f"ID: {student['student_number']} | Email: {student.get('email', 'N/A')}", font=ctk.CTkFont(size=9), text_color=self.colors["text_dark"]
            ).pack(anchor="w", pady=(0, 8))
            
            # Afficher les données académiques en bas
            self._display_academic_data_for_student(student)
        except Exception as e:
            logger.error(f"Erreur affichage info étudiant: {e}")
    
    def _display_academic_data_for_student(self, student):
        """Affiche les notes et documents existants de l'étudiant"""
        try:
            # Vider le frame
            for widget in self.academic_display_frame.winfo_children():
                widget.destroy()
            
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            # Récupérer les notes (augmenté à 10 pour plus de contexte)
            grades_query = """
                SELECT * FROM academic_record 
                WHERE student_id = %s 
                ORDER BY exam_date DESC, id DESC LIMIT 10
            """
            grades = conn.execute_query(grades_query, (student['id'],))
            
            # Récupérer les documents (augmenté à 10)
            docs_query = """
                SELECT * FROM student_document 
                WHERE student_id = %s 
                ORDER BY id DESC LIMIT 10
            """
            documents = conn.execute_query(docs_query, (student['id'],))
            
            if not grades and not documents:
                empty_label = ctk.CTkLabel(
                    self.academic_display_frame, text="Aucune donnée académique", font=ctk.CTkFont(size=10), text_color=self.colors["text_light"]
                )
                empty_label.pack(pady=10)
                self.academic_display_frame.update_idletasks()
                return
            
            # Afficher les notes
            if grades:
                grades_header = ctk.CTkLabel(
                    self.academic_display_frame, text="📊 Dernières Notes", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["primary"]
                )
                grades_header.pack(anchor="w", pady=(0, 5))
                
                for grade in grades:
                    grade_text = (
                        f"• {grade.get('course_name', 'N/A')} - "
                        f"{grade.get('grade', 'N/A')}/20 ({grade.get('grade_letter', 'N/A')}) "
                        f"| {grade.get('status', 'N/A')}"
                    )
                    grade_label = ctk.CTkLabel(
                        self.academic_display_frame, text=grade_text, font=ctk.CTkFont(size=9), text_color=self.colors["text_dark"], anchor="w", justify="left"
                    )
                    grade_label.pack(anchor="w", pady=1, padx=5)
            
            # Espace entre sections
            if grades and documents:
                spacer = ctk.CTkLabel(
                    self.academic_display_frame, text="", font=ctk.CTkFont(size=6)
                )
                spacer.pack(pady=3)
            
            # Afficher les documents
            if documents:
                docs_header = ctk.CTkLabel(
                    self.academic_display_frame, text="📄 Documents", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["primary"]
                )
                docs_header.pack(anchor="w", pady=(5, 5) if grades else (0, 5))
                
                for doc in documents:
                    doc_text = f"• {doc.get('document_type', 'N/A')} - {doc.get('title', 'N/A')}"
                    doc_label = ctk.CTkLabel(
                        self.academic_display_frame, text=doc_text, font=ctk.CTkFont(size=9), text_color=self.colors["text_dark"], anchor="w", justify="left"
                    )
                    doc_label.pack(anchor="w", pady=1, padx=5)
            
            # Forcer la mise à jour de l'affichage
            self.academic_display_frame.update_idletasks()
            self.academic_data_card.update_idletasks()
            
        except Exception as e:
            logger.error(f"Erreur affichage données académiques: {e}", exc_info=True)
    
    def _switch_academic_tab(self, tab_key, parent):
        """Change d'onglet dans les données académiques"""
        self.academic_active_tab = tab_key
        
        # Update button colors
        for tab_btn in self.academic_tab_buttons:
            if tab_btn["key"] == tab_key:
                tab_btn["button"].configure(
                    fg_color=self.colors["primary"], text_color=self.colors["text_white"]
                )
            else:
                tab_btn["button"].configure(
                    text_color=self.colors["text_dark"]
                )
        
        # Clear content
        for widget in self.academic_tab_content.winfo_children():
            widget.destroy()
        
        # Show new tab content
        if tab_key == "grades":
            self._show_academic_grades_form()
        elif tab_key == "documents":
            self._show_academic_documents_form()
    
    def _show_academic_grades_form(self):
        """Affiche le formulaire pour ajouter une note"""
        form = ctk.CTkFrame(self.academic_tab_content)
        form.pack(fill="both", expand=True)
        
        # Course name
        ctk.CTkLabel(
            form, text="Nom du Cours *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        course_entry = ctk.CTkEntry(
            form, placeholder_text="Ex: Programmation Python, Algorithmes...", height=40, font=ctk.CTkFont(size=11)
        )
        course_entry.pack(fill="x", pady=(0, 15))
        
        # Code and Credits row
        row1 = ctk.CTkFrame(form)
        row1.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row1)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1, text="Code du Cours", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        code_entry = ctk.CTkEntry(
            col1, placeholder_text="Ex: PRG101", height=40, font=ctk.CTkFont(size=11)
        )
        code_entry.pack(fill="both")
        
        col2 = ctk.CTkFrame(row1)
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2, text="Crédits ECTS", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        credits_entry = ctk.CTkEntry(
            col2, placeholder_text="Ex: 3, 4...", height=40, font=ctk.CTkFont(size=11)
        )
        credits_entry.pack(fill="both")
        
        # Grade row
        row2 = ctk.CTkFrame(form)
        row2.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row2)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1, text="Note (sur 20) *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        grade_entry = ctk.CTkEntry(
            col1, placeholder_text="Ex: 15.5", height=40, font=ctk.CTkFont(size=11)
        )
        grade_entry.pack(fill="both")
        
        col2 = ctk.CTkFrame(row2)
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2, text="Statut", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        status_combo = ctk.CTkComboBox(
            col2, values=["RÉUSSI", "ÉCHOUÉ", "EN COURS"], height=40, font=ctk.CTkFont(size=11)
        )
        status_combo.pack(fill="both")
        status_combo.set("RÉUSSI")
        
        # Semester and Date row
        row3 = ctk.CTkFrame(form)
        row3.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row3)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1, text="Semestre", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        semester_combo = ctk.CTkComboBox(
            col1, values=["1", "2", "Annuel"], height=40, font=ctk.CTkFont(size=11)
        )
        semester_combo.pack(fill="both")
        semester_combo.set("Annuel")
        
        col2 = ctk.CTkFrame(row3)
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2, text="Date d'Examen", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        date_entry = ctk.CTkEntry(
            col2, placeholder_text="YYYY-MM-DD", height=40, font=ctk.CTkFont(size=11)
        )
        date_entry.pack(fill="both")
        
        # Professeur
        ctk.CTkLabel(
            form, text="Professeur", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        professor_entry = ctk.CTkEntry(
            form, placeholder_text="Nom du professeur", height=40, font=ctk.CTkFont(size=11)
        )
        professor_entry.pack(fill="x", pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(form)
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame, text="✅ Ajouter la Note", fg_color=self.colors["success"], hover_color="#059669", height=45, font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self._add_academic_grade(course_entry, code_entry, credits_entry, grade_entry, status_combo, semester_combo, date_entry, professor_entry)
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            btn_frame, text="🔄 Réinitialiser", fg_color="#6b7280", hover_color="#4b5563", height=45, font=ctk.CTkFont(size=12, weight="bold"), command=lambda: [
                course_entry.delete(0, "end"), code_entry.delete(0, "end"), credits_entry.delete(0, "end"), grade_entry.delete(0, "end"), date_entry.delete(0, "end"), professor_entry.delete(0, "end")
            ]
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _show_academic_documents_form(self):
        """Affiche le formulaire pour ajouter un document"""
        form = ctk.CTkFrame(self.academic_tab_content)
        form.pack(fill="both", expand=True)
        
        # Document type
        ctk.CTkLabel(
            form, text="Type de Document *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        doc_type_combo = ctk.CTkComboBox(
            form, values=["LIVRE", "THÈSE", "RAPPORT", "CERTIFICAT", "DIPLÔME", "AUTRE"], height=40, font=ctk.CTkFont(size=11)
        )
        doc_type_combo.pack(fill="x", pady=(0, 15))
        doc_type_combo.set("CERTIFICAT")
        
        # Title
        ctk.CTkLabel(
            form, text="Titre du Document *", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        title_entry = ctk.CTkEntry(
            form, placeholder_text="Ex: Certificat de Complétion, Thèse...", height=40, font=ctk.CTkFont(size=11)
        )
        title_entry.pack(fill="x", pady=(0, 15))
        
        # Category and Author
        row1 = ctk.CTkFrame(form)
        row1.pack(fill="x", pady=(0, 15))
        
        col1 = ctk.CTkFrame(row1)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(
            col1, text="Catégorie", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        category_entry = ctk.CTkEntry(
            col1, placeholder_text="Ex: Sciences, Littérature", height=40, font=ctk.CTkFont(size=11)
        )
        category_entry.pack(fill="both")
        
        col2 = ctk.CTkFrame(row1)
        col2.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(
            col2, text="Auteur", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))
        
        author_entry = ctk.CTkEntry(
            col2, placeholder_text="Nom de l'auteur", height=40, font=ctk.CTkFont(size=11)
        )
        author_entry.pack(fill="both")
        
        # Description
        ctk.CTkLabel(
            form, text="Description", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        description_text = ctk.CTkTextbox(
            form, height=80, font=ctk.CTkFont(size=11)
        )
        description_text.pack(fill="both", pady=(0, 20))
        
        # Buttons
        btn_frame = ctk.CTkFrame(form)
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            btn_frame, text="✅ Ajouter le Document", fg_color=self.colors["success"], hover_color="#059669", height=45, font=ctk.CTkFont(size=12, weight="bold"), command=lambda: self._add_academic_document(doc_type_combo, title_entry, category_entry, author_entry, description_text)
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            btn_frame, text="🔄 Réinitialiser", fg_color="#6b7280", hover_color="#4b5563", height=45, font=ctk.CTkFont(size=12, weight="bold"), command=lambda: [
                title_entry.delete(0, "end"), category_entry.delete(0, "end"), author_entry.delete(0, "end"), description_text.delete("1.0", "end")
            ]
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _add_academic_grade(self, course_entry, code_entry, credits_entry, grade_entry, status_combo, semester_combo, date_entry, professor_entry):
        """Ajoute une note académique pour l'étudiant sélectionné"""
        try:
            # Vérifier si un étudiant est sélectionné
            if not self.academic_state['selected_student']:
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant dans la liste")
                return
            
            student = self.academic_state['selected_student']
            
            # Valider les entrées
            course_name = course_entry.get().strip()
            grade_str = grade_entry.get().strip()
            
            if not course_name:
                messagebox.showwarning("Attention", "Veuillez entrer le nom du cours")
                return
            
            if not grade_str:
                messagebox.showwarning("Attention", "Veuillez entrer la note")
                return
            
            # Convertir les valeurs
            try:
                grade = float(grade_str)
                credits = int(credits_entry.get()) if credits_entry.get() else 0
            except ValueError:
                messagebox.showerror("Erreur", "Note et crédits doivent être des nombres")
                return
            
            if grade < 0 or grade > 20:
                messagebox.showwarning("Attention", "La note doit être entre 0 et 20")
                return
            
            # Insérer dans la base de données
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            query = """
                INSERT INTO academic_record 
                (student_id, promotion_id, course_name, course_code, credits, grade, grade_letter, semester, exam_date, professor_name, status, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            grade_letter = self._get_grade_letter(grade)
            exam_date = date_entry.get() if date_entry.get() else None
            
            conn.execute_update(query, (
                student['id'], student['promotion_id'], course_name, code_entry.get() or None, credits, grade, grade_letter, self._map_semester_to_db(semester_combo.get()), exam_date, professor_entry.get() or None, self._map_status_to_db(status_combo.get()), None
            ))
            
            # Effacer les champs AVANT le message (pour que l'utilisateur les voie se vider)
            course_entry.delete(0, "end")
            code_entry.delete(0, "end")
            credits_entry.delete(0, "end")
            grade_entry.delete(0, "end")
            date_entry.delete(0, "end")
            professor_entry.delete(0, "end")
            
            messagebox.showinfo(
                "Succès", f"✅ Note ajoutée avec succès pour {course_name}!\n\n"
                f"Étudiant: {student['firstname']} {student['lastname']}\n"
                f"Note: {grade}/20 ({grade_letter})"
            )
            
            # Mettre à jour l'affichage des données APRÈS le message
            # Cela donne un meilleur retour utilisateur
            self._display_academic_data_for_student(student)
            
        except Exception as e:
            logger.error(f"Erreur ajout note académique: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _add_academic_document(self, doc_type_combo, title_entry, category_entry, author_entry, description_text):
        """Ajoute un document académique pour l'étudiant sélectionné"""
        try:
            # Vérifier si un étudiant est sélectionné
            if not self.academic_state['selected_student']:
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant dans la liste")
                return
            
            student = self.academic_state['selected_student']
            
            # Valider les entrées
            title = title_entry.get().strip()
            doc_type = doc_type_combo.get()
            
            if not title:
                messagebox.showwarning("Attention", "Veuillez entrer le titre du document")
                return
            
            # Insérer dans la base de données
            from core.database.connection import DatabaseConnection
            conn = DatabaseConnection()
            
            query = """
                INSERT INTO student_document 
                (student_id, document_type, title, description, author, category)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            description = description_text.get("1.0", "end-1c").strip()
            
            conn.execute_update(query, (
                student['id'], self._map_doc_type_to_db(doc_type), title, description or None, author_entry.get() or None, category_entry.get() or None
            ))
            
            # Effacer les champs AVANT le message
            title_entry.delete(0, "end")
            category_entry.delete(0, "end")
            author_entry.delete(0, "end")
            description_text.delete("1.0", "end")
            
            messagebox.showinfo(
                "Succès", f"✅ Document ajouté avec succès!\n\n"
                f"Étudiant: {student['firstname']} {student['lastname']}\n"
                f"Type: {doc_type}\n"
                f"Titre: {title}"
            )
            
            # Mettre à jour l'affichage des données APRÈS le message
            self._display_academic_data_for_student(student)
            
        except Exception as e:
            logger.error(f"Erreur ajout document académique: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _get_grade_letter(self, grade):
        """Convertit une note numérique en lettre"""
        if grade >= 18:
            return "A"
        elif grade >= 16:
            return "B"
        elif grade >= 14:
            return "C"
        elif grade >= 12:
            return "D"
        else:
            return "F"
    
    def _map_status_to_db(self, status_fr):
        """Convertit le statut français en anglais pour la base de données"""
        mapping = {
            "RÉUSSI": "PASSED", "ÉCHOUÉ": "FAILED", "EN COURS": "IN_PROGRESS"
        }
        return mapping.get(status_fr, "PASSED")
    
    def _map_semester_to_db(self, semester_fr):
        """Convertit le semestre français en anglais pour la base de données"""
        mapping = {
            "Annuel": "Annual", "1": "1", "2": "2"
        }
        return mapping.get(semester_fr, "Annual")
    
    def _map_doc_type_to_db(self, doc_type_fr):
        """Convertit le type de document français en anglais pour la base de données"""
        mapping = {
            "LIVRE": "BOOK", "THÈSE": "THESIS", "RAPPORT": "REPORT", "CERTIFICAT": "CERTIFICATE", "DIPLÔME": "DIPLOMA", "AUTRE": "OTHER"
        }
        return mapping.get(doc_type_fr, "OTHER")
    
    # ==================== TRANSFERS VIEW ====================
    
    def _show_transfers(self):
        """Affiche la page de gestion des transferts inter-universitaires"""
        if not self._can_access_view("transfers"):
            self._handle_forbidden_view("transfers")
            return
        self.current_view = "transfers"
        self._persist_ui_context(view=self.current_view)
        self._set_main_scrollbar_visible(True)
        self._update_nav_buttons("transfers")
        self.title_label.configure(text="🔄 Transferts Inter-Universitaires")
        self._clear_content()
        
        # Tabs container
        tabs_container = ctk.CTkFrame(self.content_frame)
        tabs_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tab buttons
        tab_frame = ctk.CTkFrame(tabs_container, fg_color=self.colors["card_bg"], corner_radius=10)
        tab_frame.pack(fill="x", pady=(0, 20))
        
        tab_buttons_frame = ctk.CTkFrame(tab_frame)
        tab_buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Active tab tracker
        self.active_transfer_tab = "outgoing"
        
        # Tab buttons
        tab_buttons = []
        tabs_data = [
            ("outgoing", "📤 Transferts Sortants", self._show_outgoing_transfers), ("incoming", "📥 Demandes Entrantes", self._show_incoming_transfers), ("history", "📜 Historique", self._show_transfer_history)
        ]
        
        for tab_key, tab_label, tab_callback in tabs_data:
            btn = ctk.CTkButton(
                tab_buttons_frame, text=tab_label, fg_color=self.colors["primary"] if tab_key == "outgoing" else "transparent", hover_color=self.colors["primary"], text_color=self.colors["text_white"] if tab_key == "outgoing" else self.colors["text_dark"], corner_radius=8, height=40, font=ctk.CTkFont(size=13, weight="bold"), command=lambda k=tab_key, c=tab_callback, btns=tab_buttons: self._switch_transfer_tab(k, c, btns)
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")
            tab_buttons.append({"button": btn, "key": tab_key})
        
        # Content container for tab views
        self.transfer_tab_content = ctk.CTkFrame(tabs_container)
        self.transfer_tab_content.pack(fill="both", expand=True)
        
        # Show initial tab
        self._show_outgoing_transfers()
    
    def _switch_transfer_tab(self, tab_key, callback, tab_buttons):
        """Change d'onglet dans l'interface de transferts"""
        self.active_transfer_tab = tab_key
        
        # Update button colors
        for tab_btn in tab_buttons:
            if tab_btn["key"] == tab_key:
                tab_btn["button"].configure(
                    fg_color=self.colors["primary"], text_color=self.colors["text_white"]
                )
            else:
                tab_btn["button"].configure(
                    text_color=self.colors["text_dark"]
                )
        
        # Clear ALL content FIRST before showing new tab
        for widget in self.transfer_tab_content.winfo_children():
            widget.destroy()
        
        # Now show new content
        callback()
    
    def _show_outgoing_transfers(self):
        """Affiche l'interface pour initier un transfert sortant avec sélection en cascade"""
        # Initialize transfer state if not exists
        if not hasattr(self, 'transfer_state'):
            self.transfer_state = {
                'faculty_id': None, 'department_id': None, 'promotion_id': None, 'selected_student': None, 'filtered_students': []
            }
        
        container = ctk.CTkScrollableFrame(
            self.transfer_tab_content, fg_color=self.colors["card_bg"], corner_radius=12
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(container)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header, text="📤 Initier un Transfert Sortant", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Info card
        info_card = ctk.CTkFrame(container, fg_color=self.colors["info"], corner_radius=10)
        info_card.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(
            info_card, text="ℹ️  Transférez les données académiques d'un étudiant vers une autre université.\n"
                 "Sélection : Faculté → Département → Promotion → Étudiant", font=ctk.CTkFont(size=11), text_color=self.colors["text_white"], justify="left"
        ).pack(padx=15, pady=12)
        
        # Main content in two columns
        main_content = ctk.CTkFrame(container)
        main_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # LEFT COLUMN - Selection and Student List
        left_column = ctk.CTkFrame(main_content)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Card 1: Faculty, Department, Promotion Selection
        selection_card = ctk.CTkFrame(left_column, fg_color=self.colors["hover"], corner_radius=10)
        selection_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            selection_card, text="📍 Sélection Hiérarchique", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Faculty selection
        ctk.CTkLabel(
            selection_card, text="Faculté :", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        faculties = self._get_transfer_faculties()
        faculty_names = [f['name'] for f in faculties]
        
        self.transfer_faculty_combo = ctk.CTkComboBox(
            selection_card, values=faculty_names if faculty_names else ["Aucune faculté"], width=300, height=32, font=ctk.CTkFont(size=11), command=self._on_transfer_faculty_selected
        )
        self.transfer_faculty_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Department selection
        ctk.CTkLabel(
            selection_card, text="Département :", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        self.transfer_dept_combo = ctk.CTkComboBox(
            selection_card, values=["Sélectionner une faculté d'abord"], width=300, height=32, font=ctk.CTkFont(size=11), command=self._on_transfer_department_selected
        )
        self.transfer_dept_combo.pack(anchor="w", padx=15, pady=(0, 10))
        
        # Promotion selection
        ctk.CTkLabel(
            selection_card, text="Promotion :", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        self.transfer_promotion_combo = ctk.CTkComboBox(
            selection_card, values=["Sélectionner un département d'abord"], width=300, height=32, font=ctk.CTkFont(size=11), command=self._on_transfer_promotion_selected
        )
        self.transfer_promotion_combo.pack(anchor="w", padx=15, pady=(0, 15))
        
        # Card 2: Student List with Search
        students_card = ctk.CTkFrame(left_column, fg_color=self.colors["hover"], corner_radius=10)
        students_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            students_card, text="👥 Étudiants", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Search
        ctk.CTkLabel(
            students_card, text="🔍 Rechercher :", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15)
        
        self.transfer_search_entry = ctk.CTkEntry(
            students_card, width=300, height=32, placeholder_text="Nom, Numéro ou Email"
        )
        self.transfer_search_entry.pack(anchor="w", padx=15, pady=(0, 10))
        self.transfer_search_entry.bind("<KeyRelease>", self._on_transfer_search_changed)
        
        # Students list frame
        self.transfer_students_scroll = ctk.CTkScrollableFrame(
            students_card, fg_color=self.colors["card_bg"], corner_radius=8, width=320, height=250
        )
        self.transfer_students_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # RIGHT COLUMN - Student Info and Transfer Form
        right_column = ctk.CTkFrame(main_content)
        right_column.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        # Card 3: Selected Student Info
        student_info_card = ctk.CTkFrame(right_column, fg_color=self.colors["hover"], corner_radius=10)
        student_info_card.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            student_info_card, text="📋 Informations Étudiant", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        self.transfer_student_info_frame = ctk.CTkFrame(student_info_card, fg_color=self.colors["card_bg"], corner_radius=8)
        self.transfer_student_info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            self.transfer_student_info_frame, text="Sélectionner un étudiant", font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]
        ).pack(padx=10, pady=10)
        
        # Card 4: Transfer Form
        form_card = ctk.CTkFrame(right_column, fg_color=self.colors["hover"], corner_radius=10)
        form_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            form_card, text="🎯 Détails du Transfert", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        form_scroll = ctk.CTkScrollableFrame(form_card)
        form_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Destination university + API URL editable field
        ctk.CTkLabel(
            form_scroll, text="Université de destination :", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 5))

        partners = self._get_partner_universities()
        partner_options = [f"{p['university_name']} ({p['university_code']}) - {p['country']}" for p in partners]
        self._partner_id_map = {f"{p['university_name']} ({p['university_code']}) - {p['country']}": p for p in partners}

        self.transfer_destination_combo = ctk.CTkComboBox(
            form_scroll, values=partner_options if partner_options else ["Aucune université partenaire"], width=300, height=32, font=ctk.CTkFont(size=11), command=self._on_partner_university_changed
        )
        self.transfer_destination_combo.pack(anchor="w", pady=(0, 5))
        if partner_options:
            self.transfer_destination_combo.set(partner_options[0])

        # API URL editable field
        ctk.CTkLabel(
            form_scroll, text="URL API de réception (modifiable) :", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(0, 2))
        self.partner_api_url_var = tk.StringVar()
        self.partner_api_url_entry = ctk.CTkEntry(
            form_scroll, width=350, height=30, textvariable=self.partner_api_url_var
        )
        self.partner_api_url_entry.pack(anchor="w", pady=(0, 5))
        # Save button
        self.save_api_url_btn = ctk.CTkButton(
            form_scroll, text="💾 Sauvegarder l'URL API", fg_color=self.colors["primary"], hover_color="#2563eb", text_color=self.colors["text_white"], height=32, font=ctk.CTkFont(size=11, weight="bold"), command=self._on_save_partner_api_url
        )
        self.save_api_url_btn.pack(anchor="w", pady=(0, 15))

        # Initial fill of API URL
        self._update_partner_api_url_entry()

    def _on_partner_university_changed(self, value):
        self._update_partner_api_url_entry()

    def _update_partner_api_url_entry(self):
        # Met à jour le champ d'URL API selon l'université sélectionnée
        selected = self.transfer_destination_combo.get()
        partner = self._partner_id_map.get(selected)
        if partner:
            self.partner_api_url_var.set(partner.get('api_url') or "")
        else:
            self.partner_api_url_var.set("")

    def _on_save_partner_api_url(self):
        # Sauvegarde l'URL API modifiée pour l'université sélectionnée
        selected = self.transfer_destination_combo.get()
        partner = self._partner_id_map.get(selected)
        new_url = self.partner_api_url_var.get().strip()
        if not partner:
            ErrorManager.show_error("validation_error", "Aucune université sélectionnée.")
            return
        try:
            self.transfer_service.set_partner_api_url(partner['id'], new_url)
            partner['api_url'] = new_url
            ErrorManager.show_success("Succès", "URL API sauvegardée avec succès.")
        except Exception as e:
            logger.error(f"Erreur sauvegarde URL API: {e}", exc_info=True)
            ErrorManager.show_error("database_query", str(e))
        
        # Include documents checkbox
        self.transfer_include_docs_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            form_scroll, text="✓ Inclure les documents et ouvrages", variable=self.transfer_include_docs_var, font=ctk.CTkFont(size=11), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=10)
        
        # Notes
        ctk.CTkLabel(
            form_scroll, text="Notes (optionnel) :", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", pady=(10, 5))
        
        self.transfer_notes_text = ctk.CTkTextbox(
            form_scroll, width=300, height=70, font=ctk.CTkFont(size=10)
        )
        self.transfer_notes_text.pack(anchor="w", pady=(0, 20))
        
        # Action buttons
        button_frame = ctk.CTkFrame(form_scroll)
        button_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            button_frame, text="📤 Générer", fg_color=self.colors["success"], hover_color="#059669", text_color=self.colors["text_white"], height=40, font=ctk.CTkFont(size=12, weight="bold"), command=self._generate_transfer_package_action
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, text="🔄 Rafraîchir", fg_color=self.colors["primary"], hover_color="#2563eb", text_color=self.colors["text_white"], height=40, font=ctk.CTkFont(size=12, weight="bold"), command=self._refresh_outgoing_transfers
        ).pack(side="left", padx=5)
    
    def _refresh_outgoing_transfers(self):
        """Rafraîchit la page des transferts sortants"""
        try:
            # Vider complètement le contenu
            for widget in self.transfer_tab_content.winfo_children():
                widget.destroy()
            
            # Réafficher le contenu
            self._show_outgoing_transfers()
        except Exception as e:
            logger.error(f"Erreur rafraîchissement transferts sortants: {e}")
    
    # ========== TRANSFER CASCADE METHODS ==========
    
    def _get_transfer_faculties(self):
        """Récupère toutes les facultés (avec cache)."""
        return self._get_cached_data(
            "transfer_faculties",
            self.student_service.get_faculties,
            ttl_seconds=60.0,
        )
    
    def _on_transfer_faculty_selected(self, faculty_name):
        """Gère la sélection d'une faculté"""
        try:
            faculties = self._get_transfer_faculties()
            faculty = next((f for f in faculties if f['name'] == faculty_name), None)
            
            if faculty:
                self.transfer_state['faculty_id'] = faculty['id']
                
                # Charger les départements
                departments = self.student_service.get_departments_by_faculty(faculty['id'])
                dept_names = [d['name'] for d in departments]
                
                self.transfer_dept_combo.configure(values=dept_names if dept_names else ["Aucun département"])
                if dept_names:
                    self.transfer_dept_combo.set(dept_names[0])
                    self._on_transfer_department_selected(dept_names[0])
                else:
                    self.transfer_dept_combo.set("Aucun département")
                    self.transfer_promotion_combo.configure(values=["Aucune promotion"])
                    self._clear_transfer_students_list()
            
        except Exception as e:
            logger.error(f"Erreur sélection faculté: {e}", exc_info=True)
    
    def _on_transfer_department_selected(self, dept_name):
        """Gère la sélection d'un département"""
        try:
            if not self.transfer_state['faculty_id']:
                return
            
            faculties = self._get_transfer_faculties()
            faculty = next((f for f in faculties if f['id'] == self.transfer_state['faculty_id']), None)
            
            if faculty:
                departments = self.student_service.get_departments_by_faculty(faculty['id'])
                department = next((d for d in departments if d['name'] == dept_name), None)
                
                if department:
                    self.transfer_state['department_id'] = department['id']
                    
                    # Charger les promotions
                    promotions = self.student_service.get_promotions_by_department(department['id'])
                    promo_names = [p['name'] for p in promotions]
                    
                    self.transfer_promotion_combo.configure(values=promo_names if promo_names else ["Aucune promotion"])
                    if promo_names:
                        self.transfer_promotion_combo.set(promo_names[0])
                        self._on_transfer_promotion_selected(promo_names[0])
                    else:
                        self.transfer_promotion_combo.set("Aucune promotion")
                        self._clear_transfer_students_list()
        
        except Exception as e:
            logger.error(f"Erreur sélection département: {e}", exc_info=True)
    
    def _on_transfer_promotion_selected(self, promo_name):
        """Gère la sélection d'une promotion"""
        try:
            if not self.transfer_state['department_id']:
                return
            
            departments = self.student_service.get_departments_by_faculty(self.transfer_state['faculty_id'])
            department = next((d for d in departments if d['id'] == self.transfer_state['department_id']), None)
            
            if department:
                promotions = self.student_service.get_promotions_by_department(department['id'])
                promotion = next((p for p in promotions if p['name'] == promo_name), None)
                
                if promotion:
                    self.transfer_state['promotion_id'] = promotion['id']
                    
                    # Charger les étudiants
                    self._update_transfer_students_list()
                    
                    # Effacer le champ de recherche
                    if hasattr(self, 'transfer_search_entry'):
                        self.transfer_search_entry.delete(0, "end")
        
        except Exception as e:
            logger.error(f"Erreur sélection promotion: {e}", exc_info=True)
    
    def _update_transfer_students_list(self):
        """Met à jour la liste des étudiants"""
        try:
            students = self._get_transfer_students_by_promotion()
            self.transfer_state['filtered_students'] = students
            self._clear_transfer_students_list()
            
            if not students:
                # Afficher un message si aucun étudiant
                ctk.CTkLabel(
                    self.transfer_students_scroll, text="Aucun étudiant actif\ndans cette promotion", font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]
                ).pack(pady=20)
                logger.info("Aucun étudiant trouvé pour cette promotion")
            else:
                for student in students:
                    btn = self._create_transfer_student_button(student)
                    btn.pack(fill="x", padx=5, pady=3)
                logger.info(f"{len(students)} étudiant(s) affiché(s)")
        
        except Exception as e:
            logger.error(f"Erreur mise à jour liste étudiants: {e}", exc_info=True)
    
    def _get_transfer_students_by_promotion(self, search_text=""):
        """Récupère les étudiants filtrés par promotion"""
        try:
            if not self.transfer_state['promotion_id']:
                return []
            
            from core.database.connection import DatabaseConnection
            db = DatabaseConnection()
            conn = db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT id, student_number, firstname, lastname, email FROM student
                WHERE promotion_id = %s AND is_active = TRUE
            """
            
            params = [self.transfer_state['promotion_id']]
            
            if search_text:
                query += """ AND (student_number LIKE %s OR firstname LIKE %s 
                            OR lastname LIKE %s OR email LIKE %s)"""
                search_like = f"%{search_text}%"
                params.extend([search_like, search_like, search_like, search_like])
            
            query += " ORDER BY firstname, lastname"
            
            cursor.execute(query, params)
            students = cursor.fetchall()
            
            logger.info(f"Étudiants trouvés pour promotion {self.transfer_state['promotion_id']}: {len(students)}")
            
            return students
        
        except Exception as e:
            logger.error(f"Erreur récupération étudiants: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                db.close_connection(conn)
    
    def _on_transfer_search_changed(self, event=None):
        """Gère la recherche en temps réel"""
        try:
            search_text = self.transfer_search_entry.get().strip()
            students = self._get_transfer_students_by_promotion(search_text)
            self.transfer_state['filtered_students'] = students
            self._clear_transfer_students_list()
            
            if not students:
                # Afficher un message si aucun résultat
                message = "Aucun résultat" if search_text else "Aucun étudiant actif\ndans cette promotion"
                ctk.CTkLabel(
                    self.transfer_students_scroll, text=message, font=ctk.CTkFont(size=11), text_color=self.colors["text_light"]
                ).pack(pady=20)
            else:
                for student in students:
                    btn = self._create_transfer_student_button(student)
                    btn.pack(fill="x", padx=5, pady=3)
        
        except Exception as e:
            logger.error(f"Erreur recherche: {e}", exc_info=True)
    
    def _create_transfer_student_button(self, student):
        """Crée un bouton pour chaque étudiant"""
        student_text = f"{student['student_number']} - {student['firstname']} {student['lastname']}"
        
        btn = ctk.CTkButton(
            self.transfer_students_scroll, text=student_text, font=ctk.CTkFont(size=11), fg_color=self.colors["card_bg"], text_color=self.colors["text_dark"], hover_color=self.colors["primary"], height=35, corner_radius=8, command=lambda s=student: self._select_transfer_student(s)
        )
        
        return btn
    
    def _select_transfer_student(self, student):
        """Sélectionne un étudiant"""
        try:
            self.transfer_state['selected_student'] = student
            self._display_student_transfer_info(student)
        
        except Exception as e:
            logger.error(f"Erreur sélection étudiant: {e}", exc_info=True)
    
    def _clear_transfer_students_list(self):
        """Efface la liste des étudiants"""
        try:
            for widget in self.transfer_students_scroll.winfo_children():
                widget.destroy()
        except Exception as e:
            logger.error(f"Erreur suppression liste: {e}", exc_info=True)
    
    def _show_incoming_transfers(self):
        """Affiche les demandes de transfert entrantes en attente"""
        container = ctk.CTkScrollableFrame(
            self.transfer_tab_content, fg_color=self.colors["card_bg"], corner_radius=12
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(container)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header, text="📥 Demandes de Transfert Entrantes", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Get pending requests
        pending_requests = self._get_cached_data(
            "pending_transfer_requests",
            self.transfer_service.get_pending_transfer_requests,
            ttl_seconds=20.0,
        )
        
        if not pending_requests:
            # No requests
            no_data_frame = ctk.CTkFrame(container, fg_color=self.colors["hover"], corner_radius=10)
            no_data_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                no_data_frame, text="📭 Aucune demande de transfert en attente", font=ctk.CTkFont(size=16), text_color=self.colors["text_light"]
            ).pack(pady=40)
        else:
            # Display requests
            for request in pending_requests:
                self._create_transfer_request_card(container, request)
    
    def _create_transfer_request_card(self, parent, request):
        """Crée une carte pour une demande de transfert"""
        card = ctk.CTkFrame(parent, fg_color=self.colors["hover"], corner_radius=12)
        card.pack(fill="x", padx=20, pady=10)
        
        # Header
        card_header = ctk.CTkFrame(card)
        card_header.pack(fill="x", padx=15, pady=12)
        
        # Student name
        ctk.CTkLabel(
            card_header, text=f"👤 {request['external_firstname']} {request['external_lastname']}", font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Status badge
        status_frame = ctk.CTkFrame(card_header, fg_color=self.colors["warning"], corner_radius=15)
        status_frame.pack(side="right", padx=5)
        
        ctk.CTkLabel(
            status_frame, text="⏳ EN ATTENTE", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.colors["text_white"]
        ).pack(padx=10, pady=3)
        
        # Details
        details_frame = ctk.CTkFrame(card)
        details_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        details_text = (
            f"📋 Code: {request['request_code']}\n"
            f"🏫 Université source: {request['source_university']} ({request.get('source_university_code', 'N/A')})\n"
            f"📧 Email: {request.get('external_email', 'N/A')}\n"
            f"☎️ Téléphone: {request.get('external_phone', 'N/A')}\n"
            f"📅 Date de demande: {request['requested_date'].strftime('%d/%m/%Y %H:%M') if request.get('requested_date') else 'N/A'}"
        )
        
        ctk.CTkLabel(
            details_frame, text=details_text, font=ctk.CTkFont(size=11), text_color=self.colors["text_dark"], justify="left"
        ).pack(anchor="w")
        
        # Action buttons
        button_frame = ctk.CTkFrame(card)
        button_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkButton(
            button_frame, text="👁️ Voir Détails", fg_color=self.colors["info"], hover_color="#0891b2", text_color=self.colors["text_white"], height=35, font=ctk.CTkFont(size=12, weight="bold"), command=lambda r=request: self._view_transfer_request_details(r)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, text="✅ Approuver", fg_color=self.colors["success"], hover_color="#059669", text_color=self.colors["text_white"], height=35, font=ctk.CTkFont(size=12, weight="bold"), command=lambda r=request: self._approve_transfer_request(r)
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, text="❌ Rejeter", fg_color=self.colors["danger"], hover_color="#dc2626", text_color=self.colors["text_white"], height=35, font=ctk.CTkFont(size=12, weight="bold"), command=lambda r=request: self._reject_transfer_request(r)
        ).pack(side="left", padx=5)
    
    def _show_transfer_history(self):
        """Affiche l'historique des transferts"""
        container = ctk.CTkScrollableFrame(
            self.transfer_tab_content, fg_color=self.colors["card_bg"], corner_radius=12
        )
        container.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(container)
        header.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            header, text="📜 Historique des Transferts", font=ctk.CTkFont(size=20, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(side="left")
        
        # Get transfer history
        history = self._get_cached_data(
            "transfer_history",
            lambda: self.transfer_service.get_transfer_history(limit=50),
            ttl_seconds=20.0,
        )
        
        if not history:
            # No history
            no_data_frame = ctk.CTkFrame(container, fg_color=self.colors["hover"], corner_radius=10)
            no_data_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(
                no_data_frame, text="📭 Aucun transfert enregistré", font=ctk.CTkFont(size=16), text_color=self.colors["text_light"]
            ).pack(pady=40)
        else:
            # Create table header
            table_header = ctk.CTkFrame(container, fg_color=self.colors["primary"], corner_radius=8)
            table_header.pack(fill="x", padx=20, pady=(0, 10))
            
            headers = ["Code", "Étudiant", "Type", "Université", "Date", "Statut", "Livraison", "Détails"]
            header_widths = [120, 150, 100, 200, 120, 100, 110, 80]
            
            header_row = ctk.CTkFrame(table_header, fg_color="transparent")
            header_row.pack(fill="x", padx=10, pady=8)
            
            for header_text, width in zip(headers, header_widths):
                ctk.CTkLabel(
                    header_row, text=header_text, font=ctk.CTkFont(size=11, weight="bold"), text_color=self.colors["text_white"], width=width
                ).pack(side="left", padx=5)
            
            # Create table rows
            for i, transfer in enumerate(history):
                self._create_transfer_history_row(container, transfer, i)
    
    def _create_transfer_history_row(self, parent, transfer, index):
        """Crée une ligne d'historique de transfert"""
        bg_color = self.colors["card_bg"] if index % 2 == 0 else self.colors["hover"]
        
        row = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=8)
        row.pack(fill="x", padx=20, pady=2)
        
        row_content = ctk.CTkFrame(row)
        row_content.pack(fill="x", padx=10, pady=8)
        
        # Data
        transfer_code = transfer.get('transfer_code', 'N/A')[:15] + "..." if len(transfer.get('transfer_code', '')) > 15 else transfer.get('transfer_code', 'N/A')
        student_name = f"{transfer.get('firstname', '')} {transfer.get('lastname', '')}".strip() or "N/A"
        transfer_type = "📤 Sortant" if transfer.get('transfer_type') == 'OUTGOING' else "📥 Entrant"
        university = transfer.get('destination_university', 'N/A') if transfer.get('transfer_type') == 'OUTGOING' else transfer.get('source_university', 'N/A')
        transfer_date = transfer['transfer_date'].strftime('%d/%m/%Y') if transfer.get('transfer_date') else 'N/A'
        
        # Status color
        status = transfer.get('status', 'N/A')
        status_colors = {
            'COMPLETED': self.colors['success'], 'PENDING': self.colors['warning'], 'IN_PROGRESS': self.colors['info'], 'REJECTED': self.colors['danger'], 'CANCELLED': self.colors['text_light']
        }
        status_color = status_colors.get(status, self.colors['text_light'])

        # Delivery status color
        delivery_status = transfer.get('delivery_status', 'non_envoye')
        delivery_colors = {
            'envoye': self.colors['success'], 'echec': self.colors['danger'], 'non_envoye': self.colors['warning']
        }
        delivery_color = delivery_colors.get(delivery_status, self.colors['text_light'])
        delivery_label = {
            'envoye': '✅ Envoyé', 'echec': '❌ Échec', 'non_envoye': '⏳ Non envoyé'
        }.get(delivery_status, delivery_status)

        # Columns
        widths = [120, 150, 100, 200, 120, 100, 110, 80]
        values = [transfer_code, student_name, transfer_type, university[:25], transfer_date]

        for value, width in zip(values, widths[:5]):
            ctk.CTkLabel(
                row_content, text=value, font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"], width=width, anchor="w"
            ).pack(side="left", padx=5)

        # Status badge
        status_frame = ctk.CTkFrame(row_content, fg_color=status_color, corner_radius=10, width=100)
        status_frame.pack(side="left", padx=5)
        ctk.CTkLabel(
            status_frame, text=status, font=ctk.CTkFont(size=9, weight="bold"), text_color=self.colors["text_white"]
        ).pack(padx=8, pady=3)

        # Delivery badge
        delivery_frame = ctk.CTkFrame(row_content, fg_color=delivery_color, corner_radius=10, width=110)
        delivery_frame.pack(side="left", padx=5)
        ctk.CTkLabel(
            delivery_frame, text=delivery_label, font=ctk.CTkFont(size=9, weight="bold"), text_color=self.colors["text_white"]
        ).pack(padx=8, pady=3)

        # Details button
        ctk.CTkButton(
            row_content, text="👁️", fg_color=self.colors["info"], hover_color="#0891b2", text_color=self.colors["text_white"], width=60, height=28, font=ctk.CTkFont(size=12), command=lambda t=transfer: self._view_transfer_history_details(t)
        ).pack(side="left", padx=5)
    
    # Helper methods for transfers
    
    def _get_all_students_for_transfer(self):
        """Récupère tous les étudiants actifs"""
        try:
            return self.student_service.get_all_students_with_finance()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des étudiants: {e}", exc_info=True)
            return []
    
    def _get_partner_universities(self):
        """Récupère les universités partenaires"""
        try:
            conn = self.transfer_service.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * FROM partner_university 
                WHERE is_active = TRUE 
                ORDER BY university_name
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des universités: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.transfer_service.db.close_connection(conn)
    
    def _on_transfer_student_combo_changed(self, value):
        """Appelé quand la sélection du combo étudiant change"""
        try:
            if not value or value == "Aucun étudiant disponible":
                return
            
            student_number = value.split(" - ")[0]
            selected_student = next(
                (s for s in self.transfer_available_students if s['student_number'] == student_number), None
            )
            
            if selected_student:
                self._display_student_transfer_info(selected_student)
        except Exception as e:
            logger.error(f"Erreur changement combo étudiant: {e}", exc_info=True)
    
    def _on_transfer_student_selected(self, value, students):
        """Appelé quand un étudiant est sélectionné pour transfert"""
        student_number = value.split(" - ")[0]
        selected_student = next((s for s in students if s['student_number'] == student_number), None)
        
        if selected_student:
            self._display_student_transfer_info(selected_student)
    
    def _display_student_transfer_info(self, student):
        """Affiche les informations détaillées de l'étudiant sélectionné"""
        try:
            # Clear previous content
            for widget in self.transfer_student_info_frame.winfo_children():
                widget.destroy()
            
            # Get academic summary
            summary = self.transfer_service.get_student_academic_summary(student['id'])
            
            # Header with student info
            header_frame = ctk.CTkFrame(self.transfer_student_info_frame)
            header_frame.pack(fill="x", padx=15, pady=(12, 8))
            
            student_name = f"{student['firstname']} {student['lastname']}"
            ctk.CTkLabel(
                header_frame, text=f"📋 {student_name}", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["primary"]
            ).pack(anchor="w")
            
            # Academic data
            data_frame = ctk.CTkFrame(self.transfer_student_info_frame)
            data_frame.pack(fill="x", padx=15, pady=(0, 12))
            
            # Row 1: Number and Email
            row1 = ctk.CTkFrame(data_frame)
            row1.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row1, text=f"Numéro: {student['student_number']}", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
            ).pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(
                row1, text=f"Promotion: {student.get('promotion_name', 'N/A')}", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
            ).pack(side="left")
            
            # Row 2: Courses and Credits
            row2 = ctk.CTkFrame(data_frame)
            row2.pack(fill="x", pady=3)
            
            courses = summary.get('total_courses', 0) or 0
            credits = summary.get('total_credits', 0) or 0
            average = summary.get('average_grade', 0)
            
            ctk.CTkLabel(
                row2, text=f"📚 Cours: {courses}", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
            ).pack(side="left", padx=(0, 20))
            
            ctk.CTkLabel(
                row2, text=f"⭐ Crédits: {credits}", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
            ).pack(side="left", padx=(0, 20))
            
            avg_text = f"{float(average):.2f}" if average else "N/A"
            ctk.CTkLabel(
                row2, text=f"📊 Moyenne: {avg_text}", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
            ).pack(side="left")
            
            # Row 3: Documents
            docs = summary.get('total_documents', 0) or 0
            row3 = ctk.CTkFrame(data_frame)
            row3.pack(fill="x", pady=3)
            
            ctk.CTkLabel(
                row3, text=f"📄 Documents: {docs}", font=ctk.CTkFont(size=10), text_color=self.colors["text_dark"]
            ).pack(side="left")
            
        except Exception as e:
            logger.error(f"Erreur affichage info étudiant: {e}", exc_info=True)
            ctk.CTkLabel(
                self.transfer_student_info_frame, text="❌ Erreur lors de l'affichage des informations", font=ctk.CTkFont(size=11), text_color="#ef4444"
            ).pack(padx=15, pady=12)
    
    def _generate_transfer_package_action(self):
        """Génère et enregistre le package de transfert avec le système de cascade"""
        try:
            # Vérifier qu'un étudiant est sélectionné
            selected_student = self.transfer_state.get('selected_student')
            if not selected_student:
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant")
                return
            
            # Vérifier la destination
            dest_value = self.transfer_destination_combo.get()
            if not dest_value or dest_value == "Aucune université partenaire":
                messagebox.showwarning("Attention", "Veuillez sélectionner une université de destination")
                return
            
            try:
                dest_code = dest_value.split("(")[1].split(")")[0]
            except:
                messagebox.showerror("Erreur", "Format université invalide")
                return
            
            # Récupérer l'université partenaire
            partners = self._get_partner_universities()
            selected_partner = next((p for p in partners if p['university_code'] == dest_code), None)
            
            if not selected_partner:
                messagebox.showerror("Erreur", "Université introuvable")
                return
            
            # Récupérer les options
            include_docs = self.transfer_include_docs_var.get()
            notes = self.transfer_notes_text.get("1.0", "end-1c").strip()
            
            # Initier le transfert
            success, result = self.transfer_service.initiate_outgoing_transfer(
                student_id=selected_student['id'], destination_university=selected_partner['university_name'], destination_code=selected_partner['university_code'], initiated_by="Admin", include_documents=include_docs, notes=notes if notes else None
            )
            
            if success:
                # Envoi automatique à l'API partenaire
                delivery_status = "non envoyé"
                delivery_message = ""
                try:
                    api_url = selected_partner.get('api_url')
                    if api_url:
                        # Récupérer les données du transfert
                        transfer_data = self.transfer_service.get_transfer_package_by_code(result)
                        import json
                        from app.services.transfer.transfer_service import CustomJSONEncoder
                        headers = {'Content-Type': 'application/json'}
                        response = requests.post(api_url, data=json.dumps(transfer_data, cls=CustomJSONEncoder), headers=headers, timeout=10)
                        if response.status_code == 200:
                            delivery_status = "envoyé"
                            delivery_message = "✅ Données envoyées avec succès à l'API partenaire."
                        else:
                            delivery_status = "échec"
                            delivery_message = f"❌ Erreur lors de l'envoi à l'API partenaire: {response.status_code} {response.text}"
                    else:
                        delivery_message = "⚠️ Aucune URL API définie pour l'université partenaire."
                except Exception as ex:
                    delivery_status = "échec"
                    delivery_message = f"❌ Exception lors de l'envoi à l'API partenaire: {ex}"

                # Afficher le résultat à l'utilisateur
                messagebox.showinfo(
                    "Succès", f"✅ Transfert créé avec succès!\n\n"
                    f"Code de transfert: {result}\n\n"
                    f"Statut de livraison: {delivery_status}\n{delivery_message}"
                )
                # Enregistrer le statut de livraison dans la base
                status_map = {"envoyé": "envoye", "échec": "echec", "non envoyé": "non_envoye"}
                self.transfer_service.update_delivery_status(result, status_map.get(delivery_status, "non_envoye"), delivery_message)
                self._refresh_outgoing_transfers()
            else:
                messagebox.showerror(
                    "Erreur", f"❌ Impossible de créer le transfert:\n{result}"
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du package: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _generate_transfer_package(self, students, partners):
        """Génère et enregistre le package de transfert"""
        try:
            # Get selected student
            selected_value = self.transfer_student_combo.get()
            if not selected_value or selected_value == "Aucun étudiant disponible":
                messagebox.showwarning("Attention", "Veuillez sélectionner un étudiant")
                return
            
            student_number = selected_value.split(" - ")[0]
            selected_student = next((s for s in students if s['student_number'] == student_number), None)
            
            if not selected_student:
                messagebox.showerror("Erreur", "Étudiant introuvable")
                return
            
            # Get selected destination
            dest_value = self.transfer_destination_combo.get()
            if not dest_value or dest_value == "Aucune université partenaire":
                messagebox.showwarning("Attention", "Veuillez sélectionner une université de destination")
                return
            
            dest_code = dest_value.split("(")[1].split(")")[0]
            selected_partner = next((p for p in partners if p['university_code'] == dest_code), None)
            
            if not selected_partner:
                messagebox.showerror("Erreur", "Université introuvable")
                return
            
            # Get options
            include_docs = self.transfer_include_docs_var.get()
            notes = self.transfer_notes_text.get("1.0", "end-1c").strip()
            
            # Initiate transfer
            success, result = self.transfer_service.initiate_outgoing_transfer(
                student_id=selected_student['id'], destination_university=selected_partner['university_name'], destination_code=selected_partner['university_code'], initiated_by="Admin", # TODO: Use actual logged-in user
                include_documents=include_docs, notes=notes if notes else None
            )
            
            if success:
                messagebox.showinfo(
                    "Succès", f"Transfert créé avec succès!\n\n"
                    f"Code de transfert: {result}\n\n"
                    f"Les données ont été enregistrées et peuvent être "
                    f"exportées vers l'université destinataire."
                )
                # Refresh the view
                self._show_outgoing_transfers()
            else:
                messagebox.showerror(
                    "Erreur", f"Impossible de créer le transfert:\n{result}"
                )
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération du package: {e}", exc_info=True)
            messagebox.showerror("Erreur", f"Une erreur s'est produite: {str(e)}")
    
    def _view_transfer_request_details(self, request):
        """Affiche les détails d'une demande de transfert"""
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails - {request['request_code']}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        self._animate_window_open(dialog)
        
        # Scroll frame
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=self.colors["card_bg"])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        ctk.CTkLabel(
            scroll, text=f"Demande de Transfert - {request['request_code']}", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        # Parse JSON data
        import json
        
        try:
            if request.get('received_data_json'):
                transfer_data = json.loads(request['received_data_json'])
                
                # Display formatted data
                json_display = json.dumps(transfer_data, indent=2, ensure_ascii=False)
                
                text_widget = ctk.CTkTextbox(scroll, height=400, font=ctk.CTkFont(size=10))
                text_widget.pack(fill="both", expand=True, pady=10)
                text_widget.insert("1.0", json_display)
                text_widget.configure(state="disabled")
        except Exception as e:
            ctk.CTkLabel(
                scroll, text=f"Erreur lors du chargement des données: {e}", text_color=self.colors["danger"]
            ).pack(pady=20)
        
        # Close button
        ctk.CTkButton(
            scroll, text="Fermer", fg_color=self.colors["primary"], command=dialog.destroy, height=40
        ).pack(pady=10, fill="x")
    
    def _approve_transfer_request(self, request):
        """Approuve une demande de transfert entrante"""
        # Create approval dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Approuver le Transfert")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        self._animate_window_open(dialog)
        
        frame = ctk.CTkFrame(dialog, fg_color=self.colors["card_bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame, text=f"✅ Approuver le Transfert", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            frame, text=f"Étudiant: {request['external_firstname']} {request['external_lastname']}\n"
                 f"Source: {request['source_university']}", font=ctk.CTkFont(size=12), text_color=self.colors["text_dark"]
        ).pack(pady=10)
        
        # Select promotion
        ctk.CTkLabel(
            frame, text="Sélectionner la promotion de destination:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        # Get promotions
        promotions = self._get_all_promotions()
        promo_options = [f"{p['name']} - {p['department_name']}" for p in promotions]
        
        promo_combo = ctk.CTkComboBox(
            frame, values=promo_options if promo_options else ["Aucune promotion"], width=400, height=35
        )
        promo_combo.pack(padx=20, pady=(0, 15))
        if promo_options:
            promo_combo.set(promo_options[0])
        
        # Notes
        ctk.CTkLabel(
            frame, text="Notes d'approbation:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        notes_text = ctk.CTkTextbox(frame, height=80, width=400)
        notes_text.pack(padx=20, pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def do_approve():
            selected_promo = promo_combo.get()
            if not selected_promo or selected_promo == "Aucune promotion":
                messagebox.showwarning("Attention", "Veuillez sélectionner une promotion")
                return
            
            promo_name = selected_promo.split(" - ")[0]
            selected_promotion = next((p for p in promotions if p['name'] == promo_name), None)
            
            if not selected_promotion:
                messagebox.showerror("Erreur", "Promotion introuvable")
                return
            
            approval_notes = notes_text.get("1.0", "end-1c").strip()
            
            # Approve
            success, result = self.transfer_service.approve_incoming_transfer(
                request_id=request['id'], approved_by="Admin", # TODO: Use actual logged-in user
                target_promotion_id=selected_promotion['id'], approval_notes=approval_notes if approval_notes else None
            )
            
            if success:
                messagebox.showinfo(
                    "Succès", f"Transfert approuvé avec succès!\n\n"
                    f"ID Étudiant créé: {result}\n\n"
                    f"L'étudiant a été créé avec un mot de passe temporaire: ChangeMe123!"
                )
                dialog.destroy()
                self._show_incoming_transfers()
            else:
                messagebox.showerror("Erreur", f"Impossible d'approuver le transfert:\n{result}")
        
        ctk.CTkButton(
            button_frame, text="✅ Approuver", fg_color=self.colors["success"], hover_color="#059669", command=do_approve, height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            button_frame, text="Annuler", fg_color=self.colors["text_light"], hover_color="#64748b", command=dialog.destroy, height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _reject_transfer_request(self, request):
        """Rejette une demande de transfert"""
        # Create rejection dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Rejeter le Transfert")
        dialog.geometry("500x300")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        self._animate_window_open(dialog)
        
        frame = ctk.CTkFrame(dialog, fg_color=self.colors["card_bg"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame, text="❌ Rejeter le Transfert", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            frame, text="Raison du rejet:", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(anchor="w", padx=20, pady=(10, 5))
        
        reason_text = ctk.CTkTextbox(frame, height=100, width=400)
        reason_text.pack(padx=20, pady=(0, 20))
        
        # Buttons
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        def do_reject():
            reason = reason_text.get("1.0", "end-1c").strip()
            if not reason:
                messagebox.showwarning("Attention", "Veuillez indiquer la raison du rejet")
                return
            
            success = self.transfer_service.reject_incoming_transfer(
                request_id=request['id'], rejected_by="Admin", # TODO: Use actual logged-in user
                rejection_reason=reason
            )
            
            if success:
                messagebox.showinfo("Succès", "Demande de transfert rejetée")
                dialog.destroy()
                self._show_incoming_transfers()
            else:
                messagebox.showerror("Erreur", "Impossible de rejeter la demande")
        
        ctk.CTkButton(
            button_frame, text="❌ Rejeter", fg_color=self.colors["danger"], hover_color="#dc2626", command=do_reject, height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
        
        ctk.CTkButton(
            button_frame, text="Annuler", fg_color=self.colors["text_light"], hover_color="#64748b", command=dialog.destroy, height=40
        ).pack(side="left", padx=5, expand=True, fill="x")
    
    def _view_transfer_history_details(self, transfer):
        """Affiche les détails d'un transfert dans l'historique"""
        # Create dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Détails - {transfer['transfer_code']}")
        dialog.geometry("700x600")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)
        self._animate_window_open(dialog)
        
        scroll = ctk.CTkScrollableFrame(dialog, fg_color=self.colors["card_bg"])
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            scroll, text=f"Détails du Transfert - {transfer['transfer_code']}", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.colors["text_dark"]
        ).pack(pady=(0, 20))
        
        # Display transfer info
        info_text = (
            f"Type: {transfer['transfer_type']}\n"
            f"Étudiant: {transfer.get('firstname', '')} {transfer.get('lastname', '')}\n"
            f"Source: {transfer.get('source_university', 'N/A')}\n"
            f"Destination: {transfer.get('destination_university', 'N/A')}\n"
            f"Date: {transfer['transfer_date'].strftime('%d/%m/%Y %H:%M') if transfer.get('transfer_date') else 'N/A'}\n"
            f"Statut: {transfer.get('status', 'N/A')}\n"
            f"Notes transférées: {transfer.get('records_count', 0)}\n"
            f"Documents transférés: {transfer.get('documents_count', 0)}\n"
            f"Crédits totaux: {transfer.get('total_credits', 0)}\n"
        )
        
        ctk.CTkLabel(
            scroll, text=info_text, font=ctk.CTkFont(size=12), text_color=self.colors["text_dark"], justify="left"
        ).pack(pady=10, anchor="w")
        
        # Close button
        ctk.CTkButton(
            scroll, text="Fermer", fg_color=self.colors["primary"], command=dialog.destroy, height=40
        ).pack(pady=10, fill="x")
    
    def _get_all_promotions(self):
        """Récupère toutes les promotions avec départements"""
        try:
            conn = self.transfer_service.db.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT p.id, p.name, d.name as department_name, f.name as faculty_name
                FROM promotion p
                LEFT JOIN department d ON p.department_id = d.id
                LEFT JOIN faculty f ON d.faculty_id = f.id
                WHERE p.is_active = TRUE
                ORDER BY f.name, d.name, p.name
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des promotions: {e}", exc_info=True)
            return []
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.transfer_service.db.close_connection(conn)
    
    def _clear_content(self):
        """Efface le contenu"""
        self._stop_esp32_status_polling()
        self._esp32_status_label = None
        self._cancel_scheduled_renders()
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        if not self._loading_visible:
            self._animate_view_transition()
    
    def _on_language_change(self, value):
        """Change la langue"""
        if self._ui_rebuild_in_progress:
            return

        if value == self.selected_language:
            return

        self._ui_rebuild_in_progress = True
        self._view_switch_in_progress = True
        self.selected_language = value
        self.translator.set_language(value)
        set_current_language(value)
        self._persist_ui_context(language=value, view=self.current_view)
        self._show_loading_overlay("Application de la langue...")
        self._recreate_ui()
        logger.info(f"Langue changée à: {value}")
    
    def _confirm_logout(self):
        """Demande confirmation avant déconnexion"""
        result = messagebox.askyesno(
            self._t("logout_confirm_title", "Confirmation de déconnexion"),
            self._t("logout_confirm_message", "Êtes-vous sûr de vouloir vous déconnecter?\n\nVous devrez vous reconnecter pour accéder au système."),
            icon="question"
        )
        
        if result:
            self._on_logout()
    
    def _on_logout(self):
        """Déconnecte l'utilisateur"""
        logger.info("Déconnexion de l'utilisateur")
        try:
            self._stop_idle_watcher()
            self._stop_translation_watchdog()
            self._stop_esp32_status_polling()
            if hasattr(self.parent_window, "handle_user_logout"):
                try:
                    self.parent_window.handle_user_logout()
                except Exception:
                    pass
            # Afficher un message de déconnexion
            self._show_loading_overlay(self._t("logging_out", "Déconnexion en cours..."))
            
            # Nettoyer les ressources
            if hasattr(self.parent_window, "dashboard"):
                self.parent_window.dashboard = None
            
            # Détruire le dashboard
            self.destroy()
            
            # Retourner à l'écran de login
            if hasattr(self.parent_window, "_show_login"):
                self.parent_window._show_login(animate=True)
                
            logger.info("Déconnexion réussie")
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
            try:
                self.destroy()
            except Exception:
                pass
