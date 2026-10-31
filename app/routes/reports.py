"""
Analytics and Reporting routes:
KPI metrics display, sales performance tables, JSON data APIs, and CSV report export.
"""
import csv
import io
from flask import (
    Blueprint, render_template, request, jsonify, Response, redirect, url_for
)
from app.auth_utils import admin_required
from app.analytics import AnalyticsEngine

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@admin_required
def index():
    """Renders the executive Analytics & Reports hub with interactive charts and KPIs."""
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None
    sort_by = request.args.get("sort_by", "revenue").strip()
    if sort_by not in ("revenue", "quantity"):
        sort_by = "revenue"

    # Compute analytics datasets via Pandas engine
    kpis = AnalyticsEngine.get_kpis(start_date=start_date, end_date=end_date)
    top_products_rev = AnalyticsEngine.get_top_products(start_date=start_date, end_date=end_date, limit=10, sort_by="revenue")
    top_products_qty = AnalyticsEngine.get_top_products(start_date=start_date, end_date=end_date, limit=10, sort_by="quantity")
    category_breakdown = AnalyticsEngine.get_category_breakdown(start_date=start_date, end_date=end_date)
    slow_moving = AnalyticsEngine.get_slow_moving_products(start_date=start_date, end_date=end_date, limit=10)
    sales_trend = AnalyticsEngine.get_sales_trend(start_date=start_date, end_date=end_date)

    top_products = top_products_rev if sort_by == "revenue" else top_products_qty

    return render_template(
        "reports/index.html",
        kpis=kpis,
        top_products=top_products,
        top_products_rev=top_products_rev,
        top_products_qty=top_products_qty,
        category_breakdown=category_breakdown,
        slow_moving=slow_moving,
        sales_trend=sales_trend,
        start_date=start_date or "",
        end_date=end_date or "",
        sort_by=sort_by
    )


@reports_bp.route("/api/summary")
@admin_required
def api_summary():
    """Returns JSON payload of all analytics datasets for Chart.js interactive rendering."""
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None

    kpis = AnalyticsEngine.get_kpis(start_date=start_date, end_date=end_date)
    sales_trend = AnalyticsEngine.get_sales_trend(start_date=start_date, end_date=end_date)
    category_breakdown = AnalyticsEngine.get_category_breakdown(start_date=start_date, end_date=end_date)
    top_products_rev = AnalyticsEngine.get_top_products(start_date=start_date, end_date=end_date, limit=10, sort_by="revenue")
    top_products_qty = AnalyticsEngine.get_top_products(start_date=start_date, end_date=end_date, limit=10, sort_by="quantity")

    return jsonify({
        "status": "success",
        "kpis": kpis,
        "sales_trend": sales_trend,
        "category_breakdown": category_breakdown,
        "top_products_revenue": top_products_rev,
        "top_products_quantity": top_products_qty
    })


@reports_bp.route("/export/<report_type>")
@admin_required
def export_csv(report_type):
    """Generates and downloads on-demand CSV spreadsheets of analytics reports."""
    start_date = request.args.get("start_date", "").strip() or None
    end_date = request.args.get("end_date", "").strip() or None

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "daily_sales":
        trend = AnalyticsEngine.get_sales_trend(start_date=start_date, end_date=end_date)
        writer.writerow(["Date", "Total Revenue ($)", "Bills Count", "Discounts ($)", "Average Ticket ($)"])
        for r in trend:
            writer.writerow([r["sale_date"], f"{r['revenue']:.2f}", r["bills_count"], f"{r['discounts']:.2f}", f"{r['avg_ticket']:.2f}"])
        filename = "greenleaf_daily_sales_report.csv"

    elif report_type == "categories":
        cats = AnalyticsEngine.get_category_breakdown(start_date=start_date, end_date=end_date)
        writer.writerow(["Category", "Total Revenue ($)", "Quantity Sold", "Revenue Share (%)"])
        for c in cats:
            writer.writerow([c["category"], f"{c['revenue']:.2f}", c["quantity_sold"], f"{c['share_pct']:.1f}%"])
        filename = "greenleaf_category_performance_report.csv"

    elif report_type == "top_products":
        prods = AnalyticsEngine.get_top_products(start_date=start_date, end_date=end_date, limit=50)
        writer.writerow(["Product ID", "Product Name", "Category", "Unit Price ($)", "Quantity Sold", "Total Revenue ($)"])
        for p in prods:
            writer.writerow([p["product_id"], p["name"], p["category"], f"{p['unit_price']:.2f}", p["total_qty"], f"{p['total_revenue']:.2f}"])
        filename = "greenleaf_top_products_report.csv"

    elif report_type == "slow_moving":
        slow = AnalyticsEngine.get_slow_moving_products(start_date=start_date, end_date=end_date, limit=50)
        writer.writerow(["Product ID", "Product Name", "Category", "Stock Qty", "Units Sold", "Revenue ($)", "Stock Valuation ($)"])
        for s in slow:
            writer.writerow([s["product_id"], s["name"], s["category"], s["stock_qty"], s["units_sold"], f"{s['revenue_generated']:.2f}", f"{s['stock_valuation']:.2f}"])
        filename = "greenleaf_slow_moving_inventory_report.csv"

    else:
        return jsonify({"error": "Unknown report type specified."}), 400

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )