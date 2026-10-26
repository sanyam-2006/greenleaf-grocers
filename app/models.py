"""
Purpose: Implements the business logic and queries:-
- User: Role verification (admin vs cashier), password checking.
- Supplier: Create and list vendors.
- Product: CRUD operations, search, category filter, low-stock alerts, near-expiry alerts, validation.
- Sale: Multi-item checkout executed in a single atomic transaction. Automatically rejects negative quantities, prevents selling more than available stock, inserts records into sales and sale_items, and deducts stock from products.
"""

"""
Data models and query helpers for GreenLeaf Grocers.
Implements business validation, stock consistency, and relational integrity.
"""
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
from app.database import get_db_connection
from app.utils import generate_password_hash, check_password_hash


class User:
    """User model supporting role-based access (admin, cashier)."""

    def __init__(self, user_id: int, username: str, password_hash: str, role: str, created_at: Any = None):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_cashier(self) -> bool:
        return self.role == "cashier"

    @classmethod
    def get_by_username(cls, username: str, db_path=None) -> Optional["User"]:
        conn = get_db_connection(db_path)
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                return cls(row["user_id"], row["username"], row["password_hash"], row["role"], row["created_at"])
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, user_id: int, db_path=None) -> Optional["User"]:
        conn = get_db_connection(db_path)
        try:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return cls(row["user_id"], row["username"], row["password_hash"], row["role"], row["created_at"])
            return None
        finally:
            conn.close()

    @classmethod
    def create(cls, username: str, password: str, role: str, db_path=None) -> "User":
        if role not in ("admin", "cashier"):
            raise ValueError("Role must be either 'admin' or 'cashier'")
        pw_hash = generate_password_hash(password)
        conn = get_db_connection(db_path)
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, pw_hash, role)
                )
                user_id = cur.lastrowid
            return cls(user_id, username, pw_hash, role)
        finally:
            conn.close()

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Supplier:
    """Supplier model managing vendor information."""

    @classmethod
    def get_all(cls, db_path=None) -> List[Dict]:
        conn = get_db_connection(db_path)
        try:
            rows = conn.execute("SELECT * FROM suppliers ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @classmethod
    def create(cls, name: str, phone: str, email: str = "", db_path=None) -> int:
        conn = get_db_connection(db_path)
        try:
            with conn:
                cur = conn.execute(
                    "INSERT INTO suppliers (name, phone, email) VALUES (?, ?, ?)",
                    (name.strip(), phone.strip(), email.strip() if email else None)
                )
                return cur.lastrowid
        finally:
            conn.close()


class Product:
    """Product model managing inventory items, pricing, reorder levels, and expiry."""

    @classmethod
    def get_all(cls, category: Optional[str] = None, search: Optional[str] = None, db_path=None) -> List[Dict]:
        conn = get_db_connection(db_path)
        try:
            query = """
                SELECT p.*, s.name as supplier_name 
                FROM products p 
                LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
                WHERE 1=1
            """
            params = []
            if category:
                query += " AND p.category = ?"
                params.append(category)
            if search:
                query += " AND (p.name LIKE ? OR p.category LIKE ?)"
                params.extend([f"%{search}%", f"%{search}%"])

            query += " ORDER BY p.name ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, product_id: int, db_path=None) -> Optional[Dict]:
        conn = get_db_connection(db_path)
        try:
            row = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    @classmethod
    def create(cls, name: str, category: str, unit_price: float, stock_qty: int,
               reorder_level: int, expiry_date: str, supplier_id: Optional[int] = None, db_path=None) -> int:
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        if stock_qty < 0:
            raise ValueError("Stock quantity cannot be negative.")
        if reorder_level < 0:
            raise ValueError("Reorder level cannot be negative.")

        conn = get_db_connection(db_path)
        try:
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO products (name, category, unit_price, stock_qty, reorder_level, expiry_date, supplier_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name.strip(), category.strip(), float(unit_price), int(stock_qty),
                     int(reorder_level), str(expiry_date), supplier_id)
                )
                return cur.lastrowid
        finally:
            conn.close()

    @classmethod
    def update(cls, product_id: int, name: str, category: str, unit_price: float,
               stock_qty: int, reorder_level: int, expiry_date: str, supplier_id: Optional[int] = None, db_path=None) -> bool:
        if unit_price < 0 or stock_qty < 0 or reorder_level < 0:
            raise ValueError("Prices and stock numbers cannot be negative.")

        conn = get_db_connection(db_path)
        try:
            with conn:
                cur = conn.execute(
                    """
                    UPDATE products 
                    SET name = ?, category = ?, unit_price = ?, stock_qty = ?, 
                        reorder_level = ?, expiry_date = ?, supplier_id = ?
                    WHERE product_id = ?
                    """,
                    (name.strip(), category.strip(), float(unit_price), int(stock_qty),
                     int(reorder_level), str(expiry_date), supplier_id, product_id)
                )
                return cur.rowcount > 0
        finally:
            conn.close()

    @classmethod
    def delete(cls, product_id: int, db_path=None) -> bool:
        conn = get_db_connection(db_path)
        try:
            with conn:
                cur = conn.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
                return cur.rowcount > 0
        finally:
            conn.close()

    @classmethod
    def get_low_stock(cls, db_path=None) -> List[Dict]:
        """Returns items where stock quantity is at or below the reorder level."""
        conn = get_db_connection(db_path)
        try:
            rows = conn.execute(
                "SELECT * FROM products WHERE stock_qty <= reorder_level ORDER BY stock_qty ASC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    @classmethod
    def get_near_expiry(cls, days: int = 15, db_path=None) -> List[Dict]:
        """Returns items expiring within the specified number of days."""
        conn = get_db_connection(db_path)
        try:
            rows = conn.execute(
                """
                SELECT *, 
                       CAST((julianday(expiry_date) - julianday('now')) AS INTEGER) AS days_left
                FROM products 
                WHERE expiry_date <= date('now', '+' || ? || ' days')
                ORDER BY expiry_date ASC
                """,
                (days,)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


class Sale:
    """Sale and Sale Items manager handling atomic checkout and stock updates."""

    @classmethod
    def process_checkout(cls, user_id: int, items: List[Dict[str, Any]], discount: float = 0.0,
                         sale_date: Optional[str] = None, sale_time: Optional[str] = None,
                         db_path=None) -> Dict[str, Any]:
        """
        Processes a multi-item bill inside an atomic transaction.
        items: list of dicts with keys: {'product_id': int, 'quantity': int}
        """
        if not items:
            raise ValueError("Cannot checkout an empty cart.")
        if discount < 0:
            raise ValueError("Discount cannot be negative.")

        now = datetime.now()
        s_date = sale_date or now.strftime("%Y-%m-%d")
        s_time = sale_time or now.strftime("%H:%M:%S")

        conn = get_db_connection(db_path)
        try:
            with conn:
                # 1. Validate all items and stock levels
                total_amount = 0.0
                prepared_items = []

                for item in items:
                    pid = int(item["product_id"])
                    qty = int(item["quantity"])
                    if qty <= 0:
                        raise ValueError(f"Quantity must be greater than zero for product ID {pid}")

                    p = conn.execute("SELECT * FROM products WHERE product_id = ?", (pid,)).fetchone()
                    if not p:
                        raise ValueError(f"Product ID {pid} does not exist.")

                    if p["stock_qty"] < qty:
                        raise ValueError(
                            f"Insufficient stock for '{p['name']}'. Requested: {qty}, Available: {p['stock_qty']}"
                        )

                    line_total = p["unit_price"] * qty
                    total_amount += line_total
                    prepared_items.append({
                        "product_id": pid,
                        "name": p["name"],
                        "unit_price": p["unit_price"],
                        "quantity": qty,
                        "new_stock": p["stock_qty"] - qty
                    })

                if discount > total_amount:
                    raise ValueError(f"Discount ({discount}) cannot exceed total bill amount ({total_amount}).")

                final_amount = round(total_amount - discount, 2)

                # 2. Insert into sales
                cur = conn.execute(
                    """
                    INSERT INTO sales (sale_date, sale_time, user_id, total_amount, discount, final_amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (s_date, s_time, user_id, round(total_amount, 2), round(discount, 2), final_amount)
                )
                sale_id = cur.lastrowid

                # 3. Insert sale_items and deduct stock
                for it in prepared_items:
                    conn.execute(
                        """
                        INSERT INTO sale_items (sale_id, product_id, quantity, price)
                        VALUES (?, ?, ?, ?)
                        """,
                        (sale_id, it["product_id"], it["quantity"], it["unit_price"])
                    )
                    conn.execute(
                        "UPDATE products SET stock_qty = ? WHERE product_id = ?",
                        (it["new_stock"], it["product_id"])
                    )

            return {
                "sale_id": sale_id,
                "sale_date": s_date,
                "sale_time": s_time,
                "user_id": user_id,
                "total_amount": round(total_amount, 2),
                "discount": round(discount, 2),
                "final_amount": final_amount,
                "items": prepared_items
            }
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, sale_id: int, db_path=None) -> Optional[Dict]:
        conn = get_db_connection(db_path)
        try:
            sale = conn.execute(
                """
                SELECT s.*, u.username as cashier_name
                FROM sales s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.sale_id = ?
                """,
                (sale_id,)
            ).fetchone()

            if not sale:
                return None

            items = conn.execute(
                """
                SELECT si.*, p.name as product_name, p.category
                FROM sale_items si
                JOIN products p ON si.product_id = p.product_id
                WHERE si.sale_id = ?
                """,
                (sale_id,)
            ).fetchall()

            res = dict(sale)
            res["items"] = [dict(it) for it in items]
            return res
        finally:
            conn.close()