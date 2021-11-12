import hikari
from hikari.interactions.base_interactions import ResponseType
import lightbulb
import Utils
import random
import sqlite3
import typing

from lightbulb import slash_commands
from lightbulb.command_handler import Bot
from lightbulb.slash_commands.commands import Option
from __init__ import GUILD_ID
from typing import Optional

class Rules(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.command(name = "rule", aliases = ['rule_lookup'])
	async def rule_lookup(self, ctx : lightbulb.Context, rule_id : Optional[int] = 1) -> None:
		"""Fetches the rule of the given rule number"""
		#await Utils.command_log(self.bot, ctx, "rule_lookup")
		if rule_id <= 0 or rule_id > 10:
			return await ctx.respond("That does not seem like a valid rule id. Try again.")
		
		msg = await ctx.respond(embed = Utils.loading_embed())
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		rule = c.execute("SELECT * FROM rule_table WHERE db_ID = {}".format(rule_id)).fetchone()
		print(rule)
		conn.close()
		await msg.edit(
			embed = hikari.Embed(
				title = f"{ctx.author.username} has Pulled Up a Rule!",
				description = f"**{rule[0]}.** {rule[1]}",
				colour = random.randint(0, 0xffffff)
			)
		)

class Rule_lookup(slash_commands.SlashCommand):
	description = "Fetches the server rule from the given rule number"

	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	rule_id : int = Option(description = "The rule number of rule to fetch.", required = True)

	async def callback(self, ctx: lightbulb.SlashCommandContext) -> None:
		rule_id = ctx.options.rule_id

		if rule_id <= 0 or rule_id > 10:
			return await ctx.respond("That does not seem like a valid rule id. Try again.")
		
		await ctx.respond(response_type = ResponseType.DEFERRED_MESSAGE_CREATE)

		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		rule = c.execute("SELECT * FROM rule_table WHERE db_ID = {}".format(rule_id)).fetchone()
		conn.close()

		await ctx.edit_response(
			embed = hikari.Embed(
				title = f"{ctx.author.username} has Pulled Up a Rule!",
				description = f"**{rule[0]}.** {rule[1]}",
				colour = random.randint(0, 0xffffff)
			)
		)

	
def load(bot : Bot) -> None:
	bot.add_plugin(Rules(Bot))
	bot.autodiscover_slash_commands(create = True)
	print("Plugin Rules has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Rules")
	bot.remove_slash_command("Rule_lookup")
