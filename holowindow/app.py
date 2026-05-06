"""Application bootstrap for HoloWindow."""

from __future__ import annotations


def main() -> int:
    """Start the desktop application."""
    from holowindow.rendering.renderer import run_app

    return run_app()
