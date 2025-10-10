"""S3 - funções simples para upload de imagens."""

import hashlib
from datetime import datetime
from io import BytesIO
from typing import Any

import aioboto3
from PIL import Image
from ulid import ULID

from app.core.settings import settings


def _generate_s3_key(project_id: str, extension: str = "jpg") -> str:
    """Gera chave S3 com particionamento temporal."""
    now = datetime.utcnow()
    ulid = str(ULID())
    return f"{project_id}/year={now.year}/month={now.month:02d}/day={now.day:02d}/{ulid}.{extension}"


def _compress_image(image_data: bytes, quality: int = 85) -> bytes:
    """Comprime imagem."""
    img = Image.open(BytesIO(image_data))
    
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")
    
    img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)
    
    output = BytesIO()
    img.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


def _calculate_md5(data: bytes) -> str:
    """Calcula hash MD5."""
    return hashlib.md5(data).hexdigest()


async def upload_image(project_id: str, image_data: bytes, filename: str) -> dict[str, Any]:
    """Faz upload de imagem para S3."""
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    s3_key = _generate_s3_key(project_id, extension)
    md5_key = f"{s3_key}.md5"
    
    compressed = _compress_image(image_data)
    md5_hash = _calculate_md5(compressed)
    
    session = aioboto3.Session()
    async with session.client("s3", endpoint_url=settings.aws_endpoint) as s3:
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=compressed,
            ContentType=f"image/{extension}",
            Metadata={"md5": md5_hash},
        )
        
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=md5_key,
            Body=md5_hash.encode(),
            ContentType="text/plain",
        )
    
    return {"s3_key": s3_key, "md5_key": md5_key, "md5_hash": md5_hash}


async def generate_presigned_url(filename: str, expires_in: int = 3600) -> dict[str, Any]:
    """Gera URL pré-assinada para upload."""
    session = aioboto3.Session()
    async with session.client("s3", endpoint_url=settings.aws_endpoint) as s3:
        url = await s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": settings.s3_bucket, "Key": filename},
            ExpiresIn=expires_in,
        )
    return {"upload_url": url, "s3_key": filename}
