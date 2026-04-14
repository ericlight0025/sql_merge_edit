"""Theme and style configuration for the Tkinter GUI.

This module centralizes theme setup so the large GUI class can stay focused on
layout and behavior.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def configure_theme(app) -> None:
    """Apply theme settings to the SqlMergeApp instance.

    The function mutates the app instance by assigning font attributes and
    configuring ttk styles. It expects the app object to provide color
    attributes like BG, SURFACE, TEXT, etc.
    """
    root = app.root
    root.configure(bg=app.BG)

    default_font = ("Microsoft JhengHei UI", 10)
    heading_font = ("Microsoft JhengHei UI Semibold", 11)
    hero_font = ("Microsoft JhengHei UI Semibold", 22)
    mono_font = ("Consolas", 10)

    app.default_font = default_font
    app.heading_font = heading_font
    app.hero_font = hero_font
    app.mono_font = mono_font

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        # fallback silently if theme is unavailable on platform
        pass

    style.configure(".", background=app.BG, foreground=app.TEXT, font=default_font)
    style.configure("App.TFrame", background=app.BG)
    style.configure("Panel.TFrame", background=app.SURFACE)
    style.configure("Header.TFrame", background=app.SURFACE_ALT)
    style.configure("Card.TFrame", background=app.SURFACE)
    style.configure("CardInner.TFrame", background=app.PANEL)

    style.configure("App.TNotebook", background=app.BG, borderwidth=0, tabmargins=(0, 8, 0, 0))
    style.configure(
        "App.TNotebook.Tab",
        background=app.SURFACE_ALT,
        foreground=app.MUTED,
        padding=(18, 10),
        borderwidth=0,
    )
    style.map(
        "App.TNotebook.Tab",
        background=[("selected", app.SURFACE), ("active", "#20304d")],
        foreground=[("selected", app.TEXT), ("active", app.TEXT)],
    )

    style.configure(
        "Title.TLabel",
        background=app.SURFACE_ALT,
        foreground=app.TEXT,
        font=hero_font,
    )
    style.configure("Subtitle.TLabel", background=app.SURFACE_ALT, foreground=app.MUTED, font=("Microsoft JhengHei UI", 10))
    style.configure("Section.TLabel", background=app.SURFACE, foreground=app.TEXT, font=heading_font)
    style.configure("Body.TLabel", background=app.SURFACE, foreground=app.MUTED)
    style.configure("Field.TLabel", background=app.PANEL, foreground=app.MUTED)
    style.configure("Status.TLabel", background=app.SURFACE_ALT, foreground=app.TEXT, font=("Microsoft JhengHei UI", 10))
    style.configure("Count.TLabel", background=app.SURFACE, foreground=app.ACCENT, font=("Consolas", 10, "bold"))

    style.configure(
        "TEntry",
        fieldbackground=app.INPUT_BG,
        foreground=app.TEXT,
        bordercolor=app.INPUT_BORDER,
        lightcolor=app.INPUT_BORDER,
        darkcolor=app.INPUT_BORDER,
        insertcolor=app.TEXT,
        padding=8,
    )
    style.map("TEntry", bordercolor=[("focus", app.ACCENT)], lightcolor=[("focus", app.ACCENT)], darkcolor=[("focus", app.ACCENT)])

    style.configure(
        "TCombobox",
        fieldbackground=app.INPUT_BG,
        foreground=app.TEXT,
        bordercolor=app.INPUT_BORDER,
        lightcolor=app.INPUT_BORDER,
        darkcolor=app.INPUT_BORDER,
        arrowsize=16,
        padding=6,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", app.INPUT_BG)],
        foreground=[("readonly", app.TEXT)],
        bordercolor=[("focus", app.ACCENT)],
        lightcolor=[("focus", app.ACCENT)],
        darkcolor=[("focus", app.ACCENT)],
    )

    style.configure(
        "Accent.TButton",
        background=app.ACCENT,
        foreground="#071217",
        bordercolor=app.ACCENT,
        lightcolor=app.ACCENT,
        darkcolor=app.ACCENT,
        padding=(14, 8),
        font=("Microsoft JhengHei UI Semibold", 10),
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#73eed1"), ("pressed", "#3fc8ac")],
        foreground=[("disabled", "#34525e")],
    )

    style.configure(
        "Ghost.TButton",
        background=app.SURFACE_ALT,
        foreground=app.TEXT,
        bordercolor=app.BORDER,
        lightcolor=app.BORDER,
        darkcolor=app.BORDER,
        padding=(12, 8),
    )
    style.map("Ghost.TButton", background=[("active", "#20304d"), ("pressed", "#18253c")])

    style.configure(
        "Warn.TButton",
        background="#342515",
        foreground=app.WARNING,
        bordercolor="#5c4426",
        lightcolor="#5c4426",
        darkcolor="#5c4426",
        padding=(12, 8),
    )
    style.map("Warn.TButton", background=[("active", "#48331d"), ("pressed", "#2e2113")])
