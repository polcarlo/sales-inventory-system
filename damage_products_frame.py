import sqlite3
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar, Combobox
from ttkbootstrap.widgets import DateEntry, Checkbutton
from tkinter import IntVar
from database import get_connection

class DamageProductsFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Damaged Products", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        search_frame = Frame(self)
        Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", lambda e: self.load_damage())

        Label(search_frame, text="Product:").pack(side='left', padx=(5,0))
        self.search_prod_var = tb.StringVar(value="All")
        self.search_prod_cb = Combobox(search_frame, textvariable=self.search_prod_var, state='readonly')
        self.search_prod_cb.pack(side='left', padx=(5,0))

        Label(search_frame, text="From:").pack(side='left', padx=(5,0))
        self.search_from_date = DateEntry(search_frame, dateformat='%Y-%m-%d')
        self.search_from_date.pack(side='left', padx=(5,0))
        self.search_from_date.entry.delete(0, 'end')

        Label(search_frame, text="To:").pack(side='left', padx=(5,0))
        self.search_to_date = DateEntry(search_frame, dateformat='%Y-%m-%d')
        self.search_to_date.pack(side='left', padx=(5,0))
        self.search_to_date.entry.delete(0, 'end')

        Button(search_frame, text="Filter", bootstyle="info", command=self.load_damage).pack(side='left', padx=(5,0))
        search_frame.pack(fill='x', pady=5)

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=(0,10))
        cols = ("ID", "Product", "Date", "Qty", "Reason", "Created At", "Updated At", "Active")
        self.tree = Treeview(table_frame, columns=cols, show='headings', bootstyle="table")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center')
        v_scroll = Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        h_scroll = Scrollbar(table_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())

        form = Frame(self)
        form.pack(fill='x', pady=(0,10))
        left = Frame(form)
        left.pack(side='left', fill='both', expand=True, padx=(0,5))
        right = Frame(form)
        right.pack(side='left', fill='both', expand=True, padx=(5,0))

        fields = [
            ("Product", "prod_id", left),
            ("Date", "date", left),
            ("Qty", "qty", right),
            ("Reason", "reason", right),
            ("Is Active", "is_active", right),
        ]
        self.vars = {}
        for lbl, attr, parent in fields:
            Label(parent, text=lbl).pack(anchor='w', pady=2)
            if attr == "prod_id":
                cb = Combobox(parent, state='readonly')
                cb.pack(fill='x', pady=2)
                self.vars[attr] = cb
            elif attr == "date":
                de = DateEntry(parent, dateformat='%Y-%m-%d')
                de.pack(fill='x', pady=2)
                self.vars[attr] = de
            elif attr == "is_active":
                var = IntVar(value=1)
                chk = Checkbutton(parent, variable=var, bootstyle="success")
                chk.pack(fill='x', pady=2)
                self.vars[attr] = var
            else:
                ent = Entry(parent)
                ent.pack(fill='x', pady=2)
                self.vars[attr] = ent

        btn_frame = Frame(self)
        Button(btn_frame, text="Add", bootstyle="primary", command=self.add_damage).pack(side='left', padx=5)
        Button(btn_frame, text="Update", bootstyle="warning", command=self.update_damage).pack(side='left', padx=5)
        Button(btn_frame, text="Refresh", bootstyle="info", command=self.load_damage).pack(side='left', padx=5)
        btn_frame.pack(pady=5)

        self.load_damage()

    def load_damage(self):
        prods = [(r[0], r[1]) for r in get_connection().execute('SELECT id, name FROM products')]
        names = [n for _, n in prods]
        self.vars['prod_id']['values'] = names
        self.search_prod_cb['values'] = ['All'] + names

        for r in self.tree.get_children():
            self.tree.delete(r)

        query = """
            SELECT d.id, p.name, d.date, d.qty, d.reason, d.created_at, d.updated_at, d.is_active
            FROM damage_products d
            JOIN products p ON d.prod_id = p.id
            WHERE 1=1
        """
        params = []

        term = self.search_var.get().strip()
        if term:
            query += " AND (p.name LIKE ? OR d.reason LIKE ?)"
            like_term = f"%{term}%"
            params.extend([like_term, like_term])

        prod = self.search_prod_var.get()
        if prod and prod != "All":
            query += " AND p.name = ?"
            params.append(prod)

        from_date = self.search_from_date.entry.get().strip()
        if from_date:
            query += " AND d.date >= ?"
            params.append(from_date)

        to_date = self.search_to_date.entry.get().strip()
        if to_date:
            query += " AND d.date <= ?"
            params.append(to_date)

        query += " ORDER BY d.id"

        with get_connection() as conn:
            for row in conn.execute(query, params):
                row = list(row)
                row[-1] = "Yes" if row[-1] else "No"
                self.tree.insert('', 'end', values=row)

    def clear_form(self):
        for attr, widget in self.vars.items():
            if attr == "is_active":
                widget.set(1)
            elif attr == "prod_id":
                widget.set("")
            elif attr == "date":
                widget.entry.delete(0, 'end')
                widget.entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
            else:
                widget.delete(0, 'end')

    def on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]
        data = {
            "prod_id": vals[1],
            "date": vals[2],
            "qty": vals[3],
            "reason": vals[4],
            "is_active": 1 if vals[7] == "Yes" else 0
        }
        for attr, widget in self.vars.items():
            if attr == "is_active":
                widget.set(data[attr])
            elif attr == "prod_id":
                widget.set(data[attr])
            elif attr == "date":
                widget.entry.delete(0, 'end')
                widget.entry.insert(0, data[attr])
            else:
                widget.delete(0, 'end')
                widget.insert(0, data[attr])

    def add_damage(self):
        prod_name = self.vars['prod_id'].get().strip()
        date_val = self.vars['date'].entry.get().strip()
        qty = self.vars['qty'].get().strip()
        reason = self.vars['reason'].get().strip()
        active = self.vars['is_active'].get()
        if not (prod_name and date_val and qty and reason):
            tb.toast.ToastNotification("Error", "All fields required").show_toast()
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_connection() as conn:
            pid = conn.execute('SELECT id FROM products WHERE name=?', (prod_name,)).fetchone()[0]
            conn.execute(
                'INSERT INTO damage_products(prod_id, date, qty, reason, created_at, updated_at, is_active) VALUES(?,?,?,?,?,?,?)',
                (pid, date_val, int(qty), reason, now, now, active)
            )
            conn.commit()
        self.clear_form()
        self.load_damage()

    def update_damage(self):
        if not hasattr(self, 'current_id'):
            return
        prod_name = self.vars['prod_id'].get().strip()
        date_val = self.vars['date'].entry.get().strip()
        qty = self.vars['qty'].get().strip()
        reason = self.vars['reason'].get().strip()
        active = self.vars['is_active'].get()
        if not (prod_name and date_val and qty and reason):
            tb.toast.ToastNotification("Error", "All fields required").show_toast()
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_connection() as conn:
            pid = conn.execute('SELECT id FROM products WHERE name=?', (prod_name,)).fetchone()[0]
            conn.execute(
                'UPDATE damage_products SET prod_id=?, date=?, qty=?, reason=?, updated_at=?, is_active=? WHERE id=?',
                (pid, date_val, int(qty), reason, now, active, self.current_id)
            )
            conn.commit()
        self.clear_form()
        self.load_damage()

    def delete_damage(self):
        sel = self.tree.selection()
        if not sel:
            return
        did = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute('DELETE FROM damage_products WHERE id=?', (did,))
            conn.commit()
        self.clear_form()
        self.load_damage()
