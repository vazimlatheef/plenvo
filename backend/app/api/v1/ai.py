"""
AI Terminal endpoint — parses meeting notes / updates into structured tasks.
"""

import json
import os
from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Note, Task, User

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"


class ParseNoteRequest(BaseModel):
    raw_text: str
    project_id: int | None = None
    title: str | None = None


class ExtractedTask(BaseModel):
    title: str
    description: str | None = None
    assignee_name: str | None = None
    due_date: str | None = None
    priority: str = "medium"


class ParseNoteResponse(BaseModel):
    note_id: int
    extracted_tasks: list[ExtractedTask]


class ConfirmTasksRequest(BaseModel):
    note_id: int
    tasks: list[dict]


def _parse_due_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return None


async def call_claude(raw_text: str) -> list[ExtractedTask]:
    system_prompt = """You are an AI assistant for Plenvo, a management platform.
Your job is to extract actionable tasks from meeting notes or team updates.

Return ONLY a JSON array of tasks. No explanation, no markdown, no preamble.
Each task object must have:
- title (string, concise action)
- description (string or null, extra context)
- assignee_name (string or null, person's name if mentioned)
- due_date (string ISO format YYYY-MM-DD or null)
- priority (string: "low", "medium", or "high" — infer from urgency language)"""

    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 1000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": raw_text}],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="AI service error. Check ANTHROPIC_API_KEY.")

    data = response.json()
    raw_json = data["content"][0]["text"].strip()

    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    try:
        tasks_data = json.loads(raw_json)
        return [ExtractedTask(**t) for t in tasks_data]
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Try again.")


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

    extracted_tasks = await call_claude(body.raw_text)
    return ParseNoteResponse(note_id=note.id, extracted_tasks=extracted_tasks)


@router.post("/confirm-tasks")
def confirm_tasks(
    body: ConfirmTasksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.organisation_id is None:
        raise HTTPException(status_code=400, detail="No organisation on account.")

    note = db.get(Note, body.note_id)
    if not note or note.organisation_id != current_user.organisation_id:
        raise HTTPException(status_code=404, detail="Note not found.")

    note.processed_at = datetime.now(timezone.utc)

    created_tasks = []
    for t in body.tasks:
        task = Task(
            title=t["title"],
            description=t.get("description"),
            assignee_id=t.get("assignee_id"),
            due_date=_parse_due_date(t.get("due_date")),
            priority=t.get("priority", "medium"),
            project_id=t.get("project_id"),
            source="ai",
            organisation_id=current_user.organisation_id,
            created_by_id=current_user.id,
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()
    return {"created": len(created_tasks), "message": f"{len(created_tasks)} tasks created successfully."}
