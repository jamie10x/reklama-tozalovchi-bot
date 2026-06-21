import re

from aiogram import F, Router, types
from aiogram.filters import Command

from app.bot.filters import IsGroupMessage
from app.bot.keyboards import confirm_delete_data_keyboard, mode_keyboard
from app.core.logging import get_logger
from app.database.repositories.allowlist import AllowlistRepository
from app.database.repositories.chats import ChatRepository
from app.database.repositories.deletion_logs import DeletionLogRepository
from app.i18n import I18n
from app.services.allowlist import AllowlistService
from app.services.permissions import is_group_owner, is_user_admin

logger = get_logger(__name__)

router = Router()


async def _ensure_admin(message: types.Message, session, i18n: I18n) -> bool:
    if message.from_user is None:
        await message.answer(i18n.t("commands.not_anonymous"))
        return False
    is_admin = await is_user_admin(message.bot, message.chat.id, message.from_user.id)
    if not is_admin:
        logger.warning("Admin check failed", user=message.from_user.id, chat_id=message.chat.id)
        await message.answer(i18n.t("commands.admin_required"))
        return False
    return True


@router.message(Command("start"), IsGroupMessage())
async def start_group(message: types.Message, i18n: I18n) -> None:
    await message.answer(i18n.t("commands.group_start"))


