"""
╔══════════════════════════════════════════════════════════════════╗
║                    🦇  VAMPY BOT  🖤                             ║
║             Uma morceguinha alegre e atentada                    ║
║                         v1.3 — Online                            ║
╚══════════════════════════════════════════════════════════════════╝

Inspirada na Lilu 🐱 — mesma alma cheia de carinho, agora com asinhas
e uma pontinha de arte! A Vampy vive aparecendo do nada, adora pregar
peguinhas e responde a galera igualzinho a Lilu faz.

Módulos:
  • Diálogo — Vampy aprende a conversar, responde gatilhos e
              aparece do nada de vez em quando pra dar as caras

Changelog v1.3:
  • CORRIGIDO: as reações personalizadas de "opa, chegou o Fulano!!"
    (Draw, Ghost, namorada do Ghost, Dalia, Orochi, Felipe) estavam
    disparando sempre que alguém MARCAVA essas pessoas com @menção
    dentro de uma mensagem qualquer — mesmo quando a mensagem não
    tinha nada a ver com elas terem chegado/falado. Exemplo real: o
    Felipe mandou "Vampy joga uma bomba atômica no @Draw Mori" e a
    Vampy respondeu "olha só quem chegou, o Draw!!", como se o Draw
    tivesse acabado de aparecer — só porque o nome dele foi citado
    como ALVO da mensagem de outra pessoa, não porque ele mesmo
    escreveu algo. Agora essas reações de "chegou fulano" só disparam
    quando é a PRÓPRIA pessoa (dono do ID) quem manda a mensagem —
    ser apenas citado/marcado por outra pessoa não conta mais.

Changelog v1.2:
  • CORRIGIDO: reply (responder) a uma mensagem de alguém, com a
    notificação de menção ligada, fazia o Discord incluir aquela
    pessoa em message.mentions mesmo sem ela ter sido digitada no
    texto. Isso fazia a Vampy achar que "citaram o Ghost/Draw/etc"
    só porque alguém respondeu uma mensagem qualquer deles. Agora só
    contam @menções DIGITADAS de verdade no texto cru da mensagem.
  • CORRIGIDO: proteção contra processar a mesma mensagem duas vezes
    (o que causava respostas duplicadas pra mesma mensagem).
  • CORRIGIDO: as reações especiais de "fulano foi citado por outra
    pessoa" (Draw, Ghost, namorada do Ghost, Dalia, Orochi) estavam
    disparando quando o nome dela só aparecia solto numa frase (ex:
    "a orochi é muito ativa"), mesmo sem ninguém estar de fato
    chamando/marcando ela. Agora essas reações só disparam com uma
    @menção DIGITADA de verdade (marcou o nome dela no Discord de
    propósito) — citar o nome em texto puro não conta mais sozinho.
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
# a 1 a cada 30 minutos, pra não ficar repetitivo). IMPORTANTE: essa
# interação especial ("opa, chegou o Draw!!") só dispara quando é o
# PRÓPRIO Draw quem manda a mensagem — ser apenas citado/@marcado por
# outra pessoa não conta mais (ver changelog v1.3)
DRAW_USER_ID = 763467697069359143
DRAW_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos
# apelidos/nomes do Draw — mantidos apenas como referência/utilitário,
# não são mais usados pra disparar a reação de "chegou" por citação
DRAW_APELIDOS = ["draw"]

# ID de alguém que a Vampy sempre zoa quando ele fala — reação na hora,
# sem cooldown, do jeitinho encrenqueira dela ("xispa daqui" etc.)
XISPA_USER_ID = 1374346793957064735

# ID do Ghost — assim como o Draw, recebe interações especiais e
# personalizadas (limitadas a 1 a cada 30 minutos, pra não repetir).
# IMPORTANTE: só dispara quando é o PRÓPRIO Ghost quem manda a
# mensagem — ser apenas citado/@marcado por outra pessoa não conta
# mais (ver changelog v1.3)
GHOST_USER_ID = 1077952035099512923
GHOST_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos
# apelidos/nomes do Ghost — mantidos apenas como referência/utilitário,
# não são mais usados pra disparar a reação de "chegou" por citação
GHOST_APELIDOS = ["ghost"]

# ID da namorada do Ghost — mesma lógica de interação especial que o
# Draw e o Ghost têm (limitada a 1 a cada 30 minutos, pra não repetir).
# Só dispara quando é ela mesma quem fala (ver changelog v1.3)
GHOST_NAMORADA_USER_ID = 757956601020940338
GHOST_NAMORADA_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos
# apelidos/nomes usados só como referência — deixe vazio se não tiver
# um apelido fixo pra usar aqui (ex: GHOST_NAMORADA_APELIDOS = ["nomeDela"])
GHOST_NAMORADA_APELIDOS = []

# ID da Dalia — líder do clã, recebe interações especiais e
# personalizadas (limitadas a 1 a cada 30 minutos, pra não repetir).
# Só dispara quando é ela mesma quem fala (ver changelog v1.3)
DALIA_USER_ID = 1403092977802412042
DALIA_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos
# apelidos/nomes usados só como referência/utilitário
DALIA_APELIDOS = ["dalia", "dália"]

# ID da Orochi — recebe interações especiais e personalizadas
# (limitadas a 1 a cada 30 minutos, pra não repetir). Só dispara
# quando é ela mesma quem fala (ver changelog v1.3)
OROCHI_USER_ID = 1248748685060345969
OROCHI_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos
# apelidos/nomes usados só como referência/utilitário
OROCHI_APELIDOS = ["orochi"]

# ID do Felipe — mod do servidor, recebe interações especiais e
# personalizadas (limitadas a 1 a cada 30 minutos, pra não repetir).
# Só dispara quando é ele mesmo quem fala (ver changelog v1.3)
FELIPE_USER_ID = 1466109068371431616
FELIPE_COOLDOWN_SEGUNDOS = 30 * 60  # 30 minutos
# apelido usado só como referência/utilitário
FELIPE_APELIDOS = ["felipe"]

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

# respostas pra elogios (fofa, bonita, linda etc.) — ela fica tímida
_RESP_ELOGIO = [
    "*fica vermelha* pa-para de me elogiar assim... 🦇💜😳",
    "eu?? *esconde o rosto atrás da asinha* ai que vergonha... 🦇🖤",
    "*mexe na asinha sem graça* o-obrigada... não precisava... 🦇💜",
    "*ri baixinho, envergonhada* pára, você tá me deixando sem graça 🦇✨",
    "ai... *voa rapidinho pra se esconder um pouco* obrigada mesmo... 🦇🖤",
    "*sorri tímida, olhando pro chão* isso me deixou toda boba agora 🦇💜",
    "*se enrola na própria asa de vergonha* ...obrigada 🦇🖤😳",
]

# respostas pra "você gosta de brincar? / vamos brincar" (reaproveitadas)
_RESP_GOSTA_BRINCAR = [
    "AMO brincar!! principalmente pregar peça em alguém 😈🦇",
    "com certeza!! bora, o que a gente vai aprontar?? 😈🦇✨",
    "eu vivo pra isso!! sempre pronta pra uma brincadeira 🦇🖤",
    "óbvio que sim!! só me diz o que vamos fazer 😈🦇",
    "*bate as asinhas animada* SIM!! vamos, vamos!! 🦇✨",
]

# respostas pra "pousa no meu ombro" / "senta no ombro" etc.
_RESP_POUSA_OMBRO = [
    "*voa e pousa levinha no seu ombro* consegui!! sou leve que nem uma pluma 🦇🖤",
    "*desce voando e se agarra no seu ombro* aqui tô eu, bem confortável!! 🦇✨",
    "owwn, claro que pouso!! *se ajeita toda satisfeita* 🦇💜",
    "*aterrissa igual profissional* e aí, gostou da companhia?? 😈🦇",
    "*pousa e enrola a asinha no seu pescoço* agora sou sua sombra oficial 🦇🖤",
    "*pousa suavinha* prontinho!! posso ficar aqui a noite toda 🦇🌙",
    "*chega voando e se pendura no seu ombro de cabeça pra baixo* melhor vista da minha vida 😈🦇",
]

# respostas pra "vem cá" / "vem aqui" / "chega aqui"
_RESP_VEM_CA = [
    "*voa correndo* já cheguei!! 🦇💨",
    "*aparece do nada bem do seu lado* pronto, vim!! 🦇✨",
    "owwn, chamou?? *pousa animada* 🦇🖤",
    "*bate as asinhas rapidinho e chega* tô aqui!! o que foi?? 🦇💜",
    "*voa em disparada* opa, presente!! 😈🦇",
    "*desce zunindo* cheguei antes até de você terminar de chamar 🦇✨",
]

# respostas pra "para de ficar pulando/voando atrás de mim" — ela nunca
# para de verdade, só faz graça e continua do jeitinho dela
_RESP_PARA_DE_SEGUIR = [
    "nunca!! sua sombra bagunçada agora sou eu 😈🦇",
    "*continua pulando atrás, só que rindo* nunca vou parar kkkk 🦇✨",
    "impossível, isso é contrato de morceguinha vitalício 😈🦇🖤",
    "*para bem na sua frente ao invés de atrás* satisfeito?? 😹🦇",
    "*ri e continua* eu vim de brinde, não tem devolução 🦇💜",
    "*se pendura na sua cabeça em vez das costas* melhorou?? 😈🦇",
    "hmm... não 😹🦇 *continua voando atrás*",
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

    # ── Elogios (fofa, bonita, linda etc.) — ela fica tímida ─────
    "fofa": _RESP_ELOGIO,
    "fofo": _RESP_ELOGIO,
    "fofinha": _RESP_ELOGIO,
    "fofinho": _RESP_ELOGIO,
    "bonita": _RESP_ELOGIO,
    "bonito": _RESP_ELOGIO,
    "linda": _RESP_ELOGIO,
    "lindo": _RESP_ELOGIO,
    "maravilhosa": _RESP_ELOGIO,
    "maravilhoso": _RESP_ELOGIO,
    "perfeita": _RESP_ELOGIO,
    "perfeito": _RESP_ELOGIO,
    "incrível": _RESP_ELOGIO,
    "adorável": _RESP_ELOGIO,
    "gracinha": _RESP_ELOGIO,

    # ── Gosta de brincar / vamos brincar ─────────────────────────
    "gosta de brincar": _RESP_GOSTA_BRINCAR,
    "gosta de brincadeira": _RESP_GOSTA_BRINCAR,
    "vamos brincar": _RESP_GOSTA_BRINCAR,
    "vamo brincar": _RESP_GOSTA_BRINCAR,
    "quer brincar": _RESP_GOSTA_BRINCAR,
    "bora brincar": _RESP_GOSTA_BRINCAR,
    "topa brincar": _RESP_GOSTA_BRINCAR,

    # ── Pousa no meu ombro / senta no ombro ──────────────────────
    "pousa no meu ombro": _RESP_POUSA_OMBRO,
    "pouse no meu ombro": _RESP_POUSA_OMBRO,
    "pousa no ombro": _RESP_POUSA_OMBRO,
    "pouse no ombro": _RESP_POUSA_OMBRO,
    "senta no ombro": _RESP_POUSA_OMBRO,
    "senta no meu ombro": _RESP_POUSA_OMBRO,
    "vem pro ombro": _RESP_POUSA_OMBRO,
    "vem para o ombro": _RESP_POUSA_OMBRO,

    # ── Vem cá / vem aqui / chega aqui ───────────────────────────
    "vem ca": _RESP_VEM_CA,
    "vem cá": _RESP_VEM_CA,
    "vem aqui": _RESP_VEM_CA,
    "vem pra ca": _RESP_VEM_CA,
    "vem pra cá": _RESP_VEM_CA,
    "vem para ca": _RESP_VEM_CA,
    "vem para cá": _RESP_VEM_CA,
    "venha aqui": _RESP_VEM_CA,
    "venha ca": _RESP_VEM_CA,
    "venha cá": _RESP_VEM_CA,
    "chega aqui": _RESP_VEM_CA,

    # ── Para de pular/voar atrás de mim / para de me seguir ──────
    "para de pular atras de mim": _RESP_PARA_DE_SEGUIR,
    "para de pular atrás de mim": _RESP_PARA_DE_SEGUIR,
    "pare de pular atras de mim": _RESP_PARA_DE_SEGUIR,
    "pare de pular atrás de mim": _RESP_PARA_DE_SEGUIR,
    "para de ficar pulando atras de mim": _RESP_PARA_DE_SEGUIR,
    "para de ficar pulando atrás de mim": _RESP_PARA_DE_SEGUIR,
    "pare de ficar pulando atras de mim": _RESP_PARA_DE_SEGUIR,
    "pare de ficar pulando atrás de mim": _RESP_PARA_DE_SEGUIR,
    "para de voar atras de mim": _RESP_PARA_DE_SEGUIR,
    "para de voar atrás de mim": _RESP_PARA_DE_SEGUIR,
    "pare de voar atras de mim": _RESP_PARA_DE_SEGUIR,
    "pare de voar atrás de mim": _RESP_PARA_DE_SEGUIR,
    "para de ficar atras de mim": _RESP_PARA_DE_SEGUIR,
    "para de ficar atrás de mim": _RESP_PARA_DE_SEGUIR,
    "pare de ficar atras de mim": _RESP_PARA_DE_SEGUIR,
    "pare de ficar atrás de mim": _RESP_PARA_DE_SEGUIR,
    "para de me seguir": _RESP_PARA_DE_SEGUIR,
    "pare de me seguir": _RESP_PARA_DE_SEGUIR,

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

# CORREÇÃO: chaves de elogio ("fofa", "linda", "lindo" etc.) só podem
# disparar quando a Vampy for citada de verdade na mensagem (nome dela
# no texto ou @menção real) — nunca pela chance aleatória de 25% que
# os outros gatilhos genéricos usam. Sem isso, uma frase qualquer tipo
# "que dia lindo né gente" (falando do dia, não dela) podia sortear a
# resposta tímida de elogio como se alguém tivesse elogiado ela, o que
# não faz sentido nenhum
_CHAVES_EXIGEM_CITACAO = {
    "fofa", "fofo", "fofinha", "fofinho", "bonita", "bonito", "linda",
    "lindo", "maravilhosa", "maravilhoso", "perfeita", "perfeito",
    "incrível", "adorável", "gracinha",
}


def _checar_gatilho_generico(texto: str, db: dict) -> str | None:
    texto_lower = texto.lower().strip()
    if texto_lower in db["respostas"]:
        return texto_lower
    # usa \b (fronteira de palavra) pra evitar que gatilhos curtos como
    # "oi" ou "hey" disparem dentro de palavras aleatórias (ex: "dois", "coisa")
    #
    # quando mais de uma chave bate na mesma mensagem (ex: "pousa no meu
    # ombro vampy" contém tanto "vampy" quanto "pousa no meu ombro"),
    # damos preferência pro gatilho mais específico (o mais longo), pra
    # frases inteiras não serem atropeladas por um gatilho curto e genérico
    encontrados = []
    for chave in db["respostas"]:
        padrao = r"\b" + re.escape(chave) + r"\b"
        if re.search(padrao, texto_lower):
            encontrados.append(chave)
    if not encontrados:
        return None
    return max(encontrados, key=len)


# ══════════════════════════════════════════════════════════════════
#  🎯  DETECÇÃO DE @MENÇÕES DIGITADAS DE VERDADE
# ══════════════════════════════════════════════════════════════════
# CORREÇÃO IMPORTANTE: quando alguém RESPONDE (reply) a uma mensagem
# de outra pessoa com a notificação de menção ligada (que é o padrão
# do Discord), aquela pessoa é automaticamente incluída na lista
# `message.mentions` — mesmo que o texto da resposta não fale nada
# sobre ela. Se a gente usasse `message.mentions` pra decidir "quem
# foi citado", a Vampy ia confundir um simples reply (sobre qualquer
# assunto) com uma citação de propósito. Foi exatamente isso que
# causou ela reagir com "opa, o Ghost apareceu!!" quando alguém só
# respondeu uma mensagem do Ghost falando de outra coisa, e reagir
# como se tivessem citado o Draw quando na verdade não citaram.
#
# A solução é olhar direto pro TEXTO CRU da mensagem: uma @menção só
# conta se ela foi realmente digitada (aparece como <@ID> no texto).
#
# IMPORTANTE (v1.3): mesmo uma @menção digitada de propósito não é
# garantia de que a pessoa "chegou" ou "está ali" — alguém pode digitar
# @Draw só pra falar SOBRE ele ou mandar uma AÇÃO nele (ex: "Vampy joga
# uma bomba atômica no @Draw"), sem o Draw ter dito nada. Por isso as
# reações de "opa, chegou fulano!!" (Draw, Ghost, namorada do Ghost,
# Dalia, Orochi, Felipe) agora só disparam quando é a própria pessoa
# (dono do ID) quem envia a mensagem — ver on_message mais abaixo.
# `_ids_mencionados_diretamente` continua existindo e sendo usado pra
# outras coisas (extrair o alvo de uma peça/ataque, por exemplo), só
# não é mais usado pra decidir "essa pessoa chegou".

def _ids_mencionados_diretamente(message: discord.Message) -> set[int]:
    """Retorna os IDs de usuários que foram @mencionados DE VERDADE no
    texto da mensagem (digitados de propósito), ignorando qualquer
    menção que só apareça por causa de um reply com notificação
    ligada."""
    return {int(uid) for uid in re.findall(r"<@!?(\d+)>", message.content)}


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
    própria Vampy e quem pediu (não faz sentido ela se auto-marcar).

    Só considera @menções DIGITADAS de verdade no texto (ver
    `_ids_mencionados_diretamente`) — uma menção que apareceu só por
    causa de um reply não conta como "marcou essa pessoa de propósito".
    """
    ids_diretos = _ids_mencionados_diretamente(message)
    outros = [
        u for u in message.mentions
        if u.id in ids_diretos and u.id != bot_user.id and u.id != message.author.id
    ]
    return outros[0].mention if outros else None


