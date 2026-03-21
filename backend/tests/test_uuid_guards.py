import pytest
from fastapi import HTTPException

from app.api.routes.applications import _uuid_or_400 as app_uuid_or_400
from app.api.routes.auth import _uuid_or_400 as auth_uuid_or_400


def test_uuid_guards_accept_valid_uuid() -> None:
    value = "11111111-2222-3333-4444-555555555555"
    assert str(app_uuid_or_400(value, "x")) == value
    assert str(auth_uuid_or_400(value, "x")) == value


def test_uuid_guards_reject_invalid_uuid() -> None:
    with pytest.raises(HTTPException):
        app_uuid_or_400("bad-uuid", "x")
    with pytest.raises(HTTPException):
        auth_uuid_or_400("bad-uuid", "x")
