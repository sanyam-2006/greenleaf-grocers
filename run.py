"""
Application entry point for GreenLeaf Grocers.
Run with: python run.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app
from app.database import init_db

app = create_app()

# Ensure database tables exist upon application load (for Gunicorn & WSGI)
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("==================================================")
    print(" GreenLeaf Grocers Web Application Started")
    print(f" Listening on http://0.0.0.0:{port}")
    print(" Admin:   username: admin    | password: admin123")
    print(" Cashier: username: cashier1 | password: cashier123")
    print("==================================================")
    app.run(host="0.0.0.0", port=port, debug=False)