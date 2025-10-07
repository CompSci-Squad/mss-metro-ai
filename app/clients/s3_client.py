from typing import Any

import aioboto3

from app.core.settings import settings
from app.utils.helpers import calculate_md5, compress_image, generate_md5_key, generate_s3_key


async def upload_image(project_id: str, image_data: bytes, filename: str) -> dict[str, Any]:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    s3_key = generate_s3_key(project_id, extension)
    md5_key = generate_md5_key(s3_key)

    compressed_data = compress_image(image_data)
    md5_hash = calculate_md5(compressed_data)

    async with aioboto3.client("s3", endpoint_url=settings.aws_endpoint) as s3:
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=s3_key,
            Body=compressed_data,
            ContentType=f"image/{extension}",
            Metadata={"md5": md5_hash},
        )

        await s3.put_object(Bucket=settings.s3_bucket, Key=md5_key, Body=md5_hash.encode(), ContentType="text/plain")

    return {"s3_key": s3_key, "md5_key": md5_key, "md5_hash": md5_hash}


async def generate_presigned_url(filename: str, expires_in: int = 3600) -> dict[str, Any]:
    async with aioboto3.client("s3", endpoint_url=settings.aws_endpoint) as s3:
        url = await s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={"Bucket": settings.s3_bucket, "Key": filename},
            ExpiresIn=expires_in,
        )
    return {"upload_url": url, "s3_key": filename}