def _mensagem_cita_pessoa(message: discord.Message, user_id: int, apelidos: list[str]) -> bool:
    """Verifica se a mensagem cita uma pessoa específica — seja por
    @menção DIGITADA de verdade (marcou o nome dela no Discord,
    escrevendo a menção) ou só falando o apelido/nome dela em texto
    puro (ex: 'manda um oi pro Draw', sem marcar).

    NOTA (v1.3): essa função NÃO é usada pra decidir a reação de
    "fulano chegou" (ver on_message) — mesmo uma @menção digitada de
    propósito não significa que a pessoa está de fato ali/falando, ela
    pode só estar sendo citada como alvo de uma ação de outra pessoa
    (ex: "joga uma bomba atômica no @Fulano"). A reação de "chegou"
    agora depende só de `message.author.id == user_id`. Mantida aqui
    só como utilitária, caso outra parte do código queira reaproveitar
    essa checagem por nome no futuro.
    """
    if user_id in _ids_mencionados_diretamente(message):
        return True
    texto_lower = message.content.lower()
    return any(
        re.search(r"\b" + re.escape(apelido) + r"\b", texto_lower)
        for apelido in apelidos
    )


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
    "*sorri toda boba* o Draw é praticamente da família aqui, sabia?? 🦇💜",
    "Draw!! um dos poucos que eu realmente gosto de ver por aqui 😈🦇🖤",
    "*se pendura pertinho dele* o Draw sempre traz um clima bom quando aparece 🦇✨",
    "esse aí é gente boa demais, olha só, o Draw!! 🦇🖤",
]


