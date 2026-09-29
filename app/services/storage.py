"""
Storage Service — AWS S3 operations.
Handles resume and generated document upload/download.
"""
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from app.core.config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


async def upload_file_to_s3(file_bytes: bytes, s3_key: str, content_type: str) -> str:
    """Upload bytes to S3. Returns the S3 key."""
    client = get_s3_client()
    client.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return s3_key


async def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a pre-signed URL for temporary file access."""
    client = get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn=expires_in,
    )
    return url


async def delete_s3_file(s3_key: str) -> None:
    """Delete a file from S3."""
    client = get_s3_client()
    try:
        client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
    except ClientError as e:
        pass   # Log but don't raise on delete errors
