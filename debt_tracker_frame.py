import sqlite3
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar, Combobox
from ttkbootstrap.widgets import DateEntry, Checkbutton
from tkinter import IntVar
from database import get_connection

class DebtTrackerFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)

        Label(self, text="Debt Tracker", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        filter_frame = Frame(self)
        Label(filter_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(filter_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", lambda e: self.load())

        Label(filter_frame, text="Due Date:").pack(side='left', padx=(10,0))
        de = DateEntry(filter_frame, dateformat='%Y-%m-%d')
        de.pack(side='left', padx=(5,0))
        de.entry.delete(0, 'end') 
        de.bind("<<DateEntrySelected>>", lambda e: self.load())
        self.due_date_filter = de

        Label(filter_frame, text="Active:").pack(side='left', padx=(10,0))
        self.active_filter = tb.StringVar(value="All")
        active_cb = Combobox(
            filter_frame,
            textvariable=self.active_filter,
            state='readonly',
            values=["All", "Active", "Inactive"]
        )
        active_cb.pack(side='left', padx=(5,0))
        active_cb.bind("<<ComboboxSelected>>", lambda e: self.load())

        filter_frame.pack(fill='x', pady=(0,10))

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=(0,10))
        cols = ("ID","Name","Amount","Due Date","Status","Created At","Updated At","Active")
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
        left = Frame(form);  left.pack(side='left', fill='both', expand=True, padx=(0,5))
        right = Frame(form); right.pack(side='left', fill='both', expand=True, padx=(5,0))

        fields = [
            ("Name","name", left),
            ("Amount","amount", left),
            ("Due Date","due_date", right),
            ("Status","status", right),
            ("Is Active","is_active", right)
        ]
        self.vars = {}
        for lbl, attr, parent in fields:
            Label(parent, text=lbl).pack(anchor='w', pady=2)
            if attr == "due_date":
                w = DateEntry(parent, dateformat='%Y-%m-%d')
                w.pack(fill='x', pady=2)
                self.vars[attr] = w
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
        Button(btn_frame, text="Add",    bootstyle="primary", command=self.add_debt).pack(side='left', padx=5)
        Button(btn_frame, text="Update", bootstyle="warning", command=self.update_debt).pack(side='left', padx=5)
        btn_frame.pack(pady=5)

        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        name_term = f"%{self.search_var.get().strip()}%"
        due_val  = self.due_date_filter.entry.get().strip()
        active   = self.active_filter.get()

        query = (
            "SELECT id, name, amount, due_date, status, created_at, updated_at, is_active "
            "FROM debts WHERE (name LIKE ? OR status LIKE ?)"
        )
        params = [name_term, name_term]

        if due_val:
            query += " AND due_date = ?"
            params.append(due_val)
        if active != "All":
            query += " AND is_active = ?"
            params.append(1 if active=="Active" else 0)

        query += " ORDER BY due_date"

        with get_connection() as conn:
            for row in conn.execute(query, params):
                row = list(row)
                row[-1] = "Yes" if row[-1] else "No"
                self.tree.insert('', 'end', values=row)

    def clear_form(self):
        for attr, w in self.vars.items():
            if attr == 'is_active':
                w.set(1)
            elif attr == 'due_date':
                w.entry.delete(0,'end')
                w.entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
            else:
                w.config(state='normal')
                w.delete(0,'end')

    def on_select(self):
        sel = self.tree.selection()
        if not sel: return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]
        data = {
            'name': vals[1],
            'amount': vals[2],
            'due_date': vals[3],
            'status': vals[4],
            'is_active': 1 if vals[7]=="Yes" else 0
        }
        for attr, w in self.vars.items():
            if attr == 'is_active':
                w.set(data[attr])
            elif attr == 'due_date':
                w.entry.delete(0,'end')
                w.entry.insert(0, data[attr])
            else:
                w.config(state='normal')
                w.delete(0,'end')
                w.insert(0, data[attr])

    def add_debt(self):
        v = {k: (w.get() if hasattr(w, 'get') else w.entry.get()) for k,w in self.vars.items()}
        if not all([v['name'], v['amount'], v['due_date'], v['status']]):
            tb.toast.ToastNotification("Error","All fields required").show_toast()
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_connection() as conn:
            conn.execute(
                'INSERT INTO debts(name, amount, due_date, status, created_at, updated_at, is_active) VALUES(?,?,?,?,?,?,?)',
                (v['name'], float(v['amount']), v['due_date'], v['status'], now, now, self.vars['is_active'].get())
            )
            conn.commit()
        self.clear_form()
        self.load()

    def update_debt(self):
        if not hasattr(self, 'current_id'): return
        v = {k: (w.get() if hasattr(w, 'get') else w.entry.get()) for k,w in self.vars.items()}
        if not all([v['name'], v['amount'], v['due_date'], v['status']]):
            tb.toast.ToastNotification("Error","All fields required").show_toast()
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with get_connection() as conn:
            conn.execute(
                'UPDATE debts SET name=?, amount=?, due_date=?, status=?, updated_at=?, is_active=? WHERE id=?',
                (v['name'], float(v['amount']), v['due_date'], v['status'], now, self.vars['is_active'].get(), self.current_id)
            )
            conn.commit()
        self.clear_form()
        self.load()
