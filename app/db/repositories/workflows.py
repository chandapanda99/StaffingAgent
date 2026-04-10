from __future__ import annotations

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
from sqlalchemy import delete, select
from sqlalchemy.orm import Session


class WorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_mailbox_connection(
        self,
        *,
        mailbox_connection_id: str | None,
        user_id: str,
        name: str,
        provider: str = "microsoft_graph",
    ) -> MailboxConnectionRecord:
        if mailbox_connection_id:
            existing = self.db.get(MailboxConnectionRecord, mailbox_connection_id)
            if existing:
                return existing
            connection = MailboxConnectionRecord(
                id=mailbox_connection_id,
                user_id=user_id,
                name=name,
                provider=provider,
            )
            self.db.add(connection)
            self.db.flush()
            return connection

        stmt = (
            select(MailboxConnectionRecord)
            .where(MailboxConnectionRecord.user_id == user_id)
            .where(MailboxConnectionRecord.provider == provider)
            .order_by(MailboxConnectionRecord.created_at.asc())
        )
        existing = self.db.scalar(stmt)
        if existing:
            return existing

        connection = MailboxConnectionRecord(
            user_id=user_id,
            name=name,
            provider=provider,
        )
        self.db.add(connection)
        self.db.flush()
        return connection

    def upsert_message(
        self,
        *,
        mailbox_connection_id: str,
        external_id: str,
        internet_message_id: str | None,
        subject: str,
        sender: str,
        received_at,
        body_text: str | None,
        body_html: str | None,
        status: str = "received",
    ) -> tuple[MessageRecord, bool]:
        stmt = select(MessageRecord).where(MessageRecord.external_id == external_id)
        existing = self.db.scalar(stmt)
        created = existing is None
        message = existing or MessageRecord(
            mailbox_connection_id=mailbox_connection_id,
            external_id=external_id,
            internet_message_id=internet_message_id,
            subject=subject,
            sender=sender,
            received_at=received_at,
            body_text=body_text,
            body_html=body_html,
            status=status,
        )
        if existing is None:
            self.db.add(message)
        else:
            message.mailbox_connection_id = mailbox_connection_id
            message.internet_message_id = internet_message_id
            message.subject = subject
            message.sender = sender
            message.received_at = received_at
            message.body_text = body_text
            message.body_html = body_html
            message.status = status

        self.db.flush()
        return message, created

    def replace_attachments(self, *, message_id: str, attachments: list[dict]) -> list[AttachmentRecord]:
        self.db.execute(delete(AttachmentRecord).where(AttachmentRecord.message_id == message_id))
        records: list[AttachmentRecord] = []
        for item in attachments:
            record = AttachmentRecord(
                message_id=message_id,
                filename=item["filename"],
                content_type=item.get("content_type"),
                size_bytes=item["size_bytes"],
                storage_key=item["storage_key"],
                sha256=item.get("sha256"),
            )
            self.db.add(record)
            records.append(record)
        self.db.flush()
        return records

    def get_message(self, message_id: str) -> MessageRecord | None:
        return self.db.get(MessageRecord, message_id)

    def list_attachments(self, message_id: str) -> list[AttachmentRecord]:
        stmt = (
            select(AttachmentRecord)
            .where(AttachmentRecord.message_id == message_id)
            .order_by(AttachmentRecord.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def save_classification(
        self,
        *,
        message_id: str,
        category: str,
        confidence: float,
        rationale: str,
        provider: str,
    ) -> ClassificationResultRecord:
        stmt = (
            select(ClassificationResultRecord)
            .where(ClassificationResultRecord.message_id == message_id)
            .order_by(ClassificationResultRecord.created_at.desc())
        )
        existing = self.db.scalar(stmt)
        if existing:
            existing.category = category
            existing.confidence = confidence
            existing.rationale = rationale
            existing.provider = provider
            self.db.flush()
            return existing

        record = ClassificationResultRecord(
            message_id=message_id,
            category=category,
            confidence=confidence,
            rationale=rationale,
            provider=provider,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def get_latest_classification(self, message_id: str) -> ClassificationResultRecord | None:
        stmt = (
            select(ClassificationResultRecord)
            .where(ClassificationResultRecord.message_id == message_id)
            .order_by(ClassificationResultRecord.created_at.desc())
        )
        return self.db.scalar(stmt)

    def save_contractor_profile(
        self,
        *,
        message_id: str,
        full_name: str | None,
        email: str | None,
        phone: str | None,
        location: str | None,
        summary: str | None,
        skills: list[str],
        experience_years: float | None,
        raw_extraction_json: dict,
    ) -> ContractorProfileRecord:
        stmt = select(ContractorProfileRecord).where(ContractorProfileRecord.message_id == message_id)
        existing = self.db.scalar(stmt)
        if existing:
            existing.full_name = full_name
            existing.email = email
            existing.phone = phone
            existing.location = location
            existing.summary = summary
            existing.skills_json = skills
            existing.experience_years = experience_years
            existing.raw_extraction_json = raw_extraction_json
            self.db.flush()
            return existing

        record = ContractorProfileRecord(
            message_id=message_id,
            full_name=full_name,
            email=email,
            phone=phone,
            location=location,
            summary=summary,
            skills_json=skills,
            experience_years=experience_years,
            raw_extraction_json=raw_extraction_json,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def save_job_posting(
        self,
        *,
        message_id: str,
        title: str | None,
        company: str | None,
        location: str | None,
        employment_type: str | None,
        required_skills: list[str],
        preferred_skills: list[str],
        raw_extraction_json: dict,
    ) -> JobPostingRecord:
        stmt = select(JobPostingRecord).where(JobPostingRecord.message_id == message_id)
        existing = self.db.scalar(stmt)
        if existing:
            existing.title = title
            existing.company = company
            existing.location = location
            existing.employment_type = employment_type
            existing.required_skills_json = required_skills
            existing.preferred_skills_json = preferred_skills
            existing.raw_extraction_json = raw_extraction_json
            self.db.flush()
            return existing

        record = JobPostingRecord(
            message_id=message_id,
            title=title,
            company=company,
            location=location,
            employment_type=employment_type,
            required_skills_json=required_skills,
            preferred_skills_json=preferred_skills,
            raw_extraction_json=raw_extraction_json,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def get_job_posting(self, job_posting_id: str) -> JobPostingRecord | None:
        return self.db.get(JobPostingRecord, job_posting_id)

    def list_contractor_profiles(self) -> list[ContractorProfileRecord]:
        stmt = select(ContractorProfileRecord).order_by(ContractorProfileRecord.created_at.asc())
        return list(self.db.scalars(stmt))

    def create_match_run(self, *, job_posting_id: str, requested_by: str | None, status: str) -> MatchRunRecord:
        record = MatchRunRecord(
            job_posting_id=job_posting_id,
            requested_by=requested_by,
            status=status,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def replace_match_results(self, *, match_run_id: str, candidates: list[dict]) -> list[MatchResultRecord]:
        self.db.execute(delete(MatchResultRecord).where(MatchResultRecord.match_run_id == match_run_id))
        records: list[MatchResultRecord] = []
        for candidate in candidates:
            record = MatchResultRecord(
                match_run_id=match_run_id,
                contractor_profile_id=candidate["contractor_profile_id"],
                score=candidate["score"],
                summary=candidate["summary"],
                factor_breakdown_json=candidate["factor_breakdown_json"],
            )
            self.db.add(record)
            records.append(record)
        self.db.flush()
        return records

    def update_match_run_status(self, *, match_run_id: str, status: str) -> MatchRunRecord | None:
        record = self.db.get(MatchRunRecord, match_run_id)
        if record:
            record.status = status
            self.db.flush()
        return record

    def get_match_run(self, match_run_id: str) -> MatchRunRecord | None:
        return self.db.get(MatchRunRecord, match_run_id)

    def list_match_results(self, match_run_id: str) -> list[MatchResultRecord]:
        stmt = (
            select(MatchResultRecord)
            .where(MatchResultRecord.match_run_id == match_run_id)
            .order_by(MatchResultRecord.score.desc(), MatchResultRecord.created_at.asc())
        )
        return list(self.db.scalars(stmt))
