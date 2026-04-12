import discord
from discord.ext import commands

from views.ticket_views import TicketView

class TicketsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tickets: dict[int, dict] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("[tickets] carregado")

    @commands.command(name="painelticket")
    @commands.has_permissions(administrator=True)
    async def painel_ticket(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎟️ Painel de Tickets",
            description="Selecione uma opção abaixo para abrir um ticket.",
            color=0x00FFAA
        )
        await ctx.send(embed=embed, view=TicketView())

async def setup(bot: commands.Bot):
    await bot.add_cog(TicketsCog(bot))