"""Email preference endpoints (unsubscribe)."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.models import User

router = APIRouter(prefix="/api/v1/email", tags=["email"])

_FOOTER = "Plenvo — Project and task management for professionals"


def _page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:40px 20px;font-family:Georgia,'Times New Roman',serif;background:#f7f7f5;color:#1a1a1a;">
  <div style="max-width:480px;margin:0 auto;background:#fff;border:1px solid #e5e5e0;padding:32px 28px;">
    <p style="margin:0 0 8px;font-size:13px;letter-spacing:0.04em;text-transform:uppercase;color:#666;">Plenvo</p>
    <h1 style="margin:0 0 16px;font-size:22px;font-weight:400;">{title}</h1>
    <p style="margin:0 0 24px;font-size:15px;line-height:1.55;color:#333;">{body}</p>
    <p style="margin:0;font-size:12px;color:#888;">{_FOOTER}</p>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=status_code)


@router.get("/unsubscribe")
def unsubscribe_email(
    token: str = Query(..., min_length=8, max_length=128),
    db: Session = Depends(get_db),
):
    """Opt out of non-critical Plenvo emails (welcome / marketing)."""
    user = (
        db.query(User)
        .filter(User.email_unsubscribe_token == token.strip())
        .first()
    )
    if user is None:
        return _page(
            "Link not valid",
            "This unsubscribe link is invalid or has already expired. If you continue to receive emails you do not want, contact hi@plenvo.io.",
            status_code=400,
        )

    if not user.do_not_email:
        user.do_not_email = True
        db.commit()

    return _page(
        "Email preferences updated",
        "You will no longer receive non-essential Plenvo emails at this address. Security messages such as password resets may still be sent when required.",
    )
