import hikari
import lightbulb
import miru
import aiosqlite

from lightbulb import commands, context
from random import randint
from Utils import TICKETSCATEGORYID, TICKETSLOGCHANNELID, StaffRoleID
from typing import Union
from bot import conn

tickets_plugin = lightbulb.Plugin('Tickets')

async def create_ticket(ctx : Union[context.Context, miru.Context], reason : Union[str, None]) -> hikari.GuildTextChannel:
	c = await conn.execute("SELECT db_ID from tickets_table ORDER BY db_ID DESC	LIMIT 1;")
	id = await c.fetchone()
	if not id:
		id = 0
	else:
		id = id[0]
	
	user_overwrites = hikari.PermissionOverwrite(
		id = ctx.member.id,
		type = hikari.PermissionOverwriteType.MEMBER,
		allow = (
			hikari.Permissions.VIEW_CHANNEL |
			hikari.Permissions.READ_MESSAGE_HISTORY |
			hikari.Permissions.SEND_MESSAGES
		),
	)
	staff_overwrites = hikari.PermissionOverwrite(
		id = StaffRoleID,
		type = hikari.PermissionOverwriteType.ROLE,
		allow = (
			hikari.Permissions.VIEW_CHANNEL |
			hikari.Permissions.READ_MESSAGE_HISTORY |
			hikari.Permissions.SEND_MESSAGES |
			hikari.Permissions.MANAGE_MESSAGES
		),
	)
	everyone_overwrites = hikari.PermissionOverwrite(
		id = ctx.guild_id,
		type = hikari.PermissionOverwriteType.ROLE,
		deny = (
			hikari.Permissions.VIEW_CHANNEL |
			hikari.Permissions.READ_MESSAGE_HISTORY
		),
	)
	ticket_channel = await ctx.get_guild().create_text_channel(f'ticket-id-{id + 1}', category = TICKETSCATEGORYID, permission_overwrites= [user_overwrites, staff_overwrites, everyone_overwrites])
	
	await conn.execute("INSERT INTO tickets_table VALUES (NULL, ?, ?, ?, ?, NULL, NULL, NULL, NULL);", (ctx.member.id, ticket_channel.id, "NULL" if not reason else reason, "False"))
	await conn.commit()

	await ticket_channel.send(
		f"{ctx.member.mention}",
		embed = hikari.Embed(
			title = f"Ticket #{id + 1}",
			description = f"Hey {ctx.member.mention}, a staff member will soon get in touch with you here. In the meantime, please elaborate on why you have opened this ticket so we can help you faster.",
			colour = 0x479760
		).add_field(
			"Reason for opening ticket:",
			reason if reason else f"No reason was provided"
		),
		user_mentions = [ctx.member.id]
	)

	await ctx.app.rest.create_message(
		TICKETSLOGCHANNELID, 
		embed = hikari.Embed(
			title = f"Ticket #{id + 1} opened",
			description = f"Reason: {reason}",
			colour = 0x479760
		).set_author(
			name = f"{ctx.member} ({ctx.member.id})",
			icon = ctx.member.display_avatar_url or ctx.member.default_avatar_url
		)
	)

	return ticket_channel

async def delete_ticket(ctx : context.Context, reason : Union[str, None], db) -> None:
	await ctx.app.rest.create_message(
		TICKETSLOGCHANNELID,
		embed = hikari.Embed(
			title = f"Ticket #{db[0]} closed.",
			description = f"Reason for closing ticket: {reason}",
			colour = 0xf8312f
		).set_author(
			name = f"{ctx.author} ({ctx.author.id})",
			icon = ctx.author.display_avatar_url or ctx.author.default_avatar_url
		)
	)
	
	message_history = await ctx.app.rest.fetch_messages(
		ctx.channel_id
	).sort(key = lambda x : x.id , reverse = False)

	user = ctx.get_guild().get_member(db[1])

	with open("TicketTranscript.txt", "w+") as f:
		f.write(f"Ticket ID #{db[0]} opened by {user} ({user.id}). All times in this transcript are UTC.\n\n")
		i = 1
		for message in message_history:
			str = f"[{message.timestamp.day}-{message.timestamp.month}-{message.timestamp.year} {message.timestamp.hour}:{message.timestamp.minute}:{message.timestamp.second}] {message.author} ({message.author.id}) : {message.content}"
			if message.embeds:
				for embed in message.embeds:
					str = str + f" (type : embed, "
					if embed.title:
						str = str + f"title : '{embed.title}', "
					if embed.description:
						str = str + f"description : '{embed.description}', "
					if embed.fields:
						for field in embed.fields:
							str = str + f"field '{field.name}' : '{field.value}', "
					str = str + f")"
			if message.attachments:
				for attachment in message.attachments:
					str = str + f" (type : attachment, filetype : '{attachment.extension}', filename : '{attachment.filename}')"
					await ctx.app.rest.create_message(
						TICKETSLOGCHANNELID,
						f"Attachment {i}.{attachment.extension}",
						attachment = hikari.Bytes(await attachment.read(), f"attachment {i}.{attachment.extension}")
					)
					i += 1
			str = str + f"\n"
			f.write(str)

	msg = await ctx.app.rest.create_message(
		TICKETSLOGCHANNELID,
		f"Transcript for Ticket #{db[0]}",
		attachment = hikari.File("TicketTranscript.txt", f"Ticket_No_{db[0]}_Transcript.txt")
	)
	
	# TODO: Add ticket_transcript to Database
	await conn.execute("UPDATE tickets_table SET is_closed = 'True', closing_reason = ?, closed_by = ?, ticket_transcript = ? WHERE db_ID = ?;", (reason if reason else "NULL", ctx.author.id, msg.attachments[0].url, db[0],))
	await conn.commit()

	await ctx.get_channel().delete()


