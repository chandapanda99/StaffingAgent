from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.core.config import Settings


@dataclass
class MailboxAttachment:
    filename: str
    content_type: str
    content_bytes: bytes


@dataclass
class MailboxMessage:
    external_id: str
    internet_message_id: str
    subject: str
    sender: str
    received_at: datetime
    body_text: str
    body_html: str | None = None
    attachments: list[MailboxAttachment] | None = None


class GraphMailboxClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, user_id: str) -> None:
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_id = user_id

    @classmethod
    def from_settings(cls, settings: Settings) -> "GraphMailboxClient":
        return cls(
            tenant_id=settings.graph_tenant_id,
            client_id=settings.graph_client_id,
            client_secret=settings.graph_client_secret,
            user_id=settings.graph_user_id,
        )

    def list_messages(self, limit: int) -> list[MailboxMessage]:
        now = datetime.now(timezone.utc)
        return [
            MailboxMessage(
                external_id="placeholder-message-job",
                internet_message_id="<placeholder-message-job@example.com>",
                subject="Senior Python Backend Engineer - Chicago hybrid",
                sender="recruiter@example.com",
                received_at=now - timedelta(hours=2),
                body_text=(
                    "We need a Senior Python Backend Engineer in Chicago. "
                    "Required skills: Python, FastAPI, SQLAlchemy, PostgreSQL, AWS. "
                    "Preferred skills: Docker, Terraform. Full-time role."
                ),
                body_html=None,
                attachments=[],
            ),
            MailboxMessage(
                external_id="placeholder-message-contractor",
                internet_message_id="<placeholder-message-contractor@example.com>",
                subject="Resume submission - Priya Patel",
                sender="contractor@example.com",
                received_at=now - timedelta(hours=1),
                body_text=(
                    "Priya Patel\n"
                    "Email: priya.patel@example.com\n"
                    "Phone: 312-555-0187\n"
                    "Location: Chicago, IL\n"
                    "Experience: 7 years\n"
                    "Skills: Python, FastAPI, SQLAlchemy, PostgreSQL, Docker, AWS\n"
                    "Senior backend engineer focused on staffing and workflow automation.\n"
                ),
                body_html=None,
                attachments=[
                    MailboxAttachment(
                        filename="priya-patel-resume.txt",
                        content_type="text/plain",
                        content_bytes=(
                            b"Priya Patel\nPython, FastAPI, SQLAlchemy, PostgreSQL, Docker, AWS\n"
                            b"7 years of backend engineering experience.\n"
                        ),
                    )
                ],
            ),
        ][:limit]
