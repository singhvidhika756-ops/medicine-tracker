"""
medicines.py — Medicine Catalog Management View for MediVault.

Provides full CRUD operations for medicine records, category filtering,
name search, and low-stock threshold configurations.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Optional, Dict, Any

from models.medicine import CATEGORIES, UNIT_TYPES
from ui.widgets import DataTable, SearchBar, FormField, ConfirmDialog
from utils.validators import validate_medicine_name, validate_quantity

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class MedicineDialog(tk.Toplevel):
    """
    Modal dialog for adding or editing a medicine record.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp',
                 medicine_data: Optional[Dict[str, Any]] = None,
                 on_success=None):
        super().__init__(parent)
        self.app = app
        self.tm = app.theme_manager
        self.medicine_data = medicine_data
        self.on_success = on_success
        self.is_edit = medicine_data is not None

        c = self.tm.colors
        self.configure(bg=c['card_bg'])
        title = "Edit Medicine" if self.is_edit else "Add New Medicine"
        self.title(f"{title} — MediVault")
        self.geometry("520x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        if self.is_edit:
            self._populate_fields()

        # Keyboard shortcuts
        self.bind('<Escape>', lambda e: self.destroy())

        # Center on parent window
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 520) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 620) // 2
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

    def _build_ui(self):
        c = self.tm.colors

        # Dialog Header
        header = tk.Frame(self, bg=c['card_bg'])
        header.pack(fill='x', padx=24, pady=(20, 15))

        title_text = "✏️ Edit Medicine Details" if self.is_edit else "➕ Add New Medicine"
        tk.Label(
            header, text=title_text,
            font=('Segoe UI', 14, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            header, text="Fill in medicine details. Required fields are marked with *",
            font=('Segoe UI', 9),
            bg=c['card_bg'], fg=c['text_secondary']
        ).pack(anchor='w', pady=(2, 0))

        # Form Container
        body = tk.Frame(self, bg=c['card_bg'])
        body.pack(fill='both', expand=True, padx=24, pady=0)

        self.f_name = FormField(body, "Medicine Name", field_type='entry', required=True, theme_manager=self.tm)
        self.f_name.pack(fill='x', pady=4)

        self.f_generic = FormField(body, "Generic Name (INN)", field_type='entry', theme_manager=self.tm)
        self.f_generic.pack(fill='x', pady=4)

        # Row with Category and Unit Type
        row_cat_unit = tk.Frame(body, bg=c['card_bg'])
        row_cat_unit.pack(fill='x', pady=4)

        self.f_category = FormField(row_cat_unit, "Category", field_type='combo',
                                    options=CATEGORIES, required=True, theme_manager=self.tm)
        self.f_category.pack(side='left', fill='x', expand=True, padx=(0, 6))
        self.f_category.set_value('General')

        self.f_unit = FormField(row_cat_unit, "Unit / Dosage Form", field_type='combo',
                                options=UNIT_TYPES, required=True, theme_manager=self.tm)
        self.f_unit.pack(side='right', fill='x', expand=True, padx=(6, 0))
        self.f_unit.set_value('Tablet')

        # Row with Manufacturer and Min Stock Threshold
        row_mfg_thresh = tk.Frame(body, bg=c['card_bg'])
        row_mfg_thresh.pack(fill='x', pady=4)

        self.f_mfg = FormField(row_mfg_thresh, "Manufacturer", field_type='entry', theme_manager=self.tm)
        self.f_mfg.pack(side='left', fill='x', expand=True, padx=(0, 6))

        self.f_threshold = FormField(row_mfg_thresh, "Min Stock Alert Threshold", field_type='spinbox',
                                     required=True, theme_manager=self.tm)
        self.f_threshold.pack(side='right', fill='x', expand=True, padx=(6, 0))
        self.f_threshold.set_value('10')

        self.f_desc = FormField(body, "Description / Notes", field_type='text', theme_manager=self.tm)
        self.f_desc.pack(fill='x', pady=4)

        # Footer Actions
        footer = tk.Frame(self, bg=c['card_bg'])
        footer.pack(fill='x', padx=24, pady=20)

        ttk.Button(
            footer, text="Cancel", command=self.destroy,
            style='Secondary.TButton'
        ).pack(side='right', padx=(8, 0))

        save_btn_text = "Save Changes" if self.is_edit else "Save Medicine"
        ttk.Button(
            footer, text=save_btn_text, command=self._on_save,
            style='Primary.TButton'
        ).pack(side='right')

    def _populate_fields(self):
        if not self.medicine_data:
            return
        self.f_name.set_value(self.medicine_data.get('name', ''))
        self.f_generic.set_value(self.medicine_data.get('generic_name', ''))
        self.f_category.set_value(self.medicine_data.get('category', 'General'))
        self.f_unit.set_value(self.medicine_data.get('unit_type', 'Tablet'))
        self.f_mfg.set_value(self.medicine_data.get('manufacturer', ''))
        self.f_threshold.set_value(str(self.medicine_data.get('min_stock_threshold', 10)))
        self.f_desc.set_value(self.medicine_data.get('description', ''))

    def _on_save(self):
        name = self.f_name.get_value()
        generic = self.f_generic.get_value()
        category = self.f_category.get_value() or 'General'
        unit = self.f_unit.get_value() or 'Tablet'
        mfg = self.f_mfg.get_value()
        thresh_str = self.f_threshold.get_value()
        desc = self.f_desc.get_value()

        # Validation
        valid_name, err_name = validate_medicine_name(name)
        if not valid_name:
            self.f_name.set_error(err_name)
            return
        self.f_name.clear_error()

        valid_qty, err_qty = validate_quantity(thresh_str)
        if not valid_qty:
            self.f_threshold.set_error("Threshold must be a non-negative whole number.")
            return
        self.f_threshold.clear_error()

        threshold = int(thresh_str)

        try:
            if self.is_edit:
                med_id = self.medicine_data['medicine_id']
                self.app.medicine_service.update_medicine(
                    medicine_id=med_id,
                    name=name,
                    generic_name=generic,
                    category=category,
                    manufacturer=mfg,
                    description=desc,
                    unit_type=unit,
                    min_stock_threshold=threshold
                )
                messagebox.showinfo("Success", f"Medicine '{name}' updated successfully!", parent=self)
            else:
                self.app.medicine_service.add_medicine(
                    name=name,
                    generic_name=generic,
                    category=category,
                    manufacturer=mfg,
                    description=desc,
                    unit_type=unit,
                    min_stock_threshold=threshold
                )
                messagebox.showinfo("Success", f"Medicine '{name}' added successfully!", parent=self)

            if self.on_success:
                self.on_success()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error Saving Medicine", str(e), parent=self)


class MedicinesView(tk.Frame):
    """
    Medicines Catalog View with search, filtering, and CRUD management.
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
            title_frame, text="💊 Medicine Catalog",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Manage pharmaceutical products, dosage units, and stock alert levels",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        # Action Buttons in Top Header
        btn_frame = tk.Frame(header, bg=c['bg'])
        btn_frame.pack(side='right')

        ttk.Button(
            btn_frame, text="➕ Add Medicine",
            command=self.open_add_dialog,
            style='Primary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="✏️ Edit",
            command=self.open_edit_dialog,
            style='Secondary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="📦 View Batches",
            command=self._view_batches_for_selected,
            style='Secondary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="🔄 Refresh",
            command=self.refresh,
            style='Secondary.TButton'
        ).pack(side='right')

        # Search and Filter Toolbar
        toolbar = tk.Frame(self, bg=c['card_bg'],
                           highlightbackground=c['card_border'], highlightthickness=1)
        toolbar.pack(fill='x', padx=24, pady=10)

        tool_inner = tk.Frame(toolbar, bg=c['card_bg'])
        tool_inner.pack(fill='x', padx=14, pady=10)

        self.search_bar = SearchBar(
            tool_inner,
            on_search=self._on_search,
            placeholder="Search by medicine or generic name (type to filter)...",
            filter_options=CATEGORIES,
            theme_manager=self.tm
        )
        self.search_bar.pack(side='left', fill='x', expand=True)

        # Main Table Card
        table_card = tk.Frame(self, bg=c['card_bg'],
                              highlightbackground=c['card_border'], highlightthickness=1)
        table_card.pack(fill='both', expand=True, padx=24, pady=(0, 10))

        columns = [
            {'key': 'medicine_id', 'label': 'ID', 'width': 50, 'anchor': 'center'},
            {'key': 'name', 'label': 'Medicine Name', 'width': 200},
            {'key': 'generic_name', 'label': 'Generic Name', 'width': 180},
            {'key': 'category', 'label': 'Category', 'width': 130},
            {'key': 'unit_type', 'label': 'Form', 'width': 90},
            {'key': 'manufacturer', 'label': 'Manufacturer', 'width': 160},
            {'key': 'total_stock', 'label': 'Total Stock', 'width': 100, 'anchor': 'e'},
            {'key': 'min_stock_threshold', 'label': 'Threshold', 'width': 90, 'anchor': 'e'},
            {'key': 'stock_status', 'label': 'Status', 'width': 130, 'anchor': 'center'},
        ]

        self.table = DataTable(
            table_card, columns, self.tm,
            on_double_click=lambda e: self.open_edit_dialog()
        )
        self.table.pack(fill='both', expand=True, padx=12, pady=12)

        # Right-Click Context Menu for mouse users
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="✏️ Edit Medicine", command=self.open_edit_dialog)
        self.context_menu.add_command(label="📦 View Batches", command=self._view_batches_for_selected)
        self.context_menu.add_command(label="➕ Register Batch for This Medicine", command=self._add_batch_for_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🗑️ Delete Medicine", command=self._delete_selected)
        self.table.tree.bind("<Button-3>", self._on_right_click)

        # Bottom Action Bar
        bottom_bar = tk.Frame(self, bg=c['bg'])
        bottom_bar.pack(fill='x', padx=24, pady=(0, 16))

        self.lbl_count = tk.Label(
            bottom_bar, text="0 medicines found",
            font=('Segoe UI', 9),
            bg=c['bg'], fg=c['text_secondary']
        )
        self.lbl_count.pack(side='left')

        act_frame = tk.Frame(bottom_bar, bg=c['bg'])
        act_frame.pack(side='right')

        ttk.Button(
            act_frame, text="📦 View Batches",
            command=self._view_batches_for_selected,
            style='Secondary.TButton'
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

    def refresh(self):
        """Reload all medicines with their aggregate stock levels."""
        meds = self.app.medicine_service.get_all_medicines_with_stock()
        self._display_medicines(meds)

    def _display_medicines(self, meds):
        display_data = []
        for m in meds:
            stock = m.get('total_stock', 0)
            thresh = m.get('min_stock_threshold', 10)
            status = '⚠️ LOW STOCK' if stock < thresh else '✓ IN STOCK'
            display_data.append({
                'medicine_id': m['medicine_id'],
                'name': m['name'],
                'generic_name': m.get('generic_name', '') or '-',
                'category': m.get('category', 'General'),
                'unit_type': m.get('unit_type', 'Tablet'),
                'manufacturer': m.get('manufacturer', '') or '-',
                'total_stock': f"{stock:,}",
                'min_stock_threshold': f"{thresh:,}",
                'stock_status': status
            })

        self.table.populate(
            display_data, tag_key='stock_status',
            empty_msg="No medicines match your search. Use 'Add Medicine' or clear search."
        )
        low_count = sum(1 for m in meds if m.get('total_stock', 0) < m.get('min_stock_threshold', 10))
        summary_txt = f"{len(display_data)} medicines registered"
        if low_count > 0:
            summary_txt += f"  •  ⚠️ {low_count} item(s) below threshold"
        self.lbl_count.configure(text=summary_txt)

    def _on_right_click(self, event):
        item = self.table.tree.identify_row(event.y)
        if item:
            self.table.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _add_batch_for_selected(self):
        selected = self.table.get_selected()
        if not selected:
            return
        med_id = int(selected['medicine_id'])
        self.app.show_view('batches', filter_medicine_id=med_id)
        batch_view = self.app.views.get('batches')
        if batch_view and hasattr(batch_view, 'open_add_dialog'):
            self.after(50, batch_view.open_add_dialog)

    def _on_search(self, query: str, category: str):
        cat_filter = None if category == 'All' else category
        results = self.app.medicine_service.search_medicines(query=query, category=cat_filter)
        self._display_medicines(results)

    def _clear_filters(self):
        self.search_bar.clear()
        self.refresh()

    def open_add_dialog(self):
        MedicineDialog(self, self.app, on_success=self.refresh)

    def open_edit_dialog(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Select Medicine", "Please select a medicine from the list to edit.", parent=self)
            return

        med_id = int(selected['medicine_id'])
        med = self.app.medicine_service.get_medicine(med_id)
        if med:
            MedicineDialog(self, self.app, medicine_data=med, on_success=self.refresh)

    def _delete_selected(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Select Medicine", "Please select a medicine from the list to delete.", parent=self)
            return

        med_id = int(selected['medicine_id'])
        name = selected['name']

        if ConfirmDialog.show(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{name}'?\n\n"
            f"WARNING: All associated batches and stock transactions will also be permanently deleted!"
        ):
            self.app.medicine_service.delete_medicine(med_id)
            messagebox.showinfo("Deleted", f"Medicine '{name}' has been deleted.", parent=self)
            self.refresh()

    def _view_batches_for_selected(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Select Medicine", "Please select a medicine to view its batches.", parent=self)
            return
        med_id = int(selected['medicine_id'])
        self.app.show_view('batches', filter_medicine_id=med_id)

    def apply_theme(self):
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.refresh()

