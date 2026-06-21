from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.i18n import I18n


def _mode_label(mode: str, current_mode: str, i18n: I18n) -> str:
    label = i18n.t(f"keyboards.mode.{mode}")
    if mode == current_mode:
        label = f"✅ {label}"
    return label


def mode_keyboard(current_mode: str, i18n: I18n | None = None) -> InlineKeyboardMarkup:
    i18n = i18n or I18n()
    builder = InlineKeyboardBuilder()
    for mode in ("relaxed", "normal", "strict"):
        builder.button(text=_mode_label(mode, current_mode, i18n), callback_data=f"mode:{mode}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_delete_data_keyboard(chat_id: int, i18n: I18n | None = None) -> InlineKeyboardMarkup:
    i18n = i18n or I18n()
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"🗑 {i18n.t('keyboards.confirm_delete')}",
        callback_data=f"confirm_delete:{chat_id}",
    )
    builder.button(
        text=i18n.t("keyboards.cancel_delete"),
        callback_data=f"cancel_delete:{chat_id}",
    )
    builder.adjust(1)
    return builder.as_markup()


def deletion_notification_keyboard(
    sender_id: int | None = None,
    domain: str | None = None,
    telegram_entity: str | None = None,
    i18n: I18n | None = None,
) -> InlineKeyboardMarkup:
    i18n = i18n or I18n()
    builder = InlineKeyboardBuilder()
    if sender_id is not None:
        builder.button(
            text=i18n.t("keyboards.trust_sender"),
            callback_data=f"trust_user:{sender_id}",
        )
    if domain is not None:
        builder.button(
            text=i18n.t("keyboards.allow_domain"),
            callback_data=f"allow_domain:{domain}",
        )
    if telegram_entity is not None:
        builder.button(
            text=i18n.t("keyboards.allow_tg"),
            callback_data=f"allow_tg:{telegram_entity}",
        )
    builder.adjust(1)
    return builder.as_markup()


def add_to_group_keyboard(bot_username: str, i18n: I18n | None = None) -> InlineKeyboardMarkup:
    i18n = i18n or I18n()
    url = f"https://t.me/{bot_username}?startgroup=true"
    builder = InlineKeyboardBuilder()
    builder.button(text=i18n.t("keyboards.add_to_group"), url=url)
    return builder.as_markup(as_width=1)
