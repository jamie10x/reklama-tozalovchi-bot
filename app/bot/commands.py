from aiogram.types import BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeDefault

private_commands = [
    BotCommand(command="start", description="Start the bot"),
    BotCommand(command="help", description="Show help"),
    BotCommand(command="privacy", description="Privacy information"),
    BotCommand(command="status", description="Show moderation status"),
]

group_commands = [
    BotCommand(command="on", description="Enable advertisement protection"),
    BotCommand(command="off", description="Disable advertisement protection"),
    BotCommand(command="mode", description="Change protection mode"),
    BotCommand(command="allow", description="Allow a user, bot, chat, or domain"),
    BotCommand(command="removeallow", description="Remove an allowed entity"),
    BotCommand(command="allowlist", description="Show allowed entities"),
    BotCommand(command="status", description="Show moderation status"),
    BotCommand(command="recent", description="Show recent deletions"),
    BotCommand(command="deletedata", description="Delete group data"),
    BotCommand(command="help", description="Show help"),
]


async def set_bot_commands(bot):
    await bot.set_my_commands(
        commands=private_commands,
        scope=BotCommandScopeDefault(),
    )
    await bot.set_my_commands(
        commands=group_commands,
        scope=BotCommandScopeAllGroupChats(),
    )
