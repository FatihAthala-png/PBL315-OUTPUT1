"""Konfigurasi toko: kurir & tarif ongkir, metode pembayaran, label status.

SEMUA ANGKA, REKENING, DAN TARIF DI SINI ADALAH DATA CONTOH.
Ganti dengan tarif dan rekening asli sebelum dipakai sungguhan.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Lokasi berkas upload (bukti bayar). Sengaja di luar folder static supaya tidak
# bisa dibuka langsung lewat URL: hanya lewat route yang memeriksa hak akses.
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR") or BASE_DIR / "instance" / "uploads")
MAX_PROOF_BYTES = 5 * 1024 * 1024

# kode kurir -> label, logo, layanan {kode: (nama layanan, ongkir flat dalam rupiah)}
COURIERS = {
    "jne": {
        "label": "JNE Express",
        "logo": "jne.png",
        "services": {
            "REG": ("Reguler (2-3 hari)", 25000),
            "YES": ("Yakin Esok Sampai (1 hari)", 45000),
        },
    },
    "sicepat": {
        "label": "SiCepat",
        "logo": "sicepat.png",
        "services": {
            "REG": ("Reguler (2-4 hari)", 22000),
            "BEST": ("Besok Sampai Tujuan", 35000),
        },
    },
    "jnt": {
        "label": "J&T Express",
        "logo": "jnt.png",
        "services": {
            "EZ": ("EZ (2-4 hari)", 20000),
        },
    },
}

# kode metode -> info tujuan transfer (CONTOH)
PAYMENT_METHODS = {
    "bca": {"label": "Bank BCA", "logo": "bca.png", "number": "1234567890", "holder": "PT KAMISTORE (contoh)"},
    "mandiri": {"label": "Bank Mandiri", "logo": "mandiri.png", "number": "9876543210", "holder": "PT KAMISTORE (contoh)"},
    "bni": {"label": "Bank BNI", "logo": "bni.png", "number": "1122334455", "holder": "PT KAMISTORE (contoh)"},
    "bri": {"label": "Bank BRI", "logo": "bri.png", "number": "5566778899", "holder": "PT KAMISTORE (contoh)"},
    "qris": {"label": "QRIS", "logo": "qris.png", "number": None, "holder": "KAMISTORE (contoh)"},
}

STATUS_LABELS = {
    "menunggu_pembayaran": "Menunggu Pembayaran",
    "menunggu_approval": "Menunggu Verifikasi",
    "diproses": "Diproses",
    "dikirim": "Dikirim",
    "selesai": "Selesai",
    "dibatalkan": "Dibatalkan",
}
STATUS_TONES = {
    "menunggu_pembayaran": "bg-amber-50 text-amber-700 ring-amber-200",
    "menunggu_approval": "bg-sky-50 text-sky-700 ring-sky-200",
    "diproses": "bg-blue-50 text-blue-700 ring-blue-200",
    "dikirim": "bg-indigo-50 text-indigo-700 ring-indigo-200",
    "selesai": "bg-emerald-50 text-emerald-700 ring-emerald-200",
    "dibatalkan": "bg-slate-100 text-slate-600 ring-slate-300",
}
