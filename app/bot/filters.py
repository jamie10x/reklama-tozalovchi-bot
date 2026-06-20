from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message


class IsGroupAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type not in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        ):
            return False
        if message.from_user is None:
            return False
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))


class IsGroupMessage(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        )


class IsPrivateMessage(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == ChatType.PRIVATE
