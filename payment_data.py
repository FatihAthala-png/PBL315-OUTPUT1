"""Pembayaran Midtrans: percobaan bayar, penerapan hasil, sinkronisasi status.

Pesanan yang dibayar lewat Midtrans langsung berstatus 'diproses' (stok dikurangi),
tanpa menunggu verifikasi admin. Pembayaran manual (upload bukti) tetap ada.

Kasus tepi yang ditangani: notifikasi ganda (idempoten), nominal tidak cocok,
stok habis saat pembayaran masuk, pesanan sudah dibatalkan, pembayaran ganda.
"""
import logging
from decimal import Decimal, InvalidOperation

import db
import midtrans
import order_data
from midtrans import MidtransError, MidtransNotFound

log = logging.getLogger("kamistore.midtrans")


class PaymentError(Exception):
    """Pesan aman ditampilkan ke user; `status` = kode HTTP yang cocok."""

    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def gateway_id(order_no, payment_id):
    """order_id di Midtrans: unik per percobaan bayar (Midtrans menolak order_id yang sama)."""
    return "%s-%d" % (order_no, payment_id)


def split_gateway_id(value):
    order_no, sep, pid = str(value).rpartition("-")
    if not sep or not order_no or not pid.isdigit():
        return None
    return order_no, int(pid)


def _history_once(cur, order_id, title, description):
    cur.execute(
        "SELECT id FROM order_status_history WHERE order_id = %s AND title = %s AND description = %s",
        (order_id, title, description),
    )
    if not cur.fetchall():
        cur.execute(
            "INSERT INTO order_status_history (order_id, title, description) VALUES (%s, %s, %s)",
            (order_id, title, description),
        )


def _mark_failed(payment_id, reason):
    db.execute(
        "UPDATE payments SET status = 'ditolak', reject_reason = %s, reviewed_at = CURRENT_TIMESTAMP "
        "WHERE id = %s AND status = 'menunggu'",
        (reason[:255], payment_id),
    )


# ---------------------------------------------------------------------------
# Menerapkan hasil dari Midtrans (webhook ATAU Status API)
# ---------------------------------------------------------------------------
def apply_result(payment_id, payload, order_no=None):
    """Terapkan status transaksi ke pesanan. Aman dipanggil berulang (idempoten).

    -> unknown | bad_amount | amount_mismatch | noted | already_final | pending |
       failed | paid | paid_cancelled | duplicate | stock_short
    """
    kind = midtrans.classify(payload)
    ptype = str(payload.get("payment_type") or "-")[:30]
    tstatus = str(payload.get("transaction_status") or "-")[:30]

    pre = db.query_one(
        "SELECT p.id, p.method, p.order_id, o.order_no, o.total "
        "FROM payments p JOIN orders o ON o.id = p.order_id WHERE p.id = %s",
        (payment_id,),
    )
    if pre is None or pre["method"] != "midtrans":
        return "unknown"
    if order_no is not None and pre["order_no"] != order_no:
        return "unknown"
    try:
        gross = Decimal(str(payload.get("gross_amount")))
    except InvalidOperation:
        return "bad_amount"
    if gross != Decimal(int(pre["total"])):
        return "amount_mismatch"

    with db.transaction() as cur:
        cur.execute("SELECT id, status FROM orders WHERE id = %s FOR UPDATE", (pre["order_id"],))
        order = cur.fetchall()[0]
        cur.execute("SELECT id, status FROM payments WHERE id = %s FOR UPDATE", (payment_id,))
        pay = cur.fetchall()[0]
        oid = order["id"]

        if kind == "info":
            _history_once(cur, oid, "Catatan Midtrans: %s" % tstatus, "Periksa dashboard Midtrans (refund/chargeback)")
            return "noted"
        # Uang yang masuk selalu diproses, bahkan bila percobaan ini sempat ditandai gagal.
        if kind in ("pending", "failed") and pay["status"] != "menunggu":
            return "already_final"
        if kind == "paid" and pay["status"] == "disetujui":
            return "already_final"

        if kind == "pending":
            _history_once(cur, oid, "Menunggu pembayaran via Midtrans", "Metode: %s" % ptype)
            return "pending"

        if kind == "failed":
            cur.execute(
                "UPDATE payments SET status = 'ditolak', reject_reason = %s, "
                "reviewed_at = CURRENT_TIMESTAMP WHERE id = %s",
                ("Midtrans: %s" % tstatus, payment_id),
            )
            _history_once(cur, oid, "Pembayaran Midtrans tidak berhasil", "Status: %s. Silakan coba bayar lagi." % tstatus)
            return "failed"

        # ------------------------------------------------------------- paid
        approve = (
            "UPDATE payments SET status = 'disetujui', reject_reason = NULL, "
            "reviewed_at = CURRENT_TIMESTAMP WHERE id = %s"
        )
        if order["status"] == "dibatalkan":
            cur.execute(approve, (payment_id,))
            _history_once(cur, oid, "Pembayaran Midtrans diterima untuk pesanan yang sudah dibatalkan",
                          "Perlu refund lewat dashboard Midtrans")
            return "paid_cancelled"
        if order["status"] in ("diproses", "dikirim", "selesai"):
            cur.execute(approve, (payment_id,))
            _history_once(cur, oid, "Pembayaran Midtrans ganda diterima", "Perlu refund lewat dashboard Midtrans")
            return "duplicate"

        # status: menunggu_pembayaran / menunggu_approval -> cek & kurangi stok
        cur.execute(
            "SELECT oi.product_id, oi.qty, oi.product_name, p.stock "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "WHERE oi.order_id = %s ORDER BY oi.product_id FOR UPDATE",
            (oid,),
        )
        items = cur.fetchall()
        if any(int(it["qty"]) > int(it["stock"]) for it in items):
            cur.execute("UPDATE orders SET status = 'menunggu_approval' WHERE id = %s", (oid,))
            _history_once(cur, oid, "Pembayaran Midtrans diterima, stok tidak cukup",
                          "Perlu tindakan admin: tambah stok lalu setujui, atau refund lewat Midtrans")
            return "stock_short"

        for it in items:
            cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (int(it["qty"]), it["product_id"]))
        cur.execute(approve, (payment_id,))
        cur.execute(
            "UPDATE payments SET status = 'ditolak', reject_reason = 'Pesanan sudah dibayar lewat Midtrans', "
            "reviewed_at = CURRENT_TIMESTAMP WHERE order_id = %s AND status = 'menunggu' AND id <> %s",
            (oid, payment_id),
        )
        cur.execute("UPDATE orders SET status = 'diproses' WHERE id = %s", (oid,))
        _history_once(cur, oid, "Pembayaran diterima via Midtrans", "Metode: %s" % ptype)
        _history_once(cur, oid, "Pembayaran disetujui", "Pesanan sedang dikemas")
        return "paid"


