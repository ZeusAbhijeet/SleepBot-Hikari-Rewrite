from sqlite3.dbapi2 import connect
from typing import List, Union, Optional, Iterable
import hikari
from hikari.impl import bot
import lightbulb
import sqlite3
import random
from lightbulb import slash_commands

from lightbulb.command_handler import Bot
from lightbulb.slash_commands.commands import Option
from __init__ import GUILD_ID
import Utils

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
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		target_coins = c.execute("SELECT points FROM point_table WHERE user_ID = {};".format(target.id)).fetchone()
		if target_coins is None:
			target_coins = amount
			c.execute("INSERT INTO point_table VALUES (NULL, {}, {});".format(target.id, target_coins))
		else:
			target_coins = target_coins[0]
			target_coins += amount
			c.execute(f"UPDATE point_table SET points = {target_coins} WHERE user_id = {target.id};")
		conn.commit()
		conn.close()
		await ctx.respond(f"Gave {target.mention} {amount} coins.", user_mentions = False)	

	@lightbulb.check(Utils.is_point_cmd_chnl)
	@lightbulb.command(name = "coins", aliases = ["coin"])
	async def coins(self, ctx : lightbulb.Context, target : Optional[hikari.Member] = None) -> None:
		"""Shows the amount of coins a mentioned user has."""
		await Utils.command_log(self.bot, ctx, "coins")
		if target is None:
			target = ctx.get_guild().get_member(ctx.author)
		msg = await ctx.respond(embed = Utils.loading_embed())
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		target_coins = c.execute("SELECT points FROM point_table WHERE user_ID = {};".format(target.id)).fetchone()
		if target_coins is None:
			target_coins = 0
			c.execute("INSERT INTO point_table VALUES (NULL, {}, {});".format(target.id, target_coins))
			conn.commit()
			conn.close()
		else:
			target_coins = target_coins[0]
		embed = hikari.Embed(
			title = f"User {target.display_name}'s Coins",
			description = f"{target.display_name} has {target_coins} coins since reset.",
			colour = random.randint(0, 0xffffff)
		)
		await msg.edit(embed = embed)
		return
	
	
	@lightbulb.command(name = 'top', aliases = ['leaderboard', 'all_coins', 'lb'])
	async def top_command(self, ctx : lightbulb.Context) -> None:
		await Utils.command_log(self.bot, ctx, "top")
		msg = await ctx.respond(embed = Utils.loading_embed())
		
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		DB = c.execute('SELECT user_ID, points FROM point_table;').fetchall()
		conn.close()

		total_coins = dict(DB)

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

	@lightbulb.listener(event_type = hikari.MessageCreateEvent)
	async def on_message(self, event : hikari.MessageCreateEvent):
		if not await Utils.is_point_chnl(event.channel_id):
			return
		if event.author.is_bot:
			return
		if random.randint(0, 200) == 0:
			emoji = '🎖'
			await event.app.rest.add_reaction(event.channel_id, event.message_id, emoji)
			conn = sqlite3.connect('Database.db')
			c = conn.cursor()
			target_coins = c.execute(f'SELECT points FROM point_table WHERE user_ID = {event.author_id};').fetchone()
			if target_coins is None:
				target_coins = 5
				c.execute('INSERT INTO point_table VALUES (NULL, {}, {});'.format(event.author_id, target_coins))
			else:
				target_coins = target_coins[0]
				target_coins += 5
				c.execute(f"UPDATE point_table SET points = {target_coins} WHERE user_id = {event.author_id};")
			conn.commit()
			conn.close()
	
class Coins(slash_commands.SlashCommand):
	description = "Fetch your or provided member's Coins balance."

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

	member : Optional[hikari.User] = Option(description = "The member to fetch coins of", required = False)

	async def callback(self, ctx : slash_commands.SlashCommandContext) -> None:
		target = ctx.options.member

		if target is None:
			target = ctx.get_guild().get_member(ctx.author)
		else:
			target = ctx.get_guild().get_member(target)
		
		await ctx.respond(response_type = hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
		
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		target_coins = c.execute("SELECT points FROM point_table WHERE user_ID = {};".format(target.id)).fetchone()
		if target_coins is None:
			target_coins = 0
			c.execute("INSERT INTO point_table VALUES (NULL, {}, {});".format(target.id, target_coins))
			conn.commit()
			conn.close()
		else:
			target_coins = target_coins[0]
		
		embed = hikari.Embed(
			title = f"User {target.display_name}'s Coins",
			description = f"{target.display_name} has {target_coins} since reset.",
			colour = random.randint(0, 0xffffff)
		)
		await ctx.edit_response(embed = embed)

class Leaderboard(slash_commands.SlashCommand):
	description = "See the Coins leaderboard with top 20 members."

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

	async def callback(self, ctx : slash_commands.SlashCommandContext) -> None:
		await ctx.respond(response_type = hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		DB = c.execute('SELECT user_ID, points FROM point_table;').fetchall()
		conn.close()

		total_coins = dict(DB)

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
		
		await ctx.edit_response(embed = embed)

def load(bot : Bot) -> None:
	bot.add_plugin(Points(bot))
	bot.add_slash_command(Coins, create=True)
	bot.add_slash_command(Leaderboard, create=True)
	print("Plugin Points has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Points")
