"""
Pandas-powered Analytics and KPI Computation Engine for GreenLeaf Grocers.
Computes business metrics, sales aggregations, category distributions,
and inventory velocity from SQLite database records.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from app.database import get_db_connection


class AnalyticsEngine:
    """Core data science and metrics engine backed by Pandas DataFrames."""

    @staticmethod
    def _build_date_filter(start_date: Optional[str] = None, end_date: Optional[str] = None) -> tuple[str, list]:
        """Constructs an SQL WHERE clause and parameter list for date filtering."""
        clauses = []
        params = []
        if start_date:
            clauses.append("sale_date >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("sale_date <= ?")
            params.append(end_date)

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where_sql, params

    @classmethod
    def get_kpis(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        db_path: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Calculates the 5 essential Business Key Performance Indicators:
        1. Total Revenue: Sum of final sales amounts in period
        2. Average Bill Value: Total revenue / total count of bills
        3. Stock Turnover Ratio: Total sales revenue / Current inventory valuation
        4. Low-Stock Items Count: Products at or below their reorder threshold
        5. Top Category Share (%): Contribution percentage of the highest grossing category
        """
        conn = get_db_connection(db_path)
        try:
            where_sql, params = cls._build_date_filter(start_date, end_date)

            # 1 & 2. Sales & Bill Value metrics
            sales_query = f"SELECT sale_id, final_amount, discount, sale_date FROM sales {where_sql}"
            sales_df = pd.read_sql_query(sales_query, conn, params=params)

            if sales_df.empty:
                total_revenue = 0.0
                total_bills = 0
                avg_bill_value = 0.0
                total_discounts = 0.0
            else:
                total_revenue = round(float(sales_df["final_amount"].sum()), 2)
                total_bills = int(len(sales_df))
                avg_bill_value = round(total_revenue / total_bills, 2) if total_bills > 0 else 0.0
                total_discounts = round(float(sales_df["discount"].sum()), 2)

            # 3 & 4. Inventory Valuation and Low-Stock count
            prods_df = pd.read_sql_query(
                "SELECT product_id, name, category, unit_price, stock_qty, reorder_level, expiry_date FROM products",
                conn
            )

            if prods_df.empty:
                inventory_valuation = 0.0
                stock_turnover = 0.0
                low_stock_count = 0
                near_expiry_count = 0
            else:
                prods_df["inventory_value"] = prods_df["unit_price"] * prods_df["stock_qty"]
                inventory_valuation = round(float(prods_df["inventory_value"].sum()), 2)

                # Stock turnover: Revenue generated divided by current inventory asset value
                if inventory_valuation > 0 and total_revenue > 0:
                    stock_turnover = round(total_revenue / inventory_valuation, 2)
                else:
                    stock_turnover = 0.0

                low_stock_count = int((prods_df["stock_qty"] <= prods_df["reorder_level"]).sum())

                # Near expiry (within 15 days from today)
                today = pd.to_datetime(datetime.now().date())
                prods_df["expiry_dt"] = pd.to_datetime(prods_df["expiry_date"], errors="coerce")
                days_diff = (prods_df["expiry_dt"] - today).dt.days
                near_expiry_count = int(((days_diff >= 0) & (days_diff <= 15)).sum())

            # 5. Top Category Share (%)
            cat_query = f"""
                SELECT p.category, SUM(si.quantity * si.price) as revenue
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                JOIN sales s ON si.sale_id = s.sale_id
                {where_sql}
                GROUP BY p.category
                ORDER BY revenue DESC
            """
            cat_df = pd.read_sql_query(cat_query, conn, params=params)

            if cat_df.empty or total_revenue <= 0:
                top_category_name = "N/A"
                top_category_revenue = 0.0
                top_category_share = 0.0
            else:
                top_row = cat_df.iloc[0]
                top_category_name = str(top_row["category"])
                top_category_revenue = round(float(top_row["revenue"]), 2)
                top_category_share = round((top_category_revenue / total_revenue) * 100, 1)

            return {
                "total_revenue": total_revenue,
                "total_bills": total_bills,
                "avg_bill_value": avg_bill_value,
                "total_discounts": total_discounts,
                "inventory_valuation": inventory_valuation,
                "stock_turnover": stock_turnover,
                "low_stock_count": low_stock_count,
                "near_expiry_count": near_expiry_count,
                "top_category_name": top_category_name,
                "top_category_revenue": top_category_revenue,
                "top_category_share": top_category_share,
                "start_date": start_date or "",
                "end_date": end_date or ""
            }
        finally:
            conn.close()

    @classmethod
    def get_sales_trend(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        db_path: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Computes daily timeline of revenue, transaction count, and average order value."""
        conn = get_db_connection(db_path)
        try:
            where_sql, params = cls._build_date_filter(start_date, end_date)
            query = f"""
                SELECT sale_date, final_amount, total_amount, discount
                FROM sales
                {where_sql}
                ORDER BY sale_date ASC
            """
            df = pd.read_sql_query(query, conn, params=params)
            if df.empty:
                return []

            grouped = df.groupby("sale_date").agg(
                revenue=("final_amount", "sum"),
                bills_count=("final_amount", "count"),
                discounts=("discount", "sum")
            ).reset_index()

            grouped["revenue"] = grouped["revenue"].round(2)
            grouped["discounts"] = grouped["discounts"].round(2)
            grouped["avg_ticket"] = (grouped["revenue"] / grouped["bills_count"]).round(2)

            return grouped.to_dict(orient="records")
        finally:
            conn.close()

    @classmethod
    def get_category_breakdown(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        db_path: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Computes revenue, total units sold, and contribution % for each grocery department."""
        conn = get_db_connection(db_path)
        try:
            where_sql, params = cls._build_date_filter(start_date, end_date)
            query = f"""
                SELECT p.category, si.quantity, (si.quantity * si.price) as item_revenue
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                JOIN sales s ON si.sale_id = s.sale_id
                {where_sql}
            """
            df = pd.read_sql_query(query, conn, params=params)
            if df.empty:
                return []

            grouped = df.groupby("category").agg(
                revenue=("item_revenue", "sum"),
                quantity_sold=("quantity", "sum")
            ).reset_index()

            total_cat_rev = grouped["revenue"].sum()
            grouped["share_pct"] = (
                (grouped["revenue"] / total_cat_rev * 100).round(1) if total_cat_rev > 0 else 0.0
            )
            grouped["revenue"] = grouped["revenue"].round(2)
            grouped = grouped.sort_values(by="revenue", ascending=False)

            return grouped.to_dict(orient="records")
        finally:
            conn.close()

    @classmethod
    def get_top_products(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        sort_by: str = "revenue",
        db_path: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Returns top performing products ranked by revenue or by physical quantity sold."""
        conn = get_db_connection(db_path)
        try:
            where_sql, params = cls._build_date_filter(start_date, end_date)
            query = f"""
                SELECT p.product_id, p.name, p.category, p.unit_price,
                       si.quantity, (si.quantity * si.price) as line_revenue
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                JOIN sales s ON si.sale_id = s.sale_id
                {where_sql}
            """
            df = pd.read_sql_query(query, conn, params=params)
            if df.empty:
                return []

            grouped = df.groupby(["product_id", "name", "category", "unit_price"]).agg(
                total_qty=("quantity", "sum"),
                total_revenue=("line_revenue", "sum")
            ).reset_index()

            grouped["total_revenue"] = grouped["total_revenue"].round(2)
            order_col = "total_revenue" if sort_by == "revenue" else "total_qty"
            sorted_df = grouped.sort_values(by=order_col, ascending=False).head(limit)

            return sorted_df.to_dict(orient="records")
        finally:
            conn.close()

    @classmethod
    def get_slow_moving_products(
        cls,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        db_path: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Identifies idle or low-velocity stock items with lowest sales to mitigate inventory holding costs."""
        conn = get_db_connection(db_path)
        try:
            where_sql, params = cls._build_date_filter(start_date, end_date)
            query = f"""
                SELECT p.product_id, p.name, p.category, p.unit_price, p.stock_qty,
                       COALESCE(SUM(si.quantity), 0) as units_sold,
                       COALESCE(SUM(si.quantity * si.price), 0.0) as revenue_generated
                FROM products p
                LEFT JOIN (
                    SELECT si.product_id, si.quantity, si.price
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.sale_id
                    {where_sql}
                ) si ON p.product_id = si.product_id
                GROUP BY p.product_id
                ORDER BY units_sold ASC, p.stock_qty DESC
                LIMIT ?
            """
            all_params = params + [limit]
            df = pd.read_sql_query(query, conn, params=all_params)
            if df.empty:
                return []

            df["revenue_generated"] = df["revenue_generated"].round(2)
            df["stock_valuation"] = (df["unit_price"] * df["stock_qty"]).round(2)
            return df.to_dict(orient="records")
        finally:
            conn.close()