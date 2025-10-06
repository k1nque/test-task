"""API endpoints for buildings."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from geoalchemy2.elements import WKTElement

from app.db.session import get_db
from app.core.security import verify_api_key
from app.models.models import Building as BuildingModel
from app.schemas import schemas

router = APIRouter(prefix="/buildings", tags=["buildings"])

logger = logging.getLogger(__name__)


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
    buildings: list[BuildingModel] = query.offset(offset).limit(limit).all()

    # Convert to schema format with lat/lon extraction
    buildings_response = []
    for building in buildings:
        logger.debug(
            "Building %s coordinates raw value: %s",
            building.id,
            building.coordinates,
        )
        coords = db.execute(
            text(
                "SELECT ST_X(coordinates::geometry) AS lon, ST_Y(coordinates::geometry) AS lat "
                "FROM buildings WHERE id = :id"
            ),
            {"id": building.id},
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
        text(
            "SELECT ST_X(coordinates::geometry) AS lon, ST_Y(coordinates::geometry) AS lat "
            "FROM buildings WHERE id = :id"
        ),
        {"id": building.id},
    ).first()
    
    return schemas.Building(
        id=building.id,
        address=building.address,
        latitude=coords.lat if coords else 0.0,
        longitude=coords.lon if coords else 0.0,
        created_at=building.created_at,
        updated_at=building.updated_at
    )


@router.post(
    "/",
    response_model=schemas.Building,
    status_code=201,
    summary="Create building",
    description="Create a new building entry with geographic coordinates"
)
async def create_building(
    building: schemas.BuildingCreate,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Create a new building with coordinates."""
    try:
        new_building = BuildingModel(
            address=building.address,
            coordinates=WKTElement(
                f"POINT({building.longitude} {building.latitude})",
                srid=4326,
            ),
        )
        db.add(new_building)
        db.commit()
        db.refresh(new_building)

        coords = db.execute(
            text(
                "SELECT ST_X(coordinates::geometry) AS lon, ST_Y(coordinates::geometry) AS lat "
                "FROM buildings WHERE id = :id"
            ),
            {"id": new_building.id},
        ).first()

        logger.info("Created building %s at %s", new_building.id, new_building.address)

        return schemas.Building(
            id=new_building.id,
            address=new_building.address,
            latitude=coords.lat if coords else building.latitude,
            longitude=coords.lon if coords else building.longitude,
            created_at=new_building.created_at,
            updated_at=new_building.updated_at,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        db.rollback()
        logger.exception("Failed to create building", exc_info=exc)
        raise HTTPException(status_code=500, detail="Failed to create building") from exc
