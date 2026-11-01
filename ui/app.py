"""
app.py — Main Application Window for MediVault.

Constructs the top-level Tkinter window, binds the database manager and services,
initialises the left sidebar navigation, and switches between application views.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from database.connection import DatabaseManager
from services.medicine_service import MedicineService
from services.inventory_service import InventoryService
from services.expiry_service import ExpiryService
from services.report_service import ReportService
from ui.themes import ThemeManager
from ui.widgets import SidebarNav

from ui.dashboard import DashboardView
from ui.medicines import MedicinesView
from ui.batches import BatchesView
from ui.alerts import AlertsView
from ui.stock import StockView
from ui.reports import ReportsView
from ui.settings import SettingsView
from utils.logger import setup_logger

logger = setup_logger('medivault.app')


class MediVaultApp(tk.Tk):
    """
    Main MediVault desktop application window.
    """

    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db

        # 1. Initialize Services
        self.medicine_service = MedicineService(db)
        self.inventory_service = InventoryService(db)
        self.expiry_service = ExpiryService(db)
        self.report_service = ReportService(db)

        # 2. Window Configurations
        self.title("MediVault — Medicine Inventory & Expiry Management System")
        self.geometry("1220x760")
        self.minsize(1020, 640)

        # 3. Theme Manager
        saved_theme = self._get_saved_theme()
        self.theme_manager = ThemeManager(self, default=saved_theme)

        # 4. Build Layout
        self._build_layout()

        # 5. Initialize Views
        self._init_views()

        # 6. Global Keyboard Shortcuts
        self._bind_shortcuts()

        # 7. Show Default View (Dashboard)
        self.show_view('dashboard')

        # 8. Protocol Handling
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_shortcuts(self):
        """Register friendly global keyboard accelerators."""
        self.bind('<Control-n>', lambda e: self.show_view('medicines', action='add'))
        self.bind('<Control-N>', lambda e: self.show_view('medicines', action='add'))
        self.bind('<Control-b>', lambda e: self._shortcut_add_batch())
        self.bind('<Control-B>', lambda e: self._shortcut_add_batch())
        self.bind('<F5>', lambda e: self.refresh_all_views())
        self.bind('<Control-r>', lambda e: self.refresh_all_views())
        self.bind('<Control-R>', lambda e: self.refresh_all_views())

    def _shortcut_add_batch(self):
        self.show_view('batches')
        batch_view = self.views.get('batches')
        if batch_view and hasattr(batch_view, 'open_add_dialog'):
            self.after(50, batch_view.open_add_dialog)

    def _get_saved_theme(self) -> str:
        """Fetch saved theme preference from application_settings table."""
        try:
            row = self.db.fetchone("SELECT value FROM application_settings WHERE key = 'theme'")
            if row and row['value'] in ('light', 'dark'):
                return row['value']
        except Exception:
            pass
        return 'light'

    def _build_layout(self):
        c = self.theme_manager.colors

        # Main wrapper
        self.main_container = tk.Frame(self, bg=c['bg'])
        self.main_container.pack(fill='both', expand=True)

        # Left Sidebar Navigation
        self.sidebar = SidebarNav(
            self.main_container,
            self.theme_manager,
            on_navigate=self.show_view
        )
        self.sidebar.pack(side='left', fill='y')

        # Right Content Viewport
        self.content_container = tk.Frame(self.main_container, bg=c['bg'])
        self.content_container.pack(side='right', fill='both', expand=True)

        # Bottom Friendly Status Bar
        self.status_bar = tk.Frame(self, bg=c['card_border'], height=24)
        self.status_bar.pack(side='bottom', fill='x')
        self.status_bar.pack_propagate(False)

        self.lbl_status_db = tk.Label(
            self.status_bar, text="🟢 Local Database: Connected (data/medivault.db)",
            font=('Segoe UI', 8), bg=c['card_border'], fg=c['text_secondary']
        )
        self.lbl_status_db.pack(side='left', padx=14)

        self.lbl_shortcuts = tk.Label(
            self.status_bar, text="⌨️ Shortcuts: [Ctrl+N] Add Med  |  [Ctrl+B] Add Batch  |  [F5] Refresh",
            font=('Segoe UI', 8), bg=c['card_border'], fg=c['text_muted']
        )
        self.lbl_shortcuts.pack(side='left', padx=24)

        self.lbl_status_theme = tk.Label(
            self.status_bar, text=f"Theme: {self.theme_manager.current_theme.capitalize()}",
            font=('Segoe UI', 8, 'bold'), bg=c['card_border'], fg=c['text_secondary']
        )
        self.lbl_status_theme.pack(side='right', padx=14)

    def _init_views(self):
        """Construct view frames inside content_container."""
        self.views: Dict[str, tk.Frame] = {
            'dashboard': DashboardView(self.content_container, self),
            'medicines': MedicinesView(self.content_container, self),
            'batches': BatchesView(self.content_container, self),
            'alerts': AlertsView(self.content_container, self),
            'stock': StockView(self.content_container, self),
            'reports': ReportsView(self.content_container, self),
            'settings': SettingsView(self.content_container, self),
        }
        self.current_view_key: Optional[str] = None

    def show_view(self, name: str, **kwargs):
        """
        Switch visible view in the content container.

        Args:
            name: View key ('dashboard', 'medicines', 'batches', etc.)
            **kwargs: Extra arguments passed to view hooks.
        """
        if name not in self.views:
            logger.warning("Attempted to navigate to unknown view: %s", name)
            return

        # Hide currently active view
        if self.current_view_key and self.current_view_key in self.views:
            self.views[self.current_view_key].pack_forget()

        # Update sidebar highlight
        self.sidebar.set_active(name)
        self.current_view_key = name
        view = self.views[name]

        # Handle specific view triggers
        if name == 'batches' and 'filter_medicine_id' in kwargs:
            view.set_medicine_filter(kwargs['filter_medicine_id'])
        elif name == 'medicines' and kwargs.get('action') == 'add':
            view.refresh()
            self.after(50, view.open_add_dialog)
        else:
            view.refresh()

        view.pack(fill='both', expand=True)
        logger.debug("Switched view to '%s'", name)

    def switch_theme(self, theme_name: str):
        """Switch application color scheme between light and dark."""
        self.theme_manager.switch_theme(theme_name)
        c = self.theme_manager.colors

        # Persist choice in DB
        try:
            self.db.execute(
                "INSERT OR REPLACE INTO application_settings (key, value) VALUES ('theme', ?)",
                (theme_name,)
            )
        except Exception as e:
            logger.error("Failed to persist theme setting: %s", e)

        # Apply to main frames
        self.configure(bg=c['bg'])
        self.main_container.configure(bg=c['bg'])
        self.content_container.configure(bg=c['bg'])

        # Apply to sidebar
        self.sidebar.apply_theme()

        # Apply to status bar
        if hasattr(self, 'status_bar'):
            self.status_bar.configure(bg=c['card_border'])
            self.lbl_status_db.configure(bg=c['card_border'], fg=c['text_secondary'])
            self.lbl_shortcuts.configure(bg=c['card_border'], fg=c['text_muted'])
            self.lbl_status_theme.configure(
                bg=c['card_border'], fg=c['text_secondary'],
                text=f"Theme: {theme_name.capitalize()}"
            )

        # Apply to each view
        for view in self.views.values():
            if hasattr(view, 'apply_theme'):
                view.apply_theme()

    def refresh_all_views(self):
        """Re-render current view after global data changes like restores."""
        if self.current_view_key and self.current_view_key in self.views:
            self.views[self.current_view_key].refresh()

    def _on_close(self):
        """Clean up resources on application window exit."""
        logger.info("Closing MediVault application.")
        self.destroy()

