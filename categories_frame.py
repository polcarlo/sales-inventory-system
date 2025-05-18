import sqlite3
import datetime
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Checkbutton
from database import get_connection

class CategoriesFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Categories", font=("Helvetica", 16, "bold")).pack(pady=5)

        search_frame = Frame(self)
        Label(search_frame, text="Search:", font=("Helvetica", 12)).pack(side='left')
        self.search_var = tb.StringVar()
        self.search_var.trace_add('write', lambda *args: self.load())
        Entry(search_frame, textvariable=self.search_var, bootstyle="primary").pack(
            side='left', fill='x', expand=True, padx=5
        )
        search_frame.pack(fill='x', pady=5)

        cols = ("ID", "Name", "Active", "Created At", "Updated At")
        self.tree = Treeview(self, columns=cols, show='headings', bootstyle="table")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor='center')
        self.tree.pack(fill='both', expand=True, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        form = Frame(self, padding=10)
        Label(form, text="Name:", font=("Helvetica", 12)).grid(row=0, column=0, sticky='w')
        self.name_var = tb.StringVar()
        Entry(form, textvariable=self.name_var, bootstyle="secondary").grid(
            row=0, column=1, sticky='ew', padx=5
        )
        Label(form, text="Active:", font=("Helvetica", 12)).grid(row=1, column=0, sticky='w')
        self.active_var = tb.IntVar(value=1)
        Checkbutton(form, variable=self.active_var, bootstyle="success-switch").grid(
            row=1, column=1, sticky='w', padx=5
        )
        form.columnconfigure(1, weight=1)

        self.add_btn = Button(form, text="Add Category", bootstyle="success", command=self.add_cat)
        self.add_btn.grid(row=2, column=0, columnspan=2, pady=(10,5), sticky='ew')
        self.update_btn = Button(form, text="Update Category", bootstyle="primary",
                                  command=self.update_cat, state='disabled')
        self.update_btn.grid(row=3, column=0, columnspan=2, pady=5, sticky='ew')
        form.pack(fill='x', pady=10)

        self.selected_id = None
        self.load()

    def load(self):
        filter_text = self.search_var.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)

        query = 'SELECT id, name, is_active, created_at, updated_at FROM categories'
        params = []
        if filter_text:
            query += ' WHERE name LIKE ?'
            params.append(f'%{filter_text}%')
        query += ' ORDER BY name'

        with get_connection() as conn:
            for cid, name, active, created, updated in conn.execute(query, params):
                active_label = 'Yes' if active else 'No'
                self.tree.insert('', 'end', values=(cid, name, active_label, created, updated))

    def add_cat(self):
        name = self.name_var.get().strip()
        active = self.active_var.get()
        if not name:
            tb.toast.ToastNotification("Error", "Name is required").show_toast()
            return
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            try:
                conn.execute(
                    'INSERT INTO categories(name, is_active, created_at, updated_at) VALUES(?,?,?,?)',
                    (name, active, now, now)
                )
                conn.commit()
                self.load()
                self.clear_form()
            except sqlite3.IntegrityError:
                tb.toast.ToastNotification("Error", "Category already exists").show_toast()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            self.clear_form()
            return
        cid, name, active_label, _, _ = self.tree.item(sel[0])['values']
        self.selected_id = cid
        self.name_var.set(name)
        self.active_var.set(1 if active_label == 'Yes' else 0)
        self.add_btn.configure(state='disabled')
        self.update_btn.configure(state='normal')

    def update_cat(self):
        if not self.selected_id:
            return
        name = self.name_var.get().strip()
        active = self.active_var.get()
        if not name:
            tb.toast.ToastNotification("Error", "Name is required").show_toast()
            return
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with get_connection() as conn:
            try:
                conn.execute(
                    'UPDATE categories SET name=?, is_active=?, updated_at=? WHERE id=?',
                    (name, active, now, self.selected_id)
                )
                conn.commit()
                self.load()
                self.clear_form()
            except sqlite3.IntegrityError:
                tb.toast.ToastNotification("Error", "Category already exists").show_toast()

    def clear_form(self):
        self.name_var.set('')
        self.active_var.set(1)
        self.selected_id = None
        self.add_btn.configure(state='normal')
        self.update_btn.configure(state='disabled')
