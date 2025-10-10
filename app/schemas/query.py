from typing import Any, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for querying images in a project."""

    project_id: str = Field(..., description="Project ID to query")
    question: str = Field(..., description="Question about the images")
    sequence_number: Optional[int] = Field(None, description="Specific image sequence number")
    comparison_sequences: Optional[list[int]] = Field(None, description="Sequences to compare")
    use_vector_search: bool = Field(True, description="Use vector similarity search")


class ImageInfo(BaseModel):
    """Information about an image in the response."""

    image_id: str
    sequence_number: int
    s3_key: str
    filename: str
    description: str
    relevance_score: Optional[float] = None


class ChangeDetection(BaseModel):
    """Detected change between images."""

    type: str = Field(..., description="Type of change: addition, removal, modification, similar")
    description: str
    confidence: Optional[float] = None


class QueryResponse(BaseModel):
    """Response model for image queries."""

    summary: str = Field(..., description="Summary of the answer")
    details: str = Field("", description="Detailed explanation")
    changes: list[ChangeDetection] = Field(default_factory=list, description="Detected changes")
    relevant_images: list[ImageInfo] = Field(default_factory=list, description="Relevant images")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ComparisonRequest(BaseModel):
    """Request model for comparing two images."""

    project_id: str
    sequence_1: int
    sequence_2: int
    question: Optional[str] = "What are the differences between these images?"


class ComparisonResponse(BaseModel):
    """Response model for image comparison."""

    image_1: ImageInfo
    image_2: ImageInfo
    changes: list[ChangeDetection]
    summary: str
    confidence: float
