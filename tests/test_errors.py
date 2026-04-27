"""全局异常处理测试"""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tripweaver.core.errors import register_error_handlers

app = FastAPI()
register_error_handlers(app)


@app.get("/http-error")
async def http_error():
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="资源不存在")


@app.get("/validation-error")
async def validation_error():
    from fastapi.exceptions import RequestValidationError
    raise RequestValidationError(
        [{"loc": ("body", "name"), "msg": "field required", "type": "value_error"}]
    )


@app.get("/unhandled-error")
async def unhandled_error():
    raise RuntimeError("something broke")


client = TestClient(app, raise_server_exceptions=False)


def test_http_exception_returns_standard_format():
    """HTTPException 应返回统一错误格式"""
    resp = client.get("/http-error")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["error"] == "资源不存在"


def test_validation_error_returns_422():
    """参数校验错误应返回 422 和统一格式"""
    resp = client.get("/validation-error")
    assert resp.status_code == 422
    data = resp.json()
    assert data["error"] == "请求参数校验失败"
    assert "detail" in data


def test_unhandled_exception_returns_500():
    """未处理异常应返回 500，不暴露内部信息"""
    resp = client.get("/unhandled-error")
    assert resp.status_code == 500
    data = resp.json()
    assert data["error"] == "服务器内部错误"
    assert "detail" not in data or "something broke" not in str(data)


def test_404_not_found():
    """访问不存在的路由应返回标准错误格式"""
    resp = client.get("/nonexistent")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
