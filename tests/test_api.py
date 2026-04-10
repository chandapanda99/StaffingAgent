from app.api.routes.health import healthcheck
from app.db.models.records import JobPostingRecord, MessageRecord
from app.db.session import SessionLocal
from app.domain.schemas import IntakeRequest, MatchRunRequest
from app.integrations.graph.client import GraphMailboxClient
from app.integrations.llm.openai_adapter import OpenAIPlaceholderAdapter
from app.integrations.storage.s3 import S3AttachmentStorage
from app.services.classification import ClassificationService
from app.services.extraction import ExtractionService
from app.services.intake import IntakeService
from app.services.matching import MatchingService


def test_health() -> None:
    response = healthcheck()
    assert response.status == "ok"


def test_intake_persists_messages() -> None:
    with SessionLocal() as session:
        service = IntakeService(
            db=session,
            mailbox_client=GraphMailboxClient("tenant", "client", "secret", "mailbox@example.com"),
            storage=S3AttachmentStorage(
                endpoint_url="http://localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="email-intake",
                region="us-east-1",
                secure=False,
            ),
        )

        response = service.intake(IntakeRequest(limit=1))
        assert response.accepted is True
        assert response.status == "accepted"

        messages = session.query(MessageRecord).all()
        assert len(messages) == 1
        assert "Created 1 new records" in response.detail


def test_end_to_end_matching_flow() -> None:
    with SessionLocal() as session:
        intake_service = IntakeService(
            db=session,
            mailbox_client=GraphMailboxClient("tenant", "client", "secret", "mailbox@example.com"),
            storage=S3AttachmentStorage(
                endpoint_url="http://localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin",
                bucket="email-intake",
                region="us-east-1",
                secure=False,
            ),
        )
        adapter = OpenAIPlaceholderAdapter("gpt-4.1-mini")
        classification_service = ClassificationService(db=session, classifier=adapter)
        extraction_service = ExtractionService(db=session, extractor=adapter)
        matching_service = MatchingService(db=session, matcher=adapter)

        intake_service.intake(IntakeRequest(limit=2))

        messages = session.query(MessageRecord).order_by(MessageRecord.subject.asc()).all()
        assert len(messages) == 2
        job_message_id = next(message.id for message in messages if "Python Backend Engineer" in message.subject)
        contractor_message_id = next(message.id for message in messages if "Resume submission" in message.subject)

        classify_job = classification_service.classify(job_message_id)
        classify_contractor = classification_service.classify(contractor_message_id)
        assert classify_job.category.value == "job_posting"
        assert classify_contractor.category.value == "contractor"

        extract_job = extraction_service.extract(job_message_id)
        extract_contractor = extraction_service.extract(contractor_message_id)
        assert extract_job.job_posting is not None
        assert extract_job.job_posting.required_skills
        assert extract_contractor.contractor_profile is not None
        assert extract_contractor.contractor_profile.skills

        job_posting = session.query(JobPostingRecord).one()
        run = matching_service.run(MatchRunRequest(job_posting_id=job_posting.id, limit=5))
        assert run.status == "completed"

        result = matching_service.get(run.match_run_id)
        assert result.match_run_id == run.match_run_id
        assert result.candidates
        assert result.candidates[0].score > 0
