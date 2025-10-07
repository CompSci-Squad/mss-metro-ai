from fastapi import APIRouter
from typing import Dict

router = APIRouter()


@router.get("/health", response_model=Dict[str, str])
async def health() -> Dict[str, str]:
    return {"status": "ok"}
