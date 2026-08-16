"""
AI Terminal endpoint — parses meeting notes / updates into structured tasks.
"""

import json
import traceback
from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.models import Contact, Note, Project, Task, User
from app.services.mention_match import (
    build_person_candidates,
    match_person,
    match_project,
)
from app.services.relative_dates import resolve_task_due_date

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

# Read from Settings (loads backend/.env) — not bare os.getenv, which misses .env.
ANTHROPIC_API_KEY = (settings.anthropic_api_key or "").strip()
# Current Claude API model (claude-sonnet-4-20250514 was retired 2026-06-15).
CLAUDE_MODEL = (settings.anthropic_model or "claude-sonnet-4-6").strip()


class ParseNoteRequest(BaseModel):
    raw_text: str
    project_id: int | None = None
    title: str | None = None


class ExtractedTask(BaseModel):
    title: str
    description: str | None = None
    assignee_name: str | None = None
    project_name: str | None = None
    due_date: str | None = None
    priority: str = "medium"
    # Populated after conservative org directory match (null if none / ambiguous).
    assignee_id: int | None = None
    assignee_contact_id: int | None = None
    project_id: int | None = None
    assignee_matched: bool = False
    project_matched: bool = False
    # Canonical labels from User/Contact/Project (correct casing for UI).
    matched_assignee_label: str | None = None
    matched_project_label: str | None = None
    # Unmatched project mention — UI may offer "+ Create '{name}'" on confirm.
    suggested_new_project: str | None = None


class ParseNoteResponse(BaseModel):
    note_id: int
    extracted_tasks: list[ExtractedTask]
    today: str | None = None


class ConfirmTasksRequest(BaseModel):
    note_id: int
    tasks: list[dict]


def _parse_due_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _log_ai_error(context: str, exc: BaseException) -> None:
    print(
        f"[AI] {context}: {type(exc).__name__}: {exc}",
        flush=True,
    )
    traceback.print_exc()


def _normalize_project_title(name: str | None) -> str | None:
    if not name:
        return None
    text = " ".join(str(name).split()).strip()
    return text or None


def _resolve_extracted_tasks(
    tasks: list[ExtractedTask],
    *,
    users: list[User],
    contacts: list[Contact],
    projects: list[Project],
    note_project_id: int | None,
    today: date,
) -> list[ExtractedTask]:
    people = build_person_candidates(users=users, contacts=contacts)
    project_pairs = [(p.id, p.title) for p in projects]

    resolved: list[ExtractedTask] = []
    for task in tasks:
        data = task.model_dump()
        data["assignee_id"] = None
        data["assignee_contact_id"] = None
        data["project_id"] = note_project_id
        data["assignee_matched"] = False
        data["project_matched"] = False
        data["matched_assignee_label"] = None
        data["matched_project_label"] = None
        data["suggested_new_project"] = None

        # Relative / natural-language due dates → concrete ISO date.
        data["due_date"] = resolve_task_due_date(
            due_date=task.due_date,
            title=task.title,
            description=task.description,
            today=today,
        )

        person = match_person(task.assignee_name, people)
        if person:
            data["assignee_matched"] = True
            data["matched_assignee_label"] = person.display_name
            if person.kind == "user":
                data["assignee_id"] = person.id
            else:
                data["assignee_contact_id"] = person.id

        project_name = _normalize_project_title(task.project_name)
        data["project_name"] = project_name

        matched = match_project(project_name, project_pairs) if project_name else None
        if matched is not None:
            pid, canonical_title = matched
            data["project_id"] = pid
            data["project_matched"] = True
            data["matched_project_label"] = canonical_title
        elif project_name:
            # No unique existing match — offer create-on-confirm in the UI.
            data["suggested_new_project"] = project_name
            # Don't inherit note-level project when a specific new name was mentioned.
            data["project_id"] = None

        resolved.append(ExtractedTask(**data))
    return resolved


