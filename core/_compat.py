"""
_compat.py — Universal environment & encoding compatibility layer.
Ensures stdout/stderr handle UTF-8 symbols on Windows consoles without cp1252 charmap errors.
"""
import sys

def init_encoding():
    """Ensure standard output streams are configured for UTF-8."""
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure") and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Automatically initialize on import
init_encoding()
