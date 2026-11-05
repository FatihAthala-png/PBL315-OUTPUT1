"""ProductService: seluruh operasi CRUD produk lewat model Product (SQLAlchemy)."""
from sqlalchemy import func, or_, text
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Product


def escape_like(value):
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class ProductService:
    """Kumpulan operasi produk. Semua method bersifat statis (tanpa state)."""

    # Kolom yang boleh diisi dari form admin.
    FIELDS = (
        "name", "image_url", "category", "type", "sub", "brand", "rarity", "price",
        "discount_percent", "stock", "stock_unit", "badge", "is_preorder", "description",
    )

    # ---- baca (toko) ------------------------------------------------------
    @staticmethod
    def list_active(product_type=None):
        query = Product.query.filter(Product.is_active == 1)
        if product_type:
            query = query.filter(Product.type == product_type)
        return query.order_by(Product.id).all()

    @staticmethod
    def get_active(product_id):
        return Product.query.filter(Product.id == product_id, Product.is_active == 1).first()

    # ---- baca (admin) -----------------------------------------------------
    @staticmethod
    def get(product_id):
        return db.session.get(Product, product_id)

    @staticmethod
    def list_admin(status=None, q=None, page=1, per_page=20):
        """-> (list[Product], total). status: 'aktif' | 'nonaktif' | None."""
        query = Product.query
        if status == "aktif":
            query = query.filter(Product.is_active == 1)
        elif status == "nonaktif":
            query = query.filter(Product.is_active == 0)
        if q:
            like = "%" + escape_like(q) + "%"
            query = query.filter(
                or_(Product.name.like(like, escape="\\"), Product.category.like(like, escape="\\"))
            )
        total = query.with_entities(func.count(Product.id)).scalar() or 0
        rows = (
            query.order_by(Product.id.desc()).limit(per_page).offset((page - 1) * per_page).all()
        )
        return rows, int(total)

    @staticmethod
    def low_stock(limit=8, threshold=3):
        """Produk aktif dengan stok menipis (untuk dashboard admin)."""
        rows = (
            Product.query.filter(Product.is_active == 1, Product.stock <= threshold)
            .order_by(Product.stock, Product.id)
            .limit(limit)
            .all()
        )
        return [{"id": p.id, "name": p.name, "stock": p.stock} for p in rows]

    # ---- tulis ------------------------------------------------------------
    @staticmethod
    def save(product_id, data):
        """Tambah (product_id None) atau ubah produk. -> id produk."""
        if product_id is None:
            product = Product()
            db.session.add(product)
        else:
            product = db.session.get(Product, product_id)
            if product is None:
                raise LookupError("Produk tidak ditemukan")
        for field in ProductService.FIELDS:
            setattr(product, field, data[field])
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return product.id

    @staticmethod
    def set_active(product_id, active):
        product = db.session.get(Product, product_id)
        if product is None:
            return False
        product.is_active = 1 if active else 0
        db.session.commit()
        return True

    @staticmethod
    def delete(product_id):
        """Hapus permanen. -> 'deleted' | 'in_use' (pernah dipesan) | 'not_found'."""
        product = db.session.get(Product, product_id)
        if product is None:
            return "not_found"
        used = db.session.execute(
            text("SELECT COUNT(*) FROM order_items WHERE product_id = :pid"), {"pid": product_id}
        ).scalar()
        if int(used or 0) > 0:
            return "in_use"
        try:
            db.session.delete(product)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return "in_use"
        return "deleted"
