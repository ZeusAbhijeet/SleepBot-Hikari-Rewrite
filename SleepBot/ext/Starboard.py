import hikari
import lightbulb
import aiosqlite
from random import randint
from lightbulb import commands, context
from typing import Union
from Utils import STARBOARDCHANNEL, STAREMOJI, STARTHRESHOLD
from bot import conn
from __init__ import GUILD_ID

starboard_plugin = lightbulb.Plugin("Starboard")

async def get_starboard_message(message) -> Union[hikari.Message, None]:
	c = await conn.execute(
		"SELECT starboard_ID FROM starboard_table WHERE message_ID = ?;", (message,)
	)
	data = await c.fetchone()

	if data:
		try:
			message = await starboard_plugin.app.rest.fetch_message(
				STARBOARDCHANNEL,
				data[0]
			)
			return message
		except hikari.NotFoundError:
			return None
	else:
		return None

async def add_to_db(original_message : hikari.Message, starboard_message : hikari.Message) -> None:
	await conn.execute(
		"INSERT INTO starboard_table VALUES (NULL, ?, ?, ?);",
		(original_message.id, original_message.channel_id, starboard_message.id,)
	)
	await conn.commit()

async def update_db(original_message : hikari.Message, starboard_message : hikari.Message) -> None:
	await conn.execute(
		"UPDATE starboard_table SET starboard_ID = ? WHERE message_ID = ?;",
		(starboard_message.id, original_message.id)
	)
	await conn.commit()

async def create_new_starboard_message(message : hikari.Message, count : int) -> hikari.Message:
	message_channel = await starboard_plugin.app.rest.fetch_channel(message.channel_id)

	embed = hikari.Embed(
		title = f"Jump to message!",
		url = message.make_link(GUILD_ID[0]),
		color = hikari.Color.from_hex_code("#fcd303"),
		description = message.content,
		timestamp = message.timestamp
	).set_author(
		name = f"{message.author.username}#{message.author.discriminator}",
		icon = message.author.display_avatar_url or message.author.avatar_url or message.author.default_avatar_url,
	).set_footer(
		text = f"{message_channel.name}"
	)

	if message.attachments:
		embed.set_image(message.attachments[0])

	new_message = await starboard_plugin.app.rest.create_message(
		STARBOARDCHANNEL,
		f"\u2B50 {count} <#{message_channel.id}>",
		embeds = (embed, *message.embeds[0:9]),
	)

	await add_to_db(message, new_message)
	return new_message

async def update_starboard_message(message : hikari.Message, starboard_message : hikari.Message, count : int) -> None:
	try:
		await starboard_plugin.app.rest.edit_message(
			STARBOARDCHANNEL,
			starboard_message,
			f"\u2B50 {count} <#{message.channel_id}>"
		)
	except hikari.NotFoundError:
		new_starboard_message = await create_new_starboard_message(
			message, count
		)
		await update_db(
			message, new_starboard_message
		)

async def delete_starboard_message(starboard_message : hikari.Message) -> None:
	try:
		await starboard_plugin.app.rest.delete_message(
			starboard_message.channel_id, starboard_message
		)
	except hikari.NotFoundError:
		pass

	await conn.execute("DELETE FROM starboard_table WHERE starboard_ID = ?;", (starboard_message.id))
	await conn.commit()

async def get_reaction_event_info(
    event: Union[hikari.GuildReactionAddEvent, hikari.GuildReactionDeleteEvent],
) -> Union[tuple[hikari.Message, int], None]:
	if event.emoji_name != STAREMOJI:
		return None
    
	try:
		message = await starboard_plugin.app.rest.fetch_message(event.channel_id, event.message_id)

	except hikari.NotFoundError:
        # The message got deleted.
		return None

	# Check if author has reacted with STAREMOJI and delete their reaction
	if event.user_id == message.author.id and event.is_for_emoji(STAREMOJI):
		await starboard_plugin.app.rest.delete_reaction(event.channel_id, message, message.author, emoji = STAREMOJI)
		return None

    # The total number of star emojis.
	count = sum(map(lambda r: r.count if r.emoji == STAREMOJI else 0, message.reactions))
	
	return message, count


@starboard_plugin.listener(hikari.GuildReactionAddEvent)
async def on_reaction_add(
    event: hikari.GuildReactionAddEvent,
) -> None:
    if not (event_data := await get_reaction_event_info(event)):
        # If this returns None we don't care about the event.
        return None

    message, count = event_data
    if message.channel_id == int(STARBOARDCHANNEL):
        return None

    if count >= STARTHRESHOLD:
        # This message is a star!
        starboard_message = await get_starboard_message(message.id)

        if not starboard_message:
            # This is a brand new starboard entry.
            await create_new_starboard_message(message, count)

        else:
            # This is an existing starboard entry.
            await update_starboard_message(message, starboard_message, count)


@starboard_plugin.listener(hikari.GuildReactionDeleteEvent)
async def on_reaction_delete(event: hikari.GuildReactionDeleteEvent) -> None:
    if not (event_data := await get_reaction_event_info(event)):
        # If this returns None we don't care about the event.
        return None

    message, count = event_data
    starboard_message = await get_starboard_message(message.id)

    if not starboard_message:
        # This message is not in the database and thus we can ignore it.
        return None

    if count < STARTHRESHOLD:
        # This message is no longer a star.
        await delete_starboard_message(starboard_message)

    else:
        # This is an existing starboard entry, and still a star!
        await update_starboard_message(message, starboard_message, count)


@starboard_plugin.listener(hikari.GuildMessageDeleteEvent)
@starboard_plugin.listener(hikari.GuildReactionDeleteEmojiEvent)
@starboard_plugin.listener(hikari.GuildReactionDeleteAllEvent)
async def handle_guaranteed_delete(
    event: Union[hikari.GuildMessageDeleteEvent, 
		hikari.GuildReactionDeleteEmojiEvent, 
		hikari.GuildReactionDeleteAllEvent
	]

) -> None:
    if not (guild := starboard_plugin.app.cache.get_available_guild(event.guild_id)):
        # Grab the guild from cache, or construct it from the db
        # if not cached.
        guild = await starboard_plugin.app.rest.fetch_guild(event.guild_id)

    message = await get_starboard_message(event.message_id)

    # Delete message from db and starboard, it has no more reactions.
    return await delete_starboard_message(message) if message else None

def load(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(starboard_plugin)

def unload(bot : lightbulb.BotApp) -> None:
	bot.add_plugin(starboard_plugin)

