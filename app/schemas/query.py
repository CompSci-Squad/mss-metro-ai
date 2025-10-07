from pydantic import BaseModel


class QueryRequest(BaseModel):
    project_id: str
    question: str


class QueryResponse(BaseModel):
    summary: str
    changes: list[str]
    confidence: float
