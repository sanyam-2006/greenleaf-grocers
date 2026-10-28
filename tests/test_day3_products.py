"""
Unit tests for Day 3: Product Management, CRUD Operations, Search, and CSV Import/Export.
"""
import io
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Check if flask is available before running web tests
try:
    import flask
    from app import create_app
    from app.database import init_db
    from app.models import User, Product, Supplier
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestDay3Products(unittest.TestCase):
    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask is not installed yet. Run in your active virtual environment.")

        self.test_db = Path(__file__).resolve().parent / "test_products.db"
        if self.test_db.exists():
            os.remove(self.test_db)
        init_db(self.test_db)

        # Create test users and supplier
        User.create("admin_test", "adminpass", "admin", db_path=self.test_db)
        User.create("cashier_test", "cashierpass", "cashier", db_path=self.test_db)
        Supplier.create("Green Farms", "555-0199", "vendor@greenfarms.com", db_path=self.test_db)

        # Seed initial product
        Product.create(
            name="Organic Bananas",
            category="Produce",
            unit_price=1.99,
            stock_qty=50,
            reorder_level=15,
            expiry_date="2026-11-20",
            supplier_id=1,
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

    def login_as(self, username, password):
        return self.client.post("/auth/login", data={
            "username": username,
            "password": password
        }, follow_redirects=True)

    def test_01_product_catalog_renders(self):
        """Catalog page displays products table and filters."""
        self.login_as("admin_test", "adminpass")
        response = self.client.get("/products/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Inventory & Stock Catalog", response.data)
        self.assertIn(b"Organic Bananas", response.data)

    def test_02_product_search_and_filter(self):
        """Search and category filter return matching items."""
        self.login_as("admin_test", "adminpass")
        # Search for existing item
        res = self.client.get("/products/?search=Bananas")
        self.assertIn(b"Organic Bananas", res.data)

        # Search for non-existent item
        res_empty = self.client.get("/products/?search=NonExistentPizza")
        self.assertIn(b"No products found", res_empty.data)

    def test_03_admin_add_product_success(self):
        """Admin can successfully add a new grocery product."""
        self.login_as("admin_test", "adminpass")
        response = self.client.post("/products/add", data={
            "name": "Whole Milk 1L",
            "category": "Dairy & Eggs",
            "unit_price": "3.49",
            "stock_qty": "40",
            "reorder_level": "10",
            "expiry_date": "2026-11-15",
            "supplier_id": "1"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"added successfully", response.data)
        self.assertIn(b"Whole Milk 1L", response.data)

        # Verify in DB
        prod = Product.get_all(search="Whole Milk 1L", db_path=self.test_db)
        self.assertEqual(len(prod), 1)
        self.assertEqual(prod[0]["stock_qty"], 40)

    def test_04_add_product_validation_rejects_negative_price(self):
        """Rejects products with negative prices or quantities."""
        self.login_as("admin_test", "adminpass")
        response = self.client.post("/products/add", data={
            "name": "Bad Product",
            "category": "Snacks",
            "unit_price": "-5.00",
            "stock_qty": "10",
            "reorder_level": "5",
            "expiry_date": "2026-12-01"
        }, follow_redirects=True)

        self.assertIn(b"cannot be negative", response.data)

    def test_05_admin_edit_product_success(self):
        """Admin can edit product pricing, stock, and thresholds."""
        self.login_as("admin_test", "adminpass")
        response = self.client.post("/products/edit/1", data={
            "name": "Organic Bananas (Fair Trade)",
            "category": "Produce",
            "unit_price": "2.49",
            "stock_qty": "75",
            "reorder_level": "20",
            "expiry_date": "2026-11-25",
            "supplier_id": "1"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"updated successfully", response.data)

        updated = Product.get_by_id(1, db_path=self.test_db)
        self.assertEqual(updated["name"], "Organic Bananas (Fair Trade)")
        self.assertEqual(updated["unit_price"], 2.49)
        self.assertEqual(updated["stock_qty"], 75)

    def test_06_admin_delete_product_success(self):
        """Admin can delete a product from inventory."""
        self.login_as("admin_test", "adminpass")
        response = self.client.post("/products/delete/1", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"has been removed", response.data)

        # Verify product is deleted
        deleted = Product.get_by_id(1, db_path=self.test_db)
        self.assertIsNone(deleted)

    def test_07_export_csv(self):
        """Exports catalog as downloadable CSV file."""
        self.login_as("admin_test", "adminpass")
        response = self.client.get("/products/export")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn("attachment; filename=greenleaf_inventory", response.headers["Content-Disposition"])
        self.assertIn(b"Organic Bananas", response.data)
        self.assertIn(b"Produce", response.data)

    def test_08_import_csv(self):
        """Uploads and imports products from a CSV file."""
        self.login_as("admin_test", "adminpass")
        csv_content = (
            "name,category,unit_price,stock_qty,reorder_level,expiry_date\n"
            "Greek Yogurt 500g,Dairy & Eggs,4.99,30,10,2026-12-01\n"
            "Sourdough Bread,Bakery,3.99,20,5,2026-11-05\n"
        )
        data = {
            "csv_file": (io.BytesIO(csv_content.encode("utf-8")), "test_import.csv")
        }

        response = self.client.post(
            "/products/import",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Successfully imported 2 products", response.data)

        # Verify new products exist
        all_prods = Product.get_all(db_path=self.test_db)
        self.assertEqual(len(all_prods), 3)

    def test_09_cashier_restricted_from_crud(self):
        """Cashiers cannot add, edit, delete, or import products."""
        self.login_as("cashier_test", "cashierpass")

        # Attempt to add product as cashier
        res_add = self.client.post("/products/add", data={"name": "Hacked Item"}, follow_redirects=True)
        self.assertIn(b"Access denied. Admin privileges required.", res_add.data)

        # Attempt to delete product as cashier
        res_del = self.client.post("/products/delete/1", follow_redirects=True)
        self.assertIn(b"Access denied. Admin privileges required.", res_del.data)


if __name__ == "__main__":
    unittest.main()