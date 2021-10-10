from typing import List, Union, Optional
import hikari
from hikari.impl import bot
import lightbulb
import sqlite3
import random

from lightbulb.command_handler import Bot
import Utils
import asyncio


class Points(lightbulb.Plugin):
	"""
	Contains commands for checking user's Bluelearn Coins balance and leaderboard
	"""
	def __init__(self, bot : Bot):
		self.bot = bot
		super().__init__()

	@lightbulb.check(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
	@lightbulb.command(name = "give_coins", aliases = ["givecoins"])
	async def give_coins_command(self, ctx : lightbulb.Context, target : hikari.Member = None, amount : Optional[int] = 0) -> None:
		"""Gives the mentioned user the given amount of coins"""
		await Utils.command_log(self.bot, ctx, "give_coins")
		if target == None:
			return
		if target.id in Utils.POINT:
			Utils.POINT[target.id] += amount
		else:
			Utils.POINT[target.id] = amount
		await ctx.respond(f"Gave {target.mention} {amount} coins.", user_mentions = False)	

	@lightbulb.command(name = "coins", aliases = ["coin"])
	async def coins(self, ctx : lightbulb.Context, target : Optional[hikari.Member] = None) -> None:
		"""Shows the amount of coins a mentioned user has."""
		await Utils.command_log(self.bot, ctx, "coins")
		return await ctx.respond("This command has been disabled due to a glitch for indefinite time.")
		
		total_coins = dict(Utils.POINT)
		for user in Utils.DB_POINT:
			if user[0] in total_coins:
				total_coins[user[0]] += user[1]
			else:
				total_coins[user[0]] = user[1]
			
		if target == None:
			return await ctx.respond("Mention a user to check coins.")
		else:
			msg = await ctx.respond(embed = Utils.loading_embed())
			if not (target.id in total_coins):
				total_coins[target.id] = 0
			embed = hikari.Embed(
				title = f"User {target.display_name}'s Coins",
				description = f"{target.display_name} has {total_coins[target.id]} since reset.",
				colour = random.randint(0, 0xffffff)
			)
			await msg.edit(embed = embed)
			return
	

	@lightbulb.command(name = 'top', aliases = ['leaderboard', 'all_coins', 'lb'])
	async def top_command(self, ctx : lightbulb.Context) -> None:
		await Utils.command_log(self.bot, ctx, "top")

		return await ctx.respond("This command has been disabled due to a glitch for indefinite time.")

		msg = await ctx.respond(embed = Utils.loading_embed())
		total_coins = dict(Utils.POINT)
		for user in Utils.DB_POINT:
			if user[0] in total_coins:
				total_coins[user[0]] += user[1]
			else:
				total_coins[user[0]] = user[1]
		
		top_20 = 1
		total_coins = sorted(total_coins.items(), key = lambda kv : kv[1])
		total_coins.reverse()
		embed = hikari.Embed(
			title= "Coins Leaderboard",
			colour = random.randint(0, 0xffffff)
		)
		for user in total_coins:
			try:
				member = ctx.get_guild().get_member(int(user[0]))
				#member = await self.bot.rest.fetch_member(ctx.guild_id, int(user[0]))
			except:
				continue
			if member == None:
				continue
			embed.add_field(
				name = f"{top_20} : {member.display_name}",
				value = f"{user[1]}",
				inline = True
			)
			top_20 += 1
			if top_20 == 21:
				break
		await msg.edit(embed = embed)

#	@lightbulb.listener(event_type = hikari.MessageCreateEvent)
#	async def on_message(self, event : hikari.MessageCreateEvent):
#		if not await Utils.is_point_chnl(event.channel_id):
#			return
#		if event.author.is_bot:
#			return
#		if random.randint(0, 200) == 0:
#			emoji = '🎖'
#			await event.app.rest.add_reaction(event.channel_id, event.message_id, emoji)
#			if event.author_id in Utils.POINT:
#				Utils.POINT[event.author_id] += 5
#			else:
#				Utils.POINT[event.author_id] = 5
	

def load(bot : Bot) -> None:
	bot.add_plugin(Points(bot))
	print("Plugin Points has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Points")
