from hikari.interactions.component_interactions import ComponentInteraction
from Plugins.Study import StudyBuddiesRoleID
import hikari
import lightbulb
import random

from lightbulb.command_handler import Bot
from hikari import Permissions
import Utils

# Colour Roles


# Club Roles
BookClubRoleID = 768860010120871956
MovieClubRoleID = 785773536685588500
CPClubRoleID = 818467965213081641
OpenSauceClubID = 846731337322463242
BOClubRoleID = 847143247616147466
BlueRadioRoleID = 869909933456519208
QuizClubRoleID = 889040070902956032

ClubRolesList = [BookClubRoleID, MovieClubRoleID, CPClubRoleID, OpenSauceClubID, BOClubRoleID, BlueRadioRoleID, QuizClubRoleID, StudyBuddiesRoleID]

class Roles(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.check(lightbulb.has_guild_permissions(Permissions.MANAGE_ROLES))
	@lightbulb.command(name = 'club_role_menu', aliases = ['clubroles', 'clubrm'])
	async def club_role_menu(self, ctx : lightbulb.Context) -> None:
		ClubRolesRow = self.bot.rest.build_action_row()
		ClubRolesRow2 = self.bot.rest.build_action_row()
		ClubRolesRow.add_button(
			hikari.ButtonStyle.PRIMARY,
			f"{ClubRolesList[0]}"
		).set_label("Book Club").add_to_container()
		ClubRolesRow.add_button(
			hikari.ButtonStyle.PRIMARY,
			f"{ClubRolesList[1]}"
		).set_label("Movie Club").add_to_container()
		ClubRolesRow.add_button(
			hikari.ButtonStyle.PRIMARY,
			f"{ClubRolesList[2]}"
		).set_label("CP Club").add_to_container()
		ClubRolesRow.add_button(
			hikari.ButtonStyle.PRIMARY,
			f"{ClubRolesList[3]}"
		).set_label("Open Sauce Club").add_to_container()

		ClubRolesRow2.add_button(
			hikari.ButtonStyle.SECONDARY,
			f"{ClubRolesList[4]}"
		).set_label("BO Club").add_to_container()
		ClubRolesRow2.add_button(
			hikari.ButtonStyle.SECONDARY,
			f"{ClubRolesList[5]}"
		).set_label("BlueRadio Club").add_to_container()
		ClubRolesRow2.add_button(
			hikari.ButtonStyle.SECONDARY,
			f"{ClubRolesList[6]}"
		).set_label("Quiz Club").add_to_container()
		ClubRolesRow2.add_button(
			hikari.ButtonStyle.SECONDARY,
			f"{ClubRolesList[7]}"
		).set_label("Study Buddies").add_to_container()
		await ctx.message.delete()
		await ctx.respond(f"Join clubs by selecting them from this menu.", components = [ClubRolesRow, ClubRolesRow2])
	
	@lightbulb.listener(hikari.InteractionCreateEvent)
	async def on_button_press(self, event : hikari.InteractionCreateEvent):
		if not isinstance(event.interaction, ComponentInteraction):
			return
		member_roles = event.interaction.member.role_ids
		if int(event.interaction.custom_id) in member_roles:
			await self.bot.rest.remove_role_from_member(
				guild = event.interaction.guild_id,
				user = event.interaction.user,
				role = int(event.interaction.custom_id),
				reason = "User interacted with Role Menu"
			)
			await event.interaction.create_initial_response(
				response_type = hikari.ResponseType.MESSAGE_CREATE,
				content = f"Removed <@&{int(event.interaction.custom_id)}> role!",
				flags = hikari.MessageFlag.EPHEMERAL 
			)
		else:
			await self.bot.rest.add_role_to_member(
				guild = event.interaction.guild_id,
				user = event.interaction.user,
				role = int(event.interaction.custom_id),
				reason = "User interacted with Role Menu"
			)
			await event.interaction.create_initial_response(
				response_type = hikari.ResponseType.MESSAGE_CREATE,
				content = f"Gave you <@&{int(event.interaction.custom_id)}> role!",
				flags = hikari.MessageFlag.EPHEMERAL 
			)

def load(bot : Bot):
	bot.add_plugin(Roles(bot))
	print("Plugin Roles has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Roles")
