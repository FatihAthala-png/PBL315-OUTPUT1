"""Blueprint 'shop': beranda, katalog, pencarian, detail produk, ulasan."""
from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from catalog import (
    AVAILABILITY_LABELS,
    BRAND_LABELS,
    RARITY_LABELS,
    add_review,
    build_filters,
    get_popular_products,
    get_product,
    get_products,
    get_reviews,
    get_shop_categories,
    search_products,
    user_review,
)
from security import login_required

bp = Blueprint("shop", __name__)

# Slug lama -> filter jenis produk. Dialihkan ke All Product supaya link lama
# (hero, footer, Shop By Category) tetap jalan dan filternya otomatis terpilih.
LEGACY_PAGES = {
    "pokemon-tcg": "tcg",
    "action-figures": "figure",
}

# Halaman katalog: slug URL -> judul + kunci active_page (highlight menu).
CATALOG_PAGES = {
    "semua-produk": {"title": "All Product", "active": "all_product"},
}


@bp.route("/")
def home():
    return render_template(
        "index.html",
        active_page="home",
        popular_products=get_popular_products(),
        shop_categories=get_shop_categories(),
    )


@bp.route("/<page>")
def page(page):
    # Link lama /pokemon-tcg dan /action-figures -> All Product + filter jenis.
    if page in LEGACY_PAGES:
        return redirect(
            url_for("shop.page", page="semua-produk", type=LEGACY_PAGES[page])
        )

    catalog = CATALOG_PAGES.get(page)
    if not catalog:
        abort(404)

    query = request.args.get("q", "").strip()[:100]
    products = get_products()
    title = catalog["title"]
    if query:
        products = search_products(products, query)
        title = 'Hasil pencarian: "%s"' % query

    return render_template(
        "catalog.html",
        products=products,
        filters=build_filters(products),
        active_page=catalog["active"],
        page_title=title,
    )


@bp.route("/produk/<int:product_id>")
def product(product_id):
    item = get_product(product_id)
    if item is None:
        abort(404)

    my_review = user_review(product_id, g.user["id"]) if g.user else None
    return render_template(
        "product_detail.html",
        product=item,
        reviews=get_reviews(product_id),
        my_review=my_review,
        brand_label=BRAND_LABELS.get(item["brand"], item["brand"]),
        availability_labels=[AVAILABILITY_LABELS.get(a, a) for a in item["availability"]],
        rarity_labels=[RARITY_LABELS.get(r, r) for r in item["rarity"]],
        active_page="all_product",
    )


@bp.route("/produk/<int:product_id>/ulasan", methods=["POST"])
@login_required
def post_review(product_id):
    if get_product(product_id) is None:
        abort(404)

    try:
        rating = int(request.form.get("rating", ""))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()

    if not 1 <= rating <= 5:
        flash("Pilih rating 1 sampai 5 bintang.", "error")
    elif not comment:
        flash("Komentar wajib diisi.", "error")
    elif len(comment) > 1000:
        flash("Komentar terlalu panjang (maksimal 1000 karakter).", "error")
    elif add_review(product_id, g.user["id"], rating, comment):
        flash("Terima kasih! Ulasan kamu sudah terkirim.", "success")
    else:
        flash("Kamu sudah pernah mengulas produk ini.", "error")

    return redirect(url_for("shop.product", product_id=product_id) + "#ulasan")
