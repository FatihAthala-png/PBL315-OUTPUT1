"""Data & aksi admin: daftar pesanan, dashboard, verifikasi pembayaran, pengiriman.

Setiap aksi yang mengubah status berjalan dalam SATU transaksi dengan baris
pesanan dikunci (FOR UPDATE), jadi dua admin yang menekan tombol bersamaan
tidak bisa menyetujui pembayaran yang sama dua kali.
"""
from datetime import datetime

import db
import order_data
from store_config import COURIERS


class AdminError(Exception):
    """Aksi admin gagal. Pesannya aman ditampilkan."""


def escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ---------------------------------------------------------------------------
# Daftar & detail pesanan
# ---------------------------------------------------------------------------
def status_counts():
    rows = db.query_all("SELECT status, COUNT(*) AS n FROM orders GROUP BY status")
    return {r["status"]: int(r["n"]) for r in rows}


def list_orders(status=None, q=None, page=1, per_page=20):
    """-> (baris pesanan, total). Teks SQL tersusun dari potongan tetap; nilai lewat parameter."""
    where, params = [], []
    if status:
        where.append("o.status = %s")
        params.append(status)
    if q:
        like = "%" + escape_like(q) + "%"
        where.append(
            "(o.order_no LIKE %s OR o.recipient_name LIKE %s OR u.email LIKE %s OR o.resi LIKE %s)"
        )
        params += [like, like, like, like]
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    total = int(
        db.query_one(
            "SELECT COUNT(*) AS n FROM orders o JOIN users u ON u.id = o.user_id" + clause,
            tuple(params),
        )["n"]
    )
    rows = db.query_all(
        "SELECT o.order_no, o.status, o.total, o.created_at, o.recipient_name, u.email "
        "FROM orders o JOIN users u ON u.id = o.user_id" + clause +
        " ORDER BY o.created_at DESC, o.id DESC LIMIT %s OFFSET %s",
        tuple(params) + (per_page, (page - 1) * per_page),
    )
    return rows, total


def get_order(order_no):
    """Pesanan lengkap untuk admin (termasuk data pembeli dan jejak verifikasi)."""
    order = order_data.get_order(order_no)
    if order is None:
        return None
    user = db.query_one("SELECT name, email FROM users WHERE id = %s", (order["user_id"],))
    order["user_name"] = user["name"] if user else "-"
    order["user_email"] = user["email"] if user else "-"
    order["payments"] = db.query_all(
        "SELECT p.id, p.method, p.amount, p.proof_path, p.status, p.reject_reason, "
        "p.created_at, p.reviewed_at, a.name AS reviewer "
        "FROM payments p LEFT JOIN users a ON a.id = p.reviewed_by "
        "WHERE p.order_id = %s ORDER BY p.id DESC",
        (order["id"],),
    )
    return order


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def dashboard():
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    omzet = db.query_one(
        "SELECT COALESCE(SUM(amount), 0) AS n FROM payments "
        "WHERE status = 'disetujui' AND reviewed_at >= %s",
        (month_start,),
    )
    pending = db.query_all(
        "SELECT o.order_no, o.total, o.recipient_name, p.created_at "
        "FROM payments p JOIN orders o ON o.id = p.order_id "
        "WHERE p.status = 'menunggu' AND o.status = 'menunggu_approval' "
        "ORDER BY p.created_at, p.id LIMIT 5"
    )
    low_stock = db.query_all(
        "SELECT id, name, stock FROM products WHERE is_active = 1 AND stock <= 3 "
        "ORDER BY stock, id LIMIT 8"
    )
    customers = db.query_one("SELECT COUNT(*) AS n FROM users WHERE role = 'customer'")
    return {
        "counts": status_counts(),
        "omzet": int(omzet["n"]),
        "pending": pending,
        "low_stock": low_stock,
        "customers": int(customers["n"]),
    }


# ---------------------------------------------------------------------------
# Aksi (semua di dalam transaksi)
# ---------------------------------------------------------------------------
def _lock_order(cur, order_no, expected_status, message):
    cur.execute("SELECT id, status FROM orders WHERE order_no = %s FOR UPDATE", (order_no,))
    rows = cur.fetchall()
    if not rows:
        raise AdminError("Pesanan tidak ditemukan.")
    order = rows[0]
    if order["status"] != expected_status:
        raise AdminError(message)
    return order


def _history(cur, order_id, title, description=""):
    cur.execute(
        "INSERT INTO order_status_history (order_id, title, description) VALUES (%s, %s, %s)",
        (order_id, title, description),
    )


