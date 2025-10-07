from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logger import logger
from app.routes import health, queries, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("api_service_started")
    yield
    logger.info("api_service_shutdown")


app = FastAPI(title="Image-Diff API", version="1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(uploads.router, prefix="/projects")
app.include_router(queries.router)
