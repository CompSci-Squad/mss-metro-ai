from fastapi import APIRouter, File, Form, UploadFile

from app.clients.s3_client import upload_image
from app.clients.sqs_client import send_message
from app.core.logger import logger
from app.schemas.upload import UploadResponse

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(project_id: str = Form(...), file: UploadFile = File(...)) -> UploadResponse:
    image_data = await file.read()

    result = await upload_image(project_id, image_data, file.filename)

    await send_message(
        {"action": "upload", "project_id": project_id, "s3_key": result["s3_key"], "md5_key": result["md5_key"]}
    )

    logger.info("image_uploaded", project_id=project_id, s3_key=result["s3_key"])

    return UploadResponse(upload_url=f"s3://{result['s3_key']}", s3_key=result["s3_key"], md5_key=result["md5_key"])
