"""Alert delivery channels."""
from __future__ import annotations

import asyncio
from email.message import EmailMessage
from typing import Any, Dict, Iterable

import httpx

from .config import (
    ConfigurationError,
    get_email_sender,
    get_smtp_host,
    get_smtp_password,
    get_smtp_port,
    get_smtp_use_tls,
    get_smtp_username,
    get_telegram_token,
)


ChannelStatus = Dict[str, Any]


def _build_status(
    channel: str,
    target: Any,
    success: bool,
    *,
    error: str | None = None,
    detail: Any | None = None,
) -> ChannelStatus:
    return {
        "channel": channel,
        "target": target,
        "success": success,
        "error": error,
        "detail": detail,
    }


async def send_telegram_alert(chat_id: str, text: str) -> ChannelStatus:
    """Send an alert through Telegram."""
    try:
        token = get_telegram_token()
    except ConfigurationError as exc:
        return _build_status(
            "telegram",
            chat_id,
            False,
            error=str(exc),
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            detail = getattr(exc, "response", None)
            status_code = detail.status_code if detail is not None else None
            return _build_status(
                "telegram",
                chat_id,
                False,
                error=str(exc),
                detail={"status_code": status_code},
            )

    return _build_status("telegram", chat_id, True)


async def send_email_alert(
    recipients: Iterable[str],
    subject: str,
    body: str,
) -> ChannelStatus:
    """Send an alert email using the configured SMTP server."""
    recipients_list = list(recipients)

    try:
        smtp_host = get_smtp_host()
        smtp_port = get_smtp_port()
        use_tls = get_smtp_use_tls()
        username = get_smtp_username()
        password = get_smtp_password()
        sender = get_email_sender()
    except ConfigurationError as exc:
        return _build_status("email", recipients_list, False, error=str(exc))

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(recipients_list)
    message.set_content(body)

    def _send_email() -> None:
        import smtplib

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if use_tls:
                server.starttls()
            if username and password:
                server.login(username, password)
            server.send_message(message)

    try:
        await asyncio.to_thread(_send_email)
    except Exception as exc:
        return _build_status("email", recipients_list, False, error=str(exc))

    return _build_status("email", recipients_list, True)


__all__ = ["send_telegram_alert", "send_email_alert", "ChannelStatus"]
