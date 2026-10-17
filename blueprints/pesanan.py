"""Blueprint 'pesanan': checkout, pembayaran (upload bukti), riwayat pesanan."""
import re
import secrets
from urllib.parse import urlparse

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

import cart_data
import order_data
from catalog import format_date, format_rupiah
from order_data import OrderError
from security import login_required, safe_next
from store_config import (
    COURIERS,
    MAX_PROOF_BYTES,
    PAYMENT_METHODS,
    STATUS_LABELS,
    STATUS_TONES,
    UPLOAD_DIR,
)

bp = Blueprint("pesanan", __name__)

PHONE_RE = re.compile(r"^[0-9+\-\s]{8,20}$")
POSTAL_RE = re.compile(r"^\d{5}$")
PROOF_MIME = {"jpg": "image/jpeg", "png": "image/png", "webp": "image/webp", "pdf": "application/pdf"}


# ---------------------------------------------------------------------------
# Filter & variabel template
# ---------------------------------------------------------------------------
@bp.app_template_filter("rupiah")
def rupiah_filter(value):
    return format_rupiah(int(value))


@bp.app_template_filter("tanggal")
def tanggal_filter(value):
    """'10 Okt 2026, 14:05' dari datetime (MySQL) atau string ISO."""
    from datetime import datetime

    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return "%s, %02d:%02d" % (format_date(value), value.hour, value.minute)


@bp.app_context_processor
def inject_order_constants():
    return {"STATUS_LABELS": STATUS_LABELS, "STATUS_TONES": STATUS_TONES}


@bp.app_errorhandler(413)
def too_large(_error):
    flash("Berkas terlalu besar (maksimal 5 MB).", "error")
    # Kembali ke halaman asal (hanya path di situs ini), kalau tidak ada ke daftar pesanan.
    ref = urlparse(request.referrer or "")
    target = ref.path if ref.netloc == request.host else None
    return redirect(safe_next(target) or url_for("pesanan.list_orders"))


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------
def _validate_checkout(form):
    """-> (data, courier_key, service_code, pesan_error)"""
    data = {
        k: form.get(k, "").strip()
        for k in ("recipient_name", "phone", "address", "city", "province", "postal_code")
    }
    courier_key, _, service = form.get("shipping", "").partition(":")

    error = None
    if not data["recipient_name"] or len(data["recipient_name"]) > 100:
        error = "Nama penerima wajib diisi (maksimal 100 karakter)."
    elif not PHONE_RE.match(data["phone"]):
        error = "Nomor telepon tidak valid (8-20 digit)."
    elif not data["address"] or len(data["address"]) > 300:
        error = "Alamat wajib diisi (maksimal 300 karakter)."
    elif not data["city"] or len(data["city"]) > 100:
        error = "Kota wajib diisi."
    elif not data["province"] or len(data["province"]) > 100:
        error = "Provinsi wajib diisi."
    elif not POSTAL_RE.match(data["postal_code"]):
        error = "Kode pos harus 5 digit angka."
    elif courier_key not in COURIERS or service not in COURIERS[courier_key]["services"]:
        error = "Pilih layanan pengiriman."
    return data, courier_key, service, error


@bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items = cart_data.get_cart_items(g.user["id"])
    if not items:
        flash("Keranjang masih kosong.", "error")
        return redirect(url_for("cart.view"))

    error = None
    if request.method == "POST":
        data, courier_key, service, error = _validate_checkout(request.form)
        if error is None:
            try:
                order_no = order_data.create_order(g.user["id"], data, courier_key, service)
            except OrderError as exc:
                error = str(exc)
            else:
                current_app.logger.info(
                    "ORDER_CREATED order=%s user_id=%s ip=%s", order_no, g.user["id"], request.remote_addr
                )
                flash("Pesanan dibuat. Silakan lakukan pembayaran.", "success")
                return redirect(url_for("pesanan.detail", order_no=order_no))
        if error:
            flash(error, "error")
            items = cart_data.get_cart_items(g.user["id"])  # bisa berubah (stok)
            if not items:
                return redirect(url_for("cart.view"))

    subtotal = sum(i["line_total"] for i in items)
    return render_template(
        "checkout.html",
        items=items,
        subtotal=subtotal,
        couriers=COURIERS,
        form=request.form if request.method == "POST" else {"recipient_name": g.user["name"]},
        active_page="checkout",
    )


