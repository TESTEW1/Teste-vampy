import discord
from discord.ext import commands

from config import load_config

INITIAL_EXTENSIONS = [
    "cogs.security",
    "cogs.tickets",
    "cogs.music",
    "cogs.misc",
]

class VampyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        intents.voice_states = True

        self.config = load_config()

        super().__init__(
            command_prefix=self.config.prefixes,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self) -> None:
        from views.ticket_views import TicketView
        from views.role_views import RolePanelView

        self.add_view(TicketView())
        self.add_view(RolePanelView())

    async def load_all_extensions(self) -> None:
        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)

def create_bot() -> VampyBot:
    return VampyBot()