from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models import User
from app.schemas.training import TrainingCreate, TrainingPublic, TrainingSummary, TrainingUpdate
from app.services.training_service import (
    create_training as create_training_record,
    delete_training,
    get_training_assignment_summary,
    get_training_by_id,
    list_trainings,
    update_training,
)

router = APIRouter(prefix="/api/v1", tags=["trainings"])


@router.get("/trainings", response_model=list[TrainingPublic])
def list_trainings_endpoint(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> list[TrainingPublic]:
    return list_trainings(db)


@router.get("/trainings/{training_id}", response_model=TrainingPublic)
def get_training_endpoint(
    training_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> TrainingPublic:
    return get_training_by_id(db, training_id)


@router.get("/trainings/{training_id}/summary", response_model=TrainingSummary)
def training_assignment_summary(
    training_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> TrainingSummary:
    return get_training_assignment_summary(db, training_id)


@router.post("/trainings", response_model=TrainingPublic, status_code=status.HTTP_201_CREATED)
def create_training(
    payload: TrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> TrainingPublic:
    return create_training_record(db, payload, created_by_id=current_user.id)


@router.patch("/trainings/{training_id}", response_model=TrainingPublic)
def patch_training(
    training_id: int,
    payload: TrainingUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> TrainingPublic:
    return update_training(db, training_id, payload)


@router.delete("/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_training_endpoint(
    training_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_admin_user),
) -> None:
    delete_training(db, training_id)
