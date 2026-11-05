"""Uji C2 dengan MySQL asli: pencarian, detail produk, ulasan.

Jalankan dari folder proyek (venv aktif):  python smoke_c2.py
Membuat satu user uji + satu ulasan, lalu menghapusnya dan memulihkan
rating produk yang dipakai.
"""
import re
import secrets
import sys
from decimal import ROUND_HALF_UP, Decimal

from markupsafe import escape
from werkzeug.security import generate_password_hash

import db
from app import app

app.config["WTF_CSRF_ENABLED"] = False  # CSRF sudah diuji di smoke_test.py

gagal = 0


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def jumlah_kartu(r):
    return len(re.findall(r"<article\s+data-product", teks(r)))


c = app.test_client()
prod = db.query_one("SELECT id, name FROM products WHERE is_active = 1 ORDER BY id LIMIT 1")
pid = prod["id"]
awal = db.query_one("SELECT rating, review_count FROM products WHERE id = %s", (pid,))
# Ulasan yang sudah ada (mis. dari uji manual di browser) ikut dihitung.
sebelum = db.query_one(
    "SELECT COUNT(*) AS n, COALESCE(SUM(rating), 0) AS s FROM reviews WHERE product_id = %s", (pid,)
)

email = "smoke-c2-%s@example.com" % secrets.token_hex(4)
sandi = "Smoke#Test2026"

try:
    # --- pencarian ---
    r = c.get("/semua-produk?q=pikachu")
    cek("cari 'pikachu' -> ada hasil", r.status_code == 200 and jumlah_kartu(r) >= 1, "%s kartu" % jumlah_kartu(r))
    r = c.get("/semua-produk?q=zzzzqqqq")
    cek("cari kata ngawur -> 0 kartu", r.status_code == 200 and jumlah_kartu(r) == 0, "%s kartu" % jumlah_kartu(r))
    r = c.get("/semua-produk?q=" + "a" * 500)
    cek("kata pencarian sangat panjang tidak error", r.status_code == 200, r.status_code)

    # --- detail produk ---
    r = c.get("/produk/%d" % pid)
    cek("detail produk tampil + nama produk", r.status_code == 200 and str(escape(prod["name"])) in teks(r), r.status_code)
    cek("tamu: ajakan masuk untuk ulasan", "Masuk untuk menulis ulasan" in teks(r))
    cek("produk tidak ada -> 404", c.get("/produk/999999").status_code == 404)

    r = c.post("/produk/%d/ulasan" % pid, data={"rating": "5", "comment": "tamu"})
    cek("tamu kirim ulasan -> diarahkan ke /login", r.status_code == 302 and "/login" in r.headers["Location"], r.status_code)

    # --- ulasan oleh user login ---
    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        ("Penguji Ulasan", email, generate_password_hash(sandi)),
    )
    c.post("/login", data={"email": email, "password": sandi})
    r = c.get("/produk/%d" % pid)
    cek("user login melihat form ulasan", "Kirim Ulasan" in teks(r))

    url = "/produk/%d/ulasan" % pid
    r = c.post(url, data={"rating": "0", "comment": "x"}, follow_redirects=True)
    cek("rating 0 ditolak", "Pilih rating" in teks(r))
    r = c.post(url, data={"rating": "6", "comment": "x"}, follow_redirects=True)
    cek("rating 6 ditolak", "Pilih rating" in teks(r))
    r = c.post(url, data={"rating": "abc", "comment": "x"}, follow_redirects=True)
    cek("rating bukan angka ditolak", "Pilih rating" in teks(r))
    r = c.post(url, data={"rating": "5", "comment": "   "}, follow_redirects=True)
    cek("komentar kosong ditolak", "Komentar wajib diisi" in teks(r))
    r = c.post(url, data={"rating": "5", "comment": "x" * 1001}, follow_redirects=True)
    cek("komentar >1000 karakter ditolak", "terlalu panjang" in teks(r))

    xss = "<script>alert(1)</script> bagus"
    r = c.post(url, data={"rating": "4", "comment": xss}, follow_redirects=True)
    html = teks(r)
    cek("ulasan valid tersimpan", "Terima kasih" in html)
    cek("XSS di komentar di-escape", "&lt;script&gt;alert(1)" in html and "<script>alert(1)</script>" not in html)
    bagian_ulasan = html.split('id="ulasan"', 1)[1]  # header memang memuat nama lengkap user
    cek("nama pengulas disamarkan (Penguji U.)", "Penguji U." in bagian_ulasan and "Penguji Ulasan" not in bagian_ulasan)

    agg = db.query_one("SELECT rating, review_count FROM products WHERE id = %s", (pid,))
    n_akhir = int(sebelum["n"]) + 1
    rata = ((Decimal(int(sebelum["s"])) + 4) / n_akhir).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    cek(
        "rating & jumlah ulasan dihitung ulang",
        int(agg["review_count"]) == n_akhir and Decimal(str(agg["rating"])) == rata,
        "%s (harapan: %d ulasan, rata-rata %s)" % (agg, n_akhir, rata),
    )

    r = c.post(url, data={"rating": "5", "comment": "ulasan kedua"}, follow_redirects=True)
    cek("ulasan kedua oleh user sama ditolak", "sudah pernah" in teks(r))
    r = c.get("/produk/%d" % pid)
    cek("form hilang setelah mengulas", "Kirim Ulasan" not in teks(r) and "sudah memberi ulasan" in teks(r))
finally:
    db.execute("DELETE FROM users WHERE email = %s", (email,))  # ulasan ikut terhapus (CASCADE)
    db.execute(
        "UPDATE products SET rating = %s, review_count = %s WHERE id = %s",
        (awal["rating"], awal["review_count"], pid),
    )

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
