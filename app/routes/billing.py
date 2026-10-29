"""
Point of Sale (POS) and Billing routes:
Multi-item cart, atomic transactional stock deduction, receipts, and CSV export.
"""
import csv
import io
import json
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, Response
)
from app.auth_utils import cashier_required
from app.models import Product, Sale

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.route("/")
@billing_bp.route("/pos")
@cashier_required
def pos():
    """Renders the interactive Point of Sale (POS) terminal."""
    # Only show products with positive stock for checkout
    products = Product.get_all()
    available_products = [p for p in products if p["stock_qty"] > 0]
    categories = sorted(list({p["category"] for p in products}))

    return render_template(
        "billing/pos.html",
        products=available_products,
        categories=categories
    )


@billing_bp.route("/checkout", methods=["POST"])
@cashier_required
def checkout():
    """Processes customer checkout atomically with stock decrement."""
    data = request.get_json(silent=True) or request.form

    items = data.get("items")
    discount_val = data.get("discount", 0.0)

    # Convert items if passed as string/form data
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            return jsonify({"success": False, "error": "Invalid cart items format."}), 400

    if not items:
        return jsonify({"success": False, "error": "Cart is empty. Add products before checking out."}), 400

    try:
        discount = float(discount_val) if discount_val else 0.0
    except ValueError:
        return jsonify({"success": False, "error": "Invalid discount amount."}), 400

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "User session expired. Please log in again."}), 401

    try:
        result = Sale.process_checkout(
            user_id=user_id,
            items=items,
            discount=discount
        )
        return jsonify({
            "success": True,
            "sale_id": result["sale_id"],
            "redirect_url": url_for("billing.invoice", sale_id=result["sale_id"])
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Internal error processing checkout: {str(e)}"}), 500


@billing_bp.route("/invoice/<int:sale_id>")
@billing_bp.route("/receipt/<int:sale_id>")
@cashier_required
def invoice(sale_id):
    """Renders the formatted digital receipt / bill for printing and inspection."""
    sale = Sale.get_by_id(sale_id)
    if not sale:
        flash("Invoice not found.", "warning")
        return redirect(url_for("billing.pos"))

    # Provide line_items as well so both sale['items'] and sale.line_items work in templates
    if isinstance(sale, dict):
        sale["line_items"] = sale.get("items", [])

    return render_template("billing/invoice.html", sale=sale)


@billing_bp.route("/invoice/<int:sale_id>/csv")
@billing_bp.route("/receipt/<int:sale_id>/csv")
@cashier_required
def export_invoice_csv(sale_id):
    """Exports an individual sales bill to downloadable CSV format."""
    sale = Sale.get_by_id(sale_id)
    if not sale:
        flash("Invoice not found.", "warning")
        return redirect(url_for("billing.pos"))

    output = io.StringIO()
    writer = csv.writer(output)

    # Receipt Header
    writer.writerow(["GreenLeaf Grocers - Retail Invoice"])
    writer.writerow(["Invoice Number", f"INV-{sale['sale_id']:04d}"])
    writer.writerow(["Date", sale["sale_date"]])
    writer.writerow(["Time", sale["sale_time"]])
    writer.writerow(["Cashier", sale.get("cashier_name", "Staff")])
    writer.writerow([])

    # Line Items
    writer.writerow(["#", "Product Name", "Category", "Unit Price", "Quantity", "Line Total"])
    for idx, it in enumerate(sale["items"], 1):
        line_total = it["price"] * it["quantity"]
        writer.writerow([
            idx,
            it["product_name"],
            it["category"],
            f"${it['price']:.2f}",
            it["quantity"],
            f"${line_total:.2f}"
        ])

    writer.writerow([])
    writer.writerow(["", "", "", "", "Subtotal", f"${sale['total_amount']:.2f}"])
    writer.writerow(["", "", "", "", "Discount", f"-${sale['discount']:.2f}"])
    writer.writerow(["", "", "", "", "Final Total Paid", f"${sale['final_amount']:.2f}"])

    output.seek(0)
    filename = f"invoice_INV-{sale['sale_id']:04d}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )