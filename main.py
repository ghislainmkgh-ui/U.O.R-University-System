"""Point d'entrée principal de l'application U.O.R"""
import sys
import os
import logging
import threading
from time import perf_counter, sleep


def _ensure_project_venv():
    """Relance automatiquement l'application avec le Python du .venv du projet.

    Objectif: garantir le même environnement d'exécution (dépendances, face_recognition, etc.)
    quel que soit le terminal/launcher utilisé.
    """
    if os.environ.get("UOR_SKIP_VENV_REEXEC") == "1":
        return

    project_root = os.path.dirname(os.path.abspath(__file__))
    if os.name == "nt":
        venv_python = os.path.join(project_root, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(project_root, ".venv", "bin", "python")

    if not os.path.exists(venv_python):
        return

    current_python = os.path.abspath(sys.executable)
    target_python = os.path.abspath(venv_python)
    if current_python.lower() == target_python.lower():
        return

    print(f"[UOR] Interpréteur détecté: {current_python}")
    print(f"[UOR] Bascule automatique vers l'environnement projet: {target_python}")
    os.execv(target_python, [target_python, *sys.argv])


_ensure_project_venv()

import customtkinter as ctk
from ui.i18n.translator import translate_ui_text
from ui.state.app_state_store import AppStateStore

# Ajouter le répertoire racine à sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialiser le logging
from config.logger import logger
from config.settings import APP_NAME, APP_VERSION, DEBUG

logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
logger.info(f"Debug mode: {DEBUG}")

STARTUP_T0 = perf_counter()


def _install_runtime_guards():
    """Installe des garde-fous pour journaliser les exceptions non gérées."""

    def _global_excepthook(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unhandled exception (global)", exc_info=(exc_type, exc_value, exc_traceback))

    def _thread_excepthook(args):
        logger.critical(
            "Unhandled exception in thread %s",
            getattr(args.thread, "name", "unknown"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _global_excepthook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_excepthook


_install_runtime_guards()

try:
    from ui.screens.login_screen import LoginScreen
    from ui.theme.theme_manager import ThemeManager
    
    class AppWrapper(ctk.CTk):
        """Wrapper principal qui gère le login et le dashboard"""

        def report_callback_exception(self, exc, val, tb):
            """Capture les exceptions Tkinter callback pour éviter les crashs silencieux."""
            logger.critical("Tk callback exception", exc_info=(exc, val, tb))
        
        def __init__(self):
            super().__init__()
            init_t0 = perf_counter()
            
            self.title("U.O.R - Système de Contrôle d'Accès")
            
            # Calcul responsive de la géométrie initiale
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Default size: shell applicatif qui héberge ensuite les "pages"
            default_width = max(640, min(1200, int(screen_width * 0.72)))
            default_height = max(680, min(920, int(screen_height * 0.80)))
            
            # Centrer
            x = (screen_width - default_width) // 2
            y = (screen_height - default_height) // 2
            
            self.geometry(f"{default_width}x{default_height}+{x}+{y}")
            self.minsize(520, 620)
            self.maxsize(screen_width, screen_height)
            
            self.current_screen = None
            self.login_screen = None
            self.dashboard = None
            self.current_user = None
            self.language = "FR"
            self.theme = ThemeManager("light")
            self._page_transition_in_progress = False
            self.state_store = AppStateStore(os.path.dirname(os.path.abspath(__file__)))
            self.app_state = self.state_store.load()

            # Restaurer préférences globales
            self.language = self.app_state.get("language", "FR") or "FR"
            saved_theme = self.app_state.get("theme", "light") or "light"
            self.theme = ThemeManager(saved_theme)
            
            # Bind resize event pour responsive adjustments
            self.bind("<Configure>", self._on_window_resize)
            
            # Lancer le login
            self._show_login()
            # Forcer l'affichage au premier plan
            self.after(150, self._force_show)
            logger.info("AppWrapper initialized in %.1f ms", (perf_counter() - init_t0) * 1000)

        def _persist_state(self, **updates):
            self.app_state.update(updates)
            self.state_store.save(self.app_state)

        def get_saved_login_state(self):
            """Expose l'état login persistant à l'écran de connexion."""
            return dict(self.app_state)

        def handle_login_preferences(self, identifier: str, password: str, remember_me: bool, language: str):
            """Mémorise les préférences liées à la connexion."""
            if remember_me:
                self._persist_state(
                    remember_me=True,
                    saved_identifier=identifier or "",
                    saved_password=password or "",
                    auto_login=False,
                    language=language or self.language,
                )
            else:
                self._persist_state(
                    remember_me=False,
                    saved_identifier="",
                    saved_password="",
                    auto_login=False,
                    language=language or self.language,
                )

        def handle_user_logout(self):
            """Désactive l'auto-login après une déconnexion explicite.

            On conserve les champs "Se souvenir de moi" pour pré-remplissage,
            mais on évite toute reconnexion automatique sans action utilisateur.
            """
            self.current_user = None
            self._persist_state(auto_login=False)

        def update_ui_preferences(self, language=None, theme=None, last_view=None):
            """Mémorise langue/thème/page courante pour restauration au redémarrage."""
            updates = {}
            if language:
                self.language = language
                updates["language"] = language
            if theme:
                self.theme.set_theme(theme)
                updates["theme"] = theme
            if last_view:
                updates["last_view"] = last_view
            if updates:
                self._persist_state(**updates)
        
        def _on_window_resize(self, event=None):
            """Gère les ajustements lors du redimensionnement"""
            try:
                current_page = self.dashboard or self.login_screen
                if current_page and hasattr(current_page, '_on_resize'):
                    current_page._on_resize(event)
                elif current_page and hasattr(current_page, '_on_window_resize'):
                    current_page._on_window_resize(event)
            except Exception as e:
                logger.debug(f"Resize handler error: {e}")

        def _clear_current_page(self):
            """Détruit la page active pour laisser AppWrapper piloter la navigation."""
            for attr_name in ("login_screen", "dashboard"):
                widget = getattr(self, attr_name, None)
                if widget:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
                    setattr(self, attr_name, None)

        def _show_page(self, page_name: str, factory):
            """Affiche une page applicative comme dans une navigation web."""
            self._clear_current_page()
            page = factory()
            self.current_screen = page_name
            return page

        def _animate_page_transition(self, page_name: str, factory):
            """Anime légèrement le changement de page pour un rendu plus fluide."""
            if self._page_transition_in_progress:
                return None

            self._page_transition_in_progress = True
            page = None
            try:
                alpha_supported = True
                try:
                    current_alpha = float(self.attributes("-alpha"))
                except Exception:
                    current_alpha = 1.0
                    alpha_supported = False

                if alpha_supported:
                    for level in (0.96, 0.92, 0.88, 0.84):
                        self.attributes("-alpha", level)
                        self.update_idletasks()
                        sleep(0.015)

                page = self._show_page(page_name, factory)

                if alpha_supported:
                    for level in (0.88, 0.92, 0.96, 1.0):
                        self.attributes("-alpha", level)
                        self.update_idletasks()
                        sleep(0.015)
                    self.attributes("-alpha", current_alpha if current_alpha > 0 else 1.0)
                return page
            finally:
                try:
                    self.attributes("-alpha", 1.0)
                except Exception:
                    pass
                self._page_transition_in_progress = False
        
        def _show_login(self, animate: bool = False):
            """Affiche la page login comme page d'entrée de l'application."""
            logger.info("Showing login screen")
            login_t0 = perf_counter()
            page_factory = lambda: LoginScreen(parent_app=self, parent=self)
            if animate:
                self.login_screen = self._animate_page_transition("login", page_factory)
            else:
                self.login_screen = self._show_page("login", page_factory)
            self.current_screen = "login"
            self._force_show()
            logger.info("Login screen ready in %.1f ms", (perf_counter() - login_t0) * 1000)

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
        
        def _show_dashboard(self, language="FR", animate: bool = False, user: dict = None):
            """Affiche le dashboard comme une nouvelle page de l'application."""
            logger.info("Showing dashboard")
            self.language = language
            if user is not None:
                self.current_user = user
            initial_view = self.app_state.get("last_view", "dashboard") or "dashboard"

            from ui.screens.admin.admin_dashboard import AdminDashboard
            page_factory = lambda: AdminDashboard(
                parent=self,
                language=language,
                theme=self.theme,
                initial_view=initial_view,
                current_user=self.current_user,
            )
            if animate:
                self.dashboard = self._animate_page_transition("dashboard", page_factory)
            else:
                self.dashboard = self._show_page("dashboard", page_factory)
            self.current_screen = "dashboard"

        def open_dashboard_page(self, language="FR", progress=None, user: dict = None):
            """Navigation centralisée depuis le login vers le dashboard."""
            nav_t0 = perf_counter()
            try:
                self.language = language
                if progress:
                    progress.set_progress(45, translate_ui_text("Initialisation de la page d'accueil...", self.language))

                self._show_dashboard(language=language, animate=True, user=user)

                if progress:
                    progress.set_progress(80, translate_ui_text("Chargement des données...", self.language))
                self.update_idletasks()

                if progress:
                    progress.set_progress(95, translate_ui_text("Finalisation...", self.language))
                    progress.complete()

                self._force_show()
                logger.info("Dashboard page opened in %.1f ms", (perf_counter() - nav_t0) * 1000)
            except Exception:
                if progress:
                    try:
                        progress.place_forget()
                    except Exception:
                        pass
                raise
    
    def main():
        """Lance l'application"""
        logger.info("Startup pre-mainloop: %.1f ms", (perf_counter() - STARTUP_T0) * 1000)
        app = AppWrapper()
        app.mainloop()
    
    if __name__ == "__main__":
        main()
        logger.info("Application terminated normally")
        
except Exception as e:
    logger.critical(f"Failed to start application: {e}", exc_info=True)
    sys.exit(1)
