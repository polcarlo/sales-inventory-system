import ttkbootstrap as tb
from ttkbootstrap import Frame
from login_frame import LoginFrame
from register_frame import RegisterFrame
from menu_frame import MenuFrame
from users_frame import UsersFrame
from categories_frame import CategoriesFrame
from products_frame import ProductsFrame
from department_frame import DepartmentFrame
from suppliers_frame import SuppliersFrame
from expenses_frame import ExpensesFrame
from debt_tracker_frame import DebtTrackerFrame
from inventory_frame import InventoryFrame
from sales_frame import SalesFrame
from damage_products_frame import DamageProductsFrame
from warehouse_frame import WarehouseFrame
from dashboard_frame import DashboardFrame

class App:
    def __init__(self):
        style = tb.Style(theme='flatly')
        self.root = style.master
        self.root.title("Inventory System")
        try:
            self.root.state('zoomed')   
        except:
            self.root.attributes('-fullscreen', True) 
        self.container = Frame(self.root)
        self.container.pack(fill='both', expand=True)
        self._show_login()

    def _clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def _show_login(self):
        self._clear()
        LoginFrame(
            self.container,
            on_success=self._on_login,
            on_register=self._show_register
        ).pack(fill='both', expand=True)

    def _show_register(self):
        self._clear()
        RegisterFrame(
            self.container,
            on_success=self._show_login,
            on_back=self._show_login
        ).pack(fill='both', expand=True)

    def _on_login(self, first, last, username, role):
        self.current_user = username
        self.current_user_role = role
        self._build_main()

    def _build_main(self):
        self._clear()
        menu = MenuFrame(self.container, {
            'dashboard':      self._show_dashboard,
            'users':          self._show_users,
            'categories':     self._show_categories,
            'products':       self._show_products,
            'department':     self._show_department,
            'suppliers':      self._show_suppliers,
            'expenses':       self._show_expenses,
            'debtTracker':    self._show_debt_tracker,
            'inventory':      self._show_inventory,
            'sales':          self._show_sales,
            'damageProduct':  self._show_damage_product,
            'warehouse':      self._show_warehouse,
            'logout':         self._show_login,
        })
        menu.pack(side='left', fill='y')
        self.content = Frame(self.container)
        self.content.pack(side='right', fill='both', expand=True)
        self._show_dashboard()

    def _show_users(self):
        self._swap_content(UsersFrame, current_user_role=self.current_user_role)

    def _show_dashboard(self):
        self._swap_content(DashboardFrame)

    def _show_warehouse(self):
        self._swap_content(WarehouseFrame)

    def _show_inventory(self):
        self._swap_content(InventoryFrame)

    def _show_sales(self):
        self._swap_content(SalesFrame, current_user_role=self.current_user_role)

    def _show_damage_product(self):
        self._swap_content(DamageProductsFrame)

    def _show_categories(self):
        self._swap_content(CategoriesFrame)

    def _show_products(self):
        self._swap_content(ProductsFrame)

    def _show_department(self):
        self._swap_content(DepartmentFrame)

    def _show_suppliers(self):
        self._swap_content(SuppliersFrame)

    def _show_expenses(self):
        self._swap_content(ExpensesFrame)

    def _show_debt_tracker(self):
        self._swap_content(DebtTrackerFrame)

    def _swap_content(self, FrameClass, *args, **kwargs):
        for w in self.content.winfo_children():
            w.destroy()
        FrameClass(self.content, *args, **kwargs).pack(fill='both', expand=True)

    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    App().run()