# ══════════════════════════════════════════════════════════════════
#  🦇  ZOEIRA COM O ALVO (XISPA_USER_ID) — sempre que ele fala
# ══════════════════════════════════════════════════════════════════
# esse aqui é o "saco de pancada" oficial da Vampy: toda vez que ele
# manda mensagem, ela dispara uma zoeira diferente, sem cooldown —
# fofa e engraçada do jeitinho atentado dela

_INTERACOES_XISPA = [
    "XISPAAAAAAA, ninguém te chamou aqui 😹🦇",
    "*aparece só pra zoar* xispa daqui, moço, ninguém te chamou não 😈🦇",
    "eita, apareceu de novo... xispa, xispa!! 🦇💨",
    "*bate as asinhas rindo* vai xispando, ninguém pediu pra você falar 😹🖤",
    "pssiu, some!! aqui ninguém te chamou, viu?? 😈🦇",
    "*rindo escondida atrás da asa* vai tomar um tiro do Ghost 😈🔫🦇",
    "*voa de cabeça pra baixo rindo* xispaaaa daqui, sumido!! 🦇✨",
    "hmpf, olha quem apareceu sem ninguém chamar... xispa!! 😹🦇",
    "*espia de longe e já sai rindo* xispa logo, presente de grego 🦇💜",
    "*aponta de longe* esse aí não foi chamado não, gente... xispa!! 😈🦇",
]

