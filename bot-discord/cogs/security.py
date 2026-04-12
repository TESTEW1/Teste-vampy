import re
from collections import defaultdict, deque
from datetime import datetime, timedelta

import discord
from discord.ext import commands, tasks

from core.helpers import get_text_channel_by_name

LOG_CHANNEL_NAME = "🗒️・monitoramento"
CANAL_GERAL = "💭・chat-geral"

COMMAND_SPAM_LIMIT = 3
COMMAND_SPAM_WINDOW = 5
COMMAND_COOLDOWN_TIME = 30

MSG_SPAM_LIMIT = 7
MSG_SPAM_WINDOW = 5
MSG_REPEAT_LIMIT = 4
EMOJI_SPAM_LIMIT = 20
MENTION_SPAM_LIMIT = 5

RISK_SPAM_MSG = 2
RISK_SPAM_CMD = 3
RISK_LINK = 4
RISK_SUSPICIOUS_THRESHOLD = 12

MALICIOUS_PATTERNS = [
    r"discord\.gift",
    r"discordnitro\.",
    r"free.*nitro",
    r"bit\.ly",
    r"tinyurl\.com",
    r"grabify\.link",
    r"iplogger\.",
]

class SecurityDatabase:
    def __init__(self):
        self.risk_scores: dict[int, int] = {}
        self.flagged_users: dict[int, dict] = {}
        self.alert_history: list[dict] = []

    def add_risk(self, user_id: int, points: int, reason: str) -> None:
        self.risk_scores[user_id] = self.risk_scores.get(user_id, 0) + points
        if self.risk_scores[user_id] >= RISK_SUSPICIOUS_THRESHOLD:
            self.flagged_users[user_id] = {
                "reason": reason,
                "score": self.risk_scores[user_id],
                "time": datetime.utcnow()
            }

    def get_risk(self, user_id: int) -> int:
        return self.risk_scores.get(user_id, 0)

    def is_flagged(self, user_id: int) -> bool:
        return user_id in self.flagged_users

    def log_alert(self, alert_type: str, details: str) -> None:
        self.alert_history.append({
            "type": alert_type,
            "details": details,
            "time": datetime.utcnow(),
        })
        if len(self.alert_history) > 200:
            self.alert_history.pop(0)

class SecurityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = SecurityDatabase()
        self._cmd_timestamps: defaultdict[int, deque] = defaultdict(deque)
        self._msg_timestamps: defaultdict[int, deque] = defaultdict(deque)
        self._last_messages: dict[int, list[str]] = {}
        self._cmd_cooldowns: dict[int, datetime] = {}
        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.cancel()

    def _now(self) -> float:
        return datetime.utcnow().timestamp()

    def _prune(self, dq: deque, window: int) -> None:
        cutoff = self._now() - window
        while dq and dq[0] < cutoff:
            dq.popleft()

    async def send_alert(
        self,
        guild: discord.Guild,
        threat_type: str,
        user: discord.Member | discord.User | None,
        details: str,
        color: int = 0xFF4444
    ) -> None:
        ch = get_text_channel_by_name(guild, LOG_CHANNEL_NAME)
        if ch is None:
            return

        self.db.log_alert(threat_type, details)

        embed = discord.Embed(
            title="🚨 Security Alert",
            description=details,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Tipo", value=threat_type, inline=False)
        embed.add_field(name="Usuário", value=str(user) if user else "Desconhecido", inline=True)

        if user is not None:
            embed.add_field(name="ID", value=str(user.id), inline=True)

        await ch.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        print("[security] carregado")

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.author.bot:
            return

        user_id = ctx.author.id

        if user_id in self._cmd_cooldowns:
            if datetime.utcnow() < self._cmd_cooldowns[user_id]:
                return

        dq = self._cmd_timestamps[user_id]
        dq.append(self._now())
        self._prune(dq, COMMAND_SPAM_WINDOW)

        if len(dq) > COMMAND_SPAM_LIMIT:
            self.db.add_risk(user_id, RISK_SPAM_CMD, "Spam de comandos")
            self._cmd_cooldowns[user_id] = datetime.utcnow() + timedelta(seconds=COMMAND_COOLDOWN_TIME)
            dq.clear()

            await self.send_alert(
                ctx.guild,
                "SPAM DE COMANDOS",
                ctx.author,
                f"{ctx.author.mention} excedeu o limite de comandos.",
                color=0xFF8800
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if message.channel.name != CANAL_GERAL:
            return

        uid = message.author.id
        content = message.content.strip()

        dq = self._msg_timestamps[uid]
        dq.append(self._now())
        self._prune(dq, MSG_SPAM_WINDOW)

        if len(dq) > MSG_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Flood")
            dq.clear()
            await self.send_alert(
                message.guild,
                "FLOOD DE MENSAGENS",
                message.author,
                f"Flood detectado em {message.channel.mention}",
                color=0xFF6600
            )
            return

        hist = self._last_messages.setdefault(uid, [])
        hist.append(content)
        if len(hist) > MSG_REPEAT_LIMIT:
            hist.pop(0)

        if len(hist) == MSG_REPEAT_LIMIT and len(set(hist)) == 1:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Repetição")
            hist.clear()
            await self.send_alert(
                message.guild,
                "MENSAGENS REPETIDAS",
                message.author,
                f"Mensagem repetida {MSG_REPEAT_LIMIT} vezes.",
                color=0xFF6600
            )
            return

        emoji_count = len(re.findall(r"<a?:\w+:\d+>|[\U0001F300-\U0001FAFF]", content))
        if emoji_count >= EMOJI_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Spam de emojis")
            await self.send_alert(
                message.guild,
                "SPAM DE EMOJIS",
                message.author,
                f"{emoji_count} emojis em uma mensagem.",
                color=0xFFAA00
            )
            return

        mention_count = len(message.mentions) + len(message.role_mentions)
        if mention_count >= MENTION_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Spam de menções")
            await self.send_alert(
                message.guild,
                "SPAM DE MENÇÕES",
                message.author,
                f"{mention_count} menções em uma mensagem.",
                color=0xFFAA00
            )
            return

        if "http://" in content.lower() or "https://" in content.lower():
            for pattern in MALICIOUS_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    self.db.add_risk(uid, RISK_LINK, "Link suspeito")
                    await self.send_alert(
                        message.guild,
                        "LINK SUSPEITO",
                        message.author,
                        f"Padrão detectado: `{pattern}`\nConteúdo: `{content[:150]}`",
                        color=0xFF0000
                    )
                    break

    @commands.group(name="security", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def security_group(self, ctx: commands.Context):
        await ctx.send("Use: `status`, `alerts`, `riskscore @user`")

    @security_group.command(name="status")
    @commands.has_permissions(administrator=True)
    async def security_status(self, ctx: commands.Context):
        embed = discord.Embed(
            title="Status da Segurança",
            color=0x5865F2,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Usuários com risco", value=str(len(self.db.risk_scores)))
        embed.add_field(name="Usuários sinalizados", value=str(len(self.db.flagged_users)))
        embed.add_field(name="Alertas", value=str(len(self.db.alert_history)))
        await ctx.send(embed=embed)

    @security_group.command(name="alerts")
    @commands.has_permissions(administrator=True)
    async def security_alerts(self, ctx: commands.Context):
        if not self.db.alert_history:
            await ctx.send("Nenhum alerta registrado.")
            return

        embed = discord.Embed(title="Últimos Alertas", color=0xFF8800)
        for item in self.db.alert_history[-10:]:
            embed.add_field(
                name=item["type"],
                value=item["details"][:120],
                inline=False
            )
        await ctx.send(embed=embed)

    @security_group.command(name="riskscore")
    @commands.has_permissions(administrator=True)
    async def security_riskscore(self, ctx: commands.Context, member: discord.Member):
        score = self.db.get_risk(member.id)
        embed = discord.Embed(
            title=f"Risk Score - {member}",
            description=f"Pontuação: `{score}`",
            color=0x5865F2
        )
        await ctx.send(embed=embed)

    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        for uid in list(self._cmd_timestamps.keys()):
            self._prune(self._cmd_timestamps[uid], COMMAND_SPAM_WINDOW)

        for uid in list(self._msg_timestamps.keys()):
            self._prune(self._msg_timestamps[uid], MSG_SPAM_WINDOW)

        expired = [uid for uid, until in self._cmd_cooldowns.items() if datetime.utcnow() >= until]
        for uid in expired:
            del self._cmd_cooldowns[uid]

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityCog(bot))