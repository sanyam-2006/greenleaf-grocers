# Purpose - Centralizes application-wide configurations and environment variables in one place.
# Sets SECRET_KEY, which Flask uses to cryptographically sign session cookies. This prevents malicious users or cashiers from tampering with browser cookies to elevate their privileges to admin.
# Resolves the absolute system path to greenleaf.db so database operations work regardless of where the application is launched from.
# Enables DEBUG = True for instant code reloading and readable debugging logs during development.


"""
Application configuration for GreenLeaf Grocers.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "greenleaf-grocers-super-secret-internship-key-2026")
    DATABASE_PATH = BASE_DIR / "greenleaf.db"
    DEBUG = True