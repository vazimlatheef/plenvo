from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db
from app.models import User
from app.schemas.training import TrainingCreate, TrainingListItem, TrainingPublic, TrainingSummary, TrainingUpdate
from app.services.training_service import (
    create_training as create_training_record,
    delete_training,
    get_training_assignment_summary,
    get_training_by_id,
    list_trainings,
    update_training,
)

router = APIRouter(prefix="/api/v1", tags=["trainings"])


def _org_id(user: User) -> int:
    if user.organisation_id is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No organisation on account.")
    return user.organisation_id


@router.get("/trainings", response_model=list[TrainingListItem])
def list_trainings_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> list[TrainingListItem]:
    return list_trainings(db, organisation_id=_org_id(current_user))


@router.get("/trainings/{training_id}", response_model=TrainingPublic)
def get_training_endpoint(
    training_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> TrainingPublic:
    return get_training_by_id(db, training_id, organisation_id=_org_id(current_user))


@router.get("/trainings/{training_id}/summary", response_model=TrainingSummary)
def training_assignment_summary(
    training_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> TrainingSummary:
    return get_training_assignment_summary(db, training_id, organisation_id=_org_id(current_user))


@router.post("/trainings", response_model=TrainingPublic, status_code=status.HTTP_201_CREATED)
def create_training(
    payload: TrainingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> TrainingPublic:
    return create_training_record(
        db,
        payload,
        created_by_id=current_user.id,
        organisation_id=_org_id(current_user),
    )


@router.patch("/trainings/{training_id}", response_model=TrainingPublic)
def patch_training(
    training_id: int,
    payload: TrainingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> TrainingPublic:
    return update_training(db, training_id, payload, organisation_id=_org_id(current_user))


@router.delete("/trainings/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_training_endpoint(
    training_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> None:
    delete_training(db, training_id, organisation_id=_org_id(current_user))
