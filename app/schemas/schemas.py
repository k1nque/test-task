"""Pydantic schemas for API validation."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# Building schemas
class BuildingBase(BaseModel):
    """Base building schema."""
    address: str = Field(..., description="Building address")
    latitude: float = Field(..., description="Latitude coordinate", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude coordinate", ge=-180, le=180)


class BuildingCreate(BuildingBase):
    """Schema for creating a building."""
    pass


class Building(BuildingBase):
    """Schema for building response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Activity schemas
class ActivityBase(BaseModel):
    """Base activity schema."""
    name: str = Field(..., description="Activity name")
    parent_id: Optional[int] = Field(None, description="Parent activity ID")


class ActivityCreate(ActivityBase):
    """Schema for creating an activity."""
    pass


class Activity(ActivityBase):
    """Schema for activity response."""
    id: int
    level: int = Field(..., description="Nesting level (1-3)")
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ActivityWithChildren(Activity):
    """Schema for activity with children."""
    children: List["ActivityWithChildren"] = Field(default_factory=list, description="Child activities")
    
    model_config = ConfigDict(from_attributes=True)


# Organization schemas
class OrganizationBase(BaseModel):
    """Base organization schema."""
    name: str = Field(..., description="Organization name")
    building_id: int = Field(..., description="Building ID where organization is located")


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization."""
    phone_numbers: List[str] = Field(..., description="List of phone numbers")
    activity_ids: List[int] = Field(..., description="List of activity IDs")


class OrganizationPhone(BaseModel):
    """Schema for organization phone number."""
    phone_number: str
    
    model_config = ConfigDict(from_attributes=True)


class Organization(OrganizationBase):
    """Schema for organization response."""
    id: int
    phone_numbers: List[OrganizationPhone] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)
    building: Building
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationList(BaseModel):
    """Schema for organization list response."""
    organizations: List[Organization]
    total: int


# Search schemas
class OrganizationSearch(BaseModel):
    """Schema for organization search parameters."""
    name: Optional[str] = Field(None, description="Search by organization name")
    building_id: Optional[int] = Field(None, description="Filter by building ID")
    activity_id: Optional[int] = Field(None, description="Filter by activity ID (includes children)")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class LocationSearch(BaseModel):
    """Schema for location-based search."""
    latitude: float = Field(..., description="Center point latitude", ge=-90, le=90)
    longitude: float = Field(..., description="Center point longitude", ge=-180, le=180)
    radius_meters: Optional[float] = Field(None, description="Search radius in meters", gt=0)
    min_latitude: Optional[float] = Field(None, description="Minimum latitude for bounding box", ge=-90, le=90)
    max_latitude: Optional[float] = Field(None, description="Maximum latitude for bounding box", ge=-90, le=90)
    min_longitude: Optional[float] = Field(None, description="Minimum longitude for bounding box", ge=-180, le=180)
    max_longitude: Optional[float] = Field(None, description="Maximum longitude for bounding box", ge=-180, le=180)
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class BuildingList(BaseModel):
    """Schema for building list response."""
    buildings: List[Building]
    total: int


class ActivityTree(BaseModel):
    """Schema for activity tree response."""
    activities: List[ActivityWithChildren]


# Resolve forward references
ActivityWithChildren.model_rebuild()
