from typing import Optional
import hikari
import lightbulb
from lightbulb.command_handler import Bot
import Utils
import random
import sqlite3

class Rules(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.command(name = "rule", aliases = ['rule_lookup'])
	async def rule_lookup(self, ctx : lightbulb.Context, rule_id : Optional[int] = 1) -> None:
		"""Fetches the rule of the given rule number"""
		#await Utils.command_log(self.bot, ctx, "rule_lookup")
		msg = await ctx.respond(embed = Utils.loading_embed())
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		rule = c.execute("SELECT * FROM rule_table WHERE db_ID = {}".format(rule_id)).fetchone()
		conn.close()
		await msg.edit(
			embed = hikari.Embed(
				title = f"{ctx.author.username} has Pulled Up a Rule!",
				description = f"**{rule[0]}.** {rule[1]}",
				colour = random.randint(0, 0xffffff)
			)
		)
	
def load(bot : Bot) -> None:
	bot.add_plugin(Rules(Bot))
	print("Plugin Rules has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Rules")
