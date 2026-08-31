"""Transactional email via Resend (preferred) with MailerLite fallback.

Resend:
  RESEND_API_KEY in env → POST https://api.resend.com/emails
  Authorization: Bearer <key>
  From: hi@plenvo.io (verified domain)
"""

from __future__ import annotations

import os
import secrets
import string
from typing import Optional
from urllib.parse import quote

import requests

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_API_URL = "https://api.resend.com/emails"

# Legacy fallback used by older invite/training sends if Resend is not configured.
MAILERLITE_API_KEY = os.getenv("MAILERLITE_API_KEY", "").strip()
MAILERLITE_API_URL = "https://connect.mailerlite.com/api"

FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL", "hi@plenvo.io")
FROM_NAME = os.getenv("MAIL_FROM_NAME", "Plenvo")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://plenvo.io").rstrip("/")
API_BASE_URL = os.getenv("API_BASE_URL", os.getenv("BACKEND_URL", "http://localhost:8000")).rstrip("/")

FOOTER_TAGLINE = "Plenvo — project and task management for professional teams"
FOOTER_SUPPORT = "Questions? Reply to this email or contact hi@plenvo.io"


def greeting_name(display_name: str | None) -> str:
    """First name for email salutations; falls back to 'there'."""
    text = (display_name or "").strip()
    if not text:
        return "there"
    return text.split()[0]


def organisation_display_name(org: object | None, inviter: object | None = None) -> str:
    """Prefer the admin's company name over auto-generated workspace labels."""
    company = getattr(inviter, "company_name", None) if inviter else None
    if isinstance(company, str) and company.strip():
        return company.strip()
    org_name = getattr(org, "name", None) if org else None
    if isinstance(org_name, str) and org_name.strip():
        cleaned = org_name.strip()
        if cleaned.endswith("'s workspace"):
            return cleaned[: -len("'s workspace")].strip() or cleaned
        return cleaned
    return "your organisation"


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_unsubscribe_token() -> str:
    return secrets.token_urlsafe(32)


def build_verify_email_url(token: str) -> str:
    return f"{FRONTEND_URL}/verify-email?token={quote(token, safe='')}"


def build_reset_password_url(token: str) -> str:
    return f"{FRONTEND_URL}/reset-password?token={quote(token, safe='')}"


def build_training_magic_link_url(token: str) -> str:
    return f"{FRONTEND_URL}/training/{quote(token, safe='')}"


def build_my_tasks_url() -> str:
    return f"{FRONTEND_URL}/app/tasks"


def build_account_url() -> str:
    return f"{FRONTEND_URL}/app/account"


def build_unsubscribe_url(token: str) -> str:
    return f"{FRONTEND_URL}/unsubscribe?token={quote(token, safe='')}"


def _esc(text: str) -> str:
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _html_shell(body_html: str, footer_html: str) -> str:
    """Minimal professional HTML email — light background, no marketing chrome."""
    logo_url = f"{FRONTEND_URL}/plenvo-logo-full-v2.png"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Plenvo</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f2;color:#1a1a1a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f4f2;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border:1px solid #e6e6e2;">
          <tr>
            <td style="padding:0;background:#14170f;">
              <a href="{_esc(FRONTEND_URL)}" style="display:block;padding:20px 32px;text-decoration:none;">
                <img src="{_esc(logo_url)}" alt="Plenvo" width="148" height="40" style="display:block;height:40px;width:auto;border:0;outline:none;" />
              </a>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 32px 28px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:#333333;">
              {body_html}
            </td>
          </tr>
          <tr>
            <td style="padding:20px 32px;border-top:1px solid #e6e6e2;font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.5;color:#777777;">
              {footer_html}
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _footer_html(*, unsubscribe_url: str | None = None) -> str:
    parts = [
        f'<p style="margin:0 0 8px;">{_esc(FOOTER_TAGLINE)}</p>',
        f'<p style="margin:0 0 8px;">{_esc(FOOTER_SUPPORT)}</p>',
    ]
    if unsubscribe_url:
        parts.append(
            '<p style="margin:0;">'
            f'<a href="{_esc(unsubscribe_url)}" style="color:#555555;text-decoration:underline;">Unsubscribe</a>'
            " from non-essential Plenvo emails."
            "</p>"
        )
    return "\n".join(parts)


