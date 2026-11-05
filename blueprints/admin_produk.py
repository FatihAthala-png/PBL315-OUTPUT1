"""Blueprint 'admin_produk': kelola produk (tambah, ubah, nonaktifkan, hapus)."""
import re

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    request,
    url_for,
)

import admin_data
from blueprints.admin import ADMIN_TABS, _render
from blueprints.media import ImageError, delete_product_image, save_product_image
from catalog import BRAND_LABELS, BRANDS, RARITIES, RARITY_LABELS, SUBCATEGORIES, TYPE_INFO
from security import admin_required

bp = Blueprint("admin_produk", __name__, url_prefix="/admin/produk")

PER_PAGE = 20
MAX_IMAGE_BYTES = 5 * 1024 * 1024
BADGES = ["BEST SELLER", "RARITY VAULT", "KOLEKSI PILIHAN", "PRE-ORDER", "NEW"]
URL_RE = re.compile(r"^(https://[^\s\"'<>]+|/static/[^\s\"'<>]+|/media/produk/[0-9a-f]{32}\.jpg)$")


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _log(action, product_id):
    current_app.logger.info(
        "ADMIN_ACTION admin_id=%s action=%s product=%s ip=%s",
        g.user["id"], action, product_id, request.remote_addr,
    )


def parse_form(form):
    """-> (data, pesan_error). Gambar diurus terpisah di route."""
    name = form.get("name", "").strip()
    category = form.get("category", "").strip()
    ptype = form.get("type", "")
    sub = form.get("sub", "")
    brand = form.get("brand", "")
    rarity = [r for r in form.getlist("rarity") if r in RARITY_LABELS]
    price = _int(re.sub(r"\D", "", form.get("price", "")) or None)  # "1.250.000" -> 1250000
    discount_raw = form.get("discount_percent", "").strip()
    discount = _int(discount_raw) if discount_raw else None
    stock = _int(form.get("stock", "").strip())
    unit = form.get("stock_unit", "").strip()
    badge = form.get("badge", "").strip()
    image_url = form.get("image_url", "").strip()

    error = None
    if not name or len(name) > 200:
        error = "Nama produk wajib diisi (maksimal 200 karakter)."
    elif not category or len(category) > 100:
        error = "Kategori/label wajib diisi (maksimal 100 karakter)."
    elif ptype not in TYPE_INFO:
        error = "Pilih jenis produk."
    elif sub not in dict(SUBCATEGORIES.get(ptype, [])):
        error = "Sub-kategori tidak sesuai dengan jenis produk."
    elif brand not in BRAND_LABELS:
        error = "Pilih brand."
    elif price is None or not 1 <= price <= 1_000_000_000:
        error = "Harga harus berupa angka antara 1 dan 1.000.000.000."
    elif discount_raw and (discount is None or not 1 <= discount <= 90):
        error = "Diskon harus angka 1 sampai 90 (kosongkan jika tidak ada)."
    elif stock is None or not 0 <= stock <= 1_000_000:
        error = "Stok harus angka 0 sampai 1.000.000."
    elif len(unit) > 20:
        error = "Satuan stok maksimal 20 karakter."
    elif len(badge) > 30:
        error = "Badge maksimal 30 karakter."
    elif image_url and not URL_RE.match(image_url):
        error = "URL gambar harus diawali https:// (atau gambar yang sudah diunggah)."
    if error:
        return None, error

    return {
        "name": name, "category": category, "type": ptype, "sub": sub, "brand": brand,
        "rarity": ",".join(rarity), "price": price, "discount_percent": discount,
        "stock": stock, "stock_unit": unit, "badge": badge or None,
        "is_preorder": 1 if form.get("is_preorder") else 0, "image_url_text": image_url,
    }, None


def _form_context(values, rarity, preorder, product_id=None, current_image=None, badge_current=None):
    badges = BADGES + ([badge_current] if badge_current and badge_current not in BADGES else [])
    return dict(
        values=values, rarity_selected=set(rarity), preorder=preorder, product_id=product_id,
        current_image=current_image, types=TYPE_INFO, subcats=SUBCATEGORIES, brands=BRANDS,
        rarities=RARITIES, badges=badges,
    )


def _read_upload():
    """-> (url_gambar_baru | None, pesan_error | None). Menyimpan berkas bila valid."""
    upload = request.files.get("image")
    if upload is None or not upload.filename:
        return None, None
    data = upload.read(MAX_IMAGE_BYTES + 1)
    if not data:
        return None, "Berkas gambar kosong."
    if len(data) > MAX_IMAGE_BYTES:
        return None, "Gambar terlalu besar (maksimal 5 MB)."
    try:
        return save_product_image(data), None
    except ImageError as exc:
        return None, str(exc)


