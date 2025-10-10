import json

import aioboto3
from fastapi import APIRouter, HTTPException

from app.clients.cache_client import get_cache_client
from app.clients.opensearch_client import get_opensearch_client
from app.core.logger import logger
from app.core.settings import settings
from app.schemas.query import (
    ChangeDetection,
    ComparisonRequest,
    ComparisonResponse,
    ImageInfo,
    QueryRequest,
    QueryResponse,
)
from app.services.embedding_service import get_embedding_service
from app.services.langchain_service import get_langchain_service
from app.services.vlm_service import get_vlm_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest) -> QueryResponse:
    """Handle queries about project images using VLM and vector search."""
    try:
        cache = get_cache_client()
        cache_key = f"query:{payload.project_id}:{hash(payload.question)}"

        # Check cache
        cached = cache.get(cache_key)
        if cached:
            logger.info("query_cache_hit", project_id=payload.project_id)
            return QueryResponse(**json.loads(cached))

        logger.info("query_processing", project_id=payload.project_id, question=payload.question)

        opensearch = get_opensearch_client()
        langchain_service = get_langchain_service()
        embedding_service = get_embedding_service()
        vlm_service = get_vlm_service()

        # Handle comparison queries
        if payload.comparison_sequences and len(payload.comparison_sequences) >= 2:
            return await _handle_comparison_query(
                payload.project_id,
                payload.comparison_sequences[0],
                payload.comparison_sequences[1],
                payload.question,
            )

        # Handle specific sequence query
        if payload.sequence_number is not None:
            images = await opensearch.get_images_by_project(payload.project_id)
            target_image = next((img for img in images if img["sequence_number"] == payload.sequence_number), None)

            if not target_image:
                raise HTTPException(status_code=404, detail="Image not found")

            # Download image and query VLM
            session = aioboto3.Session()
            async with session.client("s3", endpoint_url=settings.aws_endpoint, region_name="us-east-1") as s3:
                response = await s3.get_object(Bucket=settings.s3_bucket, Key=target_image["s3_key"])
                image_data = await response["Body"].read()

            answer = await vlm_service.answer_question(image_data, payload.question)

            return QueryResponse(
                summary=answer,
                details=f"Answer for image at sequence {payload.sequence_number}",
                relevant_images=[
                    ImageInfo(
                        image_id=target_image["image_id"],
                        sequence_number=target_image["sequence_number"],
                        s3_key=target_image["s3_key"],
                        filename=target_image["filename"],
                        description=target_image.get("text_description", ""),
                    )
                ],
                confidence=0.85,
            )

        # Handle general project queries with vector search
        if payload.use_vector_search:
            # Generate query embedding
            query_embedding = await embedding_service.generate_text_embedding(payload.question)

            # Search similar images
            search_results = await opensearch.search_similar_images(
                project_id=payload.project_id, query_embedding=query_embedding, k=5
            )

            image_descriptions = [result["data"] for result in search_results]
        else:
            # Get all project images
            image_descriptions = await opensearch.get_images_by_project(payload.project_id, limit=10)

        # Use LangChain to structure response
        structured_response = await langchain_service.structure_query_response(
            context=f"Project {payload.project_id}", question=payload.question, image_descriptions=image_descriptions
        )

        # Convert to response format
        relevant_images = [
            ImageInfo(
                image_id=img.get("image_id", ""),
                sequence_number=img.get("sequence_number", 0),
                s3_key=img.get("s3_key", ""),
                filename=img.get("filename", ""),
                description=img.get("text_description", ""),
                relevance_score=img.get("score"),
            )
            for img in image_descriptions[:5]
        ]

        response = QueryResponse(
            summary=structured_response.get("summary", ""),
            details=structured_response.get("details", ""),
            relevant_images=relevant_images,
            confidence=structured_response.get("confidence", 0.8),
            metadata={"images_searched": len(image_descriptions)},
        )

        # Cache the response
        cache.set(cache_key, response.model_dump_json(), expire=settings.cache_ttl)
        logger.info("query_completed", project_id=payload.project_id, confidence=response.confidence)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("query_failed", project_id=payload.project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


async def _handle_comparison_query(
    project_id: str, sequence_1: int, sequence_2: int, question: str
) -> QueryResponse:
    """Handle image comparison queries."""
    opensearch = get_opensearch_client()
    langchain_service = get_langchain_service()

    comparison_data = await opensearch.compare_images(project_id, sequence_1, sequence_2)

    if not comparison_data:
        raise HTTPException(status_code=404, detail="Images not found for comparison")

    # Use LangChain to structure comparison
    structured_comparison = await langchain_service.structure_comparison_response(
        image_1_desc=comparison_data["image_1"].get("text_description", ""),
        image_2_desc=comparison_data["image_2"].get("text_description", ""),
        question=question,
    )

    # Convert changes to ChangeDetection objects
    changes = [
        ChangeDetection(type=change["type"], description=change["description"], confidence=change.get("confidence"))
        for change in structured_comparison.get("changes", [])
    ]

    relevant_images = [
        ImageInfo(
            image_id=comparison_data["image_1"]["image_id"],
            sequence_number=comparison_data["image_1"]["sequence_number"],
            s3_key=comparison_data["image_1"]["s3_key"],
            filename=comparison_data["image_1"]["filename"],
            description=comparison_data["image_1"].get("text_description", ""),
        ),
        ImageInfo(
            image_id=comparison_data["image_2"]["image_id"],
            sequence_number=comparison_data["image_2"]["sequence_number"],
            s3_key=comparison_data["image_2"]["s3_key"],
            filename=comparison_data["image_2"]["filename"],
            description=comparison_data["image_2"].get("text_description", ""),
        ),
    ]

    return QueryResponse(
        summary=structured_comparison.get("summary", ""),
        details=f"Comparison between sequences {sequence_1} and {sequence_2}",
        changes=changes,
        relevant_images=relevant_images,
        confidence=structured_comparison.get("confidence", 0.85),
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_images(payload: ComparisonRequest) -> ComparisonResponse:
    """Compare two images directly."""
    try:
        cache = get_cache_client()
        cache_key = f"comparison:{payload.project_id}:{payload.sequence_1}:{payload.sequence_2}"

        # Check cache
        cached = cache.get(cache_key)
        if cached:
            logger.info("comparison_cache_hit", project_id=payload.project_id)
            return ComparisonResponse(**json.loads(cached))

        opensearch = get_opensearch_client()
        langchain_service = get_langchain_service()

        comparison_data = await opensearch.compare_images(payload.project_id, payload.sequence_1, payload.sequence_2)

        if not comparison_data:
            raise HTTPException(status_code=404, detail="Images not found")

        structured_comparison = await langchain_service.structure_comparison_response(
            image_1_desc=comparison_data["image_1"].get("text_description", ""),
            image_2_desc=comparison_data["image_2"].get("text_description", ""),
            question=payload.question or "What are the differences?",
        )

        changes = [
            ChangeDetection(
                type=change["type"], description=change["description"], confidence=change.get("confidence")
            )
            for change in structured_comparison.get("changes", [])
        ]

        response = ComparisonResponse(
            image_1=ImageInfo(
                image_id=comparison_data["image_1"]["image_id"],
                sequence_number=comparison_data["image_1"]["sequence_number"],
                s3_key=comparison_data["image_1"]["s3_key"],
                filename=comparison_data["image_1"]["filename"],
                description=comparison_data["image_1"].get("text_description", ""),
            ),
            image_2=ImageInfo(
                image_id=comparison_data["image_2"]["image_id"],
                sequence_number=comparison_data["image_2"]["sequence_number"],
                s3_key=comparison_data["image_2"]["s3_key"],
                filename=comparison_data["image_2"]["filename"],
                description=comparison_data["image_2"].get("text_description", ""),
            ),
            changes=changes,
            summary=structured_comparison.get("summary", ""),
            confidence=structured_comparison.get("confidence", 0.85),
        )

        # Cache the response
        cache.set(cache_key, response.model_dump_json(), expire=settings.cache_ttl)
        logger.info("comparison_completed", project_id=payload.project_id)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error("comparison_failed", project_id=payload.project_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
