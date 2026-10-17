"""Isi database: 12 produk dari products.json + akun admin pertama.

Jalankan dari folder proyek:  python seed.py   (aman diulang)
"""
import json
import os
import re
from html import unescape
from pathlib import Path

from werkzeug.security import generate_password_hash

import db

BASE_DIR = Path(__file__).parent

FIGURE_IDS = {4, 5, 8, 11}
PREORDER_IDS = {5, 6}
DISCOUNTS = {1: 13, 3: 20, 4: 10, 6: 15, 8: 20, 11: 12}
META = {
    1: {"sub": "booster-pack", "brand": "pokemon-company"},
    2: {"sub": "single-card", "brand": "pokemon-company", "rarity": ["sar", "psa10"]},
    3: {"sub": "etb", "brand": "pokemon-company"},
    4: {"sub": "scale-figure", "brand": "kotobukiya"},
    5: {"sub": "nendoroid", "brand": "good-smile"},
    6: {"sub": "booster-box", "brand": "pokemon-company"},
    7: {"sub": "single-card", "brand": "pokemon-company", "rarity": ["sar", "raw-mint"]},
    8: {"sub": "shfiguarts", "brand": "bandai"},
    9: {"sub": "single-card", "brand": "pokemon-company", "rarity": ["ur", "raw-mint"]},
    10: {"sub": "booster-pack", "brand": "pokemon-company"},
    11: {"sub": "nendoroid", "brand": "good-smile"},
    12: {"sub": "starter-acc", "brand": "ultra-pro"},
}


def parse_stock(text):
    """'18 pack' -> (18, 'pack'); 'Tersedia' -> (10, '')."""
    parts = text.split(None, 1)
    if parts and parts[0].isdigit():
        return int(parts[0]), (parts[1] if len(parts) > 1 else "")
    return 10, ""


def seed_products():
    with (BASE_DIR / "data" / "products.json").open(encoding="utf-8") as f:
        raw = json.load(f)

    with db.transaction() as cur:
        for item in raw:
            p = {k: unescape(v) if isinstance(v, str) else v for k, v in item.items()}
            pid = p["id"]
            meta = META.get(pid, {})
            stock, unit = parse_stock(p["stock"])
            price = int("".join(ch for ch in p["price"] if ch.isdigit()))
            rating = float(p["rating"].split()[0])
            reviews = re.search(r"\((\d+)", p["rating"])
            cur.execute(
                """
                INSERT INTO products
                  (id, name, image_url, category, type, sub, brand, rarity,
                   price, discount_percent, stock, stock_unit,
                   rating, review_count, badge, is_preorder)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  name=VALUES(name), image_url=VALUES(image_url),
                  category=VALUES(category), type=VALUES(type),
                  sub=VALUES(sub), brand=VALUES(brand), rarity=VALUES(rarity),
                  price=VALUES(price), discount_percent=VALUES(discount_percent),
                  stock=VALUES(stock), stock_unit=VALUES(stock_unit),
                  rating=VALUES(rating), review_count=VALUES(review_count),
                  badge=VALUES(badge), is_preorder=VALUES(is_preorder)
                """,
                (
                    pid, p["name"], p["image_url"], p["category"],
                    "figure" if pid in FIGURE_IDS else "tcg",
                    meta.get("sub", ""), meta.get("brand", ""),
                    ",".join(meta.get("rarity", [])),
                    price, DISCOUNTS.get(pid), stock, unit,
                    rating, int(reviews.group(1)) if reviews else 0,
                    p.get("badge"), 1 if pid in PREORDER_IDS else 0,
                ),
            )
    print("Produk berhasil dimasukkan.")


def seed_admin():
    email = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    if not email or not password:
        print("ADMIN_EMAIL / ADMIN_PASSWORD belum diisi di .env, admin dilewati.")
        return
    if db.query_one("SELECT id FROM users WHERE email = %s", (email,)):
        print("Admin sudah ada, dilewati.")
        return
    db.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s,%s,%s,'admin')",
        ("Administrator", email, generate_password_hash(password)),
    )
    print(f"Admin dibuat: {email}")


if __name__ == "__main__":
    seed_products()
    seed_admin()
