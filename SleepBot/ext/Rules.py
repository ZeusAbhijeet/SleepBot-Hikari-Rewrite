import hikari
import lightbulb
import aiosqlite

from lightbulb import commands, context
from random import randint

rules_plugin = lightbulb.Plugin("Rules")

@rules_plugin.command
@lightbulb.option(name = "rule_number", description = "The Rule number to look up.", type = int, required = False, default = 1, min_value = 1, max_value = 10)
@lightbulb.command("rule", "Shows the Server Rule according to the given rule number", aliases = ['rule_lookup'], auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def rule_lookup_cmd(ctx : context.Context) -> None:
	rule_id = ctx.options.rule_number

	if rule_id <= 0 or rule_id > 10:
		return await ctx.respond(f"That does not seem like a valid rule number. Try again.")

	conn = await aiosqlite.connect('Database.db')
	c = await conn.cursor()
	await c.execute(f'SELECT * FROM rule_table WHERE db_ID = {rule_id}')
	rule = await c.fetchone()
	await conn.close()

	await ctx.respond(
		embed = hikari.Embed(
			title = f"{ctx.author.username} has pulled up a rule!",
			description = f"**{rule[0]}.** {rule[1]}",
			colour = randint(0, 0xffffff)
		)
	)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(rules_plugin)

def unload(bot: lightbulb.BotApp) -> None:
	bot.remove_plugin(rules_plugin)

