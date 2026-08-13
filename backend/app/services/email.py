import os
import secrets
import string
import requests
from typing import Optional

MAILERLITE_API_KEY = os.getenv("MAILERLITE_API_KEY")
MAILERLITE_API_URL = "https://connect.mailerlite.com/api"
FROM_EMAIL = "hi@plenvo.io"
FROM_NAME = "Plenvo"


def generate_temp_password(length: int = 12) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_invite_email(
    to_email: str,
    employee_name: str,
    temp_password: str,
    organisation_name: Optional[str] = None,
) -> bool:
    """
    Send employee invite email with login credentials via MailerLite.
    
    Args:
        to_email: Employee's email address
        employee_name: Employee's full name
        temp_password: Temporary password for first login
        organisation_name: Company name (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not MAILERLITE_API_KEY:
        print("ERROR: MAILERLITE_API_KEY not set")
        return False

    org_text = f" at {organisation_name}" if organisation_name else ""
    
    subject = f"Welcome to Plenvo{org_text}!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #d4d4d8; background-color: #0f1210; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background: #18191b; border: 1px solid #27272a; border-radius: 8px; overflow: hidden;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #c4a35a, #a6853a); padding: 32px 24px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px; font-weight: 600; color: #0f1210; font-family: 'Instrument Serif', Georgia, serif;">Plenvo</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 32px 24px;">
                <h2 style="margin: 0 0 16px; font-size: 20px; color: #fafafa;">Welcome to Plenvo{org_text}!</h2>
                
                <p style="margin: 0 0 16px; color: #d4d4d8;">Hi {employee_name},</p>
                
                <p style="margin: 0 0 24px; color: #d4d4d8;">Your manager has invited you to join Plenvo. You can now view your assigned tasks, training, and collaborate with your team.</p>
                
                <!-- Login Box -->
                <div style="background: #0f1210; border: 1px solid #27272a; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
                    <p style="margin: 0 0 12px; font-weight: 600; color: #fafafa;">Your login credentials:</p>
                    <p style="margin: 0 0 8px; color: #d4d4d8;"><strong style="color: #c4a35a;">Email:</strong> {to_email}</p>
                    <p style="margin: 0; color: #d4d4d8;"><strong style="color: #c4a35a;">Temporary Password:</strong> <code style="background: #27272a; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{temp_password}</code></p>
                </div>
                
                <p style="margin: 0 0 24px; color: #a1a1aa; font-size: 14px;">⚠️ Please change your password after logging in for the first time.</p>
                
                <!-- CTA Button -->
                <div style="text-align: center; margin-bottom: 24px;">
                    <a href="https://plenvo.io/login" style="display: inline-block; background: linear-gradient(135deg, #c4a35a, #a6853a); color: #0f1210; text-decoration: none; padding: 12px 32px; border-radius: 6px; font-weight: 600; font-size: 16px;">Sign In to Plenvo →</a>
                </div>
                
                <p style="margin: 0; color: #a1a1aa; font-size: 14px;">If you have any questions, reply to this email or contact your manager.</p>
            </div>
            
            <!-- Footer -->
            <div style="background: #0f1210; padding: 20px 24px; border-top: 1px solid #27272a; text-align: center;">
                <p style="margin: 0; color: #71717a; font-size: 12px;">Plenvo · Built for managers who move fast</p>
                <p style="margin: 8px 0 0; color: #71717a; font-size: 12px;">© 2026 Plenvo. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    plain_text_content = f"""
Welcome to Plenvo{org_text}!

Hi {employee_name},

Your manager has invited you to join Plenvo. You can now view your assigned tasks, training, and collaborate with your team.

Your login credentials:
Email: {to_email}
Temporary Password: {temp_password}

⚠️ Please change your password after logging in for the first time.

Sign in: https://plenvo.io/login

If you have any questions, reply to this email or contact your manager.

---
Plenvo · Built for managers who move fast
© 2026 Plenvo. All rights reserved.
    """

    # MailerLite API v2 endpoint for sending transactional emails
    headers = {
        "Authorization": f"Bearer {MAILERLITE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "from": {
            "email": FROM_EMAIL,
            "name": FROM_NAME,
        },
        "to": [
            {
                "email": to_email,
                "name": employee_name,
            }
        ],
        "subject": subject,
        "text": plain_text_content,
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
            print(f"✓ Invite email sent to {to_email}")
            return True
        else:
            print(f"✗ Failed to send email: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Email error: {str(e)}")
        return False


def send_training_magic_link_email(
    to_email: str,
    employee_name: str,
    training_title: str,
    assigned_by_name: str,
    magic_url: str,
) -> bool:
    """Send employee a magic link to complete assigned training without logging in."""
    if not MAILERLITE_API_KEY:
        print("ERROR: MAILERLITE_API_KEY not set")
        return False

    subject = f"Training assigned: {training_title}"
    html_content = f"""
    <p>Hi {employee_name},</p>
    <p><strong>{assigned_by_name}</strong> assigned you training: <strong>{training_title}</strong>.</p>
    <p><a href="{magic_url}">Open your training →</a></p>
    <p>This link expires in 7 days.</p>
    """
    plain_text = (
        f"Hi {employee_name},\n\n"
        f"{assigned_by_name} assigned you training: {training_title}.\n\n"
        f"Open your training: {magic_url}\n\n"
        f"This link expires in 7 days."
    )

    return _send_email(to_email, employee_name, subject, plain_text, html_content)


def send_manager_training_complete_email(
    to_email: str,
    manager_name: str,
    employee_name: str,
    training_title: str,
) -> bool:
    """Notify manager when an employee completes training via magic link."""
    if not MAILERLITE_API_KEY:
        print("ERROR: MAILERLITE_API_KEY not set")
        return False

    subject = f"{employee_name} completed: {training_title}"
    html_content = f"""
    <p>Hi {manager_name},</p>
    <p><strong>{employee_name}</strong> has completed <strong>{training_title}</strong>.</p>
    <p>View progress in your <a href="https://plenvo.io/app/admin">Plenvo dashboard</a>.</p>
    """
    plain_text = (
        f"Hi {manager_name},\n\n"
        f"{employee_name} has completed {training_title}.\n\n"
        f"View progress: https://plenvo.io/app/admin"
    )

    return _send_email(to_email, manager_name, subject, plain_text, html_content)


def _send_email(to_email: str, name: str, subject: str, plain_text: str, html_content: str) -> bool:
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
            print(f"✓ Email sent to {to_email}")
            return True
        print(f"✗ Failed to send email: {response.status_code} - {response.text}")
        return False
    except Exception as e:
        print(f"✗ Email error: {str(e)}")
        return False