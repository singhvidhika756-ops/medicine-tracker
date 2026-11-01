"""
settings.py — System Preferences and Backup Management View for MediVault.

Allows users to switch themes (Light/Dark), configure application settings,
create and restore database backups, and import/export master CSV datasets.
"""

import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import TYPE_CHECKING

from ui.widgets import DataTable, ConfirmDialog
from utils.backup import (
    create_backup, restore_backup, list_backups,
    export_all_to_csv, import_medicines_from_csv
)

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class SettingsView(tk.Frame):
    """
    Settings, preferences, and database maintenance view.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp'):
        self.app = app
        self.tm = app.theme_manager
        c = self.tm.colors

        super().__init__(parent, bg=c['bg'])

        self._build_ui()

    def _build_ui(self):
        c = self.tm.colors

        # Header
        header = tk.Frame(self, bg=c['bg'])
        header.pack(fill='x', padx=24, pady=(20, 10))

        title_frame = tk.Frame(header, bg=c['bg'])
        title_frame.pack(side='left')

        tk.Label(
            title_frame, text="⚙️ System Settings & Data Management",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Configure theme appearance, database snapshots, and data integrity",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        # Two-Column Layout (Left: Preferences & Actions | Right: Backups Table)
        container = tk.Frame(self, bg=c['bg'])
        container.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        # LEFT COLUMN (Theme, CSV Operations, System Info)
        left_col = tk.Frame(container, bg=c['bg'], width=400)
        left_col.pack(side='left', fill='both', padx=(0, 10))

        # 1. Appearance Card
        card_theme = tk.Frame(left_col, bg=c['card_bg'],
                              highlightbackground=c['card_border'], highlightthickness=1)
        card_theme.pack(fill='x', pady=(0, 12))

        tk.Label(
            card_theme, text="🎨 Appearance & Theme",
            font=('Segoe UI', 12, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w', padx=16, pady=(14, 6))

        tk.Label(
            card_theme, text="Toggle between light and dark user interface modes:",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', padx=16, pady=(0, 8))

        theme_btn_box = tk.Frame(card_theme, bg=c['card_bg'])
        theme_btn_box.pack(fill='x', padx=16, pady=(0, 14))

        self.theme_var = tk.StringVar(value=self.tm.current_theme)

        ttk.Radiobutton(
            theme_btn_box, text="☀️ Light Theme",
            variable=self.theme_var, value='light',
            command=self._on_theme_changed
        ).pack(side='left', padx=(0, 16))

        ttk.Radiobutton(
            theme_btn_box, text="🌙 Dark Theme",
            variable=self.theme_var, value='dark',
            command=self._on_theme_changed
        ).pack(side='left')

        # 2. Data Import & Export Card
        card_data = tk.Frame(left_col, bg=c['card_bg'],
                             highlightbackground=c['card_border'], highlightthickness=1)
        card_data.pack(fill='x', pady=(0, 12))

        tk.Label(
            card_data, text="📦 Master CSV Operations",
            font=('Segoe UI', 12, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w', padx=16, pady=(14, 6))

        tk.Label(
            card_data, text="Bulk import new medicines or export entire database tables to CSV:",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', padx=16, pady=(0, 10))

        data_btn_box = tk.Frame(card_data, bg=c['card_bg'])
        data_btn_box.pack(fill='x', padx=16, pady=(0, 14))

        ttk.Button(
            data_btn_box, text="📤 Export All Tables to CSV",
            command=self._export_all_csv,
            style='Secondary.TButton'
        ).pack(fill='x', pady=3)

        ttk.Button(
            data_btn_box, text="📥 Import Medicines from CSV",
            command=self._import_medicines_csv,
            style='Secondary.TButton'
        ).pack(fill='x', pady=3)

        # 3. System Diagnostics Info Card
        card_sys = tk.Frame(left_col, bg=c['card_bg'],
                            highlightbackground=c['card_border'], highlightthickness=1)
        card_sys.pack(fill='both', expand=True)

        tk.Label(
            card_sys, text="ℹ️ System Diagnostics",
            font=('Segoe UI', 12, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w', padx=16, pady=(14, 6))

        self.sys_info_box = tk.Frame(card_sys, bg=c['card_bg'])
        self.sys_info_box.pack(fill='both', expand=True, padx=16, pady=(0, 14))

        # RIGHT COLUMN (Database Backup & Restore Manager)
        right_col = tk.Frame(container, bg=c['card_bg'],
                             highlightbackground=c['card_border'], highlightthickness=1)
        right_col.pack(side='right', fill='both', expand=True, padx=(10, 0))

        r_header = tk.Frame(right_col, bg=c['card_bg'])
        r_header.pack(fill='x', padx=16, pady=(14, 8))

        r_title_box = tk.Frame(r_header, bg=c['card_bg'])
        r_title_box.pack(side='left')

        tk.Label(
            r_title_box, text="💾 Database Backups & Snapshots",
            font=('Segoe UI', 12, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            r_title_box, text="Safely capture database states and revert to prior snapshots",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        ttk.Button(
            r_header, text="➕ Backup Database Now",
            command=self._create_backup_now,
            style='Primary.TButton'
        ).pack(side='right')

        # Backups Table
        b_cols = [
            {'key': 'filename', 'label': 'Backup File', 'width': 220},
            {'key': 'date', 'label': 'Creation Date', 'width': 140},
            {'key': 'size', 'label': 'File Size', 'width': 90, 'anchor': 'e'},
        ]

        self.backup_table = DataTable(right_col, b_cols, self.tm)
        self.backup_table.pack(fill='both', expand=True, padx=16, pady=(0, 10))

        r_footer = tk.Frame(right_col, bg=c['card_bg'])
        r_footer.pack(fill='x', padx=16, pady=(0, 14))

        tk.Label(
            r_footer, text="Select a backup file above to restore.",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_muted']
        ).pack(side='left')

        ttk.Button(
            r_footer, text="🔄 Restore Selected Backup",
            command=self._restore_selected_backup,
            style='Danger.TButton'
        ).pack(side='right')

    def refresh(self):
        """Update system diagnostics and list of backup files."""
        # 1. Update Backups Table
        backups = list_backups()
        self.backup_table.populate(backups)

        # 2. Update System Info Diagnostics
        for child in self.sys_info_box.winfo_children():
            child.destroy()

        c = self.tm.colors
        db_path = Path(self.app.db.db_path)
        db_size_kb = (db_path.stat().st_size / 1024) if db_path.exists() else 0

        total_meds = self.app.db.fetchone("SELECT COUNT(*) as c FROM medicines")
        total_batches = self.app.db.fetchone("SELECT COUNT(*) as c FROM batches")
        total_txns = self.app.db.fetchone("SELECT COUNT(*) as c FROM stock_transactions")

        info_items = [
            ("Application Version", "MediVault v1.0.0 (First-Year Edition)"),
            ("Python Runtime", f"{sys.version.split()[0]} ({sys.platform})"),
            ("SQLite Engine", sqlite3.sqlite_version),
            ("Database Location", str(db_path.name)),
            ("Database Size", f"{db_size_kb:.1f} KB"),
            ("Registered Medicines", f"{total_meds['c'] if total_meds else 0} records"),
            ("Active Batches", f"{total_batches['c'] if total_batches else 0} records"),
            ("Audit Transactions", f"{total_txns['c'] if total_txns else 0} logs"),
        ]

        for label, val in info_items:
            row = tk.Frame(self.sys_info_box, bg=c['card_bg'])
            row.pack(fill='x', pady=2)
            tk.Label(
                row, text=label, font=('Segoe UI', 9),
                bg=c['card_bg'], fg=c['text_secondary']
            ).pack(side='left')
            tk.Label(
                row, text=val, font=('Segoe UI', 9, 'bold'),
                bg=c['card_bg'], fg=c['text']
            ).pack(side='right')

    def _on_theme_changed(self):
        new_theme = self.theme_var.get()
        self.app.switch_theme(new_theme)

    def _create_backup_now(self):
        try:
            path = create_backup()
            messagebox.showinfo(
                "Backup Created",
                f"Database snapshot successfully saved:\n{Path(path).name}",
                parent=self
            )
            self.refresh()
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e), parent=self)

    def _restore_selected_backup(self):
        selected = self.backup_table.get_selected()
        if not selected:
            messagebox.showwarning("Select Backup", "Please choose a backup from the list to restore.", parent=self)
            return

        filename = selected['filename']
        if ConfirmDialog.show(
            self, "Confirm Database Restore",
            f"Are you sure you want to restore '{filename}'?\n\n"
            f"A safety backup of the current database will be saved before restoring."
        ):
            try:
                # Close live connection temporarily to permit file overwrite
                self.app.db.close()

                success = restore_backup(selected['path'])
                if success:
                    # Reopen connection
                    self.app.db.get_connection()
                    messagebox.showinfo(
                        "Restore Succeeded",
                        f"Database has been reverted to snapshot:\n{filename}",
                        parent=self
                    )
                    self.app.refresh_all_views()
                else:
                    self.app.db.get_connection()
                    messagebox.showerror("Restore Failed", "Could not restore the selected file.", parent=self)
            except Exception as e:
                self.app.db.get_connection()
                messagebox.showerror("Restore Error", str(e), parent=self)

    def _export_all_csv(self):
        try:
            files = export_all_to_csv(self.app.db)
            if files:
                msg = f"Exported {len(files)} tables to 'exports/' folder:\n\n" + "\n".join(Path(f).name for f in files)
                messagebox.showinfo("Export Complete", msg, parent=self)
            else:
                messagebox.showinfo("No Data", "No records found in tables to export.", parent=self)
        except Exception as e:
            messagebox.showerror("Export Error", str(e), parent=self)

    def _import_medicines_csv(self):
        filepath = filedialog.askopenfilename(
            parent=self,
            title="Select Medicines CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        try:
            count, errors = import_medicines_from_csv(self.app.db, filepath)
            if errors:
                err_msg = "\n".join(errors[:5])
                if len(errors) > 5:
                    err_msg += f"\n...and {len(errors) - 5} more errors."
                messagebox.showwarning(
                    "Import Completed with Warnings",
                    f"Successfully imported {count} medicines.\n\nErrors encountered:\n{err_msg}",
                    parent=self
                )
            else:
                messagebox.showinfo(
                    "Import Successful",
                    f"Successfully imported {count} medicines from CSV!",
                    parent=self
                )
            self.app.refresh_all_views()
        except Exception as e:
            messagebox.showerror("Import Failed", str(e), parent=self)

    def apply_theme(self):
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.theme_var.set(self.tm.current_theme)
        self.refresh()

