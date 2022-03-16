from typing import Tuple
import hikari
import lightbulb
import re
import datetime

from time import time
from datetime import timedelta
from lightbulb import commands, context

mod_plugin = lightbulb.Plugin("Mod")

MAX_MESSAGE_BULK_DELETE = datetime.timedelta(weeks=2) - datetime.timedelta(minutes=2)

def iter_messages(
    ctx: context.Context,
    bot_only: bool,
    human_only: bool,
    has_attachments: bool,
    has_embeds: bool,
	has_emojis: bool,
	has_stickers: bool,
	count: int = None,
	after: hikari.Snowflake = None,
    user: hikari.User = None,
) -> hikari.LazyIterator[hikari.Message]:
	before = hikari.Snowflake.from_datetime(datetime.datetime.now(tz = datetime.timezone.utc))

	if human_only and bot_only:
		raise lightbulb.CommandInvocationError(original="Can only specify one of `human_only` or `user_only`")

	if count is None and after is None:
		raise lightbulb.CommandInvocationError(original="Must specify `count` when `after` is not specified")

	elif count <= 0:
		raise lightbulb.CommandInvocationError(original="Count must be greater than 0.")

	if after is not None:
		iterator = ctx.app.rest.fetch_messages(ctx.channel_id, before=before).take_while(lambda message: message.id > after)

	else:
		iterator = ctx.app.rest.fetch_messages(
			ctx.channel_id,
			before=hikari.UNDEFINED if before is None else before,
			after=hikari.UNDEFINED if after is None else after,
		)

	if human_only:
		iterator = iterator.filter(lambda message: not message.author.is_bot)

	elif bot_only:
		iterator = iterator.filter(lambda message: message.author.is_bot)

	if has_attachments:
		iterator = iterator.filter(lambda message: bool(message.attachments))

	if has_embeds:
		iterator = iterator.filter(lambda message: bool(message.embeds))
	
	if has_emojis:
		iterator = iterator.filter(lambda message: bool(message.content and message.content.startswith('<') and message.content.endswith('>')))
	
	if has_stickers:
		iterator = iterator.filter(lambda message: bool(message.stickers))

	if user is not None:
		iterator = iterator.filter(lambda message: message.author.id == user.id)

	if count:
		iterator = iterator.limit(count)

	return iterator

@mod_plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MODERATE_MEMBERS))
@lightbulb.option("reason", "The reason for timeout. Will show up in Audit Logs.", type = str, modifier = lightbulb.OptionModifier.CONSUME_REST, required = True)
@lightbulb.option("duration", "The time to give time out for.", str, required = True)
@lightbulb.option("user", "The user to timeout", hikari.User, required = True)
@lightbulb.command("timeout", "Time out a user", auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def timeout_cmd(ctx : context.Context) -> None:
	target = ctx.options.user
	reason = ctx.options.reason
	duration = ctx.options.duration
	target = ctx.get_guild().get_member(target)

	time_pattern = r"(\d+\.?\d?[s|m|h|d|w]{1})\s?"

	units = {
        's': 'seconds',
        'm': 'minutes',
        'h': 'hours',
        'd': 'days',
        'w': 'weeks'
    }

	def parse(time_string: str) -> Tuple[str, float]:
		unit = time_string[-1]
		amount = float(time_string[:-1])
		return units[unit], amount

	if matched := re.findall(time_pattern, duration, flags=re.I):
		time_dict = dict(parse(match) for match in matched)
		time_s = int(timedelta(**time_dict).total_seconds())
	else:
		raise ("Invalid string format. Time must be in the form <number>[s|m|h|d|w].")
	
	if not 1 <= time_s <= 2_419_200:
		await ctx.respond("The timeout must be between 1 second and 28 days inclusive.")
		return

	await target.edit(
		communication_disabled_until = (datetime.datetime.utcnow() + datetime.timedelta(seconds=time_s)).isoformat(),
		reason = reason
	)

	await ctx.respond(f"Timed out {target.mention} until <t:{int(time())+time_s}>")

@mod_plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
@lightbulb.option('stickers', 'Only delete messages containing stickers', type = bool, required = False, default = False)
@lightbulb.option('emojis', 'Only delete messages containing emojis', type = bool, required = False, default = False)
@lightbulb.option('embeds', 'Only delete messages containing embeds', type = bool, required = False, default = False)
@lightbulb.option('attachments', 'Only delete messages containing attachments', type = bool, required = False, default = False)
@lightbulb.option('humans_only', 'Only delete messages sent by humans', type = bool, required = False, default = False)
@lightbulb.option('bot_only', 'Only delete messages sent by bots', type = bool, required = False, default = False)
@lightbulb.option('after_message_id', 'Delete messages after a particular message id', type = int, required = False)
@lightbulb.option('user', 'The user to delete messages of', type = hikari.User, required = False)
@lightbulb.option('count', 'Number of messages to delete', type = int, required = False, min_value = 1, max_value = 100)
@lightbulb.command('purge', 'Delete messages from current channel', auto_defer = True, ephemeral = True)
@lightbulb.implements(commands.SlashCommand)
async def purge_cmd(ctx : context.Context) -> None:
	now = datetime.datetime.now(tz=datetime.timezone.utc)
	after_message = None
	try:
		after_message = await ctx.app.rest.fetch_message(ctx.channel_id, ctx.options.after)
	except:
		pass
	after_too_old = after_message and now - after_message.created_at >= MAX_MESSAGE_BULK_DELETE

	if after_too_old:
		raise lightbulb.CommandInvocationError(original='Cannot delete messages that are over 14 days old')
	
	iterator = (
		iter_messages(
			ctx, 
			ctx.options.bot_only, 
			ctx.options.human_only, 
			ctx.options.attachments,
			ctx.options.embeds,
			ctx.options.emojis,
			ctx.options.stickers,
			ctx.options.count,
			ctx.options.after,
			ctx.options.user
		).take_while(lambda message : now - message.created_at < MAX_MESSAGE_BULK_DELETE)
		.map(lambda x: x.id)
		.chunk(100)
	)

	async for messages in iterator:
		await ctx.app.rest.delete_messages(ctx.channel_id, *messages)
		break

	await ctx.respond("Deleted messages", delete_after = 4)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(mod_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(mod_plugin)

