import discord

ROLE_MAP = {
    "Anúncios": "Anúncios",
    "Eventos": "Eventos",
    "Jogos": "Jogos",
}

class RoleButton(discord.ui.Button):
    def __init__(self, label: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary,
            custom_id=f"role_button::{label.lower()}"
        )

    async def callback(self, interaction: discord.Interaction):
        role = discord.utils.get(interaction.guild.roles, name=self.label)
        if role is None:
            await interaction.response.send_message(
                f"O cargo `{self.label}` não existe.",
                ephemeral=True
            )
            return

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(
                f"Cargo `{role.name}` removido.",
                ephemeral=True
            )
        else:
            await member.add_roles(role)
            await interaction.response.send_message(
                f"Cargo `{role.name}` adicionado.",
                ephemeral=True
            )

class RolePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for role_name in ROLE_MAP:
            self.add_item(RoleButton(role_name))