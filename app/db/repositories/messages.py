from __future__ import annotations

from app.db.models.records import MessageRecord
from sqlalchemy import select
from sqlalchemy.orm import Session


class MessageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, message_id: str) -> MessageRecord | None:
        return self.db.get(MessageRecord, message_id)

    def get_by_external_id(self, external_id: str) -> MessageRecord | None:
        stmt = select(MessageRecord).where(MessageRecord.external_id == external_id)
        return self.db.scalar(stmt)
