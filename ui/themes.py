"""
MediVault Theme Manager
========================
Defines light and dark color themes and a ThemeManager class
that applies consistent styling across the entire application.
"""

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Color theme dictionaries
# ---------------------------------------------------------------------------

LIGHT_THEME = {
    'bg': '#F0F2F5',
    'sidebar_bg': '#1B2A4A',
    'sidebar_fg': '#CBD5E1',
    'sidebar_active_bg': '#2563EB',
    'sidebar_active_fg': '#FFFFFF',
    'sidebar_hover_bg': '#243B5E',
    'card_bg': '#FFFFFF',
    'card_border': '#E2E8F0',
    'primary': '#2563EB',
    'primary_hover': '#1D4ED8',
    'primary_fg': '#FFFFFF',
    'success': '#10B981',
    'success_bg': '#D1FAE5',
    'warning': '#F59E0B',
    'warning_bg': '#FEF3C7',
    'danger': '#EF4444',
    'danger_bg': '#FEE2E2',
    'info': '#3B82F6',
    'info_bg': '#DBEAFE',
    'text': '#1F2937',
    'text_secondary': '#6B7280',
    'text_muted': '#9CA3AF',
    'input_bg': '#FFFFFF',
    'input_border': '#D1D5DB',
    'input_focus_border': '#2563EB',
    'table_header_bg': '#F8FAFC',
    'table_row_alt': '#F9FAFB',
    'table_selected': '#DBEAFE',
    'table_border': '#E5E7EB',
    'scrollbar_bg': '#E5E7EB',
    'scrollbar_fg': '#94A3B8',
}

DARK_THEME = {
    'bg': '#111827',
    'sidebar_bg': '#0F172A',
    'sidebar_fg': '#94A3B8',
    'sidebar_active_bg': '#2563EB',
    'sidebar_active_fg': '#FFFFFF',
    'sidebar_hover_bg': '#1E293B',
    'card_bg': '#1F2937',
    'card_border': '#374151',
    'primary': '#3B82F6',
    'primary_hover': '#2563EB',
    'primary_fg': '#FFFFFF',
    'success': '#34D399',
    'success_bg': '#064E3B',
    'warning': '#FBBF24',
    'warning_bg': '#78350F',
    'danger': '#F87171',
    'danger_bg': '#7F1D1D',
    'info': '#60A5FA',
    'info_bg': '#1E3A5F',
    'text': '#F9FAFB',
    'text_secondary': '#D1D5DB',
    'text_muted': '#6B7280',
    'input_bg': '#374151',
    'input_border': '#4B5563',
    'input_focus_border': '#3B82F6',
    'table_header_bg': '#1F2937',
    'table_row_alt': '#243044',
    'table_selected': '#1E3A5F',
    'table_border': '#374151',
    'scrollbar_bg': '#374151',
    'scrollbar_fg': '#6B7280',
}

# Map theme names to dicts for easy lookup
THEMES = {
    'light': LIGHT_THEME,
    'dark': DARK_THEME,
}


