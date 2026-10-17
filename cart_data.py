"""Data keranjang: semua query ke tabel cart_items ada di sini."""
from mysql.connector import errors as mysql_errors

import db
from catalog import format_rupiah

MAX_QTY = 99


def cart_count(user_id):
    """Total jumlah barang di keranjang (untuk badge di header)."""
    row = db.query_one(
        "SELECT COALESCE(SUM(c.qty), 0) AS n FROM cart_items c "
        "JOIN products p ON p.id = c.product_id AND p.is_active = 1 "
        "WHERE c.user_id = %s",
        (user_id,),
    )
    return int(row["n"]) if row else 0


def get_cart_items(user_id):
    rows = db.query_all(
        "SELECT c.product_id, c.qty, p.name, p.image_url, p.category, p.price, p.stock "
        "FROM cart_items c JOIN products p ON p.id = c.product_id "
        "WHERE c.user_id = %s AND p.is_active = 1 ORDER BY c.added_at, c.id",
        (user_id,),
    )
    items = []
    for r in rows:
        price, qty, stock = int(r["price"]), int(r["qty"]), int(r["stock"])
        items.append(
            {
                "product_id": r["product_id"],
                "name": r["name"],
                "image_url": r["image_url"],
                "category": r["category"],
                "price_label": format_rupiah(price),
                "qty": qty,
                "stock": stock,
                "line_total": price * qty,
                "line_label": format_rupiah(price * qty),
            }
        )
    return items


def _stock_of(product_id):
    p = db.query_one(
        "SELECT stock FROM products WHERE id = %s AND is_active = 1", (product_id,)
    )
    return None if p is None else int(p["stock"])


def _in_cart(user_id, product_id):
    return db.query_one(
        "SELECT qty FROM cart_items WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )


def add_to_cart(user_id, product_id, qty):
    """Tambah barang. Mengembalikan (status, qty_sekarang, dibatasi).

    status: 'ok' | 'not_found' | 'out_of_stock'
    """
    stock = _stock_of(product_id)
    if stock is None:
        return "not_found", 0, False
    if stock <= 0:
        return "out_of_stock", 0, False

    limit = min(stock, MAX_QTY)
    row = _in_cart(user_id, product_id)
    wanted = (int(row["qty"]) if row else 0) + qty
    new_qty = min(wanted, limit)

    if row:
        db.execute(
            "UPDATE cart_items SET qty = %s WHERE user_id = %s AND product_id = %s",
            (new_qty, user_id, product_id),
        )
    else:
        try:
            db.execute(
                "INSERT INTO cart_items (user_id, product_id, qty) VALUES (%s, %s, %s)",
                (user_id, product_id, new_qty),
            )
        except mysql_errors.IntegrityError:  # klik ganda yang bersamaan
            db.execute(
                "UPDATE cart_items SET qty = %s WHERE user_id = %s AND product_id = %s",
                (new_qty, user_id, product_id),
            )
    return "ok", new_qty, wanted > limit


def set_quantity(user_id, product_id, qty):
    """Ubah jumlah. qty <= 0 menghapus item.

    status: 'ok' | 'removed' | 'not_in_cart' | 'out_of_stock'
    """
    if _in_cart(user_id, product_id) is None:
        return "not_in_cart", 0, False
    if qty <= 0:
        remove_item(user_id, product_id)
        return "removed", 0, False

    stock = _stock_of(product_id)
    if not stock:  # produk dinonaktifkan atau stok habis
        remove_item(user_id, product_id)
        return "out_of_stock", 0, False

    limit = min(stock, MAX_QTY)
    new_qty = min(qty, limit)
    db.execute(
        "UPDATE cart_items SET qty = %s WHERE user_id = %s AND product_id = %s",
        (new_qty, user_id, product_id),
    )
    return "ok", new_qty, qty > limit


def remove_item(user_id, product_id):
    db.execute(
        "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s",
        (user_id, product_id),
    )
