from aiogram import Router, types
from aiogram.filters import Command

from app.bot.filters import IsPrivateMessage
from app.bot.keyboards import add_to_group_keyboard
from app.core.logging import get_logger
from app.i18n import I18n

logger = get_logger(__name__)

router = Router()


@router.message(Command("start"), IsPrivateMessage())
async def start_command(message: types.Message, i18n: I18n) -> None:
    bot = await message.bot.me()
    text = i18n.t("private.start", bot_name=bot.first_name)
    await message.answer(text, reply_markup=add_to_group_keyboard(bot.username or "", i18n))


@router.message(Command("help"), IsPrivateMessage())
async def help_command(message: types.Message, i18n: I18n) -> None:
    await message.answer(i18n.t("private.help"))


@router.message(Command("privacy"), IsPrivateMessage())
async def privacy_command(message: types.Message, i18n: I18n) -> None:
    await message.answer(i18n.t("private.privacy"))
