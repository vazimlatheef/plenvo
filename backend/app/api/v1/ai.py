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
from app.models.models import Contact, Note, Organisation, Project, Task, User
from app.services.mention_match import (
    build_person_candidates,
    match_person,
    match_project,
)
from app.services.plan_limits import assert_can_add_team_members
from app.services.relative_dates import resolve_task_due_date
from app.services.workspace_context import build_workspace_snapshot

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
    # Unmatched project / person mentions — UI may offer create-on-confirm.
    suggested_new_project: str | None = None
    suggested_new_contact: str | None = None


class ParseNoteResponse(BaseModel):
    note_id: int
    intent: str = "capture"
    briefing: str | None = None
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


def _normalize_person_name(name: str | None) -> str | None:
    return _normalize_project_title(name)


def _placeholder_contact_email(name: str, org_id: int) -> str:
    import re
    import secrets

    slug = re.sub(r"[^a-z0-9]+", ".", name.lower()).strip(".") or "contact"
    slug = slug[:40].strip(".")
    return f"{slug}.{org_id}.{secrets.token_hex(3)}@pending.local"


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
        data["suggested_new_contact"] = None

        # Relative / natural-language due dates → concrete ISO date.
        data["due_date"] = resolve_task_due_date(
            due_date=task.due_date,
            title=task.title,
            description=task.description,
            today=today,
        )

        assignee_name = _normalize_person_name(task.assignee_name)
        data["assignee_name"] = assignee_name

        person = match_person(assignee_name, people)
        if person:
            data["assignee_matched"] = True
            data["matched_assignee_label"] = person.display_name
            if person.kind == "user":
                data["assignee_id"] = person.id
            else:
                data["assignee_contact_id"] = person.id
        elif assignee_name:
            data["suggested_new_contact"] = assignee_name

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


async def call_claude(raw_text: str, *, today: date, snapshot: str) -> tuple[str, str | None, list[ExtractedTask]]:
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured.")

    today_iso = today.isoformat()
    today_label = today.strftime("%A, %d %B %Y")

    system_prompt = f"""You are Plenvo Brief — a calm workspace adjutant, not a chatbot and not a hype-y "AI assistant".
You help managers and individual operators run one place for their work: people, projects, tasks.

Today is {today_iso} ({today_label}).

You receive:
1) The user's message (notes, a question, or both)
2) A LIVE SNAPSHOT of their organisation (people, projects, tasks). Trust the snapshot. Do not invent people, projects, dates, or completion stats that are not in it.

Return ONLY a JSON object (no markdown fence unless you wrap the whole JSON — prefer raw JSON):
{{
  "intent": "capture" | "briefing" | "mixed",
  "briefing": string or null,
  "tasks": array of task objects
}}

intent:
- "capture" — they dumped notes / asked you to add work or people. Fill tasks. briefing may be a short confirmation (1-3 sentences) or null.
- "briefing" — they asked a question (what's next, how is X doing, team review, my performance). Fill briefing. tasks is [] unless they also asked to create work.
- "mixed" — both: e.g. "add these tasks and tell me who is overloaded".

Task object fields:
- title (string, concise action)
- description (string or null)
- assignee_name (string or null — name as written)
- project_name (string or null)
- due_date (string ISO YYYY-MM-DD or null)
- priority ("low" | "medium" | "high")

Date rules:
- Convert relative phrases using today: tomorrow, Thursday, next Monday, in 2 weeks, by Friday.
- Never leave due_date null when a day/date is mentioned.

What to capture as tasks (do not skip):
- Action items, meetings, calls, standups
- "Add Maya / new designer / intern" as a task assigned to that person (or unassigned titled "Add Maya to the team") — the product can create a contact on confirm
- Assigning existing work to someone

Briefing rules (critical):
- Ground every claim in the snapshot. If data is thin, say so in one line — do not fabricate a personality review.
- Performance = load (open tasks), overdue, priorities, recently completed. Not hours, attitude, or talent.
- "What's the most important thing next?" — pick 1-3 open items using overdue + high priority + due soon. Name the person if assigned.
- Team / employee review: compare load fairly; flag overload vs idle; name specific tasks.
- Own performance: only the asker's tasks.
- Be concise, professional, kind. No cheerleading. No "As an AI".
- Use short paragraphs or bullets. No tables.

LIVE SNAPSHOT:
{snapshot}
"""

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 4000,
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
            raw_json = raw_json.rsplit("```", 1)[0].strip()

        parsed = json.loads(raw_json)
        intent = "capture"
        briefing = None
        tasks_data: list = []

        if isinstance(parsed, list):
            tasks_data = parsed
        elif isinstance(parsed, dict):
            intent = str(parsed.get("intent") or "capture").strip().lower()
            if intent not in {"capture", "briefing", "mixed"}:
                intent = "capture"
            briefing = parsed.get("briefing")
            if briefing is not None:
                briefing = str(briefing).strip() or None
            tasks_data = parsed.get("tasks") or []
            if not isinstance(tasks_data, list):
                tasks_data = []
        else:
            raise ValueError("AI response JSON must be an object or array")

        allowed = set(ExtractedTask.model_fields)
        strip_keys = {
            "assignee_id",
            "assignee_contact_id",
            "project_id",
            "assignee_matched",
            "project_matched",
            "matched_assignee_label",
            "matched_project_label",
            "suggested_new_project",
            "suggested_new_contact",
        }
        cleaned = []
        for t in tasks_data:
            if not isinstance(t, dict):
                continue
            cleaned.append({k: v for k, v in t.items() if k in allowed and k not in strip_keys})
        return intent, briefing, [ExtractedTask(**t) for t in cleaned]
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
        snapshot = build_workspace_snapshot(
            db,
            org_id=current_user.organisation_id,
            asker=current_user,
            today=today,
        )
        intent, briefing, extracted_tasks = await call_claude(
            body.raw_text, today=today, snapshot=snapshot
        )
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
        intent=intent,
        briefing=briefing,
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

    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found.")

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

    # Create any new contacts requested in the review step (once per unique name).
    pending_contacts: dict[str, str] = {}
    for t in body.tasks:
        if t.get("assignee_id") or t.get("assignee_contact_id"):
            continue
        cname = _normalize_person_name(t.get("create_contact_name"))
        if cname:
            pending_contacts.setdefault(cname.casefold(), cname)

    if pending_contacts:
        assert_can_add_team_members(db, org, adding=len(pending_contacts))

    created_contact_ids: dict[str, int] = {}
    for key, cname in pending_contacts.items():
        contact = Contact(
            organisation_id=current_user.organisation_id,
            name=cname,
            email=_placeholder_contact_email(cname, current_user.organisation_id),
            role="Member",
        )
        db.add(contact)
        db.flush()
        created_contact_ids[key] = contact.id

    created_tasks = []
    for t in body.tasks:
        assignee_id = t.get("assignee_id")
        assignee_contact_id = t.get("assignee_contact_id")
        if assignee_id and assignee_contact_id:
            raise HTTPException(status_code=400, detail="Provide either assignee_id or assignee_contact_id, not both.")

        if not assignee_id and not assignee_contact_id:
            create_name = _normalize_person_name(t.get("create_contact_name"))
            if create_name:
                assignee_contact_id = created_contact_ids.get(create_name.casefold())

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
        "contacts_created": len(created_contact_ids),
        "message": f"{len(created_tasks)} tasks created successfully.",
    }
