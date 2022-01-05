import hikari
import lightbulb
import Utils
import asyncio
import time
import motor.motor_asyncio

from hikari.voices import VoiceState
from random import randint
from lightbulb import commands, context
from pymongo import MongoClient
from Utils import StaffRoleID, StudyVCIDs, FocusChannelID
from typing import List, Optional
from datetime import datetime
from __init__ import GUILD_ID

GUILD_ID = GUILD_ID[0]

with open("./Secrets/studystreakmongourl") as f:
	MongoURL = f.read().strip()

"""
cluster = MongoClient(MongoURL)
membertime = cluster['bluelearn']['membertime']
"""

cluster = motor.motor_asyncio.AsyncIOMotorClient(MongoURL)
db : motor.motor_asyncio.AsyncIOMotorDatabase = cluster.bluelearn
membertime : motor.motor_asyncio.AsyncIOMotorCollection = db.membertime


TIMER_UPDATE_INTERVAL = 1 # minutes
KICK_STALKERS_AFTER = 45 # seconds

CAMS_ON_VC = 770670934565715998
STUDYVC1 = 818011398231687178

STUDYING_ROLE = 816873155246817290

app : lightbulb.BotApp

# /---------------------------------------------------------/
# /    All important functions to help me manage the data   /
# /	   And also to reset some stats							/
# /---------------------------------------------------------/


def MinutesToHours(mins : int):
	hours = int(mins / 60)
	minutes = mins % 60
	return hours, minutes

async def add_member_to_db(userID : int) -> None:
	await membertime.insert_one(
		{
			"user_ID" : userID,
			"total" : 0,
			"daily" : 0,
			"yesterday" : 0,
			"weekly" : 0,
			"monthly" : 0,
			"stream" : 0,
			"video" : 0,
			"streak" : 0
		}
	)

async def update_time(userID : int, times = ("total", "daily", "weekly", "monthly")) -> None:
	member_info = await membertime.find_one({"user_ID" : userID})
	if not member_info:
		await add_member_to_db(userID)
		return
	for time in times:
		await membertime.update_one(
			{"user_ID" : userID},
			{"$set" : {f"{time}" : member_info[f"{time}"] + TIMER_UPDATE_INTERVAL}}
		)

async def reset_daily_times() -> None:
	memberinfo = membertime.find({})
	async for info in memberinfo:
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"yesterday" : info["daily"]}}
		)
		if info["yesterday"] > 0:
			await membertime.update_one(
				{"user_ID" : info["user_ID"]},
				{'$inc' : {"streak" : 1}}
			)
		else:
			await membertime.update_one(
				{"user_ID" : info["user_ID"]},
				{'$set' : {"streak" : 0}}
			)
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"daily" : 0}}
		)

async def reset_weekly_times() -> None:
	memberinfo = membertime.find({})
	async for info in memberinfo:
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"weekly" : 0}}
		)

async def reset_monthly_times() -> None:
	memberinfo = membertime.find({})
	async for info in memberinfo:
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"monthly" : 0}}
		)

# /----------------------------------------------------------/
# /           Plugin, Commands and Listeners below			 /
# /----------------------------------------------------------/

study_plugin = lightbulb.Plugin("Study")

def FetchMembersInChannels(channelIDList : list) -> list:
	VoiceStatesList = []
	for channelid in channelIDList:
		voicestates = app.cache.get_voice_states_view_for_channel(int(GUILD_ID), channelid)
		if voicestates.values():
			VoiceStatesList.extend(voicestates.values())
	return VoiceStatesList

async def GetFocusedMembers() -> list:
	focused = []
	MemberVoiceStates = FetchMembersInChannels(StudyVCIDs)

	for VoiceState in MemberVoiceStates:
		CurrentState = "None"
		if not VoiceState.member.is_bot:
			if not VoiceState.is_streaming and not VoiceState.is_video_enabled:
				CurrentState = "NONE"
			elif VoiceState.is_streaming and VoiceState.is_video_enabled:
				CurrentState = "BOTH"
			elif VoiceState.is_streaming:
				CurrentState = "STREAM"
			elif VoiceState.is_video_enabled:
				CurrentState = "VIDEO"

			focused.append((VoiceState.user_id, CurrentState))
	return focused
	
def StudyVCJoinMessage(member : hikari.Member, NoOfRoles):
	StudyVCEmbed = hikari.Embed(
		title = f"It's Focus Time, {member.display_name}!",
		description = f"To help you focus, you have been muted in all channels except <#{Utils.STUDYTOGETHERCHANNELID}>.",
		color = randint(0, 0xffffff)
	).add_field(
		name = "How do I get unmuted?",
		value = "You will be automatically unmuted when you leave the Voice Channel."
	)
	if randint(0, 150 - NoOfRoles) == 0:
		StudyVCEmbed.set_image('https://res.cloudinary.com/zeusabhijeet/image/upload/v1615206699/SleepBot/Study%20Commands/Study_you_b_words.png')
	else:
		StudyVCEmbed.set_image('https://res.cloudinary.com/zeusabhijeet/image/upload/v1615211844/SleepBot/Study%20Commands/focus_you_b_words.gif')
	return StudyVCEmbed

