import hikari
import lightbulb
import aiosqlite

from lightbulb import commands, context
from random import randint
from bot import conn
from miru.ext import nav

tag_plugin = lightbulb.Plugin('Tags')

RESERVED_TAGS = (
    "create",
	"add",
    "delete",
    "edit",
    "info",
    "list",
    "transfer",
    "claim",
    "alias",
)

@tag_plugin.command
@lightbulb.option("name", "Name of the tag to fetch", type = str, required = True)
@lightbulb.command("tag", "Fetch an existing tag.")
@lightbulb.implements(commands.PrefixCommandGroup, commands.SlashCommandGroup)
async def tag_group(ctx : context.Context) -> None:
	tag_name = ctx.options.name.lower()

	c = await conn.execute("SELECT content FROM tags_table WHERE name = ?;", (tag_name,))
	query = await c.fetchone()
	if not query:
		return await ctx.respond("Hmmm. Seems like this tag does not exist.")
	await conn.execute("UPDATE tags_table SET uses = uses + 1 WHERE name = ?;", (tag_name,))
	await conn.commit()
	
	if ctx.event.message.referenced_message:
		await ctx.event.message.referenced_message.respond(query[0], reply = True, mentions_reply = True)
	else:
		await ctx.respond(query[0])

@tag_group.child
@lightbulb.option("name", "Name of the tag to fetch", type = str, required = True)
@lightbulb.command("fetch", "Fetch an existing tag.", auto_defer = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def tag_fetch(ctx : context.Context) -> None:
	tag_name = ctx.options.name.lower()

	c = await conn.execute("SELECT content FROM tags_table WHERE name = ?;", (tag_name,))
	query = await c.fetchone()
	if not query:
		return await ctx.respond("Hmmm. Seems like this tag does not exist.")
	await conn.execute("UPDATE tags_table SET uses = uses + 1 WHERE name = ?;", (tag_name,))
	await conn.commit()

	if not ctx.interaction:
		if ctx.event.message.referenced_message:
			await ctx.event.message.referenced_message.respond(query[0], reply = True, mentions_reply = True)
		else:
			await ctx.respond(query[0])
	else:
		await ctx.respond(query[0])

@tag_group.child
@lightbulb.option("content", "The tag content", type = str, required = True, modifier = lightbulb.OptionModifier.CONSUME_REST)
@lightbulb.option("name", "The tag name", type = str, required = True)
@lightbulb.command("add", "Add a new tag", aliases = ['create'], auto_defer = True)
@lightbulb.implements(commands.PrefixSubCommand)
async def tag_add(ctx : context.Context) -> None:
	tag_name = ctx.options.name.lower()
	tag_content = ctx.options.content

	if tag_name in RESERVED_TAGS:
		await ctx.respond(f"The following tag names are reserved: ```{', '.join(RESERVED_TAGS)}```")
		return

	c = await conn.execute("SELECT content FROM tags_table WHERE name = ?;", (tag_name,))
	query = await c.fetchone()
	if query:
		await ctx.respond(f"Hmmm. Looks like tag `{tag_name}` was already created by <@!{query[0]}>. Try a different name maybe?")
		await conn.execute("UPDATE tags_table SET uses = uses + 1 WHERE name = ?;", (tag_name,))
		await conn.commit()
		return
	
	await conn.execute("INSERT INTO tags_table VALUES (NULL, ?, ?, ?, ?);", (ctx.author.id, tag_name, tag_content, 0,))
	await conn.commit()
	await ctx.respond(f'Successfully created tag `{tag_name}` by {ctx.author.mention}')

@tag_group.child
@lightbulb.option("name", "Name of the tag to pull up information of.", required = True)
@lightbulb.command("info", "Gets info about a tag", auto_defer = True)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def tag_info(ctx : context.Context) -> None:
	tag_name = ctx.options.name.lower()

	c = await conn.execute("SELECT user_ID, uses FROM tags_table WHERE name = ?;", (tag_name,))
	query = await c.fetchone()

	if not query:
		await ctx.respond("Hmmm. Looks like this tag does not exist.")
		return
	
	await ctx.respond(
		embed = hikari.Embed(
			title = f"Tag Information",
			description = f"Requested tag: `{tag_name}`",
			colour = randint(0, 0xffffff)
		)
		.add_field("Tag Owner", f"<@!{query[0]}> `({query[0]})`", inline = True)
		.add_field("Uses", query[1], inline = True)
	)

@tag_group.child
@lightbulb.command("list", "Shows a list of tags.", auto_defer = False)
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def tag_list(ctx : context.Context) -> None:
	c = await conn.execute("SELECT name, user_ID, uses FROM tags_table ORDER BY uses DESC;")
	query = await c.fetchall()
	
	if not query:
		await ctx.respond("No tags yet. Make one!")
		return
	
	def get_new_embed() -> hikari.Embed:
		return hikari.Embed(
			title = "Tag List",
			description = "",
			colour = 0x19FA3B
		)

	embeds : list[hikari.Embed] = []

	e = get_new_embed()
	current = 0
	for q in query:
		e.add_field(q[0], f"**Tag Owner :** <@!{q[1]}> `({q[1]})`\n**Tag Uses :** {q[2]}")

		if current == 4:
			embeds.append(e)
			e = get_new_embed()
			current = 0
			continue

		current += 1
	
	embeds.append(e)

	navigator = nav.NavigatorView(pages = embeds, timeout = 60)
	await navigator.send(ctx.interaction or ctx.channel_id)

@tag_group.child
@lightbulb.option("name", "Name of the tag to delete", type = str, required = True)
@lightbulb.command("delete", "Delete a tag that you own")
@lightbulb.implements(commands.PrefixSubCommand, commands.SlashSubCommand)
async def tag_delete(ctx : context.Context) -> None:
	tag_name = ctx.options.name.lower()

	c = await conn.execute("SELECT user_ID FROM tags_table WHERE name = ?", (tag_name,))
	owner = await c.fetchone()

	if not owner:
		await ctx.respond(f"Hmmm. Could not delete tag `{tag_name}`. Seems like it doesn't exist.")
		return
	
	if not ctx.author.id == owner[0]:
		member : hikari.Member = await ctx.get_guild().get_member(ctx.author)
		permissions = lightbulb.utils.permissions_for(member)
		if hikari.Permissions.ADMINISTRATOR in permissions:
			await conn.execute("DELETE FROM tags_table WHERE name = ?", (tag_name,))
			await conn.commit()
			await ctx.respond(f"{member.mention} deleted the tag `{tag_name}` (owned by <@!{owner[0]}>) using admin perms.")
			return
		
		await ctx.respond(f"You don't own the tag `{tag_name}`, <@!{owner[0]}> owns it. So you can't delete it.")
		return
	
	await conn.execute("DELETE FROM tags_table WHERE name = ?", (tag_name,))
	await conn.commit()
	await ctx.respond(f"Tag `{tag_name}` deleted by {ctx.author.mention}.")


def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(tag_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.remove_plugin(tag_plugin)
