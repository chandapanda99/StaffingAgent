from app.api.dependencies import (
    get_classification_service,
    get_db_session,
    get_extraction_service,
    get_intake_service,
    get_matching_service,
)
from app.domain.schemas import (
    ClassificationResponse,
    ExtractResponse,
    IntakeRequest,
    IntakeResponse,
    MatchResultResponse,
    MatchRunRequest,
    MatchRunResponse,
)
from app.services.classification import ClassificationService
from app.services.extraction import ExtractionService
from app.services.intake import IntakeService
from app.services.matching import MatchingService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/emails/intake", response_model=IntakeResponse)
def intake_emails(
    payload: IntakeRequest,
    db: Session = Depends(get_db_session),
) -> IntakeResponse:
    service = get_intake_service(db)
    return service.intake(payload)


@router.post("/messages/{message_id}/classify", response_model=ClassificationResponse)
def classify_message(
    message_id: str,
    db: Session = Depends(get_db_session),
) -> ClassificationResponse:
    service: ClassificationService = get_classification_service(db)
    return service.classify(message_id)


@router.post("/messages/{message_id}/extract", response_model=ExtractResponse)
def extract_message(
    message_id: str,
    db: Session = Depends(get_db_session),
) -> ExtractResponse:
    service: ExtractionService = get_extraction_service(db)
    return service.extract(message_id)


@router.post("/matches/run", response_model=MatchRunResponse)
def run_match(
    payload: MatchRunRequest,
    db: Session = Depends(get_db_session),
) -> MatchRunResponse:
    service: MatchingService = get_matching_service(db)
    return service.run(payload)


@router.get("/matches/{match_run_id}", response_model=MatchResultResponse)
def get_match_run(
    match_run_id: str,
    db: Session = Depends(get_db_session),
) -> MatchResultResponse:
    service: MatchingService = get_matching_service(db)
    return service.get(match_run_id)
