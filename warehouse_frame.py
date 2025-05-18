import sqlite3
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar
from ttkbootstrap.widgets import Checkbutton
from tkinter import IntVar
from database import get_connection

class WarehouseFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Warehouses", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        search_frame = Frame(self)
        Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", lambda e: self.load_warehouses())
        Button(search_frame, text="Refresh", bootstyle="info", command=self.load_warehouses).pack(side='left', padx=5)
        search_frame.pack(fill='x', pady=(0,10))

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=(0,10))
        cols = ("ID","Name","Location","Capacity","Created At","Updated At","Active")
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
            ("Name","name", left),
            ("Location","location", left),
            ("Capacity","capacity", right),
            ("Is Active","is_active", right)
        ]
        self.vars = {}
        for lbl, attr, parent in fields:
            Label(parent, text=lbl).pack(anchor='w', pady=2)
            if attr == 'is_active':
                var = IntVar(value=1)
                chk = Checkbutton(parent, variable=var, bootstyle="success")
                chk.pack(fill='x', pady=2)
                self.vars[attr] = var
            else:
                ent = Entry(parent)
                ent.pack(fill='x', pady=2)
                if attr in ('created_at','updated_at'):
                    ent.state(['readonly'])
                self.vars[attr] = ent

        btn_frame = Frame(self)
        Button(btn_frame, text="Add", bootstyle="primary", command=self.add_warehouse).pack(side='left', padx=5)
        Button(btn_frame, text="Update", bootstyle="warning", command=self.update_warehouse).pack(side='left', padx=5)
        Button(btn_frame, text="Refresh", bootstyle="info", command=self.load_warehouses).pack(side='left', padx=5)
        btn_frame.pack(pady=5)

        self.load_warehouses()

    def load_warehouses(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        term = f"%{self.search_var.get().strip()}%"
        query = (
            "SELECT id, name, location, capacity, created_at, updated_at, is_active "
            "FROM warehouses WHERE name LIKE ? OR location LIKE ? ORDER BY id"
        )
        with get_connection() as conn:
            for row in conn.execute(query, (term, term)):
                r = list(row)
                r[-1] = 'Yes' if r[-1] else 'No'
                self.tree.insert('', 'end', values=r)

    def clear_form(self):
        for attr, widget in self.vars.items():
            if attr == 'is_active':
                widget.set(1)
            else:
                widget.config(state='normal')
                widget.delete(0,'end')
                if attr in ('created_at','updated_at'):
                    widget.state(['readonly'])

    def on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]
        data = {
            'name': vals[1],
            'location': vals[2],
            'capacity': vals[3],
            'created_at': vals[4],
            'updated_at': vals[5],
            'is_active': 1 if vals[6]=='Yes' else 0
        }
        for attr, widget in self.vars.items():
            if attr == 'is_active':
                widget.set(data[attr])
            else:
                widget.config(state='normal')
                widget.delete(0,'end')
                widget.insert(0, data[attr])
                if attr in ('created_at','updated_at'):
                    widget.state(['readonly'])

    def add_warehouse(self):
        name = self.vars['name'].get().strip()
        loc = self.vars['location'].get().strip()
        cap = self.vars['capacity'].get().strip()
        active = self.vars['is_active'].get()
        if not (name and loc and cap):
            tb.toast.ToastNotification("Error", "All fields required").show_toast()
            return

        try:
            cap_int = int(cap)
        except ValueError:
            tb.toast.ToastNotification("Error", "Capacity must be a valid integer").show_toast()
            return

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_connection() as conn:
            conn.execute(
                'INSERT INTO warehouses(name, location, capacity, created_at, updated_at, is_active) '
                'VALUES(?,?,?,?,?,?)',
                (name, loc, cap_int, now, now, active)
            )
            conn.commit()
        self.clear_form()
        self.load_warehouses()

    def update_warehouse(self):
        if not hasattr(self, 'current_id'):
            return
        name = self.vars['name'].get().strip()
        loc = self.vars['location'].get().strip()
        cap = self.vars['capacity'].get().strip()
        active = self.vars['is_active'].get()
        if not (name and loc and cap):
            tb.toast.ToastNotification("Error", "All fields required").show_toast()
            return

        try:
            cap_int = int(cap)
        except ValueError:
            tb.toast.ToastNotification("Error", "Capacity must be a valid integer").show_toast()
            return

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_connection() as conn:
            conn.execute(
                'UPDATE warehouses SET name=?, location=?, capacity=?, updated_at=?, is_active=? '
                'WHERE id=?',
                (name, loc, cap_int, now, active, self.current_id)
            )
            conn.commit()
        self.clear_form()
        self.load_warehouses()
