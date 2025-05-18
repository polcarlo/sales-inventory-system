import sqlite3
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar, Combobox
from ttkbootstrap.widgets import DateEntry, Checkbutton
from tkinter import IntVar
from database import get_connection


class ExpensesFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Track Expenses", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        search_frame = Frame(self)
        Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", lambda e: self.load())
        search_frame.pack(fill='x', pady=(0,10))

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=(0,10))
        cols = ("ID", "Date", "Department", "Description", "Amount", "Created At", "Updated At", "Active")
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

        self.error_var = tb.StringVar()
        self.error_label = Label(self, textvariable=self.error_var, foreground="red")
        self.error_label.pack(fill='x', pady=(0,5))

        form = Frame(self)
        form.pack(fill='x', pady=(0,10))
        left = Frame(form)
        left.pack(side='left', fill='both', expand=True, padx=(0,5))
        right = Frame(form)
        right.pack(side='left', fill='both', expand=True, padx=(5,0))

        fields = [
            ("Date", "date", left),
            ("Department", "department", left),
            ("Description", "description", right),
            ("Amount", "amount", right),
            ("Is Active", "is_active", right),
        ]
        self.vars = {}
        for lbl, attr, parent in fields:
            Label(parent, text=lbl).pack(anchor='w', pady=2)
            if attr == "date":
                de = DateEntry(parent, dateformat='%Y-%m-%d')
                de.pack(fill='x', pady=2)
                self.vars[attr] = de
            elif attr == "department":
                cb = Combobox(parent, state='readonly')
                cb.pack(fill='x', pady=2)
                self.vars[attr] = cb
            elif attr == "is_active":
                var = IntVar(value=1)
                chk = Checkbutton(parent, variable=var, bootstyle="success")
                chk.pack(fill='x', pady=2)
                self.vars[attr] = var
            else:
                ent = Entry(parent)
                ent.pack(fill='x', pady=2)
                if attr in ("created_at", "updated_at"):
                    ent.state(['readonly'])
                self.vars[attr] = ent

        btn_frame = Frame(self)
        Button(btn_frame, text="Add", bootstyle="primary", command=self.add_expense).pack(side='left', padx=5)
        Button(btn_frame, text="Update", bootstyle="warning", command=self.update_expense).pack(side='left', padx=5)
        Button(btn_frame, text="Refresh", bootstyle="info", command=self.load).pack(side='left', padx=5)
        btn_frame.pack(pady=5)

        self.load()

    def load(self):
        self.error_var.set("")
        depts = [(r[0], r[1]) for r in get_connection().execute('SELECT id, name FROM departments')]
        self.vars['department']['values'] = [n for _, n in depts]
        for r in self.tree.get_children():
            self.tree.delete(r)
        query = 'SELECT id, date, department_id, description, amount, created_at, updated_at, is_active FROM expenses'
        term = self.search_var.get().strip()
        params = ()
        if term:
            query += ' WHERE date LIKE ? OR description LIKE ?'
            like = f"%{term}%"
            params = (like, like)
        with get_connection() as conn:
            for row in conn.execute(query, params):
                row = list(row)
                row[2] = next((n for i, n in depts if i == row[2]), "")
                row[-1] = "Yes" if row[-1] else "No"
                self.tree.insert('', 'end', values=row)

    def clear_form(self):
        self.error_var.set("")
        for attr, widget in self.vars.items():
            if attr == "is_active":
                widget.set(1)
            elif attr == "department":
                widget.set("")
            elif attr == "date":
                widget.entry.delete(0, 'end')
                widget.entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
            else:
                widget.config(state='normal')
                widget.delete(0, 'end')
                if attr in ("created_at", "updated_at"):
                    widget.state(['readonly'])

    def on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]
        data = {"date": vals[1], "department": vals[2], "description": vals[3], "amount": vals[4],
                "created_at": vals[5], "updated_at": vals[6], "is_active": 1 if vals[7] == "Yes" else 0}
        for attr, widget in self.vars.items():
            if attr == "is_active":
                widget.set(data[attr])
            elif attr == "department":
                widget.set(data[attr])
            elif attr == "date":
                widget.entry.delete(0, 'end')
                widget.entry.insert(0, data[attr])
            else:
                widget.config(state='normal')
                widget.delete(0, 'end')
                widget.insert(0, data[attr])
                if attr in ("created_at", "updated_at"):
                    widget.state(['readonly'])

    def add_expense(self):
        self.error_var.set("")
        date_val = self.vars['date'].entry.get().strip()
        vals = {attr: (self.vars[attr].get().strip() if attr not in ('date','is_active') else self.vars[attr].get())
                for attr in ('department','description','amount','is_active')}
        vals['date'] = date_val
        if not all(vals[a] for a in ('date','department','description','amount')):
            self.error_var.set("All fields required.")
            return
        try:
            amt = float(vals['amount'])
        except ValueError:
            self.error_var.set("Amount must be a valid number.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            dept_row = conn.execute('SELECT id FROM departments WHERE name=?', (vals['department'],)).fetchone()
            if not dept_row:
                self.error_var.set("Selected department not found.")
                return
            dept_id = dept_row[0]
            conn.execute(
                'INSERT INTO expenses(date, department_id, description, amount, created_at, updated_at, is_active) VALUES(?,?,?,?,?,?,?)',
                (vals['date'], dept_id, vals['description'], amt, now, now, int(vals['is_active']))
            )
            conn.commit()
        self.clear_form()
        self.load()

    def update_expense(self):
        if not hasattr(self, 'current_id'):
            self.error_var.set("No record selected to update.")
            return
        self.error_var.set("")
        date_val = self.vars['date'].entry.get().strip()
        vals = {attr: (self.vars[attr].get().strip() if attr not in ('date','is_active') else self.vars[attr].get())
                for attr in ('department','description','amount','is_active')}
        vals['date'] = date_val
        if not all(vals[a] for a in ('date','department','description','amount')):
            self.error_var.set("All fields required.")
            return
        try:
            amt = float(vals['amount'])
        except ValueError:
            self.error_var.set("Amount must be a valid number.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            dept_row = conn.execute('SELECT id FROM departments WHERE name=?', (vals['department'],)).fetchone()
            if not dept_row:
                self.error_var.set("Selected department not found.")
                return
            dept_id = dept_row[0]
            conn.execute(
                'UPDATE expenses SET date=?, department_id=?, description=?, amount=?, updated_at=?, is_active=? WHERE id=?',
                (vals['date'], dept_id, vals['description'], amt, now, int(vals['is_active']), self.current_id)
            )
            conn.commit()
        self.clear_form()
        self.load()

    def delete_expense(self):
        sel = self.tree.selection()
        if not sel:
            self.error_var.set("Select a record to delete.")
            return
        eid = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute('DELETE FROM expenses WHERE id=?', (eid,))
            conn.commit()
        self.clear_form()
        self.load()