"""
alerts.py — Expiry and Stock Alert Center for MediVault.

Provides categorised views for Expired, Critical (≤7d), Warning (8-15d),
Upcoming (16-30d), and Low-Stock medicines with quick disposal and restock actions.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Dict, Any, List

from ui.widgets import DataTable, ConfirmDialog

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class AlertsView(tk.Frame):
    """
    Expiry and stock alerts view with notebook tabs for each urgency tier.
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
            title_frame, text="⚠️ Expiry & Stock Alert Center",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Immediate oversight of expired batches, upcoming shelf-life limits, and stock deficits",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        btn_frame = tk.Frame(header, bg=c['bg'])
        btn_frame.pack(side='right')

        ttk.Button(
            btn_frame, text="🔄 Refresh Alerts",
            command=self.refresh,
            style='Secondary.TButton'
        ).pack(side='right')

        # Safety Disclaimer Box
        disclaimer_box = tk.Frame(self, bg=c['card_bg'],
                                  highlightbackground=c['card_border'], highlightthickness=1)
        disclaimer_box.pack(fill='x', padx=24, pady=(0, 10))

        tk.Label(
            disclaimer_box,
            text="ℹ️ Storage & Safety Notice: Products within valid shelf-life dates are not guaranteed for clinical use without proper storage inspection. This application manages inventory timelines only.",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary'],
            padx=12, pady=8, anchor='w'
        ).pack(fill='x')

        # Notebook for Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=24, pady=(0, 16))

        # 1. Tab: Expired
        self.tab_expired = tk.Frame(self.notebook, bg=c['bg'])
        self.notebook.add(self.tab_expired, text="🚨 Expired (0)")
        self._build_expired_tab()

        # 2. Tab: Critical (<= 7 Days)
        self.tab_crit = tk.Frame(self.notebook, bg=c['bg'])
        self.notebook.add(self.tab_crit, text="⚠️ Critical ≤7d (0)")
        self._build_critical_tab()

        # 3. Tab: Warning (8-15 Days)
        self.tab_warn = tk.Frame(self.notebook, bg=c['bg'])
        self.notebook.add(self.tab_warn, text="⏳ Warning 8-15d (0)")
        self._build_warning_tab()

        # 4. Tab: Upcoming (16-30 Days)
        self.tab_upcom = tk.Frame(self.notebook, bg=c['bg'])
        self.notebook.add(self.tab_upcom, text="📅 Upcoming 16-30d (0)")
        self._build_upcoming_tab()

        # 5. Tab: Low Stock
        self.tab_low = tk.Frame(self.notebook, bg=c['bg'])
        self.notebook.add(self.tab_low, text="📉 Low Stock (0)")
        self._build_low_stock_tab()

    def _build_expired_tab(self):
        c = self.tm.colors
        cols = [
            {'key': 'batch_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 200},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 120},
            {'key': 'expiry_date', 'label': 'Expiry Date', 'width': 100, 'anchor': 'center'},
            {'key': 'days_until_expiry', 'label': 'Expired Ago', 'width': 100, 'anchor': 'e'},
            {'key': 'current_quantity', 'label': 'Units in Stock', 'width': 100, 'anchor': 'e'},
            {'key': 'supplier', 'label': 'Supplier', 'width': 140},
        ]

        card = tk.Frame(self.tab_expired, bg=c['card_bg'],
                        highlightbackground=c['card_border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=8, pady=8)

        self.tbl_expired = DataTable(card, cols, self.tm)
        self.tbl_expired.pack(fill='both', expand=True, padx=8, pady=8)

        # Bottom actions
        bar = tk.Frame(self.tab_expired, bg=c['bg'])
        bar.pack(fill='x', padx=8, pady=(0, 6))

        ttk.Button(
            bar, text="🗑️ Dispose Expired Stock",
            command=self._dispose_expired_batch,
            style='Danger.TButton'
        ).pack(side='right')

    def _build_critical_tab(self):
        c = self.tm.colors
        cols = [
            {'key': 'batch_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 200},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 120},
            {'key': 'expiry_date', 'label': 'Expiry Date', 'width': 100, 'anchor': 'center'},
            {'key': 'days_until_expiry', 'label': 'Days Remaining', 'width': 110, 'anchor': 'e'},
            {'key': 'current_quantity', 'label': 'Current Units', 'width': 100, 'anchor': 'e'},
            {'key': 'supplier', 'label': 'Supplier', 'width': 140},
        ]
        card = tk.Frame(self.tab_crit, bg=c['card_bg'],
                        highlightbackground=c['card_border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=8, pady=8)

        self.tbl_crit = DataTable(card, cols, self.tm)
        self.tbl_crit.pack(fill='both', expand=True, padx=8, pady=8)

        bar = tk.Frame(self.tab_crit, bg=c['bg'])
        bar.pack(fill='x', padx=8, pady=(0, 6))

        ttk.Button(
            bar, text="📦 View Batch Details",
            command=lambda: self._view_batch(self.tbl_crit),
            style='Secondary.TButton'
        ).pack(side='right')

    def _build_warning_tab(self):
        c = self.tm.colors
        cols = [
            {'key': 'batch_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 200},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 120},
            {'key': 'expiry_date', 'label': 'Expiry Date', 'width': 100, 'anchor': 'center'},
            {'key': 'days_until_expiry', 'label': 'Days Remaining', 'width': 110, 'anchor': 'e'},
            {'key': 'current_quantity', 'label': 'Current Units', 'width': 100, 'anchor': 'e'},
            {'key': 'supplier', 'label': 'Supplier', 'width': 140},
        ]
        card = tk.Frame(self.tab_warn, bg=c['card_bg'],
                        highlightbackground=c['card_border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=8, pady=8)

        self.tbl_warn = DataTable(card, cols, self.tm)
        self.tbl_warn.pack(fill='both', expand=True, padx=8, pady=8)

        bar = tk.Frame(self.tab_warn, bg=c['bg'])
        bar.pack(fill='x', padx=8, pady=(0, 6))

        ttk.Button(
            bar, text="📦 View Batch Details",
            command=lambda: self._view_batch(self.tbl_warn),
            style='Secondary.TButton'
        ).pack(side='right')

    def _build_upcoming_tab(self):
        c = self.tm.colors
        cols = [
            {'key': 'batch_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 200},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 120},
            {'key': 'expiry_date', 'label': 'Expiry Date', 'width': 100, 'anchor': 'center'},
            {'key': 'days_until_expiry', 'label': 'Days Remaining', 'width': 110, 'anchor': 'e'},
            {'key': 'current_quantity', 'label': 'Current Units', 'width': 100, 'anchor': 'e'},
            {'key': 'supplier', 'label': 'Supplier', 'width': 140},
        ]
        card = tk.Frame(self.tab_upcom, bg=c['card_bg'],
                        highlightbackground=c['card_border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=8, pady=8)

        self.tbl_upcom = DataTable(card, cols, self.tm)
        self.tbl_upcom.pack(fill='both', expand=True, padx=8, pady=8)

        bar = tk.Frame(self.tab_upcom, bg=c['bg'])
        bar.pack(fill='x', padx=8, pady=(0, 6))

        ttk.Button(
            bar, text="📦 View Batch Details",
            command=lambda: self._view_batch(self.tbl_upcom),
            style='Secondary.TButton'
        ).pack(side='right')

    def _build_low_stock_tab(self):
        c = self.tm.colors
        cols = [
            {'key': 'medicine_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'name', 'label': 'Medicine Name', 'width': 200},
            {'key': 'category', 'label': 'Category', 'width': 120},
            {'key': 'unit_type', 'label': 'Form', 'width': 90},
            {'key': 'total_stock', 'label': 'Current Stock', 'width': 100, 'anchor': 'e'},
            {'key': 'min_stock_threshold', 'label': 'Alert Threshold', 'width': 110, 'anchor': 'e'},
            {'key': 'deficit', 'label': 'Deficit', 'width': 80, 'anchor': 'e'},
        ]
        card = tk.Frame(self.tab_low, bg=c['card_bg'],
                        highlightbackground=c['card_border'], highlightthickness=1)
        card.pack(fill='both', expand=True, padx=8, pady=8)

        self.tbl_low = DataTable(card, cols, self.tm)
        self.tbl_low.pack(fill='both', expand=True, padx=8, pady=8)

        bar = tk.Frame(self.tab_low, bg=c['bg'])
        bar.pack(fill='x', padx=8, pady=(0, 6))

        ttk.Button(
            bar, text="➕ Restock (Add Batch)",
            command=self._restock_low_item,
            style='Primary.TButton'
        ).pack(side='right')

    def select_tab(self, index: int):
        """Programmatically switch active tab (0: Expired, 1: Critical, etc.)."""
        try:
            self.notebook.select(index)
        except Exception:
            pass

    def refresh(self):
        """Fetch alert data across all expiry tiers and low-stock medicines."""
        # 1. Expired
        expired = self.app.expiry_service.get_expired_batches()
        data_exp = [{
            'batch_id': b['batch_id'],
            'medicine_name': b.get('medicine_name', 'Unknown'),
            'batch_number': b['batch_number'],
            'expiry_date': b['expiry_date'],
            'days_until_expiry': f"{abs(b['days_until_expiry'])} days ago",
            'current_quantity': f"{b['current_quantity']:,}",
            'supplier': b.get('supplier', '') or '-'
        } for b in expired]
        self.tbl_expired.populate(data_exp, empty_msg="🎉 Great news! No medicines are currently expired.")
        self.notebook.tab(0, text=f"🚨 Expired ({len(data_exp)})")

        # 2. Critical
        crit = self.app.expiry_service.get_critical_batches()
        data_crit = [{
            'batch_id': b['batch_id'],
            'medicine_name': b.get('medicine_name', 'Unknown'),
            'batch_number': b['batch_number'],
            'expiry_date': b['expiry_date'],
            'days_until_expiry': f"{b['days_until_expiry']} day(s)",
            'current_quantity': f"{b['current_quantity']:,}",
            'supplier': b.get('supplier', '') or '-'
        } for b in crit]
        self.tbl_crit.populate(data_crit, empty_msg="✓ All good! No batches expiring within the next 7 days.")
        self.notebook.tab(1, text=f"⚠️ Critical ≤7d ({len(data_crit)})")

        # 3. Warning
        warn = self.app.expiry_service.get_warning_batches()
        data_warn = [{
            'batch_id': b['batch_id'],
            'medicine_name': b.get('medicine_name', 'Unknown'),
            'batch_number': b['batch_number'],
            'expiry_date': b['expiry_date'],
            'days_until_expiry': f"{b['days_until_expiry']} days",
            'current_quantity': f"{b['current_quantity']:,}",
            'supplier': b.get('supplier', '') or '-'
        } for b in warn]
        self.tbl_warn.populate(data_warn, empty_msg="✓ Clear! No batches expiring between 8 and 15 days.")
        self.notebook.tab(2, text=f"⏳ Warning 8-15d ({len(data_warn)})")

        # 4. Upcoming
        upcom = self.app.expiry_service.get_upcoming_batches()
        data_upcom = [{
            'batch_id': b['batch_id'],
            'medicine_name': b.get('medicine_name', 'Unknown'),
            'batch_number': b['batch_number'],
            'expiry_date': b['expiry_date'],
            'days_until_expiry': f"{b['days_until_expiry']} days",
            'current_quantity': f"{b['current_quantity']:,}",
            'supplier': b.get('supplier', '') or '-'
        } for b in upcom]
        self.tbl_upcom.populate(data_upcom, empty_msg="✓ Clear! No batches expiring between 16 and 30 days.")
        self.notebook.tab(3, text=f"📅 Upcoming 16-30d ({len(data_upcom)})")

        # 5. Low stock
        all_meds = self.app.medicine_service.get_all_medicines_with_stock()
        low_meds = [m for m in all_meds if m.get('total_stock', 0) < m.get('min_stock_threshold', 10)]
        data_low = [{
            'medicine_id': m['medicine_id'],
            'name': m['name'],
            'category': m.get('category', 'General'),
            'unit_type': m.get('unit_type', 'Tablet'),
            'total_stock': f"{m.get('total_stock', 0):,}",
            'min_stock_threshold': f"{m.get('min_stock_threshold', 10):,}",
            'deficit': f"-{m.get('min_stock_threshold', 10) - m.get('total_stock', 0):,}"
        } for m in low_meds]
        self.tbl_low.populate(data_low, empty_msg="✓ Healthy inventory! All medicines are above their alert threshold.")
        self.notebook.tab(4, text=f"📉 Low Stock ({len(data_low)})")

    def _dispose_expired_batch(self):
        selected = self.tbl_expired.get_selected()
        if not selected:
            messagebox.showwarning("Select Batch", "Please select an expired batch to dispose.", parent=self)
            return

        batch_id = int(selected['batch_id'])
        batch = self.app.inventory_service.get_batch(batch_id)
        if not batch or batch['current_quantity'] <= 0:
            messagebox.showinfo("Already Cleared", "This batch already has zero remaining stock.", parent=self)
            return

        qty = batch['current_quantity']
        if ConfirmDialog.show(
            self, "Confirm Disposal",
            f"Dispose all {qty} expired units of '{selected['medicine_name']}' (Batch: {selected['batch_number']})?\n\n"
            f"This will record a REMOVED stock transaction with reason 'Disposed — Expired Product'."
        ):
            self.app.inventory_service.reduce_stock(
                batch_id, qty, reason="Disposed — Expired Product"
            )
            messagebox.showinfo("Disposed", f"Successfully disposed {qty} expired units.", parent=self)
            self.refresh()

    def _view_batch(self, table: DataTable):
        selected = table.get_selected()
        if not selected:
            messagebox.showwarning("Select Batch", "Please select a batch from the table.", parent=self)
            return
        batch_id = int(selected['batch_id'])
        batch = self.app.inventory_service.get_batch(batch_id)
        if batch:
            self.app.show_view('batches', filter_medicine_id=batch['medicine_id'])

    def _restock_low_item(self):
        selected = self.tbl_low.get_selected()
        if not selected:
            messagebox.showwarning("Select Medicine", "Please select a low-stock medicine to restock.", parent=self)
            return
        med_id = int(selected['medicine_id'])
        self.app.show_view('batches', filter_medicine_id=med_id)

    def apply_theme(self):
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.refresh()

