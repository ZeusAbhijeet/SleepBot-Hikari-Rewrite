from hikari.undefined import count
from lightbulb.slash_commands.commands import SlashSubCommand
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

MAX_MESSAGE_BULK_DELETE = datetime.timedelta(weeks = 2)

class Mod(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@checks.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
	@lightbulb.command(name = "clear", aliases = ['purge', 'cls'])
	async def clear_command(self, ctx : lightbulb.Context, amount : typing.Optional[int] = 3):
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

			async for messages in iterator:
				await self.bot.rest.delete_messages(ctx.channel_id, messages)
			
			msg = await ctx.respond(f"Deleted Messages.")
			await asyncio.sleep(5)
			await msg.delete()

class Clear(slash_commands.SlashCommandGroup):
	description = "Clear Message base group"

	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

@Clear.subcommand()
class All(slash_commands.SlashSubCommand):
	description = "Clears the given number of messages in channel before/after provided message ID."

	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	options : list[hikari.CommandOption] = [
		hikari.CommandOption(
			name = "count",
			description = "Number of messages to delete",
			type = hikari.OptionType.INTEGER,
			is_required = True
		),
	]


	async def callback(self, context: slash_commands.SlashCommandContext) -> None:
		user_permissions = context.member.permissions
		if user_permissions.any(hikari.Permissions.ADMINISTRATOR ,hikari.Permissions.MANAGE_MESSAGES):
			count = context.option_values.count

			if count <= 0 or count > 100 :
				return await context.respond("Count must be more than 0 and less than 100.")
			
			now = dt.now(tz = pytz.timezone("UTC"))
			
			iterator = context.bot.rest.fetch_messages(
				context.channel_id
			).filter(lambda message: now - message.created_at.astimezone(tz = pytz.timezone("UTC")) < MAX_MESSAGE_BULK_DELETE)

			iterator = iterator.limit(count)
			
			iterator = iterator.map(lambda x: x.id).chunk(100)

			async for messages in iterator:
				await context.bot.rest.delete_messages(context.channel_id, messages)
			
			await context.respond(f"Deleted Messages.")

		else:
			await context.respond(f"No")


def load(bot : Bot):
	bot.add_plugin(Mod(bot))
	bot.add_slash_command(Clear, create = True)

def unload(bot : Bot):
	bot.remove_plugin("Mod")
	bot.remove_slash_command("Clear")

