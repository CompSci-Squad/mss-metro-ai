from typing import Optional

from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    """Request model for uploading images."""

    project_id: str = Field(..., description="Project ID for grouping images")
    filename: str = Field(..., description="Original filename")


class UploadResponse(BaseModel):
    """Response model after successful upload."""

    image_id: str = Field(..., description="Unique image identifier")
    project_id: str
    s3_key: str = Field(..., description="S3 storage key")
    sequence_number: int = Field(..., description="Chronological sequence number")
    task_id: Optional[str] = Field(None, description="Celery task ID for async processing")
    status: str = Field("processing", description="Upload status")
    upload_url: str = Field(..., description="S3 upload URL")
