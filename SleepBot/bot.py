import aiosqlite
import hikari
import lightbulb
import time
import logging
import miru

from lightbulb import commands, context
from lightbulb.ext import tasks
from __init__ import GUILD_ID, OWNER_ID, __version__
from Utils import LOGCHANNELID

with open("./Secrets/token", 'r') as f:
	token = f.read().strip()

intent = (
	hikari.Intents.ALL_GUILDS_UNPRIVILEGED |
	hikari.Intents.GUILD_MEMBERS |
	hikari.Intents.ALL_MESSAGES |
	hikari.Intents.MESSAGE_CONTENT
)

DEFAULT = (
    hikari.Intents.GUILDS
    | hikari.Intents.GUILD_BANS
    | hikari.Intents.GUILD_EMOJIS
    | hikari.Intents.GUILD_INTEGRATIONS
    | hikari.Intents.GUILD_WEBHOOKS
    | hikari.Intents.GUILD_INVITES
    | hikari.Intents.GUILD_VOICE_STATES
    | hikari.Intents.GUILD_MESSAGES
    | hikari.Intents.GUILD_MESSAGE_REACTIONS
    | hikari.Intents.GUILD_MESSAGE_TYPING
    | hikari.Intents.DM_MESSAGES
    | hikari.Intents.DM_MESSAGE_REACTIONS
    | hikari.Intents.DM_MESSAGE_TYPING
    | hikari.Intents.GUILD_SCHEDULED_EVENTS
	| hikari.Intents.MESSAGE_CONTENT
	| hikari.Intents.GUILD_MEMBERS
    )

bot = lightbulb.BotApp(
	token = token,
	prefix = lightbulb.when_mentioned_or('?'),
	intents = DEFAULT,
	default_enabled_guilds = GUILD_ID,
	delete_unbound_commands = True,
	case_insensitive_prefix_commands = True,
	owner_ids = (OWNER_ID,),
	allow_color=False
)

tasks.load(bot)
miru.install(bot)

@bot.listen(hikari.StartingEvent)
async def starting_listener(event : hikari.StartingEvent) -> None:
	global conn
	conn = await aiosqlite.connect('Database.db')
	bot.load_extensions_from("./ext/", must_exist=True)


@bot.listen(hikari.StartedEvent)
async def ready_listener(event : hikari.StartedEvent) -> None:
	await bot.update_presence(
		status = hikari.Status.ONLINE,
		activity = hikari.Activity(
			name = f"?help | v{__version__}",
			type = hikari.ActivityType.LISTENING
		)
	)
	await bot.rest.create_message(LOGCHANNELID, f"Bot is online at time <t:{int(time.time())}>")
	logging.info(f"Bot is online!")
	bot.unsubscribe(hikari.StartingEvent, starting_listener)
	bot.unsubscribe(hikari.StartedEvent, ready_listener)

@bot.listen(hikari.StoppingEvent)
async def stopping_database_connection(event : hikari.StoppedEvent) -> None:
	global conn
	await conn.commit()
	await conn.close()

@bot.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("ext", description = "The Plugin to load", type = str, required = False)
@lightbulb.command("load", "Loads an extension", hidden = True)
@lightbulb.implements(commands.PrefixCommand)
async def load_ext(ctx : context.Context) -> None:
	ext = ctx.options.ext if ctx.options.ext is not None else None
	if ext is None:
		await ctx.respond(f"No Plugin provided to load!", reply = True)
		return
	try:
		bot.load_extensions(f"ext.{ext}")
		await ctx.respond(f"Successfully loaded Plugin {ext}", reply = True)
	except Exception as e:
		await ctx.respond(f":warning: Couldn't load Plugin {ext}. The following exception was raised: \n```{e.__cause__ or e}```")

@bot.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("ext", description = "The Plugin to unload", type = str, required = False)
@lightbulb.command("unload", "Unloads an extension", hidden = True)
@lightbulb.implements(commands.PrefixCommand)
async def unload_ext(ctx : context.Context) -> None:
	ext = ctx.options.ext if ctx.options.ext is not None else None
	if ext is None:
		await ctx.respond(f"No Plugin provided to unload!", reply = True)
		return
	else:
		try:
			bot.unload_extensions(f"ext.{ext}")
			await ctx.respond(f"Successfully unloaded Plugin {ext}", reply = True)
		except Exception as e:
			await ctx.respond(f":warning: Couldn't unload Plugin {ext}. The following exception was raised: \n```{e.__cause__ or e}```")

@bot.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("ext", description = "The Plugin to reload", type = str, required = False)
@lightbulb.command("reload", "Reloads an extension", hidden = True)
@lightbulb.implements(commands.PrefixCommand)
async def reload_ext(ctx : context.Context) -> None:
	ext = ctx.options.ext if ctx.options.ext is not None else None
	if ext is None:
		await ctx.respond(f"No Plugin provided to reload!", reply = True)
		return
	try:
		bot.reload_extensions(f"ext.{ext}")
		await ctx.respond(f"Successfully reloaded Plugin {ext}", reply = True)
	except Exception as e:
		await ctx.respond(f":warning: Couldn't reload Plugin {ext}. The Plugin has been reverted back to the previous working state if already loaded. The following exception was raised: \n```{e.__cause__ or e}```")

@bot.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("logout", "Shuts the bot down", aliases = ['shutdown'], hidden = True)
@lightbulb.implements(commands.PrefixCommand)
async def logout_bot(ctx : context.Context) -> None:
	await ctx.respond(f"Shutting the bot down")
	await bot.close()