# reação especial sempre que XISPA_USER_ID for CITADO/MARCADO por
# qualquer pessoa na mensagem (não precisa ser ele quem fala) — a
# Vampy aparece do nada só pra dar um chutinho nele, sem cooldown,
# tem prioridade máxima logo depois da apresentação
_INTERACOES_XISPA_CHUTE = [
    "*aparece do nada e dá um chute nele* toma, bem feito 😹🦇👢",
    "*voa rapidinho, chuta ele e some de novo* leva isso!! 😈🦇",
    "psiu, deixa que eu resolvo... *chuta* 🦇👢😹",
    "*pousa do lado dele só pra dar um chutinho e sair voando* 😈🦇",
    "ninguém pediu, mas toma um chute a mais da minha parte 😹🦇👢",
    "*prepara a asinha e dá um voadora nele* aiii que dó (mentira) 😈🦇",
    "*chega chutando* sempre bom fazer companhia nessas horas 🦇👢🖤",
    "*dá uma rasteira nele antes do chute, só de bônus* 😹🦇👢",
]


# ══════════════════════════════════════════════════════════════════
#  🦇  INTERAÇÕES ESPECIAIS COM O GHOST (a cada 30 minutos)
# ══════════════════════════════════════════════════════════════════
# mesma lógica do Draw: sempre que o Ghost (GHOST_USER_ID) fala, a
# Vampy manda uma mensagem personalizada pra ele — no máximo 1x a
# cada 30 minutos, pra não ficar repetindo em toda mensagem dele

_INTERACOES_GHOST = [
    "opa, chegou o Ghost!! 🦇🖤",
    "*pousa do lado do Ghost* e aí, Ghost, tudo certo?? 🦇✨",
    "hmm, o Ghost apareceu... alguém segura minhas asinhas 😈🦇",
    "Ghost!! tava pensando em você inclusive, que sincronia 🦇💜",
    "*acena animada* olha só quem chegou, o Ghost!! 😈🦇🖤",
    "*voa em círculos* Ghost na área, cuidado gente!! 🦇✨",
    "eu escuto esse nome e já sei, só pode ser o Ghost chegando 🦇🌙",
    "*se esconde atrás dele rindo* o Ghost é parceiro de arte oficial 😈🦇🖤",
    "esse aí é gente boa, olha só, o Ghost!! 🦇✨",
]

# palavras-chave que disparam a reação especial quando o Ghost faz a
# brincadeira clássica dele de "dar um tiro" em alguém (ex: "de um tiro
# no Draw") — reage na hora, sem cooldown, é a piada de sempre dele
_GATILHOS_TIRO_GHOST = ["tiro", "tiros", "atira", "atirar", "atirou", "bala", "balaço"]

_INTERACOES_GHOST_TIRO = [
    "*se esconde atrás da asinha* Ghost, calma, larga essa arma imaginária 😹🦇",
    "AAAAH lá vem o Ghost ameaçando todo mundo de novo kkkk 🔫🦇",
    "*voa se escondendo atrás de alguém* ninguém tá seguro quando o Ghost aparece assim 😈🦇",
    "*pisca pra vítima* boa sorte correndo do Ghost, viu 😹🦇",
    "Ghost sendo Ghost de novo... 🔫😈🦇",
    "*ri nervosa e se esconde* mais uma ameaça de brincadeira do Ghost 😹🦇",
    "*bate as asinhas alarmada* CUIDADO, o Ghost tá de mira em alguém!! 😈🦇",
]

