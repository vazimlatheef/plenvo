from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_current_user, get_db, require_admin_full_write_access, require_full_write_access
from app.models import User
from app.schemas.assignment import (
    AssignmentBatchResponse,
    AssignmentCreate,
    AssignmentListItem,
    AssignmentListResponse,
    AssignmentProgressResponse,
    AssignmentProgressUpdate,
)
from app.schemas.training_token import (
    TrainingTokenPublicResponse,
    TrainingTokenStatusResponse,
    TrainingTokenStatusUpdate,
)
from app.services.assignment_service import (
    _split_name,
    assignment_list_item_fields,
    create_assignments,
    get_training_by_token,
    list_assignments_for_user,
    update_assignment_by_token,
    update_assignment_progress,
)

router = APIRouter(prefix="/api/v1", tags=["assignments"])


@router.get("/assignments", response_model=AssignmentListResponse)
def list_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssignmentListResponse:
    rows = list_assignments_for_user(db, current_user=current_user)
    items = [AssignmentListItem(**assignment_list_item_fields(a)) for a in rows]
    return AssignmentListResponse(items=items, total=len(items))


@router.post("/assignments", response_model=AssignmentBatchResponse, status_code=status.HTTP_201_CREATED)
def create_assignment_batch(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_full_write_access),
) -> AssignmentBatchResponse:
    items = create_assignments(
        db,
        training_id=payload.training_id,
        assignee_emails=[str(e) for e in payload.assignee_emails],
        assignee_user_ids=payload.assignee_user_ids,
        assignee_contact_ids=payload.assignee_contact_ids,
        assigned_by_id=current_user.id,
        organisation_id=current_user.organisation_id,
    )
    return AssignmentBatchResponse(created=len(items), items=items)


@router.patch("/assignments/{assignment_id}/progress", response_model=AssignmentProgressResponse)
def update_assignment_progress_endpoint(
    assignment_id: int,
    payload: AssignmentProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_write_access),
) -> AssignmentProgressResponse:
    assignment = update_assignment_progress(
        db,
        assignment_id=assignment_id,
        current_user=current_user,
        status_value=payload.status,
    )
    return AssignmentProgressResponse(
        id=assignment.id,
        training_id=assignment.training_id,
        status=assignment.status,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
    )


@router.get("/training/token/{token}", response_model=TrainingTokenPublicResponse)
def get_training_token_public(token: str, db: Session = Depends(get_db)) -> TrainingTokenPublicResponse:
    token_row, assignment = get_training_by_token(db, token)
    training = assignment.training
    assigned_by = assignment.assigned_by
    if assignment.assignee is not None:
        assignee_first_name = assignment.assignee.first_name
        assignee_last_name = assignment.assignee.last_name
        assignee_email = assignment.assignee.email
    elif assignment.assignee_contact is not None:
        assignee_first_name, assignee_last_name = _split_name(assignment.assignee_contact.name)
        assignee_email = assignment.assignee_contact.email
    else:
        assignee_first_name, assignee_last_name, assignee_email = "Team", "Member", ""
    return TrainingTokenPublicResponse(
        assignment_id=assignment.id,
        status=assignment.status,
        training_title=training.title,
        training_description=training.description,
        content_type=training.content_type,
        youtube_video_id=training.youtube_video_id,
        external_url=training.external_url,
        assignee_first_name=assignee_first_name,
        assignee_last_name=assignee_last_name,
        assignee_email=assignee_email,
        assigned_by_full_name=assigned_by.full_name,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        token_expires_at=token_row.expires_at,
    )


@router.patch("/training/token/{token}/status", response_model=TrainingTokenStatusResponse)
def update_training_token_status(
    token: str,
    payload: TrainingTokenStatusUpdate,
    db: Session = Depends(get_db),
) -> TrainingTokenStatusResponse:
    assignment = update_assignment_by_token(db, token, payload.status)
    return TrainingTokenStatusResponse(
        status=assignment.status,
        started_at=assignment.started_at,
        completed_at=assignment.completed_at,
        message="Progress saved." if payload.status != "completed" else "Training marked complete.",
    )
