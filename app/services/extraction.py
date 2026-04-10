from app.db.repositories.workflows import WorkflowRepository
from app.domain.enums import MessageCategory
from app.domain.schemas import ExtractResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class ExtractionService:
    def __init__(self, db: Session, extractor) -> None:
        self.db = db
        self.extractor = extractor

    def extract(self, message_id: str) -> ExtractResponse:
        repository = WorkflowRepository(self.db)
        message = repository.get_message(message_id)
        if message is None:
            raise HTTPException(status_code=404, detail=f"Message {message_id} was not found.")

        classification = repository.get_latest_classification(message_id)
        if classification:
            category = MessageCategory(classification.category)
        else:
            category, _, _ = self.extractor.classify(message.subject, message.body_text or "", message.sender)

        contractor_profile = None
        job_posting = None
        if category == MessageCategory.contractor:
            contractor_profile = self.extractor.extract_resume(message.subject, message.body_text or "", message.sender)
            repository.save_contractor_profile(
                message_id=message.id,
                full_name=contractor_profile.full_name,
                email=contractor_profile.email,
                phone=contractor_profile.phone,
                location=contractor_profile.location,
                summary=contractor_profile.summary,
                skills=contractor_profile.skills,
                experience_years=contractor_profile.experience_years,
                raw_extraction_json=contractor_profile.model_dump(),
            )
        elif category == MessageCategory.job_posting:
            job_posting = self.extractor.extract_job(message.subject, message.body_text or "", message.sender)
            repository.save_job_posting(
                message_id=message.id,
                title=job_posting.title,
                company=job_posting.company,
                location=job_posting.location,
                employment_type=job_posting.employment_type,
                required_skills=job_posting.required_skills,
                preferred_skills=job_posting.preferred_skills,
                raw_extraction_json=job_posting.model_dump(),
            )

        message.status = "extracted"
        self.db.commit()
        return ExtractResponse(
            message_id=message_id,
            category=category,
            contractor_profile=contractor_profile,
            job_posting=job_posting,
            provider=self.extractor.provider_name,
            placeholder=False,
        )
