from typing import Any

import aiohttp

from app.core.logger import logger
from app.core.settings import settings


async def ask_rag(payload: dict[str, Any]) -> dict[str, Any]:
    async with (
        aiohttp.ClientSession() as session,
        session.post(f"{settings.rag_service_url}/analyze", json=payload, timeout=60) as resp,
    ):
        data = await resp.json()
        logger.info("rag_response", status=resp.status)
        return data
