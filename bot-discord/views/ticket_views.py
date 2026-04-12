import discord

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Suporte", value="suporte", emoji="🎟️"),
            discord.SelectOption(label="Denúncia", value="denuncia", emoji="⚠️"),
            discord.SelectOption(label="Parceria", value="parceria", emoji="🤝"),
        ]
        super().__init__(
            placeholder="Escolha o tipo do ticket...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_select_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{self.values[0]}-{user.name}".lower().replace(" ", "-"),
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎟️ Ticket Criado",
            description=f"{user.mention}, descreva seu problema.",
            color=0x00FFAA
        )

        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(
            f"Ticket criado: {channel.mention}",
            ephemeral=True
        )

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fechar Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="close_ticket_button"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Fechando ticket em 3 segundos...",
            ephemeral=True
        )
        await interaction.channel.delete()