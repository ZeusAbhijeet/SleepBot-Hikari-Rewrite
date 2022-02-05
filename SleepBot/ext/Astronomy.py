import hikari
import lightbulb
import requests

from lightbulb import commands, context
from random import randint

with open("./Secrets/apodkey") as f:
	apodkey = f.read().strip()

astronomy_plugin = lightbulb.Plugin("Astronomy")

@astronomy_plugin.command
@lightbulb.command("astropic", " Sends the Astronomy Picture of the Day from NASA", aliases = ['astronomypic', 'apod', 'apic'], auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def apod_cmd(ctx : context.Context) -> None:
	url = f"https://api.nasa.gov/planetary/apod?api_key={apodkey}"
	r = requests.get(url)
	result = r.json()

	embed = hikari.Embed(
		title = result['title'],
		description = f"[Click here to view]({result['url']})\n**Explanation:** {result['explanation']}" if result['media_type'] != "image" else f"**Explanation:** {result['explanation']}",
		url = 'https://apod.nasa.gov/apod/astropix.html',
		colour = randint(0, 0xffffff)
	).set_author(
		name = f"Astronomy Picture of the Day: {result['date']}"
	).set_footer(
		text = f"Requested by {ctx.author.username}#{ctx.author.discriminator}",
		icon = ctx.author.avatar_url if ctx.author.avatar_url else ctx.author.default_avatar_url
	)
	if result["media_type"] == "image":
		embed.set_image(result['hdurl'])
	
	await ctx.respond(f"" if result['media_type'] == 'image' else f"{result['url']}", embed = embed)

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(astronomy_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(astronomy_plugin)
