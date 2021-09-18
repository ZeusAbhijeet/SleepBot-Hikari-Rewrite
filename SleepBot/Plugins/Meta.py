import hikari
import lightbulb
import random

from lightbulb.slash_commands.commands import Option
import Utils
import typing
from lightbulb import commands, slash_commands
from lightbulb.command_handler import Bot
from time import time
from typing import Optional
from __init__ import GUILD_ID, __version__

class Meta(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()

	@lightbulb.command(name = "ping")
	async def ping(self, ctx : lightbulb.Context):
		"""
		Shows the bot's latency.
		"""
		await Utils.command_log(self.bot, ctx, "ping")
		start = time()
		msg = await ctx.respond(
			embed = hikari.Embed(
				title = "Ping",
				description = "Pong!",
				color = random.randint(0, 0xffffff)
			), 
			reply = True
		)
		end = time()

		await msg.edit(embed = hikari.Embed(
				title = "Ping",
				description = f"**Heartbeat**: {self.bot.heartbeat_latency * 1000:,.0f} ms \n**Latency** : {(end - start) * 1000:,.0f} ms",
				color = random.randint(0, 0xffffff)
			)
		)
	
	@lightbulb.command(name = "about")
	async def about_command(self, ctx : lightbulb.Context):
		"""
		Shows information about the bot.
		"""
		await Utils.command_log(self.bot, ctx, "about")
		AboutEmbed = hikari.Embed(
			title = "About SleepBot",
			description = "SleepBot is a custom coded and open source bot made by [ZeusAbhijeet](https://github.com/ZeusAbhijeet/) for [Bluelearn.in](https://www.bluelearn.in/) Discord Server. It is written in Python and uses [Hikari-lightbulb](https://github.com/hikari-py/hikari) library.",
			colour = random.randint(0, 0xffffff)
		).add_field(
			name = "Contribute to SleepBot!", 
			value= "SleepBot is an Open Source bot with it's source code available [here](https://github.com/Clinify-Open-Sauce/SleepBot). You are free to contribute to it!",
			inline = False
		).set_footer(
			text = f"Requested by {ctx.author.username} | Version v{__version__}",
			icon = ctx.author.avatar_url
		).set_thumbnail(
			'https://res.cloudinary.com/zeusabhijeet/image/upload/v1607093923/SleepBot/Info%20Commands/SleepBot_Image.png'
		)
		await ctx.respond(embed = AboutEmbed)
	
	@lightbulb.command(name = "avatar", aliases = ["av"])
	async def avatar_command(self, ctx : lightbulb.Context, target : Optional[hikari.Member] = None):
		"""
		Fetches the mentioned user's avatar. If no user is mentioned then fetch the avatar of command user.
		"""
		await Utils.command_log(self.bot, ctx, "avatar")
		msg = await ctx.respond(
			embed = Utils.loading_embed()
		)
		if target is None:
			target = ctx.author
		await msg.edit(
			embed = hikari.Embed(
				title = f"Avatar of {target.username}",
				color = random.randint(0, 0xffffff)
			).set_image(
				target.avatar_url
			).set_footer(
				text = f"Requested by {ctx.author.username}",
				icon = ctx.author.avatar_url
			).set_author(
				name = f"{self.bot.get_me().username}",
				icon = self.bot.get_me().avatar_url
			)
		)

class About(slash_commands.SlashCommand):
	description = "Shows information about the bot."
	
	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	async def callback(self, ctx: lightbulb.Context) -> None:
		AboutEmbed = hikari.Embed(
			title = "About SleepBot",
			description = "SleepBot is a custom coded and open source bot made by [ZeusAbhijeet](https://github.com/ZeusAbhijeet/) for [Bluelearn.in](https://www.bluelearn.in/) Discord Server. It is written in Python and uses [Hikari-lightbulb](https://github.com/hikari-py/hikari) library.",
			colour = random.randint(0, 0xffffff)
		).add_field(
			name = "Contribute to SleepBot!", 
			value= "SleepBot is an Open Source bot with it's source code available [here](https://github.com/Clinify-Open-Sauce/SleepBot). You are free to contribute to it!",
			inline = False
		).set_footer(
			text = f"Requested by {ctx.author.username} | Version v{__version__}",
			icon = ctx.author.avatar_url
		).set_thumbnail(
			'https://res.cloudinary.com/zeusabhijeet/image/upload/v1607093923/SleepBot/Info%20Commands/SleepBot_Image.png'
		)
		await ctx.respond(embed = AboutEmbed)

class Ping(slash_commands.SlashCommand):
	description = "Shows the latency of the bot."
	
	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)

	async def callback(self, ctx: lightbulb.Context) -> None:
		start = time()
		await ctx.respond(
			embed = hikari.Embed(
				title = "Ping",
				description = "Pong!",
				color = random.randint(0, 0xffffff)
			)
		)
		end = time()

		await ctx.edit_response(embed = hikari.Embed(
				title = "Ping",
				description = f"**Heartbeat**: {self.bot.heartbeat_latency * 1000:,.0f} ms \n**Latency** : {(end - start) * 1000:,.0f} ms",
				color = random.randint(0, 0xffffff)
			)
		)

class Avatar(slash_commands.SlashCommand):
	description = "Fetches the mentioned user's avatar. If no user is provided, sends the command invoker's avatar."
	
	enabled_guilds : typing.Optional[typing.Iterable[int]] = (GUILD_ID,)
	
	target : typing.Optional[hikari.User] = slash_commands.Option("The user whose avatar is to be fetched")

	"""
	options : list[hikari.CommandOption] = [
		hikari.CommandOption(
			name = "target",
			description = "The user whose avatar is to be fetched.",
			type = hikari.OptionType.USER,
			is_required = False
		),
	]
	"""

	async def callback(self, ctx: lightbulb.Context) -> None:
		try:
			target : hikari.Member = ctx.guild.get_member(int(ctx.options["target"].value))
		except KeyError:
			target = ctx.author
		
		await ctx.respond(
			embed = hikari.Embed(
				title = f"Avatar of {target.username}",
				color = random.randint(0, 0xffffff)
			).set_image(
				target.avatar_url
			).set_footer(
				text = f"Requested by {ctx.author.username}",
				icon = ctx.author.avatar_url
			).set_author(
				name = f"{self.bot.get_me().username}",
				icon = self.bot.get_me().avatar_url
			)
		)

def load(bot : Bot):
	bot.add_plugin(Meta(bot))
	bot.add_slash_command(About, create = True)
	bot.add_slash_command(Ping, create = True)
	bot.add_slash_command(Avatar, create = True)
	print(f"Plugin Meta has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Meta")
	bot.remove_slash_command("About")
	bot.remove_slash_command("Ping")
	bot.remove_slash_command("Avatar")
