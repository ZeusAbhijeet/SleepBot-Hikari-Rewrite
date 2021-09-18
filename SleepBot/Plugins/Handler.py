import hikari
import lightbulb
import traceback
from lightbulb import errors, listener
from typing import Optional, Union
from lightbulb import Bot
from lightbulb import context
from lightbulb.events import CommandErrorEvent


class Handler(lightbulb.Plugin):
	"""
	Error Handler
	"""
	def __init__(self, bot : lightbulb.Bot) -> None:
		self.bot = bot
		super().__init__()

	def ErrorHandlerEmbed(self, errorType : str, description : str) -> hikari.Embed:
		embed = hikari.Embed(
			title = f"Error : {errorType}",
			description = f"{description}",
			color = hikari.Color(0xFF0000)
		).set_thumbnail(
			"https://res.cloudinary.com/zeusabhijeet/image/upload/v1620057874/SleepBot/Errors/Error.png"
		).add_field(
			name = "What to do now?",
			value = f"Try running the command again or report this error to <@!515097702057508882>"
		)
		return embed
			
	
	@listener(event_type = CommandErrorEvent)
	async def on_command_error(self, event : CommandErrorEvent):
		if isinstance(event.exception, errors.CommandNotFound):
			pass
		elif isinstance(event.exception, errors.CommandIsOnCooldown):
			await event.context.respond(
				embed = self.ErrorHandlerEmbed(
					"Command is on Cooldown",
					f"Please try using this command again in {int(event.exception.retry_in)}s.",
				)
			)
		elif isinstance(event.exception, errors.NotEnoughArguments):
			await event.context.respond(
				embed = self.ErrorHandlerEmbed(
					"Required Arguments were not Passed",
					f"The following required argument(s) was/were not given while invoking the command\n`{event.exception.missing_args}`",
				)
			)
		elif isinstance(event.exception, errors.CheckFailure):
			await event.context.respond(
				embed = self.ErrorHandlerEmbed(
					f"Command Check Failed",
					f"{event.exception.text}" if event.exception.text.startswith("You are missing") is False else f"{event.exception.args[0]}:\n**{event.exception.args[1]}**"
				)
			)
		elif isinstance(event.exception, errors.CommandInvocationError):
			await event.context.respond(
				embed = self.ErrorHandlerEmbed(
					f"Error Occured while running the Command",
					f"An execption occured while executing the command. \n**Exception:**\n```{event.exception.text}```"
				)
			)
		elif isinstance(event.exception, errors.MissingRequiredPermission):
			await event.context.respond(
				embed = self.ErrorHandlerEmbed(
					f"User Missing Required Permissions",
					f"You are missing required permissions to run this command.\nYou need `{event.exception.permissions}` to run this command."
				)
			)
		elif isinstance(event.exception, errors.MissingRequiredRole):
			await event.context.respond(
				embed = self.ErrorHandlerEmbed(
					f"User Missing Required Role",
					f"You are missing required roles to run this command.\n**Exception:**\n```{event.exception.text}```"
				)
			)
		else:
			raise event.exception
	
def load(bot : Bot) -> None:
	bot.add_plugin(Handler(bot))

def unload(bot : Bot) -> None:
	bot.remove_plugin("Handler")
