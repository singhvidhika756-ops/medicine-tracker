"""
stock.py — Stock Management and Audit Trail View for MediVault.

Provides FEFO (First-Expired, First-Out) stock dispensing, manual stock adjustments,
and an immutable transaction history audit log.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from ui.widgets import DataTable, FormField
from utils.validators import validate_quantity

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class FEFODispenseDialog(tk.Toplevel):
    """
    Modal dialog allowing users to dispense stock using FEFO (First-Expired, First-Out).
    Automatically picks the earliest expiring non-expired batches first.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp', on_success=None):
        super().__init__(parent)
        self.app = app
        self.tm = app.theme_manager
        self.on_success = on_success

        c = self.tm.colors
        self.configure(bg=c['card_bg'])
        self.title("FEFO Stock Dispense — MediVault")
        self.geometry("540x630")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.medicines_list = self.app.medicine_service.get_all_medicines_with_stock()
        self.med_lookup = {
            f"{m['name']} (Available: {m.get('total_stock', 0)})": m['medicine_id']
            for m in self.medicines_list
        }

        self._build_ui()
        self.bind('<Escape>', lambda e: self.destroy())

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 540) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 630) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._update_preview()

    def _build_ui(self):
        c = self.tm.colors

        # Header
        header = tk.Frame(self, bg=c['card_bg'])
        header.pack(fill='x', padx=24, pady=(18, 12))

        tk.Label(
            header, text="⚡ First-Expired, First-Out (FEFO) Dispense",
            font=('Segoe UI', 13, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            header, text="Automatically deducts inventory from the nearest-expiring batches first.",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', pady=(2, 0))

        # Body
        body = tk.Frame(self, bg=c['card_bg'])
        body.pack(fill='both', expand=True, padx=24)

        med_options = list(self.med_lookup.keys())
        self.f_med = FormField(body, "Select Medicine", field_type='combo',
                               options=med_options, required=True, theme_manager=self.tm)
        self.f_med.pack(fill='x', pady=5)
        if med_options:
            self.f_med.set_value(med_options[0])
        self.f_med._var.trace_add("write", lambda *args: self._update_preview())

        self.f_qty = FormField(body, "Quantity to Dispense", field_type='spinbox',
                               required=True, theme_manager=self.tm)
        self.f_qty.pack(fill='x', pady=5)
        self.f_qty.set_value('10')
        self.f_qty._var.trace_add("write", lambda *args: self._update_preview())

        self.f_reason = FormField(body, "Reason / Customer Ref", field_type='entry',
                                  required=True, theme_manager=self.tm)
        self.f_reason.pack(fill='x', pady=5)
        self.f_reason.set_value('FEFO Sale / Dispensed')

        # Live FEFO Allocation Preview Card
        preview_card = tk.Frame(body, bg=c['bg'], highlightbackground=c['card_border'], highlightthickness=1)
        preview_card.pack(fill='x', pady=8)

        tk.Label(
            preview_card, text="💡 Live FEFO Pick Preview:",
            font=('Segoe UI', 9, 'bold'),
            bg=c['bg'], fg=c['primary']
        ).pack(anchor='w', padx=10, pady=(8, 2))

        self.lbl_preview = tk.Label(
            preview_card, text="Calculating...",
            font=('Segoe UI', 9),
            bg=c['bg'], fg=c['text'],
            justify='left', anchor='w'
        )
        self.lbl_preview.pack(fill='x', padx=10, pady=(0, 8))

        # Footer
        footer = tk.Frame(self, bg=c['card_bg'])
        footer.pack(fill='x', padx=24, pady=16)

        ttk.Button(
            footer, text="Cancel (Esc)", command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=(8, 0))

        ttk.Button(
            footer, text="⚡ Dispense Stock", command=self._on_dispense,
            style='Primary.TButton'
        ).pack(side='right')

    def _update_preview(self):
        from datetime import date
        med_str = self.f_med.get_value()
        qty_str = self.f_qty.get_value()

        if med_str not in self.med_lookup:
            self.lbl_preview.configure(text="Please select a medicine above.")
            return

        med_id = self.med_lookup[med_str]
        try:
            qty = int(qty_str)
        except (ValueError, TypeError):
            self.lbl_preview.configure(text="Enter a valid whole number for quantity.")
            return

        if qty <= 0:
            self.lbl_preview.configure(text="Quantity must be greater than zero.")
            return

        today_str = date.today().strftime("%Y-%m-%d")
        batches = self.app.db.fetchall("""
            SELECT batch_id, batch_number, expiry_date, current_quantity
            FROM   batches
            WHERE  medicine_id = ?
              AND  expiry_date >= ?
              AND  current_quantity > 0
            ORDER BY expiry_date ASC
        """, (med_id, today_str))

        total_avail = sum(b['current_quantity'] for b in batches)
        if total_avail == 0:
            self.lbl_preview.configure(text="❌ No non-expired stock available for this medicine.")
            return

        if qty > total_avail:
            self.lbl_preview.configure(
                text=f"⚠️ Insufficient stock: only {total_avail} non-expired units available (need {qty})."
            )
            return

        # Greedy simulation
        plan = []
        rem = qty
        for b in batches:
            if rem <= 0:
                break
            take = min(rem, b['current_quantity'])
            plan.append(f"  ✓ {take} unit(s) from Batch {b['batch_number']} (Exp: {b['expiry_date']})")
            rem -= take

        self.lbl_preview.configure(text="\n".join(plan))

    def _on_dispense(self):
        med_str = self.f_med.get_value()
        qty_str = self.f_qty.get_value()
        reason = self.f_reason.get_value().strip()

        if med_str not in self.med_lookup:
            self.f_med.set_error("Please select a medicine.")
            return
        self.f_med.clear_error()
        med_id = self.med_lookup[med_str]

        v_qty, err_qty = validate_quantity(qty_str)
        if not v_qty:
            self.f_qty.set_error(err_qty)
            return
        qty = int(qty_str)
        if qty <= 0:
            self.f_qty.set_error("Quantity must be greater than zero.")
            return
        self.f_qty.clear_error()

        if not reason:
            self.f_reason.set_error("Please enter a reason.")
            return

        try:
            allocations = self.app.inventory_service.reduce_stock_fefo(med_id, qty, reason=reason)
            summary_lines = [f"Batch #{b_id}: {taken} unit(s)" for b_id, taken in allocations]
            msg = f"Successfully dispensed {qty} unit(s) using FEFO:\n\n" + "\n".join(summary_lines)
            messagebox.showinfo("FEFO Dispense Successful", msg, parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Dispense Failed", str(e), parent=self)


class StockAdjustmentManualDialog(tk.Toplevel):
    """
    Modal dialog allowing manual stock correction to an exact value.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp', on_success=None):
        super().__init__(parent)
        self.app = app
        self.tm = app.theme_manager
        self.on_success = on_success

        c = self.tm.colors
        self.configure(bg=c['card_bg'])
        self.title("Manual Stock Count Correction — MediVault")
        self.geometry("480x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Cache active batches for selector
        self.batches = self.app.inventory_service.get_batches()
        self.batch_lookup = {
            f"{b.get('medicine_name', 'Unknown')} | Batch: {b['batch_number']} (Current: {b['current_quantity']})": b['batch_id']
            for b in self.batches
        }

        self._build_ui()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 480) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 420) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        c = self.tm.colors

        header = tk.Frame(self, bg=c['card_bg'])
        header.pack(fill='x', padx=24, pady=(18, 12))

        tk.Label(
            header, text="✏️ Manual Stock Count Correction",
            font=('Segoe UI', 13, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            header, text="Set a batch stock to an exact physical count. Difference is audited.",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', pady=(2, 0))

        body = tk.Frame(self, bg=c['card_bg'])
        body.pack(fill='both', expand=True, padx=24)

        batch_options = list(self.batch_lookup.keys())
        self.f_batch = FormField(body, "Select Batch", field_type='combo',
                                 options=batch_options, required=True, theme_manager=self.tm)
        self.f_batch.pack(fill='x', pady=6)
        if batch_options:
            self.f_batch.set_value(batch_options[0])

        self.f_qty = FormField(body, "Actual Counted Stock", field_type='spinbox',
                               required=True, theme_manager=self.tm)
        self.f_qty.pack(fill='x', pady=6)
        self.f_qty.set_value('0')

        self.f_reason = FormField(body, "Reason for correction", field_type='entry',
                                  required=True, theme_manager=self.tm)
        self.f_reason.pack(fill='x', pady=6)
        self.f_reason.set_value('Physical audit count')

        footer = tk.Frame(self, bg=c['card_bg'])
        footer.pack(fill='x', padx=24, pady=18)

        ttk.Button(
            footer, text="Cancel", command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=(8, 0))

        ttk.Button(
            footer, text="Apply Correction", command=self._on_correct,
            style='Primary.TButton'
        ).pack(side='right')

    def _on_correct(self):
        batch_str = self.f_batch.get_value()
        qty_str = self.f_qty.get_value()
        reason = self.f_reason.get_value().strip()

        if batch_str not in self.batch_lookup:
            self.f_batch.set_error("Please select a batch.")
            return
        self.f_batch.clear_error()
        batch_id = self.batch_lookup[batch_str]

        v_qty, err_qty = validate_quantity(qty_str)
        if not v_qty:
            self.f_qty.set_error(err_qty)
            return
        qty = int(qty_str)
        self.f_qty.clear_error()

        if not reason:
            self.f_reason.set_error("Please enter a reason.")
            return

        try:
            self.app.inventory_service.correct_stock(batch_id, qty, reason=reason)
            messagebox.showinfo("Success", f"Batch stock corrected to {qty} units.", parent=self)
            if self.on_success:
                self.on_success()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Correction Failed", str(e), parent=self)


class StockView(tk.Frame):
    """
    Stock Management View listing all historical movements and providing stock controls.
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
            title_frame, text="📋 Stock Operations & Audit Log",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Complete immutable history of additions, removals, sales, and corrections",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        btn_frame = tk.Frame(header, bg=c['bg'])
        btn_frame.pack(side='right')

        ttk.Button(
            btn_frame, text="⚡ FEFO Dispense",
            command=self._open_fefo_dialog,
            style='Primary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="✏️ Correct Stock",
            command=self._open_correct_dialog,
            style='Secondary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="🔄 Refresh",
            command=self.refresh,
            style='Secondary.TButton'
        ).pack(side='right')

        # Filter Toolbar
        toolbar = tk.Frame(self, bg=c['card_bg'],
                           highlightbackground=c['card_border'], highlightthickness=1)
        toolbar.pack(fill='x', padx=24, pady=10)

        tool_inner = tk.Frame(toolbar, bg=c['card_bg'])
        tool_inner.pack(fill='x', padx=14, pady=10)

        tk.Label(
            tool_inner, text="Transaction Type:",
            font=('Segoe UI', 10),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left', padx=(0, 6))

        self.type_filter_var = tk.StringVar(value="All Types")
        type_options = ["All Types", "INITIAL", "ADDED", "REMOVED", "ADJUSTED"]
        self.type_combo = ttk.Combobox(
            tool_inner, textvariable=self.type_filter_var,
            values=type_options, state='readonly', width=14, font=('Segoe UI', 10)
        )
        self.type_combo.pack(side='left', padx=(0, 14))
        self.type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        tk.Label(
            tool_inner, text="Limit Rows:",
            font=('Segoe UI', 10),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left', padx=(0, 6))

        self.limit_var = tk.StringVar(value="100")
        limit_combo = ttk.Combobox(
            tool_inner, textvariable=self.limit_var,
            values=["25", "50", "100", "250", "500"], state='readonly', width=8, font=('Segoe UI', 10)
        )
        limit_combo.pack(side='left', padx=(0, 14))
        limit_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        ttk.Button(
            tool_inner, text="Reset Filters",
            command=self._reset_filters,
            style='Secondary.TButton'
        ).pack(side='left')

        # Audit Table Card
        table_card = tk.Frame(self, bg=c['card_bg'],
                              highlightbackground=c['card_border'], highlightthickness=1)
        table_card.pack(fill='both', expand=True, padx=24, pady=(0, 10))

        columns = [
            {'key': 'transaction_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'transaction_date', 'label': 'Timestamp', 'width': 130},
            {'key': 'medicine_name', 'label': 'Medicine', 'width': 170},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 110},
            {'key': 'transaction_type', 'label': 'Type', 'width': 85, 'anchor': 'center'},
            {'key': 'quantity_changed', 'label': 'Delta', 'width': 70, 'anchor': 'e'},
            {'key': 'previous_quantity', 'label': 'Before', 'width': 70, 'anchor': 'e'},
            {'key': 'new_quantity', 'label': 'After', 'width': 70, 'anchor': 'e'},
            {'key': 'reason', 'label': 'Reason', 'width': 180},
        ]

        self.table = DataTable(table_card, columns, self.tm)
        self.table.pack(fill='both', expand=True, padx=12, pady=12)

        # Bottom Status Bar
        bottom_bar = tk.Frame(self, bg=c['bg'])
        bottom_bar.pack(fill='x', padx=24, pady=(0, 16))

        self.lbl_count = tk.Label(
            bottom_bar, text="0 transactions recorded",
            font=('Segoe UI', 9),
            bg=c['bg'], fg=c['text_secondary']
        )
        self.lbl_count.pack(side='left')

    def refresh(self):
        """Fetch transactions from database and populate table."""
        try:
            limit = int(self.limit_var.get())
        except ValueError:
            limit = 100

        type_filter = self.type_filter_var.get()
        if type_filter == "All Types":
            txs = self.app.inventory_service.get_transactions(limit=limit)
        else:
            txs = self.app.inventory_service.get_transactions_by_type(type_filter, limit=limit)

        display_data = []
        for t in txs:
            t_type = t['transaction_type']
            qty = t['quantity_changed']
            prefix = "+" if t_type in ('ADDED', 'INITIAL') else "-"
            display_data.append({
                'transaction_id': t['transaction_id'],
                'transaction_date': str(t['transaction_date'])[:19],
                'medicine_name': t.get('medicine_name', 'Unknown'),
                'batch_number': t.get('batch_number', '-'),
                'transaction_type': t_type,
                'quantity_changed': f"{prefix}{abs(qty)}",
                'previous_quantity': f"{t['previous_quantity']:,}",
                'new_quantity': f"{t['new_quantity']:,}",
                'reason': t.get('reason', '')
            })

        self.table.populate(display_data, tag_key='transaction_type')
        self.lbl_count.configure(text=f"Showing {len(display_data)} transaction entries")

    def _reset_filters(self):
        self.type_filter_var.set("All Types")
        self.limit_var.set("100")
        self.refresh()

    def _open_fefo_dialog(self):
        FEFODispenseDialog(self, self.app, on_success=self.refresh)

    def _open_correct_dialog(self):
        StockAdjustmentManualDialog(self, self.app, on_success=self.refresh)

    def apply_theme(self):
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.refresh()

