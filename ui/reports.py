"""
reports.py — Reporting and Export View for MediVault.

Allows users to generate, view, and export inventory, expiry, low-stock,
stock movements, and financial valuation reports to CSV format.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Any, List

from ui.widgets import DataTable

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class ReportsView(tk.Frame):
    """
    Reports view with interactive report selector and CSV exporter.
    """

    REPORT_TYPES = [
        "Complete Inventory Report",
        "Expired & Near-Expiry Batches (≤ 30d)",
        "Low Stock Deficit Report",
        "Stock Movement Audit Report",
        "Financial Inventory Valuation",
    ]

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp'):
        self.app = app
        self.tm = app.theme_manager
        self.current_data: List[Dict[str, Any]] = []
        self.current_headers: List[str] = []
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
            title_frame, text="📄 Inventory Reports & Data Export",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Generate auditable tabular reports and export formatted CSV data files",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        btn_frame = tk.Frame(header, bg=c['bg'])
        btn_frame.pack(side='right')

        ttk.Button(
            btn_frame, text="📥 Export to CSV",
            command=self._export_csv,
            style='Primary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="🔄 Generate Report",
            command=self.refresh,
            style='Secondary.TButton'
        ).pack(side='right')

        # Selector Toolbar
        toolbar = tk.Frame(self, bg=c['card_bg'],
                           highlightbackground=c['card_border'], highlightthickness=1)
        toolbar.pack(fill='x', padx=24, pady=10)

        tool_inner = tk.Frame(toolbar, bg=c['card_bg'])
        tool_inner.pack(fill='x', padx=14, pady=10)

        tk.Label(
            tool_inner, text="Select Report Type:",
            font=('Segoe UI', 10, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left', padx=(0, 8))

        self.report_var = tk.StringVar(value=self.REPORT_TYPES[0])
        self.report_combo = ttk.Combobox(
            tool_inner, textvariable=self.report_var,
            values=self.REPORT_TYPES, state='readonly', width=38, font=('Segoe UI', 10)
        )
        self.report_combo.pack(side='left', padx=(0, 14))
        self.report_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # Table Container
        self.table_card = tk.Frame(self, bg=c['card_bg'],
                                   highlightbackground=c['card_border'], highlightthickness=1)
        self.table_card.pack(fill='both', expand=True, padx=24, pady=(0, 10))

        self.table_holder = tk.Frame(self.table_card, bg=c['card_bg'])
        self.table_holder.pack(fill='both', expand=True, padx=12, pady=12)

        self.table: DataTable = None

        # Bottom Status
        bottom_bar = tk.Frame(self, bg=c['bg'])
        bottom_bar.pack(fill='x', padx=24, pady=(0, 16))

        self.lbl_status = tk.Label(
            bottom_bar, text="Ready",
            font=('Segoe UI', 9),
            bg=c['bg'], fg=c['text_secondary']
        )
        self.lbl_status.pack(side='left')

    def refresh(self):
        """Generate the currently selected report and render the appropriate table."""
        report_name = self.report_var.get()
        svc = self.app.report_service

        for child in self.table_holder.winfo_children():
            child.destroy()

        if report_name == "Complete Inventory Report":
            raw = svc.generate_inventory_report()
            cols = [
                {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 170},
                {'key': 'generic_name', 'label': 'Generic Name', 'width': 150},
                {'key': 'category', 'label': 'Category', 'width': 110},
                {'key': 'batch_number', 'label': 'Batch #', 'width': 100},
                {'key': 'expiry_date', 'label': 'Expiry', 'width': 95, 'anchor': 'center'},
                {'key': 'expiry_status', 'label': 'Status', 'width': 90, 'anchor': 'center'},
                {'key': 'current_quantity', 'label': 'Current Stock', 'width': 90, 'anchor': 'e'},
                {'key': 'purchase_price', 'label': 'Cost / Unit', 'width': 85, 'anchor': 'e'},
                {'key': 'supplier', 'label': 'Supplier', 'width': 130},
            ]
            self.current_headers = [c['key'] for c in cols]
            self.current_data = raw
            display_data = [{
                'medicine_name': r['medicine_name'],
                'generic_name': r.get('generic_name', '') or '-',
                'category': r.get('category', 'General'),
                'batch_number': r['batch_number'],
                'expiry_date': r['expiry_date'],
                'expiry_status': r.get('expiry_status', 'NORMAL'),
                'current_quantity': f"{r['current_quantity']:,}",
                'purchase_price': f"₹{r['purchase_price']:,.2f}",
                'supplier': r.get('supplier', '') or '-'
            } for r in raw]

        elif report_name == "Expired & Near-Expiry Batches (≤ 30d)":
            raw = svc.generate_expiry_report()
            cols = [
                {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 180},
                {'key': 'category', 'label': 'Category', 'width': 120},
                {'key': 'batch_number', 'label': 'Batch #', 'width': 120},
                {'key': 'expiry_date', 'label': 'Expiry Date', 'width': 110, 'anchor': 'center'},
                {'key': 'days_until_expiry', 'label': 'Days Left', 'width': 90, 'anchor': 'e'},
                {'key': 'expiry_status', 'label': 'Urgency', 'width': 100, 'anchor': 'center'},
                {'key': 'current_quantity', 'label': 'Units at Risk', 'width': 100, 'anchor': 'e'},
                {'key': 'supplier', 'label': 'Supplier', 'width': 130},
            ]
            self.current_headers = [c['key'] for c in cols]
            self.current_data = raw
            display_data = [{
                'medicine_name': r['medicine_name'],
                'category': r.get('category', 'General'),
                'batch_number': r['batch_number'],
                'expiry_date': r['expiry_date'],
                'days_until_expiry': f"{r['days_until_expiry']}d",
                'expiry_status': r.get('expiry_status', 'NORMAL'),
                'current_quantity': f"{r['current_quantity']:,}",
                'supplier': r.get('supplier', '') or '-'
            } for r in raw]

        elif report_name == "Low Stock Deficit Report":
            raw = svc.generate_low_stock_report()
            cols = [
                {'key': 'medicine_id', 'label': 'ID', 'width': 50, 'anchor': 'center'},
                {'key': 'name', 'label': 'Medicine Name', 'width': 220},
                {'key': 'category', 'label': 'Category', 'width': 140},
                {'key': 'unit_type', 'label': 'Unit Form', 'width': 100},
                {'key': 'total_stock', 'label': 'Total Available', 'width': 110, 'anchor': 'e'},
                {'key': 'min_stock_threshold', 'label': 'Threshold', 'width': 100, 'anchor': 'e'},
                {'key': 'deficit', 'label': 'Deficit', 'width': 100, 'anchor': 'e'},
            ]
            self.current_headers = [c['key'] for c in cols]
            self.current_data = raw
            display_data = [{
                'medicine_id': r['medicine_id'],
                'name': r['name'],
                'category': r.get('category', 'General'),
                'unit_type': r.get('unit_type', 'Tablet'),
                'total_stock': f"{r['total_stock']:,}",
                'min_stock_threshold': f"{r['min_stock_threshold']:,}",
                'deficit': f"-{r['min_stock_threshold'] - r['total_stock']:,}"
            } for r in raw]

        elif report_name == "Stock Movement Audit Report":
            raw = svc.generate_stock_movement_report()
            cols = [
                {'key': 'transaction_id', 'label': 'ID', 'width': 50, 'anchor': 'center'},
                {'key': 'transaction_date', 'label': 'Date & Time', 'width': 130},
                {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 170},
                {'key': 'batch_number', 'label': 'Batch #', 'width': 110},
                {'key': 'transaction_type', 'label': 'Type', 'width': 90, 'anchor': 'center'},
                {'key': 'quantity_changed', 'label': 'Delta', 'width': 75, 'anchor': 'e'},
                {'key': 'new_quantity', 'label': 'New Stock', 'width': 85, 'anchor': 'e'},
                {'key': 'reason', 'label': 'Reason', 'width': 180},
            ]
            self.current_headers = [c['key'] for c in cols]
            self.current_data = raw
            display_data = [{
                'transaction_id': r['transaction_id'],
                'transaction_date': str(r['transaction_date'])[:19],
                'medicine_name': r.get('medicine_name', 'Unknown'),
                'batch_number': r.get('batch_number', '-'),
                'transaction_type': r['transaction_type'],
                'quantity_changed': f"{'+' if r['transaction_type'] in ('ADDED', 'INITIAL') else '-'}{abs(r['quantity_changed'])}",
                'new_quantity': f"{r['new_quantity']:,}",
                'reason': r.get('reason', '')
            } for r in raw]

        else:  # Financial Valuation Report
            raw = svc.generate_valuation_report()
            cols = [
                {'key': 'medicine_name', 'label': 'Medicine Name', 'width': 220},
                {'key': 'category', 'label': 'Category', 'width': 140},
                {'key': 'batch_number', 'label': 'Batch #', 'width': 130},
                {'key': 'quantity', 'label': 'Units in Stock', 'width': 110, 'anchor': 'e'},
                {'key': 'unit_price', 'label': 'Cost / Unit', 'width': 110, 'anchor': 'e'},
                {'key': 'value', 'label': 'Total Valuation', 'width': 130, 'anchor': 'e'},
            ]
            self.current_headers = [c['key'] for c in cols]
            self.current_data = raw
            display_data = [{
                'medicine_name': r['medicine_name'],
                'category': r.get('category', 'General'),
                'batch_number': r['batch_number'],
                'quantity': f"{r['quantity']:,}",
                'unit_price': f"₹{r['unit_price']:,.2f}",
                'value': f"₹{r['value']:,.2f}"
            } for r in raw]

        self.table = DataTable(self.table_holder, cols, self.tm)
        self.table.pack(fill='both', expand=True)
        self.table.populate(display_data)

        self.lbl_status.configure(
            text=f"Report '{report_name}' generated successfully with {len(display_data)} records."
        )

    def _export_csv(self):
        if not self.current_data:
            messagebox.showinfo("No Data", "There are no records to export in the current report.", parent=self)
            return

        slug = self.report_var.get().lower().replace(" ", "_").replace("&", "and").replace("(", "").replace(")", "").replace("≤", "under")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"medivault_{slug}_{timestamp}.csv"

        filepath = filedialog.asksaveasfilename(
            parent=self,
            title="Save CSV Report",
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not filepath:
            return

        success = self.app.report_service.export_to_csv(
            data=self.current_data,
            headers=self.current_headers,
            filepath=filepath
        )

        if success:
            messagebox.showinfo(
                "Export Complete",
                f"Report successfully exported to:\n{filepath}",
                parent=self
            )
        else:
            messagebox.showerror(
                "Export Error",
                "An error occurred while writing the CSV file.",
                parent=self
            )

    def apply_theme(self):
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.refresh()

