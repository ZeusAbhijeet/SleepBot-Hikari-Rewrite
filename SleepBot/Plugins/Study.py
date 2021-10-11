import asyncio
import hikari
from hikari.users import User
import lightbulb
import random
import sqlite3

from lightbulb.converters import Greedy
import Utils
from lightbulb.command_handler import Bot
from typing import List
from Utils import StudyBuddiesRoleID

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
	
	@lightbulb.check(Utils.is_study_channel)
	@lightbulb.cooldown(7200, 1, lightbulb.ChannelBucket)
	@lightbulb.command(name="study_buddies", aliases = ['sb', 'studybuddies', 'studybuddy'])
	async def study_buddies_command(self, ctx : lightbulb.Context, msg : Greedy[str]) -> None:
		"""
		Ping the Study Buddies role to invite people to study with you
		"""
		StudyBuddyRole = ctx.get_guild().get_role(StudyBuddiesRoleID)
		if not msg:
			msg = None
		else:
			message = " ".join(msg)
		await ctx.respond(
			f"Hey {StudyBuddyRole.mention}!\n{ctx.author.mention} wants to study with y'all\nHere's the reason they pinged: **{message}**" if msg is not None else f"Hey {StudyBuddyRole.mention}!\n{ctx.author.mention} wants to study with y'all!",
			role_mentions = True
		)

	@lightbulb.plugins.listener(hikari.VoiceStateUpdateEvent)
	async def on_voice_state_update(self, event : hikari.VoiceStateUpdateEvent) -> None:
		if event.old_state is None and event.state is not None and (event.state.channel_id in self.StudyVCIDs):
			UserRoles = len(event.state.member.get_roles())
			await self.bot.rest.create_message(self.FocusChannelID, f"{event.state.member.mention}", embed = self.StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
		elif event.old_state is not None and event.state is not None and (event.state.channel_id in self.StudyVCIDs):
			if event.old_state.channel_id in self.StudyVCIDs:
				return
			UserRoles = len(event.state.member.get_roles())
			await self.bot.rest.create_message(self.FocusChannelID, f"{event.state.member.mention}", embed = self.StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
	
	@lightbulb.plugins.listener(hikari.GuildMessageCreateEvent)
	async def on_message_create(self, event : hikari.GuildMessageCreateEvent):
		if event.author.is_bot:
			return
		mention : List[User] = event.message.mentions.users
		for m in mention:
			mentioneduser = await self.bot.rest.fetch_member(event.guild_id, m)
			if mentioneduser.is_bot:
				return
			elif mentioneduser.id == event.author_id:
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


def load(bot : Bot) -> None:
	bot.add_plugin(Study(bot))
	print("Plugin Study has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Study")
