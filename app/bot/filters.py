import logging

from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Message

logger = logging.getLogger(__name__)


class IsGroupMessage(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type in (
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        )


class IsPrivateMessage(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.type == ChatType.PRIVATE
