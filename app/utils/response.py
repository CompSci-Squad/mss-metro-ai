from fastapi.responses import JSONResponse
from typing import Any


def json_ok(data: Any) -> JSONResponse:
    return JSONResponse(status_code=200, content=data)
