# Purpose: Provides password hashing (generate_password_hash) and verification (check_password_hash). If werkzeug is installed (with Flask), it uses it; otherwise, it uses Python's built-in hashlib.pbkdf2_hmac so the project works under any circumstance.

"""
Utility functions for security, hashing, and formatting.
Uses werkzeug if available, otherwise falls back to Python standard library hashlib (pbkdf2_hmac).
"""
import os
import hmac
import hashlib

try:
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    # Standard library fallback if werkzeug is not yet installed
    def generate_password_hash(password: str) -> str:
        """Generates a secure salt + pbkdf2_sha256 hash."""
        salt = os.urandom(16).hex()
        dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"pbkdf2:sha256:100000${salt}${dk.hex()}"

    def check_password_hash(pwhash: str, password: str) -> bool:
        """Verifies a password against the stored pbkdf2 hash."""
        try:
            method, salt, hash_val = pwhash.split('$')
            _, algo, iterations = method.split(':')
            dk = hashlib.pbkdf2_hmac(algo, password.encode('utf-8'), salt.encode('utf-8'), int(iterations))
            return hmac.compare_digest(dk.hex(), hash_val)
        except Exception:
            return False