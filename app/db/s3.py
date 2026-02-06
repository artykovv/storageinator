import boto3
from botocore.exceptions import ClientError
from typing import Optional

from app.core.config import settings


class S3Client:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self.bucket_name = settings.s3_bucket_name
        self.public_url = settings.s3_public_url
        self.internal_url = settings.s3_endpoint_url

    def _make_public_url(self, url: str) -> str:
        """Replace internal URL with public URL for browser access."""
        return url.replace(self.internal_url, self.public_url)

    async def ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket_name)
            print(f"Created S3 bucket: {self.bucket_name}")

    def generate_presigned_put_url(
        self,
        key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for uploading a file."""
        url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket_name,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return self._make_public_url(url)

    def generate_presigned_get_url(
        self,
        key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None,
        content_disposition: str = "attachment",
    ) -> str:
        """Generate a presigned URL for downloading a file."""
        params = {
            "Bucket": self.bucket_name,
            "Key": key,
        }
        if filename:
            params["ResponseContentDisposition"] = f'{content_disposition}; filename="{filename}"'
        
        url = self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=expires_in,
        )
        return self._make_public_url(url)

    def check_object_exists(self, key: str) -> bool:
        """Check if an object exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def get_object_metadata(self, key: str) -> Optional[dict]:
        """Get object metadata from S3."""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                "content_length": response.get("ContentLength"),
                "content_type": response.get("ContentType"),
                "etag": response.get("ETag", "").strip('"'),
            }
        except ClientError:
            return None

    def delete_object(self, key: str) -> bool:
        """Delete an object from S3."""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False


# Singleton instance
s3_client = S3Client()


def get_s3_client() -> S3Client:
    """Get S3 client instance."""
    return s3_client
