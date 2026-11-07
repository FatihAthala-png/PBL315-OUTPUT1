"""tambah kolom description pada products

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-27

Contoh migrasi untuk demo: menambah kolom deskripsi produk.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _has_column(table, column):
    cols = [c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)]
    return column in cols


def upgrade():
    if not _has_column("products", "description"):
        op.add_column("products", sa.Column("description", sa.Text(), nullable=True))


def downgrade():
    if _has_column("products", "description"):
        op.drop_column("products", "description")
