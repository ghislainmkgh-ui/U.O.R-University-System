"""Utilitaires responsive partagés pour les écrans Tk/CustomTkinter."""

from __future__ import annotations

from typing import Tuple


def get_viewport_metrics(widget) -> Tuple[int, int, int, int]:
    """Retourne (width, height, root_x, root_y) pour la fenêtre principale visible."""
    top = widget.winfo_toplevel()
    top.update_idletasks()

    width = top.winfo_width() or top.winfo_screenwidth()
    height = top.winfo_height() or top.winfo_screenheight()
    root_x = top.winfo_rootx()
    root_y = top.winfo_rooty()
    return width, height, root_x, root_y


def fit_dialog_to_viewport(
    parent_widget,
    dialog,
    desired_width: int,
    desired_height: int,
    *,
    min_width: int = 280,
    min_height: int = 140,
    width_ratio: float = 0.92,
    height_ratio: float = 0.88,
) -> Tuple[int, int, int, int]:
    """Ajuste et centre un dialogue dans l'espace visible du parent.

    Retourne (width, height, x, y).
    """
    viewport_width, viewport_height, root_x, root_y = get_viewport_metrics(parent_widget)

    width = max(min_width, min(desired_width, int(viewport_width * width_ratio)))
    height = max(min_height, min(desired_height, int(viewport_height * height_ratio)))

    x = root_x + max((viewport_width - width) // 2, 0)
    y = root_y + max((viewport_height - height) // 2, 0)

    dialog.geometry(f"{width}x{height}+{x}+{y}")
    return width, height, x, y


def fit_existing_dialog(
    parent_widget,
    dialog,
    *,
    min_width: int = 320,
    min_height: int = 120,
    width_ratio: float = 0.92,
    height_ratio: float = 0.88,
) -> Tuple[int, int, int, int]:
    """Ajuste un dialogue déjà dimensionné pour qu'il reste visible, puis le centre."""
    dialog.update_idletasks()
    desired_width = max(dialog.winfo_width(), min_width)
    desired_height = max(dialog.winfo_height(), min_height)
    return fit_dialog_to_viewport(
        parent_widget,
        dialog,
        desired_width,
        desired_height,
        min_width=min_width,
        min_height=min_height,
        width_ratio=width_ratio,
        height_ratio=height_ratio,
    )
