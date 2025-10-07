import aiohttp
from typing import Any
from app.core.settings import settings
from app.core.logger import logger


async def ask_rag(payload: dict[str, Any]) -> dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{settings.rag_service_url}/analyze", json=payload, timeout=60) as resp:
            data = await resp.json()
            logger.info("rag_response", status=resp.status)
            return data