def _contem_gatilho_tiro(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(
        re.search(r"\b" + re.escape(palavra) + r"\b", texto_lower)
        for palavra in _GATILHOS_TIRO_GHOST
    )


# ══════════════════════════════════════════════════════════════════
#  🦇  INTERAÇÕES ESPECIAIS COM A NAMORADA DO GHOST (a cada 30 min)
# ══════════════════════════════════════════════════════════════════
# mesma lógica do Draw e do Ghost: sempre que ela (GHOST_NAMORADA_USER_ID)
# fala, a Vampy manda uma mensagem personalizada — com uma zoeirinha
# extra por ela namorar o Ghost — no máximo 1x a cada 30 minutos

_INTERACOES_GHOST_NAMORADA = [
    "opa, chegou a namorada do Ghost!! 🦇💕",
    "*sorri sapeca* eii, você é quem rouba a atenção do Ghost por aqui, né?? 😈🦇💜",
    "*cochicha rindo* psiu, o Ghost fica todo bobo quando você aparece, sabia?? 🦇💕",
    "*voa em círculos animada* olha só quem chegou, a namorada do Ghost!! 🦇✨",
    "casal favorito do servidor apareceu (bem, metade dele) 🦇💜",
    "*pousa do seu lado* e aí, tudo certo?? o Ghost já sabe que você tá aqui?? 😈🦇",
    "*acena toda animada* oi oi!! como é namorar o Ghost, me conta os podres 😹🦇",
]

# ══════════════════════════════════════════════════════════════════
#  🦇  INTERAÇÕES ESPECIAIS COM A DALIA (líder do clã, a cada 30 min)
# ══════════════════════════════════════════════════════════════════
# mesma lógica do Draw, Ghost e namorada do Ghost: sempre que a Dalia
# (DALIA_USER_ID) fala, a Vampy manda uma mensagem personalizada — um
# pouco mais respeitosa, já que ela é a líder do clã — no máximo 1x a
# cada 30 minutos

_INTERACOES_DALIA = [
    "opa, a Dalia apareceu!! *se ajeita toda comportada* 🦇🖤",
    "*faz uma reverência voando* a líder do clã chegou!! 🦇✨",
    "Dalia!! sempre um prazer receber a chefona por aqui 😈🦇",
    "*pousa educadinha* e aí, Dalia, tudo em ordem no clã?? 🦇💜",
    "*bate as asinhas com respeito* olha só quem chegou, a Dalia!! 🦇🌙",
    "hmm, quando a Dalia aparece todo mundo se ajeita, né?? 😹🦇",
    "*se pendura discretamente por perto, se comportando* a líder merece atenção especial 🦇✨",
    "Dalia na área!! bora fazer valer o nome do clã 😈🦇🖤",
    "*pousa e faz continência com a asinha* Dalia, minha líder favorita!! 🦇💜",
]


# ══════════════════════════════════════════════════════════════════
#  🦇  INTERAÇÕES ESPECIAIS COM A OROCHI (a cada 30 minutos)
# ══════════════════════════════════════════════════════════════════
# mesma lógica do Draw, Ghost e Dalia: sempre que a Orochi
# (OROCHI_USER_ID) fala, a Vampy manda uma mensagem personalizada —
# no máximo 1x a cada 30 minutos

_INTERACOES_OROCHI = [
    "opa, a Orochi apareceu!! 🦇🐍",
    "*pousa de olho aceso* e aí, Orochi, tudo certo?? 🦇✨",
    "hmm, a Orochi chegou... esse nome já dá um arrepio na asinha 😈🦇",
    "*voa em círculos, meio desconfiada, meio curiosa* olha só quem apareceu, a Orochi!! 🦇🌙",
    "Orochi na área!! aposto que ela já tá aprontando alguma 😈🦇🖤",
    "*se esconde um pouquinho atrás da asa, brincando* cuidado que a Orochi chegou 🦇✨",
    "essa aí sempre traz um clima diferente quando aparece, olha só, a Orochi!! 🦇🖤",
]


# ══════════════════════════════════════════════════════════════════
#  🦇  INTERAÇÕES ESPECIAIS COM O FELIPE (a cada 30 minutos)
# ══════════════════════════════════════════════════════════════════
# mesma lógica da Dalia: o Felipe (FELIPE_USER_ID) é mod do servidor,
# então a Vampy trata ele com um pouco mais de respeito/comportada,
# mas sem perder a marra — dispara quando ele fala, no máximo 1x a
# cada 30 minutos

_INTERACOES_FELIPE = [
    "opa, o Felipe apareceu!! *se ajeita, afinal é mod* 🦇🖤",
    "*bate continência com a asinha* e aí, Felipe, tudo em ordem por aqui?? 🦇✨",
    "Felipe!! um dos mods mais gente boa que eu conheço 😈🦇",
    "*pousa educadinha, se comportando* cuidado que eu ando aprontando por aqui, viu 😹🦇",
    "hmm, quando o Felipe aparece todo mundo se ajeita, né?? 😹🦇",
    "*acena animada* olha só quem chegou, o Felipe!! 🦇🌙",
    "Felipe na área!! modera direitinho que eu fico de olho 😈🦇🖤",
    "*voa em círculos* sempre bom ver o Felipe rondando o servidor 🦇✨",
]


# ══════════════════════════════════════════════════════════════════
#  🦇  RESPOSTAS PRA ATAQUES EM GERAL (fogo, facada, tiro)
# ══════════════════════════════════════════════════════════════════
# diferente da piada específica do Ghost lá em cima, isso aqui vale
# pra QUALQUER pessoa que mandar esse tipo de mensagem — ex: "Vampy
# ateia fogo no Fulano", "dá uma facada nele", "manda bala no Fulano"
# etc. Se a mensagem citar/marcar alguém (@menção), a Vampy usa o
# nome dessa pessoa na resposta; senão, usa uma resposta genérica

_GATILHOS_ATAQUE = {
    "fogo": [
        "atear fogo", "ateia fogo", "ateie fogo", "atear fogo em", "coloca fogo",
        "colocou fogo", "põe fogo", "poe fogo", "botar fogo", "botou fogo",
        "pega fogo", "toca fogo", "queima ele", "queima ela", "incendeia",
        "incendiar",
    ],
    "faca": [
        "facada", "facadas", "esfaqueia", "esfaqueou", "esfaquear",
        "apunhala", "apunhalou", "apunhalar", "enfia a faca", "mete a faca",
    ],
    "tiro": _GATILHOS_TIRO_GHOST + [
        "dá um tiro", "de um tiro", "dê um tiro", "manda bala", "atira nele",
        "atira nela", "atirar nele", "atirar nela",
    ],
}

_RESPOSTAS_ATAQUE_COM_ALVO = {
    "fogo": [
        "*acende um fósforo do nada e ateia fogo em {alvo}* PEGOU FOGO!! 😈🔥🦇",
        "*voa em volta de {alvo} soltando fagulhas* arde, arde!! 🔥🦇😹",
        "com prazer!! *ateia fogo em {alvo}* pronto, tá quentinho agora 😈🔥🦇",
        "*risada maligna* {alvo} vai virar churrasquinho hoje 🔥🦇😈",
        "*bafo de fogo* nem sabia que sabia fazer isso, mas {alvo} que se cuide 🔥🦇",
    ],
    "faca": [
        "*saca uma faquinha do nada e vai pra cima de {alvo}* toma!! 🔪🦇😈",
        "com todo prazer!! *dá uma facadinha de leve em {alvo}* 🔪🦇",
        "*afia as garrinhas ao invés de faca* {alvo} nem vai sentir (mentira) 😈🦇🔪",
        "prontinho!! *espeta {alvo} de leve e sai voando rindo* 🔪🦇😹",
    ],
    "tiro": [
        "*saca uma arminha de brinquedo e mira em {alvo}* BANG!! 🔫🦇😈",
        "com certeza!! *atira em {alvo} e sai voando rindo* 😹🔫🦇",
        "*mira certeira* toma, {alvo}!! 🔫🦇✨",
        "pow pow!! *atira em {alvo} e esconde a arminha de volta* 😈🔫🦇",
    ],
}

_RESPOSTAS_ATAQUE_SEM_ALVO = {
    "fogo": [
        "*ateia fogo em alguém aleatório* alguém pediu incêndio?? 🔥🦇😈",
        "*bafo de fogo pra todo lado* cuidado, hoje eu tô com fósforo na asa 🔥🦇",
    ],
    "faca": [
        "*saca uma faquinha e fica de olho em quem vai ser a vítima* 🔪🦇😈",
        "hmm, alguém vai levar uma facadinha hoje... quem será?? 🔪🦇",
    ],
    "tiro": [
        "*saca uma arminha de brinquedo e fica de olho em todo mundo* 🔫🦇😈",
        "pow pow!! *atira pro alto só de brincadeira* 🔫🦇✨",
    ],
}


def _checar_gatilho_ataque(texto: str) -> str | None:
    texto_lower = texto.lower()
    for tipo, palavras in _GATILHOS_ATAQUE.items():
        for palavra in palavras:
            padrao = r"\b" + re.escape(palavra) + r"\b"
            if re.search(padrao, texto_lower):
                return tipo
    return None


# ══════════════════════════════════════════════════════════════════
#  🦇  CONVITE PRA PREGAR UMA PEÇA (ex: "vamos pregar uma peça",
#      "Vampy, vamos aprontar uma peça no @Fulano")
# ══════════════════════════════════════════════════════════════════
# reage na hora, sem cooldown, quando alguém propõe pregar uma peça —
# com ou sem alvo definido. Usa padrões de regex específicos (verbo +
# "peça") em vez de uma palavra solta como "peça" ou "aprontar",
# justamente pra não repetir o mesmo tipo de falso-positivo que
# aconteceu com a citação por nome (ver _mensagem_cita_pessoa) — uma
# frase qualquer com "aprontar" sozinho não deve disparar isso

_PADROES_PECA = [
    r"pregar\s+(?:uma\s+)?pe[çc]a",
    r"prega\s+(?:uma\s+)?pe[çc]a",
    r"pregue\s+(?:uma\s+)?pe[çc]a",
    r"aprontar\s+(?:uma\s+)?pe[çc]a",
    r"apronta\s+(?:uma\s+)?pe[çc]a",
    r"fazer\s+(?:uma\s+)?pe[çc]a\s+(?:em|no|na|com)",
    r"faz(?:er)?\s+uma\s+pe[çc]a\s+(?:em|no|na|com)",
]


def _checar_gatilho_peca(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(re.search(padrao, texto_lower) for padrao in _PADROES_PECA)


_RESPOSTAS_PECA_COM_ALVO = [
    "AEHÊ, adorei a ideia!! *já fica de olho em {alvo}* bora pregar uma peça nele(a) 😈🦇",
    "*esfrega as asinhas* {alvo} nem vai saber o que atingiu... bora!! 😈🦇✨",
    "com certeza!! já tô pensando numa peça boa pro/pra {alvo} 😈🦇🖤",
    "*sorriso maligno* {alvo} escolhido(a)!! deixa comigo que eu ajudo a bolar 😈🦇",
    "eu?? topo demais!! {alvo} vai ficar bem confuso(a) com isso 😹🦇",
    "*já sacando as ideias da cabeça* {alvo}... isso vai ser bom 😈🦇✨",
    "perfeito!! {alvo} não vai ver a peça chegando 😈🦇🖤",
]

_RESPOSTAS_PECA_SEM_ALVO = [
    "AEHÊ, eu topo!! só falta escolher a vítima 😈🦇",
    "*esfrega as asinhas animada* bora, quem vai ser o alvo dessa vez?? 😈🦇",
    "eu vivo pra isso!! só me diz em quem vamos pregar 😈🦇✨",
    "*olha em volta procurando um alvo* hmm... quem merece hoje?? 😈🦇",
    "com certeza!! escolhe a vítima que eu ajudo a bolar a peça 😈🦇🖤",
    "*bate as asinhas animada* SIM!! só preciso saber em quem 😈🦇",
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

        # Cooldown separado só pra interação especial com o Ghost — mesma
        # lógica do Draw, também começa a contar a partir do boot do bot
        self._ultimo_ghost: datetime = datetime.now(timezone.utc)

        # Cooldown separado só pra interação especial com a namorada do
        # Ghost — mesma lógica do Draw e do Ghost
        self._ultimo_ghost_namorada: datetime = datetime.now(timezone.utc)

        # Cooldown separado só pra interação especial com a Dalia —
        # mesma lógica do Draw, Ghost e namorada do Ghost
        self._ultimo_dalia: datetime = datetime.now(timezone.utc)

        # Cooldown separado só pra interação especial com a Orochi —
        # mesma lógica do Draw, Ghost e Dalia
        self._ultimo_orochi: datetime = datetime.now(timezone.utc)

        # Cooldown separado só pra interação especial com o Felipe —
        # mesma lógica do Draw, Ghost, Dalia e Orochi
        self._ultimo_felipe: datetime = datetime.now(timezone.utc)

        # Cooldown separado pras aparições espontâneas ("do nada")
        self._ultimo_espontaneo: datetime | None = None

        # CORREÇÃO: guarda os IDs das últimas mensagens já processadas,
        # pra nunca responder duas vezes à mesma mensagem — protege
        # contra o Discord entregar o mesmo evento mais de uma vez
        # (reconexões do gateway, por exemplo), que foi o que causou a
        # Vampy mandar duas respostas diferentes pra mesma mensagem
        self._mensagens_processadas: deque[int] = deque(maxlen=500)

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
        # ignora mensagens de outros bots — EXCETO a do XISPA_USER_ID,
        # que na verdade é o bot "Golden Fenix" (não uma pessoa). Sem
        # essa exceção, a zoeira automática com ele nunca dispararia,
        # porque a função já dava return antes de chegar lá
        if (message.author.bot and message.author.id != XISPA_USER_ID) or not message.guild:
            return

        # CORREÇÃO: se essa mensagem já foi processada antes (o Discord
        # às vezes entrega o mesmo evento mais de uma vez, principalmente
        # depois de reconexões), ignora — evita responder duas vezes à
        # mesma mensagem
        if message.id in self._mensagens_processadas:
            return
        self._mensagens_processadas.append(message.id)

        ctx = await self.bot.get_context(message)
        if ctx.valid:
            return

        self._contexto[message.channel.id].append({
            "user": message.author.display_name,
            "user_id": message.author.id,
            "content": message.content,
            "time": datetime.now(timezone.utc).isoformat(),
        })

        # CORREÇÃO: usa só @menções DIGITADAS de verdade (ver
        # `_ids_mencionados_diretamente`) em vez de `message.mentions`,
        # que também inclui quem foi respondido (reply) sem ter sido
        # citado de propósito no texto
        ids_mencionados = _ids_mencionados_diretamente(message)
        vampy_chamada = (
            self.bot.user.id in ids_mencionados
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

        # ── Chute automático sempre que XISPA_USER_ID for citado ────
        # toda vez que QUALQUER pessoa marcar/citar esse ID na mensagem
        # (não precisa ser ele quem fala), a Vampy aparece dando um
        # chutinho nele — sem cooldown, prioridade máxima depois só da
        # apresentação, pra garantir que ela sempre reage quando ele é
        # mencionado. Usa só @menção digitada de verdade (não conta
        # menção que apareceu só por causa de um reply)
        if XISPA_USER_ID in ids_mencionados:
            self._ultimo_resp[message.channel.id] = datetime.now(timezone.utc)
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.4, 1.0))
            await message.reply(random.choice(_INTERACOES_XISPA_CHUTE), mention_author=False)
            return

        # ── Interação especial e personalizada com o Draw ───────────
        # CORREÇÃO (v1.3): antes essa reação também disparava quando o
        # Draw era apenas @mencionado por OUTRA pessoa (ex: "Vampy joga
        # uma bomba atômica no @Draw"), fazendo a Vampy dizer "olha só
        # quem chegou, o Draw!!" como se ele tivesse aparecido/falado —
        # mesmo sendo apenas o ALVO da mensagem de outra pessoa. Agora
        # só dispara quando é o PRÓPRIO Draw quem manda a mensagem, no
        # máximo 1x a cada 30 minutos — depois que o cooldown libera,
        # ainda tem uma chance aleatória de disparar (não é automático
        # na primeira mensagem)
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

        # ── Interação especial com o Ghost ──────────────────────────
        # CORREÇÃO (v1.3): mesma correção do Draw — a reação de "chegou
        # o Ghost" agora só dispara quando é o PRÓPRIO Ghost quem fala,
        # não mais só por ser @mencionado por outra pessoa. A piada do
        # "tiro" continua reagindo na hora, sem cooldown, mas também só
        # quando é o Ghost quem manda a mensagem
        if message.author.id == GHOST_USER_ID:
            # a brincadeira do "tiro" tem prioridade e reage na hora,
            # sem cooldown — é a piada clássica dele
            if _contem_gatilho_tiro(message.content):
                self._ultimo_resp[message.channel.id] = datetime.now(timezone.utc)
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.4, 1.0))
                await message.reply(random.choice(_INTERACOES_GHOST_TIRO), mention_author=False)
                return

            agora_ghost = datetime.now(timezone.utc)
            cooldown_passou = (agora_ghost - self._ultimo_ghost).total_seconds() >= GHOST_COOLDOWN_SEGUNDOS
            if cooldown_passou and random.random() < 0.4:
                self._ultimo_ghost = agora_ghost
                self._ultimo_resp[message.channel.id] = agora_ghost
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.4))
                await message.reply(random.choice(_INTERACOES_GHOST), mention_author=False)
                return

        # ── Interação especial com a namorada do Ghost ──────────────
        # CORREÇÃO (v1.3): mesma correção do Draw e do Ghost — só
        # dispara quando é ela mesma quem fala, no máximo 1x a cada 30
        # minutos, com uma chance aleatória depois que o cooldown libera
        if message.author.id == GHOST_NAMORADA_USER_ID:
            agora_ghost_namorada = datetime.now(timezone.utc)
            cooldown_passou = (agora_ghost_namorada - self._ultimo_ghost_namorada).total_seconds() >= GHOST_NAMORADA_COOLDOWN_SEGUNDOS
            if cooldown_passou and random.random() < 0.4:
                self._ultimo_ghost_namorada = agora_ghost_namorada
                self._ultimo_resp[message.channel.id] = agora_ghost_namorada
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.4))
                await message.reply(random.choice(_INTERACOES_GHOST_NAMORADA), mention_author=False)
                return

        # ── Interação especial com a Dalia ───────────────────────────
        # CORREÇÃO (v1.3): mesma correção do Draw, Ghost e namorada do
        # Ghost — só dispara quando é ela mesma quem fala, no máximo 1x
        # a cada 30 minutos, com uma chance aleatória depois que o
        # cooldown libera
        if message.author.id == DALIA_USER_ID:
            agora_dalia = datetime.now(timezone.utc)
            cooldown_passou = (agora_dalia - self._ultimo_dalia).total_seconds() >= DALIA_COOLDOWN_SEGUNDOS
            if cooldown_passou and random.random() < 0.4:
                self._ultimo_dalia = agora_dalia
                self._ultimo_resp[message.channel.id] = agora_dalia
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.4))
                await message.reply(random.choice(_INTERACOES_DALIA), mention_author=False)
                return

        # ── Interação especial com a Orochi ─────────────────────────
        # CORREÇÃO (v1.3): mesma correção do Draw, Ghost e Dalia — só
        # dispara quando é ela mesma quem fala, no máximo 1x a cada 30
        # minutos, com uma chance aleatória depois que o cooldown libera
        if message.author.id == OROCHI_USER_ID:
            agora_orochi = datetime.now(timezone.utc)
            cooldown_passou = (agora_orochi - self._ultimo_orochi).total_seconds() >= OROCHI_COOLDOWN_SEGUNDOS
            if cooldown_passou and random.random() < 0.4:
                self._ultimo_orochi = agora_orochi
                self._ultimo_resp[message.channel.id] = agora_orochi
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.4))
                await message.reply(random.choice(_INTERACOES_OROCHI), mention_author=False)
                return

        # ── Interação especial com o Felipe ─────────────────────────
        # CORREÇÃO (v1.3): mesma correção do Draw, Ghost, Dalia e
        # Orochi — só dispara quando é ele mesmo quem fala, no máximo
        # 1x a cada 30 minutos, com uma chance aleatória depois que o
        # cooldown libera
        if message.author.id == FELIPE_USER_ID:
            agora_felipe = datetime.now(timezone.utc)
            cooldown_passou = (agora_felipe - self._ultimo_felipe).total_seconds() >= FELIPE_COOLDOWN_SEGUNDOS
            if cooldown_passou and random.random() < 0.4:
                self._ultimo_felipe = agora_felipe
                self._ultimo_resp[message.channel.id] = agora_felipe
                async with message.channel.typing():
                    await asyncio.sleep(random.uniform(0.6, 1.4))
                await message.reply(random.choice(_INTERACOES_FELIPE), mention_author=False)
                return

        # ── Respostas pra ataques em geral (fogo, facada, tiro) ─────
        # vale pra qualquer pessoa (ex: "Vampy ateia fogo no Fulano",
        # "de uma facada no Fulano") — se citar alguém, usa o nome dele
        tipo_ataque = _checar_gatilho_ataque(message.content)
        if tipo_ataque:
            self._ultimo_resp[message.channel.id] = datetime.now(timezone.utc)
            alvo = _extrair_alvo_mencao(message, self.bot.user)
            if alvo:
                resposta_ataque = random.choice(_RESPOSTAS_ATAQUE_COM_ALVO[tipo_ataque]).format(alvo=alvo)
            else:
                resposta_ataque = random.choice(_RESPOSTAS_ATAQUE_SEM_ALVO[tipo_ataque])
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.5, 1.2))
            await message.reply(resposta_ataque, mention_author=False)
            return

        # ── Convite pra pregar uma peça (ex: "vamos pregar uma peça",
        #    "Vampy, vamos pregar uma peça no @Fulano") ──────────────
        # reage na hora, sem cooldown — se alguém marcar um alvo com @
        # de verdade, ela usa o nome dele na resposta; senão, topa a
        # ideia e pergunta quem vai ser a vítima
        if _checar_gatilho_peca(message.content):
            self._ultimo_resp[message.channel.id] = datetime.now(timezone.utc)
            alvo = _extrair_alvo_mencao(message, self.bot.user)
            if alvo:
                resposta_peca = random.choice(_RESPOSTAS_PECA_COM_ALVO).format(alvo=alvo)
            else:
                resposta_peca = random.choice(_RESPOSTAS_PECA_SEM_ALVO)
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.5, 1.2))
            await message.reply(resposta_peca, mention_author=False)
            return

        # ── Zoeira automática com o alvo de sempre ──────────────────
        # sempre que XISPA_USER_ID manda mensagem, a Vampy zoa na hora,
        # sem cooldown e sem depender de gatilho — é a graça dele com ela
        if message.author.id == XISPA_USER_ID:
            self._ultimo_resp[message.channel.id] = datetime.now(timezone.utc)
            async with message.channel.typing():
                await asyncio.sleep(random.uniform(0.4, 1.0))
            await message.reply(random.choice(_INTERACOES_XISPA), mention_author=False)
            return

        now = datetime.now(timezone.utc)
        ultimo = self._ultimo_resp.get(message.channel.id)
        if ultimo and (now - ultimo).total_seconds() < self._cooldown_resp:
            return

        # ── Resposta por gatilho ──────────────────────────
        chave = self._checar_gatilho(message.content)
        # CORREÇÃO: elogios ("fofa", "linda" etc.) só disparam se a
        # Vampy foi citada de verdade (vampy_chamada) — nunca pela
        # chance aleatória de 25%, que é só pros gatilhos genéricos
        pode_por_chance = chave not in _CHAVES_EXIGEM_CITACAO and random.random() < 0.25
        if chave and (vampy_chamada or pode_por_chance):
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
