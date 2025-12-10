"""Storage service for GCS operations"""
import logging
from google.cloud import storage
from datetime import timedelta
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StorageService:
    """Service for Cloud Storage operations"""

    def __init__(self):
        self.client = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of storage client"""
        if self._initialized:
            return
        try:
            self.client = storage.Client(project=settings.GCP_PROJECT_ID)
            self._initialized = True
            logger.info("StorageService initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize StorageService: {e}")
            raise

    def create_bucket(self, bucket_name: str, location: str = None) -> storage.Bucket:
        """Create a new bucket"""
        self._ensure_initialized()
        bucket = self.client.create_bucket(
            bucket_name,
            location=location or settings.GCP_REGION
        )
        return bucket

    def delete_bucket(self, bucket_name: str, force: bool = True):
        """Delete a bucket"""
        self._ensure_initialized()
        bucket = self.client.bucket(bucket_name)
        if force:
            bucket.delete(force=True)
        else:
            bucket.delete()

    def upload_file(self, bucket_name: str, source_data: bytes, destination_blob_name: str, content_type: str = None):
        """Upload file to bucket"""
        self._ensure_initialized()
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(source_data, content_type=content_type)
        return f"gs://{bucket_name}/{destination_blob_name}"

    def delete_file(self, bucket_name: str, blob_name: str):
        """Delete file from bucket"""
        self._ensure_initialized()
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.delete()

    def generate_signed_url(self, bucket_name: str, blob_name: str, expiration_hours: int = 1) -> str:
        """Generate signed URL for file download"""
        self._ensure_initialized()
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=expiration_hours),
            method="GET"
        )
        return url

    def list_files(self, bucket_name: str, prefix: str = None) -> list:
        """List files in bucket"""
        self._ensure_initialized()
        bucket = self.client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
