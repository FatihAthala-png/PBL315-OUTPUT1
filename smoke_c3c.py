"""Uji profil, avatar, dan Cek Resi (data asli) dengan MySQL asli.

Jalankan dari folder proyek (venv aktif, Pillow terpasang):  python smoke_c3c.py
Membuat user & pesanan uji, lalu menghapus semuanya (termasuk berkas avatar).
"""
import io
import re
import secrets
import struct
import sys
import zlib

from werkzeug.security import generate_password_hash

import db
from app import app
from store_config import UPLOAD_DIR

try:
    from PIL import Image
except ImportError:
    print("GAGAL  Pillow belum terpasang (pip install Pillow)")
    sys.exit(1)

gagal = 0
sandi = "Smoke#Test2026"
sandi_baru = "Baru#Sandi2027"


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def png_bytes(size=(800, 600), mode="RGBA", color=(30, 120, 220, 180)):
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, "PNG")
    return buf.getvalue()


def png_bomb():
    def chunk(tipe, isi):
        return struct.pack(">I", len(isi)) + tipe + isi + struct.pack(">I", zlib.crc32(tipe + isi) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 100000, 100000, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(b"\x00")) + chunk(b"IEND", b"")


def upload(client, data, nama="foto.png", **kw):
    return client.post(
        "/profil/avatar",
        data={"avatar": (io.BytesIO(data), nama)},
        content_type="multipart/form-data",
        follow_redirects=True,
        **kw,
    )


def baris_user(email):
    return db.query_one("SELECT id, name, phone, avatar_path FROM users WHERE email = %s", (email,))


