import sqlite3
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Checkbutton
from ttkbootstrap.toast import ToastNotification
from database import get_connection
from datetime import datetime

class DepartmentFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        Label(self, text="Departments", font=("Helvetica", 18, "bold")).pack(pady=10)
        
        search_frame = Frame(self)
        search_frame.pack(fill='x', pady=(0,10))
        Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_var.trace_add('write', lambda *_: self.load())

        cols = ("ID", "Name", "Created At", "Updated At", "Active")
        self.tree = Treeview(self, columns=cols, show='headings', bootstyle="table")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        form_frame = Frame(self)
        form_frame.pack(fill='x', pady=10)
        Label(form_frame, text="Name").grid(row=0, column=0, sticky='w')
        self.name = Entry(form_frame)
        self.name.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        Label(form_frame, text="Active").grid(row=3, column=0, sticky='w')
        self.is_active_var = tb.IntVar(value=1)
        self.active_cb = Checkbutton(form_frame, variable=self.is_active_var)
        self.active_cb.grid(row=3, column=1, sticky='w', padx=5, pady=2)
        form_frame.columnconfigure(1, weight=1)

        btn_frame = Frame(self)
        btn_frame.pack(fill='x')
        self.add_btn = Button(btn_frame, text="Add", bootstyle="success", command=self.add_dept)
        self.add_btn.pack(side='left', padx=5)
        self.update_btn = Button(btn_frame, text="Update", bootstyle="primary", command=self.update_dept, state='disabled')
        self.update_btn.pack(side='left', padx=5)
        Button(btn_frame, text="Refresh", command=self.load).pack(side='left', padx=5)

        self.load()

    def load(self):
        query = "SELECT id,name,created_at,updated_at,is_active FROM departments WHERE name LIKE ? ORDER BY name"
        search = f"%{self.search_var.get().strip()}%"
        for row in self.tree.get_children():
            self.tree.delete(row)
        with get_connection() as conn:
            for dept in conn.execute(query, (search,)):
                did, name, created, updated, active = dept
                active_text = "Yes" if active else "No"
                self.tree.insert('', 'end', values=(did, name, created, updated, active_text))
        self.clear_form()

    def clear_form(self):
        self.name.delete(0, 'end')
        self.is_active_var.set(1)
        self.update_btn.config(state='disabled')
        self.add_btn.config(state='normal')

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        did, name, created, updated, active_text = self.tree.item(sel[0])['values']
        self.selected_id = did
        self.name.delete(0, 'end')
        self.name.insert(0, name)
        self.created_at.config(state='normal'); self.created_at.delete(0,'end'); self.created_at.insert(0, created); self.created_at.config(state='readonly')
        self.updated_at.config(state='normal'); self.updated_at.delete(0,'end'); self.updated_at.insert(0, updated); self.updated_at.config(state='readonly')
        self.is_active_var.set(1 if active_text == "Yes" else 0)
        self.update_btn.config(state='normal')
        self.delete_btn.config(state='normal')
        self.add_btn.config(state='disabled')

    def add_dept(self):
        name = self.name.get().strip()
        if not name:
            ToastNotification("Error", "Name required").show_toast()
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO departments(name,created_at,updated_at,is_active) VALUES(?,?,?,?)",
                    (name, now, now, self.is_active_var.get())
                )
                conn.commit()
                ToastNotification("Success", "Department added").show_toast()
                self.load()
            except sqlite3.IntegrityError:
                ToastNotification("Error", "Department exists").show_toast()

    def update_dept(self):
        if not hasattr(self, 'selected_id'):
            return
        name = self.name.get().strip()
        if not name:
            ToastNotification("Error", "Name required").show_toast()
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            conn.execute(
                "UPDATE departments SET name=?,updated_at=?,is_active=? WHERE id=?",
                (name, now, self.is_active_var.get(), self.selected_id)
            )
            conn.commit()
            ToastNotification("Success", "Department updated").show_toast()
            self.load()

    def delete_dept(self):
        sel = self.tree.selection()
        if not sel:
            return
        did = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute("DELETE FROM departments WHERE id=?", (did,))
            conn.commit()
        ToastNotification("Success", "Department deleted").show_toast()
        self.load()