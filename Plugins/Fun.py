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
			icon = ctx.author.avatar_url
		)
		return FunEmbed
	
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

def load(bot : Bot):
	bot.add_plugin(Fun(bot))
	print(f"Fun Plugin has been loaded")

def unload(bot : Bot):
	bot.remove_plugin("Fun")
