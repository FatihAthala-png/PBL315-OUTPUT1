"""Model SQLAlchemy (OOP): User dan Product.

Setiap model membungkus data sekaligus perilakunya, mis. User.set_password() /
check_password() dan Product.to_card(). Akses data dilakukan lewat kelas service
di folder services/. Tabel lain (keranjang, pesanan, Midtrans, OTP) masih memakai
db.py (mysql-connector) di database yang sama.
"""
from sqlalchemy import text
from sqlalchemy.dialects import mysql
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

_UINT = mysql.INTEGER(unsigned=True)
_TINY_UINT = mysql.TINYINT(unsigned=True)


def format_rupiah(value):
    """1250000 -> 'Rp 1.250.000'."""
    return "Rp " + f"{value:,}".replace(",", ".")


class DictAccessMixin:
    """Agar objek model tetap bisa dibaca seperti dict: obj["name"], obj.get("name").

    Kode lama (security.py, template, blueprint) memakai g.user["role"]; mixin ini
    menjaga kode itu tetap jalan setelah g.user menjadi objek User.
    """

    def __getitem__(self, key):
        if key in self.__table__.columns:
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key, default=None):
        return getattr(self, key, default) if key in self.__table__.columns else default

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

''' OOP itu menggabungkan data dan fungsi yang berhubungan dalam satu kelas.'''

''' Di sini ada kelas User dan Product. User punya check_password buat ngecek 
sandi dan is_admin buat ngecek apakah dia admin. Product punya to_card buat 
nyiapin data produk yang ditampilin di katalog.'''

'''Tadi waktu login, pengecekan sandinya pakai check_password dari kelas User. 
Waktu admin nambah produk, penyimpanannya lewat ProductService'''
# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(DictAccessMixin, db.Model):
    __tablename__ = "users"

    ROLE_CUSTOMER = "customer"
    ROLE_ADMIN = "admin"

    id = db.Column(_UINT, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    phone = db.Column(db.String(20), nullable=True)
    avatar_path = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("customer", "admin", name="user_role"),
        nullable=False,
        server_default="customer",
    )
    is_active = db.Column(mysql.TINYINT(1), nullable=False, server_default="1")
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    # -- perilaku ----------------------------------------------------------
    def set_password(self, raw_password):
        """Hash kata sandi (scrypt bawaan werkzeug); sandi asli tidak disimpan."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    def __repr__(self):
        return f"<User {self.id} {self.email!r} {self.role}>"


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class Product(DictAccessMixin, db.Model):
    __tablename__ = "products"

    id = db.Column(_UINT, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum("tcg", "figure", name="product_type"), nullable=False)
    sub = db.Column(db.String(50), nullable=False, server_default="")
    brand = db.Column(db.String(50), nullable=False, server_default="")
    rarity = db.Column(db.String(100), nullable=False, server_default="")
    price = db.Column(_UINT, nullable=False)
    discount_percent = db.Column(_TINY_UINT, nullable=True)
    stock = db.Column(_UINT, nullable=False, server_default="0")
    stock_unit = db.Column(db.String(20), nullable=False, server_default="")
    rating = db.Column(db.Numeric(2, 1), nullable=False, server_default="0.0")
    review_count = db.Column(_UINT, nullable=False, server_default="0")
    badge = db.Column(db.String(30), nullable=True)
    is_preorder = db.Column(mysql.TINYINT(1), nullable=False, server_default="0")
    is_active = db.Column(mysql.TINYINT(1), nullable=False, server_default="1")
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        server_onupdate=text("CURRENT_TIMESTAMP"),
    )
    # Ditambahkan lewat migrasi 0002.
    description = db.Column(db.Text, nullable=True)

    # -- perilaku ----------------------------------------------------------
    @property
    def rarity_list(self):
        return [r for r in (self.rarity or "").split(",") if r]

    @property
    def stock_label(self):
        return f"{self.stock} {self.stock_unit}" if self.stock_unit else "Tersedia"

    def to_card(self):
        """Bentuk dict yang dipakai template katalog, beranda, dan detail produk."""
        price = int(self.price)
        discount = self.discount_percent
        card = {
            "id": self.id,
            "name": self.name,
            "image_url": self.image_url,
            "category": self.category,
            "badge": self.badge,
            "stock": self.stock_label,
            "rating": f"{self.rating} ({self.review_count} ulasan)",
            "price": format_rupiah(price),
            "type": self.type,
            "sub": self.sub,
            "brand": self.brand,
            "rarity": self.rarity_list,
            "price_value": price,
            "rating_value": float(self.rating),
            "availability": ["preorder" if self.is_preorder else "ready"],
            "description": (self.description or "").strip(),
        }
        if discount:
            old_price = round(price / (1 - discount / 100), -3)
            card["discount"] = discount
            card["old_price"] = format_rupiah(int(old_price))
            card["availability"].append("promo")
        return card

    def __repr__(self):
        return f"<Product {self.id} {self.name!r}>"
