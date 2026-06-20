from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def mode_keyboard(current_mode: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for mode in ("relaxed", "normal", "strict"):
        label = f"{'✅ ' if mode == current_mode else ''}{mode.capitalize()}"
        builder.button(text=label, callback_data=f"mode:{mode}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_data_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🗑 Yes, delete all data",
        callback_data=f"confirm_delete:{chat_id}",
    )
    builder.button(
        text="Cancel",
        callback_data=f"cancel_delete:{chat_id}",
    )
    builder.adjust(1)
    return builder.as_markup()


def deletion_notification_keyboard(
    sender_id: int | None = None,
    domain: str | None = None,
    telegram_entity: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if sender_id is not None:
        builder.button(
            text="Trust sender",
            callback_data=f"trust_user:{sender_id}",
        )
    if domain is not None:
        builder.button(
            text="Allow domain",
            callback_data=f"allow_domain:{domain}",
        )
    if telegram_entity is not None:
        builder.button(
            text="Allow Telegram destination",
            callback_data=f"allow_tg:{telegram_entity}",
        )
    builder.adjust(1)
    return builder.as_markup()


def add_to_group_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    url = f"https://t.me/{bot_username}?startgroup=true"
    builder = InlineKeyboardBuilder()
    builder.button(text="Add to group", url=url)
    return builder.as_markup(as_width=1)
