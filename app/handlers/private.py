import logging

from aiogram import Router, types
from aiogram.filters import Command

from app.bot.filters import IsPrivateMessage
from app.bot.keyboards import add_to_group_keyboard
from app.config import Settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"), IsPrivateMessage())
async def start_command(message: types.Message, settings: Settings) -> None:
    bot = await message.bot.me()
    await message.answer(
        f"Hello! I'm <b>{bot.first_name}</b> — a Telegram bot that automatically "
        "detects and deletes unauthorized advertisements in groups.\n\n"
        "<b>How it works:</b>\n"
        "1. Add me to your group.\n"
        "2. Grant me administrator access with the <i>Delete messages</i> permission.\n"
        "3. I'll automatically detect and remove promotional messages.\n\n"
        "<b>Privacy:</b> I only store metadata about deleted messages. "
        "Normal messages are never stored.\n\n"
        "Use /help to see available commands.",
        reply_markup=add_to_group_keyboard(bot.username or ""),
    )


@router.message(Command("help"), IsPrivateMessage())
async def help_command(message: types.Message) -> None:
    await message.answer(
        "<b>Available commands:</b>\n\n"
        "/start — Start the bot\n"
        "/help — Show this help\n"
        "/privacy — Privacy information\n"
        "/status — Show moderation status\n\n"
        "<b>Group commands (admin only):</b>\n"
        "/on — Enable protection\n"
        "/off — Disable protection\n"
        "/mode — Change protection mode\n"
        "/allow — Allow a user, bot, chat, or domain\n"
        "/removeallow — Remove an allowed entity\n"
        "/allowlist — Show allowed entities\n"
        "/status — Show moderation status\n"
        "/recent — Show recent deletions\n"
        "/deletedata — Delete all group data\n"
        "/help — Show this help"
    )


@router.message(Command("privacy"), IsPrivateMessage())
async def privacy_command(message: types.Message) -> None:
    await message.answer(
        "<b>Privacy information:</b>\n\n"
        "• This bot reads messages only to detect advertisements.\n"
        "• Normal messages are never permanently stored.\n"
        "• Only metadata about deleted messages is stored.\n"
        "• Deleted message excerpts are limited to 250 characters.\n"
        "• Deletion logs automatically expire after 24 hours.\n"
        "• Message contents are never sent to third-party services.\n"
        "• Users are not tracked across unrelated groups.\n"
        "• Data is not sold or shared.\n"
        "• Group owners can request data deletion via /deletedata."
    )
