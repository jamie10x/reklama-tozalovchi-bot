import logging

from aiogram import Router, types
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, KICKED, ChatMemberUpdatedFilter

from app.bot.keyboards import add_to_group_keyboard
from app.database.repositories.chats import ChatRepository
from app.services.permissions import bot_can_delete_messages

logger = logging.getLogger(__name__)

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER))
async def bot_added_to_group(event: types.ChatMemberUpdated, session=None) -> None:
    chat = event.chat
    bot = event.bot
    repo = ChatRepository(session)

    existing = await repo.get_by_telegram_id(chat.id)
    if existing and existing.removed_at is None:
        logger.info("Bot already registered in chat %d", chat.id)
        return

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

    can_delete = await bot_can_delete_messages(bot, chat.id)
    await repo.set_bot_permission(chat.id, can_delete)

    if can_delete:
        await bot.send_message(
            chat.id,
            "✅ AdCleaner is now active. "
            "Unauthorized advertisements will be deleted automatically.\n\n"
            "An administrator can use /mode to change the protection level "
            "or /off to disable protection.",
        )
    else:
        bot_me = await bot.me()
        await bot.send_message(
            chat.id,
            "⚠️ AdCleaner cannot remove advertisements because it does not have "
            "permission to delete messages.\n\n"
            "Grant the bot administrator access with the <i>Delete messages</i> permission.",
            reply_markup=add_to_group_keyboard(bot_me.username or ""),
        )

    logger.info("Bot added to chat %d (%s)", chat.id, chat.title)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def bot_removed_from_group(event: types.ChatMemberUpdated, session=None) -> None:
    chat = event.chat
    repo = ChatRepository(session)
    await repo.mark_removed(chat.id)
    logger.info("Bot removed from chat %d (%s)", chat.id, chat.title)


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER))
async def bot_left_group(event: types.ChatMemberUpdated, session=None) -> None:
    chat = event.chat
    repo = ChatRepository(session)
    await repo.mark_removed(chat.id)
    logger.info("Bot left chat %d (%s)", chat.id, chat.title)
