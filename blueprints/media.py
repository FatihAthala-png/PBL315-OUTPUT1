"""Blueprint 'media': gambar produk hasil unggahan admin.

Berkas disimpan di luar folder static (UPLOAD_DIR/products) dan dilayani lewat
route ini dengan nama acak, jadi nama dari user tidak pernah dipakai.
"""
import io
import re
import secrets
import warnings

from flask import Blueprint, abort, send_file

from store_config import UPLOAD_DIR

bp = Blueprint("media", __name__)

URL_PREFIX = "/media/produk/"
NAME_RE = re.compile(r"^[0-9a-f]{32}\.jpg$")
IMAGE_SIZE = 800
MAX_PIXELS = 25_000_000  # tolak gambar raksasa (decompression bomb)


class ImageError(Exception):
    """Gambar ditolak. Pesannya aman ditampilkan ke admin."""


def process_product_image(data):
    """Dekode gambar, buang metadata, kecilkan (maks 800 px), simpan ulang JPEG."""
    try:
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError:
        raise ImageError("Fitur unggah gambar belum siap (Pillow belum terpasang).")

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            img = Image.open(io.BytesIO(data))
            if img.format not in ("JPEG", "PNG", "WEBP"):
                raise ImageError("Format gambar tidak didukung. Gunakan JPG, PNG, atau WEBP.")
            img.load()
            img = ImageOps.exif_transpose(img)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                base = Image.new("RGB", img.size, "white")
                base.paste(img, mask=img.getchannel("A"))
                img = base
            else:
                img = img.convert("RGB")
            img.thumbnail((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
    except ImageError:
        raise
    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        OSError,
        ValueError,
        SyntaxError,
    ):
        raise ImageError("Berkas bukan gambar yang valid.")

    out = io.BytesIO()
    img.save(out, "JPEG", quality=88, optimize=True)
    return out.getvalue()


def save_product_image(data):
    """Simpan gambar hasil unggahan; mengembalikan URL-nya (/media/produk/<acak>.jpg)."""
    jpeg = process_product_image(data)
    name = "%s.jpg" % secrets.token_hex(16)
    path = UPLOAD_DIR / "products" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "xb") as fh:
        fh.write(jpeg)
    return URL_PREFIX + name


def delete_product_image(url):
    """Hapus berkas kalau URL-nya gambar unggahan (URL luar diabaikan)."""
    if not url or not url.startswith(URL_PREFIX):
        return
    name = url[len(URL_PREFIX):]
    if NAME_RE.match(name):
        (UPLOAD_DIR / "products" / name).unlink(missing_ok=True)


@bp.route("/media/produk/<name>")
def product_image(name):
    if not NAME_RE.match(name):
        abort(404)
    path = (UPLOAD_DIR / "products" / name).resolve()
    if UPLOAD_DIR.resolve() not in path.parents or not path.is_file():
        abort(404)
    # Nama berkas acak dan isinya tidak pernah berubah, jadi aman di-cache lama.
    response = send_file(path, mimetype="image/jpeg", max_age=31536000)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
