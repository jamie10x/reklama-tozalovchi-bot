from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_login_validates_token():
    from fastapi import Request

    from api.auth.router import LoginRequest, login

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    body = LoginRequest(telegram_id=12345, token="wrong-token")
    session = MagicMock()
    session.execute = AsyncMock()

    with patch("api.auth.router.load_api_config") as mock_config:
        mock_config.return_value.secret_key = "correct-secret"
        mock_config.return_value.session_ttl_hours = 24

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await login(body=body, request=req, session=session)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_officer_not_found():
    from fastapi import Request

    from api.auth.router import LoginRequest, login

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    body = LoginRequest(telegram_id=99999, token="valid-token")

    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)

    session = MagicMock()
    session.execute = AsyncMock(return_value=result_mock)

    with patch("api.auth.router.load_api_config") as mock_config:
        mock_config.return_value.secret_key = "valid-token"
        mock_config.return_value.session_ttl_hours = 24

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            await login(body=body, request=req, session=session)
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_success():
    from fastapi import Request

    from api.auth.router import LoginRequest, login

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    body = LoginRequest(telegram_id=12345, token="correct-secret")

    officer = MagicMock()
    officer.id = "officer-uuid"
    officer.telegram_id = 12345
    officer.role = "super_admin"
    officer.display_name = "Admin"

    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=officer)

    session = MagicMock()
    session.execute = AsyncMock(return_value=result_mock)
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()

    with patch("api.auth.router.load_api_config") as mock_config:
        mock_config.return_value.secret_key = "correct-secret"
        mock_config.return_value.session_ttl_hours = 24

        with patch("api.auth.router.secrets.token_urlsafe", return_value="raw-token-value"):
            response = await login(body=body, request=req, session=session)

    assert response.access_token == "raw-token-value"
    assert response.token_type == "bearer"
    assert response.officer["telegram_id"] == 12345

    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_get_current_officer_missing_header():
    from fastapi import HTTPException, Request

    from api.deps import get_current_officer

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    with pytest.raises(HTTPException) as exc:
        await get_current_officer(request=req, authorization=None, session=MagicMock())
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_officer_invalid_scheme():
    from fastapi import HTTPException, Request

    from api.deps import get_current_officer

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    with pytest.raises(HTTPException) as exc:
        await get_current_officer(request=req, authorization="Basic token", session=MagicMock())
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_officer_invalid_token():
    from fastapi import HTTPException, Request

    from api.deps import get_current_officer

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)

    session = MagicMock()
    session.execute = AsyncMock(return_value=result_mock)

    with pytest.raises(HTTPException) as exc:
        await get_current_officer(
            request=req, authorization="Bearer invalid-token", session=session
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_officer_success():
    from fastapi import Request

    from api.deps import get_current_officer

    req = MagicMock(spec=Request)
    req.state.req_id = "test-req-id"

    session_obj = MagicMock()
    session_obj.id = "session-uuid"
    session_obj.officer_id = "officer-uuid"

    result1 = MagicMock()
    result1.scalar_one_or_none = MagicMock(return_value=session_obj)

    officer = MagicMock()
    officer.id = "officer-uuid"
    officer.is_active = True

    result2 = MagicMock()
    result2.scalar_one_or_none = MagicMock(return_value=officer)

    session = MagicMock()
    session.execute = AsyncMock(side_effect=[result1, result2])

    officer_result = await get_current_officer(
        request=req, authorization="Bearer valid-token", session=session
    )

    assert officer_result is officer