def _footer_text(*, unsubscribe_url: str | None = None) -> str:
    lines = [FOOTER_TAGLINE, FOOTER_SUPPORT]
    if unsubscribe_url:
        lines.append(f"Unsubscribe from non-essential emails: {unsubscribe_url}")
    return "\n".join(lines)


def _cta_button(url: str, label: str) -> str:
    return (
        f'<p style="margin:24px 0;">'
        f'<a href="{_esc(url)}" '
        f'style="display:inline-block;background:#1a1a1a;color:#ffffff;text-decoration:none;'
        f'padding:11px 20px;font-size:14px;font-family:Arial,Helvetica,sans-serif;">'
        f"{_esc(label)}</a></p>"
    )


def send_password_reset_email(
    to_email: str,
    first_name: str,
    reset_token: str,
) -> bool:
    """Password reset — security-critical; no unsubscribe link."""
    reset_url = build_reset_password_url(reset_token)
    name = greeting_name(first_name)
    subject = "Reset your Plenvo password"

    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(name)},</p>
      <p style="margin:0 0 14px;">
        We received a request to reset the password for your Plenvo account.
        Use the button below to choose a new password. This link is valid for one hour.
      </p>
      {_cta_button(reset_url, "Reset password")}
      <p style="margin:0 0 14px;font-size:13px;color:#555555;">
        If you did not request this, you can ignore this email. Your password will not change.
      </p>
      <p style="margin:0;font-size:12px;color:#888888;word-break:break-all;">
        Or open this link: {_esc(reset_url)}
      </p>
    """

    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=None))

    plain_text = f"""Hello {name},

We received a request to reset the password for your Plenvo account.
Open the link below to choose a new password. This link is valid for one hour.

{reset_url}

If you did not request this, you can ignore this email. Your password will not change.

{_footer_text()}
"""
    return _send_email(to_email, name, subject, plain_text, html_content)


def send_verification_email(
    to_email: str,
    first_name: str,
    verification_token: str,
    unsubscribe_token: str | None = None,
) -> bool:
    """Welcome + verify email for new signups. Includes unsubscribe for non-essential mail."""
    verify_url = build_verify_email_url(verification_token)
    unsub_url = build_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
    name = greeting_name(first_name)
    subject = "Welcome to Plenvo — confirm your email"

    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(name)},</p>
      <p style="margin:0 0 14px;">
        Welcome to Plenvo. We help teams plan projects, assign work, and track progress in one place.
      </p>
      <p style="margin:0 0 14px;">
        Please confirm your email address to finish setting up your account.
      </p>
      {_cta_button(verify_url, "Verify email")}
      <p style="margin:0;font-size:12px;color:#888888;word-break:break-all;">
        Or open this link: {_esc(verify_url)}
      </p>
    """

    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=unsub_url))

    plain_text = f"""Hello {name},

Welcome to Plenvo. We help teams plan projects, assign work, and track progress in one place.

Please confirm your email address to finish setting up your account:

{verify_url}

{_footer_text(unsubscribe_url=unsub_url)}
"""
    return _send_email(to_email, name, subject, plain_text, html_content)


def send_invite_email(
    to_email: str,
    employee_name: str,
    temp_password: str,
    organisation_name: Optional[str] = None,
    inviter_name: Optional[str] = None,
    unsubscribe_token: str | None = None,
) -> bool:
    """Invite with login credentials (operational). Unsubscribe optional for preference footer."""
    org_name = (organisation_name or "your organisation").strip()
    inviter = (inviter_name or "Your manager").strip()
    greeting = greeting_name(employee_name)
    subject = f"You have been invited to {org_name} on Plenvo"
    unsub_url = build_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
    login_url = f"{FRONTEND_URL}/login"
    signup_url = f"{FRONTEND_URL}/signup"

    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(greeting)},</p>
      <p style="margin:0 0 14px;">
        <strong>{_esc(inviter)}</strong> has invited you to join <strong>{_esc(org_name)}</strong> on Plenvo.
        Sign in with the details below, then change your password when prompted.
      </p>
      <p style="margin:0 0 8px;"><strong>Email:</strong> {_esc(to_email)}</p>
      <p style="margin:0 0 14px;"><strong>Temporary password:</strong> {_esc(temp_password)}</p>
      {_cta_button(login_url, "Sign in to Plenvo")}
      <p style="margin:0 0 14px;font-size:13px;color:#555555;">
        Prefer to register yourself? You can also
        <a href="{_esc(signup_url)}" style="color:#1a1a1a;">create an account</a>
        with this email address.
      </p>
      <p style="margin:0;font-size:13px;color:#555555;">
        If you were not expecting this invitation, please contact your manager or hi@plenvo.io.
      </p>
    """

    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=unsub_url))

    plain_text_content = f"""Hello {greeting},

