# Purpose - The main executable script that brings the entire application to life:
# Adds the project root to sys.path so modules resolve cleanly.
# Invokes init_db() to guarantee database tables exist before web traffic arrives.
# Displays a formatted banner in your console showing the local host URL (http://127.0.0.1:5000) and the default login credentials (admin/admin123 and cashier1/cashier123).
# Starts the local server with active hot-reload (debug=True).


"""
Application entry point for GreenLeaf Grocers.
Run with: python run.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app
from app.database import init_db

app = create_app()

if __name__ == "__main__":
    init_db()  # Ensure database tables exist
    print("==================================================")
    print(" GreenLeaf Grocers Web Application Started")
    print(" URL: http://127.0.0.1:5000")
    print(" Admin:   username: admin    | password: admin123")
    print(" Cashier: username: cashier1 | password: cashier123")
    print("==================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)