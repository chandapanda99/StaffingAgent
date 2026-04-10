from app.domain.schemas import IntakeRequest, IntakeResponse
from app.db.repositories.workflows import WorkflowRepository
from sqlalchemy.orm import Session


class IntakeService:
    def __init__(self, db: Session, mailbox_client, storage) -> None:
        self.db = db
        self.mailbox_client = mailbox_client
        self.storage = storage

    def intake(self, payload: IntakeRequest) -> IntakeResponse:
        repository = WorkflowRepository(self.db)
        mailbox_connection = repository.get_or_create_mailbox_connection(
            mailbox_connection_id=payload.mailbox_connection_id,
            user_id=self.mailbox_client.user_id,
            name=f"{self.mailbox_client.user_id} mailbox",
        )
        discovered_messages = self.mailbox_client.list_messages(limit=payload.limit)
        created_messages = 0
        updated_messages = 0

        for item in discovered_messages:
            message, created = repository.upsert_message(
                mailbox_connection_id=mailbox_connection.id,
                external_id=item.external_id,
                internet_message_id=item.internet_message_id,
                subject=item.subject,
                sender=item.sender,
                received_at=item.received_at,
                body_text=item.body_text,
                body_html=item.body_html,
                status="received",
            )
            attachments = []
            for attachment in item.attachments or []:
                storage_key, sha256 = self.storage.store_bytes(
                    key_prefix=f"mailboxes/{mailbox_connection.id}/messages/{message.id}",
                    filename=attachment.filename,
                    content_bytes=attachment.content_bytes,
                    content_type=attachment.content_type,
                )
                attachments.append(
                    {
                        "filename": attachment.filename,
                        "content_type": attachment.content_type,
                        "size_bytes": len(attachment.content_bytes),
                        "storage_key": storage_key,
                        "sha256": sha256,
                    }
                )
            repository.replace_attachments(message_id=message.id, attachments=attachments)
            created_messages += int(created)
            updated_messages += int(not created)

        self.db.commit()
        return IntakeResponse(
            status="accepted",
            accepted=True,
            detail=(
                f"Ingested {len(discovered_messages)} messages for mailbox connection {mailbox_connection.id}. "
                f"Created {created_messages} new records and refreshed {updated_messages} existing records."
            ),
            suggested_next_step="Run classification on a message, then extract structured entities for matching.",
        )
