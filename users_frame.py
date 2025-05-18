import hashlib
import sqlite3
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Combobox, Scrollbar
from ttkbootstrap.toast import ToastNotification
from database import get_connection

class UsersFrame(Frame):
    def __init__(self, master, current_user_role):
        super().__init__(master, padding=20)
        self.current_user_role = current_user_role
        self.table_name = 'users'

        Label(self, text="Manage Users", font=("Helvetica", 18, "bold")).pack(pady=(0,10))

        search_bar = Frame(self)
        Label(search_bar, text="Search:", font=("Helvetica", 12)).pack(side='left')
        self.search_var = tb.StringVar()
        Entry(search_bar, textvariable=self.search_var).pack(side='left', fill='x', expand=True, padx=5)
        Button(search_bar, text="Go", bootstyle="primary", command=self.load_users).pack(side='left')
        search_bar.pack(fill='x', pady=(0,15))

        with get_connection() as conn:
            cols_info = conn.execute(f"PRAGMA table_info({self.table_name})").fetchall()
        phys_cols = [col[1] for col in cols_info]
        display_cols = phys_cols.copy()
        if 'created_at' not in phys_cols:
            display_cols.append('created_at')
        if 'updated_at' not in phys_cols:
            display_cols.append('updated_at')
        self.display_cols = display_cols

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=(0,15))
        self.tree = Treeview(table_frame, columns=self.display_cols, show='headings')
        for c in self.display_cols:
            self.tree.heading(c, text=c.replace('_',' ').title())
            self.tree.column(c, width=100, anchor='center')
        vsb = Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)

        form = Frame(self)
        for field in ["First Name","Last Name","Username","Password"]:
            Label(form, text=field).pack(anchor='w')
            ent = Entry(form, show="*" if field=="Password" else None)
            ent.pack(fill='x', pady=2)
            setattr(self, field.replace(" ","_").lower(), ent)
        Label(form, text="Role").pack(anchor='w')
        self.role = Combobox(form, values=['user','admin'], state='readonly')
        self.role.pack(fill='x', pady=2)
        self.is_active_var = tb.BooleanVar(value=True)
        tb.Checkbutton(form, text="Active", variable=self.is_active_var).pack(anchor='w', pady=(5,0))
        form.pack(fill='x', pady=(0,15))

        btns = Frame(self)
        Button(btns, text="Add",     bootstyle="success", command=self.add_user).pack(side='left', padx=5)
        self.update_btn = Button(btns, text="Update",  bootstyle="warning", command=self.update_user)
        self.update_btn.pack(side='left', padx=5)
        Button(btns, text="Refresh", bootstyle="secondary",command=self.load_users).pack(side='left', padx=5)
        btns.pack()

        if self.current_user_role != 'admin':
            self.update_btn.state(['disabled'])

        self.load_users()

    def load_users(self):
        term = self.search_var.get().strip()
        with get_connection() as conn:
            cols_info = conn.execute(f"PRAGMA table_info({self.table_name})").fetchall()
        phys_cols = [col[1] for col in cols_info]
        select_parts = phys_cols.copy()
        if 'created_at' in phys_cols:
            select_parts.append("COALESCE(created_at, '') as created_at")
        else:
            select_parts.append("'' as created_at")
        if 'updated_at' in phys_cols:
            select_parts.append("COALESCE(updated_at, '') as updated_at")
        else:
            select_parts.append("'' as updated_at")
        sql = f"SELECT {', '.join(select_parts)} FROM {self.table_name}"
        params = []
        if term:
            where_clauses = []
            for c in phys_cols + ['created_at','updated_at']:
                where_clauses.append(f"CAST({c} AS TEXT) LIKE ?")
                params.append(f"%{term}%")
            sql += " WHERE " + " OR ".join(where_clauses)

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        self.tree.delete(*self.tree.get_children())
        for row in rows:
            self.tree.insert('', 'end', values=row)

    def on_row_selected(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0])['values']
        mapping = dict(zip(self.display_cols, vals))
        self.first_name.delete(0,'end'); self.first_name.insert(0, mapping.get('first_name',''))
        self.last_name.delete(0,'end'); self.last_name.insert(0, mapping.get('last_name',''))
        self.username.delete(0,'end'); self.username.insert(0, mapping.get('username',''))
        self.password.delete(0,'end')
        self.role.set(mapping.get('role',''))
        self.is_active_var.set(mapping.get('is_active',1)==1)

    def add_user(self):
        fn, ln = self.first_name.get().strip(), self.last_name.get().strip()
        un, pw = self.username.get().strip(), self.password.get().strip()
        role = self.role.get(); is_active = 1 if self.is_active_var.get() else 0
        if not all([fn, ln, un, pw, role]):
            ToastNotification("Error", "All fields are required").show_toast(); return
        hashed = hashlib.sha256(pw.encode()).hexdigest()
        with get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (first_name, last_name, username, password, role, is_active) VALUES (?,?,?,?,?,?)",
                    (fn, ln, un, hashed, role, is_active)
                )
                conn.commit(); self.load_users(); ToastNotification("Success", "User added").show_toast()
            except sqlite3.IntegrityError:
                ToastNotification("Error", "Username already exists").show_toast()

    def delete_user(self):
        sel = self.tree.selection();
        if not sel: return
        uid = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute('DELETE FROM users WHERE id=?', (uid,)); conn.commit()
        self.load_users(); ToastNotification("Deleted", "User removed").show_toast()

    def update_user(self):
        sel = self.tree.selection()
        if not sel:
            ToastNotification("Error", "Select a user to update").show_toast(); return
        uid = self.tree.item(sel[0])['values'][0]
        fn, ln = self.first_name.get().strip(), self.last_name.get().strip()
        un, pw = self.username.get().strip(), self.password.get().strip()
        role = self.role.get(); is_active = 1 if self.is_active_var.get() else 0
        if not all([fn, ln, un, role]):
            ToastNotification("Error", "Fields cannot be empty").show_toast(); return
        parts = ["first_name=?", "last_name=?", "username=?", "role=?", "is_active=?"]
        params = [fn, ln, un, role, is_active]
        if pw:
            hashed = hashlib.sha256(pw.encode()).hexdigest()
            parts.insert(3, "password=?"); params.insert(3, hashed)
        parts.append("updated_at=strftime('%Y-%m-%d %H:%M:%S','now')")
        sql = f"UPDATE users SET {', '.join(parts)} WHERE id=?"
        params.append(uid)
        with get_connection() as conn:
            try:
                conn.execute(sql, params); conn.commit()
                self.load_users(); ToastNotification("Updated", "User details updated").show_toast()
                self.password.delete(0,'end')
            except sqlite3.IntegrityError:
                ToastNotification("Error", "Username conflict").show_toast()
