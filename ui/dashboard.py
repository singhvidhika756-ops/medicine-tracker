"""
dashboard.py — Dashboard View for MediVault.

Displays key performance indicators (KPI stat cards), immediate expiry warnings,
category distribution, and recent stock transactions.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ui.widgets import StatCard, DataTable

if TYPE_CHECKING:
    from ui.app import MediVaultApp


class DashboardView(tk.Frame):
    """
    Dashboard view showing statistics, alerts, and recent inventory transactions.
    """

    def __init__(self, parent: tk.Widget, app: 'MediVaultApp'):
        self.app = app
        self.tm = app.theme_manager
        c = self.tm.colors

        super().__init__(parent, bg=c['bg'])

        self._build_ui()

    def _build_ui(self):
        c = self.tm.colors

        # Top Header
        header = tk.Frame(self, bg=c['bg'])
        header.pack(fill='x', padx=24, pady=(20, 10))

        title_frame = tk.Frame(header, bg=c['bg'])
        title_frame.pack(side='left')

        tk.Label(
            title_frame, text="📊 Inventory Dashboard",
            font=('Segoe UI', 18, 'bold'),
            bg=c['bg'], fg=c['text']
        ).pack(anchor='w')

        tk.Label(
            title_frame, text="Real-time stock status, expiry alerts, and movements",
            font=('Segoe UI', 10),
            bg=c['bg'], fg=c['text_secondary']
        ).pack(anchor='w')

        # Action Buttons on Right
        btn_frame = tk.Frame(header, bg=c['bg'])
        btn_frame.pack(side='right')

        ttk.Button(
            btn_frame, text="🔄 Refresh",
            command=self.refresh,
            style='Secondary.TButton'
        ).pack(side='right', padx=(6, 0))

        ttk.Button(
            btn_frame, text="➕ Add Medicine",
            command=lambda: self.app.show_view('medicines', action='add'),
            style='Primary.TButton'
        ).pack(side='right')

        # Scrollable container for dashboard content
        self.canvas = tk.Canvas(self, bg=c['bg'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=c['bg'])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.pack(side="left", fill="both", expand=True, padx=20, pady=(0, 10))
        self.scrollbar.pack(side="right", fill="y", pady=(0, 10))

        # 1. Alert Banner (Conditional)
        self.alert_banner = tk.Frame(self.scrollable_frame, bg=c['card_bg'],
                                     highlightbackground=c['card_border'], highlightthickness=1)
        self.alert_label = tk.Label(self.alert_banner, text="", font=('Segoe UI', 10, 'bold'),
                                    bg=c['card_bg'], fg=c['danger'])
        self.alert_label.pack(side='left', padx=16, pady=10)
        self.alert_btn = ttk.Button(
            self.alert_banner, text="View Alerts ➔",
            command=lambda: self.app.show_view('alerts'),
            style='Danger.TButton'
        )
        self.alert_btn.pack(side='right', padx=16, pady=6)

        # 2. KPI Stat Cards Grid (4 columns x 2 rows) - Clickable for fast navigation
        self.cards_frame = tk.Frame(self.scrollable_frame, bg=c['bg'])
        self.cards_frame.pack(fill='x', pady=10)

        # Card instances with one-click direct navigation
        self.card_meds = StatCard(
            self.cards_frame, "Total Medicines", "0", "💊", c['primary'], self.tm,
            on_click=lambda: self.app.show_view('medicines')
        )
        self.card_batches = StatCard(
            self.cards_frame, "Total Batches", "0", "📦", c['info'], self.tm,
            on_click=lambda: self.app.show_view('batches')
        )
        self.card_units = StatCard(
            self.cards_frame, "Available Units", "0", "📊", c['success'], self.tm,
            on_click=lambda: self.app.show_view('batches')
        )
        self.card_value = StatCard(
            self.cards_frame, "Inventory Value", "₹0.00", "💰", "#8B5CF6", self.tm,
            on_click=lambda: self.app.show_view('reports')
        )

        self.card_expired = StatCard(
            self.cards_frame, "Expired Batches", "0", "🚨", c['danger'], self.tm,
            on_click=lambda: self._go_alerts(0)
        )
        self.card_crit = StatCard(
            self.cards_frame, "Expiring (≤ 7 Days)", "0", "⚠️", "#EA580C", self.tm,
            on_click=lambda: self._go_alerts(1)
        )
        self.card_upcom = StatCard(
            self.cards_frame, "Expiring (≤ 30 Days)", "0", "⏳", c['warning'], self.tm,
            on_click=lambda: self._go_alerts(3)
        )
        self.card_low = StatCard(
            self.cards_frame, "Low Stock Items", "0", "📉", "#D97706", self.tm,
            on_click=lambda: self._go_alerts(4)
        )

        cards = [
            (self.card_meds, 0, 0), (self.card_batches, 0, 1),
            (self.card_units, 0, 2), (self.card_value, 0, 3),
            (self.card_expired, 1, 0), (self.card_crit, 1, 1),
            (self.card_upcom, 1, 2), (self.card_low, 1, 3)
        ]

        for card, row, col in cards:
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            self.cards_frame.columnconfigure(col, weight=1)

        # 3. Two Column Section (Recent Transactions & Category Distribution)
        content_cols = tk.Frame(self.scrollable_frame, bg=c['bg'])
        content_cols.pack(fill='both', expand=True, pady=12)

        # Left Column: Recent Stock Transactions (Weight 3)
        left_col = tk.Frame(content_cols, bg=c['card_bg'],
                            highlightbackground=c['card_border'], highlightthickness=1)
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 8))

        left_header = tk.Frame(left_col, bg=c['card_bg'])
        left_header.pack(fill='x', padx=14, pady=10)

        tk.Label(
            left_header, text="Recent Stock Movements",
            font=('Segoe UI', 12, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left')

        ttk.Button(
            left_header, text="View All ➔",
            command=lambda: self.app.show_view('stock'),
            style='Secondary.TButton'
        ).pack(side='right')

        tx_cols = [
            {'key': 'transaction_date', 'label': 'Date & Time', 'width': 130},
            {'key': 'medicine_name', 'label': 'Medicine', 'width': 140},
            {'key': 'batch_number', 'label': 'Batch #', 'width': 90},
            {'key': 'transaction_type', 'label': 'Type', 'width': 80},
            {'key': 'quantity_changed', 'label': 'Qty', 'width': 60, 'anchor': 'e'},
            {'key': 'reason', 'label': 'Reason', 'width': 140},
        ]

        self.tx_table = DataTable(left_col, tx_cols, self.tm, show_scrollbar=False)
        self.tx_table.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        # Right Column: Category Distribution (Weight 1)
        right_col = tk.Frame(content_cols, bg=c['card_bg'], width=280,
                             highlightbackground=c['card_border'], highlightthickness=1)
        right_col.pack(side='right', fill='both', padx=(8, 0))
        right_col.pack_propagate(False)

        right_header = tk.Frame(right_col, bg=c['card_bg'])
        right_header.pack(fill='x', padx=14, pady=10)

        tk.Label(
            right_header, text="Category Breakdown",
            font=('Segoe UI', 12, 'bold'),
            bg=c['card_bg'], fg=c['text']
        ).pack(side='left')

        self.cat_listbox_frame = tk.Frame(right_col, bg=c['card_bg'])
        self.cat_listbox_frame.pack(fill='both', expand=True, padx=14, pady=(0, 12))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def refresh(self):
        """Fetch fresh statistics and update all dashboard widgets."""
        stats = self.app.report_service.get_dashboard_stats()
        currency = "₹"

        # Update Stat Cards
        self.card_meds.update_value(f"{stats['total_medicines']}")
        self.card_batches.update_value(f"{stats['total_batches']}")
        self.card_units.update_value(f"{stats['total_units']:,}")
        self.card_value.update_value(f"{currency}{stats['total_value']:,.2f}")

        self.card_expired.update_value(f"{stats['expired_batches']}")
        self.card_crit.update_value(f"{stats['expiring_7_days']}")
        self.card_upcom.update_value(f"{stats['expiring_30_days']}")
        self.card_low.update_value(f"{stats['low_stock_medicines']}")

        # Update Alert Banner
        total_critical = stats['expired_batches'] + stats['expiring_7_days']
        if total_critical > 0 or stats['low_stock_medicines'] > 0:
            msg = f"⚠️ ATTENTION: {stats['expired_batches']} expired batch(es), " \
                  f"{stats['expiring_7_days']} expiring within 7 days, " \
                  f"and {stats['low_stock_medicines']} low-stock medicine(s) require action."
            self.alert_label.configure(text=msg)
            self.alert_banner.pack(fill='x', pady=(0, 10), before=self.cards_frame)
        else:
            self.alert_banner.pack_forget()

        # Update Recent Transactions Table
        recent_txs = stats.get('recent_transactions', [])
        display_txs = []
        for tx in recent_txs:
            qty_prefix = "+" if tx['transaction_type'] in ('ADDED', 'INITIAL') else "-"
            display_txs.append({
                'transaction_date': str(tx['transaction_date'])[:16],
                'medicine_name': tx.get('medicine_name', 'Unknown'),
                'batch_number': tx.get('batch_number', '-'),
                'transaction_type': tx['transaction_type'],
                'quantity_changed': f"{qty_prefix}{abs(tx['quantity_changed'])}",
                'reason': tx.get('reason', '')
            })
        self.tx_table.populate(display_txs, tag_key='transaction_type')

        # Update Category Distribution List
        for widget in self.cat_listbox_frame.winfo_children():
            widget.destroy()

        cat_dist = stats.get('category_distribution', {})
        if not cat_dist:
            tk.Label(
                self.cat_listbox_frame, text="No medicines added yet.",
                font=('Segoe UI', 9, 'italic'),
                bg=self.tm.colors['card_bg'], fg=self.tm.colors['text_muted']
            ).pack(anchor='w', pady=10)
        else:
            if isinstance(cat_dist, dict):
                items = list(cat_dist.items())[:8]
            else:
                items = [(i.get('category', 'General'), i.get('count', 0)) for i in cat_dist[:8]]

            for cat_name, count in items:
                row = tk.Frame(self.cat_listbox_frame, bg=self.tm.colors['card_bg'])
                row.pack(fill='x', pady=4)

                cat_display = cat_name or 'General'
                tk.Label(
                    row, text=f"• {cat_display}",
                    font=('Segoe UI', 9),
                    bg=self.tm.colors['card_bg'], fg=self.tm.colors['text']
                ).pack(side='left')

                tk.Label(
                    row, text=f"{count} med(s)",
                    font=('Segoe UI', 9, 'bold'),
                    bg=self.tm.colors['card_bg'], fg=self.tm.colors['primary']
                ).pack(side='right')

    def _go_alerts(self, tab_index: int):
        """Navigate to alerts page and automatically select specified urgency tab."""
        self.app.show_view('alerts')
        alerts_view = self.app.views.get('alerts')
        if alerts_view and hasattr(alerts_view, 'select_tab'):
            alerts_view.select_tab(tab_index)

    def apply_theme(self):
        """Handle theme switch."""
        c = self.tm.colors
        self.configure(bg=c['bg'])
        self.canvas.configure(bg=c['bg'])
        self.scrollable_frame.configure(bg=c['bg'])
        self.cards_frame.configure(bg=c['bg'])
        self.refresh()
