import asyncio
import discord

from music_system.track import Track

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

class MusicPlayer:
    def __init__(self):
        self.queue: asyncio.Queue[Track] = asyncio.Queue()
        self.is_running = False
        self.current: Track | None = None

    async def start(self, ctx):
        self.is_running = True

        while not self.queue.empty():
            track = await self.queue.get()
            self.current = track

            source = discord.FFmpegPCMAudio(track.stream_url, **FFMPEG_OPTIONS)

            done = asyncio.Event()

            def after_playing(error):
                if error:
                    print(f"Erro no player: {error}")
                ctx.bot.loop.call_soon_threadsafe(done.set)

            ctx.voice_client.play(source, after=after_playing)
            await ctx.send(f"🎶 Tocando agora: **{track.title}**")
            await done.wait()

        self.current = None
        self.is_running = False