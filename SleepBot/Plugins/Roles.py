from os import name
from hikari.interactions.component_interactions import ComponentInteraction
import hikari
from hikari import ButtonStyle
import lightbulb
import random
import sqlite3

from lightbulb.command_handler import Bot
from hikari import Permissions

# TODO
# Change the role menu wordings

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
			ButtonStyle.PRIMARY,
			f"BOOKCLUB"
		).set_label("Book Club").add_to_container()
		ClubRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"MOVIECLUB"
		).set_label("Movie Club").add_to_container()
		ClubRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"CPCLUB"
		).set_label("CP Club").add_to_container()
		ClubRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"OPENSAUCECLUB"
		).set_label("Open Sauce Club").add_to_container()

		ClubRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			f"BOCLUB"
		).set_label("BO Club").add_to_container()
		ClubRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			f"OPENMICCLUB"
		).set_label("Open Mic Club").add_to_container()
		ClubRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			f"QUIZCLUB"
		).set_label("Quiz Club").add_to_container()
		ClubRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			f"STUDYCLUB"
		).set_label("Study Buddies").add_to_container()
		await ctx.message.delete()
		await ctx.respond(f"Select the clubs you want to join from this menu.", components = [ClubRolesRow, ClubRolesRow2])
	
	@lightbulb.check(lightbulb.has_guild_permissions(Permissions.MANAGE_ROLES))
	@lightbulb.command(name = 'colour_role_menu', aliases = ['colourrolemenu', 'colourrm', 'colorrm'])
	async def colour_role_menu(self, ctx : lightbulb.Context) -> None:
		ColourRolesRow = self.bot.rest.build_action_row()
		ColourRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"COLOUR_RED"
		).set_label("Red").add_to_container()
		ColourRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"COLOUR_YELLOW"
		).set_label("Yellow").add_to_container()
		ColourRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"COLOUR_ORANGE"
		).set_label("Orange").add_to_container()
		ColourRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"COLOUR_GREEN"
		).set_label("Green").add_to_container()
		ColourRolesRow.add_button(
			ButtonStyle.PRIMARY,
			f"COLOUR_BLUE"
		).set_label("Blue").add_to_container()

		await ctx.message.delete()
		await ctx.respond(f"Select the colour you want your display name to show up in.", component = ColourRolesRow)
	
	@lightbulb.check(lightbulb.has_guild_permissions(Permissions.MANAGE_ROLES))
	@lightbulb.command(name = 'squad_role_menu', aliases = ['squadrolemenu', 'squadrm'])
	async def squad_role_menu(self, ctx : lightbulb.Context) -> None:
		SquadRolesRow = self.bot.rest.build_action_row()
		SquadRolesRow2 = self.bot.rest.build_action_row()
		SquadRolesRow.add_button(
			ButtonStyle.PRIMARY,
			'ASTRONOMY'
		).set_label("Astronomy Squad").add_to_container()
		SquadRolesRow.add_button(
			ButtonStyle.PRIMARY,
			'FINANCE'
		).set_label("Finance Squad").add_to_container()
		SquadRolesRow.add_button(
			ButtonStyle.PRIMARY,
			'CODING'
		).set_label("Coding Squad").add_to_container()
		
		SquadRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			'ANIME'
		).set_label("Anime Squad").add_to_container()
		SquadRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			'DESIGN'
		).set_label("Design Squad").add_to_container()
		SquadRolesRow2.add_button(
			ButtonStyle.SECONDARY,
			'PHILOSOPHY'
		).set_label("Philosphy Squad").add_to_container()

		await ctx.message.delete()
		await ctx.respond(f"Select the squads you are interested in from this menu.", components = [SquadRolesRow, SquadRolesRow2])
	
	@lightbulb.check(lightbulb.has_guild_permissions(Permissions.MANAGE_ROLES))
	@lightbulb.command(name = 'announcement_role_menu', aliases = ['announcementrolemenu', 'announcementrm'])
	async def announcement_role_menu(self, ctx : lightbulb.Context) -> None:
		RolesRow = self.bot.rest.build_action_row()
		RolesRow.add_button(
			ButtonStyle.PRIMARY,
			'COMMUNITY'
		).set_label('Community Event Announcements').add_to_container()
		RolesRow.add_button(
			ButtonStyle.PRIMARY,
			'TALKS'
		).set_label('Talks/Fireside Chat Events').add_to_container()
		RolesRow.add_button(
			ButtonStyle.PRIMARY,
			'SERVER'
		).set_label('Server Announcement Pings').add_to_container()

		await ctx.message.delete()
		await ctx.respond(f"Select the Announcements you would like to get notified for from below.", component = RolesRow)

	@lightbulb.listener(hikari.InteractionCreateEvent)
	async def on_button_press(self, event : hikari.InteractionCreateEvent):
		if not isinstance(event.interaction, ComponentInteraction):
			return
		member_roles = event.interaction.member.role_ids
		if event.interaction.custom_id.lower().startswith('colour'):
			member_role_names = await event.interaction.member.fetch_roles()
			for m in member_role_names:
				if m.name == 'Red' or m.name == 'Yellow' or m.name == 'Green' or m.name == 'Blue' or m.name == 'Orange':
					await event.interaction.member.remove_role(m)
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		Role = c.execute("SELECT role_ID FROM role_table WHERE title = '{}';".format(str(event.interaction.custom_id))).fetchone()
		Role = int(Role[0])
		conn.close()
		if int(Role) in member_roles:
			await self.bot.rest.remove_role_from_member(
				guild = event.interaction.guild_id,
				user = event.interaction.user,
				role = int(Role),
				reason = "User interacted with Role Menu"
			)
			await event.interaction.create_initial_response(
				response_type = hikari.ResponseType.MESSAGE_CREATE,
				content = f"Removed <@&{int(Role)}> role!",
				flags = hikari.MessageFlag.EPHEMERAL 
			)
		else:
			await self.bot.rest.add_role_to_member(
				guild = event.interaction.guild_id,
				user = event.interaction.user,
				role = int(Role),
				reason = "User interacted with Role Menu"
			)
			await event.interaction.create_initial_response(
				response_type = hikari.ResponseType.MESSAGE_CREATE,
				content = f"Gave you <@&{int(Role)}> role!",
				flags = hikari.MessageFlag.EPHEMERAL 
			)

def load(bot : Bot):
	bot.add_plugin(Roles(bot))
	print("Plugin Roles has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Roles")
