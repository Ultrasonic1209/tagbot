import configparser
import logging
from typing import TypedDict

import discord
from discord.ext import commands

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

discord.utils.setup_logging()

extensions = tuple(("jishaku",))

configKeys = tuple(("botToken", "dbName"))

logger = logging.getLogger(__name__)

class BotConfig(TypedDict):
    BotToken: str
    CommandPrefix: str

class Bot(commands.Bot):
    engine: AsyncEngine
    config: BotConfig

    async def setup_hook(self) -> None:

        # load the database!
        self.engine = create_async_engine("sqlite+aiosqlite:///db.sqlite")

        # load extensions
        for extension in extensions:
            try:
                await bot.load_extension(extension)
            except Exception:
                logger.exception(f"Error loading extension {extension}")
            else:
                logger.info(f"Extension {extension} loaded")


if __name__ == "__main__":

    # load the config!
    config = configparser.ConfigParser()
    config.read(('config.default.ini', 'config.ini'))
    
    botsection = config["bot"]

    botConfig = BotConfig(
        BotToken=botsection.get("BotToken"),
        CommandPrefix=botsection.get("BotPrefix", ">")
    )

    logger.info(botConfig)

    # initalise the bot!

    intents = discord.Intents.default()
    intents.message_content = True

    allowedMentions = discord.AllowedMentions.none()
    allowedMentions.replied_user = True

    bot = Bot(
        command_prefix=commands.when_mentioned_or(botConfig["CommandPrefix"]),
        intents=intents,
        allowed_mentions=allowedMentions
    )

    bot.config = botConfig

    bot.run(botConfig["BotToken"])