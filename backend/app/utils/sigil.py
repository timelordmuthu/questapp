"""
backend/app/utils/sigil.py

Sigil code generator — 8-char uppercase alphanumeric (AD-08).
"""

import secrets
import string


def generate_sigil_code() -> str:
    """Generate a cryptographically random 8-char uppercase alphanumeric code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(8))