class ThemeManager:
    """
    Manages the application theme (light / dark).
    Configures all ttk styles to match the active colour palette.

    Usage:
        theme_mgr = ThemeManager(root, default='light')
        theme_mgr.switch_theme('dark')
        colours = theme_mgr.colors
    """

    # Fonts used throughout the app (Windows-friendly)
    FONT_FAMILY = 'Segoe UI'
    FONT_TITLE = ('Segoe UI', 20, 'bold')
    FONT_SUBTITLE = ('Segoe UI', 14, 'bold')
    FONT_CARD_VALUE = ('Segoe UI', 26, 'bold')
    FONT_CARD_TITLE = ('Segoe UI', 10)
    FONT_BODY = ('Segoe UI', 10)
    FONT_BODY_BOLD = ('Segoe UI', 10, 'bold')
    FONT_SMALL = ('Segoe UI', 9)
    FONT_BUTTON = ('Segoe UI', 10)
    FONT_TABLE = ('Segoe UI', 10)
    FONT_TABLE_HEADER = ('Segoe UI', 10, 'bold')

    def __init__(self, root: tk.Tk, default: str = 'light'):
        self._root = root
        self._current = default if default in THEMES else 'light'
        self._style = ttk.Style(root)
        # Apply styles on startup
        self.apply_styles()

    # -- Public properties ---------------------------------------------------

    @property
    def current_theme(self) -> str:
        """Return the name of the active theme ('light' or 'dark')."""
        return self._current

    @property
    def colors(self) -> dict:
        """Return the colour dictionary of the active theme."""
        return THEMES[self._current]

    # -- Public methods ------------------------------------------------------

    def switch_theme(self, theme_name: str):
        """Switch to *theme_name* and re-apply all ttk styles."""
        if theme_name not in THEMES:
            return
        self._current = theme_name
        self.apply_styles()

    def apply_styles(self):
        """Configure every ttk style to match the current theme colours."""
        c = self.colors
        style = self._style

        # Use 'clam' as the base — it gives the most control
        style.theme_use('clam')

        # ---- Root / TFrame -------------------------------------------------
        style.configure('.', background=c['bg'], foreground=c['text'],
                        font=self.FONT_BODY)
        style.configure('TFrame', background=c['bg'])
        style.configure('Card.TFrame', background=c['card_bg'],
                        relief='solid', borderwidth=1)

        # ---- TLabel --------------------------------------------------------
        style.configure('TLabel', background=c['bg'], foreground=c['text'],
                        font=self.FONT_BODY)
        style.configure('Title.TLabel', font=self.FONT_TITLE,
                        foreground=c['text'], background=c['bg'])
        style.configure('Subtitle.TLabel', font=self.FONT_SUBTITLE,
                        foreground=c['text'], background=c['bg'])
        style.configure('CardValue.TLabel', font=self.FONT_CARD_VALUE,
                        foreground=c['text'], background=c['card_bg'])
        style.configure('CardTitle.TLabel', font=self.FONT_CARD_TITLE,
                        foreground=c['text_secondary'],
                        background=c['card_bg'])
        style.configure('CardIcon.TLabel', font=('Segoe UI', 24),
                        background=c['card_bg'])
        style.configure('Muted.TLabel', foreground=c['text_muted'],
                        background=c['bg'])
        style.configure('Error.TLabel', foreground=c['danger'],
                        background=c['bg'], font=self.FONT_SMALL)
        style.configure('Card.TLabel', background=c['card_bg'],
                        foreground=c['text'])

        # ---- TButton (primary) ---------------------------------------------
        style.configure('TButton',
                        font=self.FONT_BUTTON,
                        padding=(14, 6),
                        background=c['primary'],
                        foreground=c['primary_fg'],
                        borderwidth=0)
        style.map('TButton',
                  background=[('active', c['primary_hover']),
                              ('disabled', c['text_muted'])],
                  foreground=[('disabled', c['bg'])])

        # Primary.TButton — explicit alias
        style.configure('Primary.TButton',
                        background=c['primary'],
                        foreground=c['primary_fg'],
                        font=self.FONT_BUTTON,
                        padding=(14, 6))
        style.map('Primary.TButton',
                  background=[('active', c['primary_hover'])])

        # Danger / destructive button
        style.configure('Danger.TButton',
                        background=c['danger'],
                        foreground='#FFFFFF',
                        font=self.FONT_BUTTON,
                        padding=(14, 6))
        style.map('Danger.TButton',
                  background=[('active', '#DC2626')])

        # Success button
        style.configure('Success.TButton',
                        background=c['success'],
                        foreground='#FFFFFF',
                        font=self.FONT_BUTTON,
                        padding=(14, 6))
        style.map('Success.TButton',
                  background=[('active', '#059669')])

        # Secondary (gray) button
        style.configure('Secondary.TButton',
                        background=c['input_border'],
                        foreground=c['text'],
                        font=self.FONT_BUTTON,
                        padding=(14, 6))
        style.map('Secondary.TButton',
                  background=[('active', c['text_muted'])])

        # ---- TEntry --------------------------------------------------------
        style.configure('TEntry',
                        fieldbackground=c['input_bg'],
                        foreground=c['text'],
                        bordercolor=c['input_border'],
                        lightcolor=c['input_border'],
                        darkcolor=c['input_border'],
                        insertcolor=c['text'],
                        padding=6)
        style.map('TEntry',
                  bordercolor=[('focus', c['input_focus_border'])],
                  lightcolor=[('focus', c['input_focus_border'])])

        # ---- TCombobox -----------------------------------------------------
        style.configure('TCombobox',
                        fieldbackground=c['input_bg'],
                        foreground=c['text'],
                        background=c['input_bg'],
                        bordercolor=c['input_border'],
                        arrowcolor=c['text_secondary'],
                        padding=6)
        style.map('TCombobox',
                  fieldbackground=[('readonly', c['input_bg'])],
                  foreground=[('readonly', c['text'])],
                  bordercolor=[('focus', c['input_focus_border'])])

        # ---- Treeview (data table) -----------------------------------------
        style.configure('Treeview',
                        background=c['card_bg'],
                        foreground=c['text'],
                        fieldbackground=c['card_bg'],
                        borderwidth=0,
                        font=('Segoe UI', 10),
                        rowheight=34)
        style.configure('Treeview.Heading',
                        background=c['table_header_bg'],
                        foreground=c['text'],
                        font=('Segoe UI', 10, 'bold'),
                        padding=(10, 8),
                        relief='flat',
                        borderwidth=1)
        style.map('Treeview',
                  background=[('selected', c['table_selected'])],
                  foreground=[('selected', c['text'])])
        style.map('Treeview.Heading',
                  background=[('active', c['table_header_bg'])])

        # ---- TNotebook -----------------------------------------------------
        style.configure('TNotebook', background=c['bg'], borderwidth=0)
        style.configure('TNotebook.Tab',
                        background=c['card_bg'],
                        foreground=c['text'],
                        padding=(14, 6),
                        font=self.FONT_BODY)
        style.map('TNotebook.Tab',
                  background=[('selected', c['primary'])],
                  foreground=[('selected', c['primary_fg'])])

        # ---- TSpinbox ------------------------------------------------------
        style.configure('TSpinbox',
                        fieldbackground=c['input_bg'],
                        foreground=c['text'],
                        bordercolor=c['input_border'],
                        arrowcolor=c['text_secondary'],
                        padding=4)

        # ---- TLabelframe ---------------------------------------------------
        style.configure('TLabelframe',
                        background=c['card_bg'],
                        foreground=c['text'],
                        bordercolor=c['card_border'])
        style.configure('TLabelframe.Label',
                        background=c['card_bg'],
                        foreground=c['text'],
                        font=self.FONT_BODY_BOLD)

        # ---- Vertical.TScrollbar ------------------------------------------
        style.configure('Vertical.TScrollbar',
                        background=c['scrollbar_fg'],
                        troughcolor=c['scrollbar_bg'],
                        borderwidth=0,
                        arrowcolor=c['text_muted'])

        # ---- TSeparator ----------------------------------------------------
        style.configure('TSeparator', background=c['card_border'])

        # ---- TProgressbar -------------------------------------------------
        style.configure('TProgressbar',
                        background=c['primary'],
                        troughcolor=c['scrollbar_bg'])

        # Apply bg to root window
        self._root.configure(bg=c['bg'])
