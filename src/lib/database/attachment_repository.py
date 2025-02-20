from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from lib.models.attachment_dto import Attachment
from lib.database.database_models import AttachmentSchema, UserRequestAttachmentLinkSchema

class ExceptionAttachmentNotFound(Exception):
    pass

class AttachmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_attachment(self, attachment_id: UUID, object_name: str, content_type: str) -> Attachment:
        attachment = AttachmentSchema(
            id=attachment_id,
            object_name=object_name,
            content_type=content_type
        )
        self.session.add(attachment)
        self.session.commit()
        self.session.refresh(attachment)
        return Attachment(**attachment.model_dump())

    def get_attachment_by_id(self, attachment_id: UUID) -> Attachment:
        attachment_schema = self.session.query(AttachmentSchema).filter(AttachmentSchema.id == attachment_id).first()
        if not attachment_schema:
            raise ExceptionAttachmentNotFound("Attachment not found")
        return Attachment(**attachment_schema.model_dump())

    def delete_attachment(self, attachment_id: UUID):
        attachment = self.session.query(AttachmentSchema).filter(AttachmentSchema.id == attachment_id).first()
        if not attachment:
            raise ExceptionAttachmentNotFound("Attachment not found")
        self.session.delete(attachment)
        self.session.commit()

