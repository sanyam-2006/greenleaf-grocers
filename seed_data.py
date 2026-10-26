# Purpose: Generates the complete dataset as required by the internship project prompt (50+ products, 500+ sales over months, multiple suppliers, admin and cashier users).

"""
Seed script to initialize and populate GreenLeaf Grocers SQLite database.
Generates:
- 3 Users (admin, cashier1, cashier2)
- 6 Suppliers
- 60+ Realistic Grocery Products across 6 categories
- 550+ Historical Sales Transactions over the past 90 days with multi-item sale records
"""

import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path so app modules can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import get_db_connection, init_db, DEFAULT_DB_PATH
from app.utils import generate_password_hash

# 1. Preset Realistic Grocery Suppliers
SUPPLIERS_DATA = [
    ("FarmFresh Logistics", "+1-555-0101", "orders@farmfreshlogistics.com"),
    ("PureDairy Co.", "+1-555-0102", "supply@puredairy.com"),
    ("Golden Harvest Bakeries", "+1-555-0103", "contact@goldenharvest.com"),
    ("Tropicana Distributors", "+1-555-0104", "sales@tropicanadist.com"),
    ("GreenFields Organics", "+1-555-0105", "info@greenfieldsorganics.org"),
    ("Apex Beverage Corp", "+1-555-0106", "vendor@apexbev.com"),
]

