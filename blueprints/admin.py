"""Blueprint 'admin': panel admin (dashboard, pesanan, verifikasi pembayaran)."""
import re

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

import admin_data
from admin_data import AdminError
from security import admin_required
from store_config import STATUS_LABELS

bp = Blueprint("admin", __name__, url_prefix="/admin")

# Tab navigasi panel admin: (kunci, label, endpoint).
ADMIN_TABS = [
    ("dashboard", "Dashboard", "admin.dashboard"),
    ("orders", "Pesanan", "admin.orders"),
    ("produk", "Produk", "admin_produk.index"),
    ("pengguna", "Pengguna", "admin_pengguna.index"),
    ("laporan", "Laporan", "admin_laporan.index"),
]

RESI_RE = re.compile(r"^[A-Za-z0-9\-]{5,50}$")
PER_PAGE = 20


def _render(template, tab, **ctx):
    return render_template(template, admin_tabs=ADMIN_TABS, admin_tab=tab, active_page="admin", **ctx)


def _log(action, order_no):
    current_app.logger.info(
        "ADMIN_ACTION admin_id=%s action=%s order=%s ip=%s",
        g.user["id"], action, order_no, request.remote_addr,
    )


def _back(order_no):
    return redirect(url_for("admin.order_detail", order_no=order_no))


# ---------------------------------------------------------------------------
# Dashboard & daftar pesanan
# ---------------------------------------------------------------------------
@bp.route("/")
@admin_required
def dashboard():
    return _render("admin/dashboard.html", "dashboard", stats=admin_data.dashboard())


@bp.route("/pesanan")
@admin_required
def orders():
    status = request.args.get("status", "")
    if status not in STATUS_LABELS:
        status = ""
    q = request.args.get("q", "").strip()[:50]
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1

    rows, total = admin_data.list_orders(status or None, q or None, page, PER_PAGE)
    return _render(
        "admin/orders.html",
        "orders",
        rows=rows,
        total=total,
        page=page,
        pages=max(1, -(-total // PER_PAGE)),
        status=status,
        q=q,
        counts=admin_data.status_counts(),
    )


@bp.route("/pesanan/<order_no>")
@admin_required
def order_detail(order_no):
    order = admin_data.get_order(order_no)
    if order is None:
        abort(404)
    return _render("admin/order_detail.html", "orders", order=order)


# ---------------------------------------------------------------------------
# Aksi pada pesanan (semua POST + CSRF)
# ---------------------------------------------------------------------------
def _run(order_no, action, success, func, *args):
    try:
        func(*args)
    except AdminError as exc:
        flash(str(exc), "error")
    else:
        _log(action, order_no)
        flash(success, "success")
    return _back(order_no)


@bp.route("/pesanan/<order_no>/setujui", methods=["POST"])
@admin_required
def approve(order_no):
    return _run(order_no, "approve", "Pembayaran disetujui. Stok dikurangi dan pesanan diproses.",
                admin_data.approve_payment, order_no, g.user["id"])


@bp.route("/pesanan/<order_no>/tolak", methods=["POST"])
@admin_required
def reject(order_no):
    reason = request.form.get("reason", "").strip()
    if not reason or len(reason) > 255:
        flash("Alasan penolakan wajib diisi (maksimal 255 karakter).", "error")
        return _back(order_no)
    return _run(order_no, "reject", "Bukti pembayaran ditolak. Pembeli diminta mengunggah ulang.",
                admin_data.reject_payment, order_no, g.user["id"], reason)


@bp.route("/pesanan/<order_no>/kirim", methods=["POST"])
@admin_required
def ship(order_no):
    resi = request.form.get("resi", "").strip().upper()
    if not RESI_RE.match(resi):
        flash("Nomor resi tidak valid (5-50 karakter: huruf, angka, atau tanda hubung).", "error")
        return _back(order_no)
    return _run(order_no, "ship", "Pesanan ditandai dikirim.", admin_data.ship_order, order_no, resi)


@bp.route("/pesanan/<order_no>/selesai", methods=["POST"])
@admin_required
def complete(order_no):
    return _run(order_no, "complete", "Pesanan ditandai selesai.", admin_data.complete_order, order_no)


@bp.route("/pesanan/<order_no>/batal", methods=["POST"])
@admin_required
def cancel(order_no):
    reason = request.form.get("reason", "").strip()
    if not reason or len(reason) > 200:
        flash("Alasan pembatalan wajib diisi (maksimal 200 karakter).", "error")
        return _back(order_no)
    return _run(order_no, "cancel", "Pesanan dibatalkan.", admin_data.cancel_order, order_no, reason)
