"""CORS 中间件测试"""

from fastapi.testclient import TestClient

from tripweaver.main import app

client = TestClient(app)


def test_cors_preflight_request():
    """OPTIONS 预检请求应返回 CORS 头"""
    resp = client.options(
        "/api/v1/health" if False else "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_cors_allows_any_origin():
    """任意 Origin 应被允许"""
    resp = client.get(
        "/health",
        headers={"Origin": "http://example.com"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://example.com"


def test_cors_allows_post_method():
    """POST 方法应被允许"""
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code == 200
    allow_methods = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allow_methods


def test_cors_response_has_allow_credentials():
    """响应应包含 allow-credentials 头"""
    resp = client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert resp.headers.get("access-control-allow-credentials") == "true"
