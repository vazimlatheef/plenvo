from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin_full_write_access, require_full_write_access
from app.models.models import Contact, Project, Task, User
from app.schemas.link import normalize_links
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _require_org(user: User) -> int:
    if user.organisation_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organisation on account.")
    return user.organisation_id


def _validate_user_assignee(db: Session, org_id: int, assignee_id: int) -> User:
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee or assignee.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return assignee


def _validate_contact_assignee(db: Session, org_id: int, contact_id: int) -> Contact:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact or contact.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_full_write_access),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create tasks")

    org_id = _require_org(current_user)

    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if not project or project.organisation_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    assignee_id = task_in.assignee_id
    assignee_contact_id = task_in.assignee_contact_id

    if assignee_id is not None:
        _validate_user_assignee(db, org_id, assignee_id)
    if assignee_contact_id is not None:
        contact = _validate_contact_assignee(db, org_id, assignee_contact_id)
        # Prefer linked user so My Tasks works when contact already has an account.
        if contact.user_id:
            assignee_id = contact.user_id

    task = Task(
        title=task_in.title,
        description=task_in.description,
        links=normalize_links([l.model_dump() for l in task_in.links] if task_in.links else None),
        status=task_in.status or "pending",
        priority=task_in.priority or "medium",
        due_date=task_in.due_date,
        project_id=task_in.project_id,
        assignee_id=assignee_id,
        assignee_contact_id=assignee_contact_id,
        organisation_id=org_id,
        created_by_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    due_from: Optional[date] = None,
    due_to: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = _require_org(current_user)
    query = db.query(Task).filter(Task.organisation_id == org_id)

    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    if assignee_id is not None:
        query = query.filter(Task.assignee_id == assignee_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if due_from is not None or due_to is not None:
        query = query.filter(Task.due_date.isnot(None))
        if due_from is not None:
            query = query.filter(Task.due_date >= due_from)
        if due_to is not None:
            query = query.filter(Task.due_date <= due_to)

    if due_from is not None or due_to is not None:
        return query.order_by(Task.due_date.asc(), Task.created_at.desc()).all()
    return query.order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = _require_org(current_user)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_full_write_access),
):
    org_id = _require_org(current_user)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if current_user.role == "employee":
        if task.assignee_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update tasks assigned to you")
        if task_in.status is not None:
            task.status = task_in.status
            if task_in.status == "completed":
                task.completed_at = datetime.now(timezone.utc)
    else:
        data = task_in.model_dump(exclude_unset=True)
        if "title" in data and data["title"] is not None:
            task.title = data["title"]
        if "description" in data:
            task.description = data["description"]
        if "links" in data:
            task.links = normalize_links(data["links"])
        if "status" in data and data["status"] is not None:
            task.status = data["status"]
            if data["status"] == "completed":
                task.completed_at = datetime.now(timezone.utc)
        if "priority" in data and data["priority"] is not None:
            task.priority = data["priority"]
        if "due_date" in data:
            task.due_date = data["due_date"]
        if data.get("clear_assignee"):
            task.assignee_id = None
            task.assignee_contact_id = None
        elif "assignee_contact_id" in data and data["assignee_contact_id"] is not None:
            contact = _validate_contact_assignee(db, org_id, data["assignee_contact_id"])
            task.assignee_contact_id = contact.id
            task.assignee_id = contact.user_id
        elif "assignee_id" in data and data["assignee_id"] is not None:
            _validate_user_assignee(db, org_id, data["assignee_id"])
            task.assignee_id = data["assignee_id"]
            task.assignee_contact_id = None

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_full_write_access),
):
    org_id = _require_org(current_user)
    task = db.query(Task).filter(Task.id == task_id).first()
    # Org membership: never delete tasks outside the caller's organisation.
    if not task or task.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete tasks")

    db.delete(task)
    db.commit()
    return None
