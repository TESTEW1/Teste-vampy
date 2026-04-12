import random
import discord
from discord.ext import commands

class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! `{round(self.bot.latency * 1000)}ms`")

    @commands.command(name="caraoucoroa")
    async def cara_ou_coroa(self, ctx: commands.Context):
        resultado = random.choice(["Cara", "Coroa"])
        await ctx.send(f"🪙 Resultado: **{resultado}**")

    @commands.command(name="dado")
    async def dado(self, ctx: commands.Context, lados: int = 6):
        if lados < 2:
            await ctx.send("O dado precisa ter pelo menos 2 lados.")
            return
        await ctx.send(f"🎲 Saiu: **{random.randint(1, lados)}**")

async def setup(bot: commands.Bot):
    await bot.add_cog(MiscCog(bot))