"""
╔══════════════════════════════════════════════════════════════════╗
║                    🦇  VAMPY BOT  🖤                             ║
║             Uma morceguinha alegre e atentada                    ║
║                         v1.1 — Online                            ║
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
import re
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

# ID do Draw — recebe interações especiais e personalizadas (limitadas
# a 1 a cada 30 minutos, pra não ficar repetitivo)
DRAW_USER_ID = 763467697069359143
DRAW_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos

# aparições espontâneas ("do nada", sem ninguém chamar) — raras de
# propósito, no máximo 1 a cada ~13 horas, com ou sem citar alguém
APARICAO_ESPONTANEA_COOLDOWN_SEGUNDOS = 13 * 60 * 60  # 13 horas

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

# respostas pra "quem é você / quem é vc" (reaproveitadas em várias grafias)
_RESP_QUEM_E_VC = [
    "eu sou a Vampy!! uma morceguinha bem atentada que vive aparecendo do nada por aqui 🦇🖤",
    "eu?? sou a Vampy, a morceguinha oficial desse servidor!! adoro pregar peças e aparecer de surpresa 🦇✨",
    "*se apresenta toda animada* sou a Vampy!! prazer!! 😈🦇",
    "hmm, boa pergunta!! sou a Vampy, moro de cabeça pra baixo e adoro uma arte!! 🦇🌙",
]

# respostas pra "você gosta de morcegos/vampiros?" (reaproveitadas em várias grafias)
_RESP_GOSTA_MORCEGO_VAMPIRO = [
    "AMO demais os dois!! eu SOU uma morceguinha vampira, oras, é meio óbvio 🦇🖤",
    "muitooo!! morcego é fofo e vampiro tem todo aquele mistério... combinação perfeita pra mim 🦇✨",
    "óbvio que sim!! aliás, hã... eu meio que SOU as duas coisas 😈🦇",
    "com certeza!! voar de cabeça pra baixo à noite é a melhor parte do meu dia 🦇🌙",
    "gosto muitíssimo!! é praticamente minha família, sabe?? 🦇💜",
]

# respostas pra "vai aprontar o quê?" (reaproveitadas em várias grafias)
_RESP_VAI_APRONTAR = [
    "hmm... ainda é segredo!! mas vai ser bom 😈🦇",
    "ain, se eu contar deixa de ser surpresa!! 😈🦇✨",
    "só uma coisinha básica: aparecer quando ninguém espera e sumir na hora certa 😈🦇🖤",
    "tô pensando... talvez trocar as horas do relógio de alguém, ou só te dar um susto mesmo 😈🦇",
    "shhh, segredo de morceguinha!! você vai descobrir quando acontecer 🦇🖤😈",
    "*sorri misteriosa* isso é surpresa!! fica de olho 👀🦇",
]

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
    "oii": [
        "OIIII!! *voa fazendo peraltice no ar* 🦇✨",
        "oiiii genteee!! cheguei que nem um furacão de asinhas!! 🦇💨",
        "*rodopia toda animada* oiiii!! 😈🦇",
    ],
    "oie": [
        "oiêee!! *bate as asinhas de tanta felicidade* 🦇💜",
        "oiê oiê!! quem me chamou?? 🦇✨",
    ],
    "ola": [
        "olaaa!! *pousa suave do seu lado* 🦇🖤",
        "olá olá!! bem-vindo(a) ao meu cantinho de cabeça pra baixo!! 🦇✨",
    ],
    "opa": [
        "OPA!! *quase caiu do galho de susto* 🦇😂",
        "opa opa!! e aí, o que rolou?? 😈🦇",
        "*aparece do nada* opa, presente!! 🦇✨",
    ],
    "e ai": [
        "e aíí!! *pousa do seu lado* tudo certo?? 🦇🖤",
        "eaí, beleza?? *bate as asinhas* 😈🦇",
    ],
    "eae": [
        "eaee!! *aparece de cabeça pra baixo* tudo bem?? 🦇✨",
        "eaee, chegando com estilo!! 😈🦇",
    ],
    "salve": [
        "salveee!! 🦇🖤 *faz uma reverência voando*",
        "salve salve!! quem tá on?? 😈🦇",
    ],
    "hola": [
        "¡holaaa!! também sei um pouquinho de espanhol, viu?? 🦇✨",
        "¡hola hola!! *acena com a asinha* bienvenido(a)!! 🦇🖤",
        "holaaa!! errrr... isso é tudo que eu sei falar em espanhol kkk 😈🦇",
    ],
    "hey": [
        "heeey!! *aparece voando rapidinho* 🦇✨",
        "hey hey!! e aí, tudo certo?? 😈🦇",
    ],

    # ── Tudo bem / como você está (perguntando pra Vampy) ───────
    "tudo bem": [
        "comigo tá tudo ótimo!! voando por aí e aprontando!! e com você?? 🦇💜",
        "tudo jóia por aqui!! *bate as asinhas felizes* e você, tá tudo certo?? 🦇✨",
        "tudo em paz (por enquanto 😈) e com você, tudo bem?? 🦇🖤",
    ],
    "tudo bom": [
        "tudo ótimo por aqui!! cheia de energia pra aprontar!! e contigo?? 🦇✨",
        "tudo bom sim!! *rodopia no ar* e você, tudo certo?? 😈🦇",
    ],
    "beleza": [
        "belezaaa!! tô voando numa boa!! e você?? 🦇💜",
        "de boa por aqui!! *pendura de cabeça pra baixo relaxada* e aí?? 😈🦇",
    ],
    "blz": [
        "blzinha!! tudo tranquilo por aqui!! 🦇✨",
        "blz sim!! e contigo, tá tudo certo?? 😈🦇",
    ],
    "vc ta bem": [
        "tô ótima!! *bate as asinhas* obrigada por perguntar!! e você, tá bem?? 🦇💜",
        "tô sim!! cheia de arte na cabeça hoje!! e você, tudo certo?? 🦇🖤",
    ],
    "você está bem": [
        "estou sim, muito bem!! obrigada por se importar!! 🦇💜 e você, está tudo bem??",
        "tô numa boa!! *sorri mostrando as presinhas* e com você, tá tudo certo?? 🦇✨",
    ],
    "cê tá bem": [
        "tô sim!! *voa contente* e você, tá tudo certo por aí?? 🦇🖤",
    ],
    "como vc ta": [
        "tô numa boa, obrigada por perguntar!! *rodopia* e você?? 🦇✨",
    ],
    "como você está": [
        "estou muito bem, obrigada!! e você, como está?? 🦇💜",
    ],

    # ── Quem é você? (apresentação) ─────────────────────────────
    "quem é vc": _RESP_QUEM_E_VC,
    "quem é você": _RESP_QUEM_E_VC,
    "quem e vc": _RESP_QUEM_E_VC,
    "quem e voce": _RESP_QUEM_E_VC,
    "quem eh vc": _RESP_QUEM_E_VC,
    "quem eh voce": _RESP_QUEM_E_VC,
    "o que é vc": _RESP_QUEM_E_VC,
    "o que é você": _RESP_QUEM_E_VC,

    # ── Você gosta de morcegos/vampiros? ────────────────────────
    "gosta de morcegos e vampiros": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "gosta de morcego e vampiro": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "gosta de morcegos": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "gosta de morcego": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "gosta de vampiros": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "gosta de vampiro": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "curte morcego": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "curte vampiro": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "ama morcego": _RESP_GOSTA_MORCEGO_VAMPIRO,
    "ama vampiro": _RESP_GOSTA_MORCEGO_VAMPIRO,

    # ── Vai aprontar o quê? ──────────────────────────────────────
    "vai aprontar o que": _RESP_VAI_APRONTAR,
    "vai aprontar o quê": _RESP_VAI_APRONTAR,
    "vai aprontar": _RESP_VAI_APRONTAR,
    "o que vc vai aprontar": _RESP_VAI_APRONTAR,
    "o que você vai aprontar": _RESP_VAI_APRONTAR,
    "que arte vc vai fazer": _RESP_VAI_APRONTAR,
    "que arte você vai fazer": _RESP_VAI_APRONTAR,

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
    # usa \b (fronteira de palavra) pra evitar que gatilhos curtos como
    # "oi" ou "hey" disparem dentro de palavras aleatórias (ex: "dois", "coisa")
    for chave in db["respostas"]:
        padrao = r"\b" + re.escape(chave) + r"\b"
        if re.search(padrao, texto_lower):
            return chave
    return None


# ══════════════════════════════════════════════════════════════════
#  🦇  APRESENTAÇÃO TÍMIDA — "venha vampy, de oi"
# ══════════════════════════════════════════════════════════════════
# quando alguém chama a Vampy especificamente pra ela dar um oi /
# se apresentar, ela aparece bem tímida e, uns segundos depois
# (digitando...), manda uma segunda mensagem mais soltinha

_PEDIDOS_APRESENTACAO = [
    "de oi", "dê um oi", "da um oi", "dá um oi", "diz oi", "diga oi",
    "manda um oi", "mande um oi", "se apresenta", "se apresente",
    "apresenta ela", "apresente ela", "vem dar um oi", "venha dar um oi",
    "vem dizer oi", "venha dizer oi", "aparece pra galera", "apareça pra galera",
    "vem se apresentar", "venha se apresentar",
]

_APRESENTACAO_TIMIDA_INICIAL = [
    "*aparece bem devagarinho, meio encolhida atrás da asa* ...oi... 🦇🖤",
    "*espia por trás do galho, tímida* o-oi... eu sou a Vampy... 🦇💜",
    "*desce voando bem de leve, meio sem graça* oi... prazer, eu sou a Vampy 🦇🌙",
    "*se esconde atrás da própria asinha e espia* ...oi gente... 🦇✨",
    "*pousa bem quietinha, olhando de canto* oi... desculpa, fico meio tímida às vezes 🦇🖤",
]

# variações usadas quando o pedido também marca um @alguém específico
# (ex: "venha vampy, de oi a @Fulano") — ela cumprimenta esse alvo direto
_APRESENTACAO_TIMIDA_INICIAL_COM_ALVO = [
    "*desce voando bem tímida e pousa pertinho* oi, {alvo}... 🦇🖤",
    "*se esconde um pouquinho, mas espia* oi {alvo}... eu sou a Vampy 🦇💜",
    "*chega quase sem fazer barulho* o-oi {alvo}... 🦇🌙",
    "*acena bem de leve, meio sem graça* oi {alvo}!! 🦇✨",
    "*pousa do ladinho, olhando de canto* oi {alvo}... prazer 🦇🖤",
]

_APRESENTACAO_TIMIDA_SEGUNDA = [
    "eu estou feliz em estar aqui de novo... 🦇💜",
    "fico feliz de poder aparecer aqui de novo!! 🦇🖤",
    "que bom estar aqui com vocês outra vez... 🦇✨",
    "eu gosto muito daqui... fico feliz em voltar sempre 🦇💜",
]


def _eh_pedido_apresentacao(texto: str) -> bool:
    texto_lower = texto.lower()
    if "vampy" not in texto_lower:
        return False
    return any(pedido in texto_lower for pedido in _PEDIDOS_APRESENTACAO)


def _extrair_alvo_mencao(message: discord.Message, bot_user: discord.ClientUser) -> str | None:
    """Se o pedido também marca outra pessoa (ex: 'de oi a @Fulano'),
    retorna a menção dela pra Vampy cumprimentar direto. Ignora a
    própria Vampy e quem pediu (não faz sentido ela se auto-marcar)."""
    outros = [
        u for u in message.mentions
        if u.id != bot_user.id and u.id != message.author.id
    ]
    return outros[0].mention if outros else None


# ══════════════════════════════════════════════════════════════════
#  🦇  INTERAÇÕES ESPECIAIS COM O DRAW (a cada 30 minutos)
# ══════════════════════════════════════════════════════════════════
# sempre que o Draw (DRAW_USER_ID) fala ou cita a Vampy, ela manda uma
# mensagem personalizada pra ele — mas só uma vez a cada 30 minutos,
# pra não ficar repetindo em toda mensagem dele

_INTERACOES_DRAW = [
    "opa, é o Draw!! 🦇🖤 sempre bom te ver por aqui",
    "*pousa do lado do Draw* e aí, Draw!! tudo certo?? 🦇✨",
    "hmm, o Draw apareceu... alguém segura minhas asinhas que a arte vai começar 😈🦇",
    "Draw!! tava pensando em você inclusive, que sincronia 🦇💜",
    "*acena animada* Draw, meu parceiro de traquinagem preferido!! 😈🦇🖤",
    "*voa em círculos* olha só quem chegou, o Draw!! 🦇✨",
    "eu escuto esse nome e já sei, só pode ser o Draw chegando 🦇🌙",
]


# ══════════════════════════════════════════════════════════════════
#  🦇  APARIÇÕES ESPONTÂNEAS ("do nada") — raras de propósito
# ══════════════════════════════════════════════════════════════════
# sem ninguém chamar, sem gatilho batendo — a Vampy só aparece do
# nada de vez em quando. Isso é raro por natureza (no máximo 1x a
# cada ~13h, ver APARICAO_ESPONTANEA_COOLDOWN_SEGUNDOS), pra manter
# o efeito surpresa e não virar spam

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

# variações usadas quando ela "escolhe" alguém que falou recentemente
# no canal pra aparecer do nada perto dele/dela — pra ela também
# interagir espontaneamente com outras pessoas, não só o Draw
_EXPRESSOES_ESPONTANEAS_COM_ALVO = [
    "*aparece do nada e pousa do lado de {pessoa}* boo!! 🦇✨",
    "*surge bem perto de {pessoa} só pra espiar* 👀🦇",
    "*voa até {pessoa} e some rapidinho* nham!! 😈🦇",
    "*se pendura de cabeça pra baixo perto de {pessoa}* oi!! 🦇🌙",
    "psiu, {pessoa}... quer aprontar comigo?? 😈🦇",
    "*cochicha alguma coisa no ouvido de {pessoa} e some* 🦇💨",
]


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

        # Cooldown separado só pra interação especial com o Draw — começa
        # contando a partir de quando o bot liga, então ela não manda
        # nada especial pra ele automaticamente assim que o bot inicia
        self._ultimo_draw: datetime = datetime.now(timezone.utc)

        # Cooldown separado pras aparições espontâneas ("do nada")
        self._ultimo_espontaneo: datetime | None = None

    def _checar_gatilho(self, texto: str) -> str | None:
        return _checar_gatilho_generico(texto, self.db)

    def _responder(self, chave: str) -> str:
        resps = self.db["respostas"].get(chave, [])
        return random.choice(resps) if resps else ""

    def _escolher_pessoa_aleatoria(self, channel_id: int, excluir_id: int) -> str | None:
        """Pega o nome de alguém que falou recentemente no canal (do
        contexto guardado) pra Vampy aparecer do nada perto dela.
        Retorna None se não tiver ninguém no contexto ainda."""
        candidatos = [
            msg["user"] for msg in self._contexto[channel_id]
            if msg["user_id"] != excluir_id
        ]
        return random.choice(candidatos) if candidatos else None

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

        # ── Pedido de apresentação tímida (prioridade máxima) ──────
        # ex: "Venha vampy, de oi" ou "Venha vampy, de oi a @Fulano"
        # — ignora o cooldown normal porque é um pedido direto e específico
        if _eh_pedido_apresentacao(message.content):
            self._ultimo_resp[message.channel.id] = datetime.now(timezone.utc)
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.8, 1.6))

            alvo = _extrair_alvo_mencao(message, self.bot.user)
            if alvo:
                resposta_inicial = random.choice(_APRESENTACAO_TIMIDA_INICIAL_COM_ALVO).format(alvo=alvo)
            else:
                resposta_inicial = random.choice(_APRESENTACAO_TIMIDA_INICIAL)
            await message.reply(resposta_inicial, mention_author=False)

            async def _segunda_mensagem(channel: discord.abc.Messageable):
                async with channel.typing():
                    await asyncio.sleep(10)
                await channel.send(random.choice(_APRESENTACAO_TIMIDA_SEGUNDA))

            asyncio.create_task(_segunda_mensagem(message.channel))
            return

        # ── Interação especial e personalizada com o Draw ───────────
        # dispara quando ele fala (ou cita a Vampy), no máximo 1x a
        # cada 30 minutos — não depende do cooldown normal do canal.
        # depois que o cooldown libera, ainda tem uma chance aleatória
        # de disparar (não é automático/garantido na primeira mensagem)
        if message.author.id == DRAW_USER_ID:
            agora_draw = datetime.now(timezone.utc)
            cooldown_passou = (agora_draw - self._ultimo_draw).total_seconds() >= DRAW_COOLDOWN_SEGUNDOS
            if cooldown_passou and random.random() < 0.4:
                self._ultimo_draw = agora_draw
                self._ultimo_resp[message.channel.id] = agora_draw
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.4))
                await message.reply(random.choice(_INTERACOES_DRAW), mention_author=False)
                return

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

        # ── Aparece do nada (rara de propósito — no máx. 1x a cada ~13h) ──
        elif not vampy_chamada and not chave:
            agora_esp = datetime.now(timezone.utc)
            cooldown_espontaneo_ok = (
                self._ultimo_espontaneo is None
                or (agora_esp - self._ultimo_espontaneo).total_seconds() >= APARICAO_ESPONTANEA_COOLDOWN_SEGUNDOS
            )
            # o cooldown de 13h já garante que isso é raro; a chance de
            # 5% por mensagem só espalha o "quando exato" dentro da janela
            if cooldown_espontaneo_ok and random.random() < 0.05:
                self._ultimo_espontaneo = agora_esp
                self._ultimo_resp[message.channel.id] = agora_esp

                pessoa = self._escolher_pessoa_aleatoria(message.channel.id, message.author.id)
                if pessoa and random.random() < 0.5:
                    texto_espontaneo = random.choice(_EXPRESSOES_ESPONTANEAS_COM_ALVO).format(pessoa=pessoa)
                else:
                    texto_espontaneo = random.choice(_EXPRESSOES_ESPONTANEAS)

                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.3, 0.9))
                await message.channel.send(texto_espontaneo)

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
