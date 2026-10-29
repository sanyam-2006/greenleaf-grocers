"""
Unit tests for Day 4: Point of Sale (POS) Billing Engine, Checkout Validation, and Receipts.
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import flask
    from app import create_app
    from app.database import init_db
    from app.models import User, Product, Sale
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestDay4Billing(unittest.TestCase):
    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask is not installed yet. Run in your active virtual environment.")

        self.test_db = Path(__file__).resolve().parent / "test_billing.db"
        if self.test_db.exists():
            os.remove(self.test_db)
        init_db(self.test_db)

        # Create test users
        User.create("admin_tester", "adminpass", "admin", db_path=self.test_db)
        self.cashier = User.create("cashier_tester", "cashierpass", "cashier", db_path=self.test_db)

        # Seed test products
        self.p1_id = Product.create("Whole Milk 1L", "Dairy", 3.50, 20, 5, "2026-12-01", db_path=self.test_db)
        self.p2_id = Product.create("Artisan Bread", "Bakery", 4.00, 10, 3, "2026-11-15", db_path=self.test_db)
        self.p3_id = Product.create("Fresh Apples 1kg", "Produce", 2.50, 5, 2, "2026-11-20", db_path=self.test_db)

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

    def login_cashier(self):
        return self.client.post("/auth/login", data={
            "username": "cashier_tester",
            "password": "cashierpass"
        }, follow_redirects=True)

    def test_01_pos_terminal_renders(self):
        """POS terminal loads with available products."""
        self.login_cashier()
        response = self.client.get("/billing/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Point of Sale Terminal", response.data)
        self.assertIn(b"Whole Milk 1L", response.data)
        self.assertIn(b"Customer Bill", response.data)

    def test_02_successful_single_item_checkout(self):
        """Processes a single item sale and decrements product stock atomically."""
        self.login_cashier()
        payload = {
            "items": [{"product_id": self.p1_id, "quantity": 4}],
            "discount": 0.0
        }

        response = self.client.post(
            "/billing/checkout",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("sale_id", data)

        # Verify stock was decremented from 20 to 16
        prod = Product.get_by_id(self.p1_id, db_path=self.test_db)
        self.assertEqual(prod["stock_qty"], 16)

        # Verify sale in database
        sale = Sale.get_by_id(data["sale_id"], db_path=self.test_db)
        self.assertEqual(sale["total_amount"], 14.00)
        self.assertEqual(sale["final_amount"], 14.00)
        self.assertEqual(len(sale["items"]), 1)

    def test_03_multi_item_checkout_with_discount(self):
        """Processes multi-item cart with discount applied."""
        self.login_cashier()
        payload = {
            "items": [
                {"product_id": self.p1_id, "quantity": 2},
                {"product_id": self.p2_id, "quantity": 3}
            ],
            "discount": 2.00
        }

        response = self.client.post(
            "/billing/checkout",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])

        # Verify database totals
        sale = Sale.get_by_id(data["sale_id"], db_path=self.test_db)
        self.assertEqual(sale["total_amount"], 19.00)
        self.assertEqual(sale["discount"], 2.00)
        self.assertEqual(sale["final_amount"], 17.00)

        # Verify stock decrements
        p1 = Product.get_by_id(self.p1_id, db_path=self.test_db)
        p2 = Product.get_by_id(self.p2_id, db_path=self.test_db)
        self.assertEqual(p1["stock_qty"], 18)
        self.assertEqual(p2["stock_qty"], 7)

    def test_04_reject_overselling(self):
        """Rejects checkout if requested quantity exceeds available inventory."""
        self.login_cashier()
        payload = {
            "items": [{"product_id": self.p3_id, "quantity": 8}],
            "discount": 0.0
        }

        response = self.client.post(
            "/billing/checkout",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("Insufficient stock", data["error"])

        # Verify stock remains untouched at 5
        prod = Product.get_by_id(self.p3_id, db_path=self.test_db)
        self.assertEqual(prod["stock_qty"], 5)

    def test_05_reject_zero_or_negative_quantity(self):
        """Rejects cart items with zero or negative quantity."""
        self.login_cashier()
        payload = {
            "items": [{"product_id": self.p1_id, "quantity": -2}],
            "discount": 0.0
        }

        response = self.client.post(
            "/billing/checkout",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("greater than zero", data["error"])

    def test_06_reject_excessive_discount(self):
        """Rejects discount that exceeds total bill amount."""
        self.login_cashier()
        payload = {
            "items": [{"product_id": self.p1_id, "quantity": 1}],
            "discount": 10.00
        }

        response = self.client.post(
            "/billing/checkout",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("cannot exceed", data["error"])

    def test_07_reject_empty_cart(self):
        """Rejects checkout request with no items."""
        self.login_cashier()
        payload = {"items": [], "discount": 0.0}

        response = self.client.post(
            "/billing/checkout",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])

    def test_08_invoice_rendering(self):
        """Invoice receipt renders correct metadata and items."""
        self.login_cashier()
        sale = Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[{"product_id": self.p1_id, "quantity": 2}],
            discount=1.00,
            db_path=self.test_db
        )

        response = self.client.get(f"/billing/invoice/{sale['sale_id']}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"GreenLeaf Grocers", response.data)
        self.assertIn(b"Whole Milk 1L", response.data)
        self.assertIn(b"PAID IN FULL", response.data)

    def test_09_invoice_csv_download(self):
        """Invoice can be downloaded as a CSV file."""
        self.login_cashier()
        sale = Sale.process_checkout(
            user_id=self.cashier.user_id,
            items=[{"product_id": self.p1_id, "quantity": 1}],
            discount=0.0,
            db_path=self.test_db
        )

        response = self.client.get(f"/billing/invoice/{sale['sale_id']}/csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("attachment; filename=invoice_INV-", response.headers["Content-Disposition"])
        self.assertIn(b"Whole Milk 1L", response.data)
        self.assertIn(b"Final Total Paid", response.data)

    def test_10_unauthenticated_user_blocked(self):
        """Unauthenticated visitor is redirected to login."""
        response = self.client.get("/billing/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()