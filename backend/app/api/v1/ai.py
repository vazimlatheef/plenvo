"""
AI Terminal endpoint — parses meeting notes / updates into structured tasks.
POST /api/v1/ai/parse-note   → returns extracted tasks (preview, not saved)
POST /api/v1/ai/confirm-tasks → saves confirmed tasks to DB
"""

import json
import os
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.models import Note, Task, User

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-20250514"


# ---------- Schemas ----------

class ParseNoteRequest(BaseModel):
    raw_text: str
    project_id: int | None = None
    title: str | None = None


class ExtractedTask(BaseModel):
    title: str
    description: str | None = None
    assignee_name: str | None = None   # free text — manager matches to user later
    due_date: str | None = None        # ISO date string e.g. "2026-05-01"
    priority: str = "medium"           # low | medium | high


class ParseNoteResponse(BaseModel):
    note_id: int
    extracted_tasks: list[ExtractedTask]


class ConfirmTasksRequest(BaseModel):
    note_id: int
    tasks: list[dict]   # each task: {title, description, assignee_id, due_date, priority, project_id}


# ---------- Helpers ----------

async def call_claude(raw_text: str) -> list[ExtractedTask]:
    """Send note text to Claude, get structured tasks back."""

    system_prompt = """You are an AI assistant for Plenvo, a management platform.
Your job is to extract actionable tasks from meeting notes or team updates.

Return ONLY a JSON array of tasks. No explanation, no markdown, no preamble.
Each task object must have:
- title (string, concise action)
- description (string or null, extra context)
- assignee_name (string or null, person's name if mentioned)
- due_date (string ISO format YYYY-MM-DD or null)
- priority (string: "low", "medium", or "high" — infer from urgency language)

Example output:
[
  {"title": "Prepare Q3 report", "description": null, "assignee_name": "John", "due_date": "2026-05-02", "priority": "high"},
  {"title": "Schedule client call", "description": "With Acme Corp", "assignee_name": "Sarah", "due_date": null, "priority": "medium"}
]"""

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

    # Strip markdown fences if Claude wraps in ```json
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    try:
        tasks_data = json.loads(raw_json)
        return [ExtractedTask(**t) for t in tasks_data]
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Try again.")


# ---------- Routes ----------

@router.post("/parse-note", response_model=ParseNoteResponse)
async def parse_note(
    body: ParseNoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: Manager pastes notes → AI extracts tasks → returns preview.
    Note is saved to DB so manager can confirm later.
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured.")

    # Save the raw note
    note = Note(
        raw_text=body.raw_text,
        title=body.title,
        project_id=body.project_id,
        created_by_id=current_user.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    # Call Claude
    extracted_tasks = await call_claude(body.raw_text)

    return ParseNoteResponse(note_id=note.id, extracted_tasks=extracted_tasks)


@router.post("/confirm-tasks")
def confirm_tasks(
    body: ConfirmTasksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 2: Manager reviews extracted tasks, edits if needed, confirms.
    Tasks are saved to DB with source='ai'.
    """
    # Mark note as processed
    note = db.get(Note, body.note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found.")
    note.processed_at = datetime.utcnow()

    created_tasks = []
    for t in body.tasks:
        task = Task(
            title=t["title"],
            description=t.get("description"),
            assignee_id=t.get("assignee_id"),       # manager maps name → user id in frontend
            due_date=t.get("due_date"),
            priority=t.get("priority", "medium"),
            project_id=t.get("project_id"),
            source="ai",
            created_by_id=current_user.id,
        )
        db.add(task)
        created_tasks.append(task)

    db.commit()

    return {"created": len(created_tasks), "message": f"{len(created_tasks)} tasks created successfully."}