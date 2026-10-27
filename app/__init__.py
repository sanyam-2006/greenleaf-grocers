# Purpose - Replaces the basic package file with the industry-standard Application Factory Pattern (create_app):
#Instantiates and configures the Flask application.
# Uses @app.context_processor to inject current user session variables (current_username, current_role, is_admin, is_cashier) into every Jinja2 template automatically, avoiding having to pass them in every view function.
# Registers custom HTTP error handlers (404 Not Found, 403 Forbidden, 500 Server Error) to fulfill the project requirement of “Show friendly error messages and never crash on bad input”.
# Registers the auth_bp and main_bp Blueprints.


"""
GreenLeaf Grocers Application Factory.
"""
from flask import Flask, session, render_template
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Context processor to inject user session info into all Jinja templates
    @app.context_processor
    def inject_user_context():
        return {
            "current_user_id": session.get("user_id"),
            "current_username": session.get("username"),
            "current_role": session.get("role"),
            "is_admin": session.get("role") == "admin",
            "is_cashier": session.get("role") == "cashier",
            "is_authenticated": "user_id" in session
        }

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app