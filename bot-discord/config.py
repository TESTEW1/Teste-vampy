import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(slots=True)
class BotConfig:
    token: str
    prefixes: list[str]
    owner_id: int
    log_channel_name: str
    geral_channel_name: str
    ticket_channel_name: str

def load_config() -> BotConfig:
    token = os.getenv("TOKEN", "").strip()
    if not token:
        raise RuntimeError("TOKEN não encontrada no arquivo .env")

    return BotConfig(
        token=token,
        prefixes=["v!", "!"],
        owner_id=int(os.getenv("DONO_ID", "769951556388257812")),
        log_channel_name="🗒️・monitoramento",
        geral_channel_name="💭・chat-geral",
        ticket_channel_name="🎟️・ticket",
    )