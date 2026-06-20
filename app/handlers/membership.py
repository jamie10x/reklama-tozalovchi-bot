import logging

from aiogram import Router, types
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, KICKED, ChatMemberUpdatedFilter

from app.bot.keyboards import add_to_group_keyboard
from app.database.repositories.chats import ChatRepository
from app.services.permissions import bot_can_delete_messages

logger = logging.getLogger(__name__)

router = Router()


async def _register_or_update_chat(
    event: types.ChatMemberUpdated,
    repo: ChatRepository,
) -> None:
    chat = event.chat
    bot = event.bot

    existing = await repo.get_by_telegram_id(chat.id)

    if existing is None or existing.removed_at is not None:
        owner_id = None
        try:
            admins = await bot.get_chat_administrators(chat.id)
            for admin in admins:
                if admin.status == "creator":
                    owner_id = admin.user.id
                    break
        except Exception as e:
            logger.warning("Could not get admins for chat %d: %s", chat.id, e)

        linked_chat_id = None
        try:
            chat_full = await bot.get_chat(chat.id)
            if hasattr(chat_full, "linked_chat_id") and chat_full.linked_chat_id:
                linked_chat_id = chat_full.linked_chat_id
        except Exception as e:
            logger.warning("Could not get linked chat for %d: %s", chat.id, e)

        await repo.create(
            telegram_chat_id=chat.id,
            title=chat.title,
            username=chat.username,
            owner_user_id=owner_id,
            linked_chat_id=linked_chat_id,
        )
        logger.info("Bot added to chat %d (%s)", chat.id, chat.title)
    else:
        logger.info("Bot already registered in chat %d — updating permissions", chat.id)

    can_delete = await bot_can_delete_messages(bot, chat.id)
    await repo.set_bot_permission(chat.id, can_delete)

    return can_delete


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER))
async def bot_added_to_group(event: types.ChatMemberUpdated, session=None) -> None:
    repo = ChatRepository(session)
    can_delete = await _register_or_update_chat(event, repo)

    if can_delete:
        await event.bot.send_message(
            event.chat.id,
            "✅ AdCleaner is now active. "
            "Unauthorized advertisements will be deleted automatically.\n\n"
            "An administrator can use /mode to change the protection level "
            "or /off to disable protection.",
        )
    else:
        bot_me = await event.bot.me()
        await event.bot.send_message(
            event.chat.id,
            "⚠️ AdCleaner cannot remove advertisements because it does not have "
            "permission to delete messages.\n\n"
            "Grant the bot administrator access with the <i>Delete messages</i> permission.",
            reply_markup=add_to_group_keyboard(bot_me.username or ""),
        )


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def bot_removed_from_group(event: types.ChatMemberUpdated, session=None) -> None:
    repo = ChatRepository(session)
    await repo.mark_removed(event.chat.id)
    logger.info("Bot removed from chat %d (%s)", event.chat.id, event.chat.title)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER))
async def bot_left_group(event: types.ChatMemberUpdated, session=None) -> None:
    repo = ChatRepository(session)
    await repo.mark_removed(event.chat.id)
    logger.info("Bot left chat %d (%s)", event.chat.id, event.chat.title)


@router.my_chat_member()
async def bot_permission_updated(event: types.ChatMemberUpdated, session=None) -> None:
    repo = ChatRepository(session)
    can_delete = await _register_or_update_chat(event, repo)
    if can_delete:
        await event.bot.send_message(
            event.chat.id,
            "✅ Delete permission granted. AdCleaner can now remove advertisements.",
        )
    else:
        await event.bot.send_message(
            event.chat.id,
            "⚠️ Delete permission removed. Advertisements will not be deleted.",
        )
    logger.info(
        "Bot permissions updated in chat %d: can_delete=%s",
        event.chat.id,
        can_delete,
    )
