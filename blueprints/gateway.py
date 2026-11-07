"""Blueprint 'gateway': pembayaran online via Midtrans (Snap)."""
from flask import Blueprint, abort, current_app, flash, g, jsonify, redirect, request, url_for

import midtrans
import order_data
import payment_data
import ratelimit
from payment_data import PaymentError
from security import login_required

bp = Blueprint("gateway", __name__)


@bp.route("/pesanan/<order_no>/midtrans", methods=["POST"])
@login_required
def start(order_no):
    """Mulai pembayaran: mengembalikan token Snap untuk dibuka snap.js di browser."""
    if not midtrans.configured():
        return jsonify(ok=False, message="Pembayaran online belum diaktifkan."), 503
    if ratelimit.hit("midtrans-start", g.user["id"], 10, 60):
        return jsonify(ok=False, message="Terlalu banyak percobaan. Tunggu sebentar."), 429
    try:
        snap = payment_data.start_attempt(order_no, g.user["id"])
    except PaymentError as exc:
        return jsonify(ok=False, message=str(exc)), exc.status
    current_app.logger.info(
        "MIDTRANS_STARTED order=%s user_id=%s ip=%s", order_no, g.user["id"], request.remote_addr
    )
    return jsonify(ok=True, token=snap["token"], redirect_url=snap["redirect_url"])


@bp.route("/pesanan/<order_no>/midtrans/cek", methods=["POST"])
@login_required
def check(order_no):
    """Tanya status ke Midtrans (berguna kalau notifikasi belum sampai ke server)."""
    if order_data.get_order(order_no, g.user["id"]) is None:
        abort(404)
    back = redirect(url_for("pesanan.detail", order_no=order_no))
    if not midtrans.configured():
        flash("Pembayaran online belum diaktifkan.", "error")
        return back
    if ratelimit.hit("midtrans-check", g.user["id"], 20, 60):
        flash("Terlalu banyak pengecekan. Tunggu sebentar.", "error")
        return back
    try:
        outcomes = payment_data.sync_order(order_no, g.user["id"])
    except PaymentError as exc:
        flash(str(exc), "error")
        return back

    if "paid" in outcomes:
        flash("Pembayaran diterima. Pesanan sedang diproses.", "success")
    elif any(o in outcomes for o in ("stock_short", "duplicate", "paid_cancelled")):
        flash("Pembayaran diterima. Admin akan menindaklanjuti pesananmu.", "success")
    elif "pending" in outcomes:
        flash("Pembayaran belum selesai. Selesaikan sesuai instruksi dari Midtrans.", "error")
    elif "failed" in outcomes:
        flash("Pembayaran tidak berhasil atau kedaluwarsa. Silakan coba bayar lagi.", "error")
    elif not outcomes:
        flash("Tidak ada pembayaran Midtrans yang sedang menunggu.", "error")
    else:
        flash("Status pembayaran belum berubah.", "error")
    return back


@bp.route("/pembayaran/midtrans/notifikasi", methods=["POST"])
def notify():
    """Webhook dari Midtrans. Tanpa login & tanpa CSRF (dikecualikan di app.py);
    keasliannya dijamin oleh signature_key."""
    if ratelimit.hit("midtrans-notify", request.remote_addr, 300, 60):
        abort(429)
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(ok=False, message="bad request"), 400

    result = payment_data.handle_notification(payload)
    current_app.logger.info(
        "MIDTRANS_NOTIFY order=%s status=%s result=%s ip=%s",
        str(payload.get("order_id", ""))[:60], str(payload.get("transaction_status", ""))[:20],
        result, request.remote_addr,
    )
    if result == "bad_signature":
        current_app.logger.warning("MIDTRANS_BAD_SIGNATURE ip=%s", request.remote_addr)
        return jsonify(ok=False, message="invalid signature"), 403
    return jsonify(ok=True, result=result), 200
