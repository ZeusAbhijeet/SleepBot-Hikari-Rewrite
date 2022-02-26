import hikari
import lightbulb

from random import randint
from lightbulb import commands, context
from hikari.files import Bytes
from requests import get

fun_plugin = lightbulb.Plugin("Fun")

with open("./Secrets/key") as f:
	APIKey = f.read().strip()

def fun_command_embed(ctx : context.Context, title_string : str, description_string : str, image_url : str) -> hikari.Embed:
		FunEmbed = hikari.Embed(
			title = title_string,
			description = description_string,
			color = randint(0, 0xffffff)
		).set_image(
			image_url
		).set_author(
			name = ctx.author.username,
			icon = ctx.author.avatar_url if ctx.author.avatar_url is not None else ctx.author.default_avatar_url
		)
		return FunEmbed

@fun_plugin.command
@lightbulb.command("fun", "All the joke commands")
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def fun_cmd_grp(ctx : context.Context) -> None:
	await ctx.respond(
		embed = hikari.Embed(
			title = "Fun Command Group",
			description = "This command has multiple subcommands. Type `?help fun` to see them all or use slash commands.",
			colour = randint(0, 0xffffff)
		)
	)

@fun_cmd_grp.child
@lightbulb.add_cooldown(60, 1, lightbulb.UserBucket)
@lightbulb.option("reason", "Reason why you are banning.", type = str, required = False, modifier = commands.OptionModifier.CONSUME_REST)
@lightbulb.option("user", "The person you want to ban", type = hikari.User, required = False)
@lightbulb.command("ban", "Ban someone (or everyone if you will) for fun.")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def fun_ban_cmd(ctx : context.Context) -> None:
	await ctx.respond(
		embed = fun_command_embed(
			ctx,
			f"{ctx.author.username} is flaming everyone with the ban flame!" if ctx.options.user is None else f"{ctx.author.username} is flaming {ctx.options.user.username} with the Ban Flame!!",
			f"The fuel has been injected! Time to ban!" if ctx.options.reason is None else f"The fuel has been injected! Time to ban!\nReason: {ctx.options.reason}",
			"https://res.cloudinary.com/zeusabhijeet/image/upload/v1607091376/SleepBot/Fun%20Commands/ban.gif"
		)
	)

@fun_cmd_grp.child
@lightbulb.add_cooldown(60, 1, lightbulb.UserBucket)
@lightbulb.option("user", "The person whom you want to pet", type = hikari.User, required = False)
@lightbulb.command("petpat", "Pet your (or someone else's) avatar.", auto_defer = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def fun_petpat_cmd(ctx : context.Context) -> None:
	user : hikari.User = ctx.options.user if ctx.options.user is not None else ctx.user

	URL =  f'https://some-random-api.ml/premium/petpet?avatar={user.display_avatar_url}&key={APIKey}'
	resp = get(URL)

	if resp.status_code == 200:
		await ctx.respond(
			attachment = Bytes(resp.content, 'petpat.gif'),
			reply = True
		)
	elif resp.status_code != 200:
		await ctx.respond(
			content = f"An error occurred. API Status Code: {resp.status_code}",
			flags = hikari.MessageFlag.EPHEMERAL
		)
	

@fun_cmd_grp.set_error_handler()
async def fun_error_handler(event : lightbulb.CommandErrorEvent) -> bool:
	if isinstance(event.exception, lightbulb.CommandIsOnCooldown):
		await event.context.respond(
			embed = hikari.Embed(
				title = "Command is on Cooldown",
				description = f"To avoid spam, this command can only be used once per every minute by a user. You can use this command again in `{event.exception.retry_after:.2f}`s.",
				colour = 0xff0000
			),
			flags = hikari.MessageFlag.EPHEMERAL
		)
		return True
	else:
		return False

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(fun_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(fun_plugin)
