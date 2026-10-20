"""Blueprint 'admin_pengguna': kelola akun pengguna."""
from flask import Blueprint, abort, current_app, flash, g, redirect, request, url_for

import admin_data
from admin_data import AdminError
from blueprints.admin import _render
from security import admin_required

bp = Blueprint("admin_pengguna", __name__, url_prefix="/admin/pengguna")

PER_PAGE = 20


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@bp.route("/")
@admin_required
def index():
    role = request.args.get("role", "")
    status = request.args.get("status", "")
    q = request.args.get("q", "").strip()[:50]
    page = max(1, _int(request.args.get("page"), 1))
    rows, total = admin_data.list_users(q or None, role or None, status or None, page, PER_PAGE)
    return _render(
        "admin/users.html", "pengguna", rows=rows, total=total, page=page,
        pages=max(1, -(-total // PER_PAGE)), role=role, status=status, q=q,
    )


def _apply(user_id, action, success, **changes):
    try:
        admin_data.set_user_state(g.user["id"], user_id, **changes)
    except AdminError as exc:
        flash(str(exc), "error")
    else:
        current_app.logger.info(
            "ADMIN_ACTION admin_id=%s action=%s user=%s ip=%s",
            g.user["id"], action, user_id, request.remote_addr,
        )
        flash(success, "success")
    return redirect(request.form.get("back") if (request.form.get("back") or "").startswith("/admin/pengguna") else url_for("admin_pengguna.index"))


@bp.route("/<int:user_id>/status", methods=["POST"])
@admin_required
def toggle_active(user_id):
    active = request.form.get("active")
    if active not in ("0", "1"):
        abort(400)
    ok_msg = "Akun diaktifkan." if active == "1" else "Akun dinonaktifkan. Pengguna tidak bisa masuk lagi."
    return _apply(user_id, "user_activate" if active == "1" else "user_deactivate", ok_msg, active=(active == "1"))


@bp.route("/<int:user_id>/peran", methods=["POST"])
@admin_required
def change_role(user_id):
    role = request.form.get("role", "")
    if role not in ("customer", "admin"):
        flash("Peran tidak valid.", "error")
        return redirect(url_for("admin_pengguna.index"))
    return _apply(user_id, "user_role_%s" % role, "Peran diubah menjadi %s." % role, role=role)
