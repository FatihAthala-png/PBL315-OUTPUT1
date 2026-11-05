"""Uji Fase F: header keamanan, halaman error, pembatas percobaan, berkas deploy.

Jalankan dari folder proyek (venv aktif):  python smoke_f.py
Membuat dua user uji lalu menghapusnya.
"""
import runpy
import secrets
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash

import db
import ratelimit
from app import app

gagal = 0
sandi = "Smoke#Test2026"


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def buat_user(nama, role="customer"):
    email = "smoke-f-%s@example.com" % secrets.token_hex(4)
    uid = db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (nama, email, generate_password_hash(sandi), role),
    )
    return uid, email


uids = []
try:
    app.config["WTF_CSRF_ENABLED"] = False
    uid, email = buat_user("Penguji F"); uids.append(uid)

    # ------------------------------------------------------- unit pembatas
    ratelimit.reset()
    waktu = [1000.0]
    asli = ratelimit._now
    ratelimit._now = lambda: waktu[0]
    try:
        for _ in range(3):
            ratelimit.record("t", "k", 60)
        cek("blocked: di bawah batas -> False", ratelimit.blocked("t", "k", 4, 60) is False)
        ratelimit.record("t", "k", 60)
        cek("blocked: mencapai batas -> True", ratelimit.blocked("t", "k", 4, 60) is True)
        cek("kunci lain tidak terpengaruh", ratelimit.blocked("t", "lain", 4, 60) is False)
        waktu[0] += 61
        cek("kejadian kedaluwarsa setelah jendela berlalu", ratelimit.count("t", "k", 60) == 0)
        hasil = [ratelimit.hit("h", "k", 3, 60) for _ in range(5)]
        cek("hit: 3 diizinkan, selebihnya ditolak", hasil == [False, False, False, True, True], hasil)
        ratelimit.clear("h", "k")
        cek("clear: hitungan kembali nol", ratelimit.hit("h", "k", 3, 60) is False)
    finally:
        ratelimit._now = asli
    ratelimit.reset()

    # ------------------------------------------------------ header keamanan
    c = app.test_client()
    r = c.get("/")
    h = r.headers
    cek("header: X-Content-Type-Options nosniff", h.get("X-Content-Type-Options") == "nosniff")
    cek("header: X-Frame-Options DENY", h.get("X-Frame-Options") == "DENY")
    cek("header: Referrer-Policy", "strict-origin" in h.get("Referrer-Policy", ""))
    cek("header: Permissions-Policy", "camera=()" in h.get("Permissions-Policy", ""))
    cek("header: CSP frame-ancestors 'none'", "frame-ancestors 'none'" in h.get("Content-Security-Policy", ""))
    cek("HSTS tidak dikirim saat COOKIE_SECURE=0", "Strict-Transport-Security" not in h)
    app.config["SESSION_COOKIE_SECURE"] = True
    cek("HSTS dikirim saat COOKIE_SECURE=1", "max-age" in c.get("/").headers.get("Strict-Transport-Security", ""))
    app.config["SESSION_COOKIE_SECURE"] = False

    masuk = app.test_client()
    masuk.post("/login", data={"email": email, "password": sandi})
    cek("halaman user login: Cache-Control private, no-store", "no-store" in masuk.get("/profil").headers.get("Cache-Control", ""))
    cek("berkas static tidak ikut no-store", "no-store" not in masuk.get("/static/css/style.css").headers.get("Cache-Control", ""))

    # ------------------------------------------------------- halaman error
    r = c.get("/halaman-yang-tidak-ada")
    cek("404 memakai halaman kustom", r.status_code == 404 and "Halaman tidak ditemukan" in teks(r) and "Ke Beranda" in teks(r))
    r = masuk.get("/admin/")
    cek("403 memakai halaman kustom", r.status_code == 403 and "Akses ditolak" in teks(r))

    import blueprints.shop as shop_mod

    def rusak(*_a, **_k):
        raise RuntimeError("rahasia-internal-xyz")

    asli_fn = shop_mod.get_popular_products
    shop_mod.get_popular_products = rusak
    app.logger.disabled = True  # kerusakan ini disengaja; jangan cetak traceback-nya
    try:
        r = c.get("/")
    finally:
        shop_mod.get_popular_products = asli_fn
        app.logger.disabled = False
    cek("500 memakai halaman kustom tanpa detail internal",
        r.status_code == 500 and "Terjadi kesalahan" in teks(r) and "rahasia-internal-xyz" not in teks(r) and "Traceback" not in teks(r), r.status_code)

    # -------------------------------------------------- kunci login gagal
    ratelimit.reset()
    k = app.test_client()
    salah = [k.post("/login", data={"email": email, "password": "SalahSalah1!"}) for _ in range(5)]
    cek("5 login gagal pertama dijawab biasa (200, pesan salah)", all(r.status_code == 200 and "salah" in teks(r) for r in salah))
    r = k.post("/login", data={"email": email, "password": "SalahSalah1!"})
    cek("login gagal ke-6 -> 429 'Terlalu banyak percobaan'", r.status_code == 429 and "Terlalu banyak percobaan" in teks(r), r.status_code)
    r = k.post("/login", data={"email": email, "password": sandi})
    cek("sandi BENAR pun ditolak selama terkunci", r.status_code == 429)
    r = app.test_client().post("/login", data={"email": "lain-%s@example.com" % secrets.token_hex(3), "password": "x"})
    cek("email lain belum terkunci", r.status_code == 200)

    waktu[0] = 5000.0
    ratelimit._now = lambda: waktu[0]
    try:
        ratelimit.reset()
        for _ in range(5):
            k.post("/login", data={"email": email, "password": "SalahSalah1!"})
        waktu[0] += 601
        r = k.post("/login", data={"email": email, "password": sandi})
        cek("kunci terbuka setelah 10 menit: login benar berhasil", r.status_code == 302, r.status_code)
    finally:
        ratelimit._now = asli
    ratelimit.reset()

    k2 = app.test_client()
    for _ in range(3):
        k2.post("/login", data={"email": email, "password": "SalahSalah1!"})
    cek("login berhasil menghapus hitungan gagal", k2.post("/login", data={"email": email, "password": sandi}).status_code == 302)
    k2.post("/logout")
    lagi = [k2.post("/login", data={"email": email, "password": "SalahSalah1!"}).status_code for _ in range(4)]
    cek("setelah berhasil, 4 gagal baru belum terkunci", lagi == [200, 200, 200, 200], lagi)

    ratelimit.reset()
    kode = [app.test_client().post("/login", data={"email": "ip%d-%s@example.com" % (i, secrets.token_hex(2)), "password": "x"}).status_code for i in range(21)]
    cek("batas per IP: 20 gagal dari email berbeda lalu 429", kode[:20] == [200] * 20 and kode[20] == 429, kode[-3:])

    # --------------------------------------------------- batas pendaftaran
    ratelimit.reset()
    data = {"email": "bukan-email", "nama": "X", "password": "x", "konfirmasi": "x"}
    kode = [app.test_client().post("/register", data=data).status_code for _ in range(11)]
    r = app.test_client().post("/register", data=data)
    cek("pendaftaran: 10 permintaan diizinkan, berikutnya 429", kode[:10] == [200] * 10 and kode[10] == 429 and "Terlalu banyak pendaftaran" in teks(r), kode[-2:])

    # ------------------------------------------------- batas cek resi
    ratelimit.reset()
    p = app.test_client()
    kode = [p.get("/cek-resi-pesanan?q=TIDAK-ADA-%d" % i).status_code for i in range(61)]
    r = p.get("/cek-resi-pesanan?q=lagi")
    cek("cek resi: 60 pencarian/menit diizinkan, berikutnya 429 (halaman kustom)", kode[:60] == [200] * 60 and kode[60] == 429 and "Terlalu banyak permintaan" in teks(r), kode[-2:])
    cek("halaman cek resi tanpa pencarian tidak dihitung", p.get("/cek-resi-pesanan").status_code == 200)

    # ------------------------------------------ batas ganti sandi (per user)
    ratelimit.reset()
    u = app.test_client()
    u.post("/login", data={"email": email, "password": sandi})
    for _ in range(5):
        u.post("/profil/sandi", data={"current": "SalahSalah1!", "new": "Baru#Sandi2027", "confirm": "Baru#Sandi2027"})
    r = u.post("/profil/sandi", data={"current": sandi, "new": "Baru#Sandi2027", "confirm": "Baru#Sandi2027"}, follow_redirects=True)
    cek("ganti sandi: setelah 5 gagal, sandi benar pun diblokir", "Terlalu banyak percobaan" in teks(r))
    cek("sandi tidak berubah selama diblokir", app.test_client().post("/login", data={"email": email, "password": sandi}).status_code == 302)
    ratelimit.reset()

    # ---------------------------------------------------- berkas deploy
    root = Path(__file__).parent
    conf = runpy.run_path(str(root / "gunicorn.conf.py"))
    cek("gunicorn.conf.py: 1 worker, gthread, port 8000", conf["workers"] == 1 and conf["worker_class"] == "gthread" and conf["bind"].endswith(":8000"))
    unit = (root / "deploy" / "kamistore.service").read_text(encoding="utf-8")
    cek("kamistore.service: ExecStart gunicorn + User + Restart", "venv/bin/gunicorn" in unit and "User=web-srv1" in unit and "Restart=on-failure" in unit)
    cek("kamistore.service: pengerasan NoNewPrivileges", "NoNewPrivileges=yes" in unit)
finally:
    for u_id in uids:
        db.execute("DELETE FROM users WHERE id = %s", (u_id,))

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
