import asyncio
import yt_dlp

from music_system.track import Track

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "extract_flat": False,
}

class YTDLSource:
    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    @classmethod
    async def from_query(cls, query: str) -> Track:
        loop = asyncio.get_running_loop()
        info = await loop.run_in_executor(
            None,
            lambda: cls.ytdl.extract_info(query, download=False)
        )

        if "entries" in info:
            info = info["entries"][0]

        return Track(
            title=info.get("title", "Sem título"),
            url=info.get("webpage_url", query),
            stream_url=info["url"],
            duration=info.get("duration"),
            webpage_url=info.get("webpage_url"),
        )