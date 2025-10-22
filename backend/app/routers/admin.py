from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PolicyDocument, RequestType, TaskDefinition
from ..schemas import PolicyResponse, RequestTypeCreate, RequestTypeSchema
from ..services.policy_service import PolicyService

router = APIRouter(prefix="/admin", tags=["Admin Configuration"])


@router.get("/request-types", response_model=List[RequestTypeSchema])
def get_request_types(db: Session = Depends(get_db)):
    """
    Get all configured request types with their tasks

    Returns the complete configuration of all request types.
    """
    request_types = db.query(RequestType).filter(RequestType.is_active == True).all()

    return request_types


@router.get("/request-types/{request_type_id}", response_model=RequestTypeSchema)
def get_request_type(request_type_id: int, db: Session = Depends(get_db)):
    """Get specific request type configuration"""
    request_type = (
        db.query(RequestType).filter(RequestType.id == request_type_id).first()
    )

    if not request_type:
        raise HTTPException(status_code=404, detail="Request type not found")

    return request_type


@router.post("/request-types", response_model=RequestTypeSchema)
def create_request_type(request: RequestTypeCreate, db: Session = Depends(get_db)):
    """
    Create a new request type with tasks

    Allows configuration of new customer request workflows.
    """
    # Check if request type already exists
    existing = db.query(RequestType).filter(RequestType.name == request.name).first()

    if existing:
        raise HTTPException(status_code=400, detail="Request type already exists")

    # Create request type
    request_type = RequestType(name=request.name, description=request.description)
    db.add(request_type)
    db.flush()

    # Create tasks
    for task_data in request.tasks:
        task = TaskDefinition(
            request_type_id=request_type.id,
            task_name=task_data.get("task_name"),
            task_type=task_data.get("task_type"),
            execution_order=task_data.get("execution_order"),
            configuration=task_data.get("configuration"),
        )
        db.add(task)

    db.commit()
    db.refresh(request_type)

    return request_type


@router.put("/request-types/{request_type_id}", response_model=RequestTypeSchema)
def update_request_type(
    request_type_id: int, request: RequestTypeCreate, db: Session = Depends(get_db)
):
    """Update request type configuration"""
    request_type = (
        db.query(RequestType).filter(RequestType.id == request_type_id).first()
    )

    if not request_type:
        raise HTTPException(status_code=404, detail="Request type not found")

    # Update request type
    request_type.name = request.name
    request_type.description = request.description

    # Delete old tasks
    db.query(TaskDefinition).filter(
        TaskDefinition.request_type_id == request_type_id
    ).delete()

    # Create new tasks
    for task_data in request.tasks:
        task = TaskDefinition(
            request_type_id=request_type.id,
            task_name=task_data.get("task_name"),
            task_type=task_data.get("task_type"),
            execution_order=task_data.get("execution_order"),
            configuration=task_data.get("configuration"),
        )
        db.add(task)

    db.commit()
    db.refresh(request_type)

    return request_type


@router.delete("/request-types/{request_type_id}")
def delete_request_type(request_type_id: int, db: Session = Depends(get_db)):
    """Deactivate a request type"""
    request_type = (
        db.query(RequestType).filter(RequestType.id == request_type_id).first()
    )

    if not request_type:
        raise HTTPException(status_code=404, detail="Request type not found")

    request_type.is_active = False
    db.commit()

    return {"message": "Request type deactivated successfully"}


@router.get("/policies", response_model=List[PolicyResponse])
def get_policies(policy_type: str = None, db: Session = Depends(get_db)):
    """
    Get all policies or filter by type

    Returns policy documents stored in the system.
    """
    if policy_type:
        policies = PolicyService.get_policies_by_type(db, policy_type)
    else:
        policies = db.query(PolicyDocument).all()

    return policies


@router.post("/policies")
def create_policy(
    policy_type: str,
    title: str,
    content: str,
    source_url: str = None,
    db: Session = Depends(get_db),
):
    """Create or update a policy document"""
    policy = PolicyService.store_policy(
        db=db,
        policy_type=policy_type,
        title=title,
        content=content,
        source_url=source_url,
    )

    return {"message": "Policy created/updated successfully", "id": policy.id}


@router.post("/policies/initialize")
def initialize_policies(db: Session = Depends(get_db)):
    """Initialize default policies"""
    PolicyService.initialize_default_policies(db)
    return {"message": "Default policies initialized successfully"}