@study_plugin.command
@lightbulb.command(name = "study", description = "Study Streak Club Commands", auto_defer = True)
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def study_streak_cmd_group(ctx : context.Context) -> None:
	pass

@study_streak_cmd_group.child
@lightbulb.option(
	name = "timer", 
	description = 'Sort Option', 
	type = str,
	required = False,
	choices = ['total', 'daily', 'weekly', 'monthly', 'video', 'stream'],
	default = 'total'
)
@lightbulb.command(
	name = "leaderboard",
	description = "Fetches the top 12 members by time spent studying/working in Study VC.",
	aliases = ['lb', 'slb'],
	auto_defer = True
)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def study_leaderboard_command(ctx : context.Context) -> None:
	timer : str = ctx.options.timer or 'total'
	timer = timer.lower()
	leaderboard = membertime.find({}).sort(timer, -1)
	rank = 1
	LeaderboardEmbed = hikari.Embed(
		title = "Study Streak Club Leaderboard",
		description = f"Currently sorting by {timer}",
		colour = randint(0, 0xffffff)
	)
	async for memberinfo in leaderboard:
		if rank > 10:
			break
		try:
			member = ctx.get_guild().get_member(memberinfo['user_ID'])
		except:
			continue
		hrs, mins = MinutesToHours(memberinfo[timer])
		if member.id == ctx.author.id:
			LeaderboardEmbed.add_field(
				name = f"-> {rank} : {member}",
				value = f"{hrs} Hrs {mins} Mins\n**Current Streak :** {memberinfo['streak']}",
				inline = False
			)
		else:
			LeaderboardEmbed.add_field(
				name = f"{rank} : {member}",
				value = f"{hrs} Hrs {mins} Mins\n**Current Streak :** {memberinfo['streak']}",
				inline = False
			)
		
		rank += 1
		
	await ctx.respond(embed = LeaderboardEmbed)

