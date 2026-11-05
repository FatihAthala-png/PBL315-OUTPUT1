"""Uji pembayaran Midtrans dengan MySQL asli. Tidak memanggil Midtrans sungguhan:
respons Snap/Status API ditiru, sehingga tidak butuh internet atau kunci asli.

Jalankan dari folder proyek (venv aktif):  python smoke_midtrans.py
Membuat user & pesanan uji, lalu menghapusnya dan memulihkan stok produk.
"""
import hashlib
import logging
import os
import secrets
import sys
import urllib.parse

from werkzeug.security import generate_password_hash

import db
import midtrans
import ratelimit
from app import app

gagal = 0
sandi = "Smoke#Test2026"
KEY = "SB-Mid-server-UJI-%s" % secrets.token_hex(4)
CLIENT = "SB-Mid-client-UJI"
HDR = {"X-Requested-With": "fetch"}
JSON_HDR = {"X-Requested-With": "fetch", "Accept": "application/json"}


def cek(label, ok, info=""):
    global gagal
    print(("OK    " if ok else "GAGAL "), label, info)
    if not ok:
        gagal += 1


def teks(r):
    return r.get_data(as_text=True)


# ------------------------------------------------------ Midtrans palsu
STATUS = {}     # id transaksi -> dict | "error"
SNAP_CALLS = []
SNAP_FAIL = [False]


def fake_http(method, url, body=None, timeout=15):
    if url.endswith("/snap/v1/transactions"):
        SNAP_CALLS.append(body)
        if SNAP_FAIL[0]:
            raise midtrans.MidtransError("down")
        oid = body["transaction_details"]["order_id"]
        return 201, {"token": "tok-" + oid, "redirect_url": "https://app.sandbox.midtrans.com/snap/v3/redirection/x"}
    if url.endswith("/status"):
        oid = urllib.parse.unquote(url.split("/v2/", 1)[1].rsplit("/status", 1)[0])
        val = STATUS.get(oid)
        if val == "error":
            raise midtrans.MidtransError("down")
        if val is None:  # perilaku asli Midtrans: HTTP 200 dengan status_code 404 di dalamnya
            return 200, {"status_code": "404", "status_message": "Transaction doesn't exist."}
        return 200, val
    raise AssertionError("URL tak terduga: " + url)


ASLI_HTTP = midtrans._http
midtrans._http = fake_http


def notif(gid, status, total, ptype="bank_transfer", fraud=None, key=None):
    code = {"settlement": "200", "capture": "200", "pending": "201"}.get(status, "202")
    gross = "%d.00" % total
    sig = hashlib.sha512((gid + code + gross + (key or KEY)).encode()).hexdigest()
    d = {"order_id": gid, "status_code": code, "gross_amount": gross, "transaction_status": status,
         "payment_type": ptype, "signature_key": sig}
    if fraud:
        d["fraud_status"] = fraud
    return d


# ---------------------------------------------------------- data uji
def buat_user(nama, role="customer"):
    email = "smoke-mt-%s@example.com" % secrets.token_hex(4)
    uid = db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s)",
        (nama, email, generate_password_hash(sandi), role),
    )
    return uid, email


def login(email):
    c = app.test_client()
    c.post("/login", data={"email": email, "password": sandi})
    return c


def stok():
    return int(db.query_one("SELECT stock FROM products WHERE id = %s", (PID,))["stock"])


def buat_pesanan(uid, qty=2, status="menunggu_pembayaran", nama_item=None):
    no = "KMS-261016-%s" % secrets.token_hex(3).upper()
    total = HARGA * qty + 25000
    oid = db.execute(
        "INSERT INTO orders (order_no, user_id, status, recipient_name, phone, address, city, province, postal_code, "
        "courier, service, subtotal, shipping_cost, total) VALUES (%s, %s, %s, 'Penerima Midtrans', '081200001111', "
        "'Jl. Uji 1', 'Batam', 'Kepri', '29432', 'jne', 'REG', %s, 25000, %s)",
        (no, uid, status, HARGA * qty, total),
    )
    db.execute(
        "INSERT INTO order_items (order_id, product_id, product_name, unit_price, qty) VALUES (%s, %s, %s, %s, %s)",
        (oid, PID, nama_item or "Produk Uji Midtrans", HARGA, qty),
    )
    db.execute("INSERT INTO order_status_history (order_id, title, description) VALUES (%s, 'Pesanan dibuat', 'uji')", (oid,))
    return oid, no, total


