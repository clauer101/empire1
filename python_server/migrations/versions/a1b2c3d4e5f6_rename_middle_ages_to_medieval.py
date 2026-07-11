"""rename era middle_ages -> medieval in persisted data

Renames the 5th era from "middle_ages"/"MIDDLE_AGES"/"Middle Ages" to
"medieval"/"MEDIEVAL"/"Medieval" everywhere the string is stored in the DB:

- era_firsts.era_key         : 'middle_ages'      -> 'medieval'      (trophy lookup key)
- player_trophies.iid        : 'FIRST_MIDDLE_AGES'-> 'FIRST_MEDIEVAL'(trophy id)
- ai_battle_log.defender_era : 'Middle Ages'      -> 'Medieval'      (display label)
- ai_battle_log.towers_by_era / critters_by_era : JSON key 'Middle Ages' -> 'Medieval'

state.yaml is unaffected (era is stored as a numeric index, not a string).

Revision ID: a1b2c3d4e5f6
Revises: 1595c89ddf0b
Create Date: 2026-07-04

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = '1595c89ddf0b'  # pragma: allowlist secret
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE era_firsts SET era_key = 'medieval' WHERE era_key = 'middle_ages'"
    )
    op.execute(
        "UPDATE player_trophies SET iid = 'FIRST_MEDIEVAL' "
        "WHERE iid = 'FIRST_MIDDLE_AGES'"
    )
    op.execute(
        "UPDATE ai_battle_log SET defender_era = 'Medieval' "
        "WHERE defender_era = 'Middle Ages'"
    )
    op.execute(
        "UPDATE ai_battle_log "
        "SET towers_by_era = REPLACE(towers_by_era, '\"Middle Ages\"', '\"Medieval\"') "
        "WHERE towers_by_era LIKE '%\"Middle Ages\"%'"
    )
    op.execute(
        "UPDATE ai_battle_log "
        "SET critters_by_era = REPLACE(critters_by_era, '\"Middle Ages\"', '\"Medieval\"') "
        "WHERE critters_by_era LIKE '%\"Middle Ages\"%'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE era_firsts SET era_key = 'middle_ages' WHERE era_key = 'medieval'"
    )
    op.execute(
        "UPDATE player_trophies SET iid = 'FIRST_MIDDLE_AGES' "
        "WHERE iid = 'FIRST_MEDIEVAL'"
    )
    op.execute(
        "UPDATE ai_battle_log SET defender_era = 'Middle Ages' "
        "WHERE defender_era = 'Medieval'"
    )
    op.execute(
        "UPDATE ai_battle_log "
        "SET towers_by_era = REPLACE(towers_by_era, '\"Medieval\"', '\"Middle Ages\"') "
        "WHERE towers_by_era LIKE '%\"Medieval\"%'"
    )
    op.execute(
        "UPDATE ai_battle_log "
        "SET critters_by_era = REPLACE(critters_by_era, '\"Medieval\"', '\"Middle Ages\"') "
        "WHERE critters_by_era LIKE '%\"Medieval\"%'"
    )
