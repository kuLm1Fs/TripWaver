"""全局异常处理"""

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = structlog.get_logger(__name__)


# 字段中文名映射
FIELD_LABELS: dict[str, str] = {
    "destination": "目的地",
    "days": "游玩天数",
    "interests": "兴趣偏好",
    "range_mode": "范围模式",
    "range_minutes": "可达时间",
    "latitude": "纬度",
    "longitude": "经度",
    "address": "地址",
    "custom_tags": "自定义标签",
}


def _humanize_error(error: dict) -> tuple[str, str]:
    """将 Pydantic 错误转为 (字段名, 友好消息)。"""
    field = str(error["loc"][-1])
    label = FIELD_LABELS.get(field, field)
    err_type: str = error.get("type", "")
    ctx: dict = error.get("ctx", {})
    msg: str = error["msg"]

    # 基于 error type 判断
    if err_type in ("missing", "string_type"):
        friendly = f"{label}不能为空"
    elif err_type == "string_too_short":
        friendly = f"{label}不能为空"
    elif err_type == "int_too_small":
        limit = ctx.get("ge") or ctx.get("gt")
        friendly = f"{label}不能小于{limit}"
    elif err_type == "int_too_large":
        limit = ctx.get("le") or ctx.get("lt")
        if limit == 30:
            friendly = f"{label}必须在 1-30 天之间"
        elif limit == 120:
            friendly = f"{label}必须在 5-120 分钟之间"
        else:
            friendly = f"{label}不能超过{limit}"
    elif err_type == "list_too_long":
        friendly = f"{label}最多{ctx.get('max_length', 10)}个"
    elif err_type == "enum":
        friendly = f"{label}可选值不正确"
    elif "less than or equal" in msg.lower() and ctx:
        # 兜底：解析 ctx 中的 limit
        limit = ctx.get("le") or ctx.get("lt")
        if limit:
            friendly = f"{label}不能超过{limit}"
        else:
            friendly = msg
    elif "greater than or equal" in msg.lower() and ctx:
        limit = ctx.get("ge") or ctx.get("gt")
        if limit:
            friendly = f"{label}不能小于{limit}"
        else:
            friendly = msg
    else:
        friendly = msg

    return field, friendly


def register_error_handlers(app: FastAPI) -> None:
    """注册全局异常处理器"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        log.warning("http_error", status=exc.status_code, detail=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc.detail)},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        # 转换为 field → friendly message
        field_errors: dict[str, str] = {}
        for error in errors:
            field, friendly = _humanize_error(error)
            field_errors[field] = friendly

        log.warning("validation_error", errors=field_errors)
        return JSONResponse(
            status_code=422,
            content={"error": "请求参数校验失败", "detail": field_errors},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        log.error("unhandled_exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误"},
        )
