import hikari
import lightbulb
import sqlite3
import random
import asyncio
from datetime import datetime
from datetime import date
from lightbulb.command_handler import Bot
from pytz import timezone as tz

with open("./Secrets/token") as f:
	token = f.read().strip()

POINT = {}

conn = sqlite3.connect('Database.db')
c = conn.cursor()

c.execute("SELECT channel_ID FROM channel_table WHERE title='LOG';")
LOGCHANNELID = c.fetchone()
c.execute("SELECT channel_ID FROM channel_table WHERE title='POINT';")
POINTCMDCHANNELID = c.fetchone()
c.execute("SELECT channel_ID FROM channel_table WHERE title='RULE';")
RULECHANNELID = c.fetchone()
c.execute("SELECT channel_ID FROM channel_table WHERE title='POINT-EARN-CHANNEL';")
POINT_EARN_CHNLS = c.fetchall()
c.execute("SELECT user_id, points FROM point_table;")
DB_POINT = c.fetchall()

c.execute("SELECT role_ID FROM role_table WHERE title = 'STUDYBUDDIES';")
STUDYBUDDIES = c.fetchone()

StudyBuddiesRoleID : int = int(STUDYBUDDIES[0])

LOGCHANNELID : int = int(LOGCHANNELID[0])
POINTCMDCHANNELID = int(POINTCMDCHANNELID[0])
RULECHANNELID = int(RULECHANNELID[0])
STUDYTOGETHERCHANNELID = int(770940461337804810)

conn.close()

def loading_embed() -> hikari.Embed:
	loading_embed = hikari.Embed(description = "Loading...")
	return loading_embed

# Custom check to see if the command is run in the Point command channel
async def is_point_cmd_chnl(ctx : lightbulb.Context) -> bool:
	return int(ctx.channel_id) == int(POINTCMDCHANNELID)

async def is_point_chnl(channel_id) -> bool:
	for chnl in POINT_EARN_CHNLS:
		if int(chnl[0]) == int(channel_id):
			return True
	return False

async def is_study_channel(ctx : lightbulb.Context) -> bool:
	return int(ctx.channel_id) == STUDYTOGETHERCHANNELID

# Logging Command
async def command_log(bot : lightbulb.Bot, ctx : lightbulb.Context, cmdName : str):
	LogEmbed = hikari.Embed(
		title = "SleepBot Command Logs",
		color = random.randint(0, 0xffffff)
	).add_field(
		name = "Command",
		value = f"{cmdName}"
	).add_field(
		name = "Message Content:",
		value = f"{ctx.message.content}"
	).add_field(
		name = "Author :", 
		value = f"{ctx.author}, **ID** : {ctx.author.id}, **Nick** : {ctx.message.member.nickname}", 
		inline = False
	).add_field(
		name = "Channel :",
		value = f"{ctx.get_channel()}, **Channel ID** : {ctx.channel_id}",
		inline = False
	).add_field(
		name = "Time :",
		value = f"{datetime.now().astimezone(tz('Asia/Kolkata'))}",
		inline = False
	)

	await bot.rest.create_message(LOGCHANNELID, embed = LogEmbed)

"""
async def Backup(bot : Bot):
	global POINT
	global DB_POINT
	while bot.is_alive:
		await bot.rest.create_message(int(LOGCHANNELID), f"Backup OK: ```{datetime.now()}```")
		await asyncio.sleep(300)
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()

		c.execute("SELECT user_id, points FROM point_table;")
		DB_POINT = c.fetchall()

		await bot.rest.create_message(int(LOGCHANNELID), f"Performing Backup: ```{datetime.now()}```")

		for user in DB_POINT:
			if user[0] in POINT:
				c.execute("UPDATE point_table SET points = {} WHERE user_id = {}".format(POINT[user[0]] + user[1], user[0]))
		is_instance = False
		for user in POINT:
			for elm in DB_POINT:
				if user in elm:
					is_instance = True
					break
				if not is_instance:
					c.execute("INSERT INTO point_table VALUES (NULL, {}, {});".format(user, POINT[user]))
				is_instance = False
		
		c.execute("SELECT user_ID, points FROM point_table;")
		DB_POINT = c.fetchall()

		conn.commit()
		conn.close()

		POINT = {}


This one is the old one btw
async def Backup(client):
	await client.wait_until_ready()
	global POINT
	global DB_POINT
	while not client.is_closed():
		await client.get_channel(LOGCHANNELID).send(f"Backup OK: ```{datetime.now()}```")
		# Repeat every 1 hour
		await asyncio.sleep(1800)
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()

		c.execute("SELECT user_id, points FROM point_table;")
		DB_POINT = c.fetchall()

		await client.get_channel(int(LOGCHANNELID)).send(f"Performing Backup: ```{datetime.now()}```")
		# POINT BACKUP
		for user in DB_POINT:
			if user[0] in POINT:
				c.execute("UPDATE point_table SET points = {} WHERE user_ID = {}".format(POINT[user[0]]+user[1],user[0]))
		is_instance = False
		for user in POINT:
			for elm in DB_POINT:
				if user in elm:
					is_instance = True
					break
			if not is_instance:
				c.execute("INSERT INTO point_table VALUES (NULL, {}, {});".format(user,POINT[user]))
			is_instance = False
		
		c.execute("SELECT user_ID, points FROM point_table;")
		DB_POINT = c.fetchall()

		conn.commit()
		conn.close()

		POINT = {}
"""