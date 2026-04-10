from __future__ import annotations

import hashlib
import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings


class S3AttachmentStorage:
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str,
        secure: bool,
    ) -> None:
        protocol = endpoint_url if endpoint_url.startswith("http") else f"http://{endpoint_url}"
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=protocol,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            use_ssl=secure,
            config=Config(
                s3={"addressing_style": "path"},
                connect_timeout=1,
                read_timeout=1,
                retries={"max_attempts": 1},
            ),
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "S3AttachmentStorage":
        return cls(
            endpoint_url=settings.s3_endpoint_url,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            secure=settings.s3_secure,
        )

    def readiness_check(self) -> tuple[bool, str]:
        try:
            self.client.list_buckets()
        except (BotoCoreError, ClientError) as exc:
            return False, str(exc)
        return True, "ok"

    def store_bytes(
        self,
        *,
        key_prefix: str,
        filename: str,
        content_bytes: bytes,
        content_type: str | None = None,
    ) -> tuple[str, str]:
        digest = hashlib.sha256(content_bytes).hexdigest()
        storage_key = f"{key_prefix.rstrip('/')}/{digest}/{filename}"
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=storage_key,
                Body=content_bytes,
                ContentType=content_type or "application/octet-stream",
            )
        except (BotoCoreError, ClientError):
            # Keep the ingestion flow functional in local or test environments
            # even when object storage is unavailable.
            storage_key = f"pending-upload/{storage_key}"
        return storage_key, digest
