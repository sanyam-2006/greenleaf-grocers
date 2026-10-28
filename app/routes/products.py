"""
Product and Inventory Management routes:
CRUD operations, Search & Category filtering, and CSV Import/Export.
"""
import csv
import io
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, Response
)
from app.auth_utils import login_required, admin_required
from app.models import Product, Supplier

products_bp = Blueprint("products", __name__, url_prefix="/products")

CATEGORIES = ["Dairy & Eggs", "Produce", "Bakery", "Beverages", "Pantry", "Snacks"]


@products_bp.route("/")
@login_required
def index():
    """Displays the product inventory catalog with search, filtering, and alert indicators."""
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category", "").strip()

    products = Product.get_all(
        category=category_filter if category_filter else None,
        search=search_query if search_query else None
    )
    suppliers = Supplier.get_all()

    # Pre-calculate days left for near-expiry highlight
    today = datetime.now().date()
    for p in products:
        try:
            exp_d = datetime.strptime(str(p["expiry_date"]), "%Y-%m-%d").date()
            p["days_left"] = (exp_d - today).days
        except Exception:
            p["days_left"] = 999

    return render_template(
        "products/index.html",
        products=products,
        suppliers=suppliers,
        categories=CATEGORIES,
        current_search=search_query,
        current_category=category_filter
    )


@products_bp.route("/add", methods=["POST"])
@admin_required
def add():
    """Creates a new product with business validation."""
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price_str = request.form.get("unit_price", "").strip()
    stock_str = request.form.get("stock_qty", "").strip()
    reorder_str = request.form.get("reorder_level", "10").strip()
    expiry_date = request.form.get("expiry_date", "").strip()
    supplier_id = request.form.get("supplier_id", "").strip() or None

    if not name or not category or not price_str or not stock_str or not expiry_date:
        flash("Please fill in all required product fields.", "warning")
        return redirect(url_for("products.index"))

    try:
        unit_price = float(price_str)
        stock_qty = int(stock_str)
        reorder_level = int(reorder_str)

        if unit_price < 0 or stock_qty < 0 or reorder_level < 0:
            flash("Price, stock quantity, and reorder level cannot be negative.", "danger")
            return redirect(url_for("products.index"))

        # Validate date format
        datetime.strptime(expiry_date, "%Y-%m-%d")

        Product.create(
            name=name,
            category=category,
            unit_price=unit_price,
            stock_qty=stock_qty,
            reorder_level=reorder_level,
            expiry_date=expiry_date,
            supplier_id=int(supplier_id) if supplier_id else None
        )
        flash(f"Product '{name}' added successfully to inventory!", "success")
    except ValueError as e:
        flash(f"Validation error: {str(e)}", "danger")

    return redirect(url_for("products.index"))


@products_bp.route("/edit/<int:product_id>", methods=["POST"])
@admin_required
def edit(product_id):
    """Updates an existing product."""
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price_str = request.form.get("unit_price", "").strip()
    stock_str = request.form.get("stock_qty", "").strip()
    reorder_str = request.form.get("reorder_level", "10").strip()
    expiry_date = request.form.get("expiry_date", "").strip()
    supplier_id = request.form.get("supplier_id", "").strip() or None

    if not name or not category or not price_str or not stock_str or not expiry_date:
        flash("All fields are required to update a product.", "warning")
        return redirect(url_for("products.index"))

    try:
        unit_price = float(price_str)
        stock_qty = int(stock_str)
        reorder_level = int(reorder_str)

        if unit_price < 0 or stock_qty < 0 or reorder_level < 0:
            flash("Price and stock values cannot be negative.", "danger")
            return redirect(url_for("products.index"))

        datetime.strptime(expiry_date, "%Y-%m-%d")

        success = Product.update(
            product_id=product_id,
            name=name,
            category=category,
            unit_price=unit_price,
            stock_qty=stock_qty,
            reorder_level=reorder_level,
            expiry_date=expiry_date,
            supplier_id=int(supplier_id) if supplier_id else None
        )

        if success:
            flash(f"Product '{name}' updated successfully!", "success")
        else:
            flash("Product not found.", "warning")
    except ValueError as e:
        flash(f"Validation error: {str(e)}", "danger")

    return redirect(url_for("products.index"))


@products_bp.route("/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete(product_id):
    """Deletes a product from the catalog."""
    product = Product.get_by_id(product_id)
    if product:
        Product.delete(product_id)
        flash(f"Product '{product['name']}' has been removed from catalog.", "info")
    else:
        flash("Product not found.", "warning")
    return redirect(url_for("products.index"))


@products_bp.route("/export")
@admin_required
def export_csv():
    """Exports the entire inventory catalog to a downloadable CSV file."""
    products = Product.get_all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Product ID", "Name", "Category", "Unit Price",
        "Stock Qty", "Reorder Level", "Expiry Date", "Supplier"
    ])

    for p in products:
        writer.writerow([
            p["product_id"],
            p["name"],
            p["category"],
            f"{p['unit_price']:.2f}",
            p["stock_qty"],
            p["reorder_level"],
            p["expiry_date"],
            p.get("supplier_name") or "None"
        ])

    output.seek(0)
    filename = f"greenleaf_inventory_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@products_bp.route("/import", methods=["POST"])
@admin_required
def import_csv():
    """Imports or updates products from an uploaded CSV file."""
    if "csv_file" not in request.files:
        flash("No file part in upload request.", "warning")
        return redirect(url_for("products.index"))

    file = request.files["csv_file"]
    if file.filename == "":
        flash("Please select a CSV file to upload.", "warning")
        return redirect(url_for("products.index"))

    if not file.filename.endswith(".csv"):
        flash("Invalid file format. Please upload a standard .csv file.", "danger")
        return redirect(url_for("products.index"))

    try:
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
        reader = csv.DictReader(stream)

        imported_count = 0
        for row in reader:
            r = {k.strip().lower().replace(" ", "_"): v.strip() for k, v in row.items() if k}

            name = r.get("name") or r.get("product_name")
            category = r.get("category", "Produce")
            price = float(r.get("unit_price") or r.get("price") or 0.0)
            stock = int(r.get("stock_qty") or r.get("stock") or 0)
            reorder = int(r.get("reorder_level") or r.get("reorder") or 10)
            expiry = r.get("expiry_date") or r.get("expiry") or datetime.now().strftime("%Y-%m-%d")

            if name and price >= 0 and stock >= 0:
                Product.create(
                    name=name,
                    category=category,
                    unit_price=price,
                    stock_qty=stock,
                    reorder_level=reorder,
                    expiry_date=expiry
                )
                imported_count += 1

        flash(f"Successfully imported {imported_count} products from CSV!", "success")
    except Exception as e:
        flash(f"Failed to parse CSV file: {str(e)}", "danger")

    return redirect(url_for("products.index"))