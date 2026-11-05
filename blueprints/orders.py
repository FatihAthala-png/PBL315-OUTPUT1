"""Blueprint 'orders': Cek Resi & Pesanan publik (data asli dari MySQL)."""
from flask import Blueprint, abort, g, render_template, request

import order_data
import ratelimit
from blueprints.pesanan import tanggal_filter
from catalog import format_date, format_rupiah
from store_config import COURIERS, STATUS_LABELS

bp = Blueprint("orders", __name__)

# Langkah status pesanan: (label, ikon Material Symbols).
ORDER_STEPS = [
    ("Dibayar", "payments"),
    ("Dikemas", "inventory_2"),
    ("Dikirim", "local_shipping"),
    ("Diterima", "check_circle"),
]

# status pesanan -> langkah terakhir yang sudah dicapai (-1 = belum ada)
STEP_BY_STATUS = {
    "menunggu_pembayaran": -1,
    "menunggu_approval": -1,
    "diproses": 1,
    "dikirim": 2,
    "selesai": 3,
    "dibatalkan": -1,
}
TONE_BY_STATUS = {
    "menunggu_pembayaran": "amber",
    "menunggu_approval": "amber",
    "diproses": "blue",
    "dikirim": "blue",
    "selesai": "emerald",
    "dibatalkan": "slate",
}
LABEL_BY_STATUS = {
    "menunggu_pembayaran": "Menunggu Pembayaran",
    "menunggu_approval": "Menunggu Verifikasi Pembayaran",
    "diproses": "Sedang Dikemas",
    "dikirim": "Dalam Pengiriman",
    "selesai": "Pesanan Diterima",
    "dibatalkan": "Pesanan Dibatalkan",
}


def mask_name(name):
    """'Budi Santoso' -> 'B*** S.' (halaman ini publik, nama tidak ditampilkan penuh)."""
    parts = (name or "").split()
    if not parts:
        return "-"
    masked = [parts[0][0].upper() + "***"]
    masked += ["%s." % p[0].upper() for p in parts[1:2]]
    return " ".join(masked)


def public_view(order):
    """Bentuk data pesanan yang aman ditampilkan ke siapa pun yang punya nomornya."""
    courier = COURIERS.get(order["courier"] or "", {})
    service = courier.get("services", {}).get(order["service"] or "")
    status = order["status"]
    return {
        "order_no": order["order_no"],
        "resi": order["resi"],
        "courier": courier.get("label", order["courier"] or "-"),
        "courier_logo": courier.get("logo", ""),
        "service": service[0] if service else (order["service"] or "-"),
        "date": format_date(order["created_at"]),
        "step": STEP_BY_STATUS.get(status, -1),
        "tone": TONE_BY_STATUS.get(status, "amber"),
        "status_label": LABEL_BY_STATUS.get(status, STATUS_LABELS.get(status, status)),
        "recipient": mask_name(order["recipient_name"]),
        # Hanya kota & provinsi: alamat jalan dan nomor telepon tidak ditampilkan.
        "address": "%s, %s" % (order["city"], order["province"]),
        "items": [
            {"name": i["name"], "qty": i["qty"], "price": format_rupiah(i["line_total"])}
            for i in order["items"]
        ],
        "shipping": format_rupiah(int(order["shipping_cost"])),
        "total": format_rupiah(int(order["total"])),
        "history": [
            (tanggal_filter(h["created_at"]), h["title"], h["description"])
            for h in order["history"]
        ],
    }


@bp.route("/cek-resi-pesanan")
def tracking():
    query = request.args.get("q", "").strip()[:50]
    order = None
    if query:
        if ratelimit.hit("tracking", request.remote_addr, 60, 60):
            abort(429)
        order_no = order_data.find_order_no(query)
        raw = order_data.get_order(order_no) if order_no else None
        order = public_view(raw) if raw else None

    user = g.get("user")
    return render_template(
        "tracking.html",
        active_page="cek_resi_pesanan",
        query=query,
        order=order,
        steps=ORDER_STEPS,
        my_orders=order_data.list_orders(user["id"])[:3] if user else [],
    )
