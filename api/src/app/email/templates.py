"""Magic-link email templates."""

import html
from dataclasses import dataclass


@dataclass
class EmailContent:
    subject: str
    text: str
    html: str


def _strip_controls(s: str) -> str:
    """Strip CR/LF/NUL so user-controlled names can't forge headers if the sender
    backend ever interprets them that way."""
    return s.replace("\r", " ").replace("\n", " ").replace("\x00", "")


def magic_link_signin(link: str) -> EmailContent:
    safe_link = html.escape(link, quote=True)
    subject = "Your sign-in link"
    text = (
        "Hi,\n\nClick the link below to sign in. It's good for 15 minutes and only works once.\n\n"
        f"{link}\n\nIf you didn't request this, you can ignore this email.\n"
    )
    body_html = (
        "<p>Hi,</p>"
        "<p>Click the link below to sign in. It's good for 15 minutes and only works once.</p>"
        f'<p><a href="{safe_link}">Sign in to your household</a></p>'
        f'<p style="color:#555;font-size:12px">Or paste this URL: {safe_link}</p>'
        "<p>If you didn't request this, you can ignore this email.</p>"
    )
    return EmailContent(subject=subject, text=text, html=body_html)


def magic_link_invite(link: str, inviter_name: str, household_name: str) -> EmailContent:
    inviter_safe = _strip_controls(inviter_name)
    household_safe = _strip_controls(household_name)
    inviter_html = html.escape(inviter_safe, quote=True)
    household_html = html.escape(household_safe, quote=True)
    safe_link = html.escape(link, quote=True)

    subject = f"{inviter_safe} invited you to {household_safe}"
    text = (
        f"Hi,\n\n{inviter_safe} invited you to join the '{household_safe}' household. "
        "Click the link below to accept. It's good for 15 minutes and only works once.\n\n"
        f"{link}\n"
    )
    body_html = (
        f"<p>Hi,</p><p>{inviter_html} invited you to join "
        f"<strong>{household_html}</strong>.</p>"
        "<p>Click the link below to accept. Good for 15 minutes, single use.</p>"
        f'<p><a href="{safe_link}">Join {household_html}</a></p>'
    )
    return EmailContent(subject=subject, text=text, html=body_html)
