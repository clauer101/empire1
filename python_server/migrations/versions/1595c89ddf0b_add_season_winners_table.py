"""add season_winners table

Revision ID: 1595c89ddf0b
Revises: 977b61c84d43
Create Date: 2026-06-29 15:44:02.009614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1595c89ddf0b'  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = '977b61c84d43'  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'season_winners',
        sa.Column('id',            sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('season_number', sa.Integer, nullable=False),
        sa.Column('season_title',  sa.Text,    nullable=False, server_default=''),
        sa.Column('place',         sa.Integer, nullable=False),  # 1, 2, or 3
        sa.Column('empire_uid',    sa.Integer, nullable=False),
        sa.Column('empire_name',   sa.Text,    nullable=False),
        sa.Column('culture',       sa.Float,   nullable=False),
        sa.Column('recorded_at',   sa.Text,    nullable=False),  # ISO-8601 UTC
    )
    op.create_index('ix_season_winners_season', 'season_winners', ['season_number'])


def downgrade() -> None:
    op.drop_index('ix_season_winners_season', 'season_winners')
    op.drop_table('season_winners')
