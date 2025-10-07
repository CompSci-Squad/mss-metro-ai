from fastapi import APIRouter

router = APIRouter()


@router.get("/health", response_model=dict[str, str])
async def health() -> dict[str, str]:
    return {"status": "ok"}
