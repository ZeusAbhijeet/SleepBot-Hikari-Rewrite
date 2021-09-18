import hikari
import lightbulb
import requests
import random
import datetime as dt

from lightbulb import Bot

class Astronomy(lightbulb.Plugin):
	def __init__(self, bot : Bot) -> None:
		self.bot = bot
		super().__init__()
	
	@lightbulb.command(name = 'pic')
	async def pic_of_the_day_command(self, ctx : lightbulb.Context) -> None:
		"""Sends the Astronomy Picture of the Day from NASA"""
		url = "https://api.nasa.gov/planetary/apod?api_key=PFmJjSpr3F8mYvFd0DveMBZfQPlqjqXnpfV6LJMD"
		r = requests.get(url)
		result = r.json()

		embed = hikari.Embed(
			title = result['title'],
			url = 'https://apod.nasa.gov/apod/astropix.html',
			description = result['explanation'],
			color = random.randint(0, 0xffffff)
		).set_author(
			name = f"Astronomy Picture of The Day for {dt.date.today().strftime('%d, %b %Y')}",
			icon = self.bot.get_me().avatar_url
		).set_footer(
			text = f"Requested by {ctx.author.username}",
			icon = ctx.author.avatar_url
		).set_image(
			result['hdurl']
		)

		await ctx.respond(embed = embed)

def load(bot : Bot) -> None:
	bot.add_plugin(Astronomy(bot))
	print("Plugin Astronomy has been loaded")

def unload(bot : Bot) -> None:
	bot.remove_plugin("Astronomy")