async def call_claude(raw_text: str, *, today: date) -> list[ExtractedTask]:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured.")

    today_iso = today.isoformat()
    today_label = today.strftime("%A, %d %B %Y")

    system_prompt = f"""You are an AI assistant for Plenvo, a management platform.
Your job is to extract actionable tasks from meeting notes or team updates.

Today's date is {today_iso} ({today_label}). Use this as "now" for all date reasoning.

Return ONLY a JSON array of tasks. No explanation, no markdown, no preamble.
Each task object must have:
- title (string, concise action — for meetings/events use a clear title like "Team standup")
- description (string or null, extra context e.g. time "9am", location, agenda)
- assignee_name (string or null, person's name if mentioned — use the name as written)
- project_name (string or null, project / initiative name if mentioned for this task)
- due_date (string ISO format YYYY-MM-DD or null)
- priority (string: "low", "medium", or "high" — infer from urgency language)

Date rules (critical):
- Convert EVERY relative or weekday phrase to an absolute YYYY-MM-DD using today's date above.
  Examples: "tomorrow", "Thursday", "next Monday", "in 2 weeks", "by Friday", "end of week".
- "Thursday" / "by Thursday" means the upcoming Thursday (including today if today is Thursday).
- "next Monday" means the Monday after this week's Monday.
- Never leave due_date null when the notes mention a day, date, or relative deadline for that item.
- If only a time is mentioned with a day (e.g. "Monday 9am"), still set due_date to that day's date; put the time in description.

What to extract (do NOT skip):
- Classic action items ("John to finish the report by Friday")
- Calendar / meeting / standup / sync / call / workshop / demo items
  (e.g. "Team standup Monday 9am", "recurring weekly sync on Wednesdays", "client call next Tuesday")
- Recurring or event-style mentions — capture them as tasks with the next/mentioned due_date
- Soft commitments that imply work ("need to prepare slides for Thursday's review")

Do not invent people or projects that are not in the notes. Leave assignee_name / project_name null when unclear.
Do not drop meeting or calendar-style lines — they are valid tasks."""

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 2000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": raw_text}],
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
    except HTTPException:
        raise
    except Exception as exc:
        _log_ai_error("Anthropic HTTP request failed", exc)
        raise HTTPException(
            status_code=500,
            detail=f"AI request failed ({type(exc).__name__}): {exc}",
        ) from exc

    if response.status_code != 200:
        body_preview = (response.text or "")[:800]
        print(
            f"[AI] Anthropic API error HTTP {response.status_code} "
            f"model={CLAUDE_MODEL}: {body_preview}",
            flush=True,
        )
        raise HTTPException(
            status_code=500,
            detail=(
                f"AI service error (HTTP {response.status_code}). "
                "Check ANTHROPIC_API_KEY and model configuration."
            ),
        )

    try:
        data = response.json()
        raw_json = data["content"][0]["text"].strip()

        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]

        tasks_data = json.loads(raw_json)
        if not isinstance(tasks_data, list):
            raise ValueError("AI response JSON root must be an array of tasks")
        allowed = set(ExtractedTask.model_fields)
        # Ignore model-invented id / match fields; we resolve matches server-side.
        strip_keys = {
            "assignee_id",
            "assignee_contact_id",
            "project_id",
            "assignee_matched",
            "project_matched",
            "matched_assignee_label",
            "matched_project_label",
            "suggested_new_project",
        }
        cleaned = []
        for t in tasks_data:
            if not isinstance(t, dict):
                continue
            cleaned.append({k: v for k, v in t.items() if k in allowed and k not in strip_keys})
        return [ExtractedTask(**t) for t in cleaned]
    except HTTPException:
        raise
    except Exception as exc:
        _log_ai_error("Failed to parse Anthropic response", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response ({type(exc).__name__}): {exc}",
        ) from exc


