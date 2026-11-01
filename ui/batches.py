"""
batches.py — Batch Management View for MediVault.

Allows users to create, view, edit, and delete medicine batches, track individual
batch expiry dates, manage purchase costs, and perform quick stock in/out operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import TYPE_CHECKING, Optional, Dict, Any, List

from ui.widgets import DataTable, FormField, ConfirmDialog
from utils.validators import (
    validate_batch_number, validate_quantity, validate_price,
    validate_date, validate_date_range
)

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class BatchDialog(tk.Toplevel):
    """
    Modal dialog for adding or editing a medicine batch.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp',
                 batch_data: Optional[Dict[str, Any]] = None,
                 default_medicine_id: Optional[int] = None,
                 on_success=None):
        super().__init__(parent)
        self.app = app
        self.tm = app.theme_manager
        self.batch_data = batch_data
        self.default_medicine_id = default_medicine_id
        self.on_success = on_success
        self.is_edit = batch_data is not None

        c = self.tm.colors
        self.configure(bg=c['card_bg'])
        title = "Edit Batch" if self.is_edit else "Add New Batch"
        self.title(f"{title} — MediVault")
        self.geometry("540x680")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Cache medicines for the dropdown: "Paracetamol (ID: 1)"
        self.medicines_list = self.app.medicine_service.get_all_medicines()
        self.med_lookup: Dict[str, int] = {
            f"{m['name']} (ID: {m['medicine_id']})": m['medicine_id']
            for m in self.medicines_list
        }

        self._build_ui()
        if self.is_edit:
            self._populate_fields()
        elif self.default_medicine_id:
            for display_str, mid in self.med_lookup.items():
                if mid == self.default_medicine_id:
                    self.f_med.set_value(display_str)
                    break

        self.bind('<Escape>', lambda e: self.destroy())

        # Center on parent window
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 540) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 680) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        c = self.tm.colors

        # Header
        header = tk.Frame(self, bg=c['card_bg'])
        header.pack(fill='x', padx=24, pady=(18, 12))

        title_text = "✏️ Edit Batch Details" if self.is_edit else "📦 Register New Batch"
        tk.Label(
            header, text=title_text,
            font=('Segoe UI', 14, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            header, text="Track batch numbers, manufacturing & expiry dates, and unit costs.",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', pady=(2, 0))

        # Body
        body = tk.Frame(self, bg=c['card_bg'])
        body.pack(fill='both', expand=True, padx=24)

        # Medicine Selection
        med_options = list(self.med_lookup.keys())
        self.f_med = FormField(body, "Select Medicine", field_type='combo',
                               options=med_options, required=True, theme_manager=self.tm)
        self.f_med.pack(fill='x', pady=3)
        if med_options:
            self.f_med.set_value(med_options[0])

        if self.is_edit:
            # Cannot change medicine_id during edit to preserve relational integrity
            self.f_med._widget.configure(state='disabled')

        # Batch Number & Supplier
        row_bno_sup = tk.Frame(body, bg=c['card_bg'])
        row_bno_sup.pack(fill='x', pady=3)

        self.f_batch_no = FormField(row_bno_sup, "Batch Number", field_type='entry',
                                    required=True, theme_manager=self.tm)
        self.f_batch_no.pack(side='left', fill='x', expand=True, padx=(0, 6))

        self.f_supplier = FormField(row_bno_sup, "Supplier / Distributor", field_type='entry',
                                    theme_manager=self.tm)
        self.f_supplier.pack(side='right', fill='x', expand=True, padx=(6, 0))

        # Manufacturing Date & Expiry Date
        row_dates = tk.Frame(body, bg=c['card_bg'])
        row_dates.pack(fill='x', pady=3)

        today_str = date.today().strftime("%Y-%m-%d")
        self.f_mfg = FormField(row_dates, "Manufacturing Date", field_type='date',
                               required=True, theme_manager=self.tm)
        self.f_mfg.pack(side='left', fill='x', expand=True, padx=(0, 6))
        self.f_mfg.set_value(today_str)

        self.f_exp = FormField(row_dates, "Expiry Date", field_type='date',
                               required=True, theme_manager=self.tm)
        self.f_exp.pack(side='right', fill='x', expand=True, padx=(6, 0))

        # Purchase Date & Initial Quantity
        row_pur_qty = tk.Frame(body, bg=c['card_bg'])
        row_pur_qty.pack(fill='x', pady=3)

        self.f_pur_date = FormField(row_pur_qty, "Purchase Date", field_type='date',
                                    required=True, theme_manager=self.tm)
        self.f_pur_date.pack(side='left', fill='x', expand=True, padx=(0, 6))
        self.f_pur_date.set_value(today_str)

        self.f_qty = FormField(row_pur_qty, "Initial Quantity Received", field_type='spinbox',
                               required=True, theme_manager=self.tm)
        self.f_qty.pack(side='right', fill='x', expand=True, padx=(6, 0))
        self.f_qty.set_value('100')
        if self.is_edit:
            self.f_qty._widget.configure(state='disabled')

        # Purchase Price & Selling Price
        row_prices = tk.Frame(body, bg=c['card_bg'])
        row_prices.pack(fill='x', pady=3)

        self.f_purchase_price = FormField(row_prices, "Purchase Price / Unit (₹)", field_type='entry',
                                          required=True, theme_manager=self.tm)
        self.f_purchase_price.pack(side='left', fill='x', expand=True, padx=(0, 6))
        self.f_purchase_price.set_value('0.00')

        self.f_selling_price = FormField(row_prices, "Selling Price / Unit (₹)", field_type='entry',
                                         theme_manager=self.tm)
        self.f_selling_price.pack(side='right', fill='x', expand=True, padx=(6, 0))
        self.f_selling_price.set_value('0.00')

        # Notes
        self.f_notes = FormField(body, "Notes / Storage Instructions", field_type='entry', theme_manager=self.tm)
        self.f_notes.pack(fill='x', pady=3)

        # Footer
        footer = tk.Frame(self, bg=c['card_bg'])
        footer.pack(fill='x', padx=24, pady=18)

        ttk.Button(
            footer, text="Cancel", command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=(8, 0))

        save_btn_text = "Save Changes" if self.is_edit else "Register Batch"
        ttk.Button(
            footer, text=save_btn_text, command=self._on_save,
            style='Primary.TButton'
        ).pack(side='right')

    def _populate_fields(self):
        b = self.batch_data
        if not b:
            return
        # Find medicine display label
        med_id = b['medicine_id']
        for display_str, mid in self.med_lookup.items():
            if mid == med_id:
                self.f_med.set_value(display_str)
                break

        self.f_batch_no.set_value(b.get('batch_number', ''))
        self.f_supplier.set_value(b.get('supplier', ''))
        self.f_mfg.set_value(b.get('manufacturing_date', ''))
        self.f_exp.set_value(b.get('expiry_date', ''))
        self.f_pur_date.set_value(b.get('purchase_date', ''))
        self.f_qty.set_value(str(b.get('current_quantity', 0)))
        self.f_purchase_price.set_value(str(b.get('purchase_price', 0.0)))
        self.f_selling_price.set_value(str(b.get('selling_price', 0.0)))
        self.f_notes.set_value(b.get('notes', ''))

    def _on_save(self):
        med_str = self.f_med.get_value()
        batch_no = self.f_batch_no.get_value()
        supplier = self.f_supplier.get_value()
        mfg = self.f_mfg.get_value()
        exp = self.f_exp.get_value()
        pur = self.f_pur_date.get_value()
        qty_str = self.f_qty.get_value()
        p_price_str = self.f_purchase_price.get_value()
        s_price_str = self.f_selling_price.get_value()
        notes = self.f_notes.get_value()

        if med_str not in self.med_lookup:
            self.f_med.set_error("Please select a valid medicine from the list.")
            return
        self.f_med.clear_error()
        medicine_id = self.med_lookup[med_str]

        # Validations
        v_bno, err_bno = validate_batch_number(batch_no)
        if not v_bno:
            self.f_batch_no.set_error(err_bno)
            return
        self.f_batch_no.clear_error()

        v_mfg, err_mfg = validate_date(mfg)
        if not v_mfg:
            self.f_mfg.set_error(err_mfg)
            return
        self.f_mfg.clear_error()

        v_exp, err_exp = validate_date(exp)
        if not v_exp:
            self.f_exp.set_error(err_exp)
            return
        self.f_exp.clear_error()

        v_range, err_range = validate_date_range(mfg, exp)
        if not v_range:
            self.f_exp.set_error(err_range)
            return
        self.f_exp.clear_error()

        v_pur, err_pur = validate_date(pur)
        if not v_pur:
            self.f_pur_date.set_error(err_pur)
            return
        self.f_pur_date.clear_error()

        v_qty, err_qty = validate_quantity(qty_str)
        if not v_qty:
            self.f_qty.set_error(err_qty)
            return
        qty = int(qty_str)
        if not self.is_edit and qty <= 0:
            self.f_qty.set_error("Initial quantity must be greater than zero.")
            return
        self.f_qty.clear_error()

        v_pprice, err_pprice = validate_price(p_price_str)
        if not v_pprice:
            self.f_purchase_price.set_error(err_pprice)
            return
        self.f_purchase_price.clear_error()
        purchase_price = float(p_price_str)

        v_sprice, err_sprice = validate_price(s_price_str)
        if not v_sprice:
            self.f_selling_price.set_error(err_sprice)
            return
        self.f_selling_price.clear_error()
        selling_price = float(s_price_str)

        try:
            if self.is_edit:
                batch_id = self.batch_data['batch_id']
                self.app.inventory_service.update_batch(
                    batch_id=batch_id,
                    batch_number=batch_no,
                    manufacturing_date=mfg,
                    expiry_date=exp,
                    purchase_date=pur,
                    purchase_price=purchase_price,
                    selling_price=selling_price,
                    supplier=supplier,
                    notes=notes
                )
                messagebox.showinfo("Success", f"Batch '{batch_no}' updated successfully!", parent=self)
            else:
                self.app.inventory_service.add_batch(
                    medicine_id=medicine_id,
                    batch_number=batch_no,
                    mfg_date=mfg,
                    exp_date=exp,
                    purchase_date=pur,
                    qty_received=qty,
                    purchase_price=purchase_price,
                    selling_price=selling_price,
                    supplier=supplier,
                    notes=notes
                )
                messagebox.showinfo("Success", f"Batch '{batch_no}' registered successfully!", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error Saving Batch", str(e), parent=self)


class StockAdjustmentDialog(tk.Toplevel):
    """
    Quick dialog to add or remove stock units from a specific batch.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp', batch: Dict[str, Any],
                 action_type: str = 'ADD', on_success=None):
        super().__init__(parent)
        self.app = app
        self.tm = app.theme_manager
        self.batch = batch
        self.action_type = action_type  # 'ADD' or 'REMOVE'
        self.on_success = on_success

        c = self.tm.colors
        self.configure(bg=c['card_bg'])
        title_word = "Add Stock To" if action_type == 'ADD' else "Remove Stock From"
        self.title(f"{title_word} Batch — MediVault")
        self.geometry("440x360")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self.bind('<Escape>', lambda e: self.destroy())

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 440) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 360) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        c = self.tm.colors
        action_word = "Add Stock" if self.action_type == 'ADD' else "Remove Stock"

        header = tk.Frame(self, bg=c['card_bg'])
        header.pack(fill='x', padx=20, pady=(16, 10))

        tk.Label(
            header, text=f"{'➕' if self.action_type == 'ADD' else '➖'} {action_word}",
            font=('Segoe UI', 13, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w')

        b_info = f"Medicine: {self.batch.get('medicine_name', 'Unknown')} | " \
                 f"Batch: {self.batch.get('batch_number', '-')} | " \
                 f"Current: {self.batch.get('current_quantity', 0)} units"
        tk.Label(
            header, text=b_info,
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', pady=(3, 0))

        body = tk.Frame(self, bg=c['card_bg'])
        body.pack(fill='both', expand=True, padx=20)

        self.f_qty = FormField(body, f"Units to {action_word.lower()}", field_type='spinbox',
                               required=True, theme_manager=self.tm)
        self.f_qty.pack(fill='x', pady=6)
        self.f_qty.set_value('10')

        default_reason = "Restocked from vendor" if self.action_type == 'ADD' else "Dispensed / Damaged"
        self.f_reason = FormField(body, "Reason for stock movement", field_type='entry',
                                  required=True, theme_manager=self.tm)
        self.f_reason.pack(fill='x', pady=6)
        self.f_reason.set_value(default_reason)

        footer = tk.Frame(self, bg=c['card_bg'])
        footer.pack(fill='x', padx=20, pady=16)

        ttk.Button(
            footer, text="Cancel", command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=(8, 0))

        btn_style = 'Success.TButton' if self.action_type == 'ADD' else 'Danger.TButton'
        ttk.Button(
            footer, text=f"Confirm {action_word}", command=self._on_confirm,
            style=btn_style
        ).pack(side='right')

    def _on_confirm(self):
        qty_str = self.f_qty.get_value()
        reason = self.f_reason.get_value().strip()

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
            self.f_reason.set_error("Please specify a reason.")
            return

        try:
            batch_id = self.batch['batch_id']
            if self.action_type == 'ADD':
                self.app.inventory_service.add_stock(batch_id, qty, reason=reason)
                messagebox.showinfo("Success", f"Added {qty} units to batch.", parent=self)
            else:
                self.app.inventory_service.reduce_stock(batch_id, qty, reason=reason)
                messagebox.showinfo("Success", f"Removed {qty} units from batch.", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)


class BatchesView(tk.Frame):
    """
    Batch Management View listing individual batches with expiry indicators.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp'):
        self.app = app
        self.tm = app.theme_manager
        self.filter_medicine_id: Optional[int] = None
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
            title_frame, text="📦 Batch Inventory",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        self.lbl_subtitle = tk.Label(
            title_frame, text="Individual batch records, expiry monitoring, and pricing",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        )
        self.lbl_subtitle.pack(anchor='w')

        btn_frame = tk.Frame(header, bg=c['bg'])
        btn_frame.pack(side='right')

        ttk.Button(
            btn_frame, text="➕ Register Batch",
            command=self.open_add_dialog,
            style='Primary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="➕ Stock In",
            command=lambda: self._quick_stock('ADD'),
            style='Success.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="➖ Stock Out",
            command=lambda: self._quick_stock('REMOVE'),
            style='Danger.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="✏️ Edit",
            command=self.open_edit_dialog,
            style='Secondary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="🔄 Refresh",
            command=self.refresh,
            style='Secondary.TButton'
        ).pack(side='right')

        # Filter & Search Toolbar
        toolbar = tk.Frame(self, bg=c['card_bg'],
                           highlightbackground=c['card_border'], highlightthickness=1)
        toolbar.pack(fill='x', padx=24, pady=10)

        tool_inner = tk.Frame(toolbar, bg=c['card_bg'])
        tool_inner.pack(fill='x', padx=14, pady=10)

        tk.Label(
            tool_inner, text="Medicine:",
            font=('Segoe UI', 10, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left', padx=(0, 6))

        self.med_filter_var = tk.StringVar(value="All Medicines")
        self.med_combo = ttk.Combobox(
            tool_inner, textvariable=self.med_filter_var,
            state='readonly', width=28, font=('Segoe UI', 10)
        )
        self.med_combo.pack(side='left', padx=(0, 16))
        self.med_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)

        tk.Label(
            tool_inner, text="Batch # / Supplier:",
            font=('Segoe UI', 10, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left', padx=(0, 6))

        self.batch_search_var = tk.StringVar()
        self.batch_search_entry = ttk.Entry(
            tool_inner, textvariable=self.batch_search_var, width=22, font=('Segoe UI', 10)
        )
        self.batch_search_entry.pack(side='left', padx=(0, 10), ipady=2)
        self.batch_search_var.trace_add("write", lambda *args: self.refresh())

        ttk.Button(
            tool_inner, text="✕ Reset Filters",
            command=self._clear_filter,
            style='Secondary.TButton'
        ).pack(side='left')

        # Main Table Card
        table_card = tk.Frame(self, bg=c['card_bg'],
                              highlightbackground=c['card_border'], highlightthickness=1)
        table_card.pack(fill='both', expand=True, padx=24, pady=(0, 10))

        columns = [
            {'key': 'batch_id', 'label': 'ID', 'width': 45, 'anchor': 'center'},
            {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 180},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 110},
            {'key': 'expiry_date', 'label': 'Expiry Date', 'width': 95, 'anchor': 'center'},
            {'key': 'days_until_expiry', 'label': 'Days Left', 'width': 75, 'anchor': 'e'},
            {'key': 'expiry_status', 'label': 'Status', 'width': 95, 'anchor': 'center'},
            {'key': 'current_quantity', 'label': 'Current Stock', 'width': 85, 'anchor': 'e'},
            {'key': 'purchase_price', 'label': 'Cost / Unit', 'width': 80, 'anchor': 'e'},
            {'key': 'stock_value', 'label': 'Total Value', 'width': 90, 'anchor': 'e'},
            {'key': 'supplier', 'label': 'Supplier', 'width': 120},
        ]

        self.table = DataTable(
            table_card, columns, self.tm,
            on_double_click=lambda e: self.open_edit_dialog()
        )
        self.table.pack(fill='both', expand=True, padx=12, pady=12)

        # Right-Click Context Menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="➕ Quick Stock In", command=lambda: self._quick_stock('ADD'))
        self.context_menu.add_command(label="➖ Quick Stock Out", command=lambda: self._quick_stock('REMOVE'))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✏️ Edit Batch", command=self.open_edit_dialog)
        self.context_menu.add_command(label="🗑️ Delete Batch", command=self._delete_selected)
        self.table.tree.bind("<Button-3>", self._on_right_click)

        # Bottom Action Bar
        bottom_bar = tk.Frame(self, bg=c['bg'])
        bottom_bar.pack(fill='x', padx=24, pady=(0, 16))

        self.lbl_count = tk.Label(
            bottom_bar, text="0 batches found",
            font=('Segoe UI', 9),
            bg=c['bg'], fg=c['text_secondary']
        )
        self.lbl_count.pack(side='left')

        act_frame = tk.Frame(bottom_bar, bg=c['bg'])
        act_frame.pack(side='right')

        ttk.Button(
            act_frame, text="➕ Quick Stock In",
            command=lambda: self._quick_stock('ADD'),
            style='Success.TButton'
        ).pack(side='left', padx=4)

        ttk.Button(
            act_frame, text="➖ Quick Stock Out",
            command=lambda: self._quick_stock('REMOVE'),
            style='Danger.TButton'
        ).pack(side='left', padx=4)

        ttk.Button(
            act_frame, text="✏️ Edit",
            command=self.open_edit_dialog,
            style='Secondary.TButton'
        ).pack(side='left', padx=4)

        ttk.Button(
            act_frame, text="🗑️ Delete",
            command=self._delete_selected,
            style='Danger.TButton'
        ).pack(side='left', padx=4)

    def set_medicine_filter(self, medicine_id: Optional[int]):
        """Filter table to a specific medicine ID."""
        self.filter_medicine_id = medicine_id
        self.refresh()

    def refresh(self):
        """Reload batches and update filter combobox."""
        meds = self.app.medicine_service.get_all_medicines()
        combo_vals = ["All Medicines"] + [f"{m['name']} (ID: {m['medicine_id']})" for m in meds]
        self.med_combo['values'] = combo_vals

        if self.filter_medicine_id:
            found = False
            for val in combo_vals:
                if f"(ID: {self.filter_medicine_id})" in val:
                    self.med_filter_var.set(val)
                    found = True
                    break
            if not found:
                self.med_filter_var.set("All Medicines")
                self.filter_medicine_id = None
        else:
            self.med_filter_var.set("All Medicines")

        batches = self.app.inventory_service.get_batches(medicine_id=self.filter_medicine_id)
        self._display_batches(batches)

    def _display_batches(self, batches):
        display_data = []
        for b in batches:
            days = b.get('days_until_expiry', 0)
            days_str = f"{days}d" if days >= 0 else f"{abs(days)}d ago"
            cost = b.get('purchase_price', 0.0)
            qty = b.get('current_quantity', 0)
            val = cost * qty

            display_data.append({
                'batch_id': b['batch_id'],
                'medicine_name': b.get('medicine_name', 'Unknown'),
                'batch_number': b['batch_number'],
                'expiry_date': b['expiry_date'],
                'days_until_expiry': days_str,
                'expiry_status': b.get('expiry_status', 'NORMAL'),
                'current_quantity': f"{qty:,}",
                'purchase_price': f"₹{cost:,.2f}",
                'stock_value': f"₹{val:,.2f}",
                'supplier': b.get('supplier', '') or '-'
            })

        self.table.populate(
            display_data, tag_key='expiry_status',
            empty_msg="No batches registered for this medicine. Click 'Register Batch' to add stock."
        )
        self.lbl_count.configure(text=f"{len(display_data)} batches registered")

    def _on_right_click(self, event):
        item = self.table.tree.identify_row(event.y)
        if item:
            self.table.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _on_filter_changed(self, event):
        selected_text = self.med_filter_var.get()
        if selected_text == "All Medicines":
            self.filter_medicine_id = None
        else:
            try:
                # Extract ID from string format "... (ID: X)"
                id_part = selected_text.split("(ID: ")[-1].replace(")", "").strip()
                self.filter_medicine_id = int(id_part)
            except Exception:
                self.filter_medicine_id = None
        self.refresh()

    def _clear_filter(self):
        self.filter_medicine_id = None
        self.med_filter_var.set("All Medicines")
        self.refresh()

    def open_add_dialog(self):
        BatchDialog(self, self.app, default_medicine_id=self.filter_medicine_id, on_success=self.refresh)

    def open_edit_dialog(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Select Batch", "Please select a batch from the list to edit.", parent=self)
            return
        batch_id = int(selected['batch_id'])
        batch = self.app.inventory_service.get_batch(batch_id)
        if batch:
            BatchDialog(self, self.app, batch_data=batch, on_success=self.refresh)

    def _quick_stock(self, action_type: str):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Select Batch", "Please select a batch to adjust stock.", parent=self)
            return
        batch_id = int(selected['batch_id'])
        batch = self.app.inventory_service.get_batch(batch_id)
        if batch:
            StockAdjustmentDialog(self, self.app, batch=batch, action_type=action_type, on_success=self.refresh)

    def _delete_selected(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Select Batch", "Please select a batch to delete.", parent=self)
            return

        batch_id = int(selected['batch_id'])
        b_no = selected['batch_number']
        m_name = selected['medicine_name']

        if ConfirmDialog.show(
            self, "Confirm Delete",
            f"Are you sure you want to delete Batch '{b_no}' for '{m_name}'?\n\n"
            f"This will also delete the associated stock records for this batch."
        ):
            self.app.inventory_service.delete_batch(batch_id)
            messagebox.showinfo("Deleted", f"Batch '{b_no}' deleted successfully.", parent=self)
            self.refresh()

    def apply_theme(self):
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.refresh()

