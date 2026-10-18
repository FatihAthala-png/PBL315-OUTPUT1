"""Konfigurasi gunicorn untuk KAMISTORE.

Dijalankan oleh service systemd (deploy/kamistore.service):
    gunicorn --config gunicorn.conf.py app:app

SATU worker proses dengan banyak thread, sengaja: pembatas percobaan login
(ratelimit.py) menyimpan hitungan di memori proses, jadi hanya konsisten kalau
semua permintaan lewat satu proses.
"""
import os

# Port 8000 dibuka oleh firewall hanya untuk NGINX (10.10.10.2) dan jaringan development.
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

worker_class = "gthread"
workers = 1
threads = 8

timeout = 60
graceful_timeout = 30
keepalive = 5

# Percayai header X-Forwarded-* hanya dari proxy ini (isi dengan IP NGINX di produksi).
forwarded_allow_ips = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1")

# Log ke stdout/stderr -> ditangkap journald. xff= memuat IP asli klien di belakang NGINX.
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s xff=%({x-forwarded-for}i)s "%(r)s" %(s)s %(b)s %(L)ss'

limit_request_line = 4094
limit_request_fields = 100
