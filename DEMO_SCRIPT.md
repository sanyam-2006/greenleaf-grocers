# GreenLeaf Grocers — 5-Minute Live Presentation & Demo Walkthrough Script

---

## ⏱ Demo Presentation Timeline Overview

| Timestamp | Phase | Core Feature Demonstrated | Target Audience / Role |
| :---: | :--- | :--- | :--- |
| **0:00 – 0:45** | Introduction & Problem Context | The GreenLeaf Grocers Retail Challenge | Evaluators / Mentors |
| **0:45 – 1:30** | Role-Based Access & Inventory | Admin Login, Stock Alerts & Expiry Tracking | Store Manager (Admin) |
| **1:30 – 2:45** | Point of Sale (POS) Checkout | Live Cart, Atomic Checkout, Thermal Receipt | Cashier / Customer |
| **2:45 – 3:45** | Data Analytics & BI Dashboard | 5 KPIs, Chart.js Views & Revenue/Qty Toggle | Executive / Store Owner |
| **3:45 – 4:15** | Supplier Management & Edge Cases | Vendor Linking, Defensive Validation | Operations Manager |
| **4:15 – 5:00** | Quality Assurance & Conclusion | 60/60 Automated Tests & Project Summary | Engineering Lead |

---

## 🎙 Detailed Script & Action Walkthrough

---

### Step 1: Introduction & Problem Context (0:00 – 0:45)

**Action**: Open browser to `http://127.0.0.1:5000/auth/login`. Have the terminal visible in the background showing the running application.

**Say (Narration)**:
> "Good morning, everyone. Welcome to the final demonstration of the **GreenLeaf Grocers Inventory & Sales Management System with Analytics Dashboard**.
>
> GreenLeaf Grocers is a regional fresh food retailer specializing in organic produce, bakery, and dairy products. Prior to this system, store operations relied on manual paper logs and disconnected cash registers. This caused three major pain points: frequent stock-outs of high-demand items, high shrinkage from expired dairy and produce, and zero visibility into sales trends.
>
> Over this 8-day engineering internship, we designed and built an end-to-end, full-stack solution using **Python, Flask, SQLite, Pandas, and Chart.js**. Let me walk you through how the system works in practice."

---

### Step 2: Role-Based Authentication & Live Inventory (0:45 – 1:30)

**Action**:
1. Enter Username: `admin` | Password: `admin123` $\to$ Click **Sign In**.
2. Click **Inventory & Stock** in the left sidebar (`/products/`).
3. Point out the color-coded alert badges (🔴 Low-Stock and 🟡 Near-Expiry countdown).
4. Type `Organic` into the search box or filter by `Dairy & Eggs`.

**Say (Narration)**:
> "We start at the login gateway, which implements role-based access control with PBKDF2 salted password hashing. Signing in as the **Store Administrator**, we land on the **Inventory & Stock Catalog**.
>
> Notice the proactive visual indicators:
> - **Red Badges** flag items that have dropped below their minimum reorder threshold, such as *Organic Whole Milk*, alerting staff to restock immediately.
> - **Yellow Badges** display dynamic countdowns for products nearing expiration within the next 15 days, helping us discount perishables before they spoil.
>
> The catalog supports real-time search, category filtering, one-click CSV export, and bulk CSV uploads for vendor catalog updates."

---

### Step 3: Point of Sale (POS) Checkout & Invoicing (1:30 – 2:45)

**Action**:
1. Click **Point of Sale (POS)** in the sidebar (`/billing/pos`).
2. Add 2 units of *Organic Bananas* ($1.99 each) and 1 unit of *Greek Yogurt* ($4.49).
3. In the checkout panel, apply a `$0.50` promotional discount.
4. Click **Complete Checkout**.
5. The browser redirects to the generated **Thermal Invoice Receipt** (`/billing/invoice/<sale_id>`).
6. Point out the clean receipt format, click **Print Thermal Receipt** (show browser print preview with navigation hidden), then click **Export CSV**.

**Say (Narration)**:
> "Now, let’s switch to daily retail operations at the **Point of Sale Terminal**.
>
> As items are added to the cart, the system dynamically calculates line subtotals and gross totals using client-side JavaScript, while validating that quantities do not exceed available on-hand stock.
>
> When I click **Complete Checkout**, the backend executes an **atomic SQLite transaction**:
> 1. It verifies stock levels in real time to prevent overselling.
> 2. It creates the permanent sales ledger record with the active cashier ID.
> 3. It automatically decrements physical stock for every line item.
>
> The cashier is immediately presented with a professional **Thermal Supermarket Receipt**. It includes a printable CSS layout that strips out all web navigation for 80mm receipt printers, alongside a one-click CSV export for accounting reconciliation."

---

### Step 4: Executive Business Intelligence & Interactive Charts (2:45 – 3:45)

**Action**:
1. Click **Sales Analytics** in the sidebar (`/reports/`).
2. Highlight the **5 KPI summary cards** at the top of the page.
3. Scroll to the **Interactive Charts**:
   - Hover over the **Daily Revenue & Bill Count Trend line chart**.
   - Hover over the **Department Revenue Share doughnut chart**.
   - On the **Top 10 Best Sellers chart**, click the **Toggle View button** to switch from **Revenue ($)** to **Units Sold**.
4. Click the **Last 30 Days** quick preset button.
5. Scroll down to show the **Slow-Moving / Dead Inventory Watchlist** table.

