"""Uji checkout, upload bukti bayar, dan riwayat pesanan dengan MySQL asli.

Jalankan dari folder proyek (venv aktif):  python smoke_order.py
Membuat user & pesanan uji, lalu menghapus semuanya (termasuk berkas upload)
dan memulihkan stok produk yang dipakai.
"""
import io
import re
import secrets
import sys

from werkzeug.security import generate_password_hash

import db
from app import app
from store_config import COURIERS, UPLOAD_DIR

gagal = 0
sandi = "Smoke#Test2026"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
ALAMAT = {
    "recipient_name": "Penerima Uji",
    "phone": "081234567890",
    "address": "Jl. Contoh No. 1",
    "city": "Batam",
    "province": "Kepulauan Riau",
    "postal_code": "29432",
    "shipping": "jne:REG",
}


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def buat_user(nama):
    email = "smoke-ord-%s@example.com" % secrets.token_hex(4)
    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        (nama, email, generate_password_hash(sandi)),
    )
    return email


def login(email):
    c = app.test_client()
    c.post("/login", data={"email": email, "password": sandi})
    return c


def jumlah_pesanan(email):
    return db.query_one(
        "SELECT COUNT(*) AS n FROM orders o JOIN users u ON u.id = o.user_id WHERE u.email = %s", (email,)
    )["n"]


def status_pesanan(no):
    return db.query_one("SELECT status FROM orders WHERE order_no = %s", (no,))["status"]


def buat_pesanan(c, pid, qty=2):
    c.post("/keranjang/tambah", data={"product_id": pid, "qty": qty}, headers={"X-Requested-With": "fetch"})
    r = c.post("/checkout", data=ALAMAT)
    return r, (r.headers.get("Location", "").rsplit("/", 1)[-1] if r.status_code == 302 else None)


