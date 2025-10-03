"""API endpoints for buildings."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_api_key
from app.models.models import Building as BuildingModel
from app.schemas import schemas

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get(
    "/",
    response_model=schemas.BuildingList,
    summary="List all buildings",
    description="Get a paginated list of all buildings"
)
async def list_buildings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """List all buildings."""
    query = db.query(BuildingModel)
    
    total = query.count()
    buildings = query.offset(offset).limit(limit).all()
    
    # Convert to schema format with lat/lon extraction
    buildings_response = []
    for building in buildings:
        # Extract coordinates from PostGIS POINT
        coords = db.execute(
            f"SELECT ST_X(coordinates::geometry) as lon, ST_Y(coordinates::geometry) as lat "
            f"FROM buildings WHERE id = {building.id}"
        ).first()
        
        buildings_response.append(
            schemas.Building(
                id=building.id,
                address=building.address,
                latitude=coords.lat if coords else 0.0,
                longitude=coords.lon if coords else 0.0,
                created_at=building.created_at,
                updated_at=building.updated_at
            )
        )
    
    return schemas.BuildingList(
        buildings=buildings_response,
        total=total
    )


@router.get(
    "/{building_id}",
    response_model=schemas.Building,
    summary="Get building by ID",
    description="Get detailed information about a specific building"
)
async def get_building(
    building_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get building by ID."""
    building = db.query(BuildingModel).filter(BuildingModel.id == building_id).first()
    
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    # Extract coordinates from PostGIS POINT
    coords = db.execute(
        f"SELECT ST_X(coordinates::geometry) as lon, ST_Y(coordinates::geometry) as lat "
        f"FROM buildings WHERE id = {building.id}"
    ).first()
    
    return schemas.Building(
        id=building.id,
        address=building.address,
        latitude=coords.lat if coords else 0.0,
        longitude=coords.lon if coords else 0.0,
        created_at=building.created_at,
        updated_at=building.updated_at
    )
