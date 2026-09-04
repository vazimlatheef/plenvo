"""Default assignee on task create / AI confirm."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.api.v1 import tasks as tasks_api


def test_create_task_defaults_assignee_to_current_user():
    """When no assignee is sent, create_task assigns the creating admin."""
    db = MagicMock()
    current_user = MagicMock()
    current_user.id = 42
    current_user.role = "admin"
    current_user.organisation_id = 7

    task_in = MagicMock()
    task_in.project_id = None
    task_in.assignee_id = None
    task_in.assignee_contact_id = None
    task_in.title = "Solo task"
    task_in.description = None
    task_in.links = None
    task_in.status = "pending"
    task_in.priority = "medium"
    task_in.due_date = None
    task_in.due_time = None
    task_in.recurrence = "none"

    created = []

    def capture_add(obj):
        created.append(obj)

    db.add.side_effect = capture_add
    db.refresh.side_effect = lambda obj: None

    with patch("app.api.v1.tasks.expand_series", return_value=("none", None, [None])):
        with patch("app.api.v1.tasks.Task") as TaskModel:
            instance = MagicMock()
            TaskModel.return_value = instance
            result = tasks_api.create_task(task_in, db=db, current_user=current_user)

    assert result is instance
    kwargs = TaskModel.call_args.kwargs
    assert kwargs["assignee_id"] == 42
    assert kwargs["assignee_contact_id"] is None
    assert kwargs["created_by_id"] == 42
