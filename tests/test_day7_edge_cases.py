"""
Unit tests for Day 7: Defensive Edge-Case Validation, Input Hardening,
Supplier Management Lifecycle, and Error Handlers.
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db
from app.models import User, Product, Supplier, Sale
from app.analytics import AnalyticsEngine

try:
    import flask
    from app import create_app
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestDay7EdgeCases(unittest.TestCase):
    def setUp(self):
        self.test_db = Path(__file__).resolve().parent / "test_day7_edge.db"
        if self.test_db.exists():
            os.remove(self.test_db)
        init_db(self.test_db)

        # 1. Test Users
        self.admin = User.create("admin_edge", "adminpass", "admin", db_path=self.test_db)
        self.cashier = User.create("cashier_edge", "cashpass", "cashier", db_path=self.test_db)

        # 2. Test Supplier & Product
        self.s1 = Supplier.create("Green Valley Farms", "555-0100", "orders@greenvalley.com", db_path=self.test_db)
        self.p1 = Product.create(
            name="Organic Gala Apples",
            category="Produce",
            unit_price=2.99,
            stock_qty=10,
            reorder_level=5,
            expiry_date="2026-12-01",
            supplier_id=self.s1,
            db_path=self.test_db
        )

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
        self.client.get("/auth/logout")
        return self.client.post("/auth/login", data={
            "username": "admin_edge",
            "password": "adminpass"
        }, follow_redirects=True)

    def login_cashier(self):
        self.client.get("/auth/logout")
        return self.client.post("/auth/login", data={
            "username": "cashier_edge",
            "password": "cashpass"
        }, follow_redirects=True)

    def test_01_product_negative_price_rejected(self):
        """Rejects product creation with negative unit price."""
        with self.assertRaises(ValueError):
            Product.create(
                name="Defective Item",
                category="Produce",
                unit_price=-4.50,
                stock_qty=10,
                reorder_level=5,
                expiry_date="2026-12-01",
                db_path=self.test_db
            )

    def test_02_product_negative_stock_rejected(self):
        """Rejects product creation with negative stock quantity."""
        with self.assertRaises(ValueError):
            Product.create(
                name="Defective Item",
                category="Produce",
                unit_price=4.50,
                stock_qty=-10,
                reorder_level=5,
                expiry_date="2026-12-01",
                db_path=self.test_db
            )

    def test_03_supplier_empty_fields_rejected(self):
        """Rejects supplier registration with missing name or phone."""
        with self.assertRaises(ValueError):
            Supplier.create(name="", phone="555-1234", db_path=self.test_db)
        with self.assertRaises(ValueError):
            Supplier.create(name="Valid Vendor", phone="", db_path=self.test_db)

    def test_04_supplier_crud_and_nullify_on_delete(self):
        """Verifies full supplier lifecycle and verifies products are preserved when vendor is deleted."""
        # Create
        sup_id = Supplier.create("Sunny Dairy Co.", "555-0200", "milk@sunnydairy.com", db_path=self.test_db)
        self.assertIsNotNone(sup_id)

        # Read
        sup = Supplier.get_by_id(sup_id, db_path=self.test_db)
        self.assertEqual(sup["name"], "Sunny Dairy Co.")

        # Update
        updated = Supplier.update(sup_id, "Sunny Dairy & Creamery", "555-0299", "sales@sunnydairy.com", db_path=self.test_db)
        self.assertTrue(updated)
        sup_updated = Supplier.get_by_id(sup_id, db_path=self.test_db)
        self.assertEqual(sup_updated["name"], "Sunny Dairy & Creamery")

        # Assign product to supplier
        Product.create("Whole Milk", "Dairy & Eggs", 3.29, 20, 5, "2026-12-01", supplier_id=sup_id, db_path=self.test_db)

        # Delete supplier
        deleted = Supplier.delete(sup_id, db_path=self.test_db)
        self.assertTrue(deleted)
        self.assertIsNone(Supplier.get_by_id(sup_id, db_path=self.test_db))

        # Check product still exists with supplier_id set to NULL
        prods = Product.get_all(db_path=self.test_db)
        milk = next(p for p in prods if p["name"] == "Whole Milk")
        self.assertIsNone(milk["supplier_id"])

    def test_05_checkout_negative_or_zero_quantity_rejected(self):
        """Atomic checkout rejects non-positive item quantities."""
        with self.assertRaises(ValueError):
            Sale.process_checkout(
                user_id=self.cashier.user_id,
                items=[{"product_id": self.p1, "quantity": 0}],
                discount=0.0,
                db_path=self.test_db
            )
        with self.assertRaises(ValueError):
            Sale.process_checkout(
                user_id=self.cashier.user_id,
                items=[{"product_id": self.p1, "quantity": -5}],
                discount=0.0,
                db_path=self.test_db
            )

    def test_06_checkout_excessive_discount_rejected(self):
        """Atomic checkout rejects discount exceeding cart value."""
        with self.assertRaises(ValueError):
            Sale.process_checkout(
                user_id=self.cashier.user_id,
                items=[{"product_id": self.p1, "quantity": 2}],
                discount=10.00,
                db_path=self.test_db
            )

    def test_07_checkout_overselling_rejected(self):
        """Atomic checkout prevents purchasing more units than in stock."""
        # Stock is 10, try to purchase 15
        with self.assertRaises(ValueError):
            Sale.process_checkout(
                user_id=self.cashier.user_id,
                items=[{"product_id": self.p1, "quantity": 15}],
                discount=0.0,
                db_path=self.test_db
            )
        # Verify inventory remains untouched
        prod = Product.get_by_id(self.p1, db_path=self.test_db)
        self.assertEqual(prod["stock_qty"], 10)

    def test_08_inverted_date_range_graceful_handling(self):
        """Auto-corrects or safely queries inverted date ranges without crashing."""
        kpis = AnalyticsEngine.get_kpis(start_date="2026-12-31", end_date="2026-01-01", db_path=self.test_db)
        self.assertIsInstance(kpis, dict)
        self.assertIn("total_revenue", kpis)

    def test_09_suppliers_web_access_rbac(self):
        """Admin can access supplier directory, while cashiers are blocked."""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not installed in test runner environment.")

        # Admin access
        self.login_admin()
        res_admin = self.client.get("/suppliers/")
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b"Supplier Directory", res_admin.data)
        self.assertIn(b"Green Valley Farms", res_admin.data)

        # Cashier access blocked
        self.login_cashier()
        res_cashier = self.client.get("/suppliers/", follow_redirects=True)
        self.assertIn(b"Admin privileges required", res_cashier.data)

    def test_10_custom_error_handlers(self):
        """Non-existent URLs trigger branded 404 error handler."""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not installed in test runner environment.")

        res = self.client.get("/non_existent_page_12345")
        self.assertEqual(res.status_code, 404)
        self.assertIn(b"404", res.data)
        self.assertIn(b"Page Not Found", res.data)


if __name__ == "__main__":
    unittest.main()