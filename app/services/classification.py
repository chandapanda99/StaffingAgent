from app.db.repositories.workflows import WorkflowRepository
from app.domain.schemas import ClassificationResponse
from fastapi import HTTPException
from sqlalchemy.orm import Session


class ClassificationService:
    def __init__(self, db: Session, classifier) -> None:
        self.db = db
        self.classifier = classifier

    def classify(self, message_id: str) -> ClassificationResponse:
        repository = WorkflowRepository(self.db)
        message = repository.get_message(message_id)
        if message is None:
            raise HTTPException(status_code=404, detail=f"Message {message_id} was not found.")

        category, confidence, rationale = self.classifier.classify(
            message.subject,
            message.body_text or "",
            message.sender,
        )
        repository.save_classification(
            message_id=message.id,
            category=category.value,
            confidence=confidence,
            rationale=rationale,
            provider=self.classifier.provider_name,
        )
        message.status = "classified"
        self.db.commit()
        return ClassificationResponse(
            message_id=message_id,
            category=category,
            confidence=confidence,
            rationale=rationale,
            provider=self.classifier.provider_name,
            placeholder=False,
        )
