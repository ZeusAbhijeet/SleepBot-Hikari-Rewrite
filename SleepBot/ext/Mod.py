from typing import Tuple
import hikari
import lightbulb
import random
import re
import datetime

from time import time
from datetime import timedelta
from lightbulb import commands, context

mod_plugin = lightbulb.Plugin("Mod")

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

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(mod_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(mod_plugin)