# 2. Preset Realistic Grocery Products across 6 categories
# Format: (Name, Category, Unit Price, Min Stock, Max Stock, Reorder Level, Days to Expiry, Supplier Index)
PRODUCTS_CATALOG = [
    # Dairy & Eggs
    ("Whole Milk 1L", "Dairy & Eggs", 3.49, 15, 60, 20, 12, 1),
    ("Low-Fat Milk 1L", "Dairy & Eggs", 3.29, 10, 50, 15, 10, 1),
    ("Greek Yogurt 500g", "Dairy & Eggs", 4.99, 8, 40, 12, 14, 1),
    ("Cheddar Cheese Block 250g", "Dairy & Eggs", 5.49, 20, 50, 15, 60, 1),
    ("Salted Butter 200g", "Dairy & Eggs", 3.99, 18, 45, 15, 45, 1),
    ("Organic Large Eggs 12pk", "Dairy & Eggs", 4.79, 12, 40, 15, 21, 1),
    ("Heavy Whipping Cream 500ml", "Dairy & Eggs", 4.29, 6, 25, 10, 8, 1),
    ("Mozzarella Shredded 300g", "Dairy & Eggs", 4.59, 14, 35, 10, 30, 1),
    ("Cottage Cheese 400g", "Dairy & Eggs", 3.89, 5, 25, 10, 9, 1),
    ("Almond Milk Unsweetened 1L", "Dairy & Eggs", 3.99, 25, 60, 15, 90, 1),

    # Fresh Produce
    ("Organic Bananas (bunch)", "Produce", 1.89, 30, 80, 25, 6, 4),
    ("Honeycrisp Apples 1kg", "Produce", 4.49, 20, 60, 20, 20, 4),
    ("Roma Tomatoes 1kg", "Produce", 3.29, 15, 50, 15, 10, 4),
    ("Hass Avocados (3pk)", "Produce", 4.99, 12, 40, 15, 7, 4),
    ("Yellow Onions 2kg bag", "Produce", 2.99, 25, 70, 20, 45, 4),
    ("Idaho Potatoes 3kg bag", "Produce", 4.29, 30, 80, 25, 60, 4),
    ("Fresh Baby Spinach 250g", "Produce", 2.99, 8, 30, 12, 5, 4),
    ("Organic Carrots 1kg", "Produce", 2.49, 20, 50, 15, 25, 4),
    ("Red Bell Peppers (2pk)", "Produce", 3.49, 10, 35, 12, 11, 4),
    ("English Cucumbers (ea)", "Produce", 1.59, 15, 40, 15, 9, 4),

    # Bakery
    ("Artisan Sourdough Loaf", "Bakery", 4.49, 10, 30, 10, 5, 2),
    ("Whole Wheat Sandwich Bread", "Bakery", 3.29, 20, 50, 15, 7, 2),
    ("Butter Croissants (4pk)", "Bakery", 4.99, 8, 25, 10, 4, 2),
    ("Plain Bagels (6pk)", "Bakery", 3.79, 12, 35, 12, 8, 2),
    ("Chocolate Chip Muffins (4pk)", "Bakery", 4.29, 6, 20, 8, 6, 2),
    ("Brioche Burger Buns (4pk)", "Bakery", 3.99, 10, 30, 10, 10, 2),
    ("French Baguette", "Bakery", 2.49, 15, 40, 12, 3, 2),
    ("Cinnamon Rolls (4pk)", "Bakery", 4.89, 5, 20, 8, 5, 2),
    ("Pita Bread (6pk)", "Bakery", 2.79, 14, 35, 10, 12, 2),
    ("Garlic Naan (3pk)", "Bakery", 3.49, 12, 30, 10, 14, 2),

    # Beverages
    ("Fresh Orange Juice 1L", "Beverages", 4.29, 15, 40, 12, 18, 5),
    ("Pure Apple Cider 1L", "Beverages", 3.99, 10, 30, 10, 30, 5),
    ("Cold Brew Coffee 946ml", "Beverages", 5.79, 12, 35, 10, 40, 5),
    ("Organic Green Tea 20pk", "Beverages", 3.99, 20, 50, 15, 180, 5),
    ("Sparkling Water Lemon 6pk", "Beverages", 4.99, 25, 60, 20, 180, 5),
    ("Coconut Water 1L", "Beverages", 3.79, 18, 45, 15, 120, 5),
    ("Ginger Ale 2L bottle", "Beverages", 2.29, 20, 60, 15, 150, 5),
    ("Lemon Iced Tea 1.5L", "Beverages", 2.99, 15, 45, 12, 90, 5),
    ("Cranberry Juice Cocktail 1L", "Beverages", 3.49, 14, 40, 10, 120, 5),
    ("Natural Spring Water 12pk", "Beverages", 4.99, 30, 80, 25, 365, 5),

    # Pantry & Grains
    ("Basmati Rice 2kg", "Pantry", 7.99, 25, 70, 20, 365, 0),
    ("Extra Virgin Olive Oil 750ml", "Pantry", 11.99, 15, 45, 15, 300, 0),
    ("Italian Penne Rigate 500g", "Pantry", 2.19, 30, 80, 20, 365, 0),
    ("Organic Marinara Sauce 680g", "Pantry", 3.99, 20, 50, 15, 240, 0),
    ("Canned Black Beans 400g", "Pantry", 1.49, 35, 90, 25, 400, 0),
    ("Rolled Oats 1kg", "Pantry", 4.29, 18, 50, 15, 240, 0),
    ("Pure Clover Honey 500g", "Pantry", 6.99, 12, 35, 10, 365, 0),
    ("Creamy Peanut Butter 500g", "Pantry", 4.19, 20, 50, 15, 200, 0),
    ("Organic Cane Sugar 1kg", "Pantry", 3.49, 22, 60, 15, 365, 0),
    ("All-Purpose Flour 2kg", "Pantry", 3.79, 25, 70, 20, 240, 0),

    # Snacks & Confectionery
    ("Kettle Sea Salt Chips 200g", "Snacks", 3.49, 25, 70, 20, 90, 3),
    ("Organic Dark Chocolate 85% 100g", "Snacks", 2.99, 20, 50, 15, 180, 3),
    ("Roasted Almonds Salted 250g", "Snacks", 5.99, 15, 40, 12, 120, 3),
    ("Chewy Granola Bars (6pk)", "Snacks", 3.79, 20, 55, 15, 120, 3),
    ("Pretzel Twists 300g", "Snacks", 2.89, 18, 50, 15, 100, 3),
    ("Gourmet Microwave Popcorn 3pk", "Snacks", 3.29, 22, 60, 15, 150, 3),
    ("Trail Mix Cranberry & Nuts 250g", "Snacks", 4.99, 14, 40, 12, 120, 3),
    ("Rice Crackers Tamari 150g", "Snacks", 2.99, 16, 45, 12, 90, 3),
    ("Gummy Bears Organic 150g", "Snacks", 2.49, 18, 50, 15, 180, 3),
    ("Tortilla Chips Sea Salt 300g", "Snacks", 3.69, 25, 65, 20, 90, 3)
]


