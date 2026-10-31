"""
Unit tests for Day 5: Pandas Analytics Engine, Business KPIs,
Department Distributions, Sales Trends, and CSV Reports.
"""
import io
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db
from app.models import User, Product, Sale
from app.analytics import AnalyticsEngine

try:
    import flask
    from app import create_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestDay5Analytics(unittest.TestCase):
    def setUp(self):
        self.test_db = Path(__file__).resolve().parent / "test_analytics.db"
        if self.test_db.exists():
            os.remove(self.test_db)
        init_db(self.test_db)

        # 1. Create test users
        self.admin = User.create("admin_analytics", "adminpass", "admin", db_path=self.test_db)
        self.cashier = User.create("cashier_analytics", "cashpass", "cashier", db_path=self.test_db)

        # 2. Create products across 2 categories
        # Dairy
        self.p1 = Product.create("Whole Milk 1L", "Dairy", 3.50, 20, 10, "2026-12-01", db_path=self.test_db)
        self.p2 = Product.create("Cheddar Cheese", "Dairy", 5.00, 4, 10, "2026-11-05", db_path=self.test_db)

        # Produce
        self.p3 = Product.create("Organic Apples 1kg", "Produce", 4.00, 30, 15, "2026-12-10", db_path=self.test_db)
        self.p4 = Product.create("Bananas 1kg", "Produce", 2.00, 2, 5, "2026-11-02", db_path=self.test_db)

        # 3. Process controlled sales across different dates
        # Sale 1: 2026-10-01 (Dairy: 2 * 3.50 = 7.00, discount 0.0) -> $7.00
        Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[{"product_id": self.p1, "quantity": 2}],
            discount=0.0,
            sale_date="2026-10-01",
            sale_time="10:00:00",
            db_path=self.test_db
        )

        # Sale 2: 2026-10-15 (Produce: 5 * 4.00 = 20.00, discount 2.00) -> $18.00
        Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[{"product_id": self.p3, "quantity": 5}],
            discount=2.00,
            sale_date="2026-10-15",
            sale_time="14:30:00",
            db_path=self.test_db
        )

        # Sale 3: 2026-10-20 (Produce: 2 * 2.00 = 4.00, Dairy: 1 * 5.00 = 5.00) -> $9.00
        Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[
                {"product_id": self.p4, "quantity": 2},
                {"product_id": self.p2, "quantity": 1}
            ],
            discount=0.0,
            sale_date="2026-10-20",
            sale_time="16:45:00",
            db_path=self.test_db
        )

        # Total revenue: 7.00 + 18.00 + 9.00 = 34.00 across 3 bills

        if FLASK_AVAILABLE:
            class TestConfig:
                TESTING = True
                SECRET_KEY = "test-secret"
                DATABASE_PATH = self.test_db

            self.app = create_app(TestConfig)
            self.client = self.app.test_client()

    def tearDown(self):
        if hasattr(self, "test_db") and self.test_db.exists():
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def login_admin(self):
        return self.client.post("/auth/login", data={
            "username": "admin_analytics",
            "password": "adminpass"
        }, follow_redirects=True)

    def login_cashier(self):
        return self.client.post("/auth/login", data={
            "username": "cashier_analytics",
            "password": "cashpass"
        }, follow_redirects=True)

    def test_01_kpi_computation_accuracy(self):
        """Calculates 5 KPIs: Total Revenue, Avg Bill, Stock Turnover, Low Stock, and Top Category."""
        kpis = AnalyticsEngine.get_kpis(db_path=self.test_db)

        self.assertEqual(kpis["total_revenue"], 34.00)
        self.assertEqual(kpis["total_bills"], 3)
        self.assertAlmostEqual(kpis["avg_bill_value"], round(34.00 / 3, 2), places=2)
        self.assertEqual(kpis["low_stock_count"], 2)
        self.assertEqual(kpis["top_category_name"], "Produce")
        self.assertAlmostEqual(kpis["top_category_revenue"], 24.00, places=2)
        self.assertAlmostEqual(kpis["top_category_share"], 70.6, places=1)

    def test_02_kpi_date_filtering(self):
        """Filters analytics metrics within specific date windows."""
        kpis = AnalyticsEngine.get_kpis(start_date="2026-10-10", end_date="2026-10-16", db_path=self.test_db)
        self.assertEqual(kpis["total_revenue"], 18.00)
        self.assertEqual(kpis["total_bills"], 1)
        self.assertEqual(kpis["avg_bill_value"], 18.00)

    def test_03_zero_sales_handling(self):
        """Handles dates with no sales gracefully without ZeroDivisionError."""
        kpis = AnalyticsEngine.get_kpis(start_date="2025-01-01", end_date="2025-01-02", db_path=self.test_db)
        self.assertEqual(kpis["total_revenue"], 0.0)
        self.assertEqual(kpis["total_bills"], 0)
        self.assertEqual(kpis["avg_bill_value"], 0.0)
        self.assertEqual(kpis["top_category_name"], "N/A")
        self.assertEqual(kpis["top_category_share"], 0.0)

    def test_04_category_breakdown_aggregations(self):
        """Computes revenue distribution by category."""
        breakdown = AnalyticsEngine.get_category_breakdown(db_path=self.test_db)
        self.assertEqual(len(breakdown), 2)
        self.assertEqual(breakdown[0]["category"], "Produce")
        self.assertEqual(breakdown[0]["revenue"], 24.00)
        self.assertEqual(breakdown[0]["quantity_sold"], 7)
        self.assertEqual(breakdown[1]["category"], "Dairy")
        self.assertEqual(breakdown[1]["revenue"], 12.00)
        self.assertEqual(breakdown[1]["quantity_sold"], 3)

    def test_05_top_products_ranking(self):
        """Ranks top products by revenue and quantity."""
        top_by_rev = AnalyticsEngine.get_top_products(sort_by="revenue", db_path=self.test_db)
        self.assertEqual(top_by_rev[0]["name"], "Organic Apples 1kg")
        self.assertEqual(top_by_rev[0]["total_revenue"], 20.00)

        top_by_qty = AnalyticsEngine.get_top_products(sort_by="quantity", db_path=self.test_db)
        self.assertEqual(top_by_qty[0]["name"], "Organic Apples 1kg")
        self.assertEqual(top_by_qty[0]["total_qty"], 5)

    def test_06_slow_moving_products_identification(self):
        """Identifies products with low or zero velocity."""
        slow = AnalyticsEngine.get_slow_moving_products(limit=5, db_path=self.test_db)
        self.assertGreater(len(slow), 0)
        units_sold_list = [s["units_sold"] for s in slow]
        self.assertEqual(units_sold_list, sorted(units_sold_list))

    def test_07_analytics_page_admin_access(self):
        """Admin can load the analytics reports hub."""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not installed in test runner environment.")

        self.login_admin()
        res = self.client.get("/reports/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Executive Analytics &amp; Reports", res.data)
        self.assertIn(b"TOTAL REVENUE", res.data)
        self.assertIn(b"STOCK TURNOVER", res.data)

    def test_08_cashier_denied_access_to_analytics(self):
        """Cashiers cannot view executive sales analytics."""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not installed in test runner environment.")

        self.login_cashier()
        res = self.client.get("/reports/", follow_redirects=True)
        self.assertIn(b"Admin privileges required", res.data)

    def test_09_analytics_api_summary_json(self):
        """JSON summary API returns structured dataset for Chart.js."""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not installed in test runner environment.")

        self.login_admin()
        res = self.client.get("/reports/api/summary")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/json")
        data = json.loads(res.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("kpis", data)
        self.assertIn("sales_trend", data)
        self.assertIn("category_breakdown", data)

    def test_10_csv_report_export(self):
        """Downloads analytics reports in standard CSV format."""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not installed in test runner environment.")

        self.login_admin()

        # Daily sales CSV
        res_daily = self.client.get("/reports/export/daily_sales")
        self.assertEqual(res_daily.status_code, 200)
        self.assertEqual(res_daily.mimetype, "text/csv")
        self.assertIn(b"Total Revenue ($)", res_daily.data)

        # Category performance CSV
        res_cat = self.client.get("/reports/export/categories")
        self.assertEqual(res_cat.status_code, 200)
        self.assertEqual(res_cat.mimetype, "text/csv")
        self.assertIn(b"Revenue Share (%)", res_cat.data)


if __name__ == "__main__":
    unittest.main()