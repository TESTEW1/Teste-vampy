from dataclasses import dataclass

@dataclass(slots=True)
class Track:
    title: str
    url: str
    stream_url: str
    duration: int | None = None
    webpage_url: str | None = None