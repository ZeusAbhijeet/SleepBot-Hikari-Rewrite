import asyncio
import hikari
import lightbulb
import aiohttp
import aiosqlite
import Utils
import motor.motor_asyncio

from random import randint
from lightbulb import context, commands
from Utils import NOXPCHANNEL, XPMUTEDROLEID, MAXXP, MINXP, XPTIMEOUT
from hikari.files import Bytes
from typing import Optional

with open("./Secrets/mongourl") as f:
	MongoURL = f.read().strip()

with open("./Secrets/key") as f:
	APIKey = f.read().strip()

"""
cluster = MongoClient(MongoURL)
levelling = cluster['bluelearn']['levelling']
"""

cluster = motor.motor_asyncio.AsyncIOMotorClient(MongoURL)
db = cluster.bluelearn
levelling = db.levelling

level_plugin = lightbulb.Plugin("Levelling")

brake = []
role_levels = [5, 10, 20, 40, 60, 80, 100]

async def RankCardGen(member : hikari.Member, level : int, current_xp : int, next_xp : int, rank : int, bg : Optional[str], xp_bar : Optional[str]) -> bytes:
	async with aiohttp.ClientSession() as rankCardSession:
		member_avatar = member.avatar_url if member.avatar_url is not None else member.default_avatar_url
		username = member.username
		discriminator = member.discriminator
		background = bg
		async with rankCardSession.get(
				f"https://some-random-api.ml/premium/rankcard/1?key={APIKey}&username={username}&discriminator={discriminator}&avatar={member_avatar}&cxp={int(current_xp)}&nxp={int(next_xp)}&level={level}&rank={rank}&ccxp={xp_bar}&bg={background}"
		) as RankCardImg:
			rankcard = await RankCardImg.read()
			await rankCardSession.close()
			return rankcard

@level_plugin.command
@lightbulb.command("rank", "All level related commands", aliases = ['level'], auto_defer = True)
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def rankcmdgroup(ctx : context.Context) -> None:
	pass

