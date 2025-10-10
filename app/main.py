from fastapi import FastAPI

from app.routes import health, queries, uploads

app = FastAPI(
    title="MSS Metro AI API",
    version="1.0.0",
)

app.include_router(health.router, tags=["health"])
app.include_router(uploads.router, prefix="/projects", tags=["uploads"])
app.include_router(queries.router, tags=["queries"])
