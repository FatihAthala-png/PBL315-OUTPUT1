"""Uji alur akun dengan MySQL asli: register, login, next, logout, nonaktif.

Jalankan dari folder proyek (venv aktif):  python smoke_auth.py
Membuat satu user uji lalu menghapusnya lagi di akhir.
"""
import os
import secrets
import sys

os.environ["OTP_REGISTER"] = "0"  # alur registrasi tanpa OTP; OTP diuji di smoke_otp.py

import db
from app import app

app.config["WTF_CSRF_ENABLED"] = False  # alur diuji; CSRF sudah diuji di smoke_test.py

email = "smoke-%s@example.com" % secrets.token_hex(4)
nama = "Smoke Tester"
sandi = "Smoke#Test2026"
gagal = 0


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


try:
    c = app.test_client()

    r = c.post("/register", data={"email": email, "nama": nama, "password": sandi,
                                  "konfirmasi": sandi, "setuju": "on"})
    cek("register valid -> /login", r.status_code == 302 and "/login" in r.headers["Location"], r.status_code)

    r = c.post("/register", data={"email": email, "nama": nama, "password": sandi,
                                  "konfirmasi": sandi, "setuju": "on"})
    cek("register email ganda ditolak", r.status_code == 200 and "sudah terdaftar" in r.get_data(as_text=True), r.status_code)

    r = c.post("/login", data={"email": email, "password": "SalahSalah1!"})
    cek("login sandi salah ditolak", r.status_code == 200 and "salah" in r.get_data(as_text=True), r.status_code)

    r = c.post("/login", data={"email": "tidak-ada@example.com", "password": sandi})
    cek("login email tak dikenal: pesan sama", r.status_code == 200 and "salah" in r.get_data(as_text=True), r.status_code)

    r = c.post("/login", data={"email": email, "password": sandi, "next": "//evil.example"})
    loc = r.headers.get("Location", "")
    cek("open redirect (//evil) diabaikan", r.status_code == 302 and "evil" not in loc, loc)
    c.post("/logout")

    r = c.post("/login", data={"email": email, "password": sandi, "next": "/semua-produk"})
    cek("login benar + next internal", r.status_code == 302 and r.headers["Location"].endswith("/semua-produk"), r.headers.get("Location"))

    r = c.get("/")
    cek("header menampilkan nama user", nama in r.get_data(as_text=True), r.status_code)

    r = c.get("/logout")
    masih_login = nama in c.get("/").get_data(as_text=True)
    cek("GET /logout tidak melakukan logout", r.status_code in (404, 405) and masih_login, r.status_code)

    r = c.post("/logout")
    cek("logout (POST) -> beranda", r.status_code == 302, r.status_code)
    r = c.get("/")
    cek("setelah logout nama hilang", nama not in r.get_data(as_text=True), r.status_code)

    db.execute("UPDATE users SET is_active = 0 WHERE email = %s", (email,))
    r = c.post("/login", data={"email": email, "password": sandi})
    cek("akun nonaktif ditolak", r.status_code == 200 and "dinonaktifkan" in r.get_data(as_text=True), r.status_code)
finally:
    db.execute("DELETE FROM users WHERE email = %s", (email,))

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
