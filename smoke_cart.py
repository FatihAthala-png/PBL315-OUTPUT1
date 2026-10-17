"""Uji keranjang dengan MySQL asli: tambah, ubah, hapus, batas stok, isolasi antar user.

Jalankan dari folder proyek (venv aktif):  python smoke_cart.py
Membuat dua user uji, lalu menghapusnya (isi keranjang ikut terhapus).
"""
import re
import secrets
import sys

from werkzeug.security import generate_password_hash

import db
from app import app

gagal = 0
JSON = {"X-Requested-With": "fetch"}
sandi = "Smoke#Test2026"


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def badge(r):
    m = re.search(r"data-cart-count[^>]*>\s*(\d+)\s*<", teks(r))
    return int(m.group(1)) if m else None


def buat_user(nama):
    email = "smoke-cart-%s@example.com" % secrets.token_hex(4)
    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        (nama, email, generate_password_hash(sandi)),
    )
    return email


emails = []
try:
    produk = db.query_one(
        "SELECT id, name, stock FROM products WHERE is_active = 1 AND stock >= 2 ORDER BY id LIMIT 1"
    )
    pid, stok = produk["id"], int(produk["stock"])
    batas = min(stok, 99)

    # --- CSRF tetap aktif untuk endpoint keranjang ---
    app.config["WTF_CSRF_ENABLED"] = True
    r = app.test_client().post("/keranjang/tambah", data={"product_id": pid}, headers=JSON)
    cek("POST tambah tanpa token CSRF ditolak", r.status_code == 400, r.status_code)
    app.config["WTF_CSRF_ENABLED"] = False

    # --- tamu ---
    tamu = app.test_client()
    r = tamu.get("/keranjang")
    cek("tamu buka /keranjang -> diarahkan ke login", r.status_code == 302 and "/login" in r.headers["Location"], r.status_code)
    r = tamu.post("/keranjang/tambah", data={"product_id": pid, "next": "/semua-produk"}, headers=JSON)
    j = r.get_json()
    cek("tamu tambah (AJAX) -> 401 + login_url", r.status_code == 401 and "/login" in j["login_url"] and "next=" in j["login_url"], r.status_code)

    # --- user A ---
    a_email = buat_user("Pembeli Satu"); emails.append(a_email)
    a = app.test_client()
    a.post("/login", data={"email": a_email, "password": sandi})

    r = a.get("/keranjang")
    cek("keranjang kosong tampil", r.status_code == 200 and "Keranjang masih kosong" in teks(r), r.status_code)

    r = a.post("/keranjang/tambah", data={"product_id": pid, "qty": 1}, headers=JSON)
    j = r.get_json()
    cek("tambah 1 -> ok, count 1", r.status_code == 200 and j["ok"] and j["count"] == 1 and j["qty"] == 1, j)
    r = a.post("/keranjang/tambah", data={"product_id": pid, "qty": 1}, headers=JSON)
    j = r.get_json()
    cek("tambah lagi -> qty 2, count 2", j["qty"] == 2 and j["count"] == 2, j)

    r = a.get("/")
    cek("badge header menampilkan 2", badge(r) == 2, badge(r))
    r = a.get("/keranjang")
    cek("halaman keranjang memuat produk", r.status_code == 200 and "Ringkasan Belanja" in teks(r) and str(pid) in teks(r))

    r = a.post("/keranjang/tambah", data={"product_id": pid, "qty": 500}, headers=JSON)
    j = r.get_json()
    cek("qty besar dibatasi stok (maks %d)" % batas, j["qty"] == batas and j["limited"] is True, j)

    r = a.post("/keranjang/tambah", data={"product_id": 999999}, headers=JSON)
    cek("produk tidak ada -> 404", r.status_code == 404 and r.get_json()["ok"] is False, r.status_code)
    r = a.post("/keranjang/tambah", data={"product_id": "abc"}, headers=JSON)
    cek("product_id bukan angka -> 400", r.status_code == 400, r.status_code)
    r = a.post("/keranjang/tambah", data={"product_id": pid, "qty": "-3"}, headers=JSON)
    cek("qty negatif -> 400", r.status_code == 400, r.status_code)
    r = a.post("/keranjang/tambah", data={"product_id": pid, "qty": "abc"}, headers=JSON)
    cek("qty bukan angka -> 400", r.status_code == 400, r.status_code)

    # --- ubah & hapus (form biasa) ---
    r = a.post("/keranjang/ubah", data={"product_id": pid, "qty": 1}, follow_redirects=True)
    j = db.query_one("SELECT qty FROM cart_items c JOIN users u ON u.id = c.user_id WHERE u.email = %s AND c.product_id = %s", (a_email, pid))
    cek("ubah qty jadi 1", r.status_code == 200 and j and j["qty"] == 1, j)
    r = a.post("/keranjang/ubah", data={"product_id": pid, "qty": 0}, follow_redirects=True)
    j = db.query_one("SELECT c.id FROM cart_items c JOIN users u ON u.id = c.user_id WHERE u.email = %s AND c.product_id = %s", (a_email, pid))
    cek("ubah qty ke 0 menghapus item", j is None and "dihapus" in teks(r))

    a.post("/keranjang/tambah", data={"product_id": pid, "qty": 1}, headers=JSON)
    r = a.post("/keranjang/hapus", data={"product_id": pid}, follow_redirects=True)
    cek("hapus item", "Keranjang masih kosong" in teks(r))

    # --- isolasi antar user ---
    a.post("/keranjang/tambah", data={"product_id": pid, "qty": 2}, headers=JSON)
    b_email = buat_user("Pembeli Dua"); emails.append(b_email)
    b = app.test_client()
    b.post("/login", data={"email": b_email, "password": sandi})
    r = b.get("/keranjang")
    cek("user B tidak melihat keranjang user A", "Keranjang masih kosong" in teks(r))
    b.post("/keranjang/hapus", data={"product_id": pid})
    b.post("/keranjang/ubah", data={"product_id": pid, "qty": 9})
    r = a.get("/")
    cek("keranjang user A utuh setelah B mencoba mengubah", badge(r) == 2, badge(r))

    # --- fallback tanpa JS: form biasa ---
    r = a.post("/keranjang/tambah", data={"product_id": pid, "qty": 1, "next": "//evil.example"})
    cek("form biasa: redirect aman (tidak ke situs luar)", r.status_code == 302 and "evil" not in r.headers["Location"], r.headers.get("Location"))
finally:
    for e in emails:
        db.execute("DELETE FROM users WHERE email = %s", (e,))  # keranjang ikut terhapus (CASCADE)

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
