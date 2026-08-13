from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Assignment, Training
from app.schemas.training import TrainingAssignmentRow, TrainingCreate, TrainingSummary, TrainingUpdate


def _validate_training_content(t: Training) -> None:
    if t.content_type == "youtube":
        if not (t.youtube_video_id and str(t.youtube_video_id).strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Field "youtube_video_id" is required when content_type is "youtube".',
            )
    if t.content_type == "external_link":
        if not (t.external_url and str(t.external_url).strip()):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Field "external_url" is required when content_type is "external_link".',
            )


def create_training(
    db: Session,
    payload: TrainingCreate,
    *,
    created_by_id: int,
    organisation_id: int,
) -> Training:
    if organisation_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organisation on account.")

    training = Training(
        organisation_id=organisation_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        content_type=payload.content_type,
        storage_key=None,
        external_url=payload.external_url.strip() if payload.external_url else None,
        youtube_video_id=payload.youtube_video_id.strip() if payload.youtube_video_id else None,
        created_by_id=created_by_id,
    )
    db.add(training)
    db.commit()
    db.refresh(training)
    return training


def get_training_by_id(db: Session, training_id: int, *, organisation_id: int) -> Training:
    t = db.get(Training, training_id)
    if t is None or t.organisation_id != organisation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Training not found")
    return t


def update_training(
    db: Session,
    training_id: int,
    payload: TrainingUpdate,
    *,
    organisation_id: int,
) -> Training:
    t = get_training_by_id(db, training_id, organisation_id=organisation_id)
    data = payload.model_dump(exclude_unset=True)

    if "title" in data and data["title"] is not None:
        t.title = data["title"].strip()
    if "description" in data:
        d = data["description"]
        t.description = d.strip() if d else None
    if "content_type" in data and data["content_type"] is not None:
        t.content_type = data["content_type"]
    if "external_url" in data:
        eu = data["external_url"]
        t.external_url = eu.strip() if eu else None
    if "youtube_video_id" in data:
        y = data["youtube_video_id"]
        t.youtube_video_id = y.strip() if y else None

    _validate_training_content(t)
    db.commit()
    db.refresh(t)
    return t


def delete_training(db: Session, training_id: int, *, organisation_id: int) -> None:
    t = get_training_by_id(db, training_id, organisation_id=organisation_id)
    db.delete(t)
    db.commit()


def get_training_assignment_summary(db: Session, training_id: int, *, organisation_id: int) -> TrainingSummary:
    t = get_training_by_id(db, training_id, organisation_id=organisation_id)

    total_assigned = db.scalar(
        select(func.count()).select_from(Assignment).where(Assignment.training_id == training_id)
    )
    total_assigned = int(total_assigned or 0)

    stmt = (
        select(Assignment.status, func.count())
        .where(Assignment.training_id == training_id)
        .group_by(Assignment.status)
    )
    by_status = {row[0]: int(row[1]) for row in db.execute(stmt).all()}

    assign_rows = list(
        db.scalars(
            select(Assignment)
            .options(joinedload(Assignment.assignee))
            .where(Assignment.training_id == training_id)
        ).all()
    )
    assign_rows.sort(key=lambda a: (a.assignee.first_name.lower(), a.assignee.last_name.lower()))
    detail_rows = [
        TrainingAssignmentRow(
            assignee_full_name=a.assignee.full_name,
            assignee_email=a.assignee.email,
            status=a.status,
            started_at=a.started_at,
            completed_at=a.completed_at,
        )
        for a in assign_rows
    ]

    return TrainingSummary(
        training_id=training_id,
        training_title=t.title,
        total_assigned=total_assigned,
        completed=by_status.get("completed", 0),
        in_progress=by_status.get("in_progress", 0),
        not_started=by_status.get("not_started", 0),
        rows=detail_rows,
    )


def list_trainings(db: Session, *, organisation_id: int) -> list[Training]:
    if organisation_id is None:
        return []
    return list(
        db.scalars(
            select(Training)
            .where(Training.organisation_id == organisation_id)
            .order_by(Training.created_at.desc())
        ).all()
    )
