import hikari
import lightbulb
import sqlite3
import random
from datetime import datetime
from datetime import date
from pytz import timezone as tz

with open("./Secrets/token") as f:
	token = f.read().strip()

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("SELECT channel_ID FROM channel_table WHERE title='LOG';")
LOGCHANNELID = c.fetchone()
c.execute("SELECT channel_ID FROM channel_table WHERE title='POINT';")
POINTCMDCHANNELID = c.fetchone()
c.execute("SELECT channel_ID FROM channel_table WHERE title='RULE';")
RULECHANNELID = c.fetchone()
c.execute("SELECT channel_ID FROM channel_table WHERE title='POINT-EARN-CHANNEL';")
POINT_EARN_CHNLS = c.fetchall()

LOGCHANNELID = int(LOGCHANNELID[0])
POINTCMDCHANNELID = int(POINTCMDCHANNELID[0])
RULECHANNELID = int(RULECHANNELID[0])
STUDYTOGETHERCHANNELID = 886311520592617542

conn.close()

def loading_embed() -> hikari.Embed:
	loading_embed = hikari.Embed(description = "Loading...")
	return loading_embed

# Custom check to see if the command is run in the Point command channel
async def is_point_cmd_chnl(ctx : lightbulb.Context) -> bool:
	return int(ctx.channel_id) == int(POINTCMDCHANNELID)

async def is_point_chnl(ctx : lightbulb.Context) -> bool:
	for chnl in POINT_EARN_CHNLS:
		if int(chnl[0]) == int(ctx.channel_id):
			return True
	return False

async def is_study_channel(ctx : lightbulb.Context) -> bool:
	return int(ctx.channel_id) == STUDYTOGETHERCHANNELID

# Logging Command
async def command_log(bot : lightbulb.Bot, ctx : lightbulb.Context, cmdName : str):
	LogEmbed = hikari.Embed(
		title = "Sleep Command Logs",
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
