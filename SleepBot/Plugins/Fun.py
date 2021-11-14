import hikari
import lightbulb
import random

from typing import Optional
from lightbulb.command_handler import Bot
import Utils

class Fun(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	def fun_command_embed(self, ctx : lightbulb.Context, title_string : str, description_string : str, image_url : str) -> hikari.Embed:
		FunEmbed = hikari.Embed(
			title = title_string,
			description = description_string,
			color = random.randint(0, 0xffffff)
		).set_image(
			image_url
		).set_author(
			name = ctx.author.username,
			icon = ctx.author.avatar_url if ctx.author.avatar_url is not None else ctx.author.default_avatar_url
		)
		return FunEmbed
	# Ban Command
	@lightbulb.cooldown(300, 1, lightbulb.UserBucket)
	@lightbulb.command(name = "ban")
	async def fun_ban(self, ctx : lightbulb.Context, target : Optional[hikari.Member], *, reason : Optional[str] = "none"):
		"""
		Hand the Ban Hammer to a user (just for fun)
		"""
		await ctx.respond(
			embed = self.fun_command_embed(
				ctx,
				title_string = f"{ctx.author.username} is flaming everyone with the ban flame!" if target is None else f"{ctx.author.username} is flaming {target.username} with the Ban Flame!!",
				description_string = f"The fuel has been injected! Time to ban!" if reason == "none" else f"The fuel has been injected! Time to ban!\nReason: {reason}",
				image_url = "https://res.cloudinary.com/zeusabhijeet/image/upload/v1607091376/SleepBot/Fun%20Commands/ban.gif"
			)
		)
	"""
	@fun_ban.error
	async def fun_ban_error(self, ctx : lightbulb.Context, error : Exception) -> None:
		if isinstance(error, lightbulb.errors.CommandIsOnCooldown):
			ctx.respond(f"You are on cooldown. Try again in {lightbulb.errors.CommandIsOnCooldown.retry_in}")
		else:
			raise error
	"""
	
	# Kick Command
	@lightbulb.cooldown(300, 1, lightbulb.UserBucket)
	@lightbulb.command(name = "kick")
	async def fun_kick(self, ctx : lightbulb.Context, target : Optional[hikari.Member], *, reason : Optional[str] = "none"):
		"""
		Flying Power ?
		"""
		await ctx.respond(
			embed = self.fun_command_embed(
				ctx,
				title_string = f"{ctx.author.username} is kicking everyone, Flying!" if target is None else f"{ctx.author.username} is kicking {target.username} out of the chat!!",
				description_string = f"Action is a Universal Language" if reason == "none" else f"Action is a Universal Language\nReason: {reason}",
				image_url = "https://res.cloudinary.com/zeusabhijeet/image/upload/v1607091855/SleepBot/Fun%20Commands/kick.gif"
			)
		)
		
	# Shoot Command
	@lightbulb.cooldown(300, 1, lightbulb.UserBucket)
	@lightbulb.command(name = "shoot")
	async def fun_shoot(self, ctx : lightbulb.Context, target : Optional[hikari.Member], *, reason : Optional[str] = "none"):
		"""
		Shoot the mentioned user I guess.
		"""
		await ctx.respond(
			embed = self.fun_command_embed(
				ctx,
				title_string = f"{ctx.author.username} just shot everyone!" if target is None else f"{ctx.author.username} is shooting {target.username} Out of the Party!!",
				description_string = f"The gun's loaded! I taught y'all how to dodge! Right?" if reason == "none" else f"C'mon I taught you how to dodge!\nReason: {reason}",
				image_url = "https://res.cloudinary.com/zeusabhijeet/image/upload/v1607092060/SleepBot/Fun%20Commands/shoot.gif"
			)
		)
		
	# Give Rose Command
	@lightbulb.cooldown(300, 1, lightbulb.UserBucket)
	@lightbulb.command(name = "gib_rose")
	async def fun_gib_rose(self, ctx : lightbulb.Context, target : Optional[hikari.Member], *, reason : Optional[str] = "none"):
		"""
		Give a rose to the mentioned user I guess.
		"""
		await ctx.respond(
			embed = self.fun_command_embed(
				ctx,
				title_string = f"{ctx.author.username} just gave a Rose!" if target is None else f"{ctx.author.username} just gave a Rose to {target.username} !!",
				description_string = f"Take this rose pls" if reason == "none" else f"Take this rose pls\nReason: {reason}",
				image_url = "https://res.cloudinary.com/zeusabhijeet/image/upload/v1607091834/SleepBot/Fun%20Commands/gibrose.gif"
			)
		)
		
	# Slap Command
	@lightbulb.cooldown(300, 1, lightbulb.UserBucket)
	@lightbulb.command(name = "slap")
	async def fun_slap(self, ctx : lightbulb.Context, target : Optional[hikari.Member], *, reason : Optional[str] = "none"):
		"""
		Slap the mentioned user I guess.
		"""
		await ctx.respond(
			embed = self.fun_command_embed(
				ctx,
				title_string = f"{ctx.author.username} just slapped everyone!" if target is None else f"{ctx.author.username} is slapping {target.username} !!",
				description_string = f"Be ready!" if reason == "none" else f"Be Ready!\nReason: {reason}",
				image_url = "https://res.cloudinary.com/zeusabhijeet/image/upload/v1608491339/SleepBot/Fun%20Commands/slap.gif"
			)
		)

def load(bot : Bot):
	bot.add_plugin(Fun(bot))
	print(f"Plugin Fun has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Fun")
