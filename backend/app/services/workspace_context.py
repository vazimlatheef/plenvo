"""Compact org snapshot for Brief (AI) — tasks, people, projects.

Keep this small: it is injected into the model prompt every request.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.models import Contact, Project, Task, User


def _iso(d) -> str | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date().isoformat()
    if hasattr(d, "isoformat"):
        return d.isoformat()
    return str(d)


def _person_label(task: Task, users_by_id: dict[int, User], contacts_by_id: dict[int, Contact]) -> str:
    if task.assignee_id and task.assignee_id in users_by_id:
        u = users_by_id[task.assignee_id]
        return u.full_name or u.email
    if task.assignee_contact_id and task.assignee_contact_id in contacts_by_id:
        return contacts_by_id[task.assignee_contact_id].name
    return "Unassigned"


def build_workspace_snapshot(
    db: Session,
    *,
    org_id: int,
    asker: User,
    today: date,
    task_limit: int = 80,
) -> str:
    users = db.query(User).filter(User.organisation_id == org_id).all()
    contacts = db.query(Contact).filter(Contact.organisation_id == org_id).all()
    projects = db.query(Project).filter(Project.organisation_id == org_id).all()
    tasks = (
        db.query(Task)
        .filter(Task.organisation_id == org_id)
        .order_by(Task.due_date.asc().nulls_last(), Task.id.desc())
        .limit(task_limit)
        .all()
    )

    users_by_id = {u.id: u for u in users}
    contacts_by_id = {c.id: c for c in contacts}
    projects_by_id = {p.id: p for p in projects}

    people_lines = []
    for u in users:
        people_lines.append(
            f"- {u.full_name} (account, role={u.role}"
            + (f", title={u.job_title}" if u.job_title else "")
            + ")"
        )
    for c in contacts:
        if c.user_id:
            continue
        people_lines.append(
            f"- {c.name} (contact, no login yet, role={c.role or 'Member'})"
        )

    project_lines = []
    for p in projects:
        n = sum(1 for t in tasks if t.project_id == p.id)
        project_lines.append(f"- {p.title} [{p.status}] (~{n} tasks in snapshot)")

    open_statuses = {"pending", "in_progress", "todo"}
    task_lines = []
    overdue = 0
    for t in tasks:
        status = (t.status or "pending").lower()
        due = t.due_date
        is_overdue = bool(due and due < today and status not in {"completed", "done", "cancelled"})
        if is_overdue:
            overdue += 1
        who = _person_label(t, users_by_id, contacts_by_id)
        proj = projects_by_id[t.project_id].title if t.project_id and t.project_id in projects_by_id else "—"
        flag = " OVERDUE" if is_overdue else ""
        task_lines.append(
            f"- [{status}] p={t.priority} due={_iso(due) or 'none'} "
            f"assignee={who} project={proj}{flag} :: {t.title}"
        )

    completed = sum(1 for t in tasks if (t.status or "").lower() in {"completed", "done"})
    open_n = sum(1 for t in tasks if (t.status or "").lower() not in {"completed", "done", "cancelled"})

    asker_name = asker.full_name or asker.email
    return f"""Asker: {asker_name} (auth_role={asker.role})
Today: {today.isoformat()}
Counts in snapshot: {len(tasks)} tasks ({open_n} open, {completed} completed, {overdue} overdue), {len(users)} accounts, {len(contacts)} contacts, {len(projects)} projects.

PEOPLE:
{chr(10).join(people_lines) or '- (none yet)'}

PROJECTS:
{chr(10).join(project_lines) or '- (none yet)'}

TASKS:
{chr(10).join(task_lines) or '- (none yet)'}
"""
