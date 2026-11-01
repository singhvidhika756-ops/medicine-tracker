"""
MediVault Reusable Widgets
===========================
Custom Tkinter / ttk widgets designed for high usability, responsiveness,
and clean visual ergonomics across MediVault.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta


# ============================================================================
# 1. SidebarNav — left-hand navigation panel
# ============================================================================

class SidebarNav(tk.Frame):
    """
    A fixed-width sidebar with clean icons and active highlights.
    """

    NAV_ITEMS = [
        ('dashboard',  '📊', 'Dashboard'),
        ('medicines',  '💊', 'Medicines'),
        ('batches',    '📦', 'Batches'),
        ('alerts',     '⚠️', 'Expiry Alerts'),
        ('stock',      '📋', 'Stock & Audit'),
        ('reports',    '📄', 'Reports'),
        ('settings',   '⚙️', 'Settings'),
    ]

    WIDTH = 220

    def __init__(self, parent, theme_manager, on_navigate=None):
        self._tm = theme_manager
        c = self._tm.colors

        super().__init__(parent, bg=c['sidebar_bg'], width=self.WIDTH)
        self.pack_propagate(False)

        self._on_navigate = on_navigate
        self._active = 'dashboard'
        self._items: dict[str, tk.Frame] = {}

        # Logo Header
        logo_frame = tk.Frame(self, bg=c['sidebar_bg'])
        logo_frame.pack(fill='x', pady=(24, 20))

        tk.Label(
            logo_frame, text='💊 MediVault',
            font=('Segoe UI', 16, 'bold'),
            bg=c['sidebar_bg'], fg='#FFFFFF',
        ).pack(padx=20, anchor='w')

        tk.Label(
            logo_frame, text='Pharmacy Inventory & Expiry',
            font=('Segoe UI', 8),
            bg=c['sidebar_bg'], fg=c['sidebar_fg'],
        ).pack(padx=20, anchor='w', pady=(2, 0))

        # Nav Items
        for key, icon, label in self.NAV_ITEMS:
            self._create_nav_item(key, icon, label)

        # Bottom Version Tag
        bot_frame = tk.Frame(self, bg=c['sidebar_bg'])
        bot_frame.pack(side='bottom', fill='x', pady=16, padx=20)
        tk.Label(
            bot_frame, text="MediVault v1.0 • Offline",
            font=('Segoe UI', 8),
            bg=c['sidebar_bg'], fg='#64748B'
        ).pack(anchor='w')

    def _create_nav_item(self, key: str, icon: str, label: str):
        c = self._tm.colors
        is_active = (key == self._active)

        bg = c['sidebar_active_bg'] if is_active else c['sidebar_bg']
        fg = c['sidebar_active_fg'] if is_active else c['sidebar_fg']

        frame = tk.Frame(self, bg=bg, cursor='hand2')
        frame.pack(fill='x', padx=8, pady=2)

        icon_lbl = tk.Label(
            frame, text=icon, font=('Segoe UI', 12),
            bg=bg, fg=fg,
        )
        icon_lbl.pack(side='left', padx=(14, 8), pady=9)

        text_lbl = tk.Label(
            frame, text=label, font=('Segoe UI', 10, 'bold' if is_active else 'normal'),
            bg=bg, fg=fg, anchor='w',
        )
        text_lbl.pack(side='left', fill='x', expand=True, pady=9)

        for widget in (frame, icon_lbl, text_lbl):
            widget.bind('<Button-1>', lambda e, k=key: self._on_click(k))
            widget.bind('<Enter>', lambda e, f=frame, k=key: self._on_enter(f, k))
            widget.bind('<Leave>', lambda e, f=frame, k=key: self._on_leave(f, k))

        self._items[key] = frame

    def _on_click(self, key: str):
        if key == self._active:
            return
        self._active = key
        self._refresh_styles()
        if self._on_navigate:
            self._on_navigate(key)

    def _on_enter(self, frame: tk.Frame, key: str):
        if key == self._active:
            return
        c = self._tm.colors
        self._set_frame_colors(frame, c['sidebar_hover_bg'], c['sidebar_fg'])

    def _on_leave(self, frame: tk.Frame, key: str):
        if key == self._active:
            return
        c = self._tm.colors
        self._set_frame_colors(frame, c['sidebar_bg'], c['sidebar_fg'])

    def _refresh_styles(self):
        c = self._tm.colors
        for key, frame in self._items.items():
            if key == self._active:
                bg, fg = c['sidebar_active_bg'], c['sidebar_active_fg']
            else:
                bg, fg = c['sidebar_bg'], c['sidebar_fg']
            self._set_frame_colors(frame, bg, fg)

    @staticmethod
    def _set_frame_colors(frame: tk.Frame, bg: str, fg: str):
        frame.configure(bg=bg)
        for child in frame.winfo_children():
            child.configure(bg=bg, fg=fg)

    def set_active(self, key: str):
        self._active = key
        self._refresh_styles()

    def apply_theme(self):
        c = self._tm.colors
        self.configure(bg=c['sidebar_bg'])
        self._refresh_styles()


# ============================================================================
# 2. StatCard — Interactive KPI metric card
# ============================================================================

class StatCard(tk.Frame):
    """
    A polished KPI metric card with accent stripe, bold value, subtitle,
    and optional click-through navigation.
    """

    def __init__(self, parent, title: str, value: str, icon: str,
                 color: str, theme_manager, on_click=None):
        self._tm = theme_manager
        self.on_click = on_click
        self.color = color
        c = self._tm.colors
        card_bg = c['card_bg']

        super().__init__(parent, bg=card_bg, highlightthickness=1,
                         highlightbackground=c['card_border'], bd=0)

        # Coloured accent bar on the left
        self.accent = tk.Frame(self, bg=color, width=5)
        self.accent.pack(side='left', fill='y')

        # Content container
        self.content = tk.Frame(self, bg=card_bg)
        self.content.pack(side='left', fill='both', expand=True, padx=14, pady=10)

        # Top row: icon + value
        self.top = tk.Frame(self.content, bg=card_bg)
        self.top.pack(fill='x')

        self.icon_lbl = tk.Label(self.top, text=icon, font=('Segoe UI', 18),
                                 bg=card_bg, fg=color)
        self.icon_lbl.pack(side='left')

        self._value_lbl = tk.Label(
            self.top, text=str(value),
            font=('Segoe UI', 24, 'bold'),
            bg=card_bg, fg=c['text'],
        )
        self._value_lbl.pack(side='right')

        # Title row
        self._title_lbl = tk.Label(
            self.content, text=title,
            font=('Segoe UI', 9, 'bold'),
            bg=card_bg, fg=c['text_secondary'],
            anchor='w',
        )
        self._title_lbl.pack(fill='x', pady=(4, 0))

        # Clickable bindings
        if on_click:
            clickable_widgets = (self, self.accent, self.content, self.top,
                                 self.icon_lbl, self._value_lbl, self._title_lbl)
            for w in clickable_widgets:
                w.configure(cursor='hand2')
                w.bind('<Button-1>', lambda e: on_click())
                w.bind('<Enter>', self._on_enter)
                w.bind('<Leave>', self._on_leave)

    def _on_enter(self, _event):
        self.configure(highlightbackground=self.color, highlightthickness=1)

    def _on_leave(self, _event):
        c = self._tm.colors
        self.configure(highlightbackground=c['card_border'], highlightthickness=1)

    def update_value(self, value):
        self._value_lbl.configure(text=str(value))


# ============================================================================
# 3. SearchBar — Live search with instant filtering and clear button
# ============================================================================

class SearchBar(tk.Frame):
    """
    Search bar with live typing search, category dropdown filter,
    and a quick clear (✕) button.
    """

    def __init__(self, parent, on_search, placeholder='Search...',
                 filter_options=None, theme_manager=None):
        self._tm = theme_manager
        c = self._tm.colors if self._tm else {}
        bg = c.get('card_bg', '#FFFFFF')

        super().__init__(parent, bg=bg)

        self._on_search = on_search
        self._placeholder = placeholder
        self._debounce_timer = None

        # Search Entry wrapper for icon + entry + clear button
        search_box = tk.Frame(self, bg=bg)
        search_box.pack(side='left', padx=(0, 8))

        self._entry_var = tk.StringVar()
        self._entry = ttk.Entry(
            search_box, textvariable=self._entry_var,
            width=32, font=('Segoe UI', 10)
        )
        self._entry.pack(side='left', ipady=3)
        self._entry.insert(0, placeholder)
        self._entry.configure(foreground=c.get('text_muted', '#9CA3AF'))

        self._entry.bind('<FocusIn>', self._on_focus_in)
        self._entry.bind('<FocusOut>', self._on_focus_out)
        self._entry.bind('<KeyRelease>', self._on_key_release)
        self._entry.bind('<Return>', lambda e: self._do_search())

        # Category Filter Combobox
        self._filter_var = tk.StringVar(value='All')
        if filter_options:
            options = ['All'] + list(filter_options)
            self._filter = ttk.Combobox(
                self, textvariable=self._filter_var,
                values=options, state='readonly', width=16,
                font=('Segoe UI', 10),
            )
            self._filter.pack(side='left', padx=(0, 8))
            self._filter.bind('<<ComboboxSelected>>', lambda e: self._do_search())
        else:
            self._filter = None

        # Clear button
        self.btn_clear = ttk.Button(
            self, text='✕ Clear', command=self.clear,
            style='Secondary.TButton'
        )
        self.btn_clear.pack(side='left')

    def _on_focus_in(self, _event):
        if self._entry.get() == self._placeholder:
            self._entry.delete(0, 'end')
            c = self._tm.colors if self._tm else {}
            self._entry.configure(foreground=c.get('text', '#1F2937'))

    def _on_focus_out(self, _event):
        if not self._entry.get().strip():
            c = self._tm.colors if self._tm else {}
            self._entry.insert(0, self._placeholder)
            self._entry.configure(foreground=c.get('text_muted', '#9CA3AF'))

    def _on_key_release(self, _event):
        # Cancel previous timer if user continues typing (debounce of 150ms)
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        self._debounce_timer = self.after(150, self._do_search)

    def _do_search(self):
        query = self._entry.get().strip()
        if query == self._placeholder:
            query = ''
        filt = self._filter_var.get() if self._filter else 'All'
        self._on_search(query, filt)

    def clear(self):
        self._entry.delete(0, 'end')
        c = self._tm.colors if self._tm else {}
        self._entry.insert(0, self._placeholder)
        self._entry.configure(foreground=c.get('text_muted', '#9CA3AF'))
        if self._filter:
            self._filter_var.set('All')
        self._do_search()

    def focus_search(self):
        self._entry.focus_set()
        if self._entry.get() == self._placeholder:
            self._entry.delete(0, 'end')


# ============================================================================
# 4. DataTable — Treeview with sorting, tags & friendly empty state
# ============================================================================

class DataTable(tk.Frame):
    """
    Enhanced tabular Treeview with column headers, alternating row colors,
    click-to-sort columns, and clear empty state messaging.
    """

    def __init__(self, parent, columns: list, theme_manager,
                 show_scrollbar=True, on_select=None,
                 on_double_click=None):
        self._tm = theme_manager
        c = self._tm.colors

        super().__init__(parent, bg=c['bg'])

        self._columns = columns
        self._sort_directions: dict[str, bool] = {col['key']: True for col in columns}
        col_keys = [col['key'] for col in columns]

        self.tree = ttk.Treeview(
            self, columns=col_keys, show='headings',
            selectmode='browse',
        )

        for col in columns:
            anchor = col.get('anchor', 'w')
            key = col['key']
            self.tree.heading(
                key, text=col['label'], anchor=anchor,
                command=lambda k=key: self._sort_column(k)
            )
            self.tree.column(key, width=col['width'], minwidth=50,
                             anchor=anchor, stretch=True)

        if show_scrollbar:
            vsb = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
            self.tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side='right', fill='y')

        self.tree.pack(side='left', fill='both', expand=True)

        if on_select:
            self.tree.bind('<<TreeviewSelect>>', on_select)
        if on_double_click:
            self.tree.bind('<Double-1>', on_double_click)

        self._apply_row_tags()

    def _apply_row_tags(self):
        c = self._tm.colors
        is_dark = (self._tm.current_theme == 'dark')

        if is_dark:
            self.tree.tag_configure('oddrow', background='#1E293B', foreground='#F8FAFC')
            self.tree.tag_configure('evenrow', background='#0F172A', foreground='#F8FAFC')
            self.tree.tag_configure('expired', background='#450A0A', foreground='#FCA5A5')
            self.tree.tag_configure('critical', background='#431407', foreground='#FDBA74')
            self.tree.tag_configure('warning', background='#451A03', foreground='#FDE68A')
            self.tree.tag_configure('upcoming', background='#1E293B', foreground='#E2E8F0')
            self.tree.tag_configure('normal', background='#1E293B', foreground='#F8FAFC')
            self.tree.tag_configure('low_stock', background='#451A03', foreground='#FDE68A')
            self.tree.tag_configure('added', background='#052E16', foreground='#86EFAC')
            self.tree.tag_configure('removed', background='#450A0A', foreground='#FCA5A5')
            self.tree.tag_configure('adjusted', background='#172554', foreground='#93C5FD')
            self.tree.tag_configure('initial', background='#1E293B', foreground='#94A3B8')
            self.tree.tag_configure('empty_state', foreground='#94A3B8', font=('Segoe UI', 10, 'italic'))
        else:
            self.tree.tag_configure('oddrow', background='#FFFFFF', foreground='#0F172A')
            self.tree.tag_configure('evenrow', background='#F8FAFC', foreground='#0F172A')
            self.tree.tag_configure('expired', background='#FEE2E2', foreground='#991B1B')
            self.tree.tag_configure('critical', background='#FFEDD5', foreground='#9A3412')
            self.tree.tag_configure('warning', background='#FEF3C7', foreground='#92400E')
            self.tree.tag_configure('upcoming', background='#F8FAFC', foreground='#0F172A')
            self.tree.tag_configure('normal', background='#FFFFFF', foreground='#0F172A')
            self.tree.tag_configure('low_stock', background='#FEF3C7', foreground='#92400E')
            self.tree.tag_configure('added', background='#DCFCE7', foreground='#166534')
            self.tree.tag_configure('removed', background='#FEE2E2', foreground='#991B1B')
            self.tree.tag_configure('adjusted', background='#DBEAFE', foreground='#1E40AF')
            self.tree.tag_configure('initial', background='#F8FAFC', foreground='#334155')
            self.tree.tag_configure('empty_state', foreground='#64748B', font=('Segoe UI', 10, 'italic'))

    def populate(self, data: list, tag_key: str = None, empty_msg: str = "No records found."):
        self.clear()
        col_keys = [col['key'] for col in self._columns]

        if not data:
            empty_row = [''] * len(col_keys)
            if col_keys:
                empty_row[min(1, len(col_keys) - 1)] = f"  ℹ️ {empty_msg}"
            self.tree.insert('', 'end', values=empty_row, tags=['empty_state'])
            return

        for idx, row in enumerate(data):
            values = [row.get(k, '') for k in col_keys]
            alt_tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tags = [alt_tag]
            if tag_key and tag_key in row:
                status_tag = str(row[tag_key]).lower().replace(' ', '_')
                tags.append(status_tag)
            self.tree.insert('', 'end', values=values, tags=tags)

    def _sort_column(self, col_key: str):
        items = [(self.tree.set(k, col_key), k) for k in self.tree.get_children('')]
        if not items:
            return

        reverse = self._sort_directions[col_key]
        self._sort_directions[col_key] = not reverse

        # Try numeric sorting if possible
        def sort_val(val):
            v_str = str(val[0]).replace('₹', '').replace(',', '').replace('d', '').replace('+', '').replace('-', '').strip()
            try:
                return float(v_str)
            except ValueError:
                return str(val[0]).lower()

        items.sort(key=sort_val, reverse=reverse)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, '', index)

    def get_selected(self) -> dict | None:
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], 'values')
        col_keys = [col['key'] for col in self._columns]
        return dict(zip(col_keys, values))

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def get_all_data(self) -> list:
        col_keys = [col['key'] for col in self._columns]
        rows = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            rows.append(dict(zip(col_keys, values)))
        return rows


# ============================================================================
# 5. FormField — Input field with date shortcuts & live error cleaning
# ============================================================================

class FormField(tk.Frame):
    """
    Form field with labels, quick date calculation buttons, and validation error messages.
    """

    def __init__(self, parent, label: str, field_type='entry',
                 options=None, required=False, theme_manager=None):
        self._tm = theme_manager
        c = self._tm.colors if self._tm else {}
        bg = c.get('card_bg', '#FFFFFF')

        super().__init__(parent, bg=bg)

        self._required = required
        self._field_type = field_type

        # Label Header
        lbl_text = f"{label} *" if required else label
        self._label = tk.Label(
            self, text=lbl_text,
            font=('Segoe UI', 9, 'bold'),
            bg=bg, fg=c.get('text', '#1F2937'),
            anchor='w'
        )
        self._label.pack(fill='x', pady=(0, 2))

        self._var = tk.StringVar()

        if field_type in ('entry', 'date'):
            self._widget = ttk.Entry(self, textvariable=self._var, font=('Segoe UI', 10))
            self._widget.pack(fill='x', ipady=3)
            self._var.trace_add("write", lambda *args: self.clear_error())

            if field_type == 'date':
                # Quick Date Helper Buttons
                btn_row = tk.Frame(self, bg=bg)
                btn_row.pack(fill='x', pady=(3, 0))

                tk.Label(
                    btn_row, text="Quick:", font=('Segoe UI', 8),
                    bg=bg, fg=c.get('text_muted', '#9CA3AF')
                ).pack(side='left', padx=(0, 4))

                def set_offset(days):
                    target = date.today() + timedelta(days=days)
                    self._var.set(target.strftime("%Y-%m-%d"))

                btn_today = ttk.Button(btn_row, text="Today", style='Secondary.TButton',
                                       command=lambda: set_offset(0))
                btn_today.pack(side='left', padx=2)

                btn_6m = ttk.Button(btn_row, text="+6 Mos", style='Secondary.TButton',
                                    command=lambda: set_offset(180))
                btn_6m.pack(side='left', padx=2)

                btn_1y = ttk.Button(btn_row, text="+1 Year", style='Secondary.TButton',
                                    command=lambda: set_offset(365))
                btn_1y.pack(side='left', padx=2)

                btn_2y = ttk.Button(btn_row, text="+2 Years", style='Secondary.TButton',
                                    command=lambda: set_offset(730))
                btn_2y.pack(side='left', padx=2)

        elif field_type == 'combo':
            self._widget = ttk.Combobox(
                self, textvariable=self._var,
                values=options or [], state='readonly',
                font=('Segoe UI', 10),
            )
            self._widget.pack(fill='x', ipady=3)
            self._var.trace_add("write", lambda *args: self.clear_error())

        elif field_type == 'spinbox':
            self._var = tk.IntVar(value=0)
            self._widget = ttk.Spinbox(
                self, textvariable=self._var,
                from_=0, to=999999, font=('Segoe UI', 10),
            )
            self._widget.pack(fill='x', ipady=3)

        elif field_type == 'text':
            self._widget = tk.Text(
                self, height=3, font=('Segoe UI', 10), wrap='word',
                bg=c.get('input_bg', '#FFFFFF'), fg=c.get('text', '#1F2937'),
                insertbackground=c.get('text', '#1F2937'),
                relief='solid', borderwidth=1, highlightthickness=0
            )
            self._widget.pack(fill='x')
        else:
            self._widget = ttk.Entry(self, textvariable=self._var, font=('Segoe UI', 10))
            self._widget.pack(fill='x', ipady=3)

        self._error_lbl = tk.Label(
            self, text='', font=('Segoe UI', 8, 'italic'),
            bg=bg, fg=c.get('danger', '#EF4444'), anchor='w'
        )
        self._error_lbl.pack(fill='x')

    def get_value(self) -> str:
        if self._field_type == 'text':
            return self._widget.get('1.0', 'end').strip()
        if self._field_type == 'spinbox':
            try:
                return str(self._var.get())
            except tk.TclError:
                return '0'
        return self._var.get().strip()

    def set_value(self, val):
        if self._field_type == 'text':
            self._widget.delete('1.0', 'end')
            self._widget.insert('1.0', str(val))
        elif self._field_type == 'spinbox':
            try:
                self._var.set(int(val))
            except (ValueError, tk.TclError):
                self._var.set(0)
        else:
            self._var.set(str(val))

    def clear(self):
        if self._field_type == 'text':
            self._widget.delete('1.0', 'end')
        elif self._field_type == 'spinbox':
            self._var.set(0)
        else:
            self._var.set('')
        self.clear_error()

    def set_error(self, msg: str):
        self._error_lbl.configure(text=f"⚠️ {msg}")

    def clear_error(self):
        self._error_lbl.configure(text='')

    def focus(self):
        self._widget.focus_set()


# ============================================================================
# 6. StatusBadge
# ============================================================================

class StatusBadge(tk.Label):
    """Visual pill badge for statuses."""

    _STATUS_COLORS = {
        'EXPIRED':   ('#FFFFFF', '#EF4444'),
        'CRITICAL':  ('#FFFFFF', '#EA580C'),
        'WARNING':   ('#1F2937', '#F59E0B'),
        'UPCOMING':  ('#1F2937', '#84CC16'),
        'NORMAL':    ('#FFFFFF', '#10B981'),
        'LOW STOCK': ('#1F2937', '#F59E0B'),
    }

    def __init__(self, parent, status: str, theme_manager=None):
        fg, bg = self._STATUS_COLORS.get(status.upper(), ('#FFFFFF', '#6B7280'))
        super().__init__(
            parent, text=f"  {status.upper()}  ",
            font=('Segoe UI', 9, 'bold'),
            bg=bg, fg=fg, padx=6, pady=2
        )


# ============================================================================
# 7. ConfirmDialog
# ============================================================================

class ConfirmDialog:
    """User-friendly confirmation dialog."""

    @staticmethod
    def show(parent, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=parent)
