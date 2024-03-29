import hikari
import lightbulb

handler_plugin = lightbulb.Plugin('Handler')

@handler_plugin.listener(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
	if isinstance(event.exception, lightbulb.CommandInvocationError):
		await event.context.respond(f"Something went wrong during invocation of command `{event.context.command.name}`.\n`{event.exception.__cause__}`")
		raise event.exception

	# Unwrap the exception to get the original cause
	exception = event.exception.__cause__ or event.exception

	if isinstance(exception, lightbulb.NotOwner):
		await event.context.respond("You are not the owner of this bot.")
	elif isinstance(exception, lightbulb.CommandNotFound):
		pass
	elif isinstance(exception, lightbulb.CheckFailure):
		if event.context.command.plugin.name == "Coins" or event.context.command.plugin.name == "Levelling":
			await event.context.respond("You cannot use this command here. Use it in <#773962393109135380>")
		else:
			await event.context.respond("A command check failed to run. You may be running this command is an unauthorised channel.")
	elif isinstance(exception, lightbulb.CommandIsOnCooldown):
		await event.context.respond(f"This command is on cooldown. Retry in `{exception.retry_after:.2f}` seconds.")
	elif isinstance(exception, lightbulb.MissingRequiredPermission):
		await event.context.respond(f"You do not have permissions to run this command. You require {exception.missing_perms} to run this command")
	else:
		await event.context.respond(f"Something went wrong.\nError text: ```{exception}```")
		raise event.exception

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(handler_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(handler_plugin)
