import os
import sqlite3
from datetime import datetime

import ttkbootstrap as tb
from ttkbootstrap import Frame, Label, Combobox, Button, Treeview, Scrollbar

from database import get_connection
from fpdf import FPDF

class ReportFrame(Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        self._build_report_tab()
        self._load_report_years()

    def _build_report_tab(self):
        controls = Frame(self)
        controls.pack(fill='x', pady=(0,10))

        Label(controls, text="Year:").pack(side='left')
        self.year_var = tb.StringVar()
        self.year_cb = Combobox(controls, textvariable=self.year_var, state='readonly')
        self.year_cb.pack(side='left', padx=(5,15))

        Label(controls, text="Month:").pack(side='left')
        self.month_var = tb.StringVar(value='All')
        self.month_cb = Combobox(
            controls,
            textvariable=self.month_var,
            state='readonly',
            values=['All'] + [f'{i:02d}' for i in range(1,13)]
        )
        self.month_cb.pack(side='left', padx=(5,15))

        Button(
            controls, text="Generate Report",
            bootstyle="success", command=self.generate_report
        ).pack(side='left')
        Button(
            controls, text="Export PDF",
            bootstyle="info", command=self.export_report_pdf
        ).pack(side='left', padx=(10,0))

        table_frame = Frame(self)
        table_frame.pack(fill='both', expand=True)
        cols = ("Product","Total Qty","Total Cost","Total Sales")
        self.report_tree = Treeview(
            table_frame,
            columns=cols,
            show='headings',
            bootstyle="info"
        )
        for c in cols:
            self.report_tree.heading(c, text=c)
            self.report_tree.column(c, anchor='center')

        v_scroll = Scrollbar(table_frame, orient='vertical', command=self.report_tree.yview)
        h_scroll = Scrollbar(table_frame, orient='horizontal', command=self.report_tree.xview)
        self.report_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.report_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def _load_report_years(self):
        with get_connection() as conn:
            years = [r[0] for r in conn.execute(
                "SELECT DISTINCT strftime('%Y', date) FROM sales ORDER BY 1 DESC"
            )]
        self.year_cb['values'] = years
        if years:
            self.year_cb.set(years[0])

    def generate_report(self):
        year = self.year_var.get()
        month = self.month_var.get()
        if not year:
            tb.toast.ToastNotification("Error","Please select a year").show_toast()
            return

        if month != 'All':
            sql = """
                SELECT
                  p.name AS product,
                  SUM(s.qty) AS total_qty,
                  SUM(s.qty * p.cost_price) AS total_cost,
                  SUM(s.qty * p.price) AS total_sales
                FROM sales s
                JOIN products p ON s.prod_id = p.id
                WHERE strftime('%Y', s.date)=?
                  AND strftime('%m', s.date)=?
                  AND p.is_active = 1
                  AND s.is_active = 1
                GROUP BY p.name
                ORDER BY p.name
            """
            params = [year, month]
        else:
            sql = """
                SELECT
                  p.name AS product,
                  SUM(s.qty) AS total_qty,
                  SUM(s.qty * p.cost_price) AS total_cost,
                  SUM(s.qty * p.price) AS total_sales
                FROM sales s
                JOIN products p ON s.prod_id = p.id
                WHERE strftime('%Y', s.date)=?
                  AND p.is_active = 1
                  AND s.is_active = 1
                GROUP BY p.name
                ORDER BY p.name
            """
            params = [year]

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        if rows:
            for prod, qty, cost, sales in rows:
                self.report_tree.insert(
                    '', 'end',
                    values=(prod, qty or 0, f"{(cost or 0):.2f}", f"{(sales or 0):.2f}")
                )
        else:
            tb.toast.ToastNotification("Info","No active data for that period").show_toast()

    def export_report_pdf(self):
        year = self.year_var.get()
        month = self.month_var.get()
        if not year:
            tb.toast.ToastNotification("Error","Please select a year").show_toast()
            return

        items = self.report_tree.get_children()
        if not items:
            tb.toast.ToastNotification("Error","No data to export").show_toast()
            return

        folder = "reports"
        os.makedirs(folder, exist_ok=True)
        m_lbl = month if month!='All' else 'all'
        fname = f"sales_report_{year}_{m_lbl}.pdf"
        path = os.path.join(folder, fname)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        title = f"Sales Report for {year}" + (f"-{month}" if month!='All' else "")
        pdf.cell(0, 10, title, ln=1)
        pdf.ln(5)

        pdf.set_font("Arial", "B", 12)
        headers = ["Product","Total Qty","Total Cost","Total Sales"]
        widths = [70,30,30,30]
        for w,h in zip(widths, headers):
            pdf.cell(w, 10, h, border=1)
        pdf.ln()

        pdf.set_font("Arial","",12)
        for itm in items:
            prod, qty, cost, sales = self.report_tree.item(itm)['values']
            for w, v in zip(widths, [prod, qty, cost, sales]):
                pdf.cell(w, 10, str(v), border=1)
            pdf.ln()

        pdf.output(path)
        tb.toast.ToastNotification("Success", f"Exported to {path}").show_toast()
