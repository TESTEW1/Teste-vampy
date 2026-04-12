import logging
import discord

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s"
    )

def get_text_channel_by_name(guild: discord.Guild, name: str) -> discord.TextChannel | None:
    return discord.utils.get(guild.text_channels, name=name)

def get_role_by_name(guild: discord.Guild, name: str) -> discord.Role | None:
    return discord.utils.get(guild.roles, name=name)

def make_embed(
    title: str,
    description: str = "",
    color: int = 0x5865F2
) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)