"""structlog 结构化日志配置"""

import logging
import uuid
from contextvars import ContextVar
from time import perf_counter

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# 请求级别的上下文变量
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def setup_logging(log_level: str = "INFO") -> None:
    """配置 structlog，合并标准库日志"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer() if log_level == "DEBUG" else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_request_id() -> str | None:
    """获取当前请求ID"""
    return request_id_var.get()


class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件：注入 request_id，记录请求/响应信息和耗时"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        log = structlog.get_logger()
        log.info("request_started")

        start = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (perf_counter() - start) * 1000
            log.error("request_failed", duration_ms=round(duration_ms, 2))
            raise

        duration_ms = (perf_counter() - start) * 1000
        log.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers["X-Request-ID"] = request_id
        return response
