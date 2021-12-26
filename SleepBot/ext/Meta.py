import hikari
import lightbulb
import psutil

from datetime import datetime
from lightbulb import commands, context, __version__ as lightbulb_version
from random import randint
from time import time
from __init__ import OWNER_ID, __version__
from hikari import __version__ as hikari_version


meta_plugin = lightbulb.Plugin("Meta")

@meta_plugin.command
@lightbulb.option("target", "The member to get info about", hikari.User, required = False)
@lightbulb.command("userinfo", "Get info about a server member", auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def userinfo(ctx : context.Context) -> None:
    target = ctx.options.target if ctx.options.target is not None else ctx.user
    target = ctx.get_guild().get_member(target)

    if not target:
        await ctx.respond(f":warning: That user does not seem to be in this server. Double check the provided user?")
        return
    
    created_at = int(target.created_at.timestamp())
    joined_at = int(target.joined_at.timestamp())

    roles = (await target.fetch_roles())[1:] # All roles but @everyone

    embed = hikari.Embed(
        title = f"User Info - {target.display_name}",
        description = f"ID : `{target.id}`",
        colour = randint(0, 0xffffff),
        timestamp = datetime.now().astimezone()
    ).set_footer(
        text = f"Requested by {ctx.member.display_name}",
        icon = ctx.author.avatar_url
    ).set_thumbnail(
        target.avatar_url
    ).add_field(
        "Bot?",
        target.is_bot,
        inline = True
    ).add_field(
        "Account Created On",
        f"<t:{created_at}:d> (<t:{created_at}:R>)",
        inline = True
    ).add_field(
        "Joined Server On",
        f"<t:{joined_at}:d> (<t:{joined_at}:R>)",
        inline = True
    ).add_field(
        "Roles",
        ", ".join(r.mention for r in roles) if roles else "None",
        inline = False
    )
    await ctx.respond(embed = embed, reply = True)


@meta_plugin.command
@lightbulb.command("ping", description = "Check the bot's latency")
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def ping(ctx : context.Context) -> None:
	start = time()
	msg = await ctx.respond(
		embed = hikari.Embed(
			title = "Ping",
			description = "Pong!",
			color = randint(0, 0xffffff)
		), 
		reply = True
	)
	end = time()

	await msg.edit(embed = hikari.Embed(
			title = "Ping",
			description = f"**Heartbeat**: {ctx.app.heartbeat_latency * 1000:,.0f} ms \n**Latency** : {(end - start) * 1000:,.0f} ms",
			color = randint(0, 0xffffff),
            timestamp = datetime.now().astimezone()
		)
	)

@meta_plugin.command
@lightbulb.command("about", description = "Whatever you wanna know about me and Bluelearn!")
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def about_cmd_group(ctx : context.Context) -> None:
    pass

@about_cmd_group.child
@lightbulb.command("sleepbot", "All about me!")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def sleepbot_about(ctx : context.Context) -> None:
    AboutEmbed = hikari.Embed(
		title = "About SleepBot",
		description = "SleepBot is a custom coded and open source bot made by [ZeusAbhijeet](https://github.com/ZeusAbhijeet/) for [Bluelearn.in](https://www.bluelearn.in/) Discord Server. It is written in Python and uses [Hikari](https://github.com/hikari-py/hikari) API wrapper and [Lightbulb](https://github.com/tandemdude/hikari-lightbulb) Command Wrapper. SleepBot can't be invited to your server.",
		colour = randint(0, 0xffffff),
        timestamp = datetime.now().astimezone()
	).add_field(
		name = "Contribute to SleepBot!", 
		value= "SleepBot is an Open Source bot with it's source code available [here](https://github.com/ZeusAbhijeet/SleepBot-Hikari-Rewrite). You are free to contribute to it!",
		inline = False
	).add_field(
        "Ping",
        f"{ctx.app.heartbeat_latency * 1000:,.0f} ms",
        inline = True
    ).add_field(
        "CPU Usage",
        f"{psutil.cpu_percent()}%",
        inline = True
    ).add_field(
        "Memory Usage",
        f"{psutil.virtual_memory()[2]}%",
        inline = True
    ).set_author(
		name = ctx.author.username,
		icon = ctx.author.avatar_url
	).set_thumbnail(
		'https://res.cloudinary.com/zeusabhijeet/image/upload/v1607093923/SleepBot/Info%20Commands/SleepBot_Image.png'
	).set_footer(
		text = f"SleepBot v{__version__} | hikari v{hikari_version} | lightbulb v{lightbulb_version}"
	)
    row = ctx.app.rest.build_action_row()
    row.add_button(
    	hikari.ButtonStyle.LINK, 
    	"https://github.com/ZeusAbhijeet/SleepBot-Hikari-Rewrite"
    ).set_label(
		"SleepBot Repository"
	).add_to_container()
    
    await ctx.respond(embed = AboutEmbed, component = row, reply = True)

@about_cmd_group.child
@lightbulb.command("bluelearn", "All about Bluelearn!")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def bluelearn_about(ctx: context.Context) -> None:
    AboutEmbed = hikari.Embed(
        title = "About Bluelearn",
        description = "BlueLearn is one of India's largest student communities that provides a one-stop platform for students to learn new skills, network with peers, apply for internships and grow as an individual.",
        colour = randint(0, 0xffffff),
        timestamp = datetime.now().astimezone()
    ).set_thumbnail(
        "https://res.cloudinary.com/zeusabhijeet/image/upload/v1630573342/Clinify%20Stuff/Server_Logo_w0cvgw.png"
    ).set_image(
        "https://res.cloudinary.com/zeusabhijeet/image/upload/v1638546922/Clinify%20Stuff/Discord_banner_wm56of.png"
    ).set_author(
		name = ctx.author.username,
		icon = ctx.author.avatar_url
	)

    row = ctx.app.rest.build_action_row()
    row.add_button(
		hikari.ButtonStyle.LINK,
		"https://www.bluelearn.in/"
	).set_label(
		"Website"
	).add_to_container()
    row.add_button(
        hikari.ButtonStyle.LINK,
        "https://www.twitter.com/bluelearn/"
    ).set_label(
        "Twitter"
    ).add_to_container()
    row.add_button(
        hikari.ButtonStyle.LINK,
        "https://www.instagram.com/bluelearn.in/"
    ).set_label(
        "Instagram"
    ).add_to_container()
    row.add_button(
        hikari.ButtonStyle.LINK,
        "https://www.youtube.com/channel/UCSuCYJ_jvzVJYFycR4WIZhw"
    ).set_label(
        "YouTube"
    ).add_to_container()
    
    await ctx.respond(embed = AboutEmbed, component = row, reply = True)

@meta_plugin.command
@lightbulb.option("target", description = "User to fetch avatar of", type = hikari.User, required = False)
@lightbulb.command("avatar", description = "Fetch Avatar of yourself or the specified user.", aliases = ['av', 'pfp'], auto_defer = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def avatar_cmd(ctx: context.Context) -> None:
    target = ctx.options.target if ctx.options.target is not None else ctx.author

    embed = hikari.Embed(
		title = f"Avatar of {target.username}",
		color = randint(0, 0xffffff)
	).set_image(
		target.avatar_url
	).set_footer(
		text = f"Requested by {ctx.author.username}",
		icon = ctx.author.avatar_url
	).set_author(
		name = f"{ctx.app.get_me().username}",
		icon = ctx.app.get_me().avatar_url
	)

    await ctx.respond(embed = embed, reply = True)

@meta_plugin.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("text", description = "Text to repeat", type = str, modifier = commands.OptionModifier.CONSUME_REST, required = True)
@lightbulb.option("channel", description = "Channel to send message in.", type = hikari.TextableChannel, required = True)
@lightbulb.command("say", description = "Says something uwu", hidden = True)
@lightbulb.implements(commands.PrefixCommand, commands.SlashCommand)
async def say_cmd(ctx : context.Context) -> None:
    text = ctx.options.text
    channel = ctx.options.channel
    await ctx.app.rest.create_message(channel, f"```\n{text}\n```\n- {ctx.author.mention}")
    await ctx.respond(f"Message sent successfully UwU")

@meta_plugin.set_error_handler()
@meta_plugin.listener(lightbulb.CommandErrorEvent)
async def on_plugin_command_error(event : lightbulb.CommandErrorEvent) -> bool:
    exception = event.exception.__cause__ or event.exception
    
    if isinstance(exception, lightbulb.NotOwner):
        await event.context.respond(f"I am currently in testing, hence I only respond to commands triggered by <@!{OWNER_ID}>")
        return True
    else:
        return False

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(meta_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(meta_plugin)