emails = []
stok_asli = None
try:
    p = db.query_one("SELECT id, name, price, stock FROM products WHERE is_active = 1 AND stock >= 3 ORDER BY id LIMIT 1")
    pid, harga, stok_asli = p["id"], int(p["price"]), int(p["stock"])

    # --- tamu & CSRF ---
    tamu = app.test_client()
    for path in ("/checkout", "/pesanan"):
        r = tamu.get(path)
        cek("tamu buka %s -> login" % path, r.status_code == 302 and "/login" in r.headers["Location"], r.status_code)
    app.config["WTF_CSRF_ENABLED"] = True
    r = tamu.post("/checkout", data=ALAMAT)
    cek("POST /checkout tanpa token CSRF ditolak", r.status_code == 400, r.status_code)
    app.config["WTF_CSRF_ENABLED"] = False

    # --- user A: checkout ---
    a_email = buat_user("Pembeli Satu"); emails.append(a_email)
    a = login(a_email)
    r = a.get("/checkout")
    cek("keranjang kosong -> checkout diarahkan ke /keranjang", r.status_code == 302 and "/keranjang" in r.headers["Location"], r.status_code)

    a.post("/keranjang/tambah", data={"product_id": pid, "qty": 2}, headers={"X-Requested-With": "fetch"})
    r = a.get("/checkout")
    cek("halaman checkout tampil", r.status_code == 200 and "Alamat Pengiriman" in teks(r) and "Buat Pesanan" in teks(r), r.status_code)

    for label, ubah, kata in [
        ("alamat kosong ditolak", {"address": ""}, "Alamat wajib diisi"),
        ("telepon tidak valid ditolak", {"phone": "abc"}, "Nomor telepon tidak valid"),
        ("kode pos tidak valid ditolak", {"postal_code": "12ab"}, "Kode pos harus 5 digit"),
        ("layanan pengiriman ngawur ditolak", {"shipping": "x:y"}, "Pilih layanan pengiriman"),
    ]:
        r = a.post("/checkout", data={**ALAMAT, **ubah}, follow_redirects=True)
        cek(label, r.status_code == 200 and kata in teks(r) and jumlah_pesanan(a_email) == 0, r.status_code)

    # harga dari input user diabaikan
    r = a.post("/checkout", data={**ALAMAT, "total": "1", "price": "1", "subtotal": "1", "shipping_cost": "0"})
    no1 = r.headers["Location"].rsplit("/", 1)[-1] if r.status_code == 302 else None
    cek("checkout valid -> diarahkan ke detail pesanan", r.status_code == 302 and no1 and no1.startswith("KMS-"), r.headers.get("Location"))

    o = db.query_one("SELECT * FROM orders WHERE order_no = %s", (no1,))
    ongkir = COURIERS["jne"]["services"]["REG"][1]
    cek("total dihitung server (subtotal + ongkir)", int(o["subtotal"]) == harga * 2 and int(o["shipping_cost"]) == ongkir and int(o["total"]) == harga * 2 + ongkir, "total=%s" % o["total"])
    cek("status awal menunggu_pembayaran", o["status"] == "menunggu_pembayaran")
    it = db.query_one("SELECT product_name, unit_price, qty FROM order_items WHERE order_id = %s", (o["id"],))
    cek("item pesanan menyimpan salinan nama & harga", it["product_name"] == p["name"] and int(it["unit_price"]) == harga and int(it["qty"]) == 2)
    n_keranjang = db.query_one("SELECT COUNT(*) AS n FROM cart_items c JOIN users u ON u.id = c.user_id WHERE u.email = %s", (a_email,))["n"]
    cek("keranjang dikosongkan setelah checkout", n_keranjang == 0, n_keranjang)
    cek("riwayat awal tercatat", db.query_one("SELECT COUNT(*) AS n FROM order_status_history WHERE order_id = %s", (o["id"],))["n"] == 1)

    r = a.post("/checkout", data=ALAMAT)
    cek("kirim ulang (keranjang kosong) tidak membuat pesanan baru", r.status_code == 302 and jumlah_pesanan(a_email) == 1, jumlah_pesanan(a_email))

    # --- detail & kepemilikan ---
    r = a.get("/pesanan/" + no1)
    cek("detail pesanan milik sendiri tampil", r.status_code == 200 and no1 in teks(r) and "Menunggu Pembayaran" in teks(r), r.status_code)
    b_email = buat_user("Pembeli Dua"); emails.append(b_email)
    b = login(b_email)
    cek("user lain tidak bisa membuka detail (404)", b.get("/pesanan/" + no1).status_code == 404)
    cek("user lain tidak bisa upload ke pesanan itu (404)", b.post("/pesanan/%s/bayar" % no1, data={"method": "bca"}).status_code == 404)
    cek("user lain tidak bisa membatalkan (404)", b.post("/pesanan/%s/batal" % no1).status_code == 404)
    cek("tamu tidak bisa membuka detail", tamu.get("/pesanan/" + no1).status_code == 302)

    # --- upload bukti bayar ---
    url = "/pesanan/%s/bayar" % no1
    r = a.post(url, data={"method": "bca"}, follow_redirects=True)
    cek("tanpa berkas ditolak", "Pilih berkas" in teks(r))
    r = a.post(url, data={"method": "bca", "bukti": (io.BytesIO(b"bukan gambar"), "bukti.png")}, content_type="multipart/form-data", follow_redirects=True)
    cek("berkas teks bernama .png ditolak (cek isi, bukan nama)", "Format berkas tidak didukung" in teks(r))
    r = a.post(url, data={"method": "ngawur", "bukti": (io.BytesIO(PNG), "b.png")}, content_type="multipart/form-data", follow_redirects=True)
    cek("metode pembayaran ngawur ditolak", "Pilih metode" in teks(r))
    r = a.post(url, data={"method": "bca", "bukti": (io.BytesIO(b"x" * (6 * 1024 * 1024)), "besar.png")}, content_type="multipart/form-data")
    cek("berkas > 5 MB ditolak", r.status_code == 302 and status_pesanan(no1) == "menunggu_pembayaran", r.status_code)

    r = a.post(url, data={"method": "bca", "bukti": (io.BytesIO(PNG), "../../etc/passwd.png")}, content_type="multipart/form-data", follow_redirects=True)
    cek("PNG valid diterima", "Bukti pembayaran terkirim" in teks(r))
    cek("status jadi menunggu_approval", status_pesanan(no1) == "menunggu_approval")
    pay = db.query_one("SELECT proof_path, status, amount FROM payments WHERE order_id = %s", (o["id"],))
    cek("pembayaran tercatat (menunggu, jumlah = total)", pay and pay["status"] == "menunggu" and int(pay["amount"]) == int(o["total"]))
    cek("nama berkas acak, bukan dari user", re.fullmatch(r"payments/[0-9a-f]{32}\.png", pay["proof_path"]) is not None, pay["proof_path"])
    cek("berkas tersimpan di folder upload", (UPLOAD_DIR / pay["proof_path"]).is_file())
    r = a.post(url, data={"method": "bca", "bukti": (io.BytesIO(PNG), "lagi.png")}, content_type="multipart/form-data", follow_redirects=True)
    cek("upload kedua ditolak (sudah menunggu verifikasi)", "tidak bisa menerima" in teks(r))

    # --- akses berkas bukti ---
    r = a.get("/pesanan/%s/bukti" % no1)
    cek("pemilik bisa melihat bukti (image/png + nosniff)", r.status_code == 200 and r.mimetype == "image/png" and r.headers.get("X-Content-Type-Options") == "nosniff", r.status_code)
    cek("user lain tidak bisa melihat bukti (404)", b.get("/pesanan/%s/bukti" % no1).status_code == 404)
    cek("tamu tidak bisa melihat bukti", tamu.get("/pesanan/%s/bukti" % no1).status_code == 302)
    cek("berkas upload tidak bisa dibuka lewat /static", a.get("/static/" + pay["proof_path"]).status_code == 404)

    # --- batal ---
    r = a.post("/pesanan/%s/batal" % no1, follow_redirects=True)
    cek("pesanan yang sudah dibayar tidak bisa dibatalkan", "sudah tidak bisa dibatalkan" in teks(r) and status_pesanan(no1) == "menunggu_approval")
    _, no2 = buat_pesanan(a, pid, 1)
    cek("pesanan kedua dibuat", no2 is not None and no2 != no1, no2)
    r = a.post("/pesanan/%s/batal" % no2, follow_redirects=True)
    cek("pesanan belum dibayar bisa dibatalkan", "Pesanan dibatalkan" in teks(r) and status_pesanan(no2) == "dibatalkan")
    r = a.post("/pesanan/%s/bayar" % no2, data={"method": "bca", "bukti": (io.BytesIO(PNG), "x.png")}, content_type="multipart/form-data", follow_redirects=True)
    cek("upload ke pesanan dibatalkan ditolak", "tidak bisa menerima" in teks(r) and status_pesanan(no2) == "dibatalkan")

    # --- riwayat ---
    r = a.get("/pesanan")
    cek("riwayat memuat kedua pesanan", r.status_code == 200 and no1 in teks(r) and no2 in teks(r))
    cek("riwayat user lain tidak memuat pesanan A", no1 not in teks(b.get("/pesanan")))

    # --- stok tidak cukup ---
    db.execute("UPDATE products SET stock = 1 WHERE id = %s", (pid,))
    a.post("/keranjang/tambah", data={"product_id": pid, "qty": 1}, headers={"X-Requested-With": "fetch"})
    uid_a = db.query_one("SELECT id FROM users WHERE email = %s", (a_email,))["id"]
    db.execute("UPDATE cart_items SET qty = 2 WHERE user_id = %s AND product_id = %s", (uid_a, pid))  # lewati batas keranjang
    sebelum = jumlah_pesanan(a_email)
    r = a.post("/checkout", data=ALAMAT, follow_redirects=True)
    cek("stok tidak cukup -> pesanan ditolak", "tidak cukup" in teks(r) and jumlah_pesanan(a_email) == sebelum, jumlah_pesanan(a_email))
finally:
    for e in emails:
        for row in db.query_all(
            "SELECT pay.proof_path FROM payments pay JOIN orders o ON o.id = pay.order_id "
            "JOIN users u ON u.id = o.user_id WHERE u.email = %s", (e,),
        ):
            (UPLOAD_DIR / row["proof_path"]).unlink(missing_ok=True)
        u = db.query_one("SELECT id FROM users WHERE email = %s", (e,))
        if u:
            db.execute("DELETE FROM orders WHERE user_id = %s", (u["id"],))  # item, pembayaran, riwayat ikut terhapus
            db.execute("DELETE FROM users WHERE id = %s", (u["id"],))
    if stok_asli is not None:
        db.execute("UPDATE products SET stock = %s WHERE id = %s", (stok_asli, pid))

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
