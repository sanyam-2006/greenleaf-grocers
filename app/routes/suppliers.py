"""
Supplier Directory and Vendor Management routes:
CRUD operations, vendor directory listing, and contact updates.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.auth_utils import admin_required
from app.models import Supplier

suppliers_bp = Blueprint("suppliers", __name__, url_prefix="/suppliers")


@suppliers_bp.route("/")
@admin_required
def index():
    """Lists all grocery suppliers and their catalog product counts."""
    suppliers = Supplier.get_all_with_counts()
    return render_template("suppliers/index.html", suppliers=suppliers)


@suppliers_bp.route("/add", methods=["POST"])
@admin_required
def add():
    """Adds a new wholesale grocery vendor."""
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()

    if not name or not phone:
        flash("Supplier name and phone number are required.", "warning")
        return redirect(url_for("suppliers.index"))

    try:
        Supplier.create(name=name, phone=phone, email=email)
        flash(f"Supplier '{name}' registered successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error registering supplier: {str(e)}", "danger")

    return redirect(url_for("suppliers.index"))


@suppliers_bp.route("/edit/<int:supplier_id>", methods=["POST"])
@admin_required
def edit(supplier_id):
    """Updates contact details for an existing supplier."""
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()

    if not name or not phone:
        flash("Supplier name and phone number cannot be empty.", "warning")
        return redirect(url_for("suppliers.index"))

    try:
        updated = Supplier.update(supplier_id=supplier_id, name=name, phone=phone, email=email)
        if updated:
            flash(f"Supplier '{name}' updated successfully!", "success")
        else:
            flash("Supplier not found or no changes made.", "warning")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        flash(f"Error updating supplier: {str(e)}", "danger")

    return redirect(url_for("suppliers.index"))


@suppliers_bp.route("/delete/<int:supplier_id>", methods=["POST"])
@admin_required
def delete(supplier_id):
    """Removes a supplier (linked products will have supplier set to NULL)."""
    try:
        deleted = Supplier.delete(supplier_id)
        if deleted:
            flash("Supplier removed successfully. Associated products were preserved.", "success")
        else:
            flash("Supplier not found.", "warning")
    except Exception as e:
        flash(f"Error deleting supplier: {str(e)}", "danger")

    return redirect(url_for("suppliers.index"))