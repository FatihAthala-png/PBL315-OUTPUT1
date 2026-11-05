"""Uji kelola produk, kelola pengguna, dan laporan (admin) dengan MySQL asli.

Jalankan dari folder proyek (venv aktif, Pillow terpasang):  python smoke_d2.py
Membuat admin, pembeli, produk, dan pesanan uji, lalu menghapus semuanya
(termasuk berkas gambar).
"""
import csv
import io
import re
import secrets
import sys

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
TANDA = "Produk Uji D2 " + secrets.token_hex(3)
TGL = "2020-03-15"


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def png_bytes(size=(1600, 1200)):
    buf = io.BytesIO()
    Image.new("RGBA", size, (200, 40, 40, 150)).save(buf, "PNG")
    return buf.getvalue()


def buat_user(nama, role):
    email = "smoke-d2-%s@example.com" % secrets.token_hex(4)
    uid = db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (nama, email, generate_password_hash(sandi), role),
    )
    return uid, email


def login(email):
    c = app.test_client()
    c.post("/login", data={"email": email, "password": sandi})
    return c


FORM = {
    "name": TANDA, "category": "Kategori Uji", "type": "tcg", "sub": "booster-pack",
    "brand": "pokemon-company", "price": "1.250.000", "discount_percent": "", "stock": "7",
    "stock_unit": "pack", "badge": "NEW", "image_url": "https://example.com/uji.png",
}


def kirim(client, url, ubah=None, rarity=("sar", "psa10"), gambar=None, preorder=False):
    data = {**FORM, **(ubah or {})}
    data["rarity"] = list(rarity)
    if preorder:
        data["is_preorder"] = "on"
    if gambar is not None:
        data["image"] = (io.BytesIO(gambar), "foto.png")
    return client.post(url, data=data, content_type="multipart/form-data", follow_redirects=True)


def produk_uji():
    return db.query_one("SELECT * FROM products WHERE name LIKE %s ORDER BY id DESC LIMIT 1", (TANDA + "%",))


def jumlah_uji():
    return db.query_one("SELECT COUNT(*) AS n FROM products WHERE name LIKE %s", (TANDA + "%",))["n"]


