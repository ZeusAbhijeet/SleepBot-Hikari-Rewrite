import asyncio
from datetime import datetime
import hikari
from hikari.users import User
from hikari.voices import VoiceState
import lightbulb
import random
import sqlite3
import time
from lightbulb.slash_commands.commands import Option
from pymongo import MongoClient
from __init__ import GUILD_ID
from asyncio import tasks
from lightbulb.converters import Greedy
import Utils
from lightbulb.command_handler import Bot
from typing import Iterable, List, Optional
from Utils import StudyBuddiesRoleID, StaffRoleID

with open("./Secrets/studystreakmongourl") as f:
	MongoURL = f.read().strip()

cluster = MongoClient(MongoURL)
membertime = cluster['bluelearn']['membertime']

TIMER_UPDATE_INTERVAL = 1 # minutes
KICK_STALKERS_AFTER = 45 # seconds

CAMS_ON_VC = 770670934565715998
STUDYVC1 = 818011398231687178

STUDYING_ROLE = 816873155246817290

def MinutesToHours(mins : int):
	hours = int(mins / 60)
	minutes = mins % 60
	return hours, minutes

def add_member_to_db(userID : int) -> None:
	membertime.insert_one(
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

def update_time(userID : int, times = ("total", "daily", "weekly", "monthly")) -> None:
	member_info = membertime.find_one({"user_ID" : userID})
	if not member_info:
		add_member_to_db(userID)
		return
	for time in times:
		membertime.update_one(
			{"user_ID" : userID},
			{"$set" : {f"{time}" : member_info[f"{time}"] + TIMER_UPDATE_INTERVAL}}
		)

def reset_daily_times() -> None:
	memberinfo = membertime.find({})
	for info in memberinfo:
		membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"yesterday" : info["daily"]}}
		)
		if info["yesterday"] > 0:
			membertime.update_one(
				{"user_ID" : info["user_ID"]},
				{'$inc' : {"streak" : 1}}
			)
		else:
			membertime.update_one(
				{"user_ID" : info["user_ID"]},
				{'$set' : {"streak" : 0}}
			)
		membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"daily" : 0}}
		)

def reset_weekly_times() -> None:
	memberinfo = membertime.find({})
	for info in memberinfo:
		membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"weekly" : 0}}
		)

def reset_monthly_times() -> None:
	memberinfo = membertime.find({})
	for info in memberinfo:
		membertime.update_one(
			{"user_ID" : info["user_ID"]},
			{'$set' : {"monthly" : 0}}
		)

class Study(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
		conn = sqlite3.connect('Database.db')
		c = conn.cursor()
		self.StudyVCIDTuple = c.execute(f"SELECT channel_ID FROM channel_table WHERE title = 'STUDYVC';").fetchall()
		self.FocusChannelID = c.execute(f"SELECT channel_ID FROM channel_table WHERE title = 'FOCUS';").fetchone()
		self.FocusChannelID = self.FocusChannelID[0]
		self.StudyVCIDs = []
		for id in self.StudyVCIDTuple:
			self.StudyVCIDs.append(id[0])
		conn.close()
		asyncio.create_task(self.RefreshMemberTimes())
		asyncio.create_task(self.ResetLeaderboard())
		asyncio.create_task(self.KickStalkersFromCamsVC())
	
	def FetchMembersInChannels(self, channelIDList : list) -> list:
		VoiceStatesList = []
		for channelid in channelIDList:
			voicestates = self.bot.cache.get_voice_states_view_for_channel(int(GUILD_ID), channelid)
			if voicestates.values():
				VoiceStatesList.extend(voicestates.values())
		return VoiceStatesList

	async def GetFocusedMembers(self) -> list:
		focused = []
		MemberVoiceStates = self.FetchMembersInChannels(self.StudyVCIDs)

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
	
	def StudyVCJoinMessage(self, member : hikari.Member, NoOfRoles):
		StudyVCEmbed = hikari.Embed(
			title = f"It's Focus Time, {member.display_name}!",
			description = f"To help you focus, you have been muted in all channels except <#{Utils.STUDYTOGETHERCHANNELID}>.",
			color = random.randint(0, 0xffffff)
		).add_field(
			name = "How do I get unmuted?",
			value = "You will be automatically unmuted when you leave the Voice Channel."
		)
		if random.randint(0, 150 - NoOfRoles) == 0:
			StudyVCEmbed.set_image('https://res.cloudinary.com/zeusabhijeet/image/upload/v1615206699/SleepBot/Study%20Commands/Study_you_b_words.png')
		else:
			StudyVCEmbed.set_image('https://res.cloudinary.com/zeusabhijeet/image/upload/v1615211844/SleepBot/Study%20Commands/focus_you_b_words.gif')
		return StudyVCEmbed
	
	@lightbulb.check_exempt(Utils.is_bot_owner)
	@lightbulb.check(Utils.is_study_channel)
	#@lightbulb.cooldown(7200, 1, lightbulb.ChannelBucket)
	@lightbulb.command(name="study_buddies", aliases = ['sb', 'studybuddies', 'studybuddy'])
	async def study_buddies_command(self, ctx : lightbulb.Context, msg : Greedy[str]) -> None:
		"""
		Ping the Study Buddies role to invite people to study with you
		"""
		return await ctx.respond(f"This command has now been disabled", reply = True)

		StudyBuddyRole = ctx.get_guild().get_role(StudyBuddiesRoleID)
		if not msg:
			msg = None
		else:
			message = " ".join(msg)
		await ctx.respond(
			f"Hey {StudyBuddyRole.mention}!\n{ctx.author.mention} wants to study with y'all\nHere's the reason they pinged: **{message}**" if msg is not None else f"Hey {StudyBuddyRole.mention}!\n{ctx.author.mention} wants to study with y'all!",
			role_mentions = True
		)
	
	@lightbulb.command(name = "study_lb", aliases = ['studylb', 'slb'])
	async def study_leaderboard_command(self, ctx : lightbulb.Context, timer : Optional[str] = "total") -> None:
		"""
		Fetches the top 12 members by time spent studying/working in Study VC. Optionally sort by Daily, Weekly, Monthly or Total times.
		"""
		await Utils.command_log(self.bot, ctx, "study_leaderboard")
		msg = await ctx.respond(
			embed = hikari.Embed(
				description = "Fetching Time Details..."
			)
		)
		timer = timer.lower()
		leaderboard = membertime.find({}).sort(timer, -1)
		rank = 1
		LeaderboardEmbed = hikari.Embed(
			title = "Study Streak Club Leaderboard",
			description = f"Currently sorting by {timer}",
			colour = random.randint(0, 0xffffff)
		)
		for memberinfo in leaderboard:
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
		
		await msg.edit(embed = LeaderboardEmbed)

	@lightbulb.command(name = "studystats", aliases = ['study_stats', 'sstats', 'sst'])
	async def study_time_stats(self, ctx : lightbulb.Context, target : Optional[hikari.Member] = None) -> None:
		"""
		Fetch the time you/mentioned user have spent studying/working in the Study VCs
		"""
		await Utils.command_log(self.bot, ctx, "studystats")
		msg = await ctx.respond(
			embed = hikari.Embed(
				description = "Fetching details..."
			)
		)
		if target is None:
			target = ctx.member
		
		MemberStats = membertime.find_one({"user_ID" : target.id})
		if not MemberStats:
			add_member_to_db(target.id)
			MemberStats = membertime.find_one({"user_ID" : target.id})
		
		times = []
		StatsEmbed = hikari.Embed(
			title = f"{target.display_name}'s Study Stats",
			description = f"\n**Current Streak :** {MemberStats['streak']}",
			colour = random.randint(0, 0xffffff)
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

		await msg.edit(embed = StatsEmbed)

	@lightbulb.plugins.listener(hikari.VoiceStateUpdateEvent)
	async def on_voice_state_update(self, event : hikari.VoiceStateUpdateEvent) -> None:
		if event.old_state is None and event.state is not None and (event.state.channel_id in self.StudyVCIDs):
			await self.bot.rest.add_role_to_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User joined Study VC")
			UserRoles = len(event.state.member.get_roles())
			await self.bot.rest.create_message(self.FocusChannelID, f"{event.state.member.mention}", embed = self.StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
			if event.state.channel_id == CAMS_ON_VC:
				await self.bot.rest.create_message(
					self.FocusChannelID,
					f"{event.state.member.mention} Turn on your Camera or you will be kicked from <#{event.state.channel_id}>",
					user_mentions = True
				)
		elif event.old_state is not None and event.state is not None and (event.state.channel_id in self.StudyVCIDs):
			if event.old_state.channel_id in self.StudyVCIDs:
				return
			await self.bot.rest.add_role_to_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User joined Study VC")
			UserRoles = len(event.state.member.get_roles())
			await self.bot.rest.create_message(self.FocusChannelID, f"{event.state.member.mention}", embed = self.StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
			if event.state.channel_id == CAMS_ON_VC:
				await self.bot.rest.create_message(
					self.FocusChannelID,
					f"{event.state.member.mention} Turn on your Camera or you will be kicked from <#{event.state.channel_id}>",
					user_mentions = True
				)
		elif (event.old_state.channel_id in self.StudyVCIDs) and (event.state.channel_id not in self.StudyVCIDs or event.state.channel_id is None):
			await self.bot.rest.remove_role_from_member(event.guild_id, event.state.user_id, STUDYING_ROLE, reason = "User left Study VC")

	@lightbulb.plugins.listener(hikari.GuildMessageCreateEvent)
	async def on_message_create(self, event : hikari.GuildMessageCreateEvent):
		if event.author.is_bot:
			return
		if StaffRoleID in event.get_member().role_ids:
			return
		mention : List[User] = event.message.mentions.users
		for m in mention:
			mentioneduser = await self.bot.rest.fetch_member(event.guild_id, m)
			if mentioneduser.is_bot:
				return
			elif mentioneduser.id == event.author_id:
				return
			if event.message.channel_id == 770940461337804810:
				return
			roles = mentioneduser.get_roles()
			for r in roles:
				if r.name == "Studying/Working":
					msg = await self.bot.rest.create_message(
						event.channel_id, 
						content = f"Hey {event.message.author.mention}, don't disturb {mentioneduser.mention}. They are currently focusing!",
						user_mentions = False
					)
					await asyncio.sleep(10)
					await msg.delete()

	# Tasks
	async def RefreshMemberTimes(self):
		while True:
			StudyingMembers = await self.GetFocusedMembers()
			for member in StudyingMembers:
				if member[1] == "STREAM":
					timer = ("total", "daily", "weekly", "monthly", "stream")
				elif member[1] == "VIDEO":
					timer = ("total", "daily", "weekly", "monthly", "video")
				elif member[1] == "BOTH":
					timer = ("total", "daily", "weekly", "monthly", "video", "stream")
				else:
					timer = ("total", "daily", "weekly", "monthly")
				update_time(member[0], timer)
			await self.bot.rest.create_message(
				Utils.LOGCHANNELID,
				embed = hikari.Embed(
					title = "Study Streak Club Log",
					description = "Member Times have been updated",
					colour = random.randint(0, 0xffffff),
					timestamp = datetime.now().astimezone()
				)
			)
			await asyncio.sleep(60)

	async def ResetLeaderboard(self):
		while True:
			now = datetime.now()
			if now.hour == 0:
				reset_daily_times()
				await self.bot.rest.create_message(
					Utils.LOGCHANNELID,
					f"Study Streak Club Daily Leaderboard has been reset at <t:{int(time.time())}>"
				)
				if now.weekday() == 0:
					reset_weekly_times()
					await self.bot.rest.create_message(
						Utils.LOGCHANNELID,
						f"Study Streak Club Weekly Leaderboard has been reset at <t:{int(time.time())}>"
					)
				if now.day == 1:
					reset_monthly_times()
					await self.bot.rest.create_message(
						Utils.LOGCHANNELID,
						f"Study Streak Club Monthly Leaderboard has been reset at <t:{int(time.time())}>"
					)
			await asyncio.sleep(3600)
	
	async def KickStalkersFromCamsVC(self):
		while True:
			await asyncio.sleep(KICK_STALKERS_AFTER)
			MembersVoiceStates = self.FetchMembersInChannels([CAMS_ON_VC])
			VoiceStates : VoiceState
			for VoiceStates in MembersVoiceStates:
				if not VoiceStates.member.is_bot:
					if not VoiceStates.is_video_enabled:
						await self.bot.rest.edit_member(int(GUILD_ID), VoiceStates.user_id, voice_channel = STUDYVC1, reason = "User did not turn on camera")
						await self.bot.rest.create_message(
							self.FocusChannelID,
							f"{VoiceStates.member.mention} Moved you to <#{STUDYVC1}> for not turning on camera.",
							user_mentions = True
						)

class StudyStreak(lightbulb.SlashCommandGroup):
	description = "Base command for Study command group"

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

@StudyStreak.subcommand()
class Leaderboard(lightbulb.SlashSubCommand):
	description = "Fetches the top 12 members by time spent studying/working in Study VC."

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

	sort : str = Option("Choose sorting", required = True, choices = ['daily', 'weekly', 'monthly', 'total', 'video', 'stream'])

	async def callback(self, ctx: lightbulb.SlashCommandContext) -> None:
		sort = ctx.options.sort

		await ctx.respond(response_type = hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

		leaderboard = membertime.find({}).sort(sort, -1)
		rank = 1
		LeaderboardEmbed = hikari.Embed(
			title = "Study Streak Club Leaderboard",
			description = f"Currently sorting by {sort}",
			colour = random.randint(0, 0xffffff)
		)
		for memberinfo in leaderboard:
			if rank > 10:
				break
			try:
				member = ctx.get_guild().get_member(memberinfo['user_ID'])
			except:
				continue
			hrs, mins = MinutesToHours(memberinfo[sort])
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
		
		await ctx.edit_response(embed = LeaderboardEmbed)

@StudyStreak.subcommand()
class Stats(lightbulb.SlashSubCommand):
	description = "Fetch the time you/mentioned user have spent studying/working in the Study VCs"

	target : Optional[hikari.User] = Option(description = "User to fetch stats of", required = False)

	enabled_guilds : Optional[Iterable[int]] = (GUILD_ID,)

	async def callback(self, ctx: lightbulb.SlashCommandContext) -> None:
		target = ctx.options.target

		if target is None:
			target = ctx.member
		else:
			target = ctx.get_guild().get_member(target)

		await ctx.respond(response_type = hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

		MemberStats = membertime.find_one({"user_ID" : target.id})
		if not MemberStats:
			add_member_to_db(target.id)
			MemberStats = membertime.find_one({"user_ID" : target.id})
		
		times = []
		StatsEmbed = hikari.Embed(
			title = f"{target.display_name}'s Study Stats",
			description = f"\n**Current Streak :** {MemberStats['streak']}",
			colour = random.randint(0, 0xffffff)
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

		await ctx.edit_response(embed = StatsEmbed)


def load(bot : Bot) -> None:
	bot.add_plugin(Study(bot))
	bot.autodiscover_slash_commands(create = True)
	print("Plugin Study has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Study")
	bot.remove_slash_command("StudyStreak")