# ---------------------------------------------------------------------------
# Daftar
# ---------------------------------------------------------------------------
@bp.route("/")
@admin_required
def index():
    status = request.args.get("status", "")
    if status not in ("aktif", "nonaktif"):
        status = ""
    q = request.args.get("q", "").strip()[:50]
    page = max(1, _int(request.args.get("page")) or 1)
    rows, total = admin_data.list_products(status or None, q or None, page, PER_PAGE)
    return _render(
        "admin/products.html", "produk", rows=rows, total=total, page=page,
        pages=max(1, -(-total // PER_PAGE)), status=status, q=q,
    )


# ---------------------------------------------------------------------------
# Tambah
# ---------------------------------------------------------------------------
@bp.route("/baru", methods=["GET", "POST"])
@admin_required
def create():
    if request.method == "GET":
        return _render("admin/product_form.html", "produk",
                       **_form_context({"stock": "0"}, [], False))

    data, error = parse_form(request.form)
    new_url = None
    if error is None:
        new_url, error = _read_upload()
    if error is None and not (new_url or data["image_url_text"]):
        error = "Gambar produk wajib: unggah berkas atau isi URL gambar."

    if error is None:
        data["image_url"] = new_url or data["image_url_text"]
        try:
            product_id = admin_data.save_product(None, data)
        except Exception:
            delete_product_image(new_url)
            raise
        _log("product_create", product_id)
        flash("Produk ditambahkan.", "success")
        return redirect(url_for("admin_produk.index"))

    delete_product_image(new_url)
    flash(error, "error")
    return _render("admin/product_form.html", "produk",
                   **_form_context(request.form, request.form.getlist("rarity"),
                                   bool(request.form.get("is_preorder"))))


# ---------------------------------------------------------------------------
# Ubah
# ---------------------------------------------------------------------------
@bp.route("/<int:product_id>/ubah", methods=["GET", "POST"])
@admin_required
def edit(product_id):
    row = admin_data.get_product_row(product_id)
    if row is None:
        abort(404)

    if request.method == "GET":
        values = dict(row)
        values["price"] = str(row["price"])
        values["discount_percent"] = str(row["discount_percent"] or "")
        values["image_url"] = ""
        return _render("admin/product_form.html", "produk",
                       **_form_context(values, [r for r in row["rarity"].split(",") if r],
                                       bool(row["is_preorder"]), product_id, row["image_url"], row["badge"]))

    data, error = parse_form(request.form)
    new_url = None
    if error is None:
        new_url, error = _read_upload()

    if error is None:
        data["image_url"] = new_url or data["image_url_text"] or row["image_url"]
        try:
            admin_data.save_product(product_id, data)
        except Exception:
            delete_product_image(new_url)
            raise
        if data["image_url"] != row["image_url"]:
            delete_product_image(row["image_url"])  # gambar unggahan lama tidak dipakai lagi
        _log("product_update", product_id)
        flash("Produk diperbarui.", "success")
        return redirect(url_for("admin_produk.index"))

    delete_product_image(new_url)
    flash(error, "error")
    return _render("admin/product_form.html", "produk",
                   **_form_context(request.form, request.form.getlist("rarity"),
                                   bool(request.form.get("is_preorder")), product_id,
                                   row["image_url"], row["badge"]))


# ---------------------------------------------------------------------------
# Nonaktifkan / aktifkan / hapus
# ---------------------------------------------------------------------------
@bp.route("/<int:product_id>/status", methods=["POST"])
@admin_required
def toggle(product_id):
    row = admin_data.get_product_row(product_id)
    if row is None:
        abort(404)
    now_active = not row["is_active"]
    admin_data.set_product_active(product_id, now_active)
    _log("product_activate" if now_active else "product_deactivate", product_id)
    flash("Produk diaktifkan." if now_active else "Produk dinonaktifkan (tidak tampil di toko).", "success")
    return redirect(url_for("admin_produk.index"))


@bp.route("/<int:product_id>/hapus", methods=["POST"])
@admin_required
def delete(product_id):
    row = admin_data.get_product_row(product_id)
    if row is None:
        abort(404)
    result = admin_data.delete_product(product_id)
    if result == "in_use":
        flash("Produk ini sudah pernah dipesan, jadi tidak bisa dihapus permanen. Nonaktifkan saja.", "error")
    else:
        delete_product_image(row["image_url"])
        _log("product_delete", product_id)
        flash("Produk dihapus permanen.", "success")
    return redirect(url_for("admin_produk.index"))
