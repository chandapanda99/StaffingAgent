from collections.abc import Generator

from app.core.config import Settings, get_settings
from app.db.session import SessionLocal
from app.integrations.graph.client import GraphMailboxClient
from app.integrations.llm.openai_adapter import OpenAIPlaceholderAdapter
from app.integrations.storage.s3 import S3AttachmentStorage
from app.services.classification import ClassificationService
from app.services.extraction import ExtractionService
from app.services.health import HealthService
from app.services.intake import IntakeService
from app.services.matching import MatchingService
from sqlalchemy.orm import Session


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_app_settings() -> Settings:
    return get_settings()


def get_health_service() -> HealthService:
    return HealthService(
        storage=S3AttachmentStorage.from_settings(get_settings()),
    )


def get_intake_service(db: Session) -> IntakeService:
    settings = get_settings()
    return IntakeService(
        db=db,
        mailbox_client=GraphMailboxClient.from_settings(settings),
        storage=S3AttachmentStorage.from_settings(settings),
    )


def get_classification_service(db: Session) -> ClassificationService:
    return ClassificationService(
        db=db,
        classifier=OpenAIPlaceholderAdapter.from_settings(get_settings()),
    )


def get_extraction_service(db: Session) -> ExtractionService:
    return ExtractionService(
        db=db,
        extractor=OpenAIPlaceholderAdapter.from_settings(get_settings()),
    )


def get_matching_service(db: Session) -> MatchingService:
    return MatchingService(
        db=db,
        matcher=OpenAIPlaceholderAdapter.from_settings(get_settings()),
    )
