"""Alembic 迁移配置测试"""

from pathlib import Path


def test_alembic_ini_exists():
    """alembic.ini 文件应存在"""
    assert Path("alembic.ini").exists()


def test_migrations_directory_structure():
    """migrations 目录结构应完整"""
    assert Path("migrations").is_dir()
    assert Path("migrations/env.py").exists()
    assert Path("migrations/script.py.mako").exists()
    assert Path("migrations/versions").is_dir()


def test_env_py_has_async_engine():
    """env.py 应使用 async engine"""
    content = Path("migrations/env.py").read_text()
    assert "async_engine_from_config" in content
    assert "run_async_migrations" in content


def test_env_py_imports_models():
    """env.py 应导入所有 models 以支持 autogenerate"""
    content = Path("migrations/env.py").read_text()
    assert "from tripweaver.models" in content


def test_env_py_reads_settings():
    """env.py 应从 Settings 读取数据库 URL"""
    content = Path("migrations/env.py").read_text()
    assert "get_settings" in content
    assert "settings.db_url" in content


def test_initial_migration_exists():
    """初始迁移脚本应存在且是根迁移"""
    versions = list(Path("migrations/versions").glob("*.py"))
    assert len(versions) >= 1
    # 检查是否有 down_revision = None 的初始迁移
    found = False
    for vf in versions:
        content = vf.read_text()
        if "down_revision = None" in content or "down_revision: Union[str, Sequence[str], None] = None" in content:
            found = True
            break
    assert found, "未找到初始迁移脚本（down_revision=None）"


def test_initial_migration_creates_tables():
    """初始迁移应创建所有表"""
    versions = list(Path("migrations/versions").glob("*.py"))
    for vf in versions:
        content = vf.read_text()
        if "down_revision" in content and "None" in content.split("down_revision")[1].split("\n")[0]:
            assert 'create_table' in content or 'op.create_table' in content
            assert '"users"' in content
            assert '"itineraries"' in content
            assert '"votes"' in content
            assert '"share_links"' in content
            break


def test_alembic_ini_url_commented():
    """alembic.ini 中的 sqlalchemy.url 应被注释（从 Settings 读取）"""
    content = Path("alembic.ini").read_text()
    # 确保没有未注释的 sqlalchemy.url
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("sqlalchemy.url"):
            assert stripped.startswith("#"), f"sqlalchemy.url 未注释: {line}"
