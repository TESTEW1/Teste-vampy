import asyncio
from core.bot import create_bot
from core.helpers import setup_logging

async def main():
    setup_logging()
    bot = create_bot()

    async with bot:
        await bot.load_all_extensions()
        await bot.start(bot.config.token)

if __name__ == "__main__":
    asyncio.run(main())