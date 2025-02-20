import os
from uuid import UUID
import aioboto3.session
from fastapi import APIRouter, Depends, HTTPException, status, Query
from lib.app.verifiers import verify_token, only_admin
from lib.app.settings import Settings
from lib.app.services import get_attachment_repository
from lib.app.common import get_settings
from lib.database.attachment_repository import AttachmentRepository
from lib.models.user_account_dto import User
from typing import Annotated
import aioboto3
from botocore.exceptions import ClientError
from botocore.config import Config

router = APIRouter(tags=["Attachment"], dependencies=[Depends(verify_token)])


@router.post("/upload-url", response_model=dict)
async def get_presigned_url_for_upload(
    file_name: str,
    content_type: str,
    settings: Annotated[Settings, Depends(get_settings)],
    attachment_repo: Annotated[AttachmentRepository, Depends(get_attachment_repository)],
):
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    # Генерируем уникальный идентификатор для файла
    attachment_id = UUID(os.urandom(16).hex())
    object_name = f"attachments/{attachment_id}/{file_name}"

    # Сохраняем информацию о вложении в базу данных
    attachment_data = attachment_repo.create_attachment(attachment_id, object_name, content_type)

    # Создаем presigned URL для загрузки файла
    session = aioboto3.Session()
    config = Config(signature_version='s3v4')  # Создаем конфигурацию с указанием версии подписи

    async with session.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        config=config
    ) as s3_client:
        try:
            response = await s3_client.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.minio_bucket,
                    "Key": object_name,
                },
                ExpiresIn=3600,  # URL действителен в течение 1 часа
            )
        except ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))

    return {"upload_url": response, "attachment": attachment_data}

# TBD
# @router.get("/attachments/{attachment_id}/download-url", response_model=dict)
# async def get_presigned_url_for_download(
#     attachment_id: UUID,
#     settings: Annotated[Settings, Depends(get_settings)],
#     attachment_repo: Annotated[AttachmentRepository, Depends(get_attachment_repository)],
#     user: Annotated[UUID, Depends(verify_token)],  # Предполагается, что есть функция get_current_user_id для получения ID текущего пользователя
# ):
#     # Получаем информацию о вложении из базы данных
#     attachment = attachment_repo.get_attachment_by_id(attachment_id)
#     if not attachment:
#         raise HTTPException(status_code=404, detail="Attachment not found")

#     # Проверяем, имеет ли текущий пользователь право на скачивание вложения
#     if attachment != user_id and not await only_admin(user_id):
#         raise HTTPException(status_code=403, detail="Forbidden")

#     # Создаем presigned URL для скачивания файла
#     async with aioboto3.client(
#         "s3",
#         endpoint_url=settings.minio_endpoint,
#         aws_access_key_id=settings.minio_access_key,
#         aws_secret_access_key=settings.minio_secret_key,
#         region_name=settings.minio_region,
#     ) as s3_client:
#         try:
#             response = await s3_client.generate_presigned_url(
#                 "get_object",
#                 Params={
#                     "Bucket": settings.minio_bucket,
#                     "Key": attachment.object_name,
#                 },
#                 ExpiresIn=3600,  # URL действителен в течение 1 часа
#             )
#         except ClientError as e:
#             raise HTTPException(status_code=500, detail=str(e))

#     return {"download_url": response}


# @router.delete("/attachments/{attachment_id}", status_code=status.HTTP_200_OK)
# async def delete_attachment(
#     attachment_id: UUID,
#     settings: Annotated[Settings, Depends(get_settings)],
#     attachment_repo: Annotated[AttachmentRepository, Depends(get_attachment_repository)],
#     user: Annotated[UUID, Depends(verify_token)],  # Предполагается, что есть функция get_current_user_id для получения ID текущего пользователя
# ):
#     # Получаем информацию о вложении из базы данных
#     attachment = attachment_repo.get_attachment_by_id(attachment_id)
#     if not attachment:
#         raise HTTPException(status_code=404, detail="Attachment not found")

#     # Проверяем, имеет ли текущий пользователь право на удаление вложения
#     if attachment.user_id != user_id and not await only_admin(user_id):
#         raise HTTPException(status_code=403, detail="Forbidden")

#     # Удаляем файл из MinIO
#     async with aioboto3.client(
#         "s3",
#         endpoint_url=settings.minio_endpoint,
#         aws_access_key_id=settings.minio_access_key,
#         aws_secret_access_key=settings.minio_secret_key,
#         region_name=settings.minio_region,
#     ) as s3_client:
#         try:
#             await s3_client.delete_object(
#                 Bucket=settings.minio_bucket,
#                 Key=attachment.object_name,
#             )
#         except ClientError as e:
#             raise HTTPException(status_code=500, detail=str(e))

#     # Удаляем информацию о вложении из базы данных
#     attachment_repo.delete_attachment(attachment_id)

#     return {"message": "Attachment deleted successfully"}
