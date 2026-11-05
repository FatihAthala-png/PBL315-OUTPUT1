"""Pembatas laju sederhana: di memori, per proses.

Dipakai untuk: penguncian setelah terlalu banyak login gagal, batas pendaftaran,
batas pengecekan resi, dan batas percobaan ganti kata sandi.

Hitungan disimpan di memori proses. Itu cukup selama gunicorn berjalan dengan
SATU worker (lihat gunicorn.conf.py): kalau worker ditambah, hitungan terpisah
per proses dan batasnya menjadi longgar. Hitungan juga hilang saat service
di-restart.
"""
import threading
import time
from collections import deque

_lock = threading.Lock()
_events = {}   # (nama, kunci) -> deque waktu kejadian
_windows = {}  # (nama, kunci) -> jendela waktu terbesar yang dipakai (untuk pembersihan)
_ops = 0
_GC_EVERY = 500


def _now():
    return time.monotonic()


def _key(name, key):
    return (name, str(key if key is not None else "-")[:150])


def _trim(dq, window, now):
    while dq and now - dq[0] >= window:
        dq.popleft()


def _gc(now):
    """Buang kunci yang semua kejadiannya sudah kedaluwarsa (cegah memori membengkak)."""
    for k in list(_events):
        dq = _events[k]
        _trim(dq, _windows.get(k, 0), now)
        if not dq:
            _events.pop(k, None)
            _windows.pop(k, None)


def _add(k, window, now):
    global _ops
    _events.setdefault(k, deque()).append(now)
    _windows[k] = max(_windows.get(k, 0), window)
    _ops += 1
    if _ops % _GC_EVERY == 0:
        _gc(now)


def count(name, key, window):
    """Jumlah kejadian dalam `window` detik terakhir."""
    k = _key(name, key)
    with _lock:
        dq = _events.get(k)
        if not dq:
            return 0
        _trim(dq, window, _now())
        return len(dq)


def blocked(name, key, limit, window):
    """True kalau kejadian dalam `window` detik sudah mencapai `limit`."""
    return count(name, key, window) >= limit


def record(name, key, window):
    """Catat satu kejadian (mis. satu login gagal)."""
    with _lock:
        _add(_key(name, key), window, _now())


def hit(name, key, limit, window):
    """Hitung SETIAP permintaan. True bila batas terlampaui (permintaan itu tidak dicatat)."""
    k = _key(name, key)
    with _lock:
        now = _now()
        dq = _events.get(k)
        if dq:
            _trim(dq, window, now)
            if len(dq) >= limit:
                return True
        _add(k, window, now)
        return False


def clear(name, key):
    with _lock:
        k = _key(name, key)
        _events.pop(k, None)
        _windows.pop(k, None)


def reset():
    """Hapus semua hitungan (dipakai pengujian)."""
    with _lock:
        _events.clear()
        _windows.clear()