@rankcmdgroup.child
@lightbulb.option("user", "User to fetch rank card of", type = hikari.User, required = False)
@lightbulb.command("card", "Fetch a card with all your level and rank details", auto_defer = True, inherit_checks = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def rankcardcmd(ctx : context.Context) -> None:
	target = ctx.options.user if ctx.options.user is not None else ctx.user
	target = ctx.get_guild().get_member(target)

	if XPMUTEDROLEID in target.role_ids:
		return await ctx.respond(f":warning: You have been XP Muted. Hence I cannot show you your rank details.", flags = hikari.MessageFlag.EPHEMERAL)
	
	MemberData = await levelling.find_one({"user_ID" : target.id})
	if not MemberData:
		return await ctx.respond(f"You have no rank. Keep chatting to gain XP", flags = hikari.MessageFlag.EPHEMERAL)
	
	xp : int = MemberData['xp']
	lvl = 0
	rank = 0
	while True:
		if xp < ((300 / 2 * (lvl ** 2)) + (300 / 2 * lvl)):
			break
		lvl += 1
	xp -= ((300 / 2 * (lvl - 1) ** 2) + (300 / 2 * (lvl - 1)))

	rankings = levelling.find().sort("xp", -1)
	async for x in rankings:
		rank += 1
		if MemberData['user_ID'] == x['user_ID']:
			break
	
	rankcard = await RankCardGen(
		member = target,
		level = lvl,
		current_xp = int(xp),
		next_xp = int(300 * 2 * ((1 / 2) * lvl)),
		rank = rank,
		bg = MemberData['background'],
		xp_bar = MemberData['xp_colour']
	)
	await ctx.respond(attachment = Bytes(rankcard, "rank_card.png"), reply = True)

@rankcmdgroup.child
@lightbulb.command("leaderboard", "Shows the top 12 active members by XP of the server", aliases = ['lb'], auto_defer = True, inherit_checks = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def ranklbcmd(ctx : context.Context) -> None:
	rankings = levelling.find({}).sort("xp", -1).limit(15)
	rank = 1
	
	RankEmbed = hikari.Embed(
		title = "Level Leaderboard",
		description = "Here are the top 10 active members.",
		colour = randint(0, 0xffffff)
	)
	async for r in rankings:
		if rank > 12:
			break
		try:
			member = ctx.get_guild().get_member(r['user_ID'])
			if not member:
				continue
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

@level_plugin.command
@lightbulb.command("setconfig", description = "Set your levelling configs", auto_defer = True)
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def setconfiggroup(ctx : context.Context) -> None:
	pass

@setconfiggroup.child
@lightbulb.option("url", "Direct URL of the background image", type = str, required = False)
@lightbulb.command("background", "Set your rankcard's background", aliases = ['bg'])
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def setbackgroundcmd(ctx : context.Context) -> None:
	url = ctx.options.url
	MemberData = await levelling.find_one(
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
			await levelling.update_one(
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
			await levelling.update_one(
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
			await levelling.insert_one(
				{
					"user_ID" : ctx.author.id,
					"xp" : 0,
					"background" : "",
					"xp_colour" : "1483e3"
				}
			)
			return await ctx.respond("Please provide a url.")
		else:
			await levelling.insert_one(
				{
					"user_ID" : ctx.author.id,
					"xp" : 0,
					"background" : url,
					"xp_colour" : "1483e3"
				}
			)
	await ctx.respond(f"Your rank card background has been set to {url}", reply = True)

@setconfiggroup.child
@lightbulb.option("hex", "HEX code of the colour", type = str, required = False)
@lightbulb.command("xpcolour", "Set your xp bar's colour", aliases = ['xpcolor', 'xp'])
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def setxpcolourcmd(ctx : context.Context) -> None:
	hex = ctx.options.hex
	MemberData = await levelling.find_one(
		{
			"user_ID" : ctx.author.id
		}
	)
	if MemberData:
		if hex is None:
			await levelling.update_one(
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
			await levelling.update_one(
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
			await levelling.insert_one(
				{
					"user_ID" : ctx.author.id,
					"xp" : 0,
					"background" : "",
					"xp_colour" : "1483e3"
				}
			)
			return await ctx.respond("Please provide a hex colour.")
		else:
			await levelling.insert_one(
				{
					"user_ID" : ctx.author.id,
					"xp" : 0,
					"background" : "",
					"xp_colour" : hex
				}
			)
	await ctx.respond(f"Your rank card xp colour has been set to {hex}")	

@setconfiggroup.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("settings", "Set some settings for levelling", hidden = True)
@lightbulb.implements(commands.PrefixSubGroup, commands.SlashSubGroup)
async def settingssubgroup(ctx : context.Context) -> None:
	pass

@settingssubgroup.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("channel", description = "The channel to set as a no XP channel", type = hikari.GuildChannel, required = False)
@lightbulb.command(name = "noxpchannel", description = "Add a channel as a No XP channel", hidden = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def noxpchannel(ctx : context.Context) -> None:
	channel : hikari.GuildChannel = ctx.options.channel
	
	if channel is None:
		des : list = []
		for c in NOXPCHANNEL:
			des.append(f"<#{c}>")
		await ctx.respond(
			embed = hikari.Embed(
				title = "Currently Set XP Channels:",
				description = ", ".join(des),
				colour = randint(0, 0xffffff)
			),
			flags = hikari.MessageFlag.EPHEMERAL
		)
		return
	
	conn = await aiosqlite.connect('Database.db')
	c = await conn.cursor()
	await c.execute(f"INSERT INTO channel_table VALUES (NULL, 'NONLEVELCHANNEL', {channel.id});")
	await conn.commit()
	await conn.close()
	NOXPCHANNEL.append(channel.id)
	
	await ctx.respond(
		embed = hikari.Embed(
			title = "Set No XP Channel",
			description = f"Set <#{channel.id}> as a No XP Channel.",
			colour = randint(0, 0xffffff)
		),
		reply = True
	)

@settingssubgroup.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("xp", "The amount XP to set as Max", type = int, required = False)
@lightbulb.command("maxxp", description = "Set the maximum amount of XP someone can get", auto_defer = True, hidden = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def setmaxxp(ctx : context.Context) -> None:
	xp : int = ctx.options.xp

	if xp is None:
		await ctx.respond(
			embed = hikari.Embed(
				title = "Current Set Max and Min XP",
				description = f"**Max XP :** {MAXXP} \n**Min XP :** {MINXP}",
				colour = randint(0, 0xffffff)
			),
			flags = hikari.MessageFlag.EPHEMERAL
		)
		return
	
	conn = await aiosqlite.connect('Database.db')
	c = await conn.cursor()
	await c.execute(f"UPDATE general_table SET info = {xp} WHERE title = 'MAXXP';")
	await conn.commit()
	await conn.close()
	Utils.MAXXP = xp
	await ctx.respond(
		embed = hikari.Embed(
			title = "Set Max XP",
			description = f"Set Max XP to {xp}.",
			colour = randint(0, 0xffffff)
		)
	)

@settingssubgroup.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("xp", "The amount XP to set as Max", type = int, required = False)
@lightbulb.command("minxp", description = "Set the minimum amount of XP someone can get", auto_defer = True, hidden = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def setminxp(ctx : context.Context) -> None:
	xp : int = ctx.options.xp

	if xp is None:
		await ctx.respond(
			embed = hikari.Embed(
				title = "Current Set Max and Min XP",
				description = f"**Max XP :** {MAXXP} \n**Min XP :** {MINXP}",
				colour = randint(0, 0xffffff)
			),
			flags = hikari.MessageFlag.EPHEMERAL
		)
		return
	
	conn = await aiosqlite.connect('Database.db')
	c = await conn.cursor()
	await c.execute(f"UPDATE general_table SET info = {xp} WHERE title = 'MINXP';")
	await conn.commit()
	await conn.close()
	Utils.MINXP = xp
	await ctx.respond(
		embed = hikari.Embed(
			title = "Set Min XP",
			description = f"Set Min XP to {xp}.",
			colour = randint(0, 0xffffff)
		),
		flags = hikari.MessageFlag.EPHEMERAL
	)


@level_plugin.listener(hikari.MessageCreateEvent)
async def on_message_create(event : hikari.MessageCreateEvent) -> None:
	global brake, role_levels
	if event.channel_id in NOXPCHANNEL:
		return
	if not event.author.is_bot:
		if event.author_id in brake:
			return
		
		conn = await aiosqlite.connect('Database.db')
		c = await conn.cursor()
		member = await event.app.rest.fetch_member(event.message.guild_id, event.author_id)
		if XPMUTEDROLEID in member.role_ids:
			return
		AssignXP = randint(int(MINXP), int(MAXXP))
		MemberData = await levelling.find_one({"user_ID" : event.author_id})
		if not MemberData:
			await levelling.insert_one(
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
			await levelling.update_one(
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
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL5';")
				LevelRoleID = await cursor.fetchone()
			elif Afterlvl >= 10 and Afterlvl < 20:
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL10';")
				LevelRoleID = await cursor.fetchone()
			elif Afterlvl >= 20 and Afterlvl < 40:
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL20';")
				LevelRoleID = await cursor.fetchone()
			elif Afterlvl >= 40 and Afterlvl < 60:
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL40';")
				LevelRoleID = await cursor.fetchone()
			elif Afterlvl >= 60 and Afterlvl < 80:
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL60';")
				LevelRoleID = await cursor.fetchone()
			elif Afterlvl >= 80 and Afterlvl < 100:
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL80';")
				LevelRoleID = await cursor.fetchone()
			elif Afterlvl >= 100:
				cursor = await c.execute("SELECT role_ID FROM role_table WHERE title = 'LEVEL100';")
				LevelRoleID = await cursor.fetchone()
			else:
				LevelRoleID = None

			if LevelRoleID:
				await member.add_role(role = LevelRoleID[0], reason = "Level Up Reward")

			embed = hikari.Embed(
				title = "Level Up!",
				description = f"{event.author.mention} has leveled up to level {Afterlvl}!" if Afterlvl not in role_levels else f"{event.author.mention} has leveled up to level {Afterlvl} and has received <@&{LevelRoleID[0]}>",
				colour = randint(0, 0xffffff)
			)

			await event.app.rest.create_message(
				channel = event.channel_id,
				embed = embed
			)
			
		await conn.close()

		brake.append(event.author_id)
		await asyncio.sleep(int(XPTIMEOUT))
		brake.remove(event.author_id)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(level_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(level_plugin)