{inviter} has invited you to join {org_name} on Plenvo.
Sign in with the details below, then change your password when prompted.

Email: {to_email}
Temporary password: {temp_password}

Sign in: {login_url}
Create an account: {signup_url}

If you were not expecting this invitation, please contact your manager or hi@plenvo.io.

{_footer_text(unsubscribe_url=unsub_url)}
"""
    return _send_email(to_email, greeting, subject, plain_text_content, html_content)


def send_training_magic_link_email(
    to_email: str,
    employee_name: str,
    training_title: str,
    assigned_by_name: str,
    magic_url: str,
    *,
    due_date: str | None = None,
    link_valid_days: int = 7,
    unsubscribe_token: str | None = None,
) -> bool:
    """Send employee a magic link to complete assigned training without logging in."""
    greeting = greeting_name(employee_name)
    subject = f"Training assigned: {training_title}"
    unsub_url = build_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
    due_line_html = ""
    due_line_text = ""
    if due_date:
        due_line_html = f'<p style="margin:0 0 14px;"><strong>Due date:</strong> {_esc(due_date)}</p>'
        due_line_text = f"Due date: {due_date}\n\n"
    day_word = "day" if link_valid_days == 1 else "days"
    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(greeting)},</p>
      <p style="margin:0 0 14px;">
        {_esc(assigned_by_name)} has assigned you training: <strong>{_esc(training_title)}</strong>.
      </p>
      {due_line_html}
      {_cta_button(magic_url, "Open training")}
      <p style="margin:0;font-size:13px;color:#555555;">This link works for {link_valid_days} {day_word}.</p>
    """
    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=unsub_url))
    plain_text = (
        f"Hello {greeting},\n\n"
        f"{assigned_by_name} has assigned you training: {training_title}.\n\n"
        f"{due_line_text}"
        f"Open your training: {magic_url}\n\n"
        f"This link works for {link_valid_days} {day_word}.\n\n"
        f"{_footer_text(unsubscribe_url=unsub_url)}"
    )
    return _send_email(to_email, greeting, subject, plain_text, html_content)


def send_manager_training_complete_email(
    to_email: str,
    manager_name: str,
    employee_name: str,
    training_title: str,
    *,
    unsubscribe_token: str | None = None,
) -> bool:
    """Notify manager when an employee completes training via magic link."""
    greeting = greeting_name(manager_name)
    subject = f"Training completed: {training_title}"
    dash = f"{FRONTEND_URL}/app/admin"
    unsub_url = build_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(greeting)},</p>
      <p style="margin:0 0 14px;">
        {_esc(employee_name)} has completed <strong>{_esc(training_title)}</strong>.
      </p>
      {_cta_button(dash, "View dashboard")}
    """
    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=unsub_url))
    plain_text = (
        f"Hello {greeting},\n\n"
        f"{employee_name} has completed {training_title}.\n\n"
        f"View progress: {dash}\n\n"
        f"{_footer_text(unsubscribe_url=unsub_url)}"
    )
    return _send_email(to_email, greeting, subject, plain_text, html_content)


def send_overdue_tasks_email(
    to_email: str,
    user_name: str,
    tasks: list,
    *,
    unsubscribe_token: str | None = None,
) -> bool:
    """Notify assignee about tasks that just became overdue (one email per batch)."""
    count = len(tasks)
    if count == 0:
        return False

    greeting = greeting_name(user_name)
    noun = "task" if count == 1 else "tasks"
    subject = f"You have {count} overdue {noun}"
    tasks_url = build_my_tasks_url()
    unsub_url = build_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None

    rows_html = []
    rows_text = []
    for task in tasks:
        title = getattr(task, "title", "Task")
        due = task.due_date.strftime("%d %b %Y") if getattr(task, "due_date", None) else "No due date"
        if getattr(task, "due_time", None):
            due = f"{due} {task.due_time.strftime('%H:%M')}"
        rows_html.append(
            f'<li style="margin:0 0 8px;"><strong>{_esc(title)}</strong> — due {_esc(due)}</li>'
        )
        rows_text.append(f"- {title} (due {due})")

    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(greeting)},</p>
      <p style="margin:0 0 14px;">The following {noun} are now overdue:</p>
      <ul style="margin:0 0 14px;padding-left:20px;">{''.join(rows_html)}</ul>
      {_cta_button(tasks_url, "Open My Tasks")}
    """
    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=unsub_url))
    plain_text = (
        f"Hello {greeting},\n\n"
        f"The following {noun} are now overdue:\n\n"
        f"{chr(10).join(rows_text)}\n\n"
        f"Open My Tasks: {tasks_url}\n\n"
        f"{_footer_text(unsubscribe_url=unsub_url)}"
    )
    return _send_email(to_email, greeting, subject, plain_text, html_content)


