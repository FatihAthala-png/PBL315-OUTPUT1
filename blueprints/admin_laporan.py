"""Blueprint 'admin_laporan': laporan transaksi + ekspor CSV."""
import csv
import io
from datetime import date, datetime

from flask import Blueprint, Response, flash, request

import admin_data
from blueprints.admin import _render
from catalog import format_date
from security import admin_required
from store_config import COURIERS

bp = Blueprint("admin_laporan", __name__, url_prefix="/admin/laporan")

MAX_DAYS = 366


@bp.app_template_filter("hari")
def hari_filter(value):
    """'15 Mar 2020' dari date, datetime, atau string ISO."""
    return format_date(value)


def parse_range(args):
    """-> (dari, sampai, pesan_error). Bila tidak valid dipakai bulan berjalan."""
    today = date.today()
    default = (today.replace(day=1), today)
    try:
        raw_from, raw_to = args.get("dari", ""), args.get("sampai", "")
        dari = datetime.strptime(raw_from, "%Y-%m-%d").date() if raw_from else default[0]
        sampai = datetime.strptime(raw_to, "%Y-%m-%d").date() if raw_to else default[1]
    except ValueError:
        return default[0], default[1], "Format tanggal tidak valid (gunakan YYYY-MM-DD)."
    if dari > sampai:
        return default[0], default[1], "Tanggal awal tidak boleh setelah tanggal akhir."
    if (sampai - dari).days > MAX_DAYS:
        return default[0], default[1], "Rentang laporan maksimal 1 tahun."
    return dari, sampai, None


def _csv_safe(value):
    """Cegah CSV injection: sel teks yang diawali = + - @ diberi awalan tanda petik."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


@bp.route("/")
@admin_required
def index():
    dari, sampai, error = parse_range(request.args)
    if error:
        flash(error, "error")
    return _render(
        "admin/report.html", "laporan", dari=dari, sampai=sampai,
        data=admin_data.report(dari, sampai),
    )


@bp.route("/csv")
@admin_required
def export_csv():
    dari, sampai, error = parse_range(request.args)
    rows = admin_data.report_transactions(dari, sampai, limit=10000)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["No. Pesanan", "Disetujui", "Email Pembeli", "Penerima", "Metode", "Kurir",
                     "Subtotal", "Ongkir", "Total", "Status"])
    for r in rows:
        writer.writerow([
            _csv_safe(r["order_no"]), _csv_safe(r["reviewed_at"]), _csv_safe(r["email"]),
            _csv_safe(r["recipient_name"]), _csv_safe(r["method"]),
            _csv_safe(COURIERS.get(r["courier"] or "", {}).get("label", r["courier"])),
            int(r["subtotal"]), int(r["shipping_cost"]), int(r["amount"]), _csv_safe(r["status"]),
        ])
    filename = "laporan-%s_%s.csv" % (dari.isoformat(), sampai.isoformat())
    # BOM supaya Excel membaca UTF-8 dengan benar.
    return Response(
        "\ufeff" + buffer.getvalue(),
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="%s"' % filename},
    )
