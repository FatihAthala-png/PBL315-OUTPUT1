"""Uji cepat semua halaman utama + proteksi CSRF.

Jalankan dari folder proyek (venv aktif):  python smoke_test.py
Butuh MySQL menyala dan .env terisi.
"""
import sys

from app import app

client = app.test_client()
gagal = 0


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def get(path, status=200, contains=None, location=None):
    r = client.get(path)
    body = r.get_data(as_text=True)
    ok = r.status_code == status
    if contains:
        ok = ok and contains in body
    if location:
        ok = ok and location in r.headers.get("Location", "")
    cek("GET  " + path, ok, "-> %s" % r.status_code)


get("/")
get("/semua-produk")
get("/semua-produk?type=tcg")
get("/pokemon-tcg", 302, location="/semua-produk?type=tcg")
get("/action-figures", 302, location="/semua-produk?type=figure")
get("/login")
get("/register")
get("/cek-resi-pesanan")
get("/cek-resi-pesanan?q=TIDAK-ADA", contains="tidak ditemukan")
get("/halaman-tidak-ada", 404)

# CSRF: POST tanpa token harus ditolak (400).
for path in ("/login", "/register"):
    r = client.post(path, data={})
    cek("POST " + path + " tanpa token", r.status_code == 400, "-> %s" % r.status_code)

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
