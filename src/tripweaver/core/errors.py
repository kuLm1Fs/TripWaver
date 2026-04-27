"""全局异常处理"""

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = structlog.get_logger()


class ErrorResponse(JSONResponse):
    """统一错误响应格式"""

    def __init__(self, status_code: int, message: str, detail: str | None = None):
        body = {"error": message}
        if detail:
            body["detail"] = detail
        super().__init__(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        log.warning("http_error", status=exc.status_code, detail=exc.detail)
        return ErrorResponse(
            status_code=exc.status_code,
            message=str(exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
        )
        log.warning("validation_error", detail=detail)
        return ErrorResponse(
            status_code=422,
            message="请求参数校验失败",
            detail=detail,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", error=str(exc), exc_info=True)
        return ErrorResponse(
            status_code=500,
            message="服务器内部错误",
        )
