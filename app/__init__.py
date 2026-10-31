"""
GreenLeaf Grocers Application Factory.
"""
try:
    from flask import Flask, session, render_template
    from config import Config
except ImportError:
    Flask = None
    session = {}
    render_template = None
    Config = None


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
    from app.routes.products import products_bp
    from app.routes.billing import billing_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(reports_bp)

    return app