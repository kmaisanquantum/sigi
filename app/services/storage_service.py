from minio import Minio
from minio.error import S3Error
from datetime import timedelta
import io, uuid
from PIL import Image

def get_minio_client(settings) -> Minio:
    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

def ensure_bucket(client: Minio, bucket: str):
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

def upload_incident_photo(
    file_bytes: bytes,
    original_filename: str,
    mime_type: str,
    settings,
    max_dimension: int = 2048,
) -> dict:
    """
    Compress, strip EXIF (privacy), upload to MinIO.
    Returns storage key + file size.
    """
    client = get_minio_client(settings)
    ensure_bucket(client, settings.minio_bucket)

    # Resize and strip EXIF for privacy / bandwidth
    img = Image.open(io.BytesIO(file_bytes))
    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    # Strip EXIF by re-saving without it
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))

    buf = io.BytesIO()
    fmt = "JPEG" if mime_type == "image/jpeg" else "PNG"
    clean.save(buf, format=fmt, optimize=True, quality=82)
    buf.seek(0)
    processed = buf.read()

    storage_key = f"incidents/{uuid.uuid4()}/{original_filename}"
    client.put_object(
        settings.minio_bucket,
        storage_key,
        io.BytesIO(processed),
        length=len(processed),
        content_type=mime_type,
    )
    return {"storage_key": storage_key, "file_size_bytes": len(processed)}

def get_presigned_url(storage_key: str, settings, expires_hours: int = 4) -> str:
    client = get_minio_client(settings)
    return client.presigned_get_object(
        settings.minio_bucket,
        storage_key,
        expires=timedelta(hours=expires_hours),
    )
