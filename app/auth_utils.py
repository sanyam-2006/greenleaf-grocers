"""
Authentication helpers and role-based access control (RBAC) decorators.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, abort, request


def login_required(f):
    """Restricts route access to logged-in users."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.endpoint))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Restricts route access strictly to Admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.endpoint))
        if session.get("role") != "admin":
            flash("Access denied. Admin privileges required.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def cashier_required(f):
    """Restricts route access to cashiers and admins."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.endpoint))
        if session.get("role") not in ("cashier", "admin"):
            flash("Access denied. Authorized billing staff only.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function