# ---------------------------------------------------------------------------
# Riwayat & detail pesanan
# ---------------------------------------------------------------------------
@bp.route("/pesanan")
@login_required
def list_orders():
    return render_template(
        "order_list.html", orders=order_data.list_orders(g.user["id"]), active_page="orders"
    )


@bp.route("/pesanan/<order_no>")
@login_required
def detail(order_no):
    order = order_data.get_order(order_no, g.user["id"])
    if order is None:
        abort(404)  # milik orang lain pun dijawab 404 (tidak membocorkan keberadaannya)
    courier = COURIERS.get(order["courier"] or "", {})
    service = courier.get("services", {}).get(order["service"] or "")
    return render_template(
        "order_detail.html",
        order=order,
        courier_label=courier.get("label", order["courier"] or "-"),
        service_label=service[0] if service else (order["service"] or ""),
        methods=PAYMENT_METHODS,
        active_page="orders",
    )


@bp.route("/pesanan/<order_no>/batal", methods=["POST"])
@login_required
def cancel(order_no):
    if order_data.get_order(order_no, g.user["id"]) is None:
        abort(404)
    if order_data.cancel_order(order_no, g.user["id"]):
        flash("Pesanan dibatalkan.", "success")
    else:
        flash("Pesanan ini sudah tidak bisa dibatalkan.", "error")
    return redirect(url_for("pesanan.detail", order_no=order_no))


# ---------------------------------------------------------------------------
# Upload bukti bayar
# ---------------------------------------------------------------------------
def detect_proof_type(head):
    """Jenis berkas dari byte pembuka (bukan dari nama/ekstensi yang dikirim user)."""
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"%PDF-"):
        return "pdf"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


@bp.route("/pesanan/<order_no>/bayar", methods=["POST"])
@login_required
def upload_proof(order_no):
    order = order_data.get_order(order_no, g.user["id"])
    if order is None:
        abort(404)
    back = redirect(url_for("pesanan.detail", order_no=order_no))

    if order["status"] != "menunggu_pembayaran":
        flash("Pesanan ini tidak bisa menerima bukti pembayaran.", "error")
        return back

    method = request.form.get("method", "")
    if method not in PAYMENT_METHODS:
        flash("Pilih metode pembayaran yang kamu gunakan.", "error")
        return back

    upload = request.files.get("bukti")
    if upload is None or not upload.filename:
        flash("Pilih berkas bukti pembayaran.", "error")
        return back
    data = upload.read(MAX_PROOF_BYTES + 1)
    if not data:
        flash("Berkas kosong.", "error")
        return back
    if len(data) > MAX_PROOF_BYTES:
        flash("Berkas terlalu besar (maksimal 5 MB).", "error")
        return back
    ext = detect_proof_type(data[:16])
    if ext is None:
        flash("Format berkas tidak didukung. Gunakan JPG, PNG, WEBP, atau PDF.", "error")
        return back

    # Nama berkas dibuat sendiri (acak); nama dari user tidak dipakai sama sekali.
    rel_path = "payments/%s.%s" % (secrets.token_hex(16), ext)
    path = UPLOAD_DIR / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as fh:
        fh.write(data)

    try:
        order_data.add_payment_proof(order["id"], method, int(order["total"]), rel_path)
    except OrderError as exc:
        path.unlink(missing_ok=True)
        flash(str(exc), "error")
    else:
        current_app.logger.info(
            "PROOF_UPLOADED order=%s user_id=%s ip=%s", order_no, g.user["id"], request.remote_addr
        )
        flash("Bukti pembayaran terkirim. Admin akan memverifikasinya.", "success")
    return back


@bp.route("/pesanan/<order_no>/bukti")
@login_required
def proof(order_no):
    """Berkas bukti bayar terbaru: hanya untuk pemilik pesanan atau admin."""
    owner = None if g.user["role"] == "admin" else g.user["id"]
    order = order_data.get_order(order_no, owner)
    if order is None or not order["payments"]:
        abort(404)

    path = (UPLOAD_DIR / order["payments"][0]["proof_path"]).resolve()
    if UPLOAD_DIR.resolve() not in path.parents or not path.is_file():
        abort(404)

    response = send_file(path, mimetype=PROOF_MIME.get(path.suffix.lstrip("."), "application/octet-stream"), conditional=True)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, no-store"
    return response
