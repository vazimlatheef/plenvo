"""Email preference endpoints (unsubscribe)."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.models import User

router = APIRouter(prefix="/api/v1/email", tags=["email"])

_FOOTER = "Plenvo — Project and task management for professionals"
_SUCCESS_TITLE = "You're unsubscribed"
_SUCCESS_BODY = (
    "You will no longer receive non-essential Plenvo emails at this address. "
    "Security messages such as password resets may still be sent when required. "
    "You can change this anytime in Profile → Notifications."
)
_INVALID_TITLE = "Link not valid"
_INVALID_BODY = (
    "This unsubscribe link is invalid or has already expired. "
    "If you continue to receive emails you do not want, contact hi@plenvo.io."
)


def _page(title: str, body: str, status_code: int = 200) -> HTMLResponse:
    from app.services.email import FRONTEND_URL

    logo_url = f"{FRONTEND_URL.rstrip('/')}/plenvo-icon-v2.png"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:40px 20px;font-family:Georgia,'Times New Roman',serif;background:#f7f7f5;color:#1a1a1a;">
  <div style="max-width:480px;margin:0 auto;background:#fff;border:1px solid #e5e5e0;padding:32px 28px;">
    <p style="margin:0 0 16px;">
      <img src="{logo_url}" alt="Plenvo" width="36" height="36" style="display:block;border-radius:8px;" />
    </p>
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
    format: str = Query("html"),
    db: Session = Depends(get_db),
):
    """Opt out of non-critical Plenvo emails (welcome / product / training / overdue)."""
    want_json = (format or "").strip().lower() == "json"
    user = (
        db.query(User)
        .filter(User.email_unsubscribe_token == token.strip())
        .first()
    )
    if user is None:
        if want_json:
            return JSONResponse(
                {"ok": False, "title": _INVALID_TITLE, "body": _INVALID_BODY},
                status_code=400,
            )
        return _page(_INVALID_TITLE, _INVALID_BODY, status_code=400)

    if not user.do_not_email:
        user.do_not_email = True
        db.commit()

    if want_json:
        return {"ok": True, "title": _SUCCESS_TITLE, "body": _SUCCESS_BODY}
    return _page(_SUCCESS_TITLE, _SUCCESS_BODY)
