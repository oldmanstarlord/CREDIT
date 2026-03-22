"""
AWS S3 Service for document storage and retrieval
Handles file uploads, downloads, and presigned URLs
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import logging
from pathlib import Path
import mimetypes

from app.core.config import settings

logger = logging.getLogger(__name__)


class AWSService:
    """Service for AWS S3 operations"""

    def __init__(self):
        self.s3_enabled = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
        if self.s3_enabled:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION or 'ap-south-1'
            )
            self.bucket_name = settings.S3_BUCKET_NAME
        else:
            logger.warning("AWS credentials not configured. S3 operations will be disabled.")
            self.s3_client = None
            self.bucket_name = None

    def upload_file(
        self,
        file_obj: BinaryIO,
        s3_key: str,
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload file to S3
        
        Args:
            file_obj: File object to upload
            s3_key: S3 object key (path)
            content_type: MIME type of file
            
        Returns:
            dict with s3_path and success status
        """
        if not self.s3_enabled:
            logger.warning("S3 not enabled. Skipping upload.")
            return {
                "success": False,
                "error": "S3 not configured",
                "s3_path": None
            }

        try:
            # Guess content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(s3_key)
                content_type = content_type or 'application/octet-stream'

            # Upload file
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'ServerSideEncryption': 'AES256'
                }
            )

            s3_path = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"File uploaded successfully to {s3_path}")

            return {
                "success": True,
                "s3_path": s3_path,
                "bucket": self.bucket_name,
                "key": s3_key
            }

        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "s3_path": None
            }

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download file from S3 to local path
        
        Args:
            s3_key: S3 object key
            local_path: Local file path to save
            
        Returns:
            bool indicating success
        """
        if not self.s3_enabled:
            logger.warning("S3 not enabled. Cannot download.")
            return False

        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            logger.info(f"File downloaded from S3: {s3_key} -> {local_path}")
            return True

        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False

    def get_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600,
        operation: str = 'get_object'
    ) -> Optional[str]:
        """
        Generate presigned URL for S3 object
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default 1 hour)
            operation: S3 operation (get_object or put_object)
            
        Returns:
            Presigned URL string or None
        """
        if not self.s3_enabled:
            logger.warning("S3 not enabled. Cannot generate presigned URL.")
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                operation,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool indicating success
        """
        if not self.s3_enabled:
            logger.warning("S3 not enabled. Cannot delete.")
            return False

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"File deleted from S3: {s3_key}")
            return True

        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False

    def file_exists(self, s3_key: str) -> bool:
        """
        Check if file exists in S3
        
        Args:
            s3_key: S3 object key
            
        Returns:
            bool indicating if file exists
        """
        if not self.s3_enabled:
            return False

        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True

        except ClientError:
            return False

    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list:
        """
        List files in S3 bucket with given prefix
        
        Args:
            prefix: S3 key prefix to filter
            max_keys: Maximum number of keys to return
            
        Returns:
            List of S3 object keys
        """
        if not self.s3_enabled:
            return []

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]

        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []
