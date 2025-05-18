import os
import subprocess
import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Frame
from ttkbootstrap.toast import ToastNotification

from database import create_schema, apply_migrations, DB_NAME

class MenuFrame(Frame):
    def __init__(self, master, callbacks: dict, db_path: str = None):
        style    = tb.Style()
        bg_color = style.lookup('Dark.TFrame', 'background')
        self.db_path = db_path or DB_NAME
        self.project_dir = os.path.dirname(__file__)

        super().__init__(master, padding=0, bootstyle='dark')
        self.configure(width=222)
        self.pack_propagate(False)

        inner = Frame(self, padding=20, bootstyle='dark')
        inner.pack(fill='both', expand=True)

        tk.Label(inner, text="Sales", font=("Helvetica", 14, "bold"),
                 bg=bg_color, fg='black').pack(pady=(0, 10))
        tk.Label(inner, text="Inventory System", font=("Helvetica", 14, "bold"),
                 bg=bg_color, fg='black').pack(pady=(0, 10))

        menu_items = [
            ("Dashboard",      callbacks['dashboard']),
            ("Sales",          callbacks['sales']),
            ("Expenses",       callbacks['expenses']),
            ("Inventory",      callbacks['inventory']),
            ("Damage Product", callbacks['damageProduct']),
            ("Debt Tracker",   callbacks['debtTracker']),
            ("Products",       callbacks['products']),
            ("Suppliers",      callbacks['suppliers']),
            ("Users",          callbacks['users']),
        ]
        for text, cmd in menu_items:
            tk.Button(inner, text=text, bg=bg_color, fg='black', bd=0,
                      anchor='w', command=cmd)\
              .pack(fill='x', pady=3, ipady=2)

        self._settings_expanded = False
        self._settings_btn = tk.Button(inner, text="Settings ▼",
                                       bg=bg_color, fg='black', bd=0,
                                       anchor='w', command=self._toggle_settings)
        self._settings_btn.pack(fill='x', pady=(8,3), ipady=2)

        self.settings_frame = tk.Frame(inner, bg=bg_color)
        sub_items = [
            ("Categories", callbacks['categories']),
            ("Department", callbacks['department']),
            ("Warehouse",  callbacks['warehouse']),
        ]
        for text, cmd in sub_items:
            tk.Button(self.settings_frame, text=text, bg=bg_color,
                      fg='black', bd=0, anchor='w', command=cmd)\
              .pack(fill='x', pady=1, ipady=1)

        tk.Button(inner, text="Db Update", bg=bg_color, fg='black', bd=0,
                  anchor='w', command=self._run_migration)\
          .pack(fill='x', pady=6, ipady=2)

        tk.Button(inner, text="Sync Code to GitHub", bg=bg_color, fg='black', bd=0,
                  anchor='w', command=self._sync_github)\
          .pack(fill='x', pady=6, ipady=2)

        tk.Button(inner, text="Logout", bg=bg_color, fg='black', bd=0,
                  anchor='w', command=callbacks['logout'])\
          .pack(fill='x', pady=3, ipady=2)

    def _toggle_settings(self):
        if self._settings_expanded:
            self.settings_frame.pack_forget()
            self._settings_btn.configure(text="Settings ▼")
        else:
            self.settings_frame.pack(fill='x', before=self._settings_btn)
            self._settings_btn.configure(text="Settings ▲")
        self._settings_expanded = not self._settings_expanded

    def _run_migration(self):
        migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
        if not os.path.isdir(migrations_dir):
            ToastNotification("Migration", "No database folder found; already up to date").show_toast()
            return

        files = sorted(f for f in os.listdir(migrations_dir) if f.lower().endswith('.sql'))
        if not files:
            ToastNotification("Migration", "Database already up to date").show_toast()
            return

        try:
            create_schema()
            apply_migrations(migrations_dir)
            ToastNotification("Migration", "Database migration completed successfully").show_toast()
        except Exception as e:
            ToastNotification("Migration Error", str(e)).show_toast()

    def _sync_github(self):
        commit_msg = f"UI update: {tk.datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=self.project_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=self.project_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            subprocess.run(
                ["git", "push", "origin", "main"],
                cwd=self.project_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            ToastNotification("GitHub Sync", "Code successfully pushed to GitHub").show_toast()

        except subprocess.CalledProcessError as err:
            msg = err.stderr.strip() or err.stdout.strip()
            ToastNotification("GitHub Sync Error", msg).show_toast()
        except Exception as e:
            ToastNotification("GitHub Sync Error", str(e)).show_toast()
