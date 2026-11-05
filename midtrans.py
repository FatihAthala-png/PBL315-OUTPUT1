"""Klien Midtrans (Snap) hanya dengan pustaka standar: tanpa paket tambahan.

Dibaca dari .env setiap dipakai:
  MIDTRANS_SERVER_KEY   kunci server (RAHASIA, jangan di-commit)
  MIDTRANS_CLIENT_KEY   kunci klien (dipakai snap.js di browser)
  MIDTRANS_PRODUCTION   0 = sandbox (bawaan), 1 = produksi
"""
import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class MidtransError(Exception):
    """Gagal berbicara dengan Midtrans."""


class MidtransNotFound(MidtransError):
    """Transaksi tidak ada di Midtrans (metode bayar belum pernah dipilih)."""


def _env(name):
    return os.getenv(name, "").strip()


def server_key():
    return _env("MIDTRANS_SERVER_KEY")


def client_key():
    return _env("MIDTRANS_CLIENT_KEY")


def production():
    return _env("MIDTRANS_PRODUCTION") == "1"


def configured():
    return bool(server_key() and client_key())


def _hosts():
    """(host Snap, host API status)"""
    if production():
        return "https://app.midtrans.com", "https://api.midtrans.com"
    return "https://app.sandbox.midtrans.com", "https://api.sandbox.midtrans.com"


def snap_js_url():
    return _hosts()[0] + "/snap/snap.js"


def public_config():
    """Hanya yang aman dikirim ke browser (TANPA server key)."""
    return {"enabled": configured(), "client_key": client_key(), "snap_js": snap_js_url()}


# ---------------------------------------------------------------------------
# Satu-satunya pintu keluar jaringan (diganti oleh pengujian)
# ---------------------------------------------------------------------------
def _http(method, url, body=None, timeout=15):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    auth = base64.b64encode((server_key() + ":").encode("utf-8")).decode("ascii")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Basic " + auth,
            "User-Agent": "kamistore/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status, raw = response.status, response.read(1_000_000)
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read(1_000_000)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise MidtransError("Tidak bisa menghubungi Midtrans.") from exc
    try:
        payload = json.loads(raw.decode("utf-8") or "{}")
    except ValueError as exc:
        raise MidtransError("Respons Midtrans tidak dapat dibaca.") from exc
    return status, (payload if isinstance(payload, dict) else {})


# ---------------------------------------------------------------------------
# Snap & Status API
# ---------------------------------------------------------------------------
def build_items(items, shipping_cost):
    """item_details: jumlah harga x qty HARUS sama dengan gross_amount."""
    out = [
        {
            "id": str(i["product_id"])[:50],
            "price": int(i["unit_price"]),
            "quantity": int(i["qty"]),
            "name": str(i["name"])[:50],  # batas Midtrans: 50 karakter
        }
        for i in items
    ]
    if int(shipping_cost) > 0:
        out.append({"id": "ONGKIR", "price": int(shipping_cost), "quantity": 1, "name": "Ongkos kirim"})
    return out


def create_snap(order_id, gross_amount, customer, items, expiry_hours=24):
    """Buat transaksi Snap -> {'token', 'redirect_url'}."""
    body = {
        "transaction_details": {"order_id": order_id, "gross_amount": int(gross_amount)},
        "item_details": items,
        "customer_details": customer,
        "expiry": {"unit": "hours", "duration": expiry_hours},
    }
    status, data = _http("POST", _hosts()[0] + "/snap/v1/transactions", body)
    if status not in (200, 201) or "token" not in data:
        messages = data.get("error_messages") or []
        detail = "; ".join(str(m) for m in messages)[:200] if isinstance(messages, list) else ""
        raise MidtransError("Midtrans menolak transaksi" + (": " + detail if detail else "."))
    return {"token": data["token"], "redirect_url": data.get("redirect_url", "")}


def get_status(order_id):
    """Status transaksi dari Midtrans. MidtransNotFound kalau belum ada."""
    url = _hosts()[1] + "/v2/" + urllib.parse.quote(order_id, safe="") + "/status"
    status, data = _http("GET", url, timeout=8)
    # Midtrans kadang menjawab HTTP 200 dengan status_code "404" di dalam isinya.
    if status == 404 or str(data.get("status_code")) == "404":
        raise MidtransNotFound("Transaksi tidak ditemukan di Midtrans.")
    if status != 200:
        raise MidtransError("Midtrans menjawab status %s." % status)
    return data


# ---------------------------------------------------------------------------
# Notifikasi (webhook)
# ---------------------------------------------------------------------------
def signature_ok(payload):
    """signature_key = SHA512(order_id + status_code + gross_amount + ServerKey)."""
    key = server_key()
    if not key:
        return False
    try:
        raw = str(payload["order_id"]) + str(payload["status_code"]) + str(payload["gross_amount"]) + key
    except KeyError:
        return False
    expected = hashlib.sha512(raw.encode("utf-8")).hexdigest().encode("ascii")
    given = str(payload.get("signature_key", "")).lower().encode("utf-8", "ignore")
    return hmac.compare_digest(expected, given)


def classify(payload):
    """paid | pending | failed | info"""
    status = payload.get("transaction_status")
    fraud = payload.get("fraud_status")
    if status == "settlement":
        return "paid"
    if status == "capture":
        return "paid" if fraud in (None, "accept") else "pending"  # 'challenge' = ditahan Midtrans
    if status == "pending":
        return "pending"
    if status in ("deny", "cancel", "expire", "failure"):
        return "failed"
    return "info"  # refund, partial_refund, chargeback, dst.
