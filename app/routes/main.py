"""
Main dashboard and navigation routes.
"""
from flask import Blueprint, render_template, redirect, url_for, session
from app.auth_utils import login_required, admin_required, cashier_required
from app.database import get_db_connection
from app.models import Product

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Root URL redirector based on authentication state and role."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("role") == "admin":
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("billing.pos"))


@main_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin Executive Dashboard: Overview of inventory status and sales health."""
    conn = get_db_connection()
    try:
        # Key Counts
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_suppliers = conn.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0]
        total_sales = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        total_revenue = conn.execute("SELECT COALESCE(SUM(final_amount), 0.0) FROM sales").fetchone()[0]

        # Inventory Alerts
        low_stock_items = Product.get_low_stock()
        near_expiry_items = Product.get_near_expiry(days=15)

        # Recent 5 Sales
        recent_sales = conn.execute(
            """
            SELECT s.sale_id, s.sale_date, s.sale_time, s.final_amount, u.username as cashier
            FROM sales s
            JOIN users u ON s.user_id = u.user_id
            ORDER BY s.sale_date DESC, s.sale_time DESC
            LIMIT 5
            """
        ).fetchall()

        stats = {
            "total_products": total_products,
            "total_suppliers": total_suppliers,
            "total_sales": total_sales,
            "total_revenue": round(total_revenue, 2),
            "low_stock_count": len(low_stock_items),
            "near_expiry_count": len(near_expiry_items),
            "low_stock_items": low_stock_items[:5],
            "near_expiry_items": near_expiry_items[:5],
            "recent_sales": [dict(r) for r in recent_sales]
        }
    finally:
        conn.close()

    return render_template("dashboard.html", stats=stats)


@main_bp.route("/billing")
@cashier_required
def billing_home():
    """Redirects to the Point of Sale (POS) terminal."""
    return redirect(url_for("billing.pos"))