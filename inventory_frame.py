import sqlite3
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Entry, Button, Treeview, Scrollbar
from database import get_connection

class InventoryFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        Label(self, text="Inventory", font=("Helvetica", 16, "bold")).pack(pady=(0,10))

        search_frame = Frame(self)
        Label(search_frame, text="Search:").pack(side='left')
        self.search_var = tb.StringVar()
        search_entry = Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True, padx=(5,0))
        search_entry.bind("<KeyRelease>", lambda e: self.load_inventory())
        Button(search_frame, text="Refresh", bootstyle="info", command=self.load_inventory).pack(side='left', padx=5)
        search_frame.pack(fill='x', pady=5)

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True, pady=5)
        cols = ("ID", "Name", "Category", "Price", "Qty", "Damaged", "Sold")
        self.tree = Treeview(table_frame, columns=cols, show='headings', bootstyle="secondary")
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

        self.load_inventory()

    def load_inventory(self):
        term = f"%{self.search_var.get().strip()}%"
        for r in self.tree.get_children():
            self.tree.delete(r)

        query = """
            SELECT p.id, p.name, c.name AS category, p.price, p.quantity,
                   IFNULL((SELECT SUM(d.qty) FROM damage_products d WHERE d.prod_id = p.id), 0) AS damaged,
                   IFNULL((SELECT SUM(s.qty) FROM sales s WHERE s.prod_id = p.id), 0) AS sold
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.name LIKE ?
            ORDER BY p.id
        """
        with get_connection() as conn:
            for row in conn.execute(query, (term,)):
                self.tree.insert('', 'end', values=row)
