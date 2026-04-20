"""Resend-backed email client with a dev fallback that logs instead of sending."""

import asyncio

from loguru import logger

from app.core.config import settings
from app.email.templates import EmailContent


async def send_email(to: str, content: EmailContent) -> None:
    api_key = settings.email.resend_api_key
    if not api_key:
        logger.warning(
            "EMAIL__RESEND_API_KEY not set — email NOT sent. to={to} subject={subject}\n{text}",
            to=to,
            subject=content.subject,
            text=content.text,
        )
        return

    try:
        import resend
    except ImportError:  # pragma: no cover - optional dep in dev
        logger.error("resend package not installed; cannot send email")
        return

    resend.api_key = api_key
    payload = {
        "from": settings.email.from_address,
        "to": [to],
        "subject": content.subject,
        "text": content.text,
        "html": content.html,
    }
    # resend SDK is sync; offload so we don't block the event loop.
    await asyncio.to_thread(resend.Emails.send, payload)
    logger.info("Sent email to={to} subject={subject}", to=to, subject=content.subject)
