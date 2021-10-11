from hikari.errors import NotFoundError
from lightbulb.slash_commands.commands import Option, SlashSubCommand
import pytz
import typing
import lightbulb
import hikari
import Utils
import asyncio
import random
import datetime

from lightbulb import checks, slash_commands
from lightbulb.command_handler import Bot
from __init__ import GUILD_ID
from datetime import datetime as dt
from typing import Optional

MAX_MESSAGE_BULK_DELETE = datetime.timedelta(weeks = 2)

class Mod(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.check(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
	@lightbulb.command(name = "clear", aliases = ['purge', 'delete'])
	async def clear_all_command(self, ctx : lightbulb.Context, amount : typing.Optional[int] = 3):
		"""
		Deletes the given amount of messages from the channel. If no amount is given, 3 messages are deleted.
		"""
		await Utils.command_log(self.bot, ctx, "clear")
		await ctx.message.delete()
		if amount <= 0 or amount > 100:
			return await ctx.respond("Provide an amount between 1 and 100")
		else:
			now = dt.now(tz = pytz.timezone("UTC"))
			
			iterator = self.bot.rest.fetch_messages(
				ctx.channel_id
			).filter(lambda message: now - message.created_at.astimezone(tz = pytz.timezone("UTC")) < MAX_MESSAGE_BULK_DELETE)

			iterator = iterator.limit(amount)
			
			iterator = iterator.map(lambda x: x.id).chunk(100)

			try:
				async for messages in iterator:
					await self.bot.rest.delete_messages(ctx.channel_id, messages)
			except NotFoundError:
				pass
			
			msg = await ctx.respond(f"Deleted Messages.")
			await asyncio.sleep(5)
			await msg.delete()
	
	@lightbulb.check(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
	@lightbulb.command(name = "clearemote", aliases = ['clearemojis', 'clearemotes'])
	async def clear_emote_command(self, ctx : lightbulb.Context, count : typing.Optional[int] = 3):
		"""
		Deletes the given amount of emotes from the channel. If none is given, 3 emotes are deleted.
		"""
		await Utils.command_log(self.bot, ctx, "clearemote")
		await ctx.message.delete()
		
		# If count given is not between 1 and 100 (1 and 100 inclusive), return
		if count <= 0 or count > 100:
			return await ctx.respond("Count must be more than 0 and less than 100.")
		
		msg = await ctx.respond(embed = hikari.Embed(description = f"<a:BotLoading:884014612637417513> Deleting {count} messages containing emotes..."))
		
		savecount = count
		deleted = 0
		msgList = []

		now = dt.now(tz = pytz.timezone("UTC"))
		iterator = self.bot.rest.fetch_messages(
			ctx.channel_id
		).filter(lambda message: now - message.created_at.astimezone(tz = pytz.timezone("UTC")) < MAX_MESSAGE_BULK_DELETE)
		iterator = iterator.limit(1000)

		async for messages in iterator:
			if savecount <= 0:
				break
			if messages.content and messages.content.startswith("<") and messages.content.endswith(">"):
				msgList.append(messages.id)
				savecount -= 1
				deleted += 1
		
		try:
			await self.bot.rest.delete_messages(ctx.channel_id, msgList)
		except NotFoundError:
			pass

		await msg.edit(
			embed = hikari.Embed(
				title = "Delete Emotes",
				description = f"Deleted **{deleted}/{count}** Emojis.",
				color = random.randint(0, 0xffffff)
			)
		)
		await asyncio.sleep(5)
		await msg.delete()


class Clear(slash_commands.SlashCommandGroup):
	description = "Clear Message base group"

	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	checks = [lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)]

@Clear.subcommand()
class All(slash_commands.SlashSubCommand):
	description = "Clears the given number of messages in channel"

	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	count : int = Option("Number of Messages to delete", required = True)

	user : Optional[hikari.User] = Option("User to delete messages of", required = False, default = None)
	
	checks = [lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)]

	async def callback(self, context: slash_commands.SlashCommandContext) -> None:
		count = context.options.count

		user = context.options.user

		if count <= 0 or count > 100 :
			return await context.respond("Count must be more than 0 and less than 100.")
		
		now = dt.now(tz = pytz.timezone("UTC"))
		
		iterator = context.bot.rest.fetch_messages(
			context.channel_id
		).filter(lambda message: now - message.created_at.astimezone(tz = pytz.timezone("UTC")) < MAX_MESSAGE_BULK_DELETE)
		
		iterator = iterator.limit(count)

		msgList = []

		if user is not None:
			savecount = count
			deleted = 0
			async for messages in iterator:
				if savecount <= 0:
					break
				if messages.author.id == user:
					msgList.append(messages.id)
					savecount -= 1
					deleted += 1

		if not msgList:
			iterator = iterator.map(lambda x: x.id).chunk(100)
			try:
				async for messages in iterator:
					await context.bot.rest.delete_messages(context.channel_id, messages)
			except NotFoundError:
				pass
		else:
			try:
				await self.bot.rest.delete_messages(context.channel_id, msgList)
			except NotFoundError:
				pass
			
		await context.respond(f"Deleted Messages.")
		await asyncio.sleep(5)
		await context.delete_response()

	

@Clear.subcommand()
class Emotes(slash_commands.SlashSubCommand):
	description = "Clears the given number of Emojis from the channel."

	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	count : int = Option("Number of Emojis to delete", required = True)

	checks = [lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)]

	async def callback(self, context: slash_commands.SlashCommandContext) -> None:
		count = context.options.count

		if count <= 0 or count > 100:
			return await context.respond("Count must be more than 0 and less than 100.")
		
		await context.respond(embed = hikari.Embed(description = f"<a:BotLoading:884014612637417513> Deleting {count} messages containing emotes..."))

		savecount = count
		deleted = 0
		msgList = []

		now = dt.now(tz = pytz.timezone("UTC"))
		iterator = context.bot.rest.fetch_messages(
			context.channel_id
		).filter(lambda message: now - message.created_at.astimezone(tz = pytz.timezone("UTC")) < MAX_MESSAGE_BULK_DELETE)

		iterator = iterator.limit(1000)

		async for messages in iterator:
			if savecount <= 0:
				break
			if messages.content and messages.content.startswith("<") and messages.content.endswith(">"):
				msgList.append(messages.id)
				savecount -= 1
				deleted += 1
			
			
		try:
			await context.bot.rest.delete_messages(context.channel_id, msgList)
		except NotFoundError:
			pass

		await context.edit_response(
			embed = hikari.Embed(
				title = "Delete Emotes",
				description = f"Deleted **{deleted}/{count}** Emojis.",
				color = random.randint(0, 0xffffff)
			)
		)
		await asyncio.sleep(5)
		await context.delete_response()

def load(bot : Bot):
	bot.add_plugin(Mod(bot))
	bot.add_slash_command(Clear, create = True)
	print("Plugin Mod has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Mod")
	bot.remove_slash_command("Clear")

