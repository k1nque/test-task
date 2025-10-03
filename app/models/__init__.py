"""Import all models for Alembic."""
from app.models.models import Building, Activity, Organization, OrganizationPhone, organization_activity
from app.db.session import Base

__all__ = [
    "Base",
    "Building",
    "Activity",
    "Organization",
    "OrganizationPhone",
    "organization_activity",
]
