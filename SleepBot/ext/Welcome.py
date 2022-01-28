import hikari
import lightbulb
import random
import Utils
import time

from lightbulb import commands, context

welcome_plugin = lightbulb.Plugin("Welcome")

def WelcomeEmbed(target : hikari.User) -> hikari.Embed:
	welcomeEmbed = hikari.Embed(
		title = "Welcome to the Bluelearn Discord Server!",
		description = """BlueLearn is a student's community based on skill development and entrepreneurship. Learn and Network with like minded people in the Community.
		50,000 students from 3,500 schools and colleges use BlueLearn to hangout, meet new people, learn skills not taught in traditional education, and become future builders and creators of India!
		
		Make sure that you have a **verified email connected to your account** so that you can interact in the server. \nHere are a few things that you can do:""",
		color = random.randint(0, 0xffffff),
		url = 'https://www.bluelearn.in/'
	).add_field(
		name = "Read the rules",
		value = f"Read the rules in the <#{int(Utils.RULECHANNELID)}> channel carefully"
	).add_field(
		name = "Check out the Server Guide Video",
		value = "If you are new to discord, you can watch a tutorial video which will help you to go about the server.\n**Tutorial:** [Click here](https://youtu.be/AUimFYOBXYU?t=291)"
	).set_image(
		'https://res.cloudinary.com/zeusabhijeet/image/upload/v1624014516/Clinify%20Stuff/Bluelearn_welcome_banner_1.gif'
	).set_author(
		name = target.username,
		icon = target.avatar_url
	)
	return welcomeEmbed

@welcome_plugin.command
@lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.ADMINISTRATOR))
@lightbulb.option("user", "The user to send the DM to.", hikari.User, required = False)
@lightbulb.command("welcomedm", "Send Welcome DM to yourself or the mentioned user", aliases = ['welcomeDM'], ephemeral = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def welcome_dm(ctx : context.Context) -> None:
	target = ctx.options.user or ctx.user
	row = ctx.app.rest.build_action_row()
	row.add_button(
		hikari.ButtonStyle.LINK,
		"https://youtu.be/AUimFYOBXYU?t=291"
	).set_label(
		"Server Guide Video"
	).add_to_container()
	await target.send(embed = WelcomeEmbed(target), component = row)
	await ctx.respond(f"Successfully sent DM to {target.mention}")

@welcome_plugin.listener(event = hikari.MemberCreateEvent)
async def on_member_create(event : hikari.MemberCreateEvent) -> None:
	row = event.app.rest.build_action_row()
	row.add_button(
		hikari.ButtonStyle.LINK,
		"https://youtu.be/AUimFYOBXYU?t=291"
	).set_label(
		"Server Guide Video"
	).add_to_container()
	try:
		await event.member.send(embed = WelcomeEmbed(event.user), component = row)
		await event.app.rest.create_message(
			Utils.LOGCHANNELID,
			embed = hikari.Embed(
				title = "SleepBot Welcome DM Log",
				description = f"Sent DM Message Successfully to: Username : {event.member} ; ID : {event.user_id} at <t:{int(time.time())}>",
				colour = random.randint(0, 0xffffff) 
			)
		)
	except hikari.ForbiddenError:
		await event.app.rest.create_message(
			Utils.LOGCHANNELID,
			embed = hikari.Embed(
				title = "SleepBot Welcome DM Log",
				description = f"Failed to send DM to: Username : {event.member} ; ID : {event.user_id} at <t:{int(time.time())}>",
				colour = 0xd85759 
			)
		)

def load(bot : lightbulb.BotApp):
	bot.add_plugin(welcome_plugin)

def unload(bot : lightbulb.BotApp):
	bot.remove_plugin(welcome_plugin)
