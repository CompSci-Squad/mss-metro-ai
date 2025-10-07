from pydantic import BaseModel
from typing import List


class QueryRequest(BaseModel):
    project_id: str
    question: str


class QueryResponse(BaseModel):
    summary: str
    changes: List[str]
    confidence: float