def send_trial_ending_email(
    to_email: str,
    user_name: str,
    *,
    days_left: int,
    project_count: int,
    task_count: int,
    unsubscribe_token: str | None = None,
) -> bool:
    """Warn org admin that trial ends soon."""
    greeting = greeting_name(user_name)
    day_word = "day" if days_left == 1 else "days"
    subject = f"Your Plenvo trial ends in {days_left} {day_word}"
    account_url = build_account_url()
    unsub_url = build_unsubscribe_url(unsubscribe_token) if unsubscribe_token else None
    body_html = f"""
      <p style="margin:0 0 14px;">Hello {_esc(greeting)},</p>
      <p style="margin:0 0 14px;">
        Your trial ends in {days_left} {day_word}. You currently have {project_count} project{'s' if project_count != 1 else ''}
        and {task_count} task{'s' if task_count != 1 else ''}.
        Upgrade to keep full access.
      </p>
      {_cta_button(account_url, "Upgrade in Account")}
    """
    html_content = _html_shell(body_html, _footer_html(unsubscribe_url=unsub_url))
    plain_text = (
        f"Hello {greeting},\n\n"
        f"Your trial ends in {days_left} {day_word}. You currently have {project_count} projects "
        f"and {task_count} tasks. Upgrade to keep full access.\n\n"
        f"Upgrade: {account_url}\n\n"
        f"{_footer_text(unsubscribe_url=unsub_url)}"
    )
    return _send_email(to_email, greeting, subject, plain_text, html_content)


def _send_email(to_email: str, name: str, subject: str, plain_text: str, html_content: str) -> bool:
    if RESEND_API_KEY:
        return _send_via_resend(to_email, name, subject, plain_text, html_content)
    if MAILERLITE_API_KEY:
        return _send_via_mailerlite(to_email, name, subject, plain_text, html_content)
    print("ERROR: Neither RESEND_API_KEY nor MAILERLITE_API_KEY is set")
    return False


def _send_via_resend(to_email: str, name: str, subject: str, plain_text: str, html_content: str) -> bool:
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": f"{FROM_NAME} <{FROM_EMAIL}>",
        "to": [to_email],
        "subject": subject,
        "text": plain_text,
        "html": html_content,
    }
    try:
        response = requests.post(RESEND_API_URL, headers=headers, json=payload, timeout=15)
        if response.status_code in (200, 201):
            print(f"✓ Resend email sent to {to_email}")
            return True
        print(f"✗ Resend failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"✗ Resend error: {e}")
        return False


def _send_via_mailerlite(to_email: str, name: str, subject: str, plain_text: str, html_content: str) -> bool:
    headers = {
        "Authorization": f"Bearer {MAILERLITE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "from": {"email": FROM_EMAIL, "name": FROM_NAME},
        "to": [{"email": to_email, "name": name}],
        "subject": subject,
        "text": plain_text,
        "html": html_content,
    }
    try:
        response = requests.post(
            f"{MAILERLITE_API_URL}/emails",
            headers=headers,
            json=payload,
            timeout=10,
        )
        if response.status_code == 202:
            print(f"✓ MailerLite email sent to {to_email}")
            return True
        print(f"✗ MailerLite failed: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"✗ MailerLite error: {e}")
        return False
