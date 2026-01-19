"""Add locations and play_recommendations tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-19

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create locations table
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_locations_name"), "locations", ["name"], unique=True)

    # Create play_recommendations table
    op.create_table(
        "play_recommendations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time_slot", sa.String(length=20), nullable=False),
        sa.Column("num_guests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "date",
            "time_slot",
            "location_id",
            name="uq_user_date_time_location",
        ),
    )
    op.create_index(
        op.f("ix_play_recommendations_user_id"),
        "play_recommendations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_play_recommendations_location_id"),
        "play_recommendations",
        ["location_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_play_recommendations_date"),
        "play_recommendations",
        ["date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_play_recommendations_date"), table_name="play_recommendations"
    )
    op.drop_index(
        op.f("ix_play_recommendations_location_id"), table_name="play_recommendations"
    )
    op.drop_index(
        op.f("ix_play_recommendations_user_id"), table_name="play_recommendations"
    )
    op.drop_table("play_recommendations")
    op.drop_index(op.f("ix_locations_name"), table_name="locations")
    op.drop_table("locations")
