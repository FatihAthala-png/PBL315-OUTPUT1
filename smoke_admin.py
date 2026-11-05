"""Uji panel admin dengan MySQL asli: akses, verifikasi pembayaran, stok, pengiriman.

Jalankan dari folder proyek (venv aktif):  python smoke_admin.py
Membuat admin & pembeli uji, beberapa pesanan, lalu menghapus semuanya (termasuk
berkas bukti) dan memulihkan stok produk yang dipakai.
"""
import secrets
import sys

from werkzeug.security import generate_password_hash

import db
from app import app
from store_config import UPLOAD_DIR

gagal = 0
sandi = "Smoke#Test2026"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


def buat_user(nama, role):
    email = "smoke-adm-%s@example.com" % secrets.token_hex(4)
    uid = db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (nama, email, generate_password_hash(sandi), role),
    )
    return uid, email


def login(email):
    c = app.test_client()
    c.post("/login", data={"email": email, "password": sandi})
    return c


berkas = []


def buat_pesanan(uid, pid, harga, qty, status="menunggu_approval", dengan_bukti=True):
    no = "KMS-261212-%s" % secrets.token_hex(3).upper()
    oid = db.execute(
        "INSERT INTO orders (order_no, user_id, status, recipient_name, phone, address, city, province, postal_code, "
        "courier, service, subtotal, shipping_cost, total) VALUES (%s, %s, %s, 'Penerima Admin Uji', '081299990000', "
        "'Jl. Lengkap Uji No. 7', 'Batam', 'Kepulauan Riau', '29432', 'jne', 'REG', %s, 25000, %s)",
        (no, uid, status, harga * qty, harga * qty + 25000),
    )
    db.execute(
        "INSERT INTO order_items (order_id, product_id, product_name, unit_price, qty) VALUES (%s, %s, 'Produk Uji', %s, %s)",
        (oid, pid, harga, qty),
    )
    db.execute("INSERT INTO order_status_history (order_id, title, description) VALUES (%s, 'Pesanan dibuat', 'uji')", (oid,))
    if dengan_bukti:
        rel = "payments/uji-%s.png" % secrets.token_hex(8)
        (UPLOAD_DIR / "payments").mkdir(parents=True, exist_ok=True)
        (UPLOAD_DIR / rel).write_bytes(PNG)
        berkas.append(rel)
        db.execute(
            "INSERT INTO payments (order_id, method, amount, proof_path) VALUES (%s, 'bca', %s, %s)",
            (oid, harga * qty + 25000, rel),
        )
    return oid, no


def pesanan(no):
    return db.query_one("SELECT * FROM orders WHERE order_no = %s", (no,))


def stok(pid):
    return int(db.query_one("SELECT stock FROM products WHERE id = %s", (pid,))["stock"])