def pembayaran(oid):
    return db.query_all("SELECT id, method, status, reject_reason, amount FROM payments WHERE order_id = %s ORDER BY id", (oid,))


def pesanan_row(no):
    return db.query_one("SELECT id, status FROM orders WHERE order_no = %s", (no,))


def riwayat(oid, judul):
    return db.query_one("SELECT COUNT(*) AS n FROM order_status_history WHERE order_id = %s AND title LIKE %s", (oid, judul + "%"))["n"]


def mulai(client, no):
    return client.post("/pesanan/%s/midtrans" % no, headers=JSON_HDR)


def kirim_notif(client, payload, **kw):
    return client.post("/pembayaran/midtrans/notifikasi", json=payload, **kw)


def sisipkan_midtrans(oid, total, status="menunggu"):
    return db.execute(
        "INSERT INTO payments (order_id, method, amount, proof_path, status) VALUES (%s, 'midtrans', %s, 'midtrans', %s)",
        (oid, total, status),
    )


uids = []
env_asli = {k: os.environ.get(k) for k in ("MIDTRANS_SERVER_KEY", "MIDTRANS_CLIENT_KEY", "MIDTRANS_PRODUCTION")}
stok_asli = None
try:
    prod = db.query_one("SELECT id, price, stock FROM products WHERE is_active = 1 AND stock >= 10 ORDER BY id LIMIT 1")
    PID, HARGA, stok_asli = prod["id"], int(prod["price"]), int(prod["stock"])
    app.config["WTF_CSRF_ENABLED"] = False

    a_id, a_mail = buat_user("Pembeli Satu"); uids.append(a_id)
    b_id, b_mail = buat_user("Pembeli Dua"); uids.append(b_id)
    adm_id, adm_mail = buat_user("Admin MT", "admin"); uids.append(adm_id)
    a, b, adm, tamu = login(a_mail), login(b_mail), login(adm_mail), app.test_client()

    # ----------------------------------------------- unit: klasifikasi & tanda tangan
    os.environ["MIDTRANS_SERVER_KEY"] = KEY
    os.environ["MIDTRANS_CLIENT_KEY"] = CLIENT
    os.environ["MIDTRANS_PRODUCTION"] = "0"
    for ts, fs, hasil in (("settlement", None, "paid"), ("capture", "accept", "paid"), ("capture", "challenge", "pending"),
                          ("pending", None, "pending"), ("expire", None, "failed"), ("deny", None, "failed"),
                          ("cancel", None, "failed"), ("refund", None, "info"), ("chargeback", None, "info")):
        cek("klasifikasi %s/%s -> %s" % (ts, fs, hasil), midtrans.classify({"transaction_status": ts, "fraud_status": fs}) == hasil)
    asli = notif("X-1", "settlement", 1000)
    cek("tanda tangan benar diterima", midtrans.signature_ok(asli))
    cek("tanda tangan salah kunci ditolak", not midtrans.signature_ok(notif("X-1", "settlement", 1000, key="kunci-lain")))
    cek("tanda tangan dengan nominal diubah ditolak", not midtrans.signature_ok({**asli, "gross_amount": "1.00"}))
    cek("tanda tangan non-ASCII/kosong tidak membuat error", not midtrans.signature_ok({**asli, "signature_key": "é☃"}) and not midtrans.signature_ok({}))

    # ------------------------------ unit: _http ASLI lewat server HTTP lokal
    import base64
    import http.server
    import json
    import threading

    diterima = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def _balas(self, kode, isi):
            data = isi if isinstance(isi, bytes) else json.dumps(isi).encode()
            self.send_response(kode)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            panjang = int(self.headers.get("Content-Length", 0))
            diterima["auth"] = self.headers.get("Authorization")
            diterima["ctype"] = self.headers.get("Content-Type")
            diterima["body"] = json.loads(self.rfile.read(panjang) or b"{}")
            if self.path == "/ok":
                self._balas(201, {"token": "abc"})
            elif self.path == "/tolak":
                self._balas(400, {"error_messages": ["order_id has already been taken"]})
            else:
                self._balas(200, b"<html>bukan json</html>")

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % port
    try:
        status, data = ASLI_HTTP("POST", base + "/ok", {"a": 1})
        auth_benar = "Basic " + base64.b64encode((KEY + ":").encode()).decode()
        cek("_http asli: JSON + Basic Auth benar terkirim, balasan terbaca",
            status == 201 and data == {"token": "abc"} and diterima["body"] == {"a": 1}
            and diterima["auth"] == auth_benar and diterima["ctype"] == "application/json")
        status, data = ASLI_HTTP("POST", base + "/tolak", {})
        cek("_http asli: HTTP 400 berisi JSON tetap dikembalikan", status == 400 and "error_messages" in data)
        try:
            ASLI_HTTP("POST", base + "/html", {})
            ok = False
        except midtrans.MidtransError:
            ok = True
        cek("_http asli: balasan bukan JSON -> MidtransError", ok)
    finally:
        server.shutdown()
        server.server_close()
    try:
        ASLI_HTTP("GET", base + "/x", None, 2)
        ok = False
    except midtrans.MidtransError:
        ok = True
    cek("_http asli: koneksi gagal -> MidtransError (bukan crash)", ok)

    midtrans._http = lambda *a, **k: (400, {"error_messages": ["transaction_details.order_id has already been taken"]})
    try:
        midtrans.create_snap("X", 1000, {}, [])
        pesan = ""
    except midtrans.MidtransError as exc:
        pesan = str(exc)
    cek("create_snap: penolakan Midtrans -> MidtransError memuat alasannya", "already been taken" in pesan, pesan)
    midtrans._http = lambda *a, **k: (500, {})
    try:
        midtrans.get_status("X-1")
        jenis = None
    except midtrans.MidtransNotFound:
        jenis = "notfound"
    except midtrans.MidtransError:
        jenis = "error"
    cek("get_status: HTTP 500 -> MidtransError biasa (bukan 'tidak ditemukan')", jenis == "error", jenis)
    midtrans._http = fake_http

    # ------------------------------------------------------------ belum dikonfigurasi
    ratelimit.reset()
    _, no0, _ = buat_pesanan(a_id)
    os.environ.pop("MIDTRANS_SERVER_KEY"); os.environ.pop("MIDTRANS_CLIENT_KEY")
    r = mulai(a, no0)
    cek("tanpa kunci Midtrans: mulai bayar -> 503", r.status_code == 503 and r.get_json()["ok"] is False, r.status_code)
    cek("tanpa kunci: tombol Midtrans tidak tampil", "Bayar dengan Midtrans" not in teks(a.get("/pesanan/" + no0)))
    os.environ["MIDTRANS_SERVER_KEY"] = KEY; os.environ["MIDTRANS_CLIENT_KEY"] = CLIENT

    # ------------------------------------------------------------ tampilan
    h = teks(a.get("/pesanan/" + no0))
    cek("dengan kunci: tombol + snap.js sandbox + client key tampil",
        "Bayar dengan Midtrans" in h and "https://app.sandbox.midtrans.com/snap/snap.js" in h and CLIENT in h)
    cek("server key TIDAK pernah muncul di halaman", KEY not in h)
    os.environ["MIDTRANS_PRODUCTION"] = "1"
    cek("mode produksi memakai host produksi", "https://app.midtrans.com/snap/snap.js" in teks(a.get("/pesanan/" + no0)))
    os.environ["MIDTRANS_PRODUCTION"] = "0"

    # ------------------------------------------------------------ mulai bayar
    ratelimit.reset()
    oid1, no1, t1 = buat_pesanan(a_id, 2, nama_item="X" * 120)
    cek("tamu mulai bayar -> diarahkan login", tamu.post("/pesanan/%s/midtrans" % no1, headers=JSON_HDR).status_code == 302)
    cek("pembeli lain mulai bayar -> 404", mulai(b, no1).status_code == 404)
    app.config["WTF_CSRF_ENABLED"] = True
    cek("mulai bayar tanpa token CSRF ditolak", a.post("/pesanan/%s/midtrans" % no1, headers=JSON_HDR).status_code == 400)
    app.config["WTF_CSRF_ENABLED"] = False

    r = mulai(a, no1)
    j = r.get_json()
    pay1 = pembayaran(oid1)
    cek("mulai bayar -> token Snap", r.status_code == 200 and j["ok"] and j["token"] == "tok-%s-%d" % (no1, pay1[0]["id"]), r.status_code)
    cek("baris pembayaran midtrans 'menunggu' dengan nominal = total", len(pay1) == 1 and pay1[0]["method"] == "midtrans" and pay1[0]["status"] == "menunggu" and int(pay1[0]["amount"]) == t1)
    body = SNAP_CALLS[-1]
    items = body["item_details"]
    cek("order_id ke Midtrans = nomor-pesanan-idPembayaran", body["transaction_details"]["order_id"] == "%s-%d" % (no1, pay1[0]["id"]))
    cek("gross_amount = total pesanan", body["transaction_details"]["gross_amount"] == t1)
    cek("jumlah item_details = gross_amount (aturan Midtrans)", sum(i["price"] * i["quantity"] for i in items) == t1, items)
    cek("nama item dipotong maks 50 karakter + ada item ongkir", all(len(i["name"]) <= 50 for i in items) and any(i["id"] == "ONGKIR" for i in items))
    cek("data pembeli ikut dikirim (email)", body["customer_details"]["email"] == a_mail)

    # percobaan baru: percobaan lama belum pernah dipilih metodenya (404) -> ditandai tidak dilanjutkan
    r = mulai(a, no1)
    pay1 = pembayaran(oid1)
    cek("percobaan ke-2: yang lama 'ditolak', yang baru 'menunggu'", r.status_code == 200 and [p["status"] for p in pay1] == ["ditolak", "menunggu"], [p["status"] for p in pay1])
    gid1 = "%s-%d" % (no1, pay1[1]["id"])

    # percobaan lama masih pending di Midtrans -> tidak boleh membuat yang baru (cegah bayar ganda)
    STATUS[gid1] = notif(gid1, "pending", t1)
    r = mulai(a, no1)
    cek("ada transaksi pending di Midtrans -> 409, tidak ada baris baru", r.status_code == 409 and "masih menunggu" in r.get_json()["message"] and len(pembayaran(oid1)) == 2, r.status_code)
    STATUS[gid1] = "error"
    r = mulai(a, no1)
    cek("Midtrans tak terjangkau saat cek percobaan lama -> 502", r.status_code == 502 and len(pembayaran(oid1)) == 2, r.status_code)
    STATUS.pop(gid1)

    # ------------------------------------------------------------ webhook
    ratelimit.reset()
    stok0 = stok()
    r = kirim_notif(tamu, notif(gid1, "settlement", t1, key="kunci-palsu"))
    cek("webhook dengan tanda tangan palsu -> 403, tidak ada perubahan", r.status_code == 403 and pesanan_row(no1)["status"] == "menunggu_pembayaran" and stok() == stok0, r.status_code)
    r = tamu.post("/pembayaran/midtrans/notifikasi", data="bukan json", content_type="text/plain")
    cek("webhook bukan JSON -> 400", r.status_code == 400)
    r = kirim_notif(tamu, notif("KMS-000000-NOPE-99", "settlement", 1000))
    cek("webhook order tak dikenal (tanda tangan sah) -> 200 diabaikan", r.status_code == 200 and r.get_json()["result"] == "unknown")
    r = kirim_notif(tamu, notif(gid1, "settlement", t1 + 1))
    cek("webhook nominal tidak cocok -> diabaikan, pesanan tidak berubah", r.get_json()["result"] == "amount_mismatch" and pesanan_row(no1)["status"] == "menunggu_pembayaran")
    r = kirim_notif(tamu, notif("KMS-261016-AAAAAA-%d" % pay1[1]["id"], "settlement", t1))
    cek("webhook nomor pesanan tidak cocok dengan id pembayaran -> diabaikan", r.get_json()["result"] == "unknown")

    r = kirim_notif(tamu, notif(gid1, "pending", t1))
    kirim_notif(tamu, notif(gid1, "pending", t1))
    cek("notifikasi pending: pesanan tetap, riwayat hanya satu (idempoten)", r.get_json()["result"] == "pending" and pesanan_row(no1)["status"] == "menunggu_pembayaran" and riwayat(oid1, "Menunggu pembayaran via Midtrans") == 1)

    app.config["WTF_CSRF_ENABLED"] = True  # webhook harus bebas CSRF
    r = kirim_notif(tamu, notif(gid1, "settlement", t1, ptype="bca_va"))
    app.config["WTF_CSRF_ENABLED"] = False
    cek("settlement (CSRF aktif): webhook tetap diterima -> paid", r.status_code == 200 and r.get_json()["result"] == "paid", r.status_code)
    p = pembayaran(oid1)
    cek("pesanan langsung 'diproses' tanpa verifikasi admin", pesanan_row(no1)["status"] == "diproses")
    cek("stok berkurang sebesar jumlah pesanan", stok() == stok0 - 2, stok())
    cek("pembayaran 'disetujui'; percobaan lain tidak ikut berubah", p[1]["status"] == "disetujui")
    cek("riwayat: pembayaran diterima + disetujui", riwayat(oid1, "Pembayaran diterima via Midtrans") == 1 and riwayat(oid1, "Pembayaran disetujui") == 1)
    r = kirim_notif(tamu, notif(gid1, "settlement", t1))
    cek("settlement diulang: tidak mengurangi stok lagi", r.get_json()["result"] == "already_final" and stok() == stok0 - 2 and riwayat(oid1, "Pembayaran disetujui") == 1)
    cek("pembeli melihat status Diproses tanpa tautan bukti file", "Diproses" in teks(a.get("/pesanan/" + no1)) and "Lihat bukti" not in teks(a.get("/pesanan/" + no1)))
    ha = teks(adm.get("/admin/pesanan/" + no1))
    cek("halaman admin: metode MIDTRANS tampil, tanpa tautan bukti berkas", "MIDTRANS" in ha and "Buka bukti pembayaran" not in ha)
    cek("mulai bayar pada pesanan yang sudah dibayar -> 409", mulai(a, no1).status_code == 409)

    # ------------------------------------------------------------ gagal lalu coba lagi
    ratelimit.reset()
    oid2, no2, t2 = buat_pesanan(a_id)
    mulai(a, no2)
    gid2 = "%s-%d" % (no2, pembayaran(oid2)[0]["id"])
    r = kirim_notif(tamu, notif(gid2, "expire", t2))
    p = pembayaran(oid2)
    cek("expire: pembayaran 'ditolak' + alasan, pesanan tetap menunggu_pembayaran", r.get_json()["result"] == "failed" and p[0]["status"] == "ditolak" and "expire" in p[0]["reject_reason"] and pesanan_row(no2)["status"] == "menunggu_pembayaran")
    r = mulai(a, no2)
    cek("setelah gagal, bisa mulai bayar lagi", r.status_code == 200 and len(pembayaran(oid2)) == 2)
    gid2b = "%s-%d" % (no2, pembayaran(oid2)[1]["id"])
    r = kirim_notif(tamu, notif(gid2, "settlement", t2))
    cek("uang masuk di percobaan yang sempat 'ditolak' tetap diproses (uang tidak hilang)", r.get_json()["result"] == "paid" and pesanan_row(no2)["status"] == "diproses")
    cek("percobaan ke-2 yang masih menunggu otomatis ditutup", [x["status"] for x in pembayaran(oid2)] == ["disetujui", "ditolak"])

    # ------------------------------------------------------------ kartu: capture
    oid3, no3, t3 = buat_pesanan(a_id)
    mulai(a, no3)
    gid3 = "%s-%d" % (no3, pembayaran(oid3)[0]["id"])
    r = kirim_notif(tamu, notif(gid3, "capture", t3, ptype="credit_card", fraud="challenge"))
    cek("capture + fraud challenge -> tetap pending", r.get_json()["result"] == "pending" and pesanan_row(no3)["status"] == "menunggu_pembayaran")
    r = kirim_notif(tamu, notif(gid3, "capture", t3, ptype="credit_card", fraud="accept"))
    cek("capture + fraud accept -> paid", r.get_json()["result"] == "paid" and pesanan_row(no3)["status"] == "diproses")

    # ------------------------------------------------------------ stok habis saat bayar
    stok_sebelum = stok()
    oid4, no4, t4 = buat_pesanan(a_id, 3)
    mulai(a, no4)
    gid4 = "%s-%d" % (no4, pembayaran(oid4)[0]["id"])
    db.execute("UPDATE products SET stock = 1 WHERE id = %s", (PID,))
    r = kirim_notif(tamu, notif(gid4, "settlement", t4))
    cek("stok habis saat uang masuk -> menunggu_approval, stok tetap, payment tetap menunggu",
        r.get_json()["result"] == "stock_short" and pesanan_row(no4)["status"] == "menunggu_approval" and stok() == 1 and pembayaran(oid4)[0]["status"] == "menunggu")
    cek("riwayat mencatat perlunya tindakan admin", riwayat(oid4, "Pembayaran Midtrans diterima, stok tidak cukup") == 1)
    db.execute("UPDATE products SET stock = 10 WHERE id = %s", (PID,))
    adm.post("/admin/pesanan/%s/setujui" % no4)
    cek("setelah stok ditambah, admin bisa menyetujui lewat alur biasa", pesanan_row(no4)["status"] == "diproses" and stok() == 7, stok())
    db.execute("UPDATE products SET stock = %s WHERE id = %s", (stok_sebelum, PID))

    # ------------------------------------------------------------ kasus tepi pembayaran
    stok_k = stok()
    oid5, no5, t5 = buat_pesanan(a_id, 1, status="dibatalkan")
    p5 = sisipkan_midtrans(oid5, t5)
    r = kirim_notif(tamu, notif("%s-%d" % (no5, p5), "settlement", t5))
    cek("bayar untuk pesanan yang sudah dibatalkan: tetap dibatalkan, ditandai perlu refund", r.get_json()["result"] == "paid_cancelled" and pesanan_row(no5)["status"] == "dibatalkan" and riwayat(oid5, "Pembayaran Midtrans diterima untuk pesanan yang sudah dibatalkan") == 1 and stok() == stok_k)

    oid6, no6, t6 = buat_pesanan(a_id, 1, status="diproses")
    p6 = sisipkan_midtrans(oid6, t6)
    r = kirim_notif(tamu, notif("%s-%d" % (no6, p6), "settlement", t6))
    cek("pembayaran ganda pada pesanan yang sudah diproses: stok tidak berkurang lagi", r.get_json()["result"] == "duplicate" and stok() == stok_k and riwayat(oid6, "Pembayaran Midtrans ganda") == 1)

    oid7, no7, t7 = buat_pesanan(a_id, 2, status="menunggu_approval")
    db.execute("INSERT INTO payments (order_id, method, amount, proof_path) VALUES (%s, 'bca', %s, 'payments/x.png')", (oid7, t7))
    p7 = sisipkan_midtrans(oid7, t7)
    r = kirim_notif(tamu, notif("%s-%d" % (no7, p7), "settlement", t7))
    st7 = {x["method"]: x for x in pembayaran(oid7)}
    cek("upload manual menunggu + Midtrans lunas: pesanan diproses, bukti manual ditutup", r.get_json()["result"] == "paid" and pesanan_row(no7)["status"] == "diproses" and st7["bca"]["status"] == "ditolak" and "Midtrans" in st7["bca"]["reject_reason"] and stok() == stok_k - 2)
    r = kirim_notif(tamu, notif("%s-%d" % (no7, p7), "refund", t7))
    cek("notifikasi refund: hanya dicatat, status pesanan tidak berubah", r.get_json()["result"] == "noted" and pesanan_row(no7)["status"] == "diproses" and riwayat(oid7, "Catatan Midtrans: refund") == 1)

    # ------------------------------------------------------------ tombol Cek status
    ratelimit.reset()
    oid8, no8, t8 = buat_pesanan(a_id)
    mulai(a, no8)
    g8 = "%s-%d" % (no8, pembayaran(oid8)[0]["id"])
    STATUS[g8] = notif(g8, "settlement", t8)
    r = a.post("/pesanan/%s/midtrans/cek" % no8, follow_redirects=True)
    cek("Cek status: Midtrans sudah lunas -> pesanan diproses", "Pembayaran diterima" in teks(r) and pesanan_row(no8)["status"] == "diproses")

    oid9, no9, t9 = buat_pesanan(a_id)
    mulai(a, no9)
    g9 = "%s-%d" % (no9, pembayaran(oid9)[0]["id"])
    STATUS[g9] = notif(g9, "pending", t9)
    r = a.post("/pesanan/%s/midtrans/cek" % no9, follow_redirects=True)
    cek("Cek status: masih pending -> pesan 'belum selesai'", "belum selesai" in teks(r) and pesanan_row(no9)["status"] == "menunggu_pembayaran")
    cek("halaman menampilkan tombol Cek status saat ada percobaan menunggu", "Cek status pembayaran" in teks(a.get("/pesanan/" + no9)))

    oid10, no10, t10 = buat_pesanan(a_id)
    mulai(a, no10)
    r = a.post("/pesanan/%s/midtrans/cek" % no10, follow_redirects=True)
    cek("Cek status: transaksi tidak ada di Midtrans -> percobaan ditutup", "tidak berhasil" in teks(r) and pembayaran(oid10)[0]["status"] == "ditolak")
    r = a.post("/pesanan/%s/midtrans/cek" % no10, follow_redirects=True)
    cek("Cek status tanpa percobaan menunggu -> pesan jelas", "Tidak ada pembayaran Midtrans" in teks(r))

    oid11, no11, t11 = buat_pesanan(a_id)
    mulai(a, no11)
    g11 = "%s-%d" % (no11, pembayaran(oid11)[0]["id"])
    STATUS[g11] = "error"
    r = a.post("/pesanan/%s/midtrans/cek" % no11, follow_redirects=True)
    cek("Cek status saat Midtrans tak terjangkau: pesan error, data tidak berubah", "Tidak bisa memeriksa" in teks(r) and pembayaran(oid11)[0]["status"] == "menunggu")
    cek("pembeli lain tidak bisa Cek status pesanan orang (404)", b.post("/pesanan/%s/midtrans/cek" % no11).status_code == 404)

    # ------------------------------------------------------------ Snap gagal & batas laju
    ratelimit.reset()
    oid12, no12, t12 = buat_pesanan(a_id)
    SNAP_FAIL[0] = True
    logging.getLogger("kamistore.midtrans").disabled = True  # kegagalan ini disengaja
    r = mulai(a, no12)
    logging.getLogger("kamistore.midtrans").disabled = False
    cek("Snap gagal: 502 dengan pesan ramah, percobaan ditutup", r.status_code == 502 and "tidak merespons" in r.get_json()["message"] and pembayaran(oid12)[0]["status"] == "ditolak", r.status_code)
    SNAP_FAIL[0] = False
    ratelimit.reset()
    kode = [mulai(a, "KMS-BUKAN-ADA").status_code for _ in range(11)]
    cek("batas laju: 10 permintaan/menit, ke-11 -> 429", kode[:10] == [404] * 10 and kode[10] == 429, kode[-2:])
finally:
    for uid in uids:
        db.execute("DELETE FROM orders WHERE user_id = %s", (uid,))
        db.execute("DELETE FROM users WHERE id = %s", (uid,))
    if stok_asli is not None:
        db.execute("UPDATE products SET stock = %s WHERE id = %s", (stok_asli, PID))
    for k, v in env_asli.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

print()
print("SEMUA LOLOS" if not gagal else "%d pengujian GAGAL" % gagal)
sys.exit(1 if gagal else 0)
