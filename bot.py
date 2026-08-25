"""
╔══════════════════════════════════════════════════════════════════╗
║                    🦇  VAMPY BOT  🖤                             ║
║             Uma morceguinha alegre e atentada                    ║
║                         v1.0 — Online                            ║
╚══════════════════════════════════════════════════════════════════╝

Inspirada na Lilu 🐱 — mesma alma cheia de carinho, agora com asinhas
e uma pontinha de arte! A Vampy vive aparecendo do nada, adora pregar
peguinhas e responde a galera igualzinho a Lilu faz.

Módulos:
  • Diálogo — Vampy aprende a conversar, responde gatilhos e
              aparece do nada de vez em quando pra dar as caras
"""

import discord
from discord.ext import commands
import asyncio
import os
import json
import random
from datetime import datetime, timezone
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()

# ══════════════════════════════════════════════════════════════════
#  ⚙️  CONFIGURAÇÕES GERAIS
# ══════════════════════════════════════════════════════════════════

TOKEN = os.getenv("VAMPY_TOKEN") or os.getenv("TOKEN")

# Arquivo de aprendizado de diálogo
DIALOGO_FILE = "vampy_dialogo.json"

# ══════════════════════════════════════════════════════════════════
#  🤖  SETUP DO BOT
# ══════════════════════════════════════════════════════════════════

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix=["v!", "V!", "vampy ", "Vampy "], intents=intents)
bot.remove_command("help")   # usaremos help customizado

# ══════════════════════════════════════════════════════════════════
#  🦇  PALETA DE CORES DA VAMPY
# ══════════════════════════════════════════════════════════════════

COR_ROXA_ESCURA = 0x2d1b4e   # fundo escuro de morcego
COR_ROXA        = 0x9b30ff   # roxo vampiresco
COR_ROSA        = 0xFF2E9A   # rosa choque, atentada
COR_VERDE       = 0x00e676   # verde OK
COR_VERMELHO    = 0xFF5252   # erro / aviso
COR_DOURADO     = 0xFFD700   # especial

# ══════════════════════════════════════════════════════════════════
#  💾  PERSISTÊNCIA DO APRENDIZADO DE DIÁLOGO
# ══════════════════════════════════════════════════════════════════

def _carregar_dialogo() -> dict:
    if os.path.exists(DIALOGO_FILE):
        try:
            with open(DIALOGO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"respostas": {}}


