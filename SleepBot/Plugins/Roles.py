from hikari.interactions.component_interactions import ComponentInteraction
from Plugins.Study import StudyBuddiesRoleID
import hikari
import lightbulb
import random

from lightbulb.command_handler import Bot
from hikari import Permissions
import Utils

class Roles(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.check(lightbulb.has_guild_permissions(Permissions.MANAGE_ROLES))
	@lightbulb.command(name = 'role_menu', aliases = ['rolemenu'])
	async def role_menu_builder(self, ctx : lightbulb.Context) -> None:
		row = self.bot.rest.build_action_row()
		row.add_button(hikari.ButtonStyle.SECONDARY, "study_buddies").set_label("Study Buddies").set_emoji("📚").add_to_container()
		await ctx.respond(f"Select your roles from below", component = row)
	
	@lightbulb.listener(hikari.InteractionCreateEvent)
	async def on_button_press(self, event : hikari.InteractionCreateEvent):
		if not isinstance(event.interaction, ComponentInteraction):
			return
		if event.interaction.custom_id == "study_buddies":
			await self.bot.rest.add_role_to_member(
				guild = event.interaction.guild_id,
				user = event.interaction.user,
				role = StudyBuddiesRoleID,
				reason = "User Interacted with Role Menu Buttons"
			)
			await event.interaction.create_initial_response(
				response_type = hikari.ResponseType.MESSAGE_CREATE,
				content = f"Gave you <@&{StudyBuddiesRoleID}> role",
				flags = hikari.MessageFlag.EPHEMERAL 
			)

def load(bot : Bot):
	bot.add_plugin(Roles(bot))
	print("Plugin Roles has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Roles")
