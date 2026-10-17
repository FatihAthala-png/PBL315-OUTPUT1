"""Helper keamanan: dekorator login & admin, validasi redirect."""
from functools import wraps
from urllib.parse import urlparse

from flask import abort, g, redirect, request, url_for


def safe_next(target):
    """Terima hanya path internal ('/...'); tolak URL luar (open redirect)."""
    if not target or not target.startswith("/"):
        return None
    if target.startswith("//") or "\\" in target:
        return None
    parts = urlparse(target)
    if parts.scheme or parts.netloc:
        return None
    return target


def _to_login():
    nxt = request.full_path.rstrip("?") if request.method == "GET" else None
    return redirect(url_for("auth.login", next=nxt))


def login_required(view):
    """Halaman hanya untuk user yang sudah login."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if g.get("user") is None:
            return _to_login()
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    """Halaman hanya untuk admin (user biasa dapat 403)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = g.get("user")
        if user is None:
            return _to_login()
        if user["role"] != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapper
