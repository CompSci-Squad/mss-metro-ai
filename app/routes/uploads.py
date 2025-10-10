import ulid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.clients.opensearch_client import get_opensearch_client
from app.clients.s3_client import upload_image
from app.core.logger import logger
from app.schemas.upload import UploadResponse
from app.workers.image_processing import process_image_task

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_file(project_id: str = Form(...), file: UploadFile = File(...)) -> UploadResponse:
    """Upload an image to a project with chronological sequencing."""
    try:
        # Generate unique image ID
        image_id = str(ulid.ULID())
        
        # Read image data
        image_data = await file.read()
        
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Get OpenSearch client for sequence management
        opensearch = get_opensearch_client()
        
        # Get current sequence count for project
        current_sequence = await opensearch.get_sequence_count(project_id)
        sequence_number = current_sequence + 1

        # Upload to S3
        result = await upload_image(project_id, image_data, file.filename or "image.jpg")
        s3_key = result["s3_key"]

        logger.info(
            "image_uploaded_to_s3",
            project_id=project_id,
            image_id=image_id,
            s3_key=s3_key,
            sequence_number=sequence_number,
        )

        # Trigger async Celery task for processing
        task = process_image_task.delay(
            project_id=project_id,
            image_id=image_id,
            s3_key=s3_key,
            sequence_number=sequence_number,
        )

        logger.info(
            "image_processing_task_created",
            project_id=project_id,
            image_id=image_id,
            task_id=task.id,
        )

        return UploadResponse(
            image_id=image_id,
            project_id=project_id,
            s3_key=s3_key,
            sequence_number=sequence_number,
            task_id=task.id,
            status="processing",
            upload_url=f"s3://{s3_key}",
        )

    except Exception as e:
        logger.error("upload_failed", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/projects/{project_id}/images")
async def list_project_images(project_id: str, limit: int = 100):
    """List all images for a project in chronological order."""
    try:
        opensearch = get_opensearch_client()
        images = await opensearch.get_images_by_project(project_id, limit=limit)
        
        logger.info("project_images_listed", project_id=project_id, count=len(images))
        
        return {"project_id": project_id, "images": images, "count": len(images)}

    except Exception as e:
        logger.error("list_images_failed", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/images/{image_id}")
async def get_image_details(image_id: str):
    """Get details of a specific image."""
    try:
        opensearch = get_opensearch_client()
        image = await opensearch.get_image_by_id(image_id)
        
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        logger.info("image_details_retrieved", image_id=image_id)
        
        return image

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_image_failed", image_id=image_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
