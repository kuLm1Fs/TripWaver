import pytest
from pydantic import ValidationError

from tripweaver.domain.schemas import (
    CandidatePlace,
    CreateShareRequest,
    CreateShareResponse,
    ItineraryDetailResponse,
    ItineraryItem,
    ItineraryRequest,
    ItineraryResponse,
    LoginRequest,
    LoginResponse,
    SendCodeRequest,
    VoteRequest,
    VoteResponse,
)


class TestItineraryRequest:
    def test_valid_request(self):
        req = ItineraryRequest(destination="Beijing", days=3, interests=["food"])
        assert req.destination == "Beijing"
        assert req.days == 3
        assert req.interests == ["food"]

    def test_default_values(self):
        req = ItineraryRequest(destination="Shanghai")
        assert req.days == 1
        assert req.interests == []

    def test_missing_destination(self):
        with pytest.raises(ValidationError):
            ItineraryRequest(days=2)

    def test_days_out_of_range(self):
        with pytest.raises(ValidationError):
            ItineraryRequest(destination="X", days=0)
        with pytest.raises(ValidationError):
            ItineraryRequest(destination="X", days=31)


class TestCandidatePlace:
    def test_minimal(self):
        p = CandidatePlace(name="Test", category="food", reason="good")
        assert p.name == "Test"
        assert p.address is None
        assert p.longitude is None
        assert p.latitude is None
        assert p.price is None
        assert p.business_hours is None
        assert p.tags == []

    def test_full_fields(self):
        p = CandidatePlace(
            name="Test Place",
            category="landmark",
            reason="famous",
            address="123 Main St",
            longitude=120.1234,
            latitude=30.5678,
            price="人均80元",
            business_hours="09:00-21:00",
            tags=["网红", "拍照"],
        )
        assert p.address == "123 Main St"
        assert p.longitude == 120.1234
        assert p.latitude == 30.5678
        assert p.tags == ["网红", "拍照"]


class TestItineraryItem:
    def test_valid_item(self):
        item = ItineraryItem(
            day=1,
            title="Day 1",
            summary="Visit museums",
            places=[CandidatePlace(name="M", category="museum", reason="nice")],
        )
        assert item.day == 1
        assert len(item.places) == 1


class TestItineraryResponse:
    def test_with_plan_options(self):
        resp = ItineraryResponse(
            destination="Chengdu",
            overview="3-day trip",
            items=[],
            plan_options=[{"plan_name": "test"}],
        )
        assert len(resp.plan_options) == 1
        assert resp.itinerary_id is None

    def test_default_plan_options(self):
        resp = ItineraryResponse(destination="X", overview="y", items=[])
        assert resp.plan_options == []


class TestAuthSchemas:
    def test_send_code_request(self):
        req = SendCodeRequest(phone="13800138000")
        assert req.phone == "13800138000"

    def test_invalid_phone(self):
        with pytest.raises(ValidationError):
            SendCodeRequest(phone="1234")

    def test_login_request(self):
        req = LoginRequest(phone="13800138000", code="123456")
        assert req.code == "123456"

    def test_login_response(self):
        resp = LoginResponse(access_token="tok", refresh_token="refresh", user_id=1, nickname="test", avatar=None)
        assert resp.token_type == "bearer"


class TestShareSchemas:
    def test_create_share_request(self):
        req = CreateShareRequest(itinerary_id=1)
        assert req.expire_days == 7

    def test_create_share_request_permanent(self):
        req = CreateShareRequest(itinerary_id=1, expire_days=0)
        assert req.expire_days == 0


class TestVoteSchemas:
    def test_vote_request(self):
        req = VoteRequest(itinerary_id=1, plan_index=0)
        assert req.plan_index == 0

    def test_vote_negative_index(self):
        with pytest.raises(ValidationError):
            VoteRequest(itinerary_id=1, plan_index=-1)
