import sqlite3
import ttkbootstrap as tb
from ttkbootstrap import Frame, Label
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from database import get_connection

class DashboardFrame(Frame):
    LOW_STOCK_THRESHOLD = 5

    def __init__(self, master):
        super().__init__(master, padding=20)
        Label(self, text="Dashboard", font=("Helvetica", 24, "bold")).pack(pady=(0, 20))

        stats_data = [
            ("Active Products", self._get_total_products()),
            ("Total Quantity", self._get_total_quantity()),
            ("Total Sales", f"{self._get_total_sales():,.2f}"),
            ("Categories", self._get_total_categories()),
            ("Suppliers", self._get_total_suppliers()),
            ("Total Expenses", f"{self._get_total_expenses():,.2f}"),
            ("Max Inventory", self._get_top_quantity()),
            (f"Low Stock (<= {self.LOW_STOCK_THRESHOLD})", self._get_low_stock_count()),
        ]
        stats_frame = Frame(self)
        stats_frame.pack(fill='x', pady=(0, 20))

        num_cols = 4
        for idx, (title, value) in enumerate(stats_data):
            row = idx // num_cols
            col = idx % num_cols
            self._add_stat(stats_frame, title, value, row, col)

        chart_frame = Frame(self)
        chart_frame.pack(fill='both', expand=True)

        fig = Figure(figsize=(10, 4), tight_layout=True)
        ax1 = fig.add_subplot(121)
        cats, sales = self._get_sales_by_category()
        ax1.bar(cats, sales)
        ax1.set_title("Sales by Category")
        ax1.set_xlabel("Category")
        ax1.set_ylabel("Sales")
        ax1.tick_params(axis='x', rotation=45)

        ax2 = fig.add_subplot(122)
        depts, expenses = self._get_expenses_by_department()
        ax2.pie(expenses, labels=depts, autopct="%1.1f%%", startangle=140)
        ax2.set_title("Expenses by Department")

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def _add_stat(self, parent, title, value, row, col):
        card = Frame(parent, width=200, height=100, padding=15, bootstyle="primary")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        Label(card, text=title, font=("Helvetica", 12)).pack()
        Label(card, text=value, font=("Helvetica", 18, "bold")).pack()

    def _get_total_products(self):
        with get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1")
            return cur.fetchone()[0]

    def _get_total_quantity(self):
        with get_connection() as conn:
            cur = conn.execute("SELECT SUM(quantity) FROM products")
            return cur.fetchone()[0] or 0

    def _get_total_sales(self):
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT SUM(s.qty * p.price)"
                " FROM sales s JOIN products p ON s.prod_id = p.id"
            )
            return cur.fetchone()[0] or 0.0

    def _get_total_categories(self):
        with get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM categories")
            return cur.fetchone()[0]

    def _get_total_suppliers(self):
        with get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM suppliers")
            return cur.fetchone()[0]

    def _get_total_expenses(self):
        with get_connection() as conn:
            cur = conn.execute("SELECT SUM(amount) FROM expenses")
            return cur.fetchone()[0] or 0.0

    def _get_top_quantity(self):
        with get_connection() as conn:
            cur = conn.execute("SELECT MAX(quantity) FROM products")
            return cur.fetchone()[0] or 0

    def _get_low_stock_count(self):
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT COUNT(*) FROM products WHERE quantity <= ?",
                (self.LOW_STOCK_THRESHOLD,)
            )
            return cur.fetchone()[0] or 0

    def _get_sales_by_category(self):
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT c.name, SUM(s.qty * p.price)"
                " FROM sales s"
                " JOIN products p ON s.prod_id = p.id"
                " LEFT JOIN categories c ON p.category_id = c.id"
                " GROUP BY c.name"
            )
            data = cur.fetchall()
            if not data:
                return [], []
            cats, vals = zip(*data)
            return list(cats), list(vals)

    def _get_expenses_by_department(self):
        with get_connection() as conn:
            cur = conn.execute(
                "SELECT d.name, SUM(e.amount)"
                " FROM expenses e"
                " JOIN departments d ON e.department_id = d.id"
                " GROUP BY d.name"
            )
            data = cur.fetchall()
            if not data:
                return [], []
            depts, vals = zip(*data)
            return list(depts), list(vals)
