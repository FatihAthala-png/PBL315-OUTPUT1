"""Data pesanan: semua query ke orders, order_items, payments, order_status_history."""
import secrets
from datetime import datetime

from mysql.connector import errors as mysql_errors

import db
from catalog import format_rupiah
from store_config import COURIERS


class OrderError(Exception):
    """Pesanan gagal diproses. Pesannya aman ditampilkan ke user."""


def generate_order_no():
    # Akhiran acak (bukan urut) supaya nomor pesanan tidak mudah ditebak.
    return "KMS-%s-%s" % (datetime.now().strftime("%y%m%d"), secrets.token_hex(3).upper())


def create_order(user_id, ship, courier_key, service_code):
    """Buat pesanan dari isi keranjang dalam satu transaksi; kosongkan keranjang.

    Harga & ongkir selalu dihitung di server, tidak pernah dari input user.
    """
    service_label, shipping_cost = COURIERS[courier_key]["services"][service_code]

    with db.transaction() as cur:
        cur.execute(
            "SELECT c.product_id, c.qty, p.name, p.price, p.stock "
            "FROM cart_items c JOIN products p ON p.id = c.product_id "
            "WHERE c.user_id = %s AND p.is_active = 1 ORDER BY c.id FOR UPDATE",
            (user_id,),
        )
        rows = cur.fetchall()
        if not rows:
            raise OrderError("Keranjang kosong.")
        for r in rows:
            if int(r["qty"]) > int(r["stock"]):
                raise OrderError(
                    'Stok "%s" tidak cukup (tersisa %d). Ubah jumlahnya di keranjang.'
                    % (r["name"], int(r["stock"]))
                )

        subtotal = sum(int(r["price"]) * int(r["qty"]) for r in rows)
        total = subtotal + shipping_cost

        order_id = None
        order_no = None
        for _ in range(5):
            order_no = generate_order_no()
            try:
                cur.execute(
                    "INSERT INTO orders (order_no, user_id, recipient_name, phone, address, "
                    "city, province, postal_code, courier, service, subtotal, shipping_cost, total) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        order_no, user_id, ship["recipient_name"], ship["phone"], ship["address"],
                        ship["city"], ship["province"], ship["postal_code"], courier_key,
                        service_code, subtotal, shipping_cost, total,
                    ),
                )
                order_id = cur.lastrowid
                break
            except mysql_errors.IntegrityError:
                continue  # nomor pesanan bentrok (sangat jarang), coba nomor lain
        if order_id is None:
            raise OrderError("Gagal membuat nomor pesanan, silakan coba lagi.")

        for r in rows:
            cur.execute(
                "INSERT INTO order_items (order_id, product_id, product_name, unit_price, qty) "
                "VALUES (%s, %s, %s, %s, %s)",
                (order_id, r["product_id"], r["name"], int(r["price"]), int(r["qty"])),
            )
        cur.execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))
        cur.execute(
            "INSERT INTO order_status_history (order_id, title, description) VALUES (%s, %s, %s)",
            (order_id, "Pesanan dibuat", "Menunggu pembayaran %s" % format_rupiah(total)),
        )
    return order_no


def list_orders(user_id):
    return db.query_all(
        "SELECT o.order_no, o.status, o.total, o.created_at, "
        "(SELECT COALESCE(SUM(qty), 0) FROM order_items WHERE order_id = o.id) AS item_count "
        "FROM orders o WHERE o.user_id = %s ORDER BY o.created_at DESC, o.id DESC",
        (user_id,),
    )


def get_order(order_no, user_id=None):
    """Satu pesanan beserta item, pembayaran, dan riwayatnya.

    Dengan user_id, hanya pesanan milik user itu yang dikembalikan.
    """
    sql = "SELECT * FROM orders WHERE order_no = %s"
    params = [order_no]
    if user_id is not None:
        sql += " AND user_id = %s"
        params.append(user_id)
    order = db.query_one(sql, tuple(params))
    if order is None:
        return None

    oid = order["id"]
    order["items"] = [
        {
            "product_id": r["product_id"],
            "name": r["product_name"],
            "unit_price": int(r["unit_price"]),
            "qty": int(r["qty"]),
            "line_total": int(r["unit_price"]) * int(r["qty"]),
        }
        for r in db.query_all(
            "SELECT product_id, product_name, unit_price, qty FROM order_items "
            "WHERE order_id = %s ORDER BY id",
            (oid,),
        )
    ]
    order["payments"] = db.query_all(
        "SELECT id, method, amount, proof_path, status, reject_reason, created_at "
        "FROM payments WHERE order_id = %s ORDER BY id DESC",
        (oid,),
    )
    order["history"] = db.query_all(
        "SELECT title, description, created_at FROM order_status_history "
        "WHERE order_id = %s ORDER BY created_at DESC, id DESC",
        (oid,),
    )
    return order


def add_payment_proof(order_id, method, amount, rel_path):
    """Catat bukti bayar dan ubah status pesanan jadi menunggu verifikasi."""
    with db.transaction() as cur:
        cur.execute("SELECT status FROM orders WHERE id = %s FOR UPDATE", (order_id,))
        rows = cur.fetchall()  # habiskan hasil sebelum query berikutnya
        if not rows or rows[0]["status"] != "menunggu_pembayaran":
            raise OrderError("Pesanan ini tidak bisa menerima bukti pembayaran.")
        cur.execute(
            "INSERT INTO payments (order_id, method, amount, proof_path) VALUES (%s, %s, %s, %s)",
            (order_id, method, amount, rel_path),
        )
        cur.execute("UPDATE orders SET status = 'menunggu_approval' WHERE id = %s", (order_id,))
        cur.execute(
            "INSERT INTO order_status_history (order_id, title, description) VALUES (%s, %s, %s)",
            (order_id, "Bukti pembayaran diunggah", "Menunggu verifikasi admin"),
        )


def cancel_order(order_no, user_id):
    """Batalkan pesanan yang belum dibayar. False kalau sudah tidak bisa dibatalkan."""
    with db.transaction() as cur:
        cur.execute(
            "SELECT id, status FROM orders WHERE order_no = %s AND user_id = %s FOR UPDATE",
            (order_no, user_id),
        )
        rows = cur.fetchall()  # habiskan hasil sebelum query berikutnya
        row = rows[0] if rows else None
        if row is None or row["status"] != "menunggu_pembayaran":
            return False
        cur.execute("UPDATE orders SET status = 'dibatalkan' WHERE id = %s", (row["id"],))
        cur.execute(
            "INSERT INTO order_status_history (order_id, title, description) VALUES (%s, %s, %s)",
            (row["id"], "Pesanan dibatalkan", "Dibatalkan oleh pembeli"),
        )
    return True


# ---------------------------------------------------------------------------
# Pelacakan publik (Cek Resi & Pesanan)
# ---------------------------------------------------------------------------
def find_order_no(query):
    """Nomor pesanan dari nomor pesanan ATAU nomor resi; None kalau tidak ada."""
    key = "".join((query or "").split())[:50].upper()
    if not key:
        return None
    row = db.query_one(
        "SELECT order_no FROM orders WHERE order_no = %s OR resi = %s ORDER BY id LIMIT 1",
        (key, key),
    )
    return row["order_no"] if row else None
