import hikari
import lightbulb

from lightbulb import commands, context
from random import randint

faq_plugin = lightbulb.Plugin("FAQs")

@faq_plugin.command
@lightbulb.command("faq", "Check all the frequently asked questions regarding Bluelearn, Discord and this server.")
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def faq_cmd_group(ctx : context.Context) -> None:
	await ctx.respond(
		embed = hikari.Embed(
			title = "FAQ",
			description = "This command has sub commands. Type `?help faq` to find out about them.",
			colour = randint(0, 0xffffff)
		)
	)

@faq_cmd_group.child
@lightbulb.command("blc", "FAQs about Bluelearn Coins.")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def faq_blc(ctx : context.Context) -> None:
	await ctx.respond(
		embed = hikari.Embed(
			title = "BL Coins FAQ",
			description = "A few frequently asked questions about Bluelearn Coins:",
			colour = randint(0, 0xffffff)
		).add_field(
			"What are Bluelearn Coins?",
			"Bluelearn Coins are reward points that you get whenever you participate in competitions or interact on the server."
		).add_field(
			"How do I earn BL Coins?",
			"You can earn them by\n**1.** Participating in competitions, ideathons, hackathons, etc.\n**2.** Chatting on the server. The top 15 members on the levelling leaderboard get BLC on every reset.\n**3.** Studying with others in Study Streak Club. Top few members get BLC after every week."
		).add_field(
			"What can I do with BL Coins?",
			"You can redeem the BL Coins for items in <#773083211218550784>"
		).add_field(
			"How do I check my BL Coins balance?",
			"Head over to <#773962393109135380> and type `/coins` or `?coins`"
		)
	)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(faq_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(faq_plugin)