def _salvar_dialogo(db: dict):
    with open(DIALOGO_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════
#  🦇  BANCO DE RESPOSTAS-SEED — A PERSONALIDADE DA VAMPY
# ══════════════════════════════════════════════════════════════════
# alegre, atentada, adora aparecer do nada e pregar peça na galera

_RESPOSTAS_SEED = {

    # ── Bom dia ──────────────────────────────────────────────────
    "bom dia": [
        "*cai da forração* BOM DIAAA!! ☀️🦇",
        "bom dia!! já acordei de cabeça pra baixo mesmo!! 🦇✨",
        "*bate as asinhas* bom diaaa!! 🖤☀️",
        "bom dia bom dia!! quem gritou meu nome?? 🦇😈",
        "*se pendura no lustre* bom dia pra vocês!! 🌙➡️☀️🦇",
        "boooom dia!! hoje eu tô especialmente atentada!! 😈🦇",
        "bom dia!! (voando de susto na sua direção) 🦇💨",
    ],

    # ── Boa tarde ────────────────────────────────────────────────
    "boa tarde": [
        "boa tardeee!! *espreguiça as asinhas* 🦇☀️",
        "*aparece do nada* boa tarde!! 😈🖤",
        "boa tarde!! ainda intacta de sono mas cheia de arte!! 🦇✨",
        "boa tardeee!! bora aprontar alguma?? 😈🦇",
        "*balança de cabeça pra baixo* boa tarde!! 🌙🦇",
        "boa tarde boa tarde!! tô voando por aí!! 🦇💜",
    ],

    # ── Boa noite ────────────────────────────────────────────────
    "boa noite": [
        "AGORA SIM!! minha hora favorita!! boa noite!! 🌙🦇✨",
        "*abre as asinhas toda animada* boa noite!! 🦇🌙",
        "boa noite!! hora de voar por aí fazendo arte!! 😈🦇",
        "*se pendura de cabeça pra baixo pra dormir* boa noite!! 🦇💤",
        "boa noiteee!! finalmente o meu horário nobre!! 🌙✨🦇",
        "boa noite!! não deixa eu aprontar sozinha não, hein!! 😈🖤",
    ],

    # ── Chamada pelo nome ────────────────────────────────────────
    "vampy": [
        "*aparece do nada* SIM?? me chamou?? 🦇✨",
        "hm?? quem tá me chamando?? 😈🦇",
        "*desce voando de cabeça pra baixo* oi!! 🦇🖤",
        "eii, tô aqui!! *bate as asinhas* 🦇✨",
        "*surge atrás de você* boo!! me chamou?? 😈🦇",
        "presente!! e já tô pensando numa peça pra pregar!! 😈🦇",
        "*se pendura no galho mais próximo* oi oi!! 🦇🌙",
        "quem foi que me chamou hein?? 🦇👀",
        "*pisca um olho* sim, moço/moça?? 😈🦇",
        "tô aqui, voando por perto!! 🦇💨",
    ],

    # ── Oi / Olá ─────────────────────────────────────────────────
    "oi": [
        "OIII!! *voa até você* 🦇✨",
        "oi oi!! bora aprontar?? 😈🦇",
        "*aparece do nada* boo!! oi!! 🦇🖤",
        "oiii, tudo bem por aí?? 🦇🌙",
        "*bate as asinhas de felicidade* oiii!! 🦇✨",
    ],

    # ── Obrigado(a) ──────────────────────────────────────────────
    "obrigad": [
        "de nadaaa!! *faz uma reverência voando* 🦇💜",
        "imaaaa!! qualquer coisa é só chamar!! 🦇✨",
        "*sorri mostrando as presinhas* disponha!! 😈🦇",
        "sempre às ordens (e às traquinagens) 😈🦇🖤",
    ],

    # ── Tchau ────────────────────────────────────────────────────
    "tchau": [
        "tchauzinho!! vou voar por aí então!! 🦇💨",
        "*acena com a asinha* até mais!! 🦇✨",
        "flw!! vou aprontar em outro canto agora!! 😈🦇",
        "tchau tchau!! volto quando ninguém tiver esperando!! 🦇😈",
    ],

    # ── Risada ───────────────────────────────────────────────────
    "kkk": [
        "KKKKKKK exatamente o que eu queria ouvir!! 😈🦇",
        "*rindo de cabeça pra baixo* kkkkkk 🦇✨",
        "hahaha adoro quando dá certo!! 😈🦇",
        "KSKSKS foi mal, foi mal (não foi) 😈🦇🖤",
    ],

    # ── Tristeza (acolhimento, sem gracinha) ───────────────────
    "triste": [
        "*pousa do seu lado bem devagarinho* tá tudo bem?? tô aqui 🦇🖤",
        "eii, vem cá... *enrola a asinha em você* quer conversar?? 🦇💜",
        "nada de peça agora, só quero saber se você tá bem 🦇🖤",
    ],
}


def _checar_gatilho_generico(texto: str, db: dict) -> str | None:
    texto_lower = texto.lower().strip()
    if texto_lower in db["respostas"]:
        return texto_lower
    for chave in db["respostas"]:
        if chave in texto_lower:
            return chave
    return None


# ══════════════════════════════════════════════════════════════════
#  🦇  COG DE DIÁLOGO — O CORAÇÃO DA VAMPY
# ══════════════════════════════════════════════════════════════════

class DialogoCog(commands.Cog, name="VampyDialogo"):
    """🦇 Sistema de diálogo e aprendizado da Vampy."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = _carregar_dialogo()
        for chave, resps in _RESPOSTAS_SEED.items():
            if chave not in self.db["respostas"]:
                self.db["respostas"][chave] = resps
        _salvar_dialogo(self.db)

        # Contexto de conversa por canal (pra Vampy "acompanhar" a galera)
        self._contexto: dict[int, deque] = defaultdict(lambda: deque(maxlen=10))

        # Cooldown pra não spammar
        self._ultimo_resp: dict[int, datetime] = {}
        self._cooldown_resp = 3   # segundos

    def _checar_gatilho(self, texto: str) -> str | None:
        return _checar_gatilho_generico(texto, self.db)

    def _responder(self, chave: str) -> str:
        resps = self.db["respostas"].get(chave, [])
        return random.choice(resps) if resps else ""

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        self._contexto[message.channel.id].append({
            "user": message.author.display_name,
            "user_id": message.author.id,
            "content": message.content,
            "time": datetime.now(timezone.utc).isoformat(),
        })

        vampy_chamada = (
            self.bot.user in message.mentions
            or "vampy" in message.content.lower()
        )

        now = datetime.now(timezone.utc)
        ultimo = self._ultimo_resp.get(message.channel.id)
        if ultimo and (now - ultimo).total_seconds() < self._cooldown_resp:
            return

        # ── Resposta por gatilho ──────────────────────────
        chave = self._checar_gatilho(message.content)
        if chave and (vampy_chamada or random.random() < 0.25):
            resp = self._responder(chave)
            if resp:
                self._ultimo_resp[message.channel.id] = now
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.5))
                await message.reply(resp, mention_author=False)
                return

        # ── Chamada genérica (sem gatilho específico) ──────
        if vampy_chamada and not chave:
            respostas_genericas = [
                "*aparece do nada* boo!! oi!! 🦇✨",
                "hm?? me chamou?? 😈🦇",
                "*desce de cabeça pra baixo* oi!! 🦇🖤",
                "eii, tô aqui voando por perto!! 🦇💨",
                "*surge atrás de você* boo!! 😈🦇",
                "presente!! já tava pensando numa arte pra fazer!! 😈🦇",
                "*bate as asinhas* oi oi!! o que foi?? 🦇✨",
                "*pisca um olho* sim?? 😈🖤",
                "*pendura de cabeça pra baixo no galho mais perto* oi!! 🦇🌙",
                "quem me chamou hein?? 🦇👀",
                "tô aqui!! partiu aprontar algo?? 😈🦇",
                "*voa em círculos animada* oii!! 🦇✨",
                "*se esconde atrás da cortina e espia* achou!! 😈🦇",
                "AAAAH oi!! quase me pegou de surpresa!! 🦇💫",
                "*mostra as presinhas sorrindo* diga!! 😈🦇",
            ]
            self._ultimo_resp[message.channel.id] = now
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.5, 1.2))
            await message.reply(random.choice(respostas_genericas), mention_author=False)
            return

        # ── Aparece do nada (chance baixa, sem precisar ser chamada) ──
        elif not vampy_chamada and not chave and random.random() < 0.02:
            _EXPRESSOES_ESPONTANEAS = [
                "*aparece do nada* boo!! 🦇✨",
                "*surge pendurada no teto* oi, gente!! 🦇🖤",
                "*voa passando rapidinho* nham!! 😈🦇",
                "*se esconde atrás de alguém e espia* 👀🦇",
                "*bate as asinhas distraída* 🦇💜",
                "hihihi tô só observando por aqui!! 😈🦇",
                "*pendura de cabeça pra baixo num canto* 🦇🌙",
                "*aparece do nada e some de novo* boo!! 🦇💨",
                "psiu... alguém quer aprontar comigo?? 😈🦇",
                "*mostra as presinhas num sorriso* 🦇✨",
                "*rodopia no ar toda animada* 🦇🖤",
                "hm... o que será que eu posso aprontar hoje?? 😈🦇",
            ]
            self._ultimo_resp[message.channel.id] = now
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.3, 0.9))
            await message.channel.send(random.choice(_EXPRESSOES_ESPONTANEAS))

    # ── Comandos de aprendizado ────────────────────────────

    @commands.command(name="ensinar")
    @commands.has_permissions(manage_guild=True)
    async def ensinar(self, ctx: commands.Context, gatilho: str, *, resposta: str):
        gatilho = gatilho.lower().strip()
        self.db["respostas"].setdefault(gatilho, [])
        self.db["respostas"][gatilho].append(resposta)
        _salvar_dialogo(self.db)
        embed = discord.Embed(
            title="🦇 Aprendido!!",
            description=f"quando alguém disser **{gatilho}**, eu posso responder:\n> {resposta}",
            color=COR_VERDE,
        )
        embed.set_footer(text="🦇 Vampy • aprendizado")
        await ctx.send(embed=embed)

    @commands.command(name="esquecer")
    @commands.has_permissions(manage_guild=True)
    async def esquecer(self, ctx: commands.Context, *, gatilho: str):
        gatilho = gatilho.lower().strip()
        if gatilho in self.db["respostas"]:
            del self.db["respostas"][gatilho]
            _salvar_dialogo(self.db)
            await ctx.send(embed=discord.Embed(
                title="🦇 Esquecido!!",
                description=f"apaguei tudo que eu sabia sobre **{gatilho}**!! 🖤",
                color=COR_ROSA,
            ))
        else:
            await ctx.send(embed=discord.Embed(
                title="🤔 Hmm!!",
                description=f"eu não conhecia esse gatilho: **{gatilho}**",
                color=COR_VERMELHO,
            ))

    @commands.command(name="gatilhos")
    async def gatilhos(self, ctx: commands.Context):
        chaves = ", ".join(f"`{k}`" for k in self.db["respostas"].keys())
        embed = discord.Embed(
            title="🦇 Tudo que eu sei responder",
            description=chaves or "ainda não aprendi nada!! me ensina algo!! 🦇",
            color=COR_ROXA,
        )
        embed.set_footer(text="🦇 Vampy • v!ensinar <gatilho> <resposta>")
        await ctx.send(embed=embed)

    @commands.command(name="simular")
    async def simular(self, ctx: commands.Context, *, texto: str):
        chave = self._checar_gatilho(texto)
        resp = self._responder(chave) if chave else "*inclina a cabecinha* eu não saberia responder isso ainda!! 🦇🤔"
        await ctx.send(embed=discord.Embed(
            title="🦇 Simulação",
            description=resp,
            color=COR_DOURADO,
        ))


# ══════════════════════════════════════════════════════════════════
#  🦇  EVENTOS GLOBAIS
# ══════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"\n{'═'*52}")
    print(f"  🦇  VAMPY BOT — ONLINE")
    print(f"  Logado como: {bot.user} ({bot.user.id})")
    print(f"  Servidores: {len(bot.guilds)}")
    print(f"{'═'*52}\n")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="a galera de cabeça pra baixo 🦇🖤"
        )
    )


@bot.command(name="help", aliases=["ajuda", "h"])
async def vampy_help(ctx: commands.Context):
    embed = discord.Embed(
        title="🦇 Vampy Bot — Ajuda",
        description="oi!! sou a Vampy, uma morceguinha alegre e atentada!! adoro aparecer do nada!! 🦇🖤",
        color=COR_ROXA,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(
        name="💬 Diálogo & Aprendizado",
        inline=False,
        value=(
            "`v!ensinar <gatilho> <resposta>` — me ensina uma resposta nova\n"
            "`v!esquecer <gatilho>` — apaga o que eu sei sobre um gatilho\n"
            "`v!gatilhos` — lista tudo que eu já sei\n"
            "`v!simular <texto>` — testa o que eu responderia\n"
            "*(e de vez em quando eu apareço do nada sozinha!! 😈🦇)*"
        )
    )
    embed.set_footer(text="🦇 Vampy Bot • prefixo: v! ou vampy ")
    await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    latencia = round(bot.latency * 1000)
    cor = COR_VERDE if latencia < 100 else (COR_DOURADO if latencia < 200 else COR_VERMELHO)
    await ctx.send(embed=discord.Embed(
        title="🏓 Pong!!",
        description=f"latência: `{latencia}ms` 🦇🖤",
        color=cor,
    ))


@bot.command(name="vampy")
async def vampy_info(ctx: commands.Context):
    embed = discord.Embed(
        title="🖤 Oi!! Sou a Vampy!!",
        description=(
            "uma morceguinha alegre e atentada que vive aparecendo do nada!! 🦇✨\n\n"
            "adoro conversar, pregar peguinhas e voar por aí de cabeça pra baixo!! 😈🦇\n\n"
            "use `v!help` pra ver tudo que sei fazer!!"
        ),
        color=COR_ROXA,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text="🦇 Vampy Bot v1.0")
    await ctx.send(embed=embed)


# ══════════════════════════════════════════════════════════════════
#  🚀  INICIALIZAÇÃO
# ══════════════════════════════════════════════════════════════════

async def _main():
    async with bot:
        await bot.add_cog(DialogoCog(bot))
        if not TOKEN:
            print("❌ ERRO: token não encontrado! Crie um .env com VAMPY_TOKEN=seu_token")
            return
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(_main())