uids = []
stok_asli = None
try:
    p = db.query_one("SELECT id, price, stock FROM products WHERE is_active = 1 AND stock >= 5 ORDER BY id LIMIT 1")
    pid, harga, stok_asli = p["id"], int(p["price"]), int(p["stock"])
    app.config["WTF_CSRF_ENABLED"] = False

    admin_id, admin_email = buat_user("Admin Uji", "admin"); uids.append(admin_id)
    buyer_id, buyer_email = buat_user("Pembeli Uji", "customer"); uids.append(buyer_id)

    # --- hak akses ---
    tamu = app.test_client()
    for path in ("/admin/", "/admin/pesanan"):
        r = tamu.get(path)
        cek("tamu buka %s -> login" % path, r.status_code == 302 and "/login" in r.headers["Location"], r.status_code)
    pembeli = login(buyer_email)
    cek("pembeli biasa buka /admin -> 403", pembeli.get("/admin/").status_code == 403)
    cek("pembeli biasa buka daftar pesanan admin -> 403", pembeli.get("/admin/pesanan").status_code == 403)
    cek("pembeli biasa tidak bisa menyetujui (403)", pembeli.post("/admin/pesanan/KMS-X/setujui").status_code == 403)
    adm = login(admin_email)
    r = adm.get("/admin/")
    cek("admin buka dashboard", r.status_code == 200 and "Menunggu verifikasi" in teks(r), r.status_code)
    cek("menu akun admin memuat tautan Panel Admin", "Panel Admin" in teks(adm.get("/")))
    cek("menu akun pembeli tidak memuat Panel Admin", "Panel Admin" not in teks(pembeli.get("/")))

    # --- daftar, filter, cari, detail ---
    _, no_a = buat_pesanan(buyer_id, pid, harga, 2)
    r = adm.get("/admin/pesanan?status=menunggu_approval")
    cek("filter status menampilkan pesanan", r.status_code == 200 and no_a in teks(r))
    cek("cari berdasarkan email", no_a in teks(adm.get("/admin/pesanan?q=" + buyer_email.split("@")[0])))
    cek("cari kata tak dikenal -> kosong", no_a not in teks(adm.get("/admin/pesanan?q=zzzqqq")))
    cek("filter & halaman ngawur tidak error", adm.get("/admin/pesanan?status=ngawur&page=abc").status_code == 200)
    cek("pencarian dengan karakter %_ tidak error", adm.get("/admin/pesanan?q=%25_%5C").status_code == 200)
    r = adm.get("/admin/pesanan/" + no_a)
    cek("detail memuat alamat lengkap, telepon, email", r.status_code == 200 and "Jl. Lengkap Uji No. 7" in teks(r) and "081299990000" in teks(r) and buyer_email in teks(r))
    r = adm.get("/admin/pesanan/KMS-TIDAK-ADA")
    cek("pesanan tidak ada -> 404", r.status_code == 404)
    r = adm.get("/pesanan/%s/bukti" % no_a)
    cek("admin bisa membuka bukti bayar", r.status_code == 200 and r.mimetype == "image/png", r.status_code)

    # --- CSRF ---
    app.config["WTF_CSRF_ENABLED"] = True
    cek("aksi admin tanpa token CSRF ditolak", adm.post("/admin/pesanan/%s/setujui" % no_a).status_code == 400)
    app.config["WTF_CSRF_ENABLED"] = False

    # --- setujui: stok berkurang, status berubah, tak bisa dua kali ---
    r = adm.post("/admin/pesanan/%s/setujui" % no_a, follow_redirects=True)
    o = pesanan(no_a)
    pay = db.query_one("SELECT status, reviewed_by FROM payments WHERE order_id = %s", (o["id"],))
    cek("setujui: status diproses", o["status"] == "diproses" and "Pembayaran disetujui" in teks(r), o["status"])
    cek("setujui: stok berkurang sebesar jumlah pesanan", stok(pid) == stok_asli - 2, stok(pid))
    cek("setujui: pembayaran tercatat disetujui oleh admin", pay["status"] == "disetujui" and int(pay["reviewed_by"]) == admin_id)
    r = adm.post("/admin/pesanan/%s/setujui" % no_a, follow_redirects=True)
    cek("setujui kedua kali ditolak, stok tidak berkurang lagi", "tidak sedang menunggu" in teks(r) and stok(pid) == stok_asli - 2)
    cek("pembeli melihat status Diproses", "Diproses" in teks(pembeli.get("/pesanan/" + no_a)))

    # --- stok tidak cukup saat menyetujui ---
    _, no_b = buat_pesanan(buyer_id, pid, harga, 3)
    db.execute("UPDATE products SET stock = 1 WHERE id = %s", (pid,))
    r = adm.post("/admin/pesanan/%s/setujui" % no_b, follow_redirects=True)
    cek("stok tidak cukup: persetujuan ditolak, status & stok tetap", "tidak cukup" in teks(r) and pesanan(no_b)["status"] == "menunggu_approval" and stok(pid) == 1)
    db.execute("UPDATE products SET stock = %s WHERE id = %s", (stok_asli - 2, pid))

    # --- tolak: alasan wajib, pembeli mengunggah ulang ---
    r = adm.post("/admin/pesanan/%s/tolak" % no_b, data={"reason": "  "}, follow_redirects=True)
    cek("tolak tanpa alasan ditolak", "Alasan penolakan wajib" in teks(r) and pesanan(no_b)["status"] == "menunggu_approval")
    r = adm.post("/admin/pesanan/%s/tolak" % no_b, data={"reason": "Nominal tidak sesuai"}, follow_redirects=True)
    ob = pesanan(no_b)
    payb = db.query_one("SELECT status, reject_reason FROM payments WHERE order_id = %s", (ob["id"],))
    cek("tolak: pesanan kembali menunggu_pembayaran, pembayaran ditolak + alasan", ob["status"] == "menunggu_pembayaran" and payb["status"] == "ditolak" and payb["reject_reason"] == "Nominal tidak sesuai")
    cek("pembeli melihat alasan penolakan", "Nominal tidak sesuai" in teks(pembeli.get("/pesanan/" + no_b)))

    # --- kirim: validasi resi, tidak bisa dua kali ---
    r = adm.post("/admin/pesanan/%s/kirim" % no_a, data={"resi": "ab"}, follow_redirects=True)
    cek("resi tidak valid ditolak", "Nomor resi tidak valid" in teks(r) and pesanan(no_a)["status"] == "diproses")
    cek("kirim pesanan yang belum diproses ditolak", "Hanya pesanan berstatus Diproses" in teks(adm.post("/admin/pesanan/%s/kirim" % no_b, data={"resi": "JNE12345"}, follow_redirects=True)))
    resi = "JNE" + secrets.token_hex(5).upper()
    r = adm.post("/admin/pesanan/%s/kirim" % no_a, data={"resi": resi.lower()}, follow_redirects=True)
    cek("kirim: status dikirim + resi tersimpan (huruf besar)", pesanan(no_a)["status"] == "dikirim" and pesanan(no_a)["resi"] == resi)
    cek("Cek Resi publik menemukan lewat resi", "Dalam Pengiriman" in teks(tamu.get("/cek-resi-pesanan?q=" + resi)))
    cek("kirim kedua kali ditolak", "Hanya pesanan berstatus Diproses" in teks(adm.post("/admin/pesanan/%s/kirim" % no_a, data={"resi": "JNE99999"}, follow_redirects=True)))

    # --- selesai ---
    adm.post("/admin/pesanan/%s/selesai" % no_a, follow_redirects=True)
    cek("selesai: status selesai", pesanan(no_a)["status"] == "selesai")
    cek("Cek Resi publik menampilkan Pesanan Diterima", "Pesanan Diterima" in teks(tamu.get("/cek-resi-pesanan?q=" + no_a)))
    cek("selesai kedua kali ditolak", "Hanya pesanan berstatus Dikirim" in teks(adm.post("/admin/pesanan/%s/selesai" % no_a, follow_redirects=True)))

    # --- batal oleh admin ---
    _, no_c = buat_pesanan(buyer_id, pid, harga, 1, status="menunggu_pembayaran", dengan_bukti=False)
    r = adm.post("/admin/pesanan/%s/batal" % no_c, data={"reason": ""}, follow_redirects=True)
    cek("batal tanpa alasan ditolak", "Alasan pembatalan wajib" in teks(r) and pesanan(no_c)["status"] == "menunggu_pembayaran")
    adm.post("/admin/pesanan/%s/batal" % no_c, data={"reason": "Stok kosong"}, follow_redirects=True)
    cek("batal: status dibatalkan", pesanan(no_c)["status"] == "dibatalkan")
    cek("batal pesanan yang sudah diproses/selesai ditolak", "Hanya pesanan yang belum dibayar" in teks(adm.post("/admin/pesanan/%s/batal" % no_a, data={"reason": "x"}, follow_redirects=True)))
    cek("riwayat tercatat untuk setiap aksi", db.query_one("SELECT COUNT(*) AS n FROM order_status_history h JOIN orders o ON o.id = h.order_id WHERE o.order_no = %s", (no_a,))["n"] == 4)

    r = adm.get("/admin/")
    cek("dashboard tetap tampil setelah semua aksi", r.status_code == 200 and "Omzet bulan ini" in teks(r))
finally:
    for uid in uids:
        db.execute("DELETE FROM orders WHERE user_id = %s", (uid,))
        db.execute("DELETE FROM users WHERE id = %s", (uid,))
    for rel in berkas:
        (UPLOAD_DIR / rel).unlink(missing_ok=True)
    if stok_asli is not None:
        db.execute("UPDATE products SET stock = %s WHERE id = %s", (stok_asli, pid))

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