**Say (Narration)**:
> "Now let's examine the core analytical engine. In the **Sales Analytics Hub**, our backend leverages **Pandas** to process transaction data in-memory, calculating five core business KPIs:
> - **Total Gross Revenue**
> - **Average Bill Value (Basket Size)**
> - **Stock Turnover Ratio** — measuring how rapidly inventory turns into cash
> - **Low-Stock Alert Count**
> - **Top Department Market Share**
>
> Below the KPIs are three responsive **Chart.js** visualizations:
> - A dual-axis **Sales Revenue & Bill Volume Timeline** identifying peak shopping periods.
> - A **Department Share Doughnut Chart** showing revenue distribution across grocery categories.
> - A **Top 10 Best Sellers Chart** equipped with an interactive client-side toggle: with one click, management can switch between **Revenue Generated** and **Total Units Sold**.
>
> We also provide quick date presets (`7D`, `30D`, `90D`, `All Time`) and a **Slow-Moving Inventory Watchlist** highlighting items with zero recent sales, giving store managers the exact data needed to run targeted clearance promotions."

---

### Step 5: Supplier Directory & Defensive Validation (3:45 – 4:15)

**Action**:
1. Click **Suppliers** in the sidebar (`/suppliers/`).
2. Point out the vendor list with contact info and the **Supplied Products count badge**.
3. Mention role-based restrictions: *If logged in as a cashier, administrative pages like Suppliers, Reports, and Inventory editing are blocked with a secure 403 Forbidden redirect.*

**Say (Narration)**:
> "Under **Suppliers**, the application maintains wholesale distributor partnerships with active product count linkages and safe foreign key constraints (`ON DELETE SET NULL`) so supplier updates never corrupt existing product records.
>
> The system enforces strict defensive programming: negative prices or stock quantities are rejected at both the database and form layers, inverted date inputs are automatically normalized, and cashiers are strictly prevented from accessing management settings."

---

### Step 6: Automated Test Suite & Conclusion (4:15 – 5:00)

**Action**:
1. Switch to the terminal window.
2. Run the master test runner:
   ```powershell
   python run_all_tests.py
   ```
3. Show the green summary output: **60 Tests Run | 0 Failures | 0 Errors | 100% Pass Rate**.
4. Return to the browser or show the generated `test_report.md`.

**Say (Narration)**:
> "To guarantee production readiness, we built a comprehensive test suite of **60 automated unit tests** covering database constraints, session authentication, product CRUD, atomic POS checkouts, Pandas KPI math, and Chart.js data endpoints.
>
> As shown on screen, running `python run_all_tests.py` verifies all 60 tests across 7 test modules with a **100% pass rate** in just over 6 seconds, automatically compiling our formatted `test_report.md`.
>
> In summary, GreenLeaf Grocers now has an automated, secure, and data-driven platform that streamlines checkouts, eliminates stock-outs, and provides executive-level business intelligence.
>
> Thank you, and I am happy to answer any questions!"

---

## 💡 Mentor & Evaluator Q&A Cheat Sheet

Prepare confident, technically precise answers for anticipated questions:

### Q1: "How do you handle concurrency or race conditions if two cashiers checkout the last remaining item simultaneously?"
> **Answer**: "The checkout logic in `Sale.process_checkout()` is wrapped inside an **atomic SQLite database transaction**. Before committing the sale, the query locks the row and checks `stock_qty >= requested_qty`. If another cashier commits milliseconds earlier, the second checkout triggers an `InsufficientStockError`, the entire transaction automatically rolls back (`conn.rollback()`), and the cashier receives a descriptive error without corrupting inventory or creating negative stock."

### Q2: "Why did you use Pandas for analytics rather than writing aggregate SQL queries?"
> **Answer**: "While SQLite handles transactional operations (OLTP) very well, analytical operations (OLAP) — such as computing stock turnover ratios, rolling date filtering, and multi-dimensional aggregations for Chart.js — are significantly faster and cleaner in-memory with Pandas. Using Pandas also decouples business intelligence calculations from the database schema, making it straightforward to add predictive forecasting or export complex analytical DataFrames in future sprints."

### Q3: "How is user authentication secured? Are passwords safe?"
> **Answer**: "Passwords are never stored in plaintext. We implement salted cryptographic hashing using `werkzeug.security` (PBKDF2 with SHA-256) with a fallback to Python's standard `hashlib.pbkdf2_hmac` using a 16-byte random salt and 100,000 hashing iterations. In addition, route access is protected by backend decorators (`@login_required` and `@admin_required`) that inspect server-side session cookies to prevent unauthorized URL traversal."

### Q4: "How do your automated unit tests run without wiping out your production database?"
> **Answer**: "Our database connection factory `get_db_connection()` dynamically checks `current_app.config['DATABASE_PATH']`. When unit tests initialize, they create an isolated temporary SQLite database (e.g. `test_billing.db`) populated with fresh test fixtures in their `setUp()` method, and tear it down cleanly in `tearDown()`. The production `greenleaf.db` is never touched by the test runner."

### Q5: "What prevents cashiers from tampering with prices or discounts during checkout?"
> **Answer**: "The POS cart stores only `product_id` and `quantity` from the client. When submitted to `/billing/checkout`, the backend re-fetches the authoritative `unit_price` directly from the database to compute gross totals. Furthermore, discounts are validated on the server to ensure they cannot be negative or exceed the total bill amount."

### Q6: "How does the near-expiry alert calculate its threshold?"
> **Answer**: "In `app/models.py`, `Product.get_near_expiry()` calculates the difference between `expiry_date` and `date.today()`. Any item expiring within 15 days is flagged with the days remaining, and expired products ($\le 0$ days) are explicitly highlighted so staff can pull them off retail shelves."