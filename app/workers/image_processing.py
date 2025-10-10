import asyncio
from typing import Any

import aioboto3

from app.celery_app import celery_app
from app.clients import cache, opensearch
from app.core.logger import logger
from app.core.settings import settings
from app.services.embedding_service import get_embedding_service
from app.services.vlm_service import get_vlm_service


@celery_app.task(name="process_image", bind=True, max_retries=3)
def process_image_task(self, project_id: str, image_id: str, s3_key: str, sequence_number: int) -> dict[str, Any]:
    """
    Celery task to process uploaded images asynchronously.
    Generates embeddings and captions, then stores in OpenSearch.
    """
    try:
        # Run async processing in event loop
        result = asyncio.run(_process_image_async(project_id, image_id, s3_key, sequence_number))
        logger.info("image_processing_completed", project_id=project_id, image_id=image_id)
        return result

    except Exception as e:
        logger.error("image_processing_failed", project_id=project_id, image_id=image_id, error=str(e))
        raise self.retry(exc=e, countdown=2**self.request.retries) from None


async def _process_image_async(project_id: str, image_id: str, s3_key: str, sequence_number: int) -> dict[str, Any]:
    """Async image processing logic."""
    embedding_service = get_embedding_service()
    vlm_service = get_vlm_service()

    # Download image from S3
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.aws_endpoint,
        region_name="us-east-1",
    ) as s3:
        response = await s3.get_object(Bucket=settings.s3_bucket, Key=s3_key)
        image_data = await response["Body"].read()

    logger.info("image_downloaded_from_s3", s3_key=s3_key, size=len(image_data))

    # Check cache for embeddings
    cache_key = f"embedding:{image_id}"
    cached_embedding = cache.get(cache_key)

    if cached_embedding:
        logger.info("embedding_cache_hit", image_id=image_id)
        import json
        embedding = json.loads(cached_embedding)
    else:
        # Generate image embedding
        embedding = await embedding_service.generate_image_embedding(image_data)
        # Cache the embedding
        import json
        cache.set(cache_key, json.dumps(embedding), ttl=settings.cache_ttl)
        logger.info("embedding_cached", image_id=image_id)

    # Generate image caption using VLM
    caption_cache_key = f"caption:{image_id}"
    cached_caption = cache.get(caption_cache_key)

    if cached_caption:
        logger.info("caption_cache_hit", image_id=image_id)
        caption = cached_caption
    else:
        caption = await vlm_service.generate_caption(image_data)
        cache.set(caption_cache_key, caption, ttl=settings.cache_ttl)
        logger.info("caption_cached", image_id=image_id)

    # Extract filename from s3_key
    filename = s3_key.split("/")[-1]

    # Store in OpenSearch
    await opensearch.store_image(
        project_id=project_id,
        image_id=image_id,
        s3_key=s3_key,
        filename=filename,
        embedding=embedding,
        sequence_number=sequence_number,
        text_description=caption,
        metadata={"size_bytes": len(image_data)},
    )

    return {
        "status": "success",
        "project_id": project_id,
        "image_id": image_id,
        "caption": caption,
        "embedding_dimension": len(embedding),
        "sequence_number": sequence_number,
    }


@celery_app.task(name="compare_images_task", bind=True, max_retries=3)
def compare_images_task(
    self, project_id: str, sequence_1: int, sequence_2: int
) -> dict[str, Any]:
    """
    Celery task to compare two images from a project.
    """
    try:
        result = asyncio.run(_compare_images_async(project_id, sequence_1, sequence_2))
        logger.info("image_comparison_completed", project_id=project_id)
        return result

    except Exception as e:
        logger.error("image_comparison_failed", project_id=project_id, error=str(e))
        raise self.retry(exc=e, countdown=2**self.request.retries) from None


async def _compare_images_async(project_id: str, sequence_1: int, sequence_2: int) -> dict[str, Any]:
    """Async image comparison logic."""
    vlm_service = get_vlm_service()

    # Get images from OpenSearch
    image_1 = await opensearch.get_by_sequence(project_id, sequence_1)
    image_2 = await opensearch.get_by_sequence(project_id, sequence_2)

    if not image_1 or not image_2:
        return {"status": "error", "message": "Images not found"}

    # Download both images from S3
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.aws_endpoint,
        region_name="us-east-1",
    ) as s3:
        # Download image 1
        response_1 = await s3.get_object(
            Bucket=settings.s3_bucket, Key=image_1["s3_key"]
        )
        image_1_data = await response_1["Body"].read()

        # Download image 2
        response_2 = await s3.get_object(
            Bucket=settings.s3_bucket, Key=image_2["s3_key"]
        )
        image_2_data = await response_2["Body"].read()

    # Use VLM to compare
    comparison = await vlm_service.compare_images(image_1_data, image_2_data)

    return {
        "status": "success",
        "project_id": project_id,
        "image_1": {
            "sequence": sequence_1,
            "description": comparison["image_1_description"],
        },
        "image_2": {
            "sequence": sequence_2,
            "description": comparison["image_2_description"],
        },
        "comparison_summary": comparison["summary"],
    }
