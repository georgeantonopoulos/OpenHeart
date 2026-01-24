"""
S3/MinIO storage client for file operations.

Uses boto3 with endpoint_url override for MinIO compatibility.
"""

import logging
from typing import Optional

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    """S3-compatible storage client for MinIO."""

    def __init__(self) -> None:
        s3_config = Config(signature_version="s3v4")
        # Internal client for uploads/deletes (uses Docker-internal endpoint)
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=s3_config,
        )
        # Public client for presigned URLs (uses browser-accessible endpoint)
        self._public_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_public_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=s3_config,
        )

    def upload_file(
        self,
        bucket: str,
        key: str,
        content: bytes,
        content_type: str,
    ) -> None:
        """Upload file bytes to S3/MinIO."""
        self._client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        logger.info(f"Uploaded {key} to {bucket} ({len(content)} bytes)")

    def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None,
    ) -> str:
        """Generate a presigned GET URL for file download."""
        params: dict = {"Bucket": bucket, "Key": key}
        if filename:
            params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'

        url: str = self._public_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        return url

    def delete_file(self, bucket: str, key: str) -> None:
        """Delete a file from S3/MinIO."""
        self._client.delete_object(Bucket=bucket, Key=key)
        logger.info(f"Deleted {key} from {bucket}")

    def ensure_bucket(self, bucket: str) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self._client.head_bucket(Bucket=bucket)
            logger.info(f"Bucket '{bucket}' exists")
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                self._client.create_bucket(Bucket=bucket)
                logger.info(f"Created bucket '{bucket}'")
            else:
                raise


# Module-level singleton
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get or create the storage client singleton."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client
