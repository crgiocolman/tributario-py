"""add_deleted_at_to_ingresos

Revision ID: a4114aa5f457
Revises: e90319e232bb
Create Date: 2026-05-09 17:47:32.707353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a4114aa5f457'
down_revision: Union[str, None] = 'e90319e232bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ingresos', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('ingresos', 'deleted_at')
