import hashlib
from datetime import datetime
from io import BytesIO

from PIL import Image
from ulid import ULID


def generate_s3_key(project_id: str, extension: str = "jpg") -> str:
    now = datetime.utcnow()
    ulid = str(ULID())
    return f"{project_id}/year={now.year}/month={now.month:02d}/day={now.day:02d}/{ulid}.{extension}"


def generate_md5_key(s3_key: str) -> str:
    return f"{s3_key}.md5"


def compress_image(image_data: bytes, quality: int = 85, max_size: tuple[int, int] = (1920, 1080)) -> bytes:
    img = Image.open(BytesIO(image_data))

    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGB")

    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    output = BytesIO()
    img.save(output, format="JPEG", quality=quality, optimize=True)
    return output.getvalue()


def calculate_md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()
