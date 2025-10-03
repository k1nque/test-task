"""Create initial tables"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply the initial schema."""
    # Enable PostGIS extension to support geometry columns
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Buildings table stores physical locations
    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("coordinates", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_buildings_id"), "buildings", ["id"], unique=False)
    op.create_index(op.f("ix_buildings_address"), "buildings", ["address"], unique=False)
    op.execute("DROP INDEX IF EXISTS idx_buildings_coordinates")
    op.execute("CREATE INDEX idx_buildings_coordinates ON buildings USING gist (coordinates)")

    # Activities table represents hierarchical activity categories
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("name", name="uq_activities_name"),
        sa.CheckConstraint("level >= 1 AND level <= 3", name="check_activity_level"),
    )
    op.create_index(op.f("ix_activities_id"), "activities", ["id"], unique=False)
    op.create_index(op.f("ix_activities_name"), "activities", ["name"], unique=True)
    op.create_index(op.f("ix_activities_parent_id"), "activities", ["parent_id"], unique=False)

    # Organizations table references buildings and stores metadata
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "building_id",
            sa.Integer(),
            sa.ForeignKey("buildings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"], unique=False)
    op.create_index(op.f("ix_organizations_name"), "organizations", ["name"], unique=False)
    op.create_index(op.f("ix_organizations_building_id"), "organizations", ["building_id"], unique=False)

    # Organization phone numbers
    op.create_table(
        "organization_phones",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone_number", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_organization_phones_id"), "organization_phones", ["id"], unique=False)
    op.create_index(
        op.f("ix_organization_phones_organization_id"),
        "organization_phones",
        ["organization_id"],
        unique=False,
    )

    # Association table for many-to-many organization/activity relationship
    op.create_table(
        "organization_activity",
        sa.Column(
            "organization_id",
            sa.Integer(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "activity_id",
            sa.Integer(),
            sa.ForeignKey("activities.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Rollback the initial schema."""
    op.drop_table("organization_activity")

    op.drop_index(op.f("ix_organization_phones_organization_id"), table_name="organization_phones")
    op.drop_index(op.f("ix_organization_phones_id"), table_name="organization_phones")
    op.drop_table("organization_phones")

    op.drop_index(op.f("ix_organizations_building_id"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_name"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_table("organizations")

    op.drop_index(op.f("ix_activities_parent_id"), table_name="activities")
    op.drop_index(op.f("ix_activities_name"), table_name="activities")
    op.drop_index(op.f("ix_activities_id"), table_name="activities")
    op.drop_table("activities")

    op.execute("DROP INDEX IF EXISTS idx_buildings_coordinates")
    op.drop_index(op.f("ix_buildings_address"), table_name="buildings")
    op.drop_index(op.f("ix_buildings_id"), table_name="buildings")
    op.drop_table("buildings")

    op.execute("DROP EXTENSION IF EXISTS postgis")