def _pending_payment(cur, order_id):
    cur.execute(
        "SELECT id FROM payments WHERE order_id = %s AND status = 'menunggu' "
        "ORDER BY id DESC FOR UPDATE",
        (order_id,),
    )
    rows = cur.fetchall()
    if not rows:
        raise AdminError("Tidak ada bukti pembayaran yang menunggu verifikasi.")
    return rows[0]["id"]


def approve_payment(order_no, admin_id):
    """Setujui pembayaran: stok dikurangi, status jadi 'diproses'."""
    with db.transaction() as cur:
        order = _lock_order(
            cur, order_no, "menunggu_approval", "Pesanan ini tidak sedang menunggu verifikasi."
        )
        payment_id = _pending_payment(cur, order["id"])

        cur.execute(
            "SELECT oi.product_id, oi.qty, oi.product_name, p.stock "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "WHERE oi.order_id = %s ORDER BY oi.product_id FOR UPDATE",
            (order["id"],),
        )
        items = cur.fetchall()
        for it in items:
            if int(it["qty"]) > int(it["stock"]):
                raise AdminError(
                    'Stok "%s" tidak cukup (tersisa %d, dipesan %d). '
                    "Hubungi pembeli atau tolak pembayaran." % (it["product_name"], int(it["stock"]), int(it["qty"]))
                )
        for it in items:
            cur.execute(
                "UPDATE products SET stock = stock - %s WHERE id = %s",
                (int(it["qty"]), it["product_id"]),
            )
        cur.execute(
            "UPDATE payments SET status = 'disetujui', reviewed_by = %s, "
            "reviewed_at = CURRENT_TIMESTAMP WHERE id = %s",
            (admin_id, payment_id),
        )
        cur.execute("UPDATE orders SET status = 'diproses' WHERE id = %s", (order["id"],))
        _history(cur, order["id"], "Pembayaran disetujui", "Pesanan sedang dikemas")


def reject_payment(order_no, admin_id, reason):
    """Tolak bukti bayar: pembeli diminta mengunggah ulang."""
    with db.transaction() as cur:
        order = _lock_order(
            cur, order_no, "menunggu_approval", "Pesanan ini tidak sedang menunggu verifikasi."
        )
        payment_id = _pending_payment(cur, order["id"])
        cur.execute(
            "UPDATE payments SET status = 'ditolak', reject_reason = %s, reviewed_by = %s, "
            "reviewed_at = CURRENT_TIMESTAMP WHERE id = %s",
            (reason, admin_id, payment_id),
        )
        cur.execute("UPDATE orders SET status = 'menunggu_pembayaran' WHERE id = %s", (order["id"],))
        _history(cur, order["id"], "Bukti pembayaran ditolak", reason)


def ship_order(order_no, resi):
    with db.transaction() as cur:
        cur.execute(
            "SELECT id, status, courier FROM orders WHERE order_no = %s FOR UPDATE", (order_no,)
        )
        rows = cur.fetchall()
        if not rows:
            raise AdminError("Pesanan tidak ditemukan.")
        order = rows[0]
        if order["status"] != "diproses":
            raise AdminError("Hanya pesanan berstatus Diproses yang bisa dikirim.")
        courier = COURIERS.get(order["courier"] or "", {}).get("label", order["courier"] or "kurir")
        cur.execute(
            "UPDATE orders SET status = 'dikirim', resi = %s WHERE id = %s", (resi, order["id"])
        )
        _history(cur, order["id"], "Paket diserahkan ke kurir", "%s, resi %s" % (courier, resi))


def complete_order(order_no):
    with db.transaction() as cur:
        order = _lock_order(
            cur, order_no, "dikirim", "Hanya pesanan berstatus Dikirim yang bisa diselesaikan."
        )
        cur.execute("UPDATE orders SET status = 'selesai' WHERE id = %s", (order["id"],))
        _history(cur, order["id"], "Pesanan diterima", "Pesanan selesai")


def cancel_order(order_no, reason):
    """Batalkan pesanan yang belum dibayar (stok belum dikurangi, jadi tidak ada yang dipulihkan)."""
    with db.transaction() as cur:
        order = _lock_order(
            cur, order_no, "menunggu_pembayaran", "Hanya pesanan yang belum dibayar yang bisa dibatalkan."
        )
        cur.execute("UPDATE orders SET status = 'dibatalkan' WHERE id = %s", (order["id"],))
        _history(cur, order["id"], "Pesanan dibatalkan", "Dibatalkan oleh admin: %s" % reason)