def handle_notification(payload):
    """Webhook Midtrans. -> 'bad_signature' | 'ignored' | hasil apply_result."""
    if not midtrans.signature_ok(payload):
        return "bad_signature"
    ref = split_gateway_id(payload.get("order_id", ""))
    if ref is None:
        return "ignored"
    return apply_result(ref[1], payload, ref[0])


# ---------------------------------------------------------------------------
# Memulai pembayaran & sinkronisasi manual
# ---------------------------------------------------------------------------
def start_attempt(order_no, user_id):
    """Buat percobaan bayar baru dan kembalikan {'token', 'redirect_url'} dari Snap."""
    order = order_data.get_order(order_no, user_id)
    if order is None:
        raise PaymentError("Pesanan tidak ditemukan.", 404)
    if order["status"] != "menunggu_pembayaran":
        raise PaymentError("Pesanan ini tidak sedang menunggu pembayaran.", 409)

    # Percobaan lama yang masih 'menunggu': periksa dulu supaya tidak terjadi bayar dua kali.
    for pay in order["payments"]:
        if pay["method"] != "midtrans" or pay["status"] != "menunggu":
            continue
        try:
            payload = midtrans.get_status(gateway_id(order_no, pay["id"]))
        except MidtransNotFound:
            _mark_failed(pay["id"], "Percobaan pembayaran tidak dilanjutkan")
            continue
        except MidtransError:
            raise PaymentError("Tidak bisa memeriksa pembayaran sebelumnya. Coba lagi sebentar lagi.", 502)
        outcome = apply_result(pay["id"], payload, order_no)
        if outcome == "pending":
            raise PaymentError(
                "Ada pembayaran Midtrans yang masih menunggu. Selesaikan pembayarannya "
                "(atau tunggu kedaluwarsa), lalu tekan Cek status.", 409)
        if outcome in ("paid", "stock_short", "duplicate", "paid_cancelled"):
            raise PaymentError("Pembayaran sebelumnya sudah diterima. Muat ulang halaman ini.", 409)

    with db.transaction() as cur:
        cur.execute(
            "SELECT status FROM orders WHERE order_no = %s AND user_id = %s FOR UPDATE", (order_no, user_id)
        )
        rows = cur.fetchall()
        if not rows or rows[0]["status"] != "menunggu_pembayaran":
            raise PaymentError("Pesanan ini tidak sedang menunggu pembayaran.", 409)
        cur.execute(
            "INSERT INTO payments (order_id, method, amount, proof_path) VALUES (%s, 'midtrans', %s, 'midtrans')",
            (order["id"], int(order["total"])),
        )
        payment_id = cur.lastrowid

    user = db.query_one("SELECT email FROM users WHERE id = %s", (user_id,))
    try:
        return midtrans.create_snap(
            gateway_id(order_no, payment_id),
            int(order["total"]),
            {"first_name": order["recipient_name"][:100], "email": user["email"], "phone": order["phone"]},
            midtrans.build_items(order["items"], int(order["shipping_cost"])),
        )
    except MidtransError as exc:
        log.warning("MIDTRANS_SNAP_FAILED order=%s detail=%s", order_no, exc)
        _mark_failed(payment_id, "Gagal membuat transaksi Midtrans")
        raise PaymentError("Midtrans tidak merespons. Coba lagi beberapa saat lagi.", 502)


def sync_order(order_no, user_id):
    """Tanyakan status ke Midtrans untuk semua percobaan yang masih menunggu. -> daftar hasil."""
    order = order_data.get_order(order_no, user_id)
    if order is None:
        raise PaymentError("Pesanan tidak ditemukan.", 404)
    outcomes = []
    for pay in order["payments"]:
        if pay["method"] != "midtrans" or pay["status"] != "menunggu":
            continue
        try:
            payload = midtrans.get_status(gateway_id(order_no, pay["id"]))
        except MidtransNotFound:
            _mark_failed(pay["id"], "Percobaan pembayaran tidak dilanjutkan")
            outcomes.append("failed")
            continue
        except MidtransError:
            raise PaymentError("Tidak bisa memeriksa status ke Midtrans. Coba lagi sebentar lagi.", 502)
        outcomes.append(apply_result(pay["id"], payload, order_no))
    return outcomes
