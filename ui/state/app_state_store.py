"""Persistance locale de l'état UI/session utilisateur."""

from __future__ import annotations

import json
import os
from typing import Any, Dict


class AppStateStore:
    """Stocke et restaure les préférences applicatives.

    NOTE: le mot de passe est stocké localement en clair pour supporter
    le comportement "Se souvenir de moi" attendu (auto-remplissage/auto-login).
    """

    DEFAULT_STATE: Dict[str, Any] = {
        "language": "FR",
        "theme": "light",
        "last_view": "dashboard",
        "remember_me": False,
        "saved_identifier": "",
        "saved_password": "",
        "auto_login": False,
    }

    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.file_path = os.path.join(root_dir, ".uor_app_state.json")

    def load(self) -> Dict[str, Any]:
        if not os.path.exists(self.file_path):
            return dict(self.DEFAULT_STATE)

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = dict(self.DEFAULT_STATE)
                if isinstance(data, dict):
                    merged.update(data)
                return merged
        except Exception:
            return dict(self.DEFAULT_STATE)

    def save(self, state: Dict[str, Any]):
        data = dict(self.DEFAULT_STATE)
        data.update(state or {})
        os.makedirs(self.root_dir, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def update(self, **kwargs):
        state = self.load()
        state.update(kwargs)
        self.save(state)

    def clear_saved_login(self):
        self.update(
            remember_me=False,
            saved_identifier="",
            saved_password="",
            auto_login=False,
        )
