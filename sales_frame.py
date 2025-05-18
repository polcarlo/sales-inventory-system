import os
from datetime import datetime

import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar, Combobox, Notebook
from ttkbootstrap.widgets import DateEntry, Checkbutton
from ttkbootstrap.toast import ToastNotification
from tkinter import IntVar

from fpdf import FPDF
from database import get_connection
from report_frame import ReportFrame


class SalesFrame(Frame):
    def __init__(self, master, inventory_frame=None, current_user_role='user'):
        super().__init__(master, padding=20)
        self.inventory_frame = inventory_frame
        self.current_user_role = current_user_role.lower()
        self.is_admin = (self.current_user_role == 'admin')

        notebook = Notebook(self)
        self.sales_tab = Frame(notebook)
        notebook.add(self.sales_tab, text='Sales')
        notebook.add(ReportFrame(notebook), text='Reports')
        notebook.pack(fill='both', expand=True, pady=(0,15))

        self._build_sales_tab()

        self.start_date.entry.delete(0, 'end')
        self.end_date.entry.delete(0, 'end')

        self.load_sales()

    def _build_sales_tab(self):
        Label(self.sales_tab, text="Sales",
              font=("Helvetica", 18, "bold")).pack(pady=(0,15))

        filter_frame = Frame(self.sales_tab)
        Label(filter_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        Entry(filter_frame, textvariable=self.search_var).pack(
            side='left', fill='x', expand=True, padx=(5,5))
        self.search_var.trace_add('write', lambda *a: self.load_sales())

        Label(filter_frame, text="From:").pack(side='left')
        self.start_date = DateEntry(filter_frame, dateformat='%Y-%m-%d')
        self.start_date.pack(side='left', padx=(5,10))

        Label(filter_frame, text="To:").pack(side='left')
        self.end_date = DateEntry(filter_frame, dateformat='%Y-%m-%d')
        self.end_date.pack(side='left', padx=(5,10))

        Label(filter_frame, text="Active:").pack(side='left')
        self.filter_active_var = tb.StringVar(value='All')
        active_cb = Combobox(
            filter_frame,
            textvariable=self.filter_active_var,
            state='readonly',
            values=['All', 'Active', 'Inactive']
        )
        active_cb.pack(side='left', padx=(5,10))
        active_cb.bind('<<ComboboxSelected>>', lambda e: self.load_sales())

        Button(filter_frame, text="Filter",
               bootstyle="secondary", command=self.load_sales)\
            .pack(side='left', padx=5)
        Button(filter_frame, text="Refresh",
               bootstyle="info", command=self._reset_and_reload)\
            .pack(side='left', padx=5)
        filter_frame.pack(fill='x', pady=(0,10))

        table_frame = Frame(self.sales_tab)
        table_frame.pack(fill='both', expand=True, pady=(0,15))
        self._make_tree(table_frame)

        form = Frame(self.sales_tab)
        form.pack(fill='x', pady=(0,15))
        left = Frame(form); left.pack(side='left', fill='both', expand=True, padx=(0,5))
        right = Frame(form); right.pack(side='left', fill='both', expand=True, padx=(5,0))

        fields = [
            ("Receipt No", "receipt_no", left),
            ("Date",       "date",       left),
            ("Product",    "product",    left),
            ("Qty",        "qty",        right),
            ("Notes",      "notes",      right),
            ("Is Active",  "is_active",  right),
        ]
        self.vars = {}
        for lbl, key, parent in fields:
            Label(parent, text=lbl).pack(anchor='w', pady=2)
            if key == 'date':
                w = DateEntry(parent, dateformat='%Y-%m-%d')
                self.vars[key] = w
            elif key == 'product':
                w = Combobox(parent, state='readonly')
                self.vars[key] = w
            elif key == 'is_active':
                var = IntVar(value=1)
                w = Checkbutton(parent, variable=var, bootstyle="success")
                self.vars[key] = var
            else:
                w = Entry(parent)
                self.vars[key] = w
            w.pack(fill='x', pady=2)

        btn_frame = Frame(self.sales_tab)
        Button(btn_frame, text="Add Sale",
               bootstyle="primary", command=self.add_sale)\
            .pack(side='left', padx=5)

        if self.is_admin:
            self.update_btn = Button(
                btn_frame, text="Update Sale",
                bootstyle="warning", command=self.update_sale
            )
            self.update_btn.pack(side='left', padx=5)
            self.update_btn.state(['disabled'])

        Button(btn_frame, text="Export PDF",
               bootstyle="success", command=self.export_pdf)\
            .pack(side='left', padx=5)

        btn_frame.pack(pady=5)

    def _make_tree(self, parent):
        cols = ["ID", "Receipt No", "Date", "Product", "Qty"]
        if self.is_admin:
            cols.append("Cost")
        cols += ["Total", "Notes", "Created At", "Updated At", "Active"]

        self.tree = Treeview(parent, columns=cols,
                             show='headings', bootstyle="secondary")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center')

        vsb = Scrollbar(parent, orient='vertical', command=self.tree.yview)
        hsb = Scrollbar(parent, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())

    def _reset_and_reload(self):
        self.search_var.set('')
        self.start_date.entry.delete(0, 'end')
        self.end_date.entry.delete(0, 'end')
        self.filter_active_var.set('All')
        if self.is_admin:
            self.update_btn.state(['disabled'])
        self.load_sales()

    def load_sales(self):
        if self.is_admin:
            self.update_btn.state(['disabled'])

        prods = get_connection().execute(
            'SELECT id, name FROM products'
        ).fetchall()
        self.vars['product']['values'] = [
            f"{pid}: {name}" for pid, name in prods
        ]

        for r in self.tree.get_children():
            self.tree.delete(r)

        term = f"%{self.search_var.get().strip()}%"
        start = self.start_date.entry.get().strip()
        end   = self.end_date.entry.get().strip()
        active_filter = self.filter_active_var.get()

        where = ["p.name LIKE ?"]
        params = [term]

        if start and end:
            where += ["s.date BETWEEN ? AND ?"]
            params += [start, end]
        elif start:
            where += ["s.date >= ?"]
            params += [start]
        elif end:
            where += ["s.date <= ?"]
            params += [end]

        if active_filter == 'Active':
            where += ["s.is_active = 1"]
        elif active_filter == 'Inactive':
            where += ["s.is_active = 0"]

        cols = ["s.id", "s.receipt_no", "s.date", "p.name", "s.qty"]
        if self.is_admin:
            cols.append("p.cost_price")
        cols += [
            "(s.qty * p.price) AS total",
            "s.notes", "s.created_at", "s.updated_at", "s.is_active"
        ]

        sql = f"""
            SELECT {', '.join(cols)}
              FROM sales s
              JOIN products p ON s.prod_id = p.id
             WHERE {' AND '.join(where)}
          ORDER BY s.date DESC
        """

        with get_connection() as conn:
            for row in conn.execute(sql, params):
                vals = list(row)
                vals[-1] = "Yes" if vals[-1] else "No"
                self.tree.insert('', 'end', values=vals)

    def clear_form(self):
        for key, widget in self.vars.items():
            if key == 'is_active':
                widget.set(1)
            elif key == 'product':
                widget.set('')
            elif key == 'date':
                widget.entry.delete(0, 'end')
                widget.entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
            else:
                widget.config(state='normal')
                widget.delete(0, 'end')

    def set_form_state(self, editable: bool):
        state = 'normal' if editable else 'disabled'
        for key, widget in self.vars.items():
            try:
                if key == 'date':
                    widget.entry.config(state=state)
                else:
                    widget.config(state=state)
            except Exception:
                pass

    def on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]

        data = {
            'receipt_no': vals[1],
            'date':       vals[2],
            'product':    vals[3],
            'qty':        vals[4],
            'notes':      vals[6],
            'is_active':  1 if vals[-1] == "Yes" else 0
        }

        for key, widget in self.vars.items():
            if key == 'is_active':
                widget.set(data[key])
            elif key == 'product':
                widget.set(data[key])
            elif key == 'date':
                widget.entry.delete(0, 'end')
                widget.entry.insert(0, data[key])
            else:
                widget.config(state='normal')
                widget.delete(0, 'end')
                widget.insert(0, data[key])

        self.set_form_state(False)

        if self.is_admin:
            self.set_form_state(True)
            self.vars['product'].config(state='readonly')
            self.vars['date'].entry.config(state='disabled')
            self.update_btn.state(['!disabled'])

    def add_sale(self):
        vals = {k: (v.get() if hasattr(v, "get") else v.entry.get())
                for k, v in self.vars.items()}
        if not all([vals['receipt_no'], vals['date'], vals['product'], vals['qty']]):
            ToastNotification(
                "Error", "Receipt No, Date, Product & Qty are required"
            ).show_toast()
            return

        pid = int(vals['product'].split(':', 1)[0])
        q   = int(vals['qty'])
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with get_connection() as conn:
            conn.execute(
                'INSERT INTO sales (receipt_no, date, prod_id, qty, notes, '
                'created_at, updated_at, is_active) VALUES (?,?,?,?,?,?,?,?)',
                (vals['receipt_no'], vals['date'], pid, q,
                 vals['notes'], now, now, vals['is_active'])
            )
            conn.execute(
                'UPDATE products SET quantity = quantity - ? WHERE id = ?',
                (q, pid)
            )
            conn.commit()

        self.clear_form()
        self.load_sales()
        if self.inventory_frame:
            self.inventory_frame.load_inventory()

    def update_sale(self):
        if not self.is_admin:
            ToastNotification("Error", "Permission Denied").show_toast()
            return
        if not hasattr(self, 'current_id'):
            return

        vals = {
            'receipt_no': self.vars['receipt_no'].get(),
            'qty':        int(self.vars['qty'].get()),
            'notes':      self.vars['notes'].get(),
            'is_active':  self.vars['is_active'].get()
        }
        new_receipt = vals['receipt_no']
        new_qty     = vals['qty']
        new_notes   = vals['notes']
        new_active  = vals['is_active']
        now         = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with get_connection() as conn:
            old_qty, old_pid = conn.execute(
                'SELECT qty, prod_id FROM sales WHERE id = ?',
                (self.current_id,)
            ).fetchone()

            diff = new_qty - old_qty
            if diff != 0:
                conn.execute(
                    'UPDATE products '
                    'SET quantity = quantity - ? '
                    'WHERE id = ?',
                    (diff, old_pid)
                )

            conn.execute(
                'UPDATE sales '
                'SET receipt_no = ?, '
                    'qty        = ?, '
                    'notes      = ?, '
                    'is_active  = ?, '
                    'updated_at = ? '
                'WHERE id = ?',
                (new_receipt, new_qty, new_notes, new_active, now, self.current_id)
            )

            conn.commit()

        ToastNotification("Success", "Sale updated").show_toast()

        self.clear_form()
        self.update_btn.state(['disabled'])
        self.load_sales()
        if self.inventory_frame:
            self.inventory_frame.load_inventory()


    def delete_sale(self):
        if not self.is_admin:
            ToastNotification("Error", "Permission Denied").show_toast()
            return
        sel = self.tree.selection()
        if not sel:
            return
        sid = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute('DELETE FROM sales WHERE id = ?', (sid,))
            conn.commit()

        self.clear_form()
        self.load_sales()
        if self.inventory_frame:
            self.inventory_frame.load_inventory()

    def export_pdf(self):
        headers = [self.tree.heading(c)['text'] for c in self.tree['columns']]
        data    = [self.tree.item(i)['values'] for i in self.tree.get_children()]

        out_dir = "reports"
        os.makedirs(out_dir, exist_ok=True)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        epw = pdf.w - pdf.l_margin - pdf.r_margin
        col_w = epw / len(headers)

        for h in headers:
            pdf.cell(col_w, 10, str(h), border=1)
        pdf.ln()

        for row in data:
            for item in row:
                pdf.cell(col_w, 8, str(item), border=1)
            pdf.ln()

        fn   = f"sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(out_dir, fn)
        pdf.output(path)
        ToastNotification("Exported", f"Saved to {path}").show_toast()
