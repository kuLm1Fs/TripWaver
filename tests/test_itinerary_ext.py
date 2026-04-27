from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tripweaver.core.config import get_settings
from tripweaver.core.db import get_db
from tripweaver.core.deps import get_current_user, get_current_user_id
from tripweaver.main import app
from tripweaver.models.itinerary import Itinerary
from tripweaver.models.share import ShareLink
from tripweaver.models.user import User
from tripweaver.models.vote import Vote

client = TestClient(app)


def make_user(user_id=1, nickname="测试用户"):
    user = MagicMock(spec=User)
    user.id = user_id
    user.nickname = nickname
    user.avatar = None
    return user


def make_itinerary(itinerary_id=1, creator_id=1, destination="Beijing", days=3):
    it = MagicMock(spec=Itinerary)
    it.id = itinerary_id
    it.creator_id = creator_id
    it.destination = destination
    it.days = days
    it.interests = ["food"]
    it.plan_results = [{"plan_name": "test"}]
    it.is_locked = False
    it.locked_at = None
    it.final_plan_index = None
    it.created_at = datetime(2024, 1, 1)
    it.updated_at = datetime(2024, 1, 1)
    return it


class FakeAsyncSession:
    """模拟异步数据库会话"""

    def __init__(self):
        self._objects = {}
        self._added = []

    def add(self, obj):
        self._added.append(obj)

    async def commit(self):
        for obj in self._added:
            if not getattr(obj, "id", None):
                obj.id = 1
            obj.created_at = datetime(2024, 1, 1)

    async def refresh(self, obj):
        pass

    async def get(self, model, pk):
        key = (model.__name__, pk)
        return self._objects.get(key)

    async def execute(self, stmt):
        """返回一个模拟的Result对象"""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        result.all.return_value = []
        return result

    def register(self, obj, model=None):
        """注册一个对象供get查询使用"""
        if model is None:
            model = type(obj)
        self._objects[(model.__name__, obj.id)] = obj


@pytest.fixture(autouse=True)
def use_mock_providers(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDER", "mock")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    get_settings.cache_clear()


@pytest.fixture()
def mock_session():
    session = FakeAsyncSession()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth_user(mock_session):
    user = make_user()
    mock_session.register(user, User)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_user_id] = lambda: user.id
    yield user
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ── 分享链接测试 ──


class TestShareLink:
    def test_create_share_link_success(self, mock_session, auth_user):
        """创建分享链接 - 行程存在且是当前用户创建的"""
        itinerary = make_itinerary(creator_id=auth_user.id)
        mock_session.register(itinerary, Itinerary)

        # mock execute 返回行程
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = itinerary
        mock_session.execute = AsyncMock(return_value=mock_result)

        resp = client.post(
            "/api/v1/itinerary/share",
            json={"itinerary_id": 1, "expire_days": 7},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "share_id" in data
        assert len(data["share_id"]) == 8
        assert data["share_url"].startswith("/share/")
        assert data["expire_at"] is not None

    def test_create_share_link_not_found(self, mock_session, auth_user):
        """创建分享链接 - 行程不存在"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        resp = client.post(
            "/api/v1/itinerary/share",
            json={"itinerary_id": 999, "expire_days": 7},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 404

    def test_create_share_link_permanent(self, mock_session, auth_user):
        """创建永久分享链接"""
        itinerary = make_itinerary(creator_id=auth_user.id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = itinerary
        mock_session.execute = AsyncMock(return_value=mock_result)

        resp = client.post(
            "/api/v1/itinerary/share",
            json={"itinerary_id": 1, "expire_days": 0},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 200
        assert resp.json()["expire_at"] is None


# ── 投票测试 ──


class TestVote:
    def test_vote_success(self, mock_session, auth_user):
        """投票成功"""
        itinerary = make_itinerary()
        mock_session.register(itinerary, Itinerary)

        # 第一次execute查行程 -> 返回行程；第二次查已有投票 -> None；第三次查统计 -> 结果
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # get itinerary - 通过 session.get 处理
                pass
            result.scalar_one_or_none.return_value = None
            result.all.return_value = [(0, 1)]
            return result

        mock_session.execute = mock_execute

        resp = client.post(
            "/api/v1/itinerary/vote",
            json={"itinerary_id": 1, "plan_index": 0},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["plan_index"] == 0

    def test_vote_itinerary_not_found(self, mock_session, auth_user):
        """投票 - 行程不存在"""
        # session.get 返回 None
        mock_session._objects = {}

        async def mock_execute(stmt):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock_session.execute = mock_execute

        resp = client.post(
            "/api/v1/itinerary/vote",
            json={"itinerary_id": 999, "plan_index": 0},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 404

    def test_vote_itinerary_locked(self, mock_session, auth_user):
        """投票 - 行程已锁定"""
        itinerary = make_itinerary()
        itinerary.is_locked = True
        mock_session.register(itinerary, Itinerary)

        resp = client.post(
            "/api/v1/itinerary/vote",
            json={"itinerary_id": 1, "plan_index": 0},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 400
        assert "锁定" in resp.json()["error"]

    def test_vote_duplicate(self, mock_session, auth_user):
        """重复投票"""
        itinerary = make_itinerary()
        mock_session.register(itinerary, Itinerary)

        existing_vote = MagicMock(spec=Vote)

        async def mock_execute(stmt):
            result = MagicMock()
            result.scalar_one_or_none.return_value = existing_vote
            return result

        mock_session.execute = mock_execute

        resp = client.post(
            "/api/v1/itinerary/vote",
            json={"itinerary_id": 1, "plan_index": 0},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 400
        assert "已经投过票" in resp.json()["error"]


# ── 锁定/解锁测试 ──


class TestLockItinerary:
    def test_lock_success(self, mock_session, auth_user):
        """锁定行程成功"""
        itinerary = make_itinerary(creator_id=auth_user.id)
        mock_session.register(itinerary, Itinerary)

        resp = client.post(
            "/api/v1/itinerary/lock",
            params={"itinerary_id": 1, "plan_index": 0, "action": "lock"},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_locked"] is True
        assert data["final_plan_index"] == 0

    def test_unlock_success(self, mock_session, auth_user):
        """解锁行程成功"""
        itinerary = make_itinerary(creator_id=auth_user.id)
        itinerary.is_locked = True
        itinerary.locked_at = datetime.utcnow()
        mock_session.register(itinerary, Itinerary)

        resp = client.post(
            "/api/v1/itinerary/lock",
            params={"itinerary_id": 1, "action": "unlock"},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_locked"] is False

    def test_lock_not_creator(self, mock_session, auth_user):
        """非创建者锁定失败"""
        itinerary = make_itinerary(creator_id=999)  # 不同用户
        mock_session.register(itinerary, Itinerary)

        resp = client.post(
            "/api/v1/itinerary/lock",
            params={"itinerary_id": 1, "action": "lock"},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 404

    def test_lock_invalid_action(self, mock_session, auth_user):
        """无效操作"""
        itinerary = make_itinerary(creator_id=auth_user.id)
        mock_session.register(itinerary, Itinerary)

        resp = client.post(
            "/api/v1/itinerary/lock",
            params={"itinerary_id": 1, "action": "delete"},
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 400


# ── 分享链接访问测试 ──


class TestGetByShareId:
    def test_share_link_not_found(self, mock_session, auth_user):
        """分享链接不存在"""
        async def mock_execute(stmt):
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        mock_session.execute = mock_execute

        resp = client.get(
            "/api/v1/itinerary/share/abc12345",
            headers={"Authorization": "Bearer faketoken"},
        )
        assert resp.status_code == 404