@tickets_plugin.command
@lightbulb.command('ticket', "All ticket related commands", auto_defer = True)
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def ticket_group(ctx : context.Context) -> None:
	await ctx.respond(
		embed = hikari.Embed(
			title = "You are forgetting something...",
			description = "This command has subcommands.\nType `?help ticket` to see them all or just use slash commands tbh.",
			colour = 0xf8312f
		)
	)

@ticket_group.child
@lightbulb.option('reason', 'Reason for opening the ticket', type = str, modifier = lightbulb.OptionModifier.CONSUME_REST, required = False, default = "No reason was given.")
@lightbulb.command('open', "Open a new ticket to get assistance from staff or give suggestions.")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def ticket_open(ctx : context.Context) -> None:
	ticket_channel = await create_ticket(ctx, ctx.options.reason)
	
	await ctx.respond(
		f"{ctx.author.mention}, Ticket created in {ticket_channel.mention}.", 
		flags = hikari.MessageFlag.EPHEMERAL,
		delete_after = 10,
		user_mentions = [ctx.author]
	)

@ticket_group.child
@lightbulb.option('reason', 'Reason for closing the ticket', type = str, modifier = lightbulb.OptionModifier.CONSUME_REST, required = False, default = "No reason was given.")
@lightbulb.command('close', "Close the ticket.")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def ticket_close(ctx : context.Context) -> None:
	c = await conn.execute("SELECT db_ID, ticket_author FROM tickets_table WHERE ticket_channel_ID = ?;", (ctx.channel_id,))
	db = await c.fetchone()

	if not db:
		return await ctx.respond(f"Please run this command in an active ticket.")
	
	await ctx.respond("<a:bot_loading:809318632723185714> Creating logs and closing this ticket. Please wait.")
	await delete_ticket(ctx, ctx.options.reason, db)

@ticket_group.child
@lightbulb.option('user', "The user to add to the ticket", type = hikari.User, required = True)
@lightbulb.command('adduser', "Add a user to this ticket.")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def ticket_adduser(ctx : context.Context) -> None:
	c = await conn.execute("SELECT db_ID FROM tickets_table WHERE ticket_channel_ID = ?;", (ctx.channel_id,))
	db = await c.fetchone()

	if not db:
		return await ctx.respond(f"Please run this command in an active ticket.")
	
	user : hikari.User = ctx.options.user

	await ctx.get_channel().edit_overwrite(
		user,
		target_type = hikari.PermissionOverwriteType.MEMBER,
		allow = (
			hikari.Permissions.VIEW_CHANNEL |
			hikari.Permissions.READ_MESSAGE_HISTORY |
			hikari.Permissions.SEND_MESSAGES
		),
	)

	await ctx.respond(f"Added {user.mention} ({user.id}) to the ticket.")

@ticket_group.child
@lightbulb.option('user', 'The user to remove from this ticket', type = hikari.User, required = True)
@lightbulb.command('removeuser', "Remove a user from this ticket.")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def ticket_removeuser(ctx : context.Context) -> None:
	c = await conn.execute("SELECT db_ID FROM tickets_table WHERE ticket_channel_ID = ?;", (ctx.channel_id,))
	db = await c.fetchone()

	if not db:
		return await ctx.respond(f"Please run this command in an active ticket.")
	
	await ctx.get_channel().edit_overwrite(
		ctx.options.user,
		target_type = hikari.PermissionOverwriteType.MEMBER,
		deny = (
			hikari.Permissions.VIEW_CHANNEL |
			hikari.Permissions.READ_MESSAGE_HISTORY |
			hikari.Permissions.SEND_MESSAGES
		),
	)

	await ctx.respond(f"Removed {ctx.options.user.mention} ({ctx.options.user.id}) from the ticket.")

class TicketButton(miru.View):
	def __init__(self,) -> None:
		super().__init__(timeout=None, autodefer=True)
	
	@miru.button(label = "Open Ticket", custom_id = "ticket_create_button")
	async def create_ticket(self, button : miru.Button, ctx : miru.Context) -> None:
		ticket_channel = await create_ticket(ctx, reason = None)
		await ctx.respond(
			f"{ctx.member.mention}, Ticket created in {ticket_channel.mention}.",
			flags = hikari.MessageFlag.EPHEMERAL
		)

@ticket_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command('setbutton', "Set dem button")
@lightbulb.implements(commands.PrefixSubCommand)
async def tickets_button(ctx : context.Context) -> None:
	view = TicketButton()
	message = await ctx.respond(
		embed = hikari.Embed(
			title = "Create Ticket",
			description = (
				"If you want to create a ticket to submit a complaint or a suggestion privately to the Admins or Moderators then press the button below."
				"This will make a new channel below this channel that only you and the staff members can join. You can then clarify more, send attachments as evidence there."
			),
			colour = 0x6db6ea,
		),
		components = view.build() 
	)
	view.start(await message.message())

	msg = await message.message()

	c = await conn.execute("SELECT info FROM general_table WHERE title = 'TICKET-MESSAGE';")
	message_id = await c.fetchone()

	if message_id:
		await conn.execute("UPDATE general_table SET info = ? WHERE title = 'TICKET-MESSAGE';", (msg.id,))
	else:
		await conn.execute("INSERT INTO general_table VALUES (NULL, ?, ?);", ("TICKET-MESSAGE", msg.id,))
	await conn.commit()

@tickets_plugin.listener(hikari.StartedEvent)
async def startup_view(event : hikari.StartedEvent) -> None:
	view = TicketButton()

	c = await conn.execute("SELECT info FROM general_table WHERE title = TICKET-MESSAGE;")
	message_id = await c.fetchone()
	message_id = message_id[0]

	view.start_listener(message_id)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(tickets_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(tickets_plugin)
