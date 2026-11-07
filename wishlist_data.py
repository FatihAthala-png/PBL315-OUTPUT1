"""Data wishlist: semua query ke tabel wishlist_items ada di sini."""
from mysql.connector import errors as mysql_errors

import db
from catalog import get_products


def wishlist_ids(user_id):
    """Himpunan id produk aktif di wishlist user (untuk mewarnai tombol hati)."""
    rows = db.query_all(
        "SELECT w.product_id FROM wishlist_items w "
        "JOIN products p ON p.id = w.product_id AND p.is_active = 1 "
        "WHERE w.user_id = %s",
        (user_id,),
    )
    return {int(r["product_id"]) for r in rows}


def wishlist_count(user_id):
    row = db.query_one(
        "SELECT COUNT(*) AS n FROM wishlist_items w "
        "JOIN products p ON p.id = w.product_id AND p.is_active = 1 "
        "WHERE w.user_id = %s",
        (user_id,),
    )
    return int(row["n"]) if row else 0


def get_wishlist_products(user_id):
    """Produk wishlist (format kartu katalog), yang terbaru ditambahkan di depan."""
    rows = db.query_all(
        "SELECT product_id FROM wishlist_items WHERE user_id = %s ORDER BY added_at DESC, id DESC",
        (user_id,),
    )
    order = [int(r["product_id"]) for r in rows]
    by_id = {p["id"]: p for p in get_products()}
    return [by_id[i] for i in order if i in by_id]


def _product_exists(product_id):
    return (
        db.query_one(
            "SELECT id FROM products WHERE id = %s AND is_active = 1", (product_id,)
        )
        is not None
    )


def add(user_id, product_id):
    """Tambah ke wishlist. Mengembalikan 'ok' | 'not_found'. Aman dipanggil berulang."""
    if not _product_exists(product_id):
        return "not_found"
    try:
        db.execute(
            "INSERT INTO wishlist_items (user_id, product_id) VALUES (%s, %s)",
            (user_id, product_id),
        )
    except mysql_errors.IntegrityError:  # sudah ada / klik ganda
        pass
    return "ok"


def remove(user_id, product_id):
    db.execute(
        "DELETE FROM wishlist_items WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )
