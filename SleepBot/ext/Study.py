import hikari
import lightbulb
import Utils
import asyncio
import time
import miru
import motor.motor_asyncio

from hikari.voices import VoiceState
from random import randint
from lightbulb import commands, context
from lightbulb.ext import tasks
from Utils import LOGCHANNELID, StaffRoleID, StudyVCIDs, FocusChannelID
from typing import List
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

CAMS_ON_VC = 1015286325919879178
STUDYVC1 = 818011398231687178

StudyVCIDs.append(CAMS_ON_VC)

STUDYING_ROLE = 816873155246817290

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
			"streak" : 0,
			"credits" : 0,
			"today_cam" : 0,
			"today_stream" : 0,
			"yesterday_cam" : 0,
			"yesterday_stream" : 0
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
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"yesterday_cam" : info["today_cam"]}}
		)
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"yesterday_stream" : info["today_stream"]}}
		)
		if info["yesterday_stream"] < 30:
			await membertime.update_one(
				{"user_ID" : info["user_ID"]},
				{'$set' : {"streak" : 0}}
			)
#		if info["streak"] != 0 and info["streak"] % 7 == 0:
#			await membertime.update_one(
#				{"user_ID" : info["user_ID"]},
#				{'$inc' : {"credits" : 1}}
#			)
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"daily" : 0}}
		)
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"today_cam" : 0}}
		)
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"today_stream" : 0}}
		)
	streakmembers = membertime.find({'yesterday_stream' : {'$gt' : 30}})
	async for mem in streakmembers:
		await mem.update_one(
				{"user_ID" : mem["user_ID"]},
				{'$inc' : {"streak" : 1}}
			)


async def reset_weekly_times() -> None:
	memberinfo = membertime.find({'weekly' : {'$gt' : 0}})
	top_members = membertime.find({'weekly' : {'$gt' : 0}}).sort('weekly', -1).limit(15)
	top_member_ids = ""
	async for top in top_members:
		top_member_ids += f"{top['user_ID']}, "
	msg = await study_plugin.app.rest.create_message(
		LOGCHANNELID,
		f"<@!{study_plugin.app.owner_ids[0]}>",
		embed = hikari.Embed(
			title = 'Weekly Top Members',
			description = top_member_ids
		),
		user_mentions = True
	)
	pins = await study_plugin.app.rest.fetch_pins(LOGCHANNELID)
	for pin in pins:
		await study_plugin.app.rest.unpin_message(LOGCHANNELID, pin)
	await study_plugin.app.rest.pin_message(LOGCHANNELID, msg)
	async for info in memberinfo:
		await membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"weekly" : 0}}
		)

async def reset_monthly_times() -> None:
	memberinfo = membertime.find({'monthly' : {'$gt' : 0}})
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
		voicestates = study_plugin.app.cache.get_voice_states_view_for_channel(int(GUILD_ID), channelid)
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

async def resetspecificmember(user : hikari.User) -> None:
	MemberStats = await membertime.find_one({"user_ID" : user.id})
	
	if not MemberStats:
		await add_member_to_db(user.id)
		return
	
	timers = ['total', 'daily', 'yesterday', 'weekly', 'monthly', 'stream', 'video', 'streak', 'credits', 'today_cam', 'today_stream', 'yesterday_cam', 'yesterday_stream']

	for time in timers:
		await membertime.update_one(
			{"user_ID" : user.id},
			{'$set' : {time : 0}}
		)
	
	return


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
	choices = ['total', 'daily', 'weekly', 'monthly', 'video', 'stream', 'streak', 'credits'],
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
	leaderboard = membertime.find({}).sort(timer, -1).limit(15)
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
			if member == None:
				continue
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

	descrip = (
		f"\n**Current Streak :** {MemberStats['streak']}"
		f"\n**Credits:** {MemberStats['credits']}"
	)

	StatsEmbed = hikari.Embed(
		title = f"{target.display_name}'s Study Stats",
		description = descrip,
		colour = randint(0, 0xffffff)
	).set_footer(
		text = "Stats reset between 12am and 1am."
	).set_thumbnail(
		target.avatar_url or target.default_avatar_url
	).add_field(
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

@study_plugin.command
@lightbulb.command(name = "Study Stats", description = "Fetch the time you/mentioned user have spent studying/working in the Study VCs", auto_defer = True)
@lightbulb.implements(commands.UserCommand)
async def study_time_stats_user_cmd(ctx : context.Context) -> None:
	target = ctx.get_guild().get_member(ctx.options.target)
	
	MemberStats = await membertime.find_one({"user_ID" : target.id})
	if not MemberStats:
		await add_member_to_db(target.id)
		MemberStats = await membertime.find_one({"user_ID" : target.id})
		
	times = []
	
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

	descrip = (
		f"\n**Current Streak :** {MemberStats['streak']}"
		f"\n**Credits:** {MemberStats['credits']}"
	)

	StatsEmbed = hikari.Embed(
		title = f"{target.display_name}'s Study Stats",
		description = descrip,
		colour = randint(0, 0xffffff)
	).set_footer(
		text = "Stats reset between 12am and 1am."
	).set_thumbnail(
		target.avatar_url or target.default_avatar_url
	).add_field(
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

	await ctx.respond(embed = StatsEmbed, flags = hikari.MessageFlag.EPHEMERAL)

@study_streak_cmd_group.child
@lightbulb.option("compare_to", "The user to compare your stats to", hikari.User, required = True)
@lightbulb.command("compare", "Compare your study stats with another user", auto_defer = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def study_compare_cmd(ctx : context.Context) -> None:
	target = ctx.get_guild().get_member(ctx.options.compare_to)

	if target.id == ctx.author.id:
		return await ctx.respond("<:Hmmmmm:839015631922790450> You cannot compare yourself with yourself (or can you?)")

	TargetStats = await membertime.find_one({"user_ID" : target.id})
	if not TargetStats:
		await add_member_to_db(target.id)
		TargetStats = await membertime.find_one({"user_ID" : target.id})
	
	AuthorStats = await membertime.find_one({"user_ID" : ctx.author.id})
	if not AuthorStats:
		await add_member_to_db(ctx.author.id)
		AuthorStats = await membertime.find_one({"user_ID" : ctx.author.id})
	
	TargetTimes = []
	AuthorTimes = []

	for mins in (
		TargetStats["total"],
		TargetStats["daily"],
		TargetStats["weekly"],
		TargetStats["monthly"],
		TargetStats["video"],
		TargetStats["stream"]
	):
		TargetTimes.append(MinutesToHours(mins))
		
	TargetTotal = str(TargetTimes[0][0]) + " Hrs " + str(TargetTimes[0][1]) + " Mins"
	TargetDaily = str(TargetTimes[1][0]) + " Hrs " + str(TargetTimes[1][1]) + " Mins"
	TargetWeekly = str(TargetTimes[2][0]) + " Hrs " + str(TargetTimes[2][1]) + " Mins"
	TargetMonthly = str(TargetTimes[3][0]) + " Hrs " + str(TargetTimes[3][1]) + " Mins"
	TargetVideo = str(TargetTimes[4][0]) + " Hrs " + str(TargetTimes[4][1]) + " Mins"
	TargetStream = str(TargetTimes[5][0]) + " Hrs " + str(TargetTimes[5][1]) + " Mins"

	for mins in (
		AuthorStats["total"],
		AuthorStats["daily"],
		AuthorStats["weekly"],
		AuthorStats["monthly"],
		AuthorStats["video"],
		AuthorStats["stream"]
	):
		AuthorTimes.append(MinutesToHours(mins))
		
	AuthorTotal = str(AuthorTimes[0][0]) + " Hrs " + str(AuthorTimes[0][1]) + " Mins"
	AuthorDaily = str(AuthorTimes[1][0]) + " Hrs " + str(AuthorTimes[1][1]) + " Mins"
	AuthorWeekly = str(AuthorTimes[2][0]) + " Hrs " + str(AuthorTimes[2][1]) + " Mins"
	AuthorMonthly = str(AuthorTimes[3][0]) + " Hrs " + str(AuthorTimes[3][1]) + " Mins"
	AuthorVideo = str(AuthorTimes[4][0]) + " Hrs " + str(AuthorTimes[4][1]) + " Mins"
	AuthorStream = str(AuthorTimes[5][0]) + " Hrs " + str(AuthorTimes[5][1]) + " Mins"

	CompareEmbed = hikari.Embed(
		title = f"Comparing: {ctx.author} v/s {target}",
		description = f"Comparing stats since last reset.",
		colour = randint(0, 0xffffff)
	).add_field(
		"Current Streak:",
		f"**{ctx.author} : {AuthorStats['streak']}**\n{target} : {TargetStats['streak']}" if AuthorStats["streak"] >= TargetStats["streak"]
		else f"{ctx.author} : {AuthorStats['streak']}\n**{target} : {TargetStats['streak']}**",
		inline = True
	).add_field(
		"Total Times:",
		f"**{ctx.author} : {AuthorTotal}**\n{target} : {TargetTotal}" if AuthorStats["total"] >= TargetStats["total"]
		else f"{ctx.author} : {AuthorTotal}\n**{target} : {TargetTotal}**",
		inline = True
	).add_field(
		"Daily Times:",
		f"**{ctx.author} : {AuthorDaily}**\n{target} : {TargetDaily}" if AuthorStats["daily"] >= TargetStats["daily"]
		else f"{ctx.author} : {AuthorDaily}\n**{target} : {TargetDaily}**",
		inline = True
	).add_field(
		"Weekly Times:",
		f"**{ctx.author} : {AuthorWeekly}**\n{target} : {TargetWeekly}" if AuthorStats["weekly"] >= TargetStats["weekly"]
		else f"{ctx.author} : {AuthorWeekly}\n**{target} : {TargetWeekly}**",
		inline = True
	).add_field(
		"Monthly Times:",
		f"**{ctx.author} : {AuthorMonthly}**\n{target} : {TargetMonthly}" if AuthorStats["monthly"] >= TargetStats["monthly"]
		else f"{ctx.author} : {AuthorMonthly}\n**{target} : {TargetMonthly}**",
		inline = True
	).add_field(
		"Camera On Times:",
		f"**{ctx.author} : {AuthorVideo}**\n{target} : {TargetVideo}" if AuthorStats["video"] >= TargetStats["video"]
		else f"{ctx.author} : {AuthorVideo}\n**{target} : {TargetVideo}**",
		inline = True
	).add_field(
		"Stream On Times:",
		f"**{ctx.author} : {AuthorStream}**\n{target} : {TargetStream}" if AuthorStats["stream"] >= TargetStats["stream"]
		else f"{ctx.author} : {AuthorStream}\n**{target} : {TargetStream}**",
		inline = True
	)

	await ctx.respond(embed = CompareEmbed)

@study_plugin.command
@lightbulb.command("Compare Study Stats", "Compare your study stats with another user", auto_defer = True)
@lightbulb.implements(commands.UserCommand)
async def study_compare_cmd(ctx : context.Context) -> None:
	target = ctx.get_guild().get_member(ctx.options.target)

	if target.id == ctx.author.id:
		return await ctx.respond("<:Hmmmmm:839015631922790450> You cannot compare yourself with yourself (or can you?)")

	TargetStats = await membertime.find_one({"user_ID" : target.id})
	if not TargetStats:
		await add_member_to_db(target.id)
		TargetStats = await membertime.find_one({"user_ID" : target.id})
	
	AuthorStats = await membertime.find_one({"user_ID" : ctx.author.id})
	if not AuthorStats:
		await add_member_to_db(ctx.author.id)
		AuthorStats = await membertime.find_one({"user_ID" : ctx.author.id})
	
	TargetTimes = []
	AuthorTimes = []

	for mins in (
		TargetStats["total"],
		TargetStats["daily"],
		TargetStats["weekly"],
		TargetStats["monthly"],
		TargetStats["video"],
		TargetStats["stream"]
	):
		TargetTimes.append(MinutesToHours(mins))
		
	TargetTotal = str(TargetTimes[0][0]) + " Hrs " + str(TargetTimes[0][1]) + " Mins"
	TargetDaily = str(TargetTimes[1][0]) + " Hrs " + str(TargetTimes[1][1]) + " Mins"
	TargetWeekly = str(TargetTimes[2][0]) + " Hrs " + str(TargetTimes[2][1]) + " Mins"
	TargetMonthly = str(TargetTimes[3][0]) + " Hrs " + str(TargetTimes[3][1]) + " Mins"
	TargetVideo = str(TargetTimes[4][0]) + " Hrs " + str(TargetTimes[4][1]) + " Mins"
	TargetStream = str(TargetTimes[5][0]) + " Hrs " + str(TargetTimes[5][1]) + " Mins"

	for mins in (
		AuthorStats["total"],
		AuthorStats["daily"],
		AuthorStats["weekly"],
		AuthorStats["monthly"],
		AuthorStats["video"],
		AuthorStats["stream"]
	):
		AuthorTimes.append(MinutesToHours(mins))
		
	AuthorTotal = str(AuthorTimes[0][0]) + " Hrs " + str(AuthorTimes[0][1]) + " Mins"
	AuthorDaily = str(AuthorTimes[1][0]) + " Hrs " + str(AuthorTimes[1][1]) + " Mins"
	AuthorWeekly = str(AuthorTimes[2][0]) + " Hrs " + str(AuthorTimes[2][1]) + " Mins"
	AuthorMonthly = str(AuthorTimes[3][0]) + " Hrs " + str(AuthorTimes[3][1]) + " Mins"
	AuthorVideo = str(AuthorTimes[4][0]) + " Hrs " + str(AuthorTimes[4][1]) + " Mins"
	AuthorStream = str(AuthorTimes[5][0]) + " Hrs " + str(AuthorTimes[5][1]) + " Mins"

	CompareEmbed = hikari.Embed(
		title = f"Comparing: {ctx.author} v/s {target}",
		description = f"Comparing stats since last reset.",
		colour = randint(0, 0xffffff)
	).add_field(
		"Current Streak:",
		f"**{ctx.author} : {AuthorStats['streak']}**\n{target} : {TargetStats['streak']}" if AuthorStats["streak"] >= TargetStats["streak"]
		else f"{ctx.author} : {AuthorStats['streak']}\n**{target} : {TargetStats['streak']}**",
		inline = True
	).add_field(
		"Total Times:",
		f"**{ctx.author} : {AuthorTotal}**\n{target} : {TargetTotal}" if AuthorStats["total"] >= TargetStats["total"]
		else f"{ctx.author} : {AuthorTotal}\n**{target} : {TargetTotal}**",
		inline = True
	).add_field(
		"Daily Times:",
		f"**{ctx.author} : {AuthorDaily}**\n{target} : {TargetDaily}" if AuthorStats["daily"] >= TargetStats["daily"]
		else f"{ctx.author} : {AuthorDaily}\n**{target} : {TargetDaily}**",
		inline = True
	).add_field(
		"Weekly Times:",
		f"**{ctx.author} : {AuthorWeekly}**\n{target} : {TargetWeekly}" if AuthorStats["weekly"] >= TargetStats["weekly"]
		else f"{ctx.author} : {AuthorWeekly}\n**{target} : {TargetWeekly}**",
		inline = True
	).add_field(
		"Monthly Times:",
		f"**{ctx.author} : {AuthorMonthly}**\n{target} : {TargetMonthly}" if AuthorStats["monthly"] >= TargetStats["monthly"]
		else f"{ctx.author} : {AuthorMonthly}\n**{target} : {TargetMonthly}**",
		inline = True
	).add_field(
		"Camera On Times:",
		f"**{ctx.author} : {AuthorVideo}**\n{target} : {TargetVideo}" if AuthorStats["video"] >= TargetStats["video"]
		else f"{ctx.author} : {AuthorVideo}\n**{target} : {TargetVideo}**",
		inline = True
	).add_field(
		"Stream On Times:",
		f"**{ctx.author} : {AuthorStream}**\n{target} : {TargetStream}" if AuthorStats["stream"] >= TargetStats["stream"]
		else f"{ctx.author} : {AuthorStream}\n**{target} : {TargetStream}**",
		inline = True
	)

	await ctx.respond(embed = CompareEmbed)

class AcceptReset(miru.Button):
	def __init__(self) -> None:
		super().__init__(style=hikari.ButtonStyle.DANGER, label = 'Yes. Reset Member.')
	
	async def callback(self, ctx : miru.Context) -> None:
		await ctx.defer()
		await resetspecificmember(self.view.user)
		await ctx.edit_response(
				embed = hikari.Embed(
					title = "Reset Member",
					description = f"Successfully reset {self.view.user.mention}'s stats.",
					colour = 0xd85759
				),
				components = []
			)
		self.view.answer = True
		self.view.stop()

class RejectReset(miru.Button):
	def __init__(self) -> None:
		super().__init__(style=hikari.ButtonStyle.SECONDARY, label = 'No. Go Back.')
	
	async def callback(self, ctx : miru.Context) -> None:
		await ctx.defer()
		await ctx.edit_response(
				embed = hikari.Embed(
					title = "Reset Member",
					description = "Operation cancelled",
					colour = 0xd85759
				),
				components = []
			)
		self.view.answer = False
		self.view.stop()

@study_plugin.command
@lightbulb.add_checks(lightbulb.has_roles(742028591281340557, 754760818289279057, mode = any))
@lightbulb.option(name = 'user', description = "The user to reset the stats of", type = hikari.User, required = True)
@lightbulb.command(name = 'resetmember', description = "Reset a member's study streak club stats. Staff only command", auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def resetmember(ctx : context.Context) -> None:
	user : hikari.User = ctx.options.user
	view = miru.View(timeout = 60, autodefer = True)
	view.add_item(AcceptReset())
	view.add_item(RejectReset())
	message = await ctx.respond(
		embed = hikari.Embed(
			title = "Reset Member",
			description = f"Are you sure you want to reset {user.mention}'s stats?",
			colour = 0xd85759
		),
		components = view.build()
	)
	view.start(await message.message())
	view.user = user

	await view.wait()

	if hasattr(view, "answer"):
		return
		if view.answer == True:
			await ctx.edit_last_response(
				embed = hikari.Embed(
					title = "Reset Member",
					description = f"Successfully reset {user.mention}'s stats.",
					colour = 0xd85759
				),
				components = []
			)
		else:
			await ctx.edit_last_response(
				embed = hikari.Embed(
					title = "Reset Member",
					description = "Operation cancelled",
					colour = 0xd85759
				),
				components = []
			)
	else:	
		await ctx.edit_last_response(
			embed = hikari.Embed(
				title = "Reset Member",
				description = "Did not get any response. Timed out",
				colour = 0xd85759
			),
			components = []
		)

@study_plugin.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("resetdaily", description = 'Resets daily stats')
@lightbulb.implements(commands.PrefixCommand)
async def resetdailymanual(ctx : context.Context) -> None:
	await reset_daily_times()
	await ctx.respond("Done")

@study_plugin.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("resetall", description = 'Resets everything')
@lightbulb.implements(commands.PrefixCommand)
async def resetallmanual(ctx : context.Context) -> None:
	result = await membertime.delete_many({})
	await ctx.respond(f"Deleted {result.deleted_count} entries.")

@study_plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_voice_state_update(event : hikari.VoiceStateUpdateEvent) -> None:
	if event.state.member.is_bot:
		return
	if event.old_state is None and event.state is not None and (event.state.channel_id in StudyVCIDs):
		await study_plugin.app.rest.add_role_to_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User joined Study VC")
		UserRoles = len(event.state.member.get_roles())
		await study_plugin.app.rest.create_message(FocusChannelID, f"{event.state.member.mention}", embed = StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
		if event.state.channel_id == CAMS_ON_VC:
			await study_plugin.app.rest.create_message(
				FocusChannelID,
				f"{event.state.member.mention} Turn on your Camera or you will be kicked from <#{event.state.channel_id}>",
				user_mentions = True
			)
	elif event.old_state is not None and event.state is not None and (event.state.channel_id in StudyVCIDs):
		if event.old_state.channel_id in StudyVCIDs:
			return
		await study_plugin.app.rest.add_role_to_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User joined Study VC")
		UserRoles = len(event.state.member.get_roles())
		await study_plugin.app.rest.create_message(FocusChannelID, f"{event.state.member.mention}", embed = StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
		if event.state.channel_id == CAMS_ON_VC:
			await study_plugin.app.rest.create_message(
				FocusChannelID,
				f"{event.state.member.mention} Turn on your Camera or you will be kicked from <#{event.state.channel_id}>",
				user_mentions = True
			)
	elif event.state and event.old_state and (event.old_state.channel_id in StudyVCIDs) and (event.state.channel_id not in StudyVCIDs or event.state.channel_id is None):
		await study_plugin.app.rest.remove_role_from_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User left Study VC")


@study_plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message_create(event : hikari.GuildMessageCreateEvent):
	if event.author.is_bot:
		return
	if StaffRoleID in event.get_member().role_ids:
		return
	mention : List[hikari.Snowflake, hikari.User] = list(event.message.user_mentions)
	for m in mention:
		mentioneduser = await study_plugin.app.rest.fetch_member(event.guild_id, m)
		if mentioneduser.is_bot:
			return
		elif mentioneduser.id == event.author_id:
			return
		if event.message.channel_id == 770940461337804810:
			return
		roles = mentioneduser.get_roles()
		for r in roles:
			if r.name == "Studying/Working":
				msg = await study_plugin.app.rest.create_message(
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

@tasks.task(s = 60)
async def RefreshMemberTimes():
	StudyingMembers = await GetFocusedMembers()
	for member in StudyingMembers:
		if member[1] == "STREAM":
			timer = ("total", "daily", "weekly", "monthly", "stream", "today_stream")
		elif member[1] == "VIDEO":
			timer = ("total", "daily", "weekly", "monthly", "video", "today_cam")
		elif member[1] == "BOTH":
			timer = ("total", "daily", "weekly", "monthly", "video", "stream", "today_cam", "today_stream")
		else:
			timer = ("total", "daily", "weekly", "monthly")
		await update_time(member[0], timer)
	await study_plugin.app.rest.create_message(
		Utils.LOGCHANNELID,
		embed = hikari.Embed(
			title = "Study Streak Club Log",
			description = "Member Times have been updated",
			colour = randint(0, 0xffffff),
			timestamp = datetime.now().astimezone()
		)
	)

@tasks.task(s = 3600)
async def ResetLeaderboard():
	now = datetime.now()
	if now.hour == 0:
		await reset_daily_times()
		await study_plugin.app.rest.create_message(
			Utils.LOGCHANNELID,
			f"Study Streak Club Daily Leaderboard has been reset at <t:{int(time.time())}>"
		)
		if now.weekday() == 0:
			await reset_weekly_times()
			await study_plugin.app.rest.create_message(
				Utils.LOGCHANNELID,
				f"Study Streak Club Weekly Leaderboard has been reset at <t:{int(time.time())}>"
			)
		if now.day == 1:
			await reset_monthly_times()
			await study_plugin.app.rest.create_message(
				Utils.LOGCHANNELID,
				f"Study Streak Club Monthly Leaderboard has been reset at <t:{int(time.time())}>"
			)

@tasks.task(s = 45)
async def KickStalkersFromCamsVC():
	MembersVoiceStates = FetchMembersInChannels([CAMS_ON_VC])
	VoiceStates : VoiceState
	for VoiceStates in MembersVoiceStates:
		if not VoiceStates.member.is_bot:
			if not VoiceStates.is_video_enabled:
				await study_plugin.app.rest.edit_member(int(GUILD_ID), VoiceStates.user_id, voice_channel = STUDYVC1, reason = "User did not turn on camera")
				await study_plugin.app.rest.create_message(
					FocusChannelID,
					f"{VoiceStates.member.mention} Moved you to <#{STUDYVC1}> for not turning on camera.",
					user_mentions = True
				)

# /----------------------------------------------------------/

def load(bot : lightbulb.BotApp) -> None:
	global app
	bot.add_plugin(study_plugin)
	RefreshMemberTimes.start()
	ResetLeaderboard.start()
	KickStalkersFromCamsVC.start()

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(study_plugin)
	RefreshMemberTimes.stop()
	ResetLeaderboard.stop()
	KickStalkersFromCamsVC.stop()
	
