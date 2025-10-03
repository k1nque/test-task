"""Database models."""
from datetime import datetime
from typing import List, Optional

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Table,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped

from app.db.session import Base


# Association table for many-to-many relationship between Organization and Activity
organization_activity = Table(
    "organization_activity",
    Base.metadata,
    Column("organization_id", Integer, ForeignKey("organizations.id", ondelete="CASCADE"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True),
)


class Building(Base):
    """Building model representing a physical location."""
    
    __tablename__ = "buildings"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False, index=True)
    # Store geographic coordinates as a PostGIS POINT
    coordinates = Column(
        Geometry(geometry_type='POINT', srid=4326),
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to organizations
    organizations: Mapped[List["Organization"]] = relationship(
        "Organization",
        back_populates="building",
        cascade="all, delete-orphan"
    )
    
    @property
    def latitude(self) -> Optional[float]:
        """Return latitude extracted from PostGIS coordinates."""
        if not self.coordinates:
            return None
        point = to_shape(self.coordinates)
        return float(point.y)

    @property
    def longitude(self) -> Optional[float]:
        """Return longitude extracted from PostGIS coordinates."""
        if not self.coordinates:
            return None
        point = to_shape(self.coordinates)
        return float(point.x)

    def __repr__(self):
        return f"<Building(id={self.id}, address='{self.address}')>"


class Activity(Base):
    """Activity model representing business activity categories in a tree structure."""
    
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True, unique=True)
    parent_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), nullable=True, index=True)
    level = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referential relationship for tree structure
    parent: Mapped[Optional["Activity"]] = relationship(
        "Activity",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["Activity"]] = relationship(
        "Activity",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # Many-to-many relationship with organizations
    organizations: Mapped[List["Organization"]] = relationship(
        "Organization",
        secondary=organization_activity,
        back_populates="activities"
    )
    
    # Constraint to limit nesting level to 3
    __table_args__ = (
        CheckConstraint("level >= 1 AND level <= 3", name="check_activity_level"),
    )
    
    def __repr__(self):
        return f"<Activity(id={self.id}, name='{self.name}', level={self.level})>"


# Association table for organization phone numbers
class OrganizationPhone(Base):
    """Organization phone numbers."""
    
    __tablename__ = "organization_phones"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<OrganizationPhone(id={self.id}, phone='{self.phone_number}')>"


class Organization(Base):
    """Organization model representing a company or entity."""
    
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="organizations")
    
    phone_numbers: Mapped[List["OrganizationPhone"]] = relationship(
        "OrganizationPhone",
        cascade="all, delete-orphan",
        lazy="joined"
    )
    
    activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        secondary=organization_activity,
        back_populates="organizations"
    )
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"
