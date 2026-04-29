"""请求 body 大小限制中间件"""

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

log = structlog.get_logger(__name__)

# 最大请求体 1MB
MAX_BODY_SIZE = 1 * 1024 * 1024


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """限制请求 body 大小，防止大 payload 攻击。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > MAX_BODY_SIZE:
                log.warning("request_body_too_large", size=content_length, path=request.url.path)
                return JSONResponse(
                    status_code=413,
                    content={"error": f"请求体过大，最大 {MAX_BODY_SIZE // 1024 // 1024}MB"},
                )
        return await call_next(request)
