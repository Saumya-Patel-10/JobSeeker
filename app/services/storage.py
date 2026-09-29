"""
Storage Service — AWS S3 operations with local filesystem fallback.
Handles resume and generated document upload/download.
"""
from pathlib import Path
from app.core.config import settings

try:
    import boto3
    from botocore.exceptions import ClientError
    from botocore.config import Config
except ImportError:
    boto3 = None
    ClientError = Exception
    Config = None

_s3_client = None


def get_s3_client():
    global _s3_client
    if boto3 is None:
        return None
    if _s3_client is None and settings.AWS_ACCESS_KEY_ID:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4") if Config else None,
        )
    return _s3_client


async def upload_file_to_s3(file_bytes: bytes, s3_key: str, content_type: str) -> str:
    """Upload bytes to S3 or local data directory as fallback. Returns the key/path."""
    client = get_s3_client()
    if client is not None:
        client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return s3_key
    
    # Local fallback
    local_path = Path("data/resumes") / s3_key
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(file_bytes)
    return str(local_path)


async def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a pre-signed URL or local file URL."""
    client = get_s3_client()
    if client is not None:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expires_in,
        )
    return f"/data/resumes/{s3_key}"


async def delete_s3_file(s3_key: str) -> None:
    """Delete a file from S3 or local filesystem."""
    client = get_s3_client()
    if client is not None:
        try:
            client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
        except ClientError:
            pass
        return
    local_path = Path("data/resumes") / s3_key
    if local_path.exists():
        local_path.unlink()
