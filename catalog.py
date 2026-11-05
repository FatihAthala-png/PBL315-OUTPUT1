"""Data & logika katalog: produk dari MySQL, opsi filter, kategori beranda.

Dipakai bersama oleh banyak blueprint (shop, cart, admin), jadi tidak
ditaruh di dalam blueprint tertentu.
"""
import math

import db

# ---------------------------------------------------------------------------
# Opsi filter katalog
# ---------------------------------------------------------------------------
# Label opsi filter (urutan = urutan tampil di sidebar).
TYPE_INFO = {
    "tcg": {"label": "Pokémon TCG", "icon": "style"},
    "figure": {"label": "Action Figure & Scale", "icon": "smart_toy"},
}
SUBCATEGORIES = {
    "tcg": [
        ("booster-pack", "Booster Pack"),
        ("etb", "Elite Trainer Box (ETB)"),
        ("booster-box", "Booster Box & Display"),
        ("single-card", "Single Card (SAR/Holo)"),
        ("starter-acc", "Starter Deck & Acc"),
    ],
    "figure": [
        ("scale-figure", "Scale Figure (Kotobukiya)"),
        ("nendoroid", "Nendoroid & Pop Up Parade"),
        ("shfiguarts", "SHFiguarts & Monster Col."),
        ("plush-display", "Plush & Display Case"),
    ],
}
AVAILABILITY = [
    ("ready", "Ready Stock (Langsung Kirim)"),
    ("preorder", "Pre-Order (Batch Baru)"),
    ("promo", "Promo & Diskon Spesial"),
]
RARITIES = [
    ("sar", "SAR"),
    ("ur", "Ultra Rare (UR)"),
    ("rr", "Double Rare (RR)"),
    ("psa10", "PSA 10 Gem Mint"),
    ("raw-mint", "Raw Mint"),
]
BRANDS = [
    ("pokemon-company", "The Pokémon Company"),
    ("kotobukiya", "Kotobukiya (ARTFX J)"),
    ("good-smile", "Good Smile Company"),
    ("bandai", "Bandai Namco"),
    ("ultra-pro", "Ultra PRO"),
]


# ---------------------------------------------------------------------------
# Helper harga & data produk
# ---------------------------------------------------------------------------
def rupiah_to_int(text):
    return int("".join(ch for ch in text if ch.isdigit()))


def format_rupiah(value):
    return "Rp " + f"{value:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Data produk
# ---------------------------------------------------------------------------
def get_products(product_type=None):
    """Ambil produk aktif dari MySQL, dalam format yang sama seperti sebelumnya."""
    sql = "SELECT * FROM products WHERE is_active = 1"
    params = []
    if product_type:
        sql += " AND type = %s"
        params.append(product_type)
    sql += " ORDER BY id"

    products = []
    for row in db.query_all(sql, params):
        price = int(row["price"])
        discount = row["discount_percent"]
        stock_label = (
            f"{row['stock']} {row['stock_unit']}" if row["stock_unit"] else "Tersedia"
        )
        product = {
            "id": row["id"],
            "name": row["name"],
            "image_url": row["image_url"],
            "category": row["category"],
            "badge": row["badge"],
            "stock": stock_label,
            "rating": f"{row['rating']} ({row['review_count']} ulasan)",
            "price": format_rupiah(price),
            "type": row["type"],
            "sub": row["sub"],
            "brand": row["brand"],
            "rarity": [r for r in row["rarity"].split(",") if r],
            "price_value": price,
            "rating_value": float(row["rating"]),
            "availability": ["preorder" if row["is_preorder"] else "ready"],
        }
        if discount:
            old_price = round(price / (1 - discount / 100), -3)
            product["discount"] = discount
            product["old_price"] = format_rupiah(int(old_price))
            product["availability"].append("promo")
        products.append(product)
    return products


def get_popular_products(limit=8):
    """Produk untuk section Most Popular Items di beranda."""
    return get_products()[:limit]