@router.post("/parse-note", response_model=ParseNoteResponse)
async def parse_note(
    body: ParseNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured.")
    if current_user.organisation_id is None:
        raise HTTPException(status_code=400, detail="No organisation on account.")

    today = date.today()

    note = Note(
        organisation_id=current_user.organisation_id,
        raw_text=body.raw_text,
        title=body.title,
        project_id=body.project_id,
        created_by_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    try:
        extracted_tasks = await call_claude(body.raw_text, today=today)
    except HTTPException:
        raise
    except Exception as exc:
        _log_ai_error("parse-note unhandled failure", exc)
        raise HTTPException(
            status_code=500,
            detail=f"AI parse failed ({type(exc).__name__}): {exc}",
        ) from exc

    org_id = current_user.organisation_id
    users = db.query(User).filter(User.organisation_id == org_id).all()
    contacts = db.query(Contact).filter(Contact.organisation_id == org_id).all()
    projects = db.query(Project).filter(Project.organisation_id == org_id).all()
    extracted_tasks = _resolve_extracted_tasks(
        extracted_tasks,
        users=users,
        contacts=contacts,
        projects=projects,
        note_project_id=body.project_id,
        today=today,
    )

    return ParseNoteResponse(
        note_id=note.id,
        extracted_tasks=extracted_tasks,
        today=today.isoformat(),
    )


@router.post("/confirm-tasks")
def confirm_tasks(
    body: ConfirmTasksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.organisation_id is None:
        raise HTTPException(status_code=400, detail="No organisation on account.")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can confirm AI tasks.")

    note = db.get(Note, body.note_id)
    if not note or note.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=404, detail="Note not found.")

    note.processed_at = datetime.now(timezone.utc)

    # Create any new projects requested in the review step (once per unique title).
    pending_titles: dict[str, str] = {}
    for t in body.tasks:
        if t.get("project_id"):
            continue
        title = _normalize_project_title(t.get("create_project_title"))
        if title:
            pending_titles.setdefault(title.casefold(), title)

    created_project_ids: dict[str, int] = {}
    for key, title in pending_titles.items():
        existing = (
            db.query(Project)
            .filter(
                Project.organisation_id == current_user.organisation_id,
                Project.title.ilike(title),
            )
            .first()
        )
        if existing:
            created_project_ids[key] = existing.id
            continue
        project = Project(
            title=title,
            description=None,
            organisation_id=current_user.organisation_id,
            manager_id=current_user.id,
        )
        db.add(project)
        db.flush()
        created_project_ids[key] = project.id

    created_tasks = []
    for t in body.tasks:
        assignee_id = t.get("assignee_id")
        assignee_contact_id = t.get("assignee_contact_id")
        if assignee_id and assignee_contact_id:
            raise HTTPException(status_code=400, detail="Provide either assignee_id or assignee_contact_id, not both.")
        if assignee_contact_id:
            contact = db.get(Contact, assignee_contact_id)
            if not contact or contact.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=404, detail="Contact not found.")
            if contact.user_id:
                assignee_id = contact.user_id

        project_id = t.get("project_id")
        if not project_id:
            create_title = _normalize_project_title(t.get("create_project_title"))
            if create_title:
                project_id = created_project_ids.get(create_title.casefold())

        if project_id:
            project = db.get(Project, project_id)
            if not project or project.organisation_id != current_user.organisation_id:
                raise HTTPException(status_code=404, detail="Project not found.")

        task = Task(
            title=t["title"],
            description=t.get("description"),
            assignee_id=assignee_id,
            assignee_contact_id=assignee_contact_id,
            due_date=_parse_due_date(t.get("due_date")),
            priority=t.get("priority", "medium"),
            project_id=project_id,
            source="ai",
            organisation_id=current_user.organisation_id,
            created_by_id=current_user.id,
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()
    return {
        "created": len(created_tasks),
        "projects_created": len(created_project_ids),
        "message": f"{len(created_tasks)} tasks created successfully.",
    }
