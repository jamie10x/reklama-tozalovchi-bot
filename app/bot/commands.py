from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeDefault

from app.i18n import I18n


def private_commands(i18n: I18n | None = None) -> list[BotCommand]:
    i18n = i18n or I18n()
    return [
        BotCommand(command="start", description=i18n.t("commands_desc.private.start")),
        BotCommand(command="help", description=i18n.t("commands_desc.private.help")),
        BotCommand(command="privacy", description=i18n.t("commands_desc.private.privacy")),
        BotCommand(command="status", description=i18n.t("commands_desc.private.status")),
    ]


def group_commands(i18n: I18n | None = None) -> list[BotCommand]:
    i18n = i18n or I18n()
    return [
        BotCommand(command="on", description=i18n.t("commands_desc.group.on")),
        BotCommand(command="off", description=i18n.t("commands_desc.group.off")),
        BotCommand(command="mode", description=i18n.t("commands_desc.group.mode")),
        BotCommand(command="allow", description=i18n.t("commands_desc.group.allow")),
        BotCommand(command="removeallow", description=i18n.t("commands_desc.group.removeallow")),
        BotCommand(command="allowlist", description=i18n.t("commands_desc.group.allowlist")),
        BotCommand(command="status", description=i18n.t("commands_desc.group.status")),
        BotCommand(command="recent", description=i18n.t("commands_desc.group.recent")),
        BotCommand(command="deletedata", description=i18n.t("commands_desc.group.deletedata")),
        BotCommand(command="help", description=i18n.t("commands_desc.group.help")),
    ]


async def set_bot_commands(bot, i18n: I18n | None = None) -> None:
    await bot.set_my_commands(
        commands=private_commands(i18n),
        scope=BotCommandScopeDefault(),
    )
    await bot.set_my_commands(
        commands=group_commands(i18n),
        scope=BotCommandScopeAllGroupChats(),
    )
