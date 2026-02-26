"""
Email service for Radius.

Thin wrapper around Resend. All outbound email goes through here,
so swapping providers means changing this file only.

Requires:
    RESEND_API_KEY env var — get from resend.com
    FROM_EMAIL env var    — must be a verified domain on Resend (default: hello@getradius.com)

If RESEND_API_KEY is not set, emails are logged instead of sent.
This lets the signup flow work in development without a real Resend account.
"""

import logging

logger = logging.getLogger(__name__)


def send_welcome_email(
    to_email: str,
    business_name: str,
    api_key: str,
    business_id: str,
) -> bool:
    """
    Send a welcome email containing the new sandbox API key.

    The key is shown in the email because this is the only time it's available
    in plaintext — we only store a SHA-256 hash in the database.

    Returns True if sent successfully, False otherwise.
    If RESEND_API_KEY is not configured, logs the email content and returns True
    (so development/testing works without an email provider).
    """
    from app.core.config import settings

    subject = "Your Radius API key is ready"
    html = _welcome_html(business_name, api_key, business_id)

    if not settings.resend_api_key:
        logger.info(
            "email_skipped",
            extra={
                "event": "email_skipped",
                "reason": "RESEND_API_KEY not configured",
                "to": to_email,
                "subject": subject,
                "api_key_preview": api_key[:16] + "...",
            },
        )
        return True

    try:
        import resend
        resend.api_key = settings.resend_api_key

        resend.Emails.send({
            "from": settings.from_email,
            "to": [to_email],
            "subject": subject,
            "html": html,
        })

        logger.info(
            "welcome_email_sent",
            extra={"event": "welcome_email_sent", "to": to_email, "business_id": business_id},
        )
        return True

    except Exception as exc:
        logger.error(
            "welcome_email_failed",
            extra={"event": "welcome_email_failed", "to": to_email, "error": str(exc)},
        )
        return False


def _welcome_html(business_name: str, api_key: str, business_id: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f9fafb; margin: 0; padding: 40px 20px; color: #111827; }}
    .card {{ background: white; border-radius: 12px; padding: 40px;
             max-width: 560px; margin: 0 auto; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    h1 {{ font-size: 22px; margin: 0 0 8px; }}
    p  {{ font-size: 15px; line-height: 1.6; color: #374151; margin: 0 0 16px; }}
    .key-box {{ background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 8px;
                padding: 16px 20px; font-family: monospace; font-size: 14px;
                word-break: break-all; margin: 24px 0; color: #111827; }}
    .warning {{ font-size: 13px; color: #dc2626; margin: 0 0 24px; }}
    .steps {{ background: #eff6ff; border-radius: 8px; padding: 20px 24px; margin: 24px 0; }}
    .steps p {{ margin: 0 0 8px; font-size: 14px; }}
    .steps p:last-child {{ margin: 0; }}
    .footer {{ font-size: 13px; color: #6b7280; margin: 24px 0 0; border-top: 1px solid #f3f4f6; padding-top: 20px; }}
    a {{ color: #2563eb; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Welcome to Radius, {business_name}</h1>
    <p>Your sandbox API key is ready. This is the <strong>only time</strong> we'll show it — we store only a hash, not the key itself.</p>

    <div class="key-box">{api_key}</div>
    <p class="warning">⚠ Copy this key now and store it somewhere safe (a password manager or secrets vault). It cannot be recovered.</p>

    <div class="steps">
      <p><strong>Get started in 3 steps:</strong></p>
      <p>1. Add <code>X-API-Key: {api_key[:20]}...</code> to your request headers</p>
      <p>2. POST to <code>/v1/transactions/ingest</code> with a transaction payload</p>
      <p>3. GET <code>/v1/transactions/{{id}}/audit</code> to retrieve the compliance record</p>
    </div>

    <p>Your account ID is <code>{business_id}</code> — you'll see this in audit records and logs.</p>

    <p>This is a <strong>sandbox key</strong>. It's isolated from production data and has a lower rate limit. When you're ready to go live, reply to this email and we'll upgrade your account.</p>

    <p>Questions? Email us at <a href="mailto:hello@getradius.com">hello@getradius.com</a> or check the <a href="https://getradius.com/docs">docs</a>.</p>

    <div class="footer">Radius · Payment attestation infrastructure · <a href="https://getradius.com">getradius.com</a></div>
  </div>
</body>
</html>
"""