def seed_database(db_path=None):
    """Initializes tables and seeds test data."""
    print(f"--> Initializing schema on: {db_path or DEFAULT_DB_PATH}")
    init_db(db_path)

    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # Clear existing data to allow clean re-runs
    cur.execute("DELETE FROM sale_items")
    cur.execute("DELETE FROM sales")
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM suppliers")
    cur.execute("DELETE FROM users")
    conn.commit()

    print("--> Seeding Users (admin, cashier1, cashier2)...")
    users = [
        ("admin", generate_password_hash("admin123"), "admin"),
        ("cashier1", generate_password_hash("cashier123"), "cashier"),
        ("cashier2", generate_password_hash("cashier123"), "cashier"),
    ]
    cur.executemany("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", users)
    conn.commit()

    # Map usernames to user_ids
    user_rows = cur.execute("SELECT user_id, username, role FROM users").fetchall()
    cashier_ids = [r["user_id"] for r in user_rows if r["role"] == "cashier"]
    admin_id = [r["user_id"] for r in user_rows if r["role"] == "admin"][0]

    print("--> Seeding Suppliers...")
    supplier_ids = []
    for s_name, s_phone, s_email in SUPPLIERS_DATA:
        cur.execute("INSERT INTO suppliers (name, phone, email) VALUES (?, ?, ?)", (s_name, s_phone, s_email))
        supplier_ids.append(cur.lastrowid)
    conn.commit()

    print(f"--> Seeding {len(PRODUCTS_CATALOG)} Products...")
    today = datetime.now().date()
    product_records = []

    # Intentionally make a couple of products "low stock" and "near expiry" for alerts testing
    for i, item in enumerate(PRODUCTS_CATALOG):
        name, category, price, min_s, max_s, reorder, exp_days, supp_idx = item
        supplier_id = supplier_ids[supp_idx]

        # Determine stock level: intentionally leave 4 products below reorder level
        if i in [3, 11, 22, 34]:
            stock_qty = random.randint(1, reorder - 2)
        else:
            stock_qty = random.randint(min_s, max_s)

        # Determine expiry date: intentionally set 3 products to expire within 5-10 days
        if i in [6, 16, 26]:
            expiry_date = today + timedelta(days=random.randint(3, 10))
        else:
            expiry_date = today + timedelta(days=exp_days)

        cur.execute(
            """
            INSERT INTO products (name, category, unit_price, stock_qty, reorder_level, expiry_date, supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name, category, price, stock_qty, reorder, str(expiry_date), supplier_id)
        )
        product_records.append({
            "product_id": cur.lastrowid,
            "name": name,
            "category": category,
            "unit_price": price
        })
    conn.commit()

    print("--> Generating 550+ Historical Sales Transactions over the last 90 days...")
    # Spread 560 sales over the last 90 days with weekend weight
    total_sales_to_generate = 560
    start_date = today - timedelta(days=90)

    # Pre-generate dates with natural distribution
    date_weights = []
    for day_offset in range(91):
        cur_d = start_date + timedelta(days=day_offset)
        # Saturday and Sunday get slightly more foot traffic
        weight = 8 if cur_d.weekday() in (5, 6) else 5
        date_weights.extend([cur_d] * weight)

    for _ in range(total_sales_to_generate):
        sale_d = random.choice(date_weights)
        # Random time between 08:30:00 and 21:30:00
        hour = random.randint(8, 21)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        sale_t = f"{hour:02d}:{minute:02d}:{second:02d}"

        cashier_id = random.choice(cashier_ids)

        # Basket size: 1 to 5 distinct items
        basket_size = random.choices([1, 2, 3, 4, 5], weights=[20, 35, 25, 12, 8])[0]
        selected_products = random.sample(product_records, basket_size)

        sale_total = 0.0
        sale_items = []

        for prod in selected_products:
            qty = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
            item_price = prod["unit_price"]
            line_total = round(item_price * qty, 2)
            sale_total += line_total
            sale_items.append((prod["product_id"], qty, item_price))

        # Occasional promotional discount (e.g. 10% chance of $1 - $5 discount)
        discount = 0.0
        if random.random() < 0.15 and sale_total > 15.0:
            discount = round(min(sale_total * 0.1, random.choice([1.0, 2.0, 3.0, 5.0])), 2)

        final_amt = round(max(0.0, sale_total - discount), 2)

        cur.execute(
            """
            INSERT INTO sales (sale_date, sale_time, user_id, total_amount, discount, final_amount)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(sale_d), sale_t, cashier_id, round(sale_total, 2), discount, final_amt)
        )
        sale_id = cur.lastrowid

        for pid, qty, price in sale_items:
            cur.execute(
                """
                INSERT INTO sale_items (sale_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
                """,
                (sale_id, pid, qty, price)
            )

    conn.commit()

    # Query counts for verification
    u_count = cur.execute("SELECT count(*) FROM users").fetchone()[0]
    p_count = cur.execute("SELECT count(*) FROM products").fetchone()[0]
    s_count = cur.execute("SELECT count(*) FROM sales").fetchone()[0]
    si_count = cur.execute("SELECT count(*) FROM sale_items").fetchone()[0]
    low_stock = cur.execute("SELECT count(*) FROM products WHERE stock_qty <= reorder_level").fetchone()[0]
    expiring = cur.execute("SELECT count(*) FROM products WHERE expiry_date <= date('now', '+15 days')").fetchone()[0]

    conn.close()

    print("\n================ SEED SUMMARY ================")
    print(f" Users seeded:            {u_count}")
    print(f" Suppliers seeded:        {len(supplier_ids)}")
    print(f" Products seeded:         {p_count}")
    print(f" Sales transactions:      {s_count}")
    print(f" Line items (sale_items): {si_count}")
    print(f" Low-stock items count:   {low_stock} (triggers alert test)")
    print(f" Near-expiry items count: {expiring} (triggers alert test)")
    print("==============================================")
    print("SUCCESS: Day 1 database and seed data setup complete!")


if __name__ == "__main__":
    seed_database()