# ===========================================================================
# D2: produk, pengguna, laporan
# ===========================================================================
from datetime import timedelta  # noqa: E402

from mysql.connector import errors as mysql_errors  # noqa: E402

PRODUCT_COLUMNS = (
    "id, name, image_url, category, type, sub, brand, rarity, price, "
    "discount_percent, stock, stock_unit, badge, is_preorder, is_active"
)


# ---------------------------------------------------------------------------
# Produk
# ---------------------------------------------------------------------------
def list_products(status=None, q=None, page=1, per_page=20):
    where, params = [], []
    if status == "aktif":
        where.append("is_active = 1")
    elif status == "nonaktif":
        where.append("is_active = 0")
    if q:
        like = "%" + escape_like(q) + "%"
        where.append("(name LIKE %s OR category LIKE %s)")
        params += [like, like]
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    total = int(db.query_one("SELECT COUNT(*) AS n FROM products" + clause, tuple(params))["n"])
    rows = db.query_all(
        "SELECT id, name, image_url, category, type, price, discount_percent, stock, "
        "stock_unit, is_active FROM products" + clause + " ORDER BY id DESC LIMIT %s OFFSET %s",
        tuple(params) + (per_page, (page - 1) * per_page),
    )
    return rows, total


def get_product_row(product_id):
    return db.query_one(
        "SELECT " + PRODUCT_COLUMNS + " FROM products WHERE id = %s", (product_id,)
    )


def save_product(product_id, d):
    """Tambah produk (product_id None) atau ubah. d = nilai yang sudah divalidasi."""
    values = (
        d["name"], d["image_url"], d["category"], d["type"], d["sub"], d["brand"],
        d["rarity"], d["price"], d["discount_percent"], d["stock"], d["stock_unit"],
        d["badge"], d["is_preorder"],
    )
    if product_id is None:
        return db.execute(
            "INSERT INTO products (name, image_url, category, type, sub, brand, rarity, price, "
            "discount_percent, stock, stock_unit, badge, is_preorder) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            values,
        )
    db.execute(
        "UPDATE products SET name = %s, image_url = %s, category = %s, type = %s, sub = %s, "
        "brand = %s, rarity = %s, price = %s, discount_percent = %s, stock = %s, "
        "stock_unit = %s, badge = %s, is_preorder = %s WHERE id = %s",
        values + (product_id,),
    )
    return product_id


def set_product_active(product_id, active):
    db.execute("UPDATE products SET is_active = %s WHERE id = %s", (1 if active else 0, product_id))


def delete_product(product_id):
    """Hapus permanen. -> 'deleted' | 'in_use' (pernah dipesan) | 'not_found'."""
    if get_product_row(product_id) is None:
        return "not_found"
    used = db.query_one("SELECT COUNT(*) AS n FROM order_items WHERE product_id = %s", (product_id,))
    if int(used["n"]) > 0:
        return "in_use"
    try:
        db.execute("DELETE FROM products WHERE id = %s", (product_id,))
    except mysql_errors.IntegrityError:
        return "in_use"
    return "deleted"


# ---------------------------------------------------------------------------
# Pengguna
# ---------------------------------------------------------------------------
def list_users(q=None, role=None, status=None, page=1, per_page=20):
    where, params = [], []
    if role in ("customer", "admin"):
        where.append("u.role = %s")
        params.append(role)
    if status == "aktif":
        where.append("u.is_active = 1")
    elif status == "nonaktif":
        where.append("u.is_active = 0")
    if q:
        like = "%" + escape_like(q) + "%"
        where.append("(u.name LIKE %s OR u.email LIKE %s)")
        params += [like, like]
    clause = (" WHERE " + " AND ".join(where)) if where else ""

    total = int(db.query_one("SELECT COUNT(*) AS n FROM users u" + clause, tuple(params))["n"])
    rows = db.query_all(
        "SELECT u.id, u.name, u.email, u.role, u.is_active, u.created_at, "
        "(SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) AS n_orders "
        "FROM users u" + clause + " ORDER BY u.id DESC LIMIT %s OFFSET %s",
        tuple(params) + (per_page, (page - 1) * per_page),
    )
    return rows, total


