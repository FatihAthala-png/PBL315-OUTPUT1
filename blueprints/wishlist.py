"""Blueprint 'wishlist': daftar produk favorit (tersimpan di tabel wishlist_items)."""
from flask import (
    Blueprint,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

import wishlist_data
from security import login_required, safe_next

bp = Blueprint("wishlist", __name__)


def _wants_json():
    return request.headers.get("X-Requested-With") == "fetch"


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@bp.app_context_processor
def inject_wishlist():
    """ids = produk yang sudah di-love (untuk status awal tombol), count = badge header."""
    user = g.get("user")
    if not user:
        return {"wishlist_ids": frozenset(), "wishlist_count": 0}
    ids = wishlist_data.wishlist_ids(user["id"])
    return {"wishlist_ids": ids, "wishlist_count": len(ids)}


@bp.route("/wishlist")
@login_required
def view():
    products = wishlist_data.get_wishlist_products(g.user["id"])
    return render_template("wishlist.html", products=products, active_page="wishlist")


@bp.route("/wishlist/toggle", methods=["POST"])
def toggle():
    wants_json = _wants_json()
    next_url = safe_next(request.form.get("next"))

    if g.user is None:
        login_url = url_for("auth.login", next=next_url)
        if wants_json:
            return (
                jsonify(ok=False, login_url=login_url, message="Masuk dulu untuk memakai wishlist."),
                401,
            )
        return redirect(login_url)

    def fail(status, message):
        if wants_json:
            return jsonify(ok=False, message=message), status
        flash(message, "error")
        return redirect(next_url or url_for("wishlist.view"))

    product_id = _int(request.form.get("product_id"))
    if product_id is None:
        return fail(400, "Permintaan tidak valid.")

    # 'state' (on/off) dikirim klien supaya klik ganda tidak saling membatalkan.
    state = request.form.get("state")
    user_id = g.user["id"]
    currently = product_id in wishlist_data.wishlist_ids(user_id)
    want = (not currently) if state not in ("on", "off") else state == "on"

    if want:
        if wishlist_data.add(user_id, product_id) == "not_found":
            return fail(404, "Produk tidak ditemukan.")
        message = "Ditambahkan ke wishlist."
    else:
        wishlist_data.remove(user_id, product_id)
        message = "Dihapus dari wishlist."

    if wants_json:
        return jsonify(
            ok=True,
            liked=want,
            message=message,
            count=wishlist_data.wishlist_count(user_id),
        )
    flash(message, "success")
    return redirect(next_url or url_for("wishlist.view"))
