"""
Verification unit tests for Day 1 deliverables.
Tests User authentication, Product querying, and transactional Sale checkout logic.
Uses standard library unittest.
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, get_db_connection
from app.models import User, Product, Sale

TEST_DB = Path(__file__).resolve().parent / "test_verify.db"


class TestDay1Verification(unittest.TestCase):
    def setUp(self):
        self.test_db = TEST_DB
        if self.test_db.exists():
            try:
                os.remove(self.test_db)
            except Exception:
                pass
        init_db(self.test_db)
        
        # Clean slate guarantee even if file was locked
        conn = get_db_connection(self.test_db)
        try:
            conn.execute("DELETE FROM sale_items")
            conn.execute("DELETE FROM sales")
            conn.execute("DELETE FROM products")
            conn.execute("DELETE FROM suppliers")
            conn.execute("DELETE FROM users")
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        if hasattr(self, "test_db") and self.test_db.exists():
            try:
                os.remove(self.test_db)
            except Exception:
                pass

    def test_01_user_creation_and_auth(self):
        user = User.create("test_admin", "securepass123", "admin", db_path=self.test_db)
        self.assertIsNotNone(user.user_id)
        self.assertEqual(user.username, "test_admin")
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_cashier)

        # Check password verification
        self.assertTrue(user.check_password("securepass123"))
        self.assertFalse(user.check_password("wrongpass"))

    def test_02_product_creation_and_validation(self):
        pid = Product.create(
            name="Organic Gala Apples 1kg",
            category="Produce",
            unit_price=3.99,
            stock_qty=50,
            reorder_level=10,
            expiry_date="2026-12-31",
            db_path=self.test_db
        )
        self.assertGreater(pid, 0)
        prod = Product.get_by_id(pid, db_path=self.test_db)
        self.assertEqual(prod["name"], "Organic Gala Apples 1kg")
        self.assertEqual(prod["stock_qty"], 50)

        # Test validation rejects negative price
        with self.assertRaises(ValueError):
            Product.create("Bad Price", "Produce", -1.0, 10, 5, "2026-12-31", db_path=self.test_db)

    def test_03_transactional_sale_checkout_and_stock_deduction(self):
        # 1. Create a product with 20 items
        pid = Product.create("Farm Milk 1L", "Dairy", 3.00, 20, 5, "2026-11-15", db_path=self.test_db)
        cashier = User.create("cashier_tester", "pass123", "cashier", db_path=self.test_db)

        # 2. Checkout 4 items
        result = Sale.process_checkout(
            user_id=cashier.user_id,
            items=[{"product_id": pid, "quantity": 4}],
            discount=1.0,
            db_path=self.test_db
        )

        self.assertEqual(result["total_amount"], 12.00)
        self.assertEqual(result["discount"], 1.00)
        self.assertEqual(result["final_amount"], 11.00)

        # 3. Verify stock was decremented from 20 to 16
        updated_prod = Product.get_by_id(pid, db_path=self.test_db)
        self.assertEqual(updated_prod["stock_qty"], 16)

    def test_04_overselling_rejected(self):
        pid = Product.create("Rare Exotic Fruit", "Produce", 10.00, 2, 1, "2026-11-20", db_path=self.test_db)
        cashier = User.create("cashier_oversell", "pass123", "cashier", db_path=self.test_db)

        # Attempt to sell 5 items when only 2 are in stock
        with self.assertRaises(ValueError):
            Sale.process_checkout(
                user_id=cashier.user_id,
                items=[{"product_id": pid, "quantity": 5}],
                db_path=self.test_db
            )

        # Verify stock remains unchanged at 2
        prod = Product.get_by_id(pid, db_path=self.test_db)
        self.assertEqual(prod["stock_qty"], 2)


if __name__ == "__main__":
    unittest.main()