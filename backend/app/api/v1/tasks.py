from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Task, User, Project
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new task (admin only).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create tasks",
        )

    # Verify project belongs to admin's organisation
    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if not project or project.organisation_id != current_user.organisation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

    # Verify assigned user belongs to admin's organisation
    if task_in.assigned_to:
        assigned_user = db.query(User).filter(User.id == task_in.assigned_to).first()
        if not assigned_user or assigned_user.organisation_id != current_user.organisation_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

    task = Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status or "pending",
        priority=task_in.priority or "medium",
        deadline=task_in.deadline,
        project_id=task_in.project_id,
        assigned_to=task_in.assigned_to,
        organisation_id=current_user.organisation_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List tasks in the current user's organisation.
    Filter by project_id, assigned_to, or status.
    """
    query = db.query(Task).filter(Task.organisation_id == current_user.organisation_id)

    if project_id is not None:
        query = query.filter(Task.project_id == project_id)
    
    if assigned_to is not None:
        query = query.filter(Task.assigned_to == assigned_to)
    
    if status is not None:
        query = query.filter(Task.status == status)

    tasks = query.order_by(Task.created_at.desc()).all()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific task by ID (must belong to user's organisation).
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Organisation isolation check
    if task.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a task. Admins can update any field, employees can only update status.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Organisation isolation check
    if task.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Employees can only update status of tasks assigned to them
    if current_user.role == "employee":
        if task.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update tasks assigned to you",
            )
        # Employee can only change status
        if task_in.status is not None:
            task.status = task_in.status
    else:
        # Admin can update all fields
        if task_in.title is not None:
            task.title = task_in.title
        if task_in.description is not None:
            task.description = task_in.description
        if task_in.status is not None:
            task.status = task_in.status
        if task_in.priority is not None:
            task.priority = task_in.priority
        if task_in.deadline is not None:
            task.deadline = task_in.deadline
        if task_in.assigned_to is not None:
            # Verify new assignee belongs to organisation
            assigned_user = db.query(User).filter(User.id == task_in.assigned_to).first()
            if not assigned_user or assigned_user.organisation_id != current_user.organisation_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            task.assigned_to = task_in.assigned_to

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a task (admin only, must belong to user's organisation).
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete tasks",
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Organisation isolation check
    if task.organisation_id != current_user.organisation_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    db.delete(task)
    db.commit()
    return None