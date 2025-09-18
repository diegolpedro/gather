"""Minimal Alerts service API stub."""

from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(title="Gather Alerts Service")


class Targets(BaseModel):
    """Delivery targets for alerts."""

    telegram: Optional[List[str]] = Field(
        default=None,
        description="Chat identifiers that should receive the message via Telegram.",
    )
    email: Optional[List[EmailStr]] = Field(
        default=None,
        description="E-mail addresses that should receive the message.",
    )


class AlertRequest(BaseModel):
    """Payload accepted by the alerts endpoint."""

    subject: Optional[str] = Field(
        default=None,
        description="Subject line to use when sending e-mails.",
    )
    body: str = Field(..., description="Body of the alert message in plain text.")
    targets: Targets = Field(
        default_factory=Targets,
        description="Destinations that should receive the alert.",
    )


@app.post("/alerts")
async def create_alert(alert: AlertRequest) -> dict[str, object]:
    """Acknowledge receipt of the alert request."""

    return {
        "status": "queued",
        "subject": alert.subject,
        "recipients": alert.targets.model_dump(exclude_none=True),
    }
