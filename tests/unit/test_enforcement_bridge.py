from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.enforcement_bridge import EnforcementBridge


@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.delete_message = AsyncMock()
    bot.restrict_chat_member = AsyncMock()
    bot.ban_chat_member = AsyncMock()
    bot.get_chat_member = AsyncMock()
    return bot


@pytest.fixture
def bridge(mock_bot):
    return EnforcementBridge(bot=mock_bot)


@pytest.mark.asyncio
async def test_execute_delete_message_success(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "delete_message"
    action.target_chat_id = -100123
    action.target_message_id = 456
    action.target_user_id = None

    result = await bridge._execute_action(action)

    mock_bot.delete_message.assert_awaited_once_with(chat_id=-100123, message_id=456)
    assert result == {"deleted": True}


@pytest.mark.asyncio
async def test_execute_delete_message_missing_fields(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "delete_message"
    action.target_chat_id = None
    action.target_message_id = None

    result = await bridge._execute_action(action)

    mock_bot.delete_message.assert_not_awaited()
    assert "error" in result


@pytest.mark.asyncio
async def test_execute_delete_message_api_error(bridge, mock_bot):
    mock_bot.delete_message.side_effect = Exception("Message not found")

    action = MagicMock()
    action.action_type = "delete_message"
    action.target_chat_id = -100123
    action.target_message_id = 999

    result = await bridge._execute_action(action)

    assert result == {"error": "Message not found"}


@pytest.mark.asyncio
async def test_execute_trust_sender_success(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "trust_sender"
    action.target_chat_id = -100123
    action.target_user_id = 789
    action.target_message_id = None

    result = await bridge._execute_action(action)

    mock_bot.restrict_chat_member.assert_awaited_once_with(
        chat_id=-100123,
        user_id=789,
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    assert result == {"trusted": True}


@pytest.mark.asyncio
async def test_execute_restrict_member_success(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "restrict_member"
    action.target_chat_id = -100123
    action.target_user_id = 789
    action.target_message_id = None

    result = await bridge._execute_action(action)

    mock_bot.restrict_chat_member.assert_awaited_once_with(
        chat_id=-100123,
        user_id=789,
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False,
    )
    assert result == {"restricted": True}


@pytest.mark.asyncio
async def test_execute_mute_member_success(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "mute_member"
    action.target_chat_id = -100123
    action.target_user_id = 789
    action.target_message_id = None

    result = await bridge._execute_action(action)

    mock_bot.restrict_chat_member.assert_awaited_once()
    kwargs = mock_bot.restrict_chat_member.await_args.kwargs
    assert kwargs["chat_id"] == -100123
    assert kwargs["user_id"] == 789
    assert kwargs["can_send_messages"] is False
    assert "until_date" in kwargs
    assert result["muted"] is True


@pytest.mark.asyncio
async def test_execute_ban_member_success(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "ban_member"
    action.target_chat_id = -100123
    action.target_user_id = 789
    action.target_message_id = None

    result = await bridge._execute_action(action)

    mock_bot.ban_chat_member.assert_awaited_once_with(chat_id=-100123, user_id=789)
    assert result == {"banned": True}


@pytest.mark.asyncio
async def test_execute_ban_member_missing_fields(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "ban_member"
    action.target_chat_id = None
    action.target_user_id = None

    result = await bridge._execute_action(action)

    mock_bot.ban_chat_member.assert_not_awaited()
    assert "error" in result


@pytest.mark.asyncio
async def test_execute_refresh_member_success(bridge, mock_bot):
    mock_bot.get_chat_member.return_value.status = "member"

    action = MagicMock()
    action.action_type = "refresh_member"
    action.target_chat_id = -100123
    action.target_user_id = 789

    result = await bridge._execute_action(action)

    mock_bot.get_chat_member.assert_awaited_once_with(chat_id=-100123, user_id=789)
    assert result == {"status": "member", "user_id": 789}


@pytest.mark.asyncio
async def test_execute_refresh_group_permissions(bridge, mock_bot):
    bot_member = MagicMock()
    bot_member.can_delete_messages = True
    bot_member.status = "administrator"
    mock_bot.get_chat_member.return_value = bot_member

    action = MagicMock()
    action.action_type = "refresh_group_permissions"
    action.target_chat_id = -100123
    action.target_message_id = None
    action.target_user_id = None

    result = await bridge._execute_action(action)

    assert result == {"can_delete_messages": True, "status": "administrator"}


@pytest.mark.asyncio
async def test_execute_block_indicator(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "block_indicator"
    action.target_chat_id = -100123

    result = await bridge._execute_action(action)

    assert "info" in result
    assert "block_indicator" in result["info"]


@pytest.mark.asyncio
async def test_execute_allow_indicator(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "allow_indicator"

    result = await bridge._execute_action(action)

    assert "info" in result
    assert "allow_indicator" in result["info"]


@pytest.mark.asyncio
async def test_execute_unknown_action_type(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "unknown_action"

    result = await bridge._execute_action(action)

    assert "error" in result
    assert "unknown" in result["error"].lower()


@pytest.mark.asyncio
async def test_process_batch_empty(bridge, mock_bot):
    mock_repo = MagicMock()
    mock_repo.claim_next = AsyncMock(return_value=[])

    session = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.enforcement_bridge.EnforcementRepository", return_value=mock_repo):
        count = await bridge._process_batch(session)

    assert count == 0
    mock_repo.claim_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_batch_with_actions(bridge, mock_bot):
    action = MagicMock()
    action.id = "test-id"
    action.action_type = "delete_message"
    action.target_chat_id = -100123
    action.target_message_id = 456
    action.target_user_id = None

    mock_repo = MagicMock()
    mock_repo.claim_next = AsyncMock(return_value=[action])
    mock_repo.mark_completed = AsyncMock()
    mock_repo.mark_failed = AsyncMock()

    session = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.enforcement_bridge.EnforcementRepository", return_value=mock_repo):
        count = await bridge._process_batch(session)

    assert count == 1
    mock_repo.mark_completed.assert_awaited_once()
    mock_repo.mark_failed.assert_not_called()


@pytest.mark.asyncio
async def test_process_batch_action_fails(bridge, mock_bot):
    mock_bot.delete_message.side_effect = Exception("API error")

    action = MagicMock()
    action.id = "test-id"
    action.action_type = "delete_message"
    action.target_chat_id = -100123
    action.target_message_id = 999
    action.target_user_id = None

    mock_repo = MagicMock()
    mock_repo.claim_next = AsyncMock(return_value=[action])
    mock_repo.mark_failed = AsyncMock()
    mock_repo.mark_completed = AsyncMock()

    session = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.enforcement_bridge.EnforcementRepository", return_value=mock_repo):
        count = await bridge._process_batch(session)

    assert count == 1
    mock_repo.mark_failed.assert_awaited_once()
    mock_repo.mark_completed.assert_not_called()


@pytest.mark.asyncio
async def test_start_stop(bridge):
    assert bridge._running is False
    assert bridge._task is None

    bridge.start()

    assert bridge._running is True
    assert bridge._task is not None

    await bridge.stop()

    assert bridge._running is False
    assert bridge._task is None


@pytest.mark.asyncio
async def test_start_twice(bridge):
    bridge.start()
    task = bridge._task

    bridge.start()

    assert bridge._task is task


@pytest.mark.asyncio
async def test_trust_sender_missing_fields(bridge, mock_bot):
    action = MagicMock()
    action.action_type = "trust_sender"
    action.target_chat_id = None
    action.target_user_id = None

    result = await bridge._execute_action(action)

    mock_bot.restrict_chat_member.assert_not_awaited()
    assert "error" in result


@pytest.mark.asyncio
async def test_run_once_no_sessionmaker(bridge):
    with patch(
        "app.services.enforcement_bridge.get_secadmin_sessionmaker",
        side_effect=RuntimeError("Not initialized"),
    ):
        count = await bridge.run_once()
    assert count == 0


@pytest.mark.asyncio
async def test_run_once_generic_error(bridge):
    with patch(
        "app.services.enforcement_bridge.get_secadmin_sessionmaker",
        side_effect=Exception("Unexpected"),
    ):
        count = await bridge.run_once()
    assert count == 0
