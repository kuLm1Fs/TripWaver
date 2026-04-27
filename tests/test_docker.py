"""Docker 容器化配置测试"""

from pathlib import Path

import yaml


def test_dockerfile_exists():
    """Dockerfile 应存在"""
    assert Path("Dockerfile").exists()


def test_dockerfile_uses_python312():
    """Dockerfile 应基于 Python 3.12"""
    content = Path("Dockerfile").read_text()
    assert "python:3.12" in content


def test_dockerfile_runs_alembic():
    """Dockerfile 启动时应执行 alembic upgrade head"""
    content = Path("Dockerfile").read_text()
    assert "alembic upgrade head" in content


def test_dockerfile_exposes_8000():
    """Dockerfile 应暴露 8000 端口"""
    content = Path("Dockerfile").read_text()
    assert "EXPOSE 8000" in content


def test_docker_compose_exists():
    """docker-compose.yml 应存在"""
    assert Path("docker-compose.yml").exists()


def test_docker_compose_services():
    """docker-compose.yml 应包含 app/postgres/redis 三个服务"""
    with open("docker-compose.yml") as f:
        config = yaml.safe_load(f)
    services = config["services"]
    assert "app" in services
    assert "postgres" in services
    assert "redis" in services


def test_docker_compose_postgres_config():
    """postgres 服务应配置健康检查和数据卷"""
    with open("docker-compose.yml") as f:
        config = yaml.safe_load(f)
    pg = config["services"]["postgres"]
    assert "healthcheck" in pg
    assert "volumes" in pg


def test_docker_compose_redis_config():
    """redis 服务应配置健康检查"""
    with open("docker-compose.yml") as f:
        config = yaml.safe_load(f)
    redis = config["services"]["redis"]
    assert "healthcheck" in redis


def test_docker_compose_app_depends_on():
    """app 服务应依赖 postgres 和 redis"""
    with open("docker-compose.yml") as f:
        config = yaml.safe_load(f)
    app = config["services"]["app"]
    assert "postgres" in app["depends_on"]
    assert "redis" in app["depends_on"]


def test_dockerignore_exists():
    """.dockerignore 应存在"""
    assert Path(".dockerignore").exists()


def test_dockerignore_excludes_venv():
    """.dockerignore 应排除 .venv"""
    content = Path(".dockerignore").read_text()
    assert ".venv" in content
