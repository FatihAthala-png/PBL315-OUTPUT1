"""baseline: adopsi skema yang sudah ada (schema.sql)

Revision ID: 0001
Revises:
Create Date: 2026-10-27

Tabel dibuat lebih dulu lewat schema.sql. Migrasi ini TIDAK membuat tabel;
ia hanya menandai titik awal riwayat dan memastikan skema dasar sudah ada.
"""
'''
Migration itu cara kami mengelola perubahan struktur database lewat file 
versi, jadi nggak diubah manual lewat SQL.

Di sini ada dua revisi. 0001 itu baseline, mengadopsi tabel yang sudah 
ada dari schema.sql. 0002 nambah kolom description di tabel products
'''

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "products" not in tables or "users" not in tables:
        raise RuntimeError(
            "Tabel dasar belum ada. Jalankan dulu:  mysql -u root -p < schema.sql"
        )


def downgrade():
    # Titik awal: tidak ada yang dibatalkan (tabel dasar milik schema.sql).
    pass
