import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button
from ttkbootstrap.toast import ToastNotification
from auth import register_user

class RegisterFrame(Frame):
    def __init__(self, master, on_success, on_back):
        super().__init__(master)
        self.on_success = on_success
        self.on_back = on_back
        self.sales_color = '#28A745'  

        self.canvas = tb.Canvas(self, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', self._on_resize)

        self.panel = Frame(
            self.canvas,
            padding=30,
            borderwidth=2,
            relief='groove'
        )
        self.window = self.canvas.create_window(0, 0, window=self.panel)

        self._build()

    def _on_resize(self, event):
        w, h = event.width, event.height
        self.canvas.delete('bg')
        self.canvas.create_rectangle(0, 0, w, h * 0.6,
                                     fill='#f0f4f8', tags='bg', outline='')
        self.canvas.create_rectangle(0, h * 0.6, w, h,
                                     fill='#e2e8f0', tags='bg', outline='')
        pw, ph = w * 0.4, h * 0.7
        self.canvas.coords(self.window, w / 2, h / 2)
        self.canvas.itemconfig(self.window, width=pw, height=ph)

    def _clear(self):
        for widget in self.panel.winfo_children():
            widget.destroy()

    def _build(self):
        self._clear()
        Label(
            self.panel,
            text='REGISTER',
            font=('Exo 2', 32, 'bold'),
            foreground=self.sales_color
        ).pack(pady=(0, 20))

        self._build_field('First Name', 'first')
        self._build_field('Last Name', 'last')
        self._build_field('Username', 'user')
        self._build_field('Password', 'pass', show='*')

        Button(
            self.panel,
            text='Submit',
            bootstyle='primary',
            command=self._do_register
        ).pack(fill='x', pady=(20, 10))

        Button(
            self.panel,
            text='Back to Login',
            bootstyle='light',
            command=self.on_back
        ).pack(fill='x')

    def _build_field(self, label_text, attr, show=None):
        Label(
            self.panel,
            text=label_text,
            font=('Segoe UI', 10)
        ).pack(anchor='w', pady=(10, 2))
        entry = Entry(
            self.panel,
            bootstyle='default',
            show=show,
            font=('Segoe UI', 12)
        )
        entry.pack(fill='x')
        setattr(self, f'{attr}_entry', entry)

    def _do_register(self):
        ok = register_user(
            self.first_entry.get(),
            self.last_entry.get(),
            self.user_entry.get(),
            self.pass_entry.get()
        )
        if ok:
            ToastNotification(
                title='Success',
                message='Registered! You can now log in.',
                bootstyle='success'
            ).show_toast()
            self.on_success()
        else:
            ToastNotification(
                title='Error',
                message='Username already exists',
                bootstyle='warning'
            ).show_toast()

if __name__ == '__main__':
    root = tb.Window(themename='flatly')
    root.title('Register • 2100')
    root.geometry('1200x800')
    root.minsize(600, 400)

    def on_success():
        print('Registration complete, switch to login')

    def on_back():
        print('Back to login')

    RegisterFrame(root, on_success, on_back).pack(fill='both', expand=True)
    root.mainloop()
