from aiogram import Router, types
from aiogram.enums import ChatMemberStatus, ChatType

from app.core.logging import get_logger

logger = get_logger(__name__)

router = Router()


async def _upsert_observed_user(
    user: types.User,
    chat_id: int,
    repo,
) -> None:
    new_status = None
    if hasattr(user, "_membership_status"):
        new_status = user._membership_status

    await repo.upsert(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_bot=user.is_bot or False,
        language_code=user.language_code,
        is_premium=user.is_premium or False,
    )

    await repo.upsert_profile(
        user_id=user.id,
        chat_id=chat_id,
        membership_status=new_status,
        is_admin=new_status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR)
        if new_status
        else False,
    )


@router.chat_member()
async def observe_member_update(event: types.ChatMemberUpdated) -> None:
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    new_status = event.new_chat_member.status
    old_status = event.old_chat_member.status

    if old_status == new_status:
        return

    user = event.new_chat_member.user
    if user is None or user.is_bot:
        return

    secadmin_session = event.get("secadmin_session")
    if secadmin_session is None:
        return

    from app.database.repositories.users import ObservedUserRepository

    repo = ObservedUserRepository(secadmin_session)

    await _upsert_observed_user(user, event.chat.id, repo)

    direction = "joined"
    if new_status in (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED):
        direction = "left"

    logger.info(
        "Member observed",
        user_id=user.id,
        name=user.full_name,
        action=direction,
        chat_id=event.chat.id,
        old_status=old_status,
        new_status=new_status,
    )
