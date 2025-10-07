from typing import Any

from fastapi.responses import JSONResponse


def json_ok(data: Any) -> JSONResponse:
    return JSONResponse(status_code=200, content=data)
