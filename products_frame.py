import sqlite3
from datetime import datetime
import os
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Combobox, StringVar
from ttkbootstrap.toast import ToastNotification
from fpdf import FPDF
from database import get_connection

class ProductsFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Manage Products", font=("Helvetica", 16)).pack(pady=5)

        search_bar = Frame(self)
        Label(search_bar, text="Search:").pack(side='left')
        self.search_var = StringVar()
        search_entry = Entry(search_bar, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.search_var.trace_add('write', lambda *args: self.load_products())
        search_bar.pack(fill='x', pady=5)

        table_frame = Frame(self)
        vsb = tb.Scrollbar(table_frame, orient='vertical')
        hsb = tb.Scrollbar(table_frame, orient='horizontal')
        self.tree = Treeview(
            table_frame,
            columns=(
                "ID", "SKU", "Name", "Description", "Category",
                "Cost", "Price", "Qty", "Warehouse",
                "Active", "Created At", "Updated At"
            ),
            show='headings',
            bootstyle="table",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        for col in self.tree['columns']:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center')
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.pack(fill='both', expand=True, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        form = Frame(self)
        fields = [
            ("SKU", 'sku'), ("Name", 'name'), ("Description", 'description'),
            ("Category", 'category'), ("Cost", 'cost_price'),
            ("Price", 'sale_price'), ("Qty", 'quantity'),
            ("Warehouse", 'warehouse'), ("Active", 'is_active')
        ]
        self.entries = {}
        for i, (label_text, key) in enumerate(fields):
            Label(form, text=label_text).grid(row=i, column=0, sticky='w', pady=2)
            if key in ('category', 'warehouse', 'is_active'):
                widget = Combobox(form, state='readonly')
                widget.grid(row=i, column=1, sticky='ew', pady=2)
            else:
                widget = Entry(form)
                widget.grid(row=i, column=1, sticky='ew', pady=2)
            self.entries[key] = widget
        form.columnconfigure(1, weight=1)
        form.pack(fill='x', pady=5)

        btns = Frame(self)
        Button(btns, text="Add/Update", bootstyle="success", command=self.add_or_update).pack(side='left', padx=5)
        Button(btns, text="Export PDF", bootstyle="info", command=self.export_pdf).pack(side='left', padx=5)
        Button(btns, text="Refresh", bootstyle="secondary", command=self.load_products).pack(side='left', padx=5)
        btns.pack(pady=5)

        self.selected_id = None
        self.load_products()

    def on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        values = self.tree.item(sel[0])['values']
        (pid, sku, name, description, category, cost_price,
         sale_price, quantity, warehouse, is_active, created_at, updated_at) = values
        self.selected_id = pid
        for key, widget in self.entries.items():
            widget.configure(state='normal')
            if isinstance(widget, Entry): widget.delete(0, 'end')
        self.entries['sku'].insert(0, sku)
        self.entries['name'].insert(0, name)
        self.entries['description'].insert(0, description)
        self.entries['category'].set(category)
        self.entries['cost_price'].insert(0, cost_price)
        self.entries['sale_price'].insert(0, sale_price)
        self.entries['quantity'].insert(0, quantity)
        self.entries['warehouse'].set(warehouse)
        self.entries['is_active'].set(is_active)

    def load_products(self):
        term = f"%{self.search_var.get().strip()}%"
        with get_connection() as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            cats = [r[1] for r in conn.execute('SELECT id,name FROM categories WHERE is_active=1')]
            whs = [r[1] for r in conn.execute('SELECT id,name FROM warehouses WHERE is_active=1')]
        self.entries['category']['values'] = cats
        self.entries['warehouse']['values'] = whs
        self.entries['is_active']['values'] = ["Yes", "No"]

        for row in self.tree.get_children():
            self.tree.delete(row)

        query = '''
            SELECT p.id,p.sku,p.name,p.description,
                   c.name,p.cost_price,p.price,p.quantity,
                   w.name,CASE p.is_active WHEN 1 THEN 'Yes' ELSE 'No' END,
                   p.created_at,p.updated_at
            FROM products p
            LEFT JOIN categories c ON p.category_id=c.id
            LEFT JOIN warehouses w ON p.warehouse_id=w.id
            WHERE (p.name LIKE ? OR p.sku LIKE ?)
        '''
        with get_connection() as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            for row in conn.execute(query, (term, term)):
                self.tree.insert('', 'end', values=row)

    def add_or_update(self):
        vals = {k: v.get().strip() for k, v in self.entries.items()}
        if not all(vals[f] for f in ['sku','name','category','cost_price','sale_price','quantity','warehouse','is_active']):
            ToastNotification(title='Error', message='All fields required').show_toast()
            return
        try:
            cost = float(vals['cost_price']); price = float(vals['sale_price']); qty = int(vals['quantity'])
        except ValueError:
            ToastNotification(title='Error', message='Cost/Price must be numeric; Qty must be integer').show_toast()
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with get_connection() as conn:
                conn.execute('PRAGMA foreign_keys = ON')
                cid = conn.execute('SELECT id FROM categories WHERE name=? AND is_active=1', (vals['category'],)).fetchone()[0]
                wid = conn.execute('SELECT id FROM warehouses WHERE name=? AND is_active=1', (vals['warehouse'],)).fetchone()[0]
                active = 1 if vals['is_active']=='Yes' else 0
                if self.selected_id:
                    conn.execute(
                        'UPDATE products SET sku=?, name=?, description=?, category_id=?, cost_price=?, price=?, quantity=?, warehouse_id=?, is_active=?, updated_at=? WHERE id=?',
                        (vals['sku'], vals['name'], vals['description'], cid, cost, price, qty, wid, active, now, self.selected_id)
                    )
                else:
                    conn.execute(
                        'INSERT INTO products (sku,name,description,category_id,cost_price,price,quantity,warehouse_id,is_active,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                        (vals['sku'], vals['name'], vals['description'], cid, cost, price, qty, wid, active, now, now)
                    )
                conn.commit()
        except sqlite3.IntegrityError as e:
            ToastNotification(title='Error', message=str(e)).show_toast()
            return
        self.load_products()

    def delete_product(self):
        sel = self.tree.selection()
        if not sel: return
        pid = self.tree.item(sel[0])['values'][0]
        with get_connection() as conn:
            conn.execute('PRAGMA foreign_keys = ON')
            conn.execute('DELETE FROM products WHERE id=?', (pid,))
            conn.commit()
        self.load_products()

    def export_pdf(self):
        items = self.tree.get_children()
        if not items:
            ToastNotification(title='Export PDF', message='No data to export').show_toast()
            return
        export_dir = os.path.join(os.getcwd(), 'exports'); os.makedirs(export_dir, exist_ok=True)
        filename = f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"; filepath = os.path.join(export_dir, filename)
        pdf = FPDF(orientation='L', unit='mm', format='A4'); pdf.set_auto_page_break(auto=True, margin=10); pdf.add_page()
        page_width = pdf.w - 2*pdf.l_margin
        pdf.set_font('Arial','B',12); pdf.cell(page_width*0.7,10,'Products', ln=False, align='L')
        pdf.set_font('Arial','',8); pdf.cell(page_width*0.3,10, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), ln=True, align='R')
        pdf.ln(2)
        pdf.set_font('Arial','B',8); pdf.set_fill_color(200,200,200)
        col_width = page_width / len(self.tree['columns'])
        for col in self.tree['columns']:
            pdf.cell(col_width,6,col, border=1, align='C', fill=True)
        pdf.ln()
        pdf.set_font('Arial','',6); fill=False
        for iid in items:
            values = self.tree.item(iid)['values']
            pdf.set_fill_color(245,245,245) if fill else pdf.set_fill_color(255,255,255)
            for v in values:
                text = str(v)
                if len(text) > int(col_width/2): text = text[:int(col_width/2)-3] + '...'
                pdf.cell(col_width,5,text, border=1, align='L', fill=fill)
            pdf.ln(); fill = not fill
        pdf.output(filepath); ToastNotification(title='Export PDF', message=f'PDF saved to {filepath}').show_toast()
