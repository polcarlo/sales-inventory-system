import sqlite3
from datetime import datetime
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar
from ttkbootstrap.widgets import Checkbutton
from tkinter import IntVar
from database import get_connection

class SuppliersFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Suppliers", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        search_frame = Frame(self)
        Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", lambda e: self.load())
        search_frame.pack(fill='x', pady=(0,10))

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=(0,10))
        cols = ("ID","Name","Contact","Phone","Email","Address","Created At","Updated At","Active")
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
        left = Frame(form);   left.pack(side='left', fill='both', expand=True, padx=(0,5))
        right = Frame(form);  right.pack(side='left', fill='both', expand=True, padx=(5,0))

        fields = [
            ("Name","name", left),
            ("Contact Person","contact", left),
            ("Phone","phone", left),
            ("Email","email", right),
            ("Address","address", right),
            ("Is Active","is_active", right),
        ]
        self.vars = {}
        for lbl_text, attr, parent in fields:
            Label(parent, text=lbl_text).pack(anchor='w', pady=2)
            if attr == "is_active":
                var = IntVar(value=1)
                Checkbutton(parent, variable=var, bootstyle="success").pack(fill='x', pady=2)
                self.vars[attr] = var
            else:
                ent = Entry(parent)
                ent.pack(fill='x', pady=2)
                if attr in ("created_at","updated_at"):
                    ent.state(['readonly'])
                self.vars[attr] = ent

        btn_frame = Frame(self)
        Button(btn_frame, text="Add",    bootstyle="primary", command=self.add_supplier).pack(side='left', padx=5)
        Button(btn_frame, text="Update", bootstyle="warning", command=self.update_supplier).pack(side='left', padx=5)
        Button(btn_frame, text="Refresh",bootstyle="info",    command=self.load).pack(side='left', padx=5)
        btn_frame.pack(pady=5)

        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        query = """
            SELECT id,name,contact,phone,email,address,created_at,updated_at,is_active
              FROM suppliers
        """
        term = self.search_var.get().strip()
        params = ()
        if term:
            query += " WHERE name LIKE ? OR contact LIKE ? OR phone LIKE ? OR email LIKE ?"
            like = f"%{term}%"
            params = (like, like, like, like)
        with get_connection() as conn:
            for row in conn.execute(query, params):
                row = list(row)
                row[-1] = "Yes" if row[-1] else "No"
                self.tree.insert('', 'end', values=row)

    def clear_form(self):
        for attr, widget in self.vars.items():
            if attr == "is_active":
                widget.set(1)
            else:
                widget.config(state='normal')
                widget.delete(0, 'end')
                if attr in ("created_at","updated_at"):
                    widget.state(['readonly'])

    def on_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        self.current_id = vals[0]
        data = {
            "name":(vals[1]), "contact":vals[2], "phone":vals[3],
            "email":vals[4], "address":vals[5],
            "created_at":vals[6], "updated_at":vals[7],
            "is_active":(1 if vals[8]=="Yes" else 0)
        }
        for attr, widget in self.vars.items():
            if attr == "is_active":
                widget.set(data[attr])
            else:
                widget.config(state='normal')
                widget.delete(0,'end')
                widget.insert(0, data[attr])
                if attr in ("created_at","updated_at"):
                    widget.state(['readonly'])

    def add_supplier(self):
        vals = {attr:(w.get().strip() if attr!="is_active" else w.get())
                for attr,w in self.vars.items()}
        if not all(vals[a] for a in ("name","contact","phone","email","address")):
            tb.toast.ToastNotification("Error","All fields required").show_toast()
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with get_connection() as conn:
                conn.execute(
                    '''INSERT INTO suppliers
                          (name,contact,phone,email,address,created_at,updated_at,is_active)
                       VALUES(?,?,?,?,?,?,?,?)''',
                    (vals["name"], vals["contact"], vals["phone"], vals["email"],
                     vals["address"], now, now, vals["is_active"])
                )
                conn.commit()
        except sqlite3.IntegrityError:
            tb.toast.ToastNotification(
                "Error",
                f"A supplier named '{vals['name']}' already exists."
            ).show_toast()
            return

        self.clear_form()
        self.load()

    def update_supplier(self):
        if not hasattr(self, 'current_id'):
            tb.toast.ToastNotification("Error","No supplier selected").show_toast()
            return
        vals = {attr:(w.get().strip() if attr!="is_active" else w.get())
                for attr,w in self.vars.items()}
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with get_connection() as conn:
                conn.execute(
                    '''UPDATE suppliers
                        SET name=?,contact=?,phone=?,email=?,address=?,
                            updated_at=?,is_active=?
                        WHERE id=?''',
                    (vals["name"], vals["contact"], vals["phone"], vals["email"],
                     vals["address"], now, vals["is_active"], self.current_id)
                )
                conn.commit()
        except sqlite3.IntegrityError:
            tb.toast.ToastNotification(
                "Error",
                f"A supplier named '{vals['name']}' already exists."
            ).show_toast()
            return

        self.clear_form()
        self.load()

    def delete_supplier(self):
        sel = self.tree.selection()
        if not sel:
            return
        sid = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute('DELETE FROM suppliers WHERE id=?',(sid,))
            conn.commit()
        self.clear_form()
        self.load()
