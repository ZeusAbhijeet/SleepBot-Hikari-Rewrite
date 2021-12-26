import hikari
import lightbulb
import sqlite3
import random
import asyncio
from datetime import datetime
from datetime import date
from pytz import timezone as tz
from lightbulb import context

with open("./Secrets/token") as f:
	token = f.read().strip()

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
c.execute("SELECT channel_ID FROM channel_table WHERE title='NONLEVELCHANNEL';")
NOXPCHANNELTUPLE = c.fetchall()
StudyVCIDTuple = c.execute(f"SELECT channel_ID FROM channel_table WHERE title = 'STUDYVC';").fetchall()

c.execute("SELECT role_ID FROM role_table WHERE title = 'STUDYBUDDIES';")
STUDYBUDDIES = c.fetchone()
c.execute("SELECT role_ID FROM role_table WHERE title = 'STAFF';")
STAFF = c.fetchone()
c.execute("SELECT role_ID FROM role_table WHERE title = 'XPMUTED'")
XPMUTED = c.fetchone()
FocusChannelID = c.execute(f"SELECT channel_ID FROM channel_table WHERE title = 'FOCUS';").fetchone()
c.execute("SELECT info FROM general_table WHERE title = 'MAXXP';")
MAX_XP = c.fetchone()
c.execute("SELECT info FROM general_table WHERE title = 'MINXP';")
MIN_XP = c.fetchone()
c.execute("SELECT info FROM general_table WHERE title = 'XPTIMEOUT';")
XP_TIMEOUT = c.fetchone()

StudyBuddiesRoleID : int = int(STUDYBUDDIES[0])
StaffRoleID : int = int(STAFF[0])
LOGCHANNELID : int = int(LOGCHANNELID[0])
XPMUTEDROLEID : int = int(XPMUTED[0])

POINTCMDCHANNELID = int(POINTCMDCHANNELID[0])
RULECHANNELID = int(RULECHANNELID[0])
STUDYTOGETHERCHANNELID = int(770940461337804810)
FocusChannelID = FocusChannelID[0]

MAXXP : int = MAX_XP[0]
MINXP : int = MIN_XP[0]
XPTIMEOUT : int = XP_TIMEOUT[0]

NOXPCHANNEL : list = []
StudyVCIDs : list = []

for XP in NOXPCHANNELTUPLE:
	NOXPCHANNEL.append(XP[0])
for id in StudyVCIDTuple:
	StudyVCIDs.append(id[0])

conn.close()

def loading_embed(loading_text : str = None) -> hikari.Embed:
	loading_embed = hikari.Embed(description = "Loading..." if loading_text is None else loading_text)
	return loading_embed

# Custom check to see if the command is run in the Point command channel
async def is_point_cmd_chnl(ctx : context.Context) -> bool:
	return int(ctx.channel_id) == int(POINTCMDCHANNELID)

async def is_point_chnl(channel_id) -> bool:
	for chnl in POINT_EARN_CHNLS:
		if int(chnl[0]) == int(channel_id):
			return True
	return False

async def is_study_channel(ctx : lightbulb.context.Context) -> bool:
	return int(ctx.channel_id) == STUDYTOGETHERCHANNELID

# Logging Command
async def command_log(bot : lightbulb.BotApp, ctx : lightbulb.context.Context, cmdName : str):
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