def set_user_state(acting_id, user_id, active=None, role=None):
    """Aktifkan/nonaktifkan atau ubah peran, dengan pengaman:

    - tidak boleh mengubah akun sendiri;
    - admin aktif terakhir tidak boleh dinonaktifkan/diturunkan.
    """
    if user_id == acting_id:
        raise AdminError("Kamu tidak bisa mengubah status atau peran akunmu sendiri.")
    if role is not None and role not in ("customer", "admin"):
        raise AdminError("Peran tidak valid.")

    with db.transaction() as cur:
        cur.execute("SELECT id, role, is_active FROM users WHERE id = %s FOR UPDATE", (user_id,))
        rows = cur.fetchall()
        if not rows:
            raise AdminError("Pengguna tidak ditemukan.")
        target = rows[0]
        new_active = int(target["is_active"]) if active is None else (1 if active else 0)
        new_role = target["role"] if role is None else role

        if target["role"] == "admin" and int(target["is_active"]) and (not new_active or new_role != "admin"):
            cur.execute(
                "SELECT COUNT(*) AS n FROM users WHERE role = 'admin' AND is_active = 1 AND id <> %s",
                (user_id,),
            )
            if int(cur.fetchall()[0]["n"]) == 0:
                raise AdminError("Ini admin aktif terakhir; tidak bisa dinonaktifkan atau diturunkan.")

        cur.execute(
            "UPDATE users SET is_active = %s, role = %s WHERE id = %s",
            (new_active, new_role, user_id),
        )


# ---------------------------------------------------------------------------
# Laporan transaksi (transaksi = pembayaran yang disetujui dalam rentang tanggal)
# ---------------------------------------------------------------------------
def _bounds(dari, sampai):
    start = datetime(dari.year, dari.month, dari.day)
    end = datetime(sampai.year, sampai.month, sampai.day) + timedelta(days=1)
    return start, end


def report(dari, sampai, tx_limit=200):
    start, end = _bounds(dari, sampai)
    paid = "p.status = 'disetujui' AND p.reviewed_at >= %s AND p.reviewed_at < %s"

    s = db.query_one(
        "SELECT COUNT(*) AS n, COALESCE(SUM(p.amount), 0) AS omzet, "
        "COALESCE(SUM(o.subtotal), 0) AS barang, COALESCE(SUM(o.shipping_cost), 0) AS ongkir "
        "FROM payments p JOIN orders o ON o.id = p.order_id WHERE " + paid,
        (start, end),
    )
    n, omzet = int(s["n"]), int(s["omzet"])
    summary = {
        "count": n,
        "omzet": omzet,
        "barang": int(s["barang"]),
        "ongkir": int(s["ongkir"]),
        "average": omzet // n if n else 0,
    }
    per_day = [
        {"hari": r["hari"], "n": int(r["n"]), "omzet": int(r["omzet"])}
        for r in db.query_all(
            "SELECT DATE(p.reviewed_at) AS hari, COUNT(*) AS n, SUM(p.amount) AS omzet "
            "FROM payments p JOIN orders o ON o.id = p.order_id WHERE " + paid +
            " GROUP BY DATE(p.reviewed_at) ORDER BY DATE(p.reviewed_at)",
            (start, end),
        )
    ]
    top = [
        {"name": r["product_name"], "qty": int(r["qty"]), "omzet": int(r["omzet"])}
        for r in db.query_all(
            "SELECT oi.product_name, SUM(oi.qty) AS qty, SUM(oi.unit_price * oi.qty) AS omzet "
            "FROM order_items oi JOIN orders o ON o.id = oi.order_id "
            "JOIN payments p ON p.order_id = o.id WHERE " + paid +
            " GROUP BY oi.product_id, oi.product_name ORDER BY qty DESC, omzet DESC LIMIT 10",
            (start, end),
        )
    ]
    status_new = {
        r["status"]: int(r["n"])
        for r in db.query_all(
            "SELECT status, COUNT(*) AS n FROM orders WHERE created_at >= %s AND created_at < %s "
            "GROUP BY status",
            (start, end),
        )
    }
    return {
        "summary": summary,
        "per_day": per_day,
        "top": top,
        "status_new": status_new,
        "transactions": report_transactions(dari, sampai, tx_limit),
    }


def report_transactions(dari, sampai, limit=200):
    start, end = _bounds(dari, sampai)
    return db.query_all(
        "SELECT o.order_no, p.reviewed_at, p.amount, p.method, o.status, o.recipient_name, "
        "u.email, o.courier, o.subtotal, o.shipping_cost "
        "FROM payments p JOIN orders o ON o.id = p.order_id JOIN users u ON u.id = o.user_id "
        "WHERE p.status = 'disetujui' AND p.reviewed_at >= %s AND p.reviewed_at < %s "
        "ORDER BY p.reviewed_at DESC, p.id DESC LIMIT %s",
        (start, end, limit),
    )