@study_streak_cmd_group.child
@lightbulb.option("target", "User to fetch stats of", type = hikari.User, required = False)
@lightbulb.command(name = "stats", description = "Fetch the time you/mentioned user have spent studying/working in the Study VCs", auto_defer = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def study_time_stats(ctx : context.Context) -> None:
	target = ctx.options.target if ctx.options.target is not None else ctx.user
	target = ctx.get_guild().get_member(target)
	
	MemberStats = await membertime.find_one({"user_ID" : target.id})
	if not MemberStats:
		await add_member_to_db(target.id)
		MemberStats = await membertime.find_one({"user_ID" : target.id})
		
	times = []
	StatsEmbed = hikari.Embed(
		title = f"{target.display_name}'s Study Stats",
		description = f"\n**Current Streak :** {MemberStats['streak']}",
		colour = randint(0, 0xffffff)
	).set_footer(text = "Stats reset between 12am and 1am.")

	for mins in (
		MemberStats["total"],
		MemberStats["daily"],
		MemberStats["weekly"],
		MemberStats["monthly"],
		MemberStats["video"],
		MemberStats["stream"]
	):
		times.append(MinutesToHours(mins))
		
	total = str(times[0][0]) + " Hrs " + str(times[0][1]) + " Mins"
	daily = str(times[1][0]) + " Hrs " + str(times[1][1]) + " Mins"
	weekly = str(times[2][0]) + " Hrs " + str(times[2][1]) + " Mins"
	monthly = str(times[3][0]) + " Hrs " + str(times[3][1]) + " Mins"
	video = str(times[4][0]) + " Hrs " + str(times[4][1]) + " Mins"
	stream = str(times[5][0]) + " Hrs " + str(times[5][1]) + " Mins"

	StatsEmbed.add_field(
		name = "Total",
		value = total,
		inline = True
	).add_field(
		name = "Daily",
		value = daily,
		inline = True
	).add_field(
		name = "Weekly",
		value = weekly,
		inline = True
	).add_field(
		name = "Monthly",
		value = monthly,
		inline = True
	).add_field(
		name = "Video On Time",
		value = video,
		inline = True
	).add_field(
		name = "Stream Time",
		value = stream,
		inline = True
	)

	await ctx.respond(embed = StatsEmbed)

@study_plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_voice_state_update(event : hikari.VoiceStateUpdateEvent) -> None:
	if event.state.member.is_bot:
		return
	if event.old_state is None and event.state is not None and (event.state.channel_id in StudyVCIDs):
		await app.rest.add_role_to_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User joined Study VC")
		UserRoles = len(event.state.member.get_roles())
		await app.rest.create_message(FocusChannelID, f"{event.state.member.mention}", embed = StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
		if event.state.channel_id == CAMS_ON_VC:
			await app.rest.create_message(
				FocusChannelID,
				f"{event.state.member.mention} Turn on your Camera or you will be kicked from <#{event.state.channel_id}>",
				user_mentions = True
			)
	elif event.old_state is not None and event.state is not None and (event.state.channel_id in StudyVCIDs):
		if event.old_state.channel_id in StudyVCIDs:
			return
		await app.rest.add_role_to_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User joined Study VC")
		UserRoles = len(event.state.member.get_roles())
		await app.rest.create_message(FocusChannelID, f"{event.state.member.mention}", embed = StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
		if event.state.channel_id == CAMS_ON_VC:
			await app.rest.create_message(
				FocusChannelID,
				f"{event.state.member.mention} Turn on your Camera or you will be kicked from <#{event.state.channel_id}>",
				user_mentions = True
			)
	elif event.state and event.old_state and (event.old_state.channel_id in StudyVCIDs) and (event.state.channel_id not in StudyVCIDs or event.state.channel_id is None):
		await app.rest.remove_role_from_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User left Study VC")

@study_plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event : hikari.GuildMessageCreateEvent):
	if event.author.is_bot:
		return
	if StaffRoleID in event.get_member().role_ids:
		return
	mention : List[hikari.User] = event.message.mentions.users
	for m in mention:
		mentioneduser = await app.rest.fetch_member(event.guild_id, m)
		if mentioneduser.is_bot:
			return
		elif mentioneduser.id == event.author_id:
			return
		if event.message.channel_id == 770940461337804810:
			return
		roles = mentioneduser.get_roles()
		for r in roles:
			if r.name == "Studying/Working":
				msg = await app.rest.create_message(
					event.channel_id, 
					content = f"Hey {event.message.author.mention}, don't disturb {mentioneduser.mention}. They are currently focusing!",
					user_mentions = False
				)
				await asyncio.sleep(10)
				await msg.delete()

# /----------------------------------------------------------/
# /		All tasks related to Refeshing times and kicking     /
# /		stalkers from cam VC below							 /
# /----------------------------------------------------------/


async def RefreshMemberTimes():
	while True:
		StudyingMembers = await GetFocusedMembers()
		for member in StudyingMembers:
			if member[1] == "STREAM":
				timer = ("total", "daily", "weekly", "monthly", "stream")
			elif member[1] == "VIDEO":
				timer = ("total", "daily", "weekly", "monthly", "video")
			elif member[1] == "BOTH":
				timer = ("total", "daily", "weekly", "monthly", "video", "stream")
			else:
				timer = ("total", "daily", "weekly", "monthly")
			await update_time(member[0], timer)
		await app.rest.create_message(
			Utils.LOGCHANNELID,
			embed = hikari.Embed(
				title = "Study Streak Club Log",
				description = "Member Times have been updated",
				colour = randint(0, 0xffffff),
				timestamp = datetime.now().astimezone()
			)
		)
		await asyncio.sleep(60)

async def ResetLeaderboard():
	while True:
		now = datetime.now()
		if now.hour == 0:
			await reset_daily_times()
			await app.rest.create_message(
				Utils.LOGCHANNELID,
				f"Study Streak Club Daily Leaderboard has been reset at <t:{int(time.time())}>"
			)
			if now.weekday() == 0:
				await reset_weekly_times()
				await app.rest.create_message(
					Utils.LOGCHANNELID,
					f"Study Streak Club Weekly Leaderboard has been reset at <t:{int(time.time())}>"
				)
			if now.day == 1:
				await reset_monthly_times()
				await app.rest.create_message(
					Utils.LOGCHANNELID,
					f"Study Streak Club Monthly Leaderboard has been reset at <t:{int(time.time())}>"
				)
		await asyncio.sleep(3600)
	
async def KickStalkersFromCamsVC():
	while True:
		await asyncio.sleep(KICK_STALKERS_AFTER)
		MembersVoiceStates = FetchMembersInChannels([CAMS_ON_VC])
		VoiceStates : VoiceState
		for VoiceStates in MembersVoiceStates:
			if not VoiceStates.member.is_bot:
				if not VoiceStates.is_video_enabled:
					await app.rest.edit_member(int(GUILD_ID), VoiceStates.user_id, voice_channel = STUDYVC1, reason = "User did not turn on camera")
					await app.rest.create_message(
						FocusChannelID,
						f"{VoiceStates.member.mention} Moved you to <#{STUDYVC1}> for not turning on camera.",
						user_mentions = True
					)

# /----------------------------------------------------------/

def load(bot : lightbulb.BotApp) -> None:
	global app
	bot.add_plugin(study_plugin)
	app = bot
	asyncio.create_task(RefreshMemberTimes())
	asyncio.create_task(ResetLeaderboard())
	asyncio.create_task(KickStalkersFromCamsVC())

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(study_plugin)
