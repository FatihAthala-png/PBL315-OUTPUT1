"""Blueprint 'auth': registrasi, login, logout + pemuatan user dari session."""
import re

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import generate_password_hash

import otp_flow
import ratelimit
from security import safe_next
from services import EmailAlreadyUsed, UserService

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _landing_url(user, next_url):
    """Tujuan setelah login: tujuan `next` bila ada; admin langsung ke Panel Admin."""
    if next_url:
        return next_url
    return url_for("admin.dashboard") if user.is_admin else url_for("shop.home")


def password_valid(password):
    return bool(
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


def _safe(value, limit=100):
    """Bersihkan input sebelum masuk log (cegah log injection)."""
    return re.sub(r"[^\w@.+\-]", "?", value or "")[:limit]


# ---------------------------------------------------------------------------
# User yang sedang login (dimuat dari session untuk setiap request)
# ---------------------------------------------------------------------------
@bp.before_app_request
def load_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id is None or request.endpoint == "static":
        return
    user = UserService.get_by_id(user_id)
    if user is None or not user.is_active:
        session.clear()
        return
    g.user = user


@bp.app_context_processor
def inject_user():
    return {"current_user": g.get("user")}


# ---------------------------------------------------------------------------
# Login & logout
# ---------------------------------------------------------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next(request.values.get("next"))
    if g.user:
        return redirect(_landing_url(g.user, next_url))

    error = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Kunci sementara setelah terlalu banyak percobaan gagal (per email dan per IP).
        if ratelimit.blocked("login-email", email, 5, 600) or ratelimit.blocked(
            "login-ip", request.remote_addr, 20, 600
        ):
            current_app.logger.warning("RATE_LIMITED name=login ip=%s", request.remote_addr)
            error = "Terlalu banyak percobaan gagal. Coba lagi dalam beberapa menit."
            return render_template("login.html", error=error, email=email, next=next_url), 429

        user = None
        if EMAIL_RE.match(email) and len(email) <= 150:
            user = UserService.verify_credentials(email, password)
        else:
            UserService.verify_credentials(None, password)  # waktu proses tetap sama

        if user is None:
            error = "Email atau kata sandi salah."
            ratelimit.record("login-email", email, 600)
            ratelimit.record("login-ip", request.remote_addr, 600)
            current_app.logger.warning(
                "LOGIN_FAILED email=%s ip=%s", _safe(email), request.remote_addr
            )
        elif not user.is_active:
            error = "Akun kamu dinonaktifkan. Hubungi admin."
            current_app.logger.warning(
                "LOGIN_BLOCKED user_id=%s ip=%s", user.id, request.remote_addr
            )
        else:
            ratelimit.clear("login-email", email)
            session.clear()  # session baru (cegah session fixation)
            session["user_id"] = user.id
            session.permanent = True
            current_app.logger.info(
                "LOGIN_OK user_id=%s ip=%s", user.id, request.remote_addr
            )
            return redirect(_landing_url(user, next_url))

    return render_template("login.html", error=error, email=email, next=next_url)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("shop.home"))


# ---------------------------------------------------------------------------
# Registrasi
# ---------------------------------------------------------------------------
@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("shop.home"))

    error = None
    if request.method == "POST":
        if ratelimit.hit("register", request.remote_addr, 10, 3600):
            current_app.logger.warning("RATE_LIMITED name=register ip=%s", request.remote_addr)
            return render_template(
                "register.html",
                error="Terlalu banyak pendaftaran dari alamat ini. Coba lagi nanti.",
                form=request.form,
            ), 429
        email = request.form.get("email", "").strip().lower()
        nama = request.form.get("nama", "").strip()
        password = request.form.get("password", "")
        konfirmasi = request.form.get("konfirmasi", "")
        setuju = request.form.get("setuju")

        if not EMAIL_RE.match(email) or len(email) > 150:
            error = "Format email tidak valid."
        elif not nama:
            error = "Nama lengkap wajib diisi."
        elif len(nama) > 100:
            error = "Nama terlalu panjang (maksimal 100 karakter)."
        elif not password_valid(password):
            error = "Kata sandi belum memenuhi syarat."
        elif password != konfirmasi:
            error = "Konfirmasi kata sandi tidak sama."
        elif not setuju:
            error = "Kamu harus menyetujui Syarat & Ketentuan."
        elif UserService.email_exists(email):
            error = "Email sudah terdaftar."
        elif otp_flow.enabled():
            try:
                otp_flow.begin(email, nama, generate_password_hash(password))
            except otp_flow.OtpError as exc:
                error = str(exc)
            else:
                session["otp_email"] = email
                return redirect(url_for("verifikasi.page"))
        else:
            try:
                UserService.register(nama, email, password)
            except EmailAlreadyUsed:
                error = "Email sudah terdaftar."  # balapan dua pendaftaran
            else:
                flash("Pendaftaran berhasil. Silakan masuk.")
                return redirect(url_for("auth.login"))

    return render_template("register.html", error=error, form=request.form)