def build_filters(products):
    """Susun opsi filter sidebar berdasarkan produk yang ada di halaman."""

    def count_by(field):
        counts = {}
        for product in products:
            value = product[field]
            for item in value if isinstance(value, list) else [value]:
                counts[item] = counts.get(item, 0) + 1
        return counts

    def options(labels, field):
        counts = count_by(field)
        return [
            {"key": key, "label": label, "count": counts[key]}
            for key, label in labels
            if counts.get(key)
        ]

    # Filter jenis produk (Pokémon TCG / Action Figures).
    type_counts = count_by("type")
    types = [
        {"key": key, "label": info["label"], "icon": info["icon"], "count": type_counts[key]}
        for key, info in TYPE_INFO.items()
        if type_counts.get(key)
    ]

    # Sub-kategori dari semua jenis; "type" dipakai untuk menyembunyikan
    # sub-kategori yang tidak sesuai dengan jenis yang dipilih.
    sub_counts = count_by("sub")
    subs = [
        {"key": key, "label": label, "count": sub_counts[key], "type": type_key}
        for type_key, items in SUBCATEGORIES.items()
        for key, label in items
        if sub_counts.get(key)
    ]

    top_price = max((p["price_value"] for p in products), default=0)
    price_max = max(500_000, math.ceil(top_price / 500_000) * 500_000)

    return {
        "types": types,
        "sub": subs,
        "availability": options(AVAILABILITY, "availability"),
        "rarity": options(RARITIES, "rarity"),
        "brand": options(BRANDS, "brand"),
        "price": {"min": 0, "max": price_max},
    }


# ---------------------------------------------------------------------------
# Kategori untuk section Shop By Category
# ---------------------------------------------------------------------------
SHOP_CATEGORIES = [
    {"key": "tcg", "label": "Pokémon TCG", "page": "pokemon-tcg", "icon": "kartu.gif"},
    {"key": "figure", "label": "Action Figures", "page": "action-figures", "icon": "figure.gif"},
]


def get_shop_categories(limit=6):
    """Kategori + produknya untuk section Shop By Category di beranda."""
    return [
        {**cat, "products": get_products(cat["key"])[:limit]}
        for cat in SHOP_CATEGORIES
    ]



# ---------------------------------------------------------------------------
# Pencarian, detail produk, ulasan (C2)
# ---------------------------------------------------------------------------
from datetime import datetime  # noqa: E402

BRAND_LABELS = dict(BRANDS)
AVAILABILITY_LABELS = dict(AVAILABILITY)
RARITY_LABELS = dict(RARITIES)
_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


def search_products(products, query):
    """Sisakan produk yang memuat SEMUA kata pencarian (nama, kategori, brand, sub)."""
    words = (query or "").lower().split()
    if not words:
        return products

    def haystack(p):
        return " ".join(
            [p["name"], p["category"], p["brand"].replace("-", " "), p["sub"].replace("-", " ")]
        ).lower()

    return [p for p in products if all(w in haystack(p) for w in words)]


def get_product(product_id):
    """Satu produk aktif berdasarkan id, atau None."""
    return next((p for p in get_products() if p["id"] == product_id), None)


def format_date(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return "%d %s %d" % (value.day, _BULAN[value.month - 1], value.year)


def display_name(name):
    """'Fatih Athala' -> 'Fatih A.' (nama pengulas tidak ditampilkan penuh)."""
    parts = (name or "").split()
    if not parts:
        return "Pengguna"
    if len(parts) == 1:
        return parts[0]
    return "%s %s." % (parts[0], parts[1][0].upper())


def get_reviews(product_id, limit=50):
    rows = db.query_all(
        "SELECT r.id, r.rating, r.comment, r.created_at, u.name "
        "FROM reviews r JOIN users u ON u.id = r.user_id "
        "WHERE r.product_id = %s ORDER BY r.created_at DESC, r.id DESC LIMIT %s",
        (product_id, limit),
    )
    return [
        {
            "id": r["id"],
            "rating": int(r["rating"]),
            "comment": r["comment"],
            "name": display_name(r["name"]),
            "initial": (r["name"] or "?")[:1].upper(),
            "date": format_date(r["created_at"]),
        }
        for r in rows
    ]


def user_review(product_id, user_id):
    return db.query_one(
        "SELECT id, rating, comment FROM reviews WHERE product_id = %s AND user_id = %s",
        (product_id, user_id),
    )


def add_review(product_id, user_id, rating, comment):
    """Simpan ulasan, lalu hitung ulang rating & jumlah ulasan produk.

    Mengembalikan False kalau user ini sudah pernah mengulas produk tersebut.
    """
    from mysql.connector import errors as mysql_errors

    if user_review(product_id, user_id):
        return False
    try:
        with db.transaction() as cur:
            cur.execute(
                "INSERT INTO reviews (product_id, user_id, rating, comment) "
                "VALUES (%s, %s, %s, %s)",
                (product_id, user_id, rating, comment),
            )
            cur.execute(
                "UPDATE products SET "
                "rating = (SELECT ROUND(AVG(rating), 1) FROM reviews WHERE product_id = %s), "
                "review_count = (SELECT COUNT(*) FROM reviews WHERE product_id = %s) "
                "WHERE id = %s",
                (product_id, product_id, product_id),
            )
    except mysql_errors.IntegrityError:
        return False  # balapan dua kiriman sekaligus
    return True
