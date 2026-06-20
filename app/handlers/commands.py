import logging
import re

from aiogram import F, Router, types
from aiogram.filters import Command

from app.bot.filters import IsGroupMessage
from app.bot.keyboards import confirm_delete_data_keyboard, mode_keyboard
from app.database.repositories.allowlist import AllowlistRepository
from app.database.repositories.chats import ChatRepository
from app.database.repositories.deletion_logs import DeletionLogRepository
from app.services.allowlist import AllowlistService
from app.services.permissions import is_group_owner, is_user_admin

logger = logging.getLogger(__name__)

router = Router()


async def _ensure_admin(message: types.Message, session) -> bool:
    if message.from_user is None:
        await message.answer(
            "Could not verify your identity. Anonymous admins cannot change settings."
        )
        return False
    is_admin = await is_user_admin(message.bot, message.chat.id, message.from_user.id)
    if not is_admin:
        chat_title = (
            message.chat.title
            or message.chat.username
            or str(message.chat.id)
        )
        logger.warning(
            "Admin check failed: user=%d chat_id=%d chat=%r",
            message.from_user.id,
            message.chat.id,
            chat_title,
        )
        await message.answer("You must be a group administrator to use this command.")
        return False
    logger.debug(
        "Admin check passed for user %d in chat %d",
        message.from_user.id,
        message.chat.id,
    )
    return True


@router.message(Command("start"), IsGroupMessage())
async def start_group(message: types.Message) -> None:
    await message.answer(
        "AdCleaner is protecting this group. "
        "An administrator can use /help to see available commands.",
    )


