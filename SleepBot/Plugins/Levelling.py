import asyncio
from typing import Iterable, Optional
import hikari
from hikari.embeds import Embed
from hikari.files import Bytes
from hikari.guilds import Member
import lightbulb
from lightbulb import slash_commands
from lightbulb.command_handler import Bot
from lightbulb.slash_commands.commands import Option
from pymongo import MongoClient
import vacefron
import sqlite3
import random
import Utils
from Utils import NOXPCHANNEL, XPMUTEDROLEID

from __init__ import GUILD_ID

with open("./Secrets/mongourl") as f:
	MongoURL = f.read().strip()

cluster = MongoClient(MongoURL)
levelling = cluster['bluelearn']['levelling']


vac_api = vacefron.Client()

class Levelling(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		self.brake = []
		self.role_levels = [5, 10, 20, 40, 60, 80, 100]
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		c.execute("SELECT info FROM general_table WHERE title = 'MAXXP';")
		MAXXP = c.fetchone()
		c.execute("SELECT info FROM general_table WHERE title = 'MINXP';")
		MINXP = c.fetchone()
		c.execute("SELECT info FROM general_table WHERE title = 'XPTIMEOUT';")
		XPTIMEOUT = c.fetchone()

		self.MAXXP : int = MAXXP[0]
		self.MINXP : int = MINXP[0]
		self.XPTIMEOUT : int = XPTIMEOUT[0]

		conn.close()
		super().__init__()
	
	@lightbulb.command(name = "rankcard", aliases = ['rank'])
	async def rankcard(self, ctx : lightbulb.Context, member : hikari.Member = None):
		"Shows your activity level, xp and rank."
		if member is None:
			member = ctx.get_guild().get_member(ctx.author)
		msg = await ctx.respond("Fetching XP and level details...", reply = True)
		
		if XPMUTEDROLEID in member.role_ids:
			return await msg.edit(f"You have been XP Muted. Hence I cannot show you your rank.")
		
		MemberData = levelling.find_one(
			{
				"user_ID" : member.id
			}
		)
		if not MemberData:
			return await msg.edit("You have no rank. Keep chatting to gain XP.")

		xp : int = MemberData['xp']
		lvl = 0
		rank = 0
		while True:
			if xp < ((300 / 2 * (lvl ** 2)) + (300 / 2 * lvl)):
				break
			lvl += 1
		xp -= ((300 / 2 * (lvl - 1) ** 2) + (300 / 2 * (lvl - 1)))

		#rankings = c.execute(f"SELECT user_ID, xp FROM level_table;").fetchall()
		rankings = levelling.find().sort("xp", -1)
		for x in rankings:
			rank += 1
			if MemberData['user_ID'] == x['user_ID']:
				break

		card = await vac_api.rank_card(
			username = member,
			avatar = member.avatar_url,
			level = lvl,
			rank = rank,
			current_xp = xp,
			next_level_xp = int(300 * 2 * ((1 / 2) * lvl)),
			previous_level_xp = 0,
			circle_avatar = False,
			custom_background = MemberData['background'],
			xp_color = f"#{MemberData['xp_colour']}",
			is_boosting = (True if member.premium_since is not None else False)
		)
		rankcard = await card.read(bytesio=False)
		#await msg.delete()
		await msg.edit(content = "", attachment = Bytes(rankcard, "rank_card.png"))
	
	@lightbulb.command(name = 'ranklb', aliases = ['levellb'])
	async def ranklb(self, ctx : lightbulb.Context):
		"Shows the top 10 members of the server"
		rankings = levelling.find({}).sort("xp", -1)
		rank = 1
		
		RankEmbed = Embed(
			title = "Level Leaderboard",
			description = "Here are the top 10 active members.",
			colour = random.randint(0, 0xffffff)
		)
		for r in rankings:
			if rank > 12:
				break
			try:
				member = ctx.get_guild().get_member(r['user_ID'])
			except:
				continue
			if member.is_bot:
				continue
			xp : int = r['xp']
			lvl = 0
			while True:
				if xp < ((300 / 2 * (lvl ** 2)) + (300 / 2 * lvl)):
					break
				lvl += 1
			
			RankEmbed.add_field(
				name = f"{rank}. {member.display_name}",
				value = f"Level : {lvl}\nXP : {xp}",
				inline = True
			)
			rank = rank + 1
		
		await ctx.respond(embed = RankEmbed, reply = True)

	@lightbulb.command(name = 'setbackground', aliases = ['setbg'])
	async def set_background(self, ctx : lightbulb.Context, url : str = None) -> None:
		"Sets your rank card background"
		MemberData = levelling.find_one(
			{
				"user_ID" : ctx.author.id
			}
		)
		if MemberData:
			Existing_BG = MemberData['background']
			if Existing_BG == "":
				if url is None:
					return await ctx.respond("You have no background set.")
			if url is None:
				levelling.update_one(
					{
						'user_ID' : ctx.author.id
					},
					{
						'$set' : {
							'background' : ""
						}
					}
				)
			else:
				levelling.update_one(
					{
						'user_ID' : ctx.author.id
					},
					{
						'$set' : {
							'background' : url
						}
					}
				)
		else:
			if url is None:
				levelling.insert_one(
					{
						"user_ID" : ctx.author.id,
						"xp" : 0,
						"background" : "",
						"xp_colour" : "1483e3"
					}
				)
				return await ctx.respond("Please provide a url.")
			else:
				levelling.insert_one(
					{
						"user_ID" : ctx.author.id,
						"xp" : 0,
						"background" : url,
						"xp_colour" : "1483e3"
					}
				)
		await ctx.respond(f"Your rank card background has been set to {url}")
	
	@lightbulb.command(name = 'setxpcolour', aliases = ['setcolour', 'setxpcolor', 'setcolor'])
	async def set_xp_colour(self, ctx : lightbulb.Context, hex : str = None) -> None:
		"Sets your rank card XP colour"
		MemberData = levelling.find_one(
			{
				"user_ID" : ctx.author.id
			}
		)
		if MemberData:
			Existing_colour = MemberData['xp_colour']
			if hex is None:
				levelling.update_one(
					{
						'user_ID' : ctx.author.id
					},
					{
						'$set' : {
							'xp_xolour' : "1483e3"
						}
					}
				)
			else:
				levelling.update_one(
					{
						'user_ID' : ctx.author.id
					},
					{
						'$set' : {
							'xp_colour' : hex
						}
					}
				)
		else:
			if hex is None:
				levelling.insert_one(
					{
						"user_ID" : ctx.author.id,
						"xp" : 0,
						"background" : "",
						"xp_colour" : "1483e3"
					}
				)
				return await ctx.respond("Please provide a hex colour.")
			else:
				levelling.insert_one(
					{
						"user_ID" : ctx.author.id,
						"xp" : 0,
						"background" : "",
						"xp_colour" : hex
					}
				)
		await ctx.respond(f"Your rank card xp colour has been set to {hex}")	
	
	@lightbulb.check(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
	@lightbulb.command(name = 'setnoxpchannel', aliases = ['setblacklistchannel'])
	async def set_no_xp_channel(self, ctx : lightbulb.Context, channel : hikari.TextableChannel) -> None:
		await Utils.command_log(self.bot, ctx, "setnoxpchannel")
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		c.execute(f"INSERT INTO channel_table VALUES (NULL, 'NONLEVELCHANNEL', {channel.id});")
		conn.commit()
		conn.close()
		await ctx.respond(
			embed = Embed(
				title = "Set No XP Channel",
				description = f"Set <#{channel.id}> as a No XP Channel.",
				colour = random.randint(0, 0xffffff)
			)
		)
	
	@lightbulb.listener(hikari.MessageCreateEvent)
	async def on_message_create(self, event : hikari.MessageCreateEvent) -> None:
		if event.channel_id in NOXPCHANNEL:
			return
		if not event.author.is_bot:
			if event.author_id in self.brake:
				return
			
			conn = sqlite3.connect('Database.db')
			c = conn.cursor()
			member = await self.bot.rest.fetch_member(event.message.guild_id, event.author_id)
			if XPMUTEDROLEID in member.role_ids:
				return
			AssignXP = random.randint(int(self.MINXP), int(self.MAXXP))
			MemberData = levelling.find_one({"user_ID" : event.author_id})
			if not MemberData:
				levelling.insert_one(
					{
						"user_ID" : event.author_id,
						"xp" : AssignXP,
						"background" : "",
						"xp_colour" : "1483e3"
					}
				)
				BeforeXP = AssignXP
			else:
				AssignXP += MemberData['xp']
				BeforeXP = MemberData['xp']
				levelling.update_one(
					{
						'user_ID' : event.author_id
					},
					{
						'$set' : {
							"xp" : AssignXP
						}
					}
				)
				
			
			Beforelvl = 0
			while True:
				if BeforeXP < ((300 / 2 * (Beforelvl ** 2)) + (300 / 2 * Beforelvl)):
					break
				Beforelvl += 1
			BeforeXP -= ((300 / 2 * (Beforelvl - 1) ** 2) + (300 / 2 * (Beforelvl - 1)))

			Afterxp : int = AssignXP
			Afterlvl = 0
			while True:
				if Afterxp < ((300 / 2 * (Afterlvl ** 2)) + (300 / 2 * Afterlvl)):
					break
				Afterlvl += 1
			Afterxp -= ((300 / 2 * (Afterlvl - 1) ** 2) + (300 / 2 * (Afterlvl - 1)))

			if Beforelvl != Afterlvl:
				LevelRoleID : tuple
				if Afterlvl >= 5 and Afterlvl < 10:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL5';").fetchone()
				elif Afterlvl >= 10 and Afterlvl < 20:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL10';").fetchone()
				elif Afterlvl >= 20 and Afterlvl < 40:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL20';").fetchone()
				elif Afterlvl >= 40 and Afterlvl < 60:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL40';").fetchone()
				elif Afterlvl >= 60 and Afterlvl < 80:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL60';").fetchone()
				elif Afterlvl >= 80 and Afterlvl < 100:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL80';").fetchone()
				elif Afterlvl >= 100:
					LevelRoleID = c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL100';").fetchone()

				if LevelRoleID:
					await member.add_role(role = LevelRoleID[0], reason = "Level Up Reward")

				embed = Embed(
					title = "Level Up!",
					description = f"{event.author.mention} has leveled up to level {Afterlvl}!" if Afterlvl not in self.role_levels else f"{event.author.mention} has leveled up to level {Afterlvl} and has received <@&{LevelRoleID[0]}>",
					colour = random.randint(0, 0xffffff)
				)

				await self.bot.rest.create_message(
					channel = event.channel_id,
					embed = embed
				)
			
			conn.close()

			self.brake.append(event.author_id)
			await asyncio.sleep(int(self.XPTIMEOUT))
			self.brake.remove(event.author_id)

class Level(slash_commands.SlashCommand):
	description = "Shows your activity level, rank and XP points."

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

	member : Optional[hikari.User] = Option(description = "The member to check level of.", required = False)

	async def callback(self, ctx: lightbulb.SlashCommandContext) -> None:
		target = ctx.options.member

		if target is None:
			member = ctx.get_guild().get_member(ctx.author)
		else:
			member = ctx.get_guild().get_member(target)
		
		await ctx.respond(response_type = hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
		
		if XPMUTEDROLEID in member.role_ids:
			return await ctx.edit_response(f"You have been XP Muted. Hence I cannot show you your rank.")

		MemberData = levelling.find_one(
			{
				"user_ID" : member.id
			}
		)
		if not MemberData:
			return await ctx.edit_response("You have no rank. Keep chatting to gain XP.")

		xp : int = MemberData['xp']
		lvl = 0
		rank = 0
		while True:
			if xp < ((300 / 2 * (lvl ** 2)) + (300 / 2 * lvl)):
				break
			lvl += 1
		xp -= ((300 / 2 * (lvl - 1) ** 2) + (300 / 2 * (lvl - 1)))

		rankings = levelling.find().sort("xp", -1)
		for x in rankings:
			rank += 1
			if MemberData['user_ID'] == x['user_ID']:
				break

		card = await vac_api.rank_card(
			username = member,
			avatar = member.avatar_url,
			level = lvl,
			rank = rank,
			current_xp = xp,
			next_level_xp = int(300 * 2 * ((1 / 2) * lvl)),
			previous_level_xp = 0,
			circle_avatar = False,
			custom_background = MemberData['background'],
			xp_color = f"#{MemberData['xp_colour']}",
			is_boosting = (True if member.premium_since is not None else False)
		)
		rankcard = await card.read(bytesio=False)
		await ctx.edit_response(attachment = Bytes(rankcard, "rank_card.png"))

class Level_Leaderboard(slash_commands.SlashCommand):
	description = "Shows the top 12 members of the server"

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

	async def callback(self, ctx : lightbulb.SlashCommandContext):
		await ctx.respond(response_type = hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

		rankings = levelling.find({}).sort("xp", -1)
		rank = 1
		
		RankEmbed = Embed(
			title = "Level Leaderboard",
			description = "Here are the top 10 active members.",
			colour = random.randint(0, 0xffffff)
		)
		for r in rankings:
			if rank > 12:
				break
			try:
				member = ctx.get_guild().get_member(r['user_ID'])
			except:
				continue
			if member.is_bot:
				continue
			xp : int = r['xp']
			lvl = 0
			while True:
				if xp < ((300 / 2 * (lvl ** 2)) + (300 / 2 * lvl)):
					break
				lvl += 1
			
			RankEmbed.add_field(
				name = f"{rank}. {member.display_name}",
				value = f"Level : {lvl}\nXP : {xp}",
				inline = True
			)
			rank = rank + 1
		
		await ctx.edit_response(embed = RankEmbed)

def load(bot : Bot) -> None:
	bot.add_plugin(Levelling(bot))
	bot.add_slash_command(Level, create = True)
	bot.add_slash_command(Level_Leaderboard, create = True)
	print("Plugin Levelling has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Levelling")

