from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Project, Task, User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def _require_org(user: User) -> int:
    if user.organisation_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No organisation on account.")
    return user.organisation_id


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create tasks")

    org_id = _require_org(current_user)

    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if not project or project.organisation_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if task_in.assignee_id:
        assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
        if not assignee or assignee.organisation_id != org_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status or "pending",
        priority=task_in.priority or "medium",
        due_date=task_in.due_date,
        project_id=task_in.project_id,
        assignee_id=task_in.assignee_id,
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
    current_user: User = Depends(get_current_user),
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
        if task_in.title is not None:
            task.title = task_in.title
        if task_in.description is not None:
            task.description = task_in.description
        if task_in.status is not None:
            task.status = task_in.status
            if task_in.status == "completed":
                task.completed_at = datetime.now(timezone.utc)
        if task_in.priority is not None:
            task.priority = task_in.priority
        if task_in.due_date is not None:
            task.due_date = task_in.due_date
        if task_in.assignee_id is not None:
            assignee = db.query(User).filter(User.id == task_in.assignee_id).first()
            if not assignee or assignee.organisation_id != org_id:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            task.assignee_id = task_in.assignee_id

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete tasks")

    org_id = _require_org(current_user)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or task.organisation_id != org_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(task)
    db.commit()
    return None