@router.message(Command("on"), IsGroupMessage())
async def enable_protection(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return
    repo = ChatRepository(session)
    chat = await repo.set_enabled(message.chat.id, True)
    if chat is None:
        await message.answer("This group is not registered. Remove and re-add the bot.")
        return
    await message.answer("✅ Advertisement protection is now enabled.")


@router.message(Command("off"), IsGroupMessage())
async def disable_protection(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return
    repo = ChatRepository(session)
    chat = await repo.set_enabled(message.chat.id, False)
    if chat is None:
        await message.answer("This group is not registered. Remove and re-add the bot.")
        return
    await message.answer("✅ Advertisement protection is now disabled.")


@router.message(Command("mode"), IsGroupMessage())
async def change_mode(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return
    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(message.chat.id)
    if chat is None:
        await message.answer("This group is not registered. Remove and re-add the bot.")
        return
    await message.answer(
        f"Current mode: <b>{chat.mode.capitalize()}</b>\n\nChoose a protection level:",
        reply_markup=mode_keyboard(chat.mode),
    )


@router.callback_query(F.data.startswith("mode:"))
async def mode_callback(callback: types.CallbackQuery, session=None) -> None:
    if callback.message is None or callback.from_user is None:
        return
    mode = callback.data.removeprefix("mode:")

    is_admin = await is_user_admin(
        callback.bot,
        callback.message.chat.id,
        callback.from_user.id,
    )
    if not is_admin:
        await callback.answer("Only administrators can change the mode.", show_alert=True)
        return

    repo = ChatRepository(session)
    chat = await repo.update_mode(callback.message.chat.id, mode)
    if chat is None:
        await callback.answer("Chat not found.", show_alert=True)
        return

    await callback.message.edit_text(
        f"✅ Protection mode changed to <b>{mode.capitalize()}</b>.",
        reply_markup=None,
    )
    await callback.answer(f"Mode set to {mode.capitalize()}")


DOMAIN_IN_TEXT = re.compile(
    r"(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\."
    r"[a-z0-9][a-z0-9-]{0,61}[a-z0-9])",
    re.IGNORECASE,
)


@router.message(Command("allow"), IsGroupMessage())
async def allow_entity(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return

    args = message.text.split(maxsplit=1)

    if message.reply_to_message:
        replied = message.reply_to_message
        service = AllowlistService(session)

        if replied.from_user and replied.from_user.is_bot:
            result = await service.add_bot_by_id(
                message.chat.id,
                replied.from_user.id,
                replied.from_user.username,
                message.from_user.id,
            )
            await message.reply(result.message)
            return
        elif replied.from_user and not replied.from_user.is_bot:
            result = await service.add_user_by_id(
                message.chat.id,
                replied.from_user.id,
                replied.from_user.full_name or f"@{replied.from_user.username}",
                message.from_user.id,
            )
            await message.reply(result.message)
            return
        elif replied.sender_chat:
            username = replied.sender_chat.username or f"chat_{replied.sender_chat.id}"
            result = await service.add_telegram_chat(
                message.chat.id,
                username,
                message.from_user.id,
            )
            await message.reply(result.message)
            return
        else:
            replied_text = replied.text or replied.caption or ""
            domain_match = DOMAIN_IN_TEXT.search(replied_text)
            if domain_match:
                domain = domain_match.group(1)
                result = await service.add_domain(message.chat.id, domain, message.from_user.id)
                await message.reply(result.message)
                return

    if len(args) < 2:
        await message.answer(
            "Usage: /allow @username\n"
            "       /allow example.com\n"
            "Or reply to a message to allow that user, bot, or domain."
        )
        return

    value = args[1].strip()
    service = AllowlistService(session)

    if value.startswith("@"):
        result = await service.add_user(message.chat.id, value, message.from_user.id)
    elif value.count(".") >= 1 and not value.startswith("@"):
        result = await service.add_domain(message.chat.id, value, message.from_user.id)
    else:
        result = await service.add_user(message.chat.id, value, message.from_user.id)

    await message.reply(result.message)


@router.message(Command("removeallow"), IsGroupMessage())
async def remove_allow(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: /removeallow @username\n       /removeallow example.com")
        return

    value = args[1].strip()
    service = AllowlistService(session)

    if value.startswith("@"):
        result = await service.remove(message.chat.id, "user", value)
    elif value.count(".") >= 1:
        result = await service.remove(message.chat.id, "domain", value)
    else:
        result = await service.remove(message.chat.id, "user", value)

    await message.reply(result.message)


@router.message(Command("allowlist"), IsGroupMessage())
async def show_allowlist(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return

    service = AllowlistService(session)
    text = await service.get_formatted_list(message.chat.id)
    await message.answer(text)


@router.message(Command("status"), IsGroupMessage())
async def show_status(message: types.Message, session=None) -> None:
    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(message.chat.id)
    if chat is None:
        await message.answer("This group is not registered.")
        return

    log_repo = DeletionLogRepository(session)
    deleted_today = await log_repo.count_today(chat.id)

    al_repo = AllowlistRepository(session)
    all_entities = await al_repo.get_all_for_chat(chat.id)
    trusted_count = len(all_entities)
    domain_count = sum(1 for e in all_entities if e.entity_type == "domain")

    status_text = "Active" if chat.enabled else "Disabled"

    await message.answer(
        f"AdCleaner is <b>{status_text}</b>.\n\n"
        f"Mode: <b>{chat.mode.capitalize()}</b>\n"
        f"Deleted today: <b>{deleted_today}</b>\n"
        f"Trusted users and bots: <b>{trusted_count}</b>\n"
        f"Trusted domains: <b>{domain_count}</b>"
    )


@router.message(Command("recent"), IsGroupMessage())
async def show_recent(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return

    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(message.chat.id)
    if chat is None:
        await message.answer("This group is not registered.")
        return

    log_repo = DeletionLogRepository(session)
    logs = await log_repo.get_recent(chat.id, limit=10)
    if not logs:
        await message.answer("No recent deletions.")
        return

    lines = ["<b>Recent deletions:</b>\n"]
    for i, log in enumerate(logs, 1):
        reasons_str = ", ".join(log.reasons or []) if log.reasons else "N/A"
        excerpt = (log.message_excerpt or "")[:80]
        if excerpt:
            excerpt = excerpt.replace("<", "&lt;").replace(">", "&gt;")
        lines.append(f"{i}. Score: <b>{log.score}</b> | Reasons: {reasons_str}")
        if excerpt:
            lines.append(f"   Excerpt: {excerpt}")
        lines.append("")

    text = "\n".join(lines)
    await message.answer(text)


@router.message(Command("deletedata"), IsGroupMessage())
async def delete_data(message: types.Message, session=None) -> None:
    if not await _ensure_admin(message, session):
        return

    is_owner = await is_group_owner(message.bot, message.chat.id, message.from_user.id)
    if not is_owner:
        await message.answer(
            "Only the group owner can delete all data. Please contact the group creator."
        )
        return

    await message.answer(
        "⚠️ <b>Are you sure?</b>\n\n"
        "This will permanently delete all stored configuration and deletion logs "
        "for this group. The bot will leave the group.\n\n"
        "This action cannot be undone.",
        reply_markup=confirm_delete_data_keyboard(message.chat.id),
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_callback(callback: types.CallbackQuery, session=None) -> None:
    if callback.message is None or callback.from_user is None:
        return
    chat_id = int(callback.data.removeprefix("confirm_delete:"))

    is_owner = await is_group_owner(callback.bot, chat_id, callback.from_user.id)
    if not is_owner:
        await callback.answer("Only the group owner can delete data.", show_alert=True)
        return

    repo = ChatRepository(session)
    await repo.delete_chat_data(chat_id)

    await callback.message.edit_text("✅ All data has been deleted. The bot is leaving the group.")
    await callback.answer()

    try:
        await callback.bot.leave_chat(chat_id)
    except Exception as e:
        logger.warning("Failed to leave chat %d: %s", chat_id, e)


@router.callback_query(F.data.startswith("cancel_delete:"))
async def cancel_delete_callback(callback: types.CallbackQuery) -> None:
    if callback.message is None:
        return
    await callback.message.edit_text("✅ Data deletion cancelled.")
    await callback.answer()


@router.message(Command("help"), IsGroupMessage())
async def help_group(message: types.Message) -> None:
    await message.answer(
        "<b>AdCleaner commands (admin only):</b>\n\n"
        "/on — Enable advertisement protection\n"
        "/off — Disable advertisement protection\n"
        "/mode — Change protection mode (Relaxed / Normal / Strict)\n"
        "/allow @username — Allow a user or bot\n"
        "/allow example.com — Allow a domain\n"
        "/removeallow @username — Remove from allowlist\n"
        "/removeallow example.com — Remove domain from allowlist\n"
        "/allowlist — Show allowed entities\n"
        "/status — Show moderation status\n"
        "/recent — Show recent deletions\n"
        "/deletedata — Delete all group data (owner only)\n"
        "/help — Show this help"
    )
