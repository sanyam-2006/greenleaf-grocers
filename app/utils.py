# Purpose: Provides password hashing (generate_password_hash) and verification (check_password_hash). If werkzeug is installed (with Flask), it uses it; otherwise, it uses Python's built-in hashlib.pbkdf2_hmac so the project works under any circumstance.

"""
Utility functions for security, hashing, and formatting.
Universally compatible with Werkzeug and standard library pbkdf2.
"""
import os
import hmac
import hashlib

try:
    from werkzeug.security import generate_password_hash as werkzeug_generate, check_password_hash as werkzeug_check
    HAS_WERKZEUG = True
except ImportError:
    HAS_WERKZEUG = False


def generate_password_hash(password: str) -> str:
    """Generates a secure password hash."""
    if HAS_WERKZEUG:
        return werkzeug_generate(password)
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"pbkdf2:sha256:100000${salt}${dk.hex()}"


def check_password_hash(pwhash: str, password: str) -> bool:
    """Verifies a password against the stored hash universally."""
    # 1. Try Werkzeug verifier
    if HAS_WERKZEUG:
        try:
            if werkzeug_check(pwhash, password):
                return True
        except Exception:
            pass

    # 2. Try Standard library pbkdf2 verifier
    try:
        method, salt, hash_val = pwhash.split('$')
        _, algo, iterations = method.split(':')
        dk = hashlib.pbkdf2_hmac(algo, password.encode('utf-8'), salt.encode('utf-8'), int(iterations))
        return hmac.compare_digest(dk.hex(), hash_val)
    except Exception:
        return False