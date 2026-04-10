"""ORM model package."""

from app.db.models.records import (
    AttachmentRecord,
    ClassificationResultRecord,
    ContractorProfileRecord,
    JobPostingRecord,
    MailboxConnectionRecord,
    MatchResultRecord,
    MatchRunRecord,
    MessageRecord,
)

__all__ = [
    "AttachmentRecord",
    "ClassificationResultRecord",
    "ContractorProfileRecord",
    "JobPostingRecord",
    "MailboxConnectionRecord",
    "MatchResultRecord",
    "MatchRunRecord",
    "MessageRecord",
]
