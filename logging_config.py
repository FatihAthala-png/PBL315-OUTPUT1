"""Konfigurasi logging terpusat KAMISTORE.

Satu tempat untuk mengatur semua log aplikasi:
  - format seragam: waktu | level | nama logger | pesan
  - keluaran ke konsol (stdout -> ditangkap journald saat dijalankan systemd)
  - keluaran ke berkas berotasi logs/kamistore.log (maks 1 MB, simpan 5 cadangan)

Pengaturan lewat .env (semuanya opsional):
  LOG_LEVEL=INFO          DEBUG / INFO / WARNING / ERROR
  LOG_DIR=logs            folder berkas log
  LOG_TO_FILE=1           isi 0 untuk mematikan berkas log

Dipanggil sekali dari app.py:  setup_logging(app)
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_BYTES = 1_000_000
BACKUP_COUNT = 5

_HANDLER_TAG = "_kamistore_handler"


def setup_logging(app=None):
    """Pasang handler konsol + berkas berotasi pada root logger (aman dipanggil berulang)."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    root = logging.getLogger()
    root.setLevel(level)

    # Buang handler buatan kita dari pemanggilan sebelumnya agar log tidak ganda.
    for h in list(root.handlers):
        if getattr(h, _HANDLER_TAG, False):
            root.removeHandler(h)
            h.close()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    setattr(console, _HANDLER_TAG, True)
    root.addHandler(console)

    if os.getenv("LOG_TO_FILE", "1") == "1":
        log_dir = os.getenv("LOG_DIR", "logs")
        try:
            os.makedirs(log_dir, exist_ok=True)
            fh = RotatingFileHandler(
                os.path.join(log_dir, "kamistore.log"),
                maxBytes=MAX_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
            )
            fh.setFormatter(formatter)
            setattr(fh, _HANDLER_TAG, True)
            root.addHandler(fh)
        except OSError as exc:  # mis. folder read-only di server: tetap jalan, hanya konsol
            root.warning("Berkas log tidak bisa dibuat (%s); memakai konsol saja.", exc)

    if app is not None:
        # app.logger ikut ke root; hindari handler bawaan Flask yang membuat baris ganda.
        app.logger.handlers.clear()
        app.logger.propagate = True
        app.logger.setLevel(level)

    return root
