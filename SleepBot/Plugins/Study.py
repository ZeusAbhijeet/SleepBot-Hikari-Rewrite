import asyncio
import hikari
from hikari.guilds import Role
from hikari.users import User
import lightbulb
import random
import Utils
from datetime import datetime as dt
from lightbulb import checks
from lightbulb.command_handler import Bot
from typing import Optional, List

FocusChannelID = 818131313810079744 #818131313810079744
StudyBuddiesRoleID = 770667627047682058 #770667627047682058
StudyCategoryID = 771215519193104404 #771215519193104404
StudyVCID = 770670934565715998
LofiStudyVCID = 818011398231687178

class Study(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
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
	async def study_buddies_command(self, ctx : lightbulb.Context, *, msg : str = None) -> None:
		"""
		Ping the Study Buddies role to invite people to study with you
		"""
		StudyBuddyRole = ctx.get_guild().get_role(StudyBuddiesRoleID)

		await ctx.respond(
			f"{StudyBuddyRole.mention}", 
			embed = hikari.Embed(
				description = f"{ctx.author.mention} wants to study with y'all!\nHere's the reason they pinged: **{msg}**" if msg is not None else f"{ctx.author.mention} wants to study with y'all!",
				color = random.randint(0, 0xFFFFFF)
			).set_author(
				name = f"{self.bot.get_me().username}",
				icon = self.bot.get_me().avatar_url
			),
			role_mentions = True
		)

	@lightbulb.plugins.listener(hikari.VoiceStateUpdateEvent)
	async def on_voice_state_update(self, event : hikari.VoiceStateUpdateEvent) -> None:
		if event.old_state is None and event.state is not None and (event.state.channel_id == StudyVCID or event.state.channel_id == LofiStudyVCID):
			UserRoles = len(event.state.member.get_roles())
			await self.bot.rest.create_message(FocusChannelID, f"{event.state.member.mention}", embed = self.StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
		elif event.old_state is not None and event.state is not None and (event.state.channel_id == StudyVCID or event.state.channel_id == LofiStudyVCID):
			if event.old_state.channel_id == StudyVCID or event.old_state.channel_id == LofiStudyVCID:
				return
			UserRoles = len(event.state.member.get_roles())
			await self.bot.rest.create_message(FocusChannelID, f"{event.state.member.mention}", embed = self.StudyVCJoinMessage(event.state.member, UserRoles), user_mentions = True)
	
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
			#MemberBoi = await self.bot.rest.fetch_member(event.guild_id, mentioneduser)
			roles = mentioneduser.get_roles()
			for r in roles:
				if r.name == "Studying/Working":
					msg = await self.bot.rest.create_message(
						event.channel_id, 
						content = f"{event.message.author.mention}",
						embed = hikari.Embed(
							description = f"Don't ping {mentioneduser.mention}. They are currently Studying/Working",
							color = random.randint(0, 0xffffff)
						).set_author(
							name = f"{event.message.author.username}",
							icon = event.message.author.avatar_url
						),
						user_mentions = True
					)
					await asyncio.sleep(10)
					await msg.delete()


def load(bot : Bot) -> None:
	bot.add_plugin(Study(bot))
	print("Plugin Study has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Study")
