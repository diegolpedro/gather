"""FastAPI application exposing the alert service."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, root_validator

from .channels import ChannelStatus, send_email_alert, send_telegram_alert
from .db import create_alert_log, init_db


app = FastAPI(title="Alerts Service")


@app.on_event("startup")
async def startup() -> None:
    """Ensure database structures are created when the service starts."""

    await asyncio.to_thread(init_db)


class TelegramTarget(BaseModel):
    """Target configuration for Telegram alerts."""

    chat_id: str


class EmailTarget(BaseModel):
    """Target configuration for email alerts."""

    recipients: List[EmailStr]
    subject: Optional[str] = None
    body: Optional[str] = None

    @root_validator
    def check_recipients(cls, values: dict) -> dict:
        recipients = values.get("recipients") or []
        if not recipients:
            raise ValueError("At least one recipient is required for email alerts")
        return values


class AlertRequest(BaseModel):
    """Incoming alert definition."""

    message: str
    telegram: Optional[TelegramTarget] = None
    email: Optional[EmailTarget] = None

    @root_validator
    def check_channels(cls, values: dict) -> dict:
        if not values.get("telegram") and not values.get("email"):
            raise ValueError("At least one delivery channel must be provided")
        return values


async def _safe_execute(channel: str, target, coro) -> ChannelStatus:
    try:
        return await coro
    except Exception as exc:
        return {
            "channel": channel,
            "target": target,
            "success": False,
            "error": str(exc),
            "detail": None,
        }


@app.get("/health")
async def health() -> dict:
    """Health-check endpoint."""

    return {"status": "ok"}


@app.post("/alerts")
async def create_alert(request: AlertRequest) -> JSONResponse:
    """Dispatch an alert to the requested channels."""

    tasks = []
    audit_entries: List[Dict[str, Any]] = []

    if request.telegram is not None:
        tasks.append(
            _safe_execute(
                "telegram",
                request.telegram.chat_id,
                send_telegram_alert(request.telegram.chat_id, request.message),
            )
        )
        audit_entries.append(
            {
                "channel": "telegram",
                "target": request.telegram.chat_id,
                "message": request.message,
                "subject": None,
            }
        )

    if request.email is not None:
        email_target = request.email
        subject = email_target.subject or "Alert Notification"
        body = email_target.body or request.message
        recipients = [str(r) for r in email_target.recipients]
        tasks.append(
            _safe_execute(
                "email",
                recipients,
                send_email_alert(recipients, subject, body),
            )
        )
        audit_entries.append(
            {
                "channel": "email",
                "target": recipients,
                "message": body,
                "subject": subject,
            }
        )

    if not tasks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No delivery channels requested")

    results: List[ChannelStatus] = await asyncio.gather(*tasks)
    log_tasks = [
        asyncio.to_thread(
            create_alert_log,
            channel=entry["channel"],
            target=entry["target"],
            message=entry["message"],
            subject=entry["subject"],
            success=result.get("success", False),
            error=result.get("error"),
            detail=result.get("detail"),
        )
        for entry, result in zip(audit_entries, results)
    ]

    if log_tasks:
        log_results = await asyncio.gather(*log_tasks, return_exceptions=True)
        for idx, log_result in enumerate(log_results):
            detail: Any = results[idx].get("detail")
            if isinstance(detail, dict):
                detail_payload: Dict[str, Any] = detail
            elif detail is None:
                detail_payload = {}
            else:
                detail_payload = {"payload": detail}

            if isinstance(log_result, Exception):
                detail_payload["log_error"] = str(log_result)
            else:
                detail_payload["log_id"] = log_result

            results[idx]["detail"] = detail_payload

    overall_success = all(result.get("success") for result in results)

    status_code = status.HTTP_200_OK if overall_success else status.HTTP_207_MULTI_STATUS
    return JSONResponse(status_code=status_code, content={"results": results})
