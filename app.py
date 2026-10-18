import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, g, render_template, request
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from blueprints.admin import bp as admin_bp
from blueprints.admin_laporan import bp as admin_laporan_bp
from blueprints.admin_pengguna import bp as admin_pengguna_bp
from blueprints.admin_produk import bp as admin_produk_bp
from blueprints.auth import bp as auth_bp
from blueprints.cart import bp as cart_bp
from blueprints.media import bp as media_bp
from blueprints.orders import bp as orders_bp
from blueprints.pesanan import bp as pesanan_bp
from blueprints.profil import bp as profil_bp
from blueprints.shop import bp as shop_bp

load_dotenv()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # batas upload 5 MB
)

csrf = CSRFProtect(app)
app.logger.setLevel("INFO")  # catat LOGIN_OK / LOGIN_FAILED

if os.getenv("BEHIND_PROXY", "0") == "1":
    # Percayai header X-Forwarded-* dari NGINX (hanya 1 lapis proxy).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.register_blueprint(shop_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(orders_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(pesanan_bp)
app.register_blueprint(profil_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(admin_produk_bp)
app.register_blueprint(admin_pengguna_bp)
app.register_blueprint(admin_laporan_bp)
app.register_blueprint(media_bp)

# ---------------------------------------------------------------------------
# Halaman error kustom
# ---------------------------------------------------------------------------
ERROR_PAGES = {
    403: ("Akses ditolak", "Kamu tidak punya izin untuk membuka halaman ini."),
    404: ("Halaman tidak ditemukan", "Halaman yang kamu cari tidak ada atau sudah dipindahkan."),
    429: ("Terlalu banyak permintaan", "Kamu terlalu sering mengirim permintaan. Tunggu beberapa saat lalu coba lagi."),
}


@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(429)
def http_error(error):
    if error.code == 429:
        app.logger.warning("RATE_LIMITED path=%s ip=%s", request.path, request.remote_addr)
    title, message = ERROR_PAGES[error.code]
    return render_template("error.html", code=error.code, title=title, message=message, active_page=None), error.code


@app.errorhandler(500)
def server_error(_error):
    # Halaman mandiri (tanpa base.html): tidak boleh bergantung pada database.
    return render_template("error_500.html"), 500


# ---------------------------------------------------------------------------
# Header keamanan (NGINX milik tim jaringan boleh menambah; duplikat tidak masalah)
# ---------------------------------------------------------------------------
@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    # Hanya arahan yang tidak mengganggu Tailwind CDN / skrip inline yang dipakai halaman.
    response.headers.setdefault(
        "Content-Security-Policy",
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'",
    )
    if app.config["SESSION_COOKIE_SECURE"]:  # aktif hanya di belakang HTTPS
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    # Halaman milik user yang login tidak boleh tersimpan di cache (tombol Back setelah logout).
    if g.get("user") and response.mimetype == "text/html":
        response.headers["Cache-Control"] = "private, no-store"
    return response

if __name__ == "__main__":
    app.run()  # produksi: gunicorn app:app
