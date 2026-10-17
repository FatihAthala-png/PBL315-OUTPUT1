"""Koneksi MySQL (connection pool) + helper query."""
import os
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling

try:  # opsional: baca konfigurasi dari file .env
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="kamistore",
            pool_size=5,
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "kamistore"),
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
        )
    return _pool


@contextmanager
def _cursor():
    conn = _get_pool().get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        yield cur, conn
    finally:
        cur.close()
        conn.close()


def query_all(sql, params=()):
    """SELECT banyak baris -> list of dict."""
    with _cursor() as (cur, _):
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(sql, params=()):
    """SELECT satu baris -> dict atau None."""
    with _cursor() as (cur, _):
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql, params=()):
    """INSERT/UPDATE/DELETE tunggal -> id baris terakhir."""
    with _cursor() as (cur, conn):
        cur.execute(sql, params)
        conn.commit()
        return cur.lastrowid


@contextmanager
def transaction():
    """Beberapa query dalam satu transaksi (commit semua atau batal semua).

    with db.transaction() as cur:
        cur.execute(...)
        cur.execute(...)
    """
    with _cursor() as (cur, conn):
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise