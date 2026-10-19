"""Blueprint 'cart': keranjang belanja (tersimpan di tabel cart_items)."""
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

import cart_data
from catalog import format_rupiah
from security import login_required, safe_next

bp = Blueprint("cart", __name__)


def _wants_json():
    return request.headers.get("X-Requested-With") == "fetch"


def _int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@bp.app_context_processor
def inject_cart_count():
    user = g.get("user")
    return {"cart_count": cart_data.cart_count(user["id"]) if user else 0}


@bp.route("/keranjang")
@login_required
def view():
    items = cart_data.get_cart_items(g.user["id"])
    return render_template(
        "cart.html",
        items=items,
        total_qty=sum(i["qty"] for i in items),
        subtotal_label=format_rupiah(sum(i["line_total"] for i in items)),
        active_page="cart",
    )


@bp.route("/keranjang/tambah", methods=["POST"])
def add():
    wants_json = _wants_json()
    next_url = safe_next(request.form.get("next"))

    if g.user is None:
        login_url = url_for("auth.login", next=next_url)
        if wants_json:
            return (
                jsonify(ok=False, login_url=login_url, message="Masuk dulu untuk berbelanja."),
                401,
            )
        return redirect(login_url)

    def fail(status, message):
        if wants_json:
            return jsonify(ok=False, message=message), status
        flash(message, "error")
        return redirect(next_url or url_for("cart.view"))

    product_id = _int(request.form.get("product_id"))
    raw_qty = request.form.get("qty")
    qty = 1 if raw_qty is None else _int(raw_qty)  # kosong = 1; bukan angka = ditolak
    if product_id is None or qty is None or qty < 1:
        return fail(400, "Permintaan tidak valid.")
    qty = min(qty, cart_data.MAX_QTY)

    status, new_qty, limited = cart_data.add_to_cart(g.user["id"], product_id, qty)
    if status == "not_found":
        return fail(404, "Produk tidak ditemukan.")
    if status == "out_of_stock":
        return fail(409, "Stok produk habis.")

    message = (
        "Jumlah dibatasi sesuai stok (%d)." % new_qty if limited else "Ditambahkan ke keranjang."
    )
    if wants_json:
        return jsonify(
            ok=True,
            qty=new_qty,
            limited=limited,
            message=message,
            count=cart_data.cart_count(g.user["id"]),
        )
    flash(message, "success")
    return redirect(next_url or url_for("cart.view"))


@bp.route("/keranjang/ubah", methods=["POST"])
@login_required
def update():
    product_id = _int(request.form.get("product_id"))
    qty = _int(request.form.get("qty"))
    if product_id is None or qty is None:
        flash("Permintaan tidak valid.", "error")
        return redirect(url_for("cart.view"))

    status, new_qty, limited = cart_data.set_quantity(g.user["id"], product_id, qty)
    if status == "not_in_cart":
        flash("Barang itu tidak ada di keranjang.", "error")
    elif status == "out_of_stock":
        flash("Stok barang habis, barang dihapus dari keranjang.", "error")
    elif status == "removed":
        flash("Barang dihapus dari keranjang.", "success")
    elif limited:
        flash("Jumlah dibatasi sesuai stok (%d)." % new_qty, "error")
    return redirect(url_for("cart.view"))


@bp.route("/keranjang/hapus", methods=["POST"])
@login_required
def remove():
    product_id = _int(request.form.get("product_id"))
    if product_id is None:
        flash("Permintaan tidak valid.", "error")
    else:
        cart_data.remove_item(g.user["id"], product_id)
        flash("Barang dihapus dari keranjang.", "success")
    return redirect(url_for("cart.view"))
