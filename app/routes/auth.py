# Purpose - Houses all authentication and session lifecycle endpoints inside a dedicated Flask Blueprint("auth"):
# GET /auth/login: Renders the employee portal sign-in form. If a user is already logged in, it redirects them to their appropriate dashboard automatically.
# POST /auth/login: Retrieves submitted credentials, queries the SQLite database via User.get_by_username(), and verifies the password hash using PBKDF2/SHA-256. Upon success, it writes user_id, username, and role into Flask's encrypted session and routes admins to /dashboard and cashiers to /billing.
# GET /auth/logout: Clears the session dictionary, removes session cookies, flashes a goodbye confirmation, and returns to /auth/login.


"""
Authentication routes: Login, Logout, and Session Management.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect to appropriate home
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("main.billing_home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "warning")
            return render_template("auth/login.html")

        user = User.get_by_username(username)

        if not user or not user.check_password(password):
            flash("Invalid username or password. Please try again.", "danger")
            return render_template("auth/login.html", username=username)

        # Successfully authenticated - initialize session
        session.clear()
        session["user_id"] = user.user_id
        session["username"] = user.username
        session["role"] = user.role

        flash(f"Welcome back, {user.username}! Logged in as {user.role.capitalize()}.", "success")

        # Redirect based on role
        if user.is_admin:
            return redirect(url_for("main.dashboard"))
        else:
            return redirect(url_for("main.billing_home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    username = session.get("username", "User")
    session.clear()
    flash(f"You have been successfully logged out, {username}.", "info")
    return redirect(url_for("auth.login"))