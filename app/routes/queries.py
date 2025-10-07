from fastapi import APIRouter
from app.schemas.query import QueryRequest, QueryResponse
from app.clients.rag_client import ask_rag
from app.clients.cache_client import get_cache, set_cache
from app.core.logger import logger
import json

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest) -> QueryResponse:
    cache_key = f"query:{payload.project_id}:{hash(payload.question)}"

    cached = get_cache(cache_key)
    if cached:
        logger.info("query_cache_hit", project_id=payload.project_id)
        return QueryResponse(**json.loads(cached))

    logger.info("query_processing", project_id=payload.project_id)

    rag_response = await ask_rag(payload.dict())

    response = QueryResponse(
        summary=rag_response.get("summary", ""),
        changes=rag_response.get("changes", []),
        confidence=rag_response.get("confidence", 0.0),
    )

    set_cache(cache_key, response.model_dump_json(), expire=300)
    logger.info("query_completed", project_id=payload.project_id, confidence=response.confidence)

    return response
