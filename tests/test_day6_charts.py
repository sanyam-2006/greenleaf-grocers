"""
Unit tests for Day 6: Interactive Dashboard Visualizations with Chart.js,
Dynamic View Toggles, Multi-Series Charts, and Reporting APIs.
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db
from app.models import User, Product, Sale

try:
    import flask
    from app import create_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestDay6Charts(unittest.TestCase):
    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask is not installed in the current environment.")

        self.test_db = Path(__file__).resolve().parent / "test_day6_charts.db"
        if self.test_db.exists():
            os.remove(self.test_db)
        init_db(self.test_db)

        # 1. Create test users
        self.admin = User.create("admin_charts", "adminpass", "admin", db_path=self.test_db)
        self.cashier = User.create("cashier_charts", "cashpass", "cashier", db_path=self.test_db)

        # 2. Create products
        # Product 1: High price, low volume ($10.00 each)
        self.p1 = Product.create("Premium Olive Oil", "Pantry", 10.00, 50, 10, "2026-12-01", db_path=self.test_db)
        # Product 2: Low price, high volume ($1.00 each)
        self.p2 = Product.create("Sparkling Water", "Beverages", 1.00, 100, 20, "2026-11-20", db_path=self.test_db)

        # 3. Create transactions
        # Sale 1: 2 units of Olive Oil = $20.00
        Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[{"product_id": self.p1, "quantity": 2}],
            discount=0.0,
            sale_date="2026-10-10",
            sale_time="10:00:00",
            db_path=self.test_db
        )
        # Sale 2: 15 units of Sparkling Water = $15.00
        Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[{"product_id": self.p2, "quantity": 15}],
            discount=0.0,
            sale_date="2026-10-15",
            sale_time="12:00:00",
            db_path=self.test_db
        )

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
            "username": "admin_charts",
            "password": "adminpass"
        }, follow_redirects=True)

    def login_cashier(self):
        return self.client.post("/auth/login", data={
            "username": "cashier_charts",
            "password": "cashpass"
        }, follow_redirects=True)

    def test_01_reports_renders_all_chart_canvases(self):
        """Reports page contains canvas elements for all 3 primary Chart.js charts."""
        self.login_admin()
        res = self.client.get("/reports/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="salesTrendChart"', res.data)
        self.assertIn(b'id="categoryChart"', res.data)
        self.assertIn(b'id="topProductsChart"', res.data)

    def test_02_reports_has_interactive_view_toggle(self):
        """Reports page includes interactive toggles for Revenue vs Quantity views."""
        self.login_admin()
        res = self.client.get("/reports/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="btnViewRevenue"', res.data)
        self.assertIn(b'id="btnViewQuantity"', res.data)
        self.assertIn(b"switchProductChartView", res.data)

    def test_03_dashboard_renders_preview_charts(self):
        """Executive dashboard renders quick overview charts for trend and departments."""
        self.login_admin()
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'id="dashTrendChart"', res.data)
        self.assertIn(b'id="dashCategoryChart"', res.data)

    def test_04_api_summary_returns_chart_ready_payloads(self):
        """API summary provides structured series for Chart.js rendering."""
        self.login_admin()
        res = self.client.get("/reports/api/summary")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/json")
        data = json.loads(res.data)

        self.assertEqual(data["status"], "success")
        self.assertIn("sales_trend", data)
        self.assertIn("category_breakdown", data)
        self.assertIn("top_products_revenue", data)
        self.assertIn("top_products_quantity", data)
        self.assertEqual(len(data["sales_trend"]), 2)

    def test_05_date_filter_applied_to_charts(self):
        """Applying start_date and end_date filters reduces data points in charts."""
        self.login_admin()
        res = self.client.get("/reports/?start_date=2026-10-14&end_date=2026-10-16")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"1 Data Points", res.data)

    def test_06_top_products_revenue_vs_quantity_sorting(self):
        """Validates that Revenue view ranks by dollars, while Quantity view ranks by units."""
        self.login_admin()
        res = self.client.get("/reports/api/summary")
        data = json.loads(res.data)

        # Olive Oil earned $20 (rank 1 by revenue), Water earned $15 (rank 2)
        self.assertEqual(data["top_products_revenue"][0]["name"], "Premium Olive Oil")
        self.assertEqual(data["top_products_revenue"][0]["total_revenue"], 20.00)

        # Water sold 15 units (rank 1 by quantity), Olive Oil sold 2 units (rank 2)
        self.assertEqual(data["top_products_quantity"][0]["name"], "Sparkling Water")
        self.assertEqual(data["top_products_quantity"][0]["total_qty"], 15)

    def test_07_chartjs_script_included(self):
        """Chart.js library is loaded in base layout."""
        self.login_admin()
        res = self.client.get("/reports/")
        self.assertIn(b"chart.umd.min.js", res.data)

    def test_08_cashier_restricted_from_charts(self):
        """Cashiers cannot view reports or call chart data API."""
        self.login_cashier()

        # HTML reports page
        res_page = self.client.get("/reports/", follow_redirects=True)
        self.assertIn(b"Admin privileges required", res_page.data)

        # JSON data API
        res_api = self.client.get("/reports/api/summary", follow_redirects=True)
        self.assertIn(b"Admin privileges required", res_api.data)

    def test_09_unauthenticated_user_redirected(self):
        """Anonymous user is redirected to login."""
        res = self.client.get("/reports/")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/auth/login", res.headers["Location"])

    def test_10_empty_database_graceful_chart_rendering(self):
        """Page and charts render cleanly when date window has zero sales."""
        self.login_admin()
        res = self.client.get("/reports/?start_date=2024-01-01&end_date=2024-01-02")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"0 Data Points", res.data)
        self.assertIn(b"$0.00", res.data)


if __name__ == "__main__":
    unittest.main()