@router.message(Command("on"), IsGroupMessage())
async def enable_protection(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return
    repo = ChatRepository(session)
    chat = await repo.set_enabled(message.chat.id, True)
    if chat is None:
        await message.answer(i18n.t("commands.chat_not_registered"))
        return
    await message.answer(i18n.t("commands.protection_enabled"))


@router.message(Command("off"), IsGroupMessage())
async def disable_protection(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return
    repo = ChatRepository(session)
    chat = await repo.set_enabled(message.chat.id, False)
    if chat is None:
        await message.answer(i18n.t("commands.chat_not_registered"))
        return
    await message.answer(i18n.t("commands.protection_disabled"))


@router.message(Command("mode"), IsGroupMessage())
async def change_mode(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return
    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(message.chat.id)
    if chat is None:
        await message.answer(i18n.t("commands.chat_not_registered"))
        return
    await message.answer(
        i18n.t("commands.mode_prompt", mode=chat.mode.capitalize()),
        reply_markup=mode_keyboard(chat.mode, i18n),
    )


@router.callback_query(F.data.startswith("mode:"))
async def mode_callback(callback: types.CallbackQuery, session=None, i18n: I18n = None) -> None:
    if callback.message is None or callback.from_user is None:
        return
    mode = callback.data.removeprefix("mode:")

    is_admin = await is_user_admin(
        callback.bot,
        callback.message.chat.id,
        callback.from_user.id,
    )
    if not is_admin:
        await callback.answer(
            i18n.t("commands.mode_denied") if i18n else "Only administrators can change the mode.",
            show_alert=True,
        )
        return

    repo = ChatRepository(session)
    chat = await repo.update_mode(callback.message.chat.id, mode)
    if chat is None:
        await callback.answer(
            i18n.t("commands.mode_chat_not_found") if i18n else "Chat not found.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        i18n.t("commands.mode_changed", mode=mode.capitalize()),
        reply_markup=None,
    )
    await callback.answer(i18n.t("commands.mode_set", mode=mode.capitalize()))


DOMAIN_IN_TEXT = re.compile(
    r"(?:https?://)?(?:www\.)?([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\."
    r"[a-z0-9][a-z0-9-]{0,61}[a-z0-9])",
    re.IGNORECASE,
)


@router.message(Command("allow"), IsGroupMessage())
async def allow_entity(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return

    args = message.text.split(maxsplit=1)

    if message.reply_to_message:
        replied = message.reply_to_message
        service = AllowlistService(session, i18n)

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
        await message.answer(i18n.t("commands.allow_usage"))
        return

    value = args[1].strip()
    service = AllowlistService(session, i18n)

    if value.startswith("@"):
        result = await service.add_user(message.chat.id, value, message.from_user.id)
    elif value.count(".") >= 1 and not value.startswith("@"):
        result = await service.add_domain(message.chat.id, value, message.from_user.id)
    else:
        result = await service.add_user(message.chat.id, value, message.from_user.id)

    await message.reply(result.message)


@router.message(Command("removeallow"), IsGroupMessage())
async def remove_allow(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(i18n.t("commands.removeallow_usage"))
        return

    value = args[1].strip()
    service = AllowlistService(session, i18n)

    if value.startswith("@"):
        result = await service.remove(message.chat.id, "user", value)
    elif value.count(".") >= 1:
        result = await service.remove(message.chat.id, "domain", value)
    else:
        result = await service.remove(message.chat.id, "user", value)

    await message.reply(result.message)


@router.message(Command("allowlist"), IsGroupMessage())
async def show_allowlist(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return
    service = AllowlistService(session, i18n)
    text = await service.get_formatted_list(message.chat.id)
    await message.answer(text)


@router.message(Command("status"), IsGroupMessage())
async def show_status(message: types.Message, session=None, i18n: I18n = None) -> None:
    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(message.chat.id)
    if chat is None:
        await message.answer(i18n.t("commands.chat_not_registered"))
        return

    log_repo = DeletionLogRepository(session)
    deleted_today = await log_repo.count_today(chat.id)

    al_repo = AllowlistRepository(session)
    all_entities = await al_repo.get_all_for_chat(chat.id)
    trusted_count = len(all_entities)
    domain_count = sum(1 for e in all_entities if e.entity_type == "domain")

    status = (
        i18n.t("commands.status_active") if chat.enabled else i18n.t("commands.status_disabled")
    )

    await message.answer(
        i18n.t(
            "commands.status_text",
            status=status,
            mode=chat.mode.capitalize(),
            deleted=deleted_today,
            users=trusted_count,
            domains=domain_count,
        )
    )


@router.message(Command("recent"), IsGroupMessage())
async def show_recent(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return

    repo = ChatRepository(session)
    chat = await repo.get_by_telegram_id(message.chat.id)
    if chat is None:
        await message.answer(i18n.t("commands.chat_not_registered"))
        return

    log_repo = DeletionLogRepository(session)
    logs = await log_repo.get_recent(chat.id, limit=10)
    if not logs:
        await message.answer(i18n.t("commands.no_recent"))
        return

    lines = [i18n.t("commands.recent_title")]
    for i, log in enumerate(logs, 1):
        reasons_str = ", ".join(log.reasons or []) if log.reasons else "N/A"
        excerpt = (log.message_excerpt or "")[:80]
        if excerpt:
            excerpt = excerpt.replace("<", "&lt;").replace(">", "&gt;")
        lines.append(i18n.t("commands.recent_item", i=i, score=log.score, reasons=reasons_str))
        if excerpt:
            lines.append(i18n.t("commands.recent_excerpt", excerpt=excerpt))
        lines.append("")

    text = "\n".join(lines)
    await message.answer(text)


@router.message(Command("deletedata"), IsGroupMessage())
async def delete_data(message: types.Message, session=None, i18n: I18n = None) -> None:
    if not await _ensure_admin(message, session, i18n):
        return

    is_owner = await is_group_owner(message.bot, message.chat.id, message.from_user.id)
    if not is_owner:
        await message.answer(i18n.t("commands.delete_owner_only"))
        return

    await message.answer(
        i18n.t("commands.delete_confirm"),
        reply_markup=confirm_delete_data_keyboard(message.chat.id, i18n),
    )


@router.callback_query(F.data.startswith("confirm_delete:"))
async def confirm_delete_callback(
    callback: types.CallbackQuery, session=None, i18n: I18n = None
) -> None:
    if callback.message is None or callback.from_user is None:
        return
    chat_id = int(callback.data.removeprefix("confirm_delete:"))

    is_owner = await is_group_owner(callback.bot, chat_id, callback.from_user.id)
    if not is_owner:
        await callback.answer(
            (
                i18n.t("commands.delete_owner_only")
                if i18n
                else "Only the group owner can delete data."
            ),
            show_alert=True,
        )
        return

    repo = ChatRepository(session)
    await repo.delete_chat_data(chat_id)

    await callback.message.edit_text(i18n.t("commands.delete_done"))
    await callback.answer()

    try:
        await callback.bot.leave_chat(chat_id)
    except Exception as e:
        logger.warning("Failed to leave chat %d: %s", chat_id, e)


@router.callback_query(F.data.startswith("cancel_delete:"))
async def cancel_delete_callback(callback: types.CallbackQuery, i18n: I18n = None) -> None:
    if callback.message is None:
        return
    await callback.message.edit_text(i18n.t("commands.delete_cancelled"))
    await callback.answer()


@router.message(Command("help"), IsGroupMessage())
async def help_group(message: types.Message, i18n: I18n) -> None:
    await message.answer(i18n.t("commands.help_group"))
