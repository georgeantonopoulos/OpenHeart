"""
S3/MinIO Storage Integration.

Provides file upload, download (presigned URLs), and bucket management
for clinical note attachments.
"""

from app.integrations.storage.client import StorageClient, get_storage_client

__all__ = ["StorageClient", "get_storage_client"]
