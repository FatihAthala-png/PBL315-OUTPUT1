"""Blueprint 'profil': data diri, ganti kata sandi, foto avatar."""
import io
import re
import secrets
import warnings

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import db
from blueprints.auth import password_valid
import ratelimit
from security import login_required
from store_config import UPLOAD_DIR

bp = Blueprint("profil", __name__)

PHONE_RE = re.compile(r"^[0-9+\-\s]{8,20}$")
MAX_AVATAR_BYTES = 5 * 1024 * 1024
AVATAR_SIZE = 256
MAX_PIXELS = 25_000_000  # tolak gambar raksasa (decompression bomb)


class AvatarError(Exception):
    """Berkas avatar ditolak. Pesannya aman ditampilkan ke user."""


def process_avatar(data):
    """Buka gambar, buang metadata (EXIF/GPS), potong persegi 256x256, simpan ulang JPEG.

    Gambar benar-benar didekode di sini, jadi berkas yang bukan gambar (atau
    gambar yang disusupi data lain) ditolak, dan hasilnya selalu JPEG bersih.
    """
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError:
        raise AvatarError("Fitur foto profil belum siap (Pillow belum terpasang).")

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(data))
            if img.format not in ("JPEG", "PNG", "WEBP"):
                raise AvatarError("Format gambar tidak didukung. Gunakan JPG, PNG, atau WEBP.")
            img.load()
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                base = Image.new("RGB", img.size, "white")
                base.paste(img, mask=img.getchannel("A"))
                img = base
            else:
                img = img.convert("RGB")
            img = ImageOps.fit(img, (AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)
    except AvatarError:
        raise
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        ValueError,
        SyntaxError,
    ):
        raise AvatarError("Berkas bukan gambar yang valid.")

    out = io.BytesIO()
    img.save(out, "JPEG", quality=88, optimize=True)
    return out.getvalue()


def _remove_file(rel_path):
    if not rel_path:
        return
    path = (UPLOAD_DIR / rel_path).resolve()
    if UPLOAD_DIR.resolve() in path.parents:
        path.unlink(missing_ok=True)


def _back():
    return redirect(url_for("profil.view"))


@bp.route("/profil")
@login_required
def view():
    user = db.query_one(
        "SELECT id, name, email, phone, avatar_path, created_at FROM users WHERE id = %s",
        (g.user["id"],),
    )
    return render_template("profil.html", user=user, active_page="profil")


@bp.route("/profil/data", methods=["POST"])
@login_required
def update_data():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    if not name or len(name) > 100:
        flash("Nama wajib diisi (maksimal 100 karakter).", "error")
    elif phone and not PHONE_RE.match(phone):
        flash("Nomor telepon tidak valid (8-20 digit).", "error")
    else:
        db.execute(
            "UPDATE users SET name = %s, phone = %s WHERE id = %s",
            (name, phone or None, g.user["id"]),
        )
        flash("Data diri diperbarui.", "success")
    return _back()


@bp.route("/profil/sandi", methods=["POST"])
@login_required
def change_password():
    current = request.form.get("current", "")
    new = request.form.get("new", "")
    confirm = request.form.get("confirm", "")

    if ratelimit.blocked("pwchange", g.user["id"], 5, 600):
        flash("Terlalu banyak percobaan. Coba lagi dalam beberapa menit.", "error")
        return _back()

    row = db.query_one("SELECT password_hash FROM users WHERE id = %s", (g.user["id"],))
    if not check_password_hash(row["password_hash"], current):
        ratelimit.record("pwchange", g.user["id"], 600)
        current_app.logger.warning(
            "PASSWORD_CHANGE_FAILED user_id=%s ip=%s", g.user["id"], request.remote_addr
        )
        flash("Kata sandi saat ini salah.", "error")
    elif not password_valid(new):
        flash("Kata sandi baru belum memenuhi syarat (min. 8 karakter, huruf besar, huruf kecil, angka, dan simbol).", "error")
    elif new != confirm:
        flash("Konfirmasi kata sandi baru tidak sama.", "error")
    elif new == current:
        flash("Kata sandi baru harus berbeda dari yang lama.", "error")
    else:
        db.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (generate_password_hash(new), g.user["id"]),
        )
        current_app.logger.info(
            "PASSWORD_CHANGED user_id=%s ip=%s", g.user["id"], request.remote_addr
        )
        flash("Kata sandi diperbarui.", "success")
    return _back()


@bp.route("/profil/avatar", methods=["POST"])
@login_required
def upload_avatar():
    upload = request.files.get("avatar")
    if upload is None or not upload.filename:
        flash("Pilih berkas gambar.", "error")
        return _back()
    data = upload.read(MAX_AVATAR_BYTES + 1)
    if not data:
        flash("Berkas kosong.", "error")
        return _back()
    if len(data) > MAX_AVATAR_BYTES:
        flash("Berkas terlalu besar (maksimal 5 MB).", "error")
        return _back()

    try:
        jpeg = process_avatar(data)
    except AvatarError as exc:
        flash(str(exc), "error")
        return _back()

    rel_path = "avatars/%s.jpg" % secrets.token_hex(16)
    path = UPLOAD_DIR / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as fh:
        fh.write(jpeg)

    old = db.query_one("SELECT avatar_path FROM users WHERE id = %s", (g.user["id"],))
    db.execute("UPDATE users SET avatar_path = %s WHERE id = %s", (rel_path, g.user["id"]))
    _remove_file(old["avatar_path"] if old else None)
    flash("Foto profil diperbarui.", "success")
    return _back()


@bp.route("/profil/avatar/hapus", methods=["POST"])
@login_required
def delete_avatar():
    old = db.query_one("SELECT avatar_path FROM users WHERE id = %s", (g.user["id"],))
    db.execute("UPDATE users SET avatar_path = NULL WHERE id = %s", (g.user["id"],))
    _remove_file(old["avatar_path"] if old else None)
    flash("Foto profil dihapus.", "success")
    return _back()


@bp.route("/avatar/<int:user_id>")
def avatar(user_id):
    """Foto profil. URL memuat ?v=<nama berkas>, jadi aman di-cache lama."""
    row = db.query_one(
        "SELECT avatar_path FROM users WHERE id = %s AND is_active = 1", (user_id,)
    )
    if row is None or not row["avatar_path"]:
        abort(404)
    path = (UPLOAD_DIR / row["avatar_path"]).resolve()
    if UPLOAD_DIR.resolve() not in path.parents or not path.is_file():
        abort(404)
    response = send_file(path, mimetype="image/jpeg", max_age=86400)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
