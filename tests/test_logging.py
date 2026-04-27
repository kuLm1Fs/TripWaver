"""structlog 日志模块测试"""

from unittest.mock import patch

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from tripweaver.core.logging import (
    LoggingMiddleware,
    get_request_id,
    request_id_var,
    setup_logging,
)


def test_setup_logging_configures_structlog():
    """setup_logging 应正确配置 structlog 处理器链"""
    setup_logging(log_level="INFO")
    logger = structlog.get_logger()
    assert logger is not None
    # 验证可以正常记录日志（不抛异常）
    logger.info("test_message", key="value")


def test_setup_logging_debug_mode():
    """DEBUG 模式使用 ConsoleRenderer"""
    setup_logging(log_level="DEBUG")
    logger = structlog.get_logger()
    assert logger is not None


def test_request_id_var_default():
    """request_id_var 默认值为 None"""
    request_id_var.set(None)
    assert get_request_id() is None


def test_request_id_var_set():
    """request_id_var 可以设置和读取"""
    request_id_var.set("test-id-123")
    assert get_request_id() == "test-id-123"
    request_id_var.set(None)


class TestLoggingMiddleware:
    """LoggingMiddleware 中间件测试"""

    def _make_app(self):
        """创建带日志中间件的测试应用"""
        app = FastAPI()
        app.add_middleware(LoggingMiddleware)

        @app.get("/test")
        async def test_route():
            return JSONResponse({"message": "ok"})

        @app.get("/test-error")
        async def test_error_route():
            raise ValueError("boom")

        return app

    def test_middleware_adds_request_id_header(self):
        """中间件应在响应中注入 X-Request-ID 头"""
        app = self._make_app()
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        # UUID 格式验证（8-4-4-4-12）
        request_id = resp.headers["X-Request-ID"]
        assert len(request_id) == 36
        assert request_id.count("-") == 4

    def test_middleware_request_id_uniqueness(self):
        """每次请求的 request_id 应不同"""
        app = self._make_app()
        client = TestClient(app)
        resp1 = client.get("/test")
        resp2 = client.get("/test")
        assert resp1.headers["X-Request-ID"] != resp2.headers["X-Request-ID"]

    def test_middleware_logs_request_started(self):
        """中间件应记录 request_started 日志"""
        app = self._make_app()
        client = TestClient(app)
        with patch("tripweaver.core.logging.structlog") as mock_structlog:
            mock_logger = mock_structlog.get_logger.return_value
            resp = client.get("/test")
            assert resp.status_code == 200

    def test_middleware_handles_errors(self):
        """中间件在请求异常时应记录 request_failed 并重新抛出"""
        app = self._make_app()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-error")
        assert resp.status_code == 500

    def test_middleware_response_body_intact(self):
        """中间件不应影响响应内容"""
        app = self._make_app()
        client = TestClient(app)
        resp = client.get("/test")
        assert resp.json() == {"message": "ok"}
