"""
Unit tests for Day 2: Authentication and Role-Based Access Control (RBAC).
Tests:
- Login page rendering
- Admin login and session creation
- Cashier login and session creation
- Invalid password rejection
- Protected route redirection for unauthenticated users
- Admin route protection against cashiers
- Logout functionality
"""
import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Check if flask is available before running web tests
try:
    import flask
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestDay2Auth(unittest.TestCase):
    def setUp(self):
        if not FLASK_AVAILABLE:
            self.skipTest("Flask is not installed yet. Run 'pip install flask' to execute web tests.")

        from app import create_app
        from app.database import init_db
        from app.models import User

        self.test_db = Path(__file__).resolve().parent / "test_auth.db"
        if self.test_db.exists():
            try:
                os.remove(self.test_db)
            except Exception:
                pass
        init_db(self.test_db)

        # Create test users
        User.create("admin_test", "adminpass", "admin", db_path=self.test_db)
        User.create("cashier_test", "cashierpass", "cashier", db_path=self.test_db)

        # Set up Flask test client
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

    def test_01_login_page_renders(self):
        """Verify the login page loads with HTTP 200."""
        response = self.client.get("/auth/login")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Employee Portal", response.data)
        self.assertIn(b"Sign In", response.data)

    def test_02_admin_login_success(self):
        """Admin login succeeds and redirects to dashboard."""
        response = self.client.post("/auth/login", data={
            "username": "admin_test",
            "password": "adminpass"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Executive Dashboard", response.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("username"), "admin_test")
            self.assertEqual(sess.get("role"), "admin")

    def test_03_cashier_login_success(self):
        """Cashier login succeeds and redirects to cashier billing terminal."""
        response = self.client.post("/auth/login", data={
            "username": "cashier_test",
            "password": "cashierpass"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b"Point of Sale" in response.data or b"Cashier" in response.data or b"POS" in response.data,
            "Expected cashier to be redirected to Point of Sale terminal"
        )
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("username"), "cashier_test")
            self.assertEqual(sess.get("role"), "cashier")

    def test_04_invalid_credentials_rejected(self):
        """Invalid credentials stay on login page with error."""
        response = self.client.post("/auth/login", data={
            "username": "admin_test",
            "password": "wrong_password"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    def test_05_unauthenticated_user_redirected(self):
        """Accessing protected routes without login redirects to /auth/login."""
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

    def test_06_cashier_blocked_from_admin_dashboard(self):
        """Cashiers cannot access the admin dashboard."""
        # Log in as cashier
        self.client.post("/auth/login", data={
            "username": "cashier_test",
            "password": "cashierpass"
        })

        # Attempt to access admin dashboard
        response = self.client.get("/dashboard", follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Access Forbidden", response.data)

    def test_07_logout_clears_session(self):
        """Logging out clears session and redirects to login."""
        # Log in first
        self.client.post("/auth/login", data={
            "username": "admin_test",
            "password": "adminpass"
        })

        # Log out
        response = self.client.get("/auth/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sign In", response.data)

        # Confirm session is cleared
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)
            self.assertNotIn("username", sess)


if __name__ == "__main__":
    unittest.main()