import discord
from discord.ext import commands

from music_system.player import MusicPlayer
from music_system.ytdl_source import YTDLSource

class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, MusicPlayer] = {}

    def get_player(self, guild_id: int) -> MusicPlayer:
        if guild_id not in self.players:
            self.players[guild_id] = MusicPlayer()
        return self.players[guild_id]

    @commands.command(name="join")
    async def join(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Você precisa estar em um canal de voz.")
            return

        channel = ctx.author.voice.channel
        if ctx.voice_client is None:
            await channel.connect()
        else:
            await ctx.voice_client.move_to(channel)

        await ctx.send(f"Conectado em **{channel.name}**")

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, query: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Entre em um canal de voz primeiro.")
            return

        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()

        player = self.get_player(ctx.guild.id)

        try:
            track = await YTDLSource.from_query(query)
        except Exception as e:
            await ctx.send(f"Erro ao carregar música: `{e}`")
            return

        await player.queue.put(track)
        await ctx.send(f"Adicionado à fila: **{track.title}**")

        if not ctx.voice_client.is_playing() and not player.is_running:
            self.bot.loop.create_task(player.start(ctx))

    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Música pulada.")

    @commands.command(name="leave")
    async def leave(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Sai do canal de voz.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))