uids = []
berkas = []
try:
    app.config["WTF_CSRF_ENABLED"] = False
    admin_id, admin_email = buat_user("Admin D2", "admin"); uids.append(admin_id)
    buyer_id, buyer_email = buat_user("Pembeli D2", "customer"); uids.append(buyer_id)
    adm, pembeli, tamu = login(admin_email), login(buyer_email), app.test_client()

    # ------------------------------------------------------------- akses
    for path in ("/admin/produk/", "/admin/pengguna/", "/admin/laporan/", "/admin/laporan/csv"):
        cek("tamu %s -> login" % path, tamu.get(path).status_code == 302)
        cek("pembeli %s -> 403" % path, pembeli.get(path).status_code == 403)
    cek("pembeli tidak bisa menambah produk (403)", pembeli.post("/admin/produk/baru", data=FORM).status_code == 403)
    cek("tab Produk/Pengguna/Laporan ada di panel", all(k in teks(adm.get("/admin/")) for k in ("Produk", "Pengguna", "Laporan")))

    # ----------------------------------------------------- produk: validasi
    r = adm.get("/admin/produk/")
    cek("daftar produk tampil", r.status_code == 200 and "Produk baru" in teks(r))
    cek("form tambah tampil", adm.get("/admin/produk/baru").status_code == 200)
    salah = [
        ("nama kosong ditolak", {"name": " "}, "Nama produk wajib"),
        ("harga 0 ditolak", {"price": "0"}, "Harga harus"),
        ("harga bukan angka ditolak", {"price": "abc"}, "Harga harus"),
        ("sub-kategori tak cocok jenis ditolak", {"type": "figure", "sub": "booster-pack"}, "Sub-kategori tidak sesuai"),
        ("brand ngawur ditolak", {"brand": "ngawur"}, "Pilih brand"),
        ("diskon 95 ditolak", {"discount_percent": "95"}, "Diskon harus"),
        ("stok negatif ditolak", {"stock": "-1"}, "Stok harus"),
        ("URL javascript: ditolak", {"image_url": "javascript:alert(1)"}, "URL gambar"),
        ("URL http (bukan https) ditolak", {"image_url": "http://example.com/a.png"}, "URL gambar"),
        ("tanpa gambar ditolak", {"image_url": ""}, "Gambar produk wajib"),
    ]
    for label, ubah, kata in salah:
        r = kirim(adm, "/admin/produk/baru", ubah)
        cek(label, kata in teks(r) and jumlah_uji() == 0, r.status_code)
    r = kirim(adm, "/admin/produk/baru", gambar=b"bukan gambar", ubah={"image_url": ""})
    cek("berkas teks sebagai gambar ditolak", "bukan gambar yang valid" in teks(r) and jumlah_uji() == 0)

    # ------------------------------------------------- produk: tambah (URL)
    app.config["WTF_CSRF_ENABLED"] = True
    cek("tambah produk tanpa token CSRF ditolak", adm.post("/admin/produk/baru", data=FORM).status_code == 400)
    app.config["WTF_CSRF_ENABLED"] = False

    r = kirim(adm, "/admin/produk/baru", {"discount_percent": "20"}, preorder=True)
    p = produk_uji()
    cek("tambah produk (URL gambar) berhasil", p is not None and "Produk ditambahkan" in teks(r))
    cek("harga '1.250.000' terbaca 1250000, diskon 20, stok 7", int(p["price"]) == 1250000 and int(p["discount_percent"]) == 20 and int(p["stock"]) == 7)
    cek("rarity & pre-order & badge tersimpan", p["rarity"] == "sar,psa10" and int(p["is_preorder"]) == 1 and p["badge"] == "NEW")
    pid = p["id"]
    r = tamu.get("/semua-produk")
    cek("produk baru tampil di katalog publik", TANDA in teks(r))
    r = tamu.get("/produk/%d" % pid)
    cek("halaman detail produk baru tampil", r.status_code == 200 and TANDA in teks(r))

    # ------------------------------------------------ produk: ubah & gambar
    r = adm.get("/admin/produk/%d/ubah" % pid)
    cek("form ubah terisi data produk", r.status_code == 200 and TANDA in teks(r) and "1250000" in teks(r))
    r = kirim(adm, "/admin/produk/%d/ubah" % pid, {"price": "999000", "stock": "3", "image_url": ""})
    p2 = produk_uji()
    cek("ubah harga & stok; gambar lama tetap", int(p2["price"]) == 999000 and int(p2["stock"]) == 3 and p2["image_url"] == "https://example.com/uji.png")
    cek("ubah produk tidak ada -> 404", adm.get("/admin/produk/999999/ubah").status_code == 404)

    r = kirim(adm, "/admin/produk/%d/ubah" % pid, {"image_url": ""}, gambar=png_bytes())
    p3 = produk_uji()
    m = re.fullmatch(r"/media/produk/([0-9a-f]{32})\.jpg", p3["image_url"])
    cek("unggah gambar: URL acak /media/produk/<hex>.jpg", m is not None, p3["image_url"])
    path1 = UPLOAD_DIR / "products" / (m.group(1) + ".jpg"); berkas.append(path1)
    hasil = Image.open(path1)
    cek("gambar diperkecil (maks 800 px) & JPEG", hasil.format == "JPEG" and max(hasil.size) == 800, "%s %s" % (hasil.format, hasil.size))
    r = tamu.get(p3["image_url"])
    cek("gambar produk dilayani (image/jpeg + nosniff)", r.status_code == 200 and r.mimetype == "image/jpeg" and r.headers.get("X-Content-Type-Options") == "nosniff")
    cek("nama berkas ngawur -> 404", tamu.get("/media/produk/..%2Fx.jpg").status_code == 404 and tamu.get("/media/produk/abc.jpg").status_code == 404)

    kirim(adm, "/admin/produk/%d/ubah" % pid, {"image_url": ""}, gambar=png_bytes((300, 300)))
    p4 = produk_uji()
    m2 = re.fullmatch(r"/media/produk/([0-9a-f]{32})\.jpg", p4["image_url"])
    path2 = UPLOAD_DIR / "products" / (m2.group(1) + ".jpg"); berkas.append(path2)
    cek("ganti gambar unggahan: berkas lama dihapus dari disk", p4["image_url"] != p3["image_url"] and not path1.exists() and path2.exists())

    # --------------------------------------------- produk: nonaktif & hapus
    adm.post("/admin/produk/%d/status" % pid)
    cek("nonaktif: hilang dari katalog & detail 404", produk_uji()["is_active"] == 0 and TANDA not in teks(tamu.get("/semua-produk")) and tamu.get("/produk/%d" % pid).status_code == 404)
    cek("daftar admin tetap memuat produk nonaktif", TANDA in teks(adm.get("/admin/produk/?status=nonaktif")))
    adm.post("/admin/produk/%d/status" % pid)
    cek("aktifkan kembali: tampil lagi", produk_uji()["is_active"] == 1 and TANDA in teks(tamu.get("/semua-produk")))

    oid = db.execute(
        "INSERT INTO orders (order_no, user_id, status, recipient_name, phone, address, city, province, postal_code, "
        "subtotal, shipping_cost, total) VALUES (%s, %s, 'selesai', 'X', '081200000000', 'Jl X', 'Batam', 'Kepri', '29432', 1000, 0, 1000)",
        ("KMS-261313-%s" % secrets.token_hex(3).upper(), buyer_id),
    )
    db.execute("INSERT INTO order_items (order_id, product_id, product_name, unit_price, qty) VALUES (%s, %s, 'x', 1000, 1)", (oid, pid))
    r = adm.post("/admin/produk/%d/hapus" % pid, follow_redirects=True)
    cek("produk yang pernah dipesan tidak bisa dihapus permanen", "sudah pernah dipesan" in teks(r) and produk_uji() is not None)
    db.execute("DELETE FROM orders WHERE id = %s", (oid,))
    r = adm.post("/admin/produk/%d/hapus" % pid, follow_redirects=True)
    cek("produk yang belum pernah dipesan terhapus permanen + gambar ikut hilang", produk_uji() is None and not path2.exists() and "dihapus permanen" in teks(r))
    cek("hapus produk tidak ada -> 404", adm.post("/admin/produk/999999/hapus").status_code == 404)

    # -------------------------------------------------------------- pengguna
    r = adm.get("/admin/pengguna/")
    cek("daftar pengguna memuat pembeli uji", r.status_code == 200 and buyer_email in teks(r))
    cek("cari pengguna berdasarkan email", buyer_email in teks(adm.get("/admin/pengguna/?q=" + buyer_email.split("@")[0])))
    cek("filter peran admin tidak memuat pembeli", buyer_email not in teks(adm.get("/admin/pengguna/?role=admin")))
    cek("parameter ngawur tidak error", adm.get("/admin/pengguna/?page=abc&role=x&status=y").status_code == 200)

    cek("sebelum dinonaktifkan pembeli bisa buka /profil", pembeli.get("/profil").status_code == 200)
    adm.post("/admin/pengguna/%d/status" % buyer_id, data={"active": "0"})
    cek("nonaktifkan: sesi pembeli langsung tidak berlaku", pembeli.get("/profil").status_code == 302)
    r = app.test_client().post("/login", data={"email": buyer_email, "password": sandi})
    cek("pengguna nonaktif tidak bisa login", r.status_code == 200 and "dinonaktifkan" in teks(r))
    adm.post("/admin/pengguna/%d/status" % buyer_id, data={"active": "1"})
    cek("aktifkan kembali: bisa login", app.test_client().post("/login", data={"email": buyer_email, "password": sandi}).status_code == 302)

    cek("nilai aktif ngawur -> 400", adm.post("/admin/pengguna/%d/status" % buyer_id, data={"active": "x"}).status_code == 400)
    adm.post("/admin/pengguna/%d/peran" % buyer_id, data={"role": "admin"})
    cek("jadikan admin: pembeli bisa buka /admin", login(buyer_email).get("/admin/").status_code == 200)
    adm.post("/admin/pengguna/%d/peran" % buyer_id, data={"role": "customer"})
    cek("kembalikan ke customer: /admin ditolak lagi", login(buyer_email).get("/admin/").status_code == 403)
    r = adm.post("/admin/pengguna/%d/peran" % buyer_id, data={"role": "superuser"}, follow_redirects=True)
    cek("peran ngawur ditolak", "Peran tidak valid" in teks(r) and db.query_one("SELECT role FROM users WHERE id = %s", (buyer_id,))["role"] == "customer")
    r = adm.post("/admin/pengguna/%d/status" % admin_id, data={"active": "0"}, follow_redirects=True)
    cek("admin tidak bisa menonaktifkan akunnya sendiri", "akunmu sendiri" in teks(r) and db.query_one("SELECT is_active FROM users WHERE id = %s", (admin_id,))["is_active"] == 1)
    r = adm.post("/admin/pengguna/%d/peran" % admin_id, data={"role": "customer"}, follow_redirects=True)
    cek("admin tidak bisa menurunkan perannya sendiri", "akunmu sendiri" in teks(r) and db.query_one("SELECT role FROM users WHERE id = %s", (admin_id,))["role"] == "admin")
    r = adm.post("/admin/pengguna/999999/status", data={"active": "0"}, follow_redirects=True)
    cek("pengguna tidak ada -> pesan error", "tidak ditemukan" in teks(r))

    # --------------------------------------------------------------- laporan
    p_lap = db.query_one("SELECT id FROM products ORDER BY id LIMIT 1")["id"]
    rata = 0
    for qty, harga, nama in ((2, 100000, "=HYPERLINK(1)"), (1, 50000, "Penerima Biasa")):
        no = "KMS-200315-%s" % secrets.token_hex(3).upper()
        total = harga * qty + 20000
        oid = db.execute(
            "INSERT INTO orders (order_no, user_id, status, recipient_name, phone, address, city, province, postal_code, courier, service, "
            "subtotal, shipping_cost, total) VALUES (%s, %s, 'selesai', %s, '081211112222', 'Jl L', 'Batam', 'Kepri', '29432', 'jne', 'REG', %s, 20000, %s)",
            (no, buyer_id, nama, harga * qty, total),
        )
        db.execute("INSERT INTO order_items (order_id, product_id, product_name, unit_price, qty) VALUES (%s, %s, 'Produk Laris Uji', %s, %s)", (oid, p_lap, harga, qty))
        db.execute(
            "INSERT INTO payments (order_id, method, amount, proof_path, status, reviewed_by, reviewed_at) "
            "VALUES (%s, 'bca', %s, 'payments/x.png', 'disetujui', %s, %s)", (oid, total, admin_id, TGL + " 10:00:00"),
        )
        rata += total
    r = adm.get("/admin/laporan/?dari=%s&sampai=%s" % (TGL, TGL))
    html = teks(r)
    cek("laporan: halaman tampil", r.status_code == 200 and "Omzet per hari" in html)
    cek("laporan: omzet = jumlah pembayaran disetujui", ("Rp " + f"{rata:,}".replace(",", ".")) in html, rata)
    cek("laporan: 2 transaksi, produk terlaris tampil", "Produk Laris Uji" in html and "KMS-200315-" in html)
    cek("laporan: rentang lain tidak memuat transaksi uji", "KMS-200315-" not in teks(adm.get("/admin/laporan/?dari=2020-03-16&sampai=2020-03-20")))
    for label, q, kata in (
        ("tanggal ngawur ditolak", "dari=abc&sampai=xyz", "Format tanggal"),
        ("tanggal awal > akhir ditolak", "dari=2020-03-20&sampai=2020-03-10", "tidak boleh setelah"),
        ("rentang > 1 tahun ditolak", "dari=2018-01-01&sampai=2020-03-10", "maksimal 1 tahun"),
    ):
        r = adm.get("/admin/laporan/?" + q)
        cek(label, r.status_code == 200 and kata in teks(r), r.status_code)

    r = adm.get("/admin/laporan/csv?dari=%s&sampai=%s" % (TGL, TGL))
    cek("CSV: tipe & nama berkas", r.status_code == 200 and r.mimetype == "text/csv" and 'attachment; filename="laporan-%s_%s.csv"' % (TGL, TGL) in r.headers.get("Content-Disposition", ""))
    baris = list(csv.reader(io.StringIO(teks(r).lstrip("\ufeff"))))
    cek("CSV: header + 2 baris data", len(baris) == 3 and baris[0][0] == "No. Pesanan", len(baris))
    cek("CSV: total jumlah benar", sorted(int(b[8]) for b in baris[1:]) == sorted([100000 * 2 + 20000, 50000 + 20000]))
    cek("CSV injection dinetralkan (=... diberi awalan ')", any(b[3] == "'=HYPERLINK(1)" for b in baris[1:]), [b[3] for b in baris[1:]])
finally:
    for uid in uids:
        db.execute("DELETE FROM orders WHERE user_id = %s", (uid,))
        db.execute("DELETE FROM users WHERE id = %s", (uid,))
    for row in db.query_all("SELECT id, image_url FROM products WHERE name LIKE %s", (TANDA + "%",)):
        db.execute("DELETE FROM products WHERE id = %s", (row["id"],))
    for path in berkas:
        path.unlink(missing_ok=True)

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
