# Purpose - Implements Role-Based Access Control (RBAC) using reusable Python decorators:
# - @login_required: Checks if user_id exists in the session. If an unauthenticated user attempts to access any internal page, it blocks access, flashes a warning message, and redirects them to the login screen.
# - @admin_required: Gating decorator for managers. Confirms the user's role is strictly admin. If a cashier attempts to access the Executive Dashboard or inventory editing routes, it blocks them, flashes an "Access denied. Admin privileges required." alert, and redirects them to safety.
# - @cashier_required: Protects billing routes, permitting both billing cashiers and administrators to operate the Point of Sale terminal.


"""
Authentication helpers and role-based access control (RBAC) decorators.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request

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
            return redirect(url_for("main.index"))
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
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function