emails = []
try:
    app.config["WTF_CSRF_ENABLED"] = False
    email = "smoke-prof-%s@example.com" % secrets.token_hex(4)
    emails.append(email)
    db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
        ("Profil Penguji", email, generate_password_hash(sandi)),
    )
    uid = baris_user(email)["id"]

    # ---------------------------------------------------------------- profil
    tamu = app.test_client()
    r = tamu.get("/profil")
    cek("tamu buka /profil -> login", r.status_code == 302 and "/login" in r.headers["Location"], r.status_code)
    cek("avatar user tanpa foto -> 404", tamu.get("/avatar/%d" % uid).status_code == 404)

    c = app.test_client()
    c.post("/login", data={"email": email, "password": sandi})
    r = c.get("/profil")
    cek("halaman profil tampil", r.status_code == 200 and email in teks(r) and "Foto Profil" in teks(r), r.status_code)

    r = c.post("/profil/data", data={"name": "Nama Baru", "phone": "081200000000"}, follow_redirects=True)
    u = baris_user(email)
    cek("data diri tersimpan", u["name"] == "Nama Baru" and u["phone"] == "081200000000" and "Data diri diperbarui" in teks(r))
    cek("nama baru tampil di header", "Nama Baru" in teks(c.get("/")))
    r = c.post("/profil/data", data={"name": "X", "phone": "abc"}, follow_redirects=True)
    cek("telepon tidak valid ditolak", "tidak valid" in teks(r) and baris_user(email)["name"] == "Nama Baru")
    r = c.post("/profil/data", data={"name": "  ", "phone": ""}, follow_redirects=True)
    cek("nama kosong ditolak", "Nama wajib diisi" in teks(r) and baris_user(email)["name"] == "Nama Baru")

    # ------------------------------------------------------------ kata sandi
    def ganti(cur, new, conf):
        return c.post("/profil/sandi", data={"current": cur, "new": new, "confirm": conf}, follow_redirects=True)

    cek("sandi lama salah ditolak", "saat ini salah" in teks(ganti("SalahSalah1!", sandi_baru, sandi_baru)))
    cek("sandi baru lemah ditolak", "belum memenuhi" in teks(ganti(sandi, "abc", "abc")))
    cek("konfirmasi tidak sama ditolak", "tidak sama" in teks(ganti(sandi, sandi_baru, "Lain#Sandi2027")))
    cek("sandi baru sama dengan lama ditolak", "harus berbeda" in teks(ganti(sandi, sandi, sandi)))
    cek("ganti sandi valid", "Kata sandi diperbarui" in teks(ganti(sandi, sandi_baru, sandi_baru)))
    lama = app.test_client().post("/login", data={"email": email, "password": sandi})
    baru = app.test_client().post("/login", data={"email": email, "password": sandi_baru})
    cek("login dengan sandi lama gagal, sandi baru berhasil", lama.status_code == 200 and baru.status_code == 302)

    # ---------------------------------------------------------------- avatar
    r = c.post("/profil/avatar", data={}, follow_redirects=True)
    cek("tanpa berkas ditolak", "Pilih berkas" in teks(r))
    r = upload(c, b"ini bukan gambar", "a.png")
    cek("berkas teks bernama .png ditolak", "bukan gambar yang valid" in teks(r) and baris_user(email)["avatar_path"] is None)
    gif = io.BytesIO(); Image.new("RGB", (50, 50), "red").save(gif, "GIF")
    cek("GIF (valid tapi tidak diizinkan) ditolak", "tidak didukung" in teks(upload(c, gif.getvalue(), "a.gif")))
    cek("decompression bomb ditolak", "bukan gambar yang valid" in teks(upload(c, png_bomb(), "bom.png")))

    r = upload(c, png_bytes())
    u = baris_user(email)
    cek("PNG transparan 800x600 diterima", "Foto profil diperbarui" in teks(r))
    cek("nama berkas avatar acak (.jpg)", re.fullmatch(r"avatars/[0-9a-f]{32}\.jpg", u["avatar_path"] or "") is not None, u["avatar_path"])
    hasil = Image.open(UPLOAD_DIR / u["avatar_path"])
    cek("hasil: JPEG persegi 256x256", hasil.format == "JPEG" and hasil.size == (256, 256), "%s %s" % (hasil.format, hasil.size))

    # metadata EXIF harus hilang
    foto = Image.new("RGB", (400, 300), (200, 30, 30))
    exif = foto.getexif(); exif[0x010F] = "KameraRahasia"; exif[0x0112] = 6
    buf = io.BytesIO(); foto.save(buf, "JPEG", exif=exif)
    lama_path = u["avatar_path"]
    upload(c, buf.getvalue(), "foto.jpg")
    u2 = baris_user(email)
    bersih = Image.open(UPLOAD_DIR / u2["avatar_path"])
    cek("EXIF (merk kamera, orientasi) dibuang", 0x010F not in bersih.getexif(), dict(bersih.getexif()))
    cek("avatar lama dihapus dari disk saat diganti", u2["avatar_path"] != lama_path and not (UPLOAD_DIR / lama_path).exists())

    r = c.get("/avatar/%d" % uid)
    cek("/avatar/<id> -> image/jpeg + nosniff", r.status_code == 200 and r.mimetype == "image/jpeg" and r.headers.get("X-Content-Type-Options") == "nosniff", r.status_code)
    cek("header menampilkan foto profil", "/avatar/%d" % uid in teks(c.get("/")))
    cek("halaman profil menampilkan foto", "/avatar/%d" % uid in teks(c.get("/profil")))

    r = c.post("/profil/avatar", data={"avatar": (io.BytesIO(b"x" * (6 * 1024 * 1024)), "besar.png")},
               content_type="multipart/form-data", headers={"Referer": "http://localhost/profil"})
    cek("berkas > 5 MB: kembali ke /profil dengan pesan", r.status_code == 302 and r.headers["Location"].endswith("/profil"), r.headers.get("Location"))

    path_terakhir = u2["avatar_path"]
    r = c.post("/profil/avatar/hapus", follow_redirects=True)
    cek("hapus foto: DB kosong, berkas hilang, URL 404",
        baris_user(email)["avatar_path"] is None and not (UPLOAD_DIR / path_terakhir).exists() and c.get("/avatar/%d" % uid).status_code == 404)

    app.config["WTF_CSRF_ENABLED"] = True
    r = c.post("/profil/data", data={"name": "Tanpa Token"})
    cek("POST /profil/data tanpa token CSRF ditolak", r.status_code == 400, r.status_code)
    app.config["WTF_CSRF_ENABLED"] = False

    # --------------------------------------------------- Cek Resi (data asli)
    produk = db.query_one("SELECT id, name FROM products WHERE is_active = 1 ORDER BY id LIMIT 1")
    resi = "JNE%s" % secrets.token_hex(5).upper()
    no_dikirim = "KMS-261111-%s" % secrets.token_hex(3).upper()
    no_batal = "KMS-261111-%s" % secrets.token_hex(3).upper()
    for no, status, r_ in ((no_dikirim, "dikirim", resi), (no_batal, "dibatalkan", None)):
        oid = db.execute(
            "INSERT INTO orders (order_no, user_id, status, recipient_name, phone, address, city, province, "
            "postal_code, courier, service, resi, subtotal, shipping_cost, total) "
            "VALUES (%s, %s, %s, 'Budi Santoso', '081234567890', 'Jl. Rahasia No. 12', 'Batam', 'Kepulauan Riau', "
            "'29432', 'jne', 'REG', %s, 100000, 25000, 125000)",
            (no, uid, status, r_),
        )
        db.execute(
            "INSERT INTO order_items (order_id, product_id, product_name, unit_price, qty) VALUES (%s, %s, %s, 100000, 1)",
            (oid, produk["id"], produk["name"]),
        )
        db.execute("INSERT INTO order_status_history (order_id, title, description) VALUES (%s, 'Pesanan dibuat', 'uji')", (oid,))

    p = app.test_client()
    r = p.get("/cek-resi-pesanan?q=" + no_dikirim)
    html = teks(r)
    cek("cari nomor pesanan -> status Dalam Pengiriman", r.status_code == 200 and "Dalam Pengiriman" in html)
    cek("nama penerima disamarkan (B*** S.)", "B*** S." in html and "Budi" not in html and "Santoso" not in html)
    cek("alamat jalan & telepon tidak tampil, kota tampil", "Rahasia" not in html and "081234567890" not in html and "Batam, Kepulauan Riau" in html)
    cek("kurir & layanan tampil", "JNE Express" in html and "Reguler" in html)
    r = p.get("/cek-resi-pesanan?q=" + resi.lower())
    cek("cari nomor resi (huruf kecil) berhasil", r.status_code == 200 and no_dikirim in teks(r))
    r = p.get("/cek-resi-pesanan?q=" + no_batal)
    cek("pesanan dibatalkan tampil", "Pesanan Dibatalkan" in teks(r))
    r = p.get("/cek-resi-pesanan?q=KMS-261001-0001")
    cek("nomor contoh lama tidak ada lagi", "tidak ditemukan" in teks(r))
    r = p.get("/cek-resi-pesanan?q=" + "' OR '1'='1")
    cek("percobaan SQL injection -> tidak ditemukan, tanpa error", r.status_code == 200 and "tidak ditemukan" in teks(r), r.status_code)
    r = p.get("/cek-resi-pesanan?q=" + "A" * 500)
    cek("kata kunci sangat panjang tidak error", r.status_code == 200, r.status_code)
    cek("tamu tidak melihat daftar pesanan sendiri", "Pesanan terakhirmu" not in teks(p.get("/cek-resi-pesanan")))
    r = c.get("/cek-resi-pesanan")
    cek("user login melihat nomor pesanannya sendiri", "Pesanan terakhirmu" in teks(r) and no_dikirim in teks(r))
finally:
    for e in emails:
        u = db.query_one("SELECT id, avatar_path FROM users WHERE email = %s", (e,))
        if u:
            if u["avatar_path"]:
                (UPLOAD_DIR / u["avatar_path"]).unlink(missing_ok=True)
            db.execute("DELETE FROM orders WHERE user_id = %s", (u["id"],))
            db.execute("DELETE FROM users WHERE id = %s", (u["id"],))

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
