"""API endpoints for activities."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import verify_api_key
from app.models.models import Activity as ActivityModel
from app.schemas import schemas

router = APIRouter(prefix="/activities", tags=["activities"])


def build_activity_tree(activities: List[ActivityModel]) -> List[schemas.ActivityWithChildren]:
    """
    Build a tree structure from flat list of activities.
    
    Args:
        activities: List of activity models
        
    Returns:
        List of root activities with nested children
    """
    activity_dict = {}
    root_activities = []
    
    # Create dictionary of all activities
    for activity in activities:
        activity_with_children = schemas.ActivityWithChildren(
            id=activity.id,
            name=activity.name,
            parent_id=activity.parent_id,
            level=activity.level,
            created_at=activity.created_at,
            updated_at=activity.updated_at,
            children=[]
        )
        activity_dict[activity.id] = activity_with_children
    
    # Build tree structure
    for activity in activities:
        if activity.parent_id is None:
            root_activities.append(activity_dict[activity.id])
        else:
            if activity.parent_id in activity_dict:
                activity_dict[activity.parent_id].children.append(activity_dict[activity.id])
    
    return root_activities


@router.get(
    "/tree",
    response_model=schemas.ActivityTree,
    summary="Get activity tree",
    description="Get all activities organized in a tree structure"
)
async def get_activity_tree(
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get activity tree."""
    activities = db.query(ActivityModel).order_by(ActivityModel.level, ActivityModel.name).all()
    
    tree = build_activity_tree(activities)
    
    return schemas.ActivityTree(activities=tree)


@router.get(
    "/",
    response_model=List[schemas.Activity],
    summary="List all activities",
    description="Get a flat list of all activities"
)
async def list_activities(
    level: int = Query(None, ge=1, le=3, description="Filter by level (1-3)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """List all activities."""
    query = db.query(ActivityModel)
    
    if level is not None:
        query = query.filter(ActivityModel.level == level)
    
    activities = query.order_by(ActivityModel.level, ActivityModel.name).offset(offset).limit(limit).all()
    
    return activities


@router.get(
    "/{activity_id}",
    response_model=schemas.ActivityWithChildren,
    summary="Get activity by ID",
    description="Get detailed information about a specific activity including its children"
)
async def get_activity(
    activity_id: int,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Get activity by ID."""
    activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Get all descendants
    def get_all_descendants(act_id: int) -> List[ActivityModel]:
        children = db.query(ActivityModel).filter(ActivityModel.parent_id == act_id).all()
        all_desc = list(children)
        for child in children:
            all_desc.extend(get_all_descendants(child.id))
        return all_desc
    
    all_activities = [activity] + get_all_descendants(activity.id)
    tree = build_activity_tree(all_activities)
    
    return tree[0] if tree else schemas.ActivityWithChildren(
        id=activity.id,
        name=activity.name,
        parent_id=activity.parent_id,
        level=activity.level,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
        children=[]
    )
