"""API endpoints for organizations."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from geoalchemy2.functions import ST_DWithin
from geoalchemy2.elements import WKTElement

from app.db.session import get_db
from app.core.security import verify_api_key
from app.models.models import Organization as OrganizationModel, Building, Activity, OrganizationPhone
from app.schemas import schemas

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_activity_descendants(db: Session, activity_id: int) -> List[int]:
    """
    Get all descendant activities recursively.
    
    Args:
        db: Database session
        activity_id: Parent activity ID
        
    Returns:
        List of activity IDs including the parent
    """
    activity_ids = [activity_id]
    
    # Get direct children
    children = db.query(Activity).filter(Activity.parent_id == activity_id).all()
    
    # Recursively get descendants
    for child in children:
        activity_ids.extend(get_activity_descendants(db, child.id))
    
    return activity_ids


@router.get(
    "/by-building/{building_id}",
    response_model=schemas.OrganizationList,
    summary="Get organizations by building",
    description="Get all organizations located in a specific building"
)
async def get_organizations_by_building(
    building_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all organizations in a specific building."""
    # Verify building exists
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    query = (
        db.query(OrganizationModel)
        .filter(OrganizationModel.building_id == building_id)
        .options(
            joinedload(OrganizationModel.building),
            joinedload(OrganizationModel.phone_numbers),
            joinedload(OrganizationModel.activities)
        )
    )
    
    total = query.count()
    organizations = query.offset(offset).limit(limit).all()
    
    return schemas.OrganizationList(
        organizations=organizations,
        total=total
    )


@router.get(
    "/by-activity/{activity_id}",
    response_model=schemas.OrganizationList,
    summary="Get organizations by activity",
    description="Get all organizations related to a specific activity (includes child activities)"
)
async def get_organizations_by_activity(
    activity_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get all organizations related to a specific activity."""
    # Verify activity exists
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Get all descendant activity IDs
    activity_ids = get_activity_descendants(db, activity_id)
    
    query = (
        db.query(OrganizationModel)
        .join(OrganizationModel.activities)
        .filter(Activity.id.in_(activity_ids))
        .options(
            joinedload(OrganizationModel.building),
            joinedload(OrganizationModel.phone_numbers),
            joinedload(OrganizationModel.activities)
        )
        .distinct()
    )
    
    total = query.count()
    organizations = query.offset(offset).limit(limit).all()
    
    return schemas.OrganizationList(
        organizations=organizations,
        total=total
    )


@router.get(
    "/{organization_id}",
    response_model=schemas.Organization,
    summary="Get organization by ID",
    description="Get detailed information about a specific organization"
)
async def get_organization(
    organization_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get organization by ID."""
    organization = (
        db.query(OrganizationModel)
        .filter(OrganizationModel.id == organization_id)
        .options(
            joinedload(OrganizationModel.building),
            joinedload(OrganizationModel.phone_numbers),
            joinedload(OrganizationModel.activities)
        )
        .first()
    )
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return organization


@router.get(
    "/search/by-name",
    response_model=schemas.OrganizationList,
    summary="Search organizations by name",
    description="Search organizations by name (case-insensitive partial match)"
)
async def search_organizations_by_name(
    name: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Search organizations by name."""
    query = (
        db.query(OrganizationModel)
        .filter(OrganizationModel.name.ilike(f"%{name}%"))
        .options(
            joinedload(OrganizationModel.building),
            joinedload(OrganizationModel.phone_numbers),
            joinedload(OrganizationModel.activities)
        )
    )
    
    total = query.count()
    organizations = query.offset(offset).limit(limit).all()
    
    return schemas.OrganizationList(
        organizations=organizations,
        total=total
    )


@router.post(
    "/search/by-location",
    response_model=schemas.OrganizationList,
    summary="Search organizations by location",
    description="Search organizations within a radius or bounding box"
)
async def search_organizations_by_location(
    search: schemas.LocationSearch,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Search organizations by geographic location."""
    point = WKTElement(f"POINT({search.longitude} {search.latitude})", srid=4326)
    
    query = (
        db.query(OrganizationModel)
        .join(OrganizationModel.building)
        .options(
            joinedload(OrganizationModel.building),
            joinedload(OrganizationModel.phone_numbers),
            joinedload(OrganizationModel.activities)
        )
    )
    
    if search.radius_meters:
        # Search within radius
        query = query.filter(
            ST_DWithin(
                Building.coordinates,
                point,
                search.radius_meters,
                use_spheroid=True
            )
        )
    elif all([
        search.min_latitude is not None,
        search.max_latitude is not None,
        search.min_longitude is not None,
        search.max_longitude is not None
    ]):
        # Search within bounding box
        bbox = f"POLYGON(({search.min_longitude} {search.min_latitude}, " \
               f"{search.max_longitude} {search.min_latitude}, " \
               f"{search.max_longitude} {search.max_latitude}, " \
               f"{search.min_longitude} {search.max_latitude}, " \
               f"{search.min_longitude} {search.min_latitude}))"
        bbox_geom = WKTElement(bbox, srid=4326)
        
        query = query.filter(
            func.ST_Within(Building.coordinates, bbox_geom)
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Either radius_meters or all bounding box parameters must be provided"
        )
    
    total = query.count()
    organizations = query.offset(search.offset).limit(search.limit).all()
    
    return schemas.OrganizationList(
        organizations=organizations,
        total=total
    )


@router.get(
    "/",
    response_model=schemas.OrganizationList,
    summary="List all organizations",
    description="Get a paginated list of all organizations"
)
async def list_organizations(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """List all organizations."""
    query = (
        db.query(OrganizationModel)
        .options(
            joinedload(OrganizationModel.building),
            joinedload(OrganizationModel.phone_numbers),
            joinedload(OrganizationModel.activities)
        )
    )
    
    total = query.count()
    organizations = query.offset(offset).limit(limit).all()
    
    return schemas.OrganizationList(
        organizations=organizations,
        total=total
    )


@router.post(
    "/",
    response_model=schemas.Organization,
    status_code=201,
    summary="Create a new organization",
    description="Create a new organization with phone numbers and activities"
)
async def create_organization(
    organization: schemas.OrganizationCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    # Verify building exists
    building = db.query(Building).filter(Building.id == organization.building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail=f"Building with id {organization.building_id} not found")
    
    # Verify all activities exist
    if organization.activity_ids:
        activities = db.query(Activity).filter(Activity.id.in_(organization.activity_ids)).all()
        if len(activities) != len(organization.activity_ids):
            found_ids = {a.id for a in activities}
            missing_ids = set(organization.activity_ids) - found_ids
            raise HTTPException(
                status_code=404, 
                detail=f"Activities with ids {missing_ids} not found"
            )
    
    # Create organization
    new_organization = OrganizationModel(
        name=organization.name,
        building_id=organization.building_id
    )
    
    # Add phone numbers
    for phone in organization.phone_numbers:
        org_phone = OrganizationPhone(
            phone_number=phone
        )
        new_organization.phone_numbers.append(org_phone)
    
    # Add activities
    if organization.activity_ids:
        activities = db.query(Activity).filter(Activity.id.in_(organization.activity_ids)).all()
        new_organization.activities.extend(activities)
    
    db.add(new_organization)
    db.commit()
    db.refresh(new_organization)
    
    # Load relationships for response
    db.refresh(new_organization)
    for phone in new_organization.phone_numbers:
        db.refresh(phone)
    
    return